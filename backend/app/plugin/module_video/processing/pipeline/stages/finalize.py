from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config.setting import settings
from app.core.database import async_db_session
from app.core.exceptions import CustomException

from ...crud import VideoAssetCRUD, VideoTaskCRUD
from ...mediakit_types import VolcMediaKitSubtitleCue
from ...planner import VideoEditPlan
from ...schema import VideoAssetCreateSchema
from ...storage import VideoObjectStorage
from ..context import VideoInputAsset, VideoTaskInputs


async def load_input_assets(
    *,
    task_id: int,
) -> VideoTaskInputs:
    """读取任务的已完成输入素材。"""
    async with async_db_session() as db:
        task = await VideoTaskCRUD.get_task_for_worker_crud(db, task_id)
        if task is None:
            raise CustomException(msg="自动剪辑任务不存在")
        completed_input_assets = [
            VideoInputAsset(
                id=asset.id,
                asset_role=asset.asset_role,
                object_key=asset.object_key,
                file_name=asset.file_name,
                file_metadata=dict(asset.file_metadata or {}),
            )
            for asset in task.assets
            if asset.asset_role in {"source", "ending"} and asset.upload_status == "completed"
        ]
        source_asset = next(
            (
                asset
                for asset in sorted(
                    completed_input_assets,
                    key=lambda item: item.id,
                    reverse=True,
                )
                if asset.asset_role == "source"
            ),
            None,
        )
        if not source_asset:
            raise CustomException(msg="自动剪辑任务缺少已上传完成的原视频")
        ending_asset = next(
            (
                asset
                for asset in sorted(
                    completed_input_assets,
                    key=lambda item: item.id,
                    reverse=True,
                )
                if asset.asset_role == "ending"
            ),
            None,
        )
        task_config = dict(task.config or {})
        checkpoint = await VideoTaskCRUD.get_task_checkpoint_for_worker_crud(db, task_id)
        if not checkpoint:
            # 断点已搬到 video_task_checkpoint 表；迁移还没跑（或老数据）时
            # 它仍留在 config 里，这里兜一下，否则在跑的任务会从头重跑。
            legacy = task_config.get("processing_checkpoint")
            checkpoint = legacy if isinstance(legacy, dict) else {}
        return VideoTaskInputs(
            task_no=task.task_no,
            title=task.title,
            config=task_config,
            checkpoint=checkpoint,
            source=source_asset,
            ending=ending_asset,
        )


async def record_media_cloud_metadata(
    *,
    worker_cls: type,
    task_id: int,
    asset: VideoInputAsset,
    cloud_media: dict[str, Any],
    preprocess_metadata: dict[str, Any],
    speech_cleanup_metadata: dict[str, Any],
) -> None:
    """记录实际送入云端处理区的视频引用信息。"""
    metadata = {
        **asset.file_metadata,
        **preprocess_metadata,
        **speech_cleanup_metadata,
        "source_reference": cloud_media,
        "source_play_url": str(cloud_media.get("url") or ""),
        "source_provider": str(cloud_media.get("provider") or ""),
        "source_object_key": str(cloud_media.get("object_key") or ""),
        "source_duration_ms": int(cloud_media.get("duration_ms") or 0),
    }
    async with async_db_session() as db:
        async with db.begin():
            await worker_cls._ensure_not_cancelled(task_id, db=db)
            await VideoAssetCRUD.update_asset_metadata_for_worker_crud(
                db=db,
                asset_id=asset.id,
                metadata=metadata,
            )


