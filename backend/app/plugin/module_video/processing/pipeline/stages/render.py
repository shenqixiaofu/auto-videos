from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.config.setting import settings
from app.core.exceptions import CustomException

from ...cover import VideoCoverGenerator
from ...creative import VideoCreativeEditingStage
from ...planner import VideoCreativeEditingPlan, VideoEditPlan
from ...providers import build_render_provider
from ...render_contract import (
    DEFAULT_ASPECT_RATIO,
    VideoRenderOutput,
    VideoTimeline,
    VideoTimelineClip,
)
from ...rendering import VideoRenderingStage
from ...speech_cleanup_parts.media import probe_duration_seconds
from ...storage import VideoObjectStorage
from ..cloud import (
    aliyun_reference_from_creative_metadata,
    download_video_reference,
    upload_local_video_to_aliyun_oss,
)
from ..context import VideoTaskInputs

# 断点落在这些阶段，说明封面还没做完。
_COVER_RESUME_STAGES = {"cover_plan", "cover_generate", "cover_download"}
# 断点落在这些阶段，说明创意渲染或片尾还没结束，封面可以与之并行。
_RENDER_PENDING_STAGES = {
    "creative_plan",
    "creative_render",
    "creative_artifact",
    "ending",
    "ending_render",
    "ending_artifact",
}


def build_ending_concat_timeline(
    *,
    creative_video_url: str,
    creative_duration_seconds: float,
    ending_video_url: str,
    ending_duration_seconds: float,
    output_spec: dict[str, Any],
) -> VideoTimeline:
    """把创意成片和片尾拼成阿里 Timeline 双段视频。

    两个 clip 都从各自素材的第 0 秒开始取（`source_offset_seconds` 默认 0），
    前后顺序由数组顺序决定。`start_seconds` 只记录时间线位置，别拿它当裁切点。
    """
    return VideoTimeline(
        duration_seconds=creative_duration_seconds + ending_duration_seconds,
        tracks=[
            [
                VideoTimelineClip(
                    asset={"kind": "video", "src": creative_video_url},
                    start_seconds=0.0,
                    length_seconds=creative_duration_seconds,
                    metadata={"role": "creative_output"},
                ),
                VideoTimelineClip(
                    asset={"kind": "video", "src": ending_video_url},
                    start_seconds=creative_duration_seconds,
                    length_seconds=ending_duration_seconds,
                    metadata={"role": "ending"},
                ),
            ]
        ],
        output=VideoRenderOutput(
            width=int(output_spec["width"]),
            height=int(output_spec["height"]),
            fps=int(output_spec["fps"]),
            format=str(output_spec.get("format") or "mp4"),
            aspect_ratio=str(
                output_spec.get("aspect_ratio") or DEFAULT_ASPECT_RATIO
            ),
        ),
    )


