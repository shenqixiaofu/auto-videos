from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.exceptions import CustomException

from ...preprocessor import VideoSourcePreprocessor
from ...providers.aliyun_asr import AliyunDashScopeAsrProvider
from ...providers.aliyun_public_media import AliyunPublicMediaProvider
from ...render_contract import DEFAULT_ASPECT_RATIO
from ...speech_cleanup import VideoSpeechCleanupStage
from ..cloud import (
    download_video_reference,
    resolve_video_url,
    upload_local_video_to_aliyun_oss,
)
from ..context import VideoTaskInputs


async def prepare_processing_context(
    *,
    worker_cls: type,
    task_id: int,
    inputs: VideoTaskInputs,
    checkpoint: dict[str, Any],
    temp_dir: Path,
    speech_provider: AliyunDashScopeAsrProvider,
    public_bgm_provider: AliyunPublicMediaProvider,
) -> dict[str, Any]:
    """准备断点之后各阶段复用的本地文件和结构化上下文。"""
    resume_stage = str(checkpoint.get("resume_stage") or "media_analysis")
    source_path = worker_cls._temp_asset_path(temp_dir, inputs.source)
    preprocessed_path = temp_dir / "preprocessed.mp4"
    speech_cleaned_path = temp_dir / "speech-cleaned.mp4"

    if resume_stage == "media_analysis":
        await worker_cls._ensure_not_cancelled(task_id)
        await worker_cls._begin_stage(task_id, checkpoint, "media_analysis")
        await worker_cls._set_task_status(task_id, "processing", 10, "media_analysis")
        from ...storage import VideoObjectStorage

        await VideoObjectStorage.download_object_to_file(
            object_key=inputs.source.object_key,
            target_path=source_path,
        )
        preprocess_result = await VideoSourcePreprocessor.preprocess(
            source_path=source_path,
            output_path=preprocessed_path,
            original_file_name=inputs.source.file_name,
            output_file_name=worker_cls._preprocessed_file_name(inputs.source.file_name),
            target_aspect_ratio=str(
                inputs.config.get("aspect_ratio") or DEFAULT_ASPECT_RATIO
            ),
        )
        preprocessed_artifact = await upload_local_video_to_aliyun_oss(
            file_path=preprocess_result.output_path,
            file_name=preprocess_result.output_file_name,
            role="preprocessed",
        )
        checkpoint.update(
            {
                "preprocessed": preprocessed_artifact,
                "preprocess_metadata": preprocess_result.to_metadata(),
                "resume_stage": "speech_cleanup",
            }
        )
        worker_cls._record_stage_timing(checkpoint, "media_analysis")
        await worker_cls._save_processing_checkpoint(task_id, checkpoint)
        resume_stage = "speech_cleanup"
    else:
        await download_video_reference(
            checkpoint["preprocessed"],
            target_path=preprocessed_path,
        )

    if resume_stage == "speech_cleanup":
        await worker_cls._ensure_not_cancelled(task_id)
        await worker_cls._begin_stage(task_id, checkpoint, "speech_cleanup")
        await worker_cls._set_task_status(task_id, "processing", 25, "editing")
        speech_cleanup_result = await VideoSpeechCleanupStage.run(
            task_id=task_id,
            task_no=inputs.task_no,
            provider=speech_provider,
            source_path=preprocessed_path,
            output_path=speech_cleaned_path,
            source_file_name=str(
                checkpoint.get("preprocess_metadata", {}).get(
                    "preprocess_output_file_name",
                    inputs.source.file_name,
                )
            ),
            output_file_name=worker_cls._speech_cleanup_file_name(inputs.source.file_name),
            ensure_not_cancelled=worker_cls._ensure_not_cancelled,
        )
        remapped_utterances = VideoSpeechCleanupStage.remap_utterances_to_output_timeline(
            utterances=speech_cleanup_result.recognition_result.utterances,
            kept_intervals=speech_cleanup_result.kept_intervals,
        )
        timeline_utterances = worker_cls._serialize_utterances_for_timeline(remapped_utterances)
        subtitle_segments = VideoSpeechCleanupStage.build_subtitle_segments(
            utterances=remapped_utterances
        )
        speech_artifact = await upload_local_video_to_aliyun_oss(
            file_path=speech_cleanup_result.output_path,
            file_name=speech_cleanup_result.output_file_name,
            role="speech_cleaned",
        )
        checkpoint.update(
            {
                "speech_cleaned": speech_artifact,
                "speech_cleanup_metadata": speech_cleanup_result.to_metadata(),
                "timeline_utterances": timeline_utterances,
                "subtitle_segments": subtitle_segments,
                "subtitle_cues": [
                    cue.to_dict()
                    for cue in worker_cls._build_subtitle_cues_from_utterances(
                        subtitle_segments
                    )
                ],
                "resume_stage": "creative_plan",
            }
        )
        worker_cls._record_stage_timing(checkpoint, "speech_cleanup")
        await worker_cls._save_processing_checkpoint(task_id, checkpoint)
    else:
        await download_video_reference(
            checkpoint["speech_cleaned"],
            target_path=speech_cleaned_path,
        )

    # 媒资登记和选曲都算 creative_prepare，断点续跑时同样要跑，所以标记放在
    # 分支外面，别只覆盖首次执行。
    await worker_cls._begin_stage(task_id, checkpoint, "creative_prepare")
    if resume_stage in {"media_analysis", "speech_cleanup"}:
        await worker_cls._ensure_not_cancelled(task_id)
        await worker_cls._set_task_status(task_id, "processing", 30, "editing")
        source_reference = dict(checkpoint["speech_cleaned"])
        source_reference["duration_ms"] = _resolve_output_duration_ms(
            checkpoint["speech_cleanup_metadata"]
        )
        await worker_cls._record_media_cloud_metadata(
            task_id=task_id,
            asset=inputs.source,
            cloud_media=source_reference,
            preprocess_metadata=dict(checkpoint["preprocess_metadata"]),
            speech_cleanup_metadata=dict(checkpoint["speech_cleanup_metadata"]),
        )
        checkpoint["cloud_source"] = source_reference
        checkpoint["resume_stage"] = "creative_plan"
        await worker_cls._save_processing_checkpoint(task_id, checkpoint)
    else:
        source_reference = dict(checkpoint["cloud_source"])
        if "duration_ms" not in source_reference:
            source_reference["duration_ms"] = _resolve_output_duration_ms(
                checkpoint["speech_cleanup_metadata"]
            )

    source_play_url = await resolve_video_url(source_reference)

    edit_plan = worker_cls._build_edit_plan(
        task_no=inputs.task_no,
        config=inputs.config,
        source_duration_ms=int(source_reference["duration_ms"]),
    )
    if not edit_plan.subtitle_enabled:
        raise CustomException(msg="当前智能视频流程需要开启自动字幕")

    if checkpoint.get("bgm_track"):
        bgm_track = worker_cls._bgm_track_from_checkpoint(checkpoint["bgm_track"])
    else:
        await worker_cls._ensure_not_cancelled(task_id)
        bgm_track = await public_bgm_provider.pick_bgm_track(
            style_preset=edit_plan.style_preset,
            task_seed=edit_plan.seed,
        )
    edit_plan.music = bgm_track.to_metadata()
    checkpoint.update(
        {
            "cloud_source": source_reference,
            "bgm_track": bgm_track.to_metadata(),
            "resume_stage": (
                "creative_plan"
                if resume_stage in {"media_analysis", "speech_cleanup"}
                else checkpoint.get("resume_stage")
            ),
        }
    )
    worker_cls._record_stage_timing(checkpoint, "creative_prepare")
    await worker_cls._save_processing_checkpoint(task_id, checkpoint)
    return {
        "speech_cleaned_path": speech_cleaned_path,
        "preprocess_metadata": dict(checkpoint["preprocess_metadata"]),
        "speech_cleanup_metadata": dict(checkpoint["speech_cleanup_metadata"]),
        "cloud_source": source_reference,
        "source_play_url": source_play_url,
        "edit_plan": edit_plan,
        "timeline_utterances": list(checkpoint["timeline_utterances"]),
        "subtitle_segments": list(checkpoint["subtitle_segments"]),
        "subtitle_cues": worker_cls._subtitle_cues_from_checkpoint(
            checkpoint["subtitle_cues"]
        ),
        "bgm_track": bgm_track,
    }


def _resolve_output_duration_ms(speech_cleanup_metadata: dict[str, Any]) -> int:
    """取口语清理后的成片时长，作为时间线总时长。

    老断点没有该字段，回退到源时长，行为与改动前一致。
    """
    seconds = speech_cleanup_metadata.get(
        "speech_cleanup_output_duration_seconds"
    ) or speech_cleanup_metadata.get("speech_cleanup_source_duration_seconds")
    return int(round(float(seconds) * 1000))