def _build_debug_summary(
    *,
    edit_plan: VideoEditPlan,
    creative_result_metadata: dict[str, Any],
    enhancement_metadata: dict[str, Any],
    subtitle_cues: list[VolcMediaKitSubtitleCue],
) -> dict[str, Any]:
    """汇总一次渲染实际用到的变量，随任务配置下发到列表，便于前端直接排查。"""
    creative_plan = dict(creative_result_metadata.get("creative_plan") or {})
    timeline = dict(creative_result_metadata.get("timeline") or {})
    timeline_metadata = dict(timeline.get("metadata") or {})
    submit_result = dict(creative_result_metadata.get("submit_result") or {})
    sticker_events = list(creative_plan.get("sticker_events") or [])
    animation_events = list(creative_plan.get("animation_events") or [])
    graphic_sticker_events = list(creative_plan.get("graphic_sticker_events") or [])
    keyword_groups = list(creative_plan.get("subtitle_keywords") or [])
    bgm_track = dict((enhancement_metadata.get("bgm") or {}).get("track") or {})
    cover_metadata = dict(enhancement_metadata.get("cover") or {})
    return {
        "style_preset": edit_plan.style_preset,
        "sticker_theme_id": timeline_metadata.get("sticker_theme_id"),
        "sticker_templates": sorted(
            {
                str(event["template_id"])
                for event in sticker_events
                if event.get("template_id")
            }
        ),
        "sticker_count": len(sticker_events),
        "animation_count": len(animation_events),
        "graphic_sticker_count": len(graphic_sticker_events),
        # 氛围装饰层条数由时间线构建时定，规划结果里没有对应事件，只能从 timeline 元数据取。
        "effect_sticker_count": timeline_metadata.get("effect_sticker_count") or 0,
        "graphic_sticker_tones": sorted(
            {
                str(event["tone"])
                for event in graphic_sticker_events
                if event.get("tone")
            }
        ),
        "transitions": sorted(
            {
                str(clip.get(key))
                for track in [
                    *(timeline.get("tracks") or []),
                    *(timeline.get("audio_tracks") or []),
                ]
                for clip in track
                for key in ("transition_in", "transition_out")
                if clip.get(key)
            }
        ),
        "subtitle_count": len(subtitle_cues),
        "highlight_keyword_count": sum(
            len(group) for group in keyword_groups if isinstance(group, list)
        ),
        "bgm_title": bgm_track.get("title"),
        "bgm_tag": bgm_track.get("media_tag_label"),
        "audio_mix": timeline_metadata.get("audio_mix"),
        "render_provider": submit_result.get("provider"),
        "render_id": submit_result.get("render_id"),
        "models": {
            "asr": settings.ALIYUN_DASHSCOPE_ASR_MODEL,
            # 全局配置能覆盖 env，一律优先用本次实际记录的值，缺了才回落 settings。
            "creative_planner": creative_plan.get("planner_model")
            or settings.VIDEO_CREATIVE_PLANNER_MODEL,
            "cover_summary": cover_metadata.get("cover_summary_model")
            or settings.VIDEO_COVER_SUMMARY_MODEL,
            # relay 与 seedream 是两套模型名，只有封面元数据记得住本次实际走了哪个通道，
            # 直接读设置会把 seedream 的端点名显示在 relay 任务上。
            "cover_image": cover_metadata.get("cover_image_model")
            or settings.VIDEO_COVER_IMAGE_MODEL,
        },
    }