async def run_processing_tail(
    *,
    worker_cls: type,
    task_id: int,
    inputs: VideoTaskInputs,
    checkpoint: dict[str, Any],
    context: dict[str, Any],
    temp_dir: Path,
) -> None:
    """从创意规划开始按断点继续渲染、封面和审核资产。

    封面只需要口语清理后的视频和字幕，这两样在渲染开始前就已就绪，所以与
    云端渲染并行跑，省掉整段封面等待。两条链都会写同一份断点，用一把锁把
    落库串行化；resume_stage 只由渲染侧推进，封面侧不碰，避免互相覆盖。
    """
    edit_plan: VideoEditPlan = context["edit_plan"]
    bgm_track = context["bgm_track"]
    resume_stage = str(checkpoint.get("resume_stage") or "creative_plan")
    creative_result_metadata = checkpoint.get("creative_result")

    cover_state: dict[str, Any] = dict(checkpoint.get("cover") or {})
    # 断点落在 cover_download 说明生图已完成，直接复用，不重复烧生图额度。
    cover_stage = str(cover_state.get("cover_stage") or "")
    if not cover_stage and resume_stage in _COVER_RESUME_STAGES:
        cover_stage = resume_stage

    checkpoint_lock = asyncio.Lock()

    async def persist_checkpoint() -> None:
        """封面与渲染并发写断点，落库必须串行。"""
        async with checkpoint_lock:
            await worker_cls._save_processing_checkpoint(task_id, checkpoint)

    async def run_cover_stage(*, sync_resume_stage: bool) -> dict[str, Any]:
        """生成 AI 封面图。

        sync_resume_stage=True 时同步推进 resume_stage（渲染已完成后的串行
        补跑），保证封面失败后重试能精确停在封面内部阶段；并行模式下不能动
        它，否则会覆盖渲染侧正在推进的断点。
        """

        async def save_cover_checkpoint(stage: str, payload: dict[str, Any]) -> None:
            # 封面策划、生图和下载分别落断点，避免重复调用生图服务。
            cover_state.update(payload)
            cover_state["cover_stage"] = stage
            checkpoint["cover"] = dict(cover_state)
            if sync_resume_stage:
                checkpoint["resume_stage"] = stage
            await persist_checkpoint()

        # 并行时主链的进行中标记归渲染侧，这里标记会把它顶掉，所以只在串行补跑时标。
        if sync_resume_stage:
            await worker_cls._begin_stage(task_id, checkpoint, "cover")

        cover_result = await VideoCoverGenerator.generate_cover_image(
            task_no=inputs.task_no,
            task_title=inputs.title,
            source_path=context["speech_cleaned_path"],
            source_duration_ms=int(context["cloud_source"]["duration_ms"]),
            temp_dir=temp_dir,
            subtitles=context["subtitle_cues"],
            cover_plan_override=cover_state.get("plan"),
            generated_image_url_override=(
                cover_state.get("generated_image_url")
                if cover_stage == "cover_download"
                else None
            ),
            # 建任务时选的通道优先；老任务 config 里没有这个键，交给 env 兜底。
            provider_override=inputs.config.get("cover_image_provider"),
            save_cover_checkpoint=save_cover_checkpoint,
        )
        return cover_result.to_metadata()

    cover_task: asyncio.Task[dict[str, Any]] | None = None
    if (
        settings.VIDEO_COVER_ENABLED
        and resume_stage in _RENDER_PENDING_STAGES
        and not cover_state.get("cover_object_key")
    ):
        cover_task = asyncio.create_task(run_cover_stage(sync_resume_stage=False))

    try:
        if resume_stage in {"creative_plan", "creative_render"}:
            await worker_cls._ensure_not_cancelled(task_id)
            # 从 creative_render 续跑说明规划早就落库了，这一轮只剩渲染。
            await worker_cls._begin_stage(
                task_id,
                checkpoint,
                "creative_render" if resume_stage == "creative_render" else "creative_plan",
            )
            timeline_task_label = (
                "创意时间线渲染"
                if settings.VIDEO_CREATIVE_EDITING_ENABLED
                else "字幕+BGM 时间线渲染"
            )
            creative_plan_override = None
            if resume_stage == "creative_render":
                creative_plan_override = worker_cls._creative_plan_from_checkpoint(
                    checkpoint["creative_plan"]
                )
            elif not settings.VIDEO_CREATIVE_EDITING_ENABLED:
                creative_plan_override = VideoCreativeEditingPlan.empty()

            async def save_creative_plan(plan: VideoCreativeEditingPlan) -> None:
                # 规划成功后锁定计划，后续渲染失败只重提交时间线。
                checkpoint["creative_plan"] = plan.to_dict()
                checkpoint["resume_stage"] = "creative_render"
                worker_cls._record_stage_timing(checkpoint, "creative_plan")
                # 规划一结束就是渲染，立刻切进行中标记，中间不留空窗。
                await worker_cls._begin_stage(task_id, checkpoint, "creative_render")
                await persist_checkpoint()

            async def save_creative_submission(
                plan: VideoCreativeEditingPlan,
                timeline,
                submit_result,
            ) -> None:
                # 提交后先落库 render_id 和时间线，避免阿里云失败时只剩一条泛化英文报错。
                checkpoint["creative_result"] = {
                    "creative_plan": plan.to_dict(),
                    "timeline": timeline.to_metadata(),
                    "submit_result": submit_result.to_metadata(),
                }
                checkpoint["resume_stage"] = "creative_render"
                await persist_checkpoint()

            creative_stage_result = await VideoCreativeEditingStage.run(
                task_id=task_id,
                task_no=inputs.task_no,
                task_title=inputs.title,
                edit_plan=edit_plan,
                provider=build_render_provider(),
                source_url=context["source_play_url"],
                source_path=context["speech_cleaned_path"],
                utterances=context["timeline_utterances"],
                # 原始句段供创意规划，切分句段只供实际字幕轨渲染。
                subtitle_utterances=context["subtitle_segments"],
                bgm_asset=bgm_track.to_timeline_asset(),
                ensure_not_cancelled=worker_cls._ensure_not_cancelled,
                set_task_status=worker_cls._set_task_status,
                save_creative_plan=save_creative_plan,
                save_creative_submission=save_creative_submission,
                creative_plan_override=creative_plan_override,
                task_label=timeline_task_label,
            )
            creative_result_metadata = creative_stage_result.to_metadata()
            checkpoint["creative_result"] = creative_result_metadata
            checkpoint["resume_stage"] = "creative_artifact"
            worker_cls._record_stage_timing(checkpoint, "creative_render")
            await persist_checkpoint()

        if not isinstance(creative_result_metadata, dict):
            raise CustomException(msg="任务断点缺少创意时间线结果")

        enhancement_metadata = dict(checkpoint.get("enhancement_metadata") or {})
        if not enhancement_metadata:
            enhancement_metadata = {
                "pipeline": (
                    "creative_editing_aliyun_timeline_bgm"
                    if settings.VIDEO_CREATIVE_EDITING_ENABLED
                    else "subtitle_aliyun_timeline_bgm"
                ),
                "timeline_render": creative_result_metadata,
                "bgm": {
                    "provider": "aliyun_public_media",
                    "track": bgm_track.to_metadata(),
                },
            }

        creative_output_reference = checkpoint.get("creative_output")
        if resume_stage in {"creative_plan", "creative_render", "creative_artifact"}:
            if not creative_output_reference:
                creative_output_reference = aliyun_reference_from_creative_metadata(
                    creative_result_metadata
                )
                checkpoint["creative_output"] = creative_output_reference
            resume_stage = worker_cls._next_video_stage(inputs)
            checkpoint["resume_stage"] = resume_stage
            checkpoint["enhancement_metadata"] = enhancement_metadata
            await persist_checkpoint()

        if not isinstance(creative_output_reference, dict):
            raise CustomException(msg="任务断点缺少创意时间线视频产物")

        final_video_reference = creative_output_reference
        if inputs.ending is not None:
            if resume_stage in {"ending", "ending_render"}:
                await worker_cls._begin_stage(task_id, checkpoint, "ending")
                ending_reference = checkpoint.get("ending_reference")
                if not isinstance(ending_reference, dict):
                    await worker_cls._ensure_not_cancelled(task_id)
                    ending_path = worker_cls._temp_asset_path(temp_dir, inputs.ending)
                    await worker_cls._download_input_asset(inputs.ending, ending_path)
                    ending_reference = await upload_local_video_to_aliyun_oss(
                        file_path=ending_path,
                        file_name=worker_cls._ending_file_name(inputs.ending.file_name),
                        role="ending",
                    )
                    ending_reference["duration_ms"] = int(
                        round(await probe_duration_seconds(ending_path) * 1000)
                    )
                    checkpoint["ending_reference"] = ending_reference
                    checkpoint["resume_stage"] = "ending_render"
                    await persist_checkpoint()
                ending_play_url = str(ending_reference["url"])
                creative_output_path = temp_dir / f"{inputs.task_no}-creative-output.mp4"
                await download_video_reference(
                    creative_output_reference,
                    target_path=creative_output_path,
                )
                creative_timeline_meta = dict(creative_result_metadata["timeline"])
                concat_timeline = build_ending_concat_timeline(
                    creative_video_url=str(
                        creative_output_reference.get("url")
                        or creative_result_metadata.get("enhanced_video_url")
                        or ""
                    ),
                    creative_duration_seconds=float(creative_timeline_meta["duration_seconds"]),
                    ending_video_url=ending_play_url,
                    ending_duration_seconds=float(ending_reference["duration_ms"]) / 1000,
                    output_spec=dict(creative_timeline_meta["output"]),
                )
                concat_provider = build_render_provider()
                ending_submit_result = await concat_provider.submit_timeline_render(
                    timeline=concat_timeline,
                    client_token=worker_cls._build_media_kit_client_token(
                        inputs.task_no,
                        edit_plan,
                        "ending",
                    ),
                    source_path=creative_output_path,
                )
                ending_render_result = await VideoRenderingStage.wait_for_video_output(
                    task_id=task_id,
                    provider=concat_provider,
                    render_id=ending_submit_result.render_id,
                    progress=92,
                    task_label="片尾拼接",
                    ensure_not_cancelled=worker_cls._ensure_not_cancelled,
                    set_task_status=worker_cls._set_task_status,
                )
                ending_video_url = ending_render_result.ensure_video_url()
                ending_output_reference = {
                    "provider": "aliyun_oss",
                    "object_key": str(ending_submit_result.raw["output_object_key"]),
                    "url": ending_video_url,
                }
                checkpoint["ending_result"] = {
                    "submit_result": ending_submit_result.to_metadata(),
                    "render_result": ending_render_result.to_metadata(),
                    "video_url": ending_video_url,
                }
                edit_plan.ending = {
                    "asset_id": inputs.ending.id,
                    "file_name": inputs.ending.file_name,
                    "source_reference": ending_reference,
                }
                enhancement_metadata["pipeline"] = f"{enhancement_metadata['pipeline']}_ending"
                enhancement_metadata["ending"] = {
                    "asset_id": inputs.ending.id,
                    "file_name": inputs.ending.file_name,
                    "ending_play_url": ending_play_url,
                    "render_id": ending_submit_result.render_id,
                    "submit_request_id": ending_submit_result.request_id,
                    "result": ending_render_result.to_metadata(),
                }
                checkpoint["ending_output"] = ending_output_reference
                final_video_reference = ending_output_reference
                checkpoint["enhancement_metadata"] = enhancement_metadata
                checkpoint["resume_stage"] = "ending_artifact"
                worker_cls._record_stage_timing(checkpoint, "ending")
                await persist_checkpoint()

            if resume_stage in {"ending", "ending_render", "ending_artifact"}:
                ending_output_reference = checkpoint.get("ending_output")
                if not ending_output_reference:
                    ending_result = checkpoint.get("ending_result")
                    if not isinstance(ending_result, dict):
                        raise CustomException(msg="任务断点缺少片尾渲染结果")
                    submit_result = dict(ending_result.get("submit_result") or {})
                    raw = dict(submit_result.get("raw") or {})
                    output_object_key = str(raw.get("output_object_key") or "").strip()
                    if not output_object_key:
                        raise CustomException(msg="任务断点缺少片尾输出对象键")
                    ending_output_reference = {
                        "provider": "aliyun_oss",
                        "object_key": output_object_key,
                        "url": str(ending_result["video_url"]),
                    }
                    checkpoint["ending_output"] = ending_output_reference
                final_video_reference = ending_output_reference
                resume_stage = worker_cls._next_stage_after_ending()
                checkpoint["resume_stage"] = resume_stage
                checkpoint["enhancement_metadata"] = enhancement_metadata
                await persist_checkpoint()
            elif checkpoint.get("ending_output"):
                final_video_reference = checkpoint["ending_output"]
                edit_plan.ending = {
                    "asset_id": inputs.ending.id,
                    "file_name": inputs.ending.file_name,
                    "source_reference": checkpoint.get("ending_reference"),
                }
    except BaseException:
        # 渲染中途失败时封面协程还在跑：不取消会继续烧生图额度，还会在任务
        # 已经判失败之后接着写断点。
        if cover_task is not None and not cover_task.done():
            cover_task.cancel()
            await asyncio.gather(cover_task, return_exceptions=True)
        raise

    final_video_url = str(final_video_reference.get("url") or "")
    cover_metadata = checkpoint.get("cover")
    if cover_task is not None or (
        settings.VIDEO_COVER_ENABLED and resume_stage in _COVER_RESUME_STAGES
    ):
        try:
            if cover_task is not None:
                cover_metadata = await cover_task
            else:
                # 渲染已经完成、封面还没做（断点续跑）：串行补跑。
                cover_metadata = await run_cover_stage(sync_resume_stage=True)
        except Exception:
            # 成片已经渲染好了，别丢：断点停在封面内部阶段，重试只补封面。
            checkpoint["cover"] = dict(cover_state)
            checkpoint["resume_stage"] = str(
                cover_state.get("cover_stage") or "cover_plan"
            )
            await persist_checkpoint()
            raise
        enhancement_metadata["pipeline"] = (
            f"{enhancement_metadata['pipeline']}_cover_first_frame"
        )
        enhancement_metadata["cover"] = cover_metadata
        checkpoint["cover"] = cover_metadata
        checkpoint["enhancement_metadata"] = enhancement_metadata
        checkpoint["resume_stage"] = "review_output"
        # 并行时封面不占主链时间，只把封面自身耗时记进去，方便判断它是否拖后腿。
        worker_cls._record_stage_timing(
            checkpoint,
            "cover",
            elapsed_seconds=(
                float(cover_metadata.get("cover_elapsed_seconds") or 0.0)
                if cover_task is not None
                else None
            ),
            parallel=cover_task is not None,
        )
        await persist_checkpoint()
    elif settings.VIDEO_COVER_ENABLED and isinstance(cover_metadata, dict):
        enhancement_metadata["pipeline"] = (
            f"{enhancement_metadata['pipeline']}_cover_first_frame"
            if not str(enhancement_metadata["pipeline"]).endswith("_cover_first_frame")
            else enhancement_metadata["pipeline"]
        )
        enhancement_metadata["cover"] = cover_metadata

    resume_stage = str(checkpoint.get("resume_stage") or resume_stage)
    if resume_stage in {"review_output", "asset_create"}:
        await worker_cls._begin_stage(task_id, checkpoint, "review_output")
        review_output_path = temp_dir / "review-output.mp4"
        review_artifact = checkpoint.get("review_output")
        if not isinstance(review_artifact, dict):
            await worker_cls._ensure_not_cancelled(task_id)
            checkpoint["resume_stage"] = "review_output"
            await persist_checkpoint()
            if isinstance(cover_metadata, dict):
                cover_path = temp_dir / "cover-generated.png"
                await VideoObjectStorage.download_object_to_file(
                    object_key=str(cover_metadata["cover_object_key"]),
                    target_path=cover_path,
                )
                final_path = temp_dir / "final-video.mp4"
                await download_video_reference(
                    final_video_reference,
                    target_path=final_path,
                )
                await VideoCoverGenerator.write_cover_as_first_frame(
                    cover_image_path=cover_path,
                    source_video_path=final_path,
                    output_video_path=review_output_path,
                )
            else:
                await download_video_reference(
                    final_video_reference,
                    target_path=review_output_path,
                )
            review_artifact = await worker_cls._persist_final_file(
                task_no=inputs.task_no,
                file_path=review_output_path,
                file_name=f"{inputs.task_no}-review-output.mp4",
                content_type="video/mp4",
            )
            checkpoint["review_output"] = review_artifact
            checkpoint["resume_stage"] = "asset_create"
            await persist_checkpoint()
        else:
            await download_video_reference(
                review_artifact,
                target_path=review_output_path,
            )

        await worker_cls._ensure_not_cancelled(task_id)
        await worker_cls._set_task_status(task_id, "processing", 98, "quality_check")
        await worker_cls._create_review_asset(
            task_id=task_id,
            source=context["cloud_source"],
            source_play_url=context["source_play_url"],
            preprocess_metadata=context["preprocess_metadata"],
            speech_cleanup_metadata=context["speech_cleanup_metadata"],
            creative_result_metadata=creative_result_metadata,
            subtitle_cues=context["subtitle_cues"],
            output_path=review_output_path,
            edit_plan=edit_plan,
            cover_metadata=cover_metadata if isinstance(cover_metadata, dict) else None,
            final_video_url=final_video_url,
            enhancement_metadata=enhancement_metadata,
        )
        checkpoint["enhancement_metadata"] = enhancement_metadata
        checkpoint["resume_stage"] = "completed"
        worker_cls._record_stage_timing(checkpoint, "review_output")
        await persist_checkpoint()