async def create_review_asset(
    *,
    worker_cls: type,
    task_id: int,
    source: dict[str, Any],
    source_play_url: str,
    preprocess_metadata: dict[str, Any],
    speech_cleanup_metadata: dict[str, Any],
    creative_result_metadata: dict[str, Any],
    subtitle_cues: list[VolcMediaKitSubtitleCue],
    output_path: Path,
    edit_plan: VideoEditPlan,
    cover_metadata: dict[str, Any] | None,
    final_video_url: str,
    enhancement_metadata: dict[str, Any],
) -> None:
    """将云端成片上传回 MinIO，并创建待审核 review 资产记录。"""
    async with async_db_session() as db:
        async with db.begin():
            task = await VideoTaskCRUD.get_task_for_worker_crud(db, task_id)
            if task is None:
                raise CustomException(msg="自动剪辑任务不存在")
            await worker_cls._ensure_not_cancelled(task_id, db=db)

            file_name = f"{task.task_no}-review-v{edit_plan.version}.mp4"
            object_key = VideoObjectStorage.build_object_key(
                task_no=task.task_no,
                asset_role="review",
                file_name=file_name,
            )
            metadata = await VideoObjectStorage.upload_file(
                object_key=object_key,
                file_path=output_path,
                content_type="video/mp4",
            )
            if cover_metadata is not None:
                await VideoAssetCRUD.create_asset_for_worker_crud(
                    db=db,
                    task=task,
                    data=VideoAssetCreateSchema(
                        task_id=task.id,
                        asset_role="cover",
                        file_name=f"{task.task_no}-cover-v{edit_plan.version}.png",
                        file_size=int(cover_metadata["cover_file_size"]),
                        content_type="image/png",
                        file_metadata=cover_metadata,
                        bucket=settings.MINIO_BUCKET_NAME,
                        object_key=str(cover_metadata["cover_object_key"]),
                        upload_id=None,
                        upload_status="completed",
                        etag=str(cover_metadata["cover_etag"]),
                    ),
                )
            submit_result = dict(creative_result_metadata.get("submit_result") or {})
            render_result = dict(creative_result_metadata.get("render_result") or {})
            await VideoAssetCRUD.create_asset_for_worker_crud(
                db=db,
                task=task,
                data=VideoAssetCreateSchema(
                    task_id=task.id,
                    asset_role="review",
                    file_name=file_name,
                    file_size=metadata["file_size"],
                    content_type="video/mp4",
                    file_metadata={
                        **preprocess_metadata,
                        **speech_cleanup_metadata,
                        "timeline_render_provider": submit_result.get("provider"),
                        "timeline_render_id": submit_result.get("render_id"),
                        "timeline_render_submit_request_id": submit_result.get("request_id"),
                        "timeline_render_status": render_result.get("status"),
                        "timeline_render_output_url": creative_result_metadata.get(
                            "enhanced_video_url"
                        ),
                        "timeline_render_plan": creative_result_metadata.get(
                            "creative_plan"
                        ),
                        "timeline_render_timeline": creative_result_metadata.get(
                            "timeline"
                        ),
                        "timeline_render_result": render_result,
                        "source_reference": source,
                        "source_play_url": source_play_url,
                        "video_pipeline": enhancement_metadata["pipeline"],
                        "video_final_video_url": final_video_url,
                        "video_enhancements": enhancement_metadata,
                        # 创意规划模型名补进元数据，调试面板要能一眼看到各阶段用的模型。
                        # 全局配置可覆盖 env，优先用本次实际调用的那个。
                        "creative_planner_model": dict(
                            creative_result_metadata.get("creative_plan") or {}
                        ).get("planner_model")
                        or settings.VIDEO_CREATIVE_PLANNER_MODEL,
                        "timeline_subtitle_mode": "aliyun_timeline",
                        "timeline_subtitle_count": len(subtitle_cues),
                        "timeline_subtitles": [
                            subtitle.to_dict() for subtitle in subtitle_cues
                        ],
                        "review_version": edit_plan.version,
                        "review_status": "pending",
                        "edit_plan": edit_plan.to_dict(),
                        "cover": cover_metadata,
                    },
                    bucket=settings.MINIO_BUCKET_NAME,
                    object_key=object_key,
                    upload_id=None,
                    upload_status="completed",
                    etag=metadata["etag"],
                ),
            )
            # 摘要写进任务配置，列表响应就能直接带出，不用为了看调试信息再拉一次详情。
            task.config = {
                **dict(task.config or {}),
                "debug_summary": _build_debug_summary(
                    edit_plan=edit_plan,
                    creative_result_metadata=creative_result_metadata,
                    enhancement_metadata=enhancement_metadata,
                    subtitle_cues=subtitle_cues,
                ),
            }
