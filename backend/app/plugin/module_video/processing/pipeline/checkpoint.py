from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.config.setting import settings
from app.core.database import async_db_session

from ..crud import VideoTaskCRUD
from ..mediakit_types import VolcMediaKitSubtitleCue
from ..planner import (
    VideoCreativeAnimationEvent,
    VideoCreativeEditingPlan,
    VideoCreativeGraphicStickerEvent,
    VideoCreativeStickerEvent,
)
from ..providers.aliyun_public_media import AliyunPublicBgmTrack
from ..storage import VideoObjectStorage

INITIAL_CHECKPOINT: dict[str, Any] = {
    "version": 1,
    "resume_stage": "media_analysis",
}

STAGE_TIMINGS_KEY = "stage_timings"
# 当前正在跑的阶段。阶段耗时是结束后才记录的，中途只有这个标记能让前端
# 知道「现在跑到哪、已经跑了多久」。
_ACTIVE_STAGE_KEY = "_active_stage"
# 本次尝试的起点，第一个阶段的耗时从这里开始算。
_ATTEMPT_STARTED_AT_KEY = "_attempt_started_at"
# 上一次阶段打点时刻，用来算相邻阶段之间的耗时。
_STAGE_TIMING_CURSOR_KEY = "_stage_timing_cursor"
# 打点只在进程内做减法，用微秒精度避免秒级截断把短阶段算歪。
# 注意：schema.py 里解析同一格式，改这里要同步改那边。
_TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

# 阶段标识 → 展示名。标签由后端下发，前端不再维护第二套映射。
STAGE_TIMING_LABELS: dict[str, str] = {
    "media_analysis": "素材预处理",
    "speech_cleanup": "语音转写与口语清理",
    "creative_prepare": "媒资登记与选曲",
    "creative_plan": "创意规划",
    "creative_render": "云端渲染",
    "ending": "片尾拼接",
    "cover": "AI 封面",
    "review_output": "成片质检与入库",
}


def _format_time(value: datetime) -> str:
    """带微秒格式化，只在断点内部做时间差，不与数据库时间列混用。"""
    return value.strftime(_TIME_FORMAT)


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.strptime(value, _TIME_FORMAT)
    except ValueError:
        return None


class ProcessingCheckpointMixin:
    """提供阶段断点、阶段产物和结构化结果的持久化能力。"""

    @staticmethod
    def _load_processing_checkpoint(
        raw_checkpoint: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """读取任务内部断点，没有断点时从首阶段开始。"""
        if not isinstance(raw_checkpoint, dict):
            return dict(INITIAL_CHECKPOINT)
        return {
            "version": int(raw_checkpoint.get("version") or 1),
            **raw_checkpoint,
        }

    @staticmethod
    def _start_stage_timings(checkpoint: dict[str, Any]) -> None:
        """重置阶段耗时，只保留本次尝试的记录。

        总耗时按 config.attempt_started_time 算，每次领取任务都会刷新，
        阶段耗时保持同一口径，避免重试后各阶段之和超过总耗时。
        """
        checkpoint[STAGE_TIMINGS_KEY] = []
        checkpoint[_ATTEMPT_STARTED_AT_KEY] = _format_time(datetime.now())
        checkpoint.pop(_STAGE_TIMING_CURSOR_KEY, None)
        checkpoint.pop(_ACTIVE_STAGE_KEY, None)

    @classmethod
    async def _begin_stage(
        cls,
        task_id: int,
        checkpoint: dict[str, Any],
        stage: str,
    ) -> None:
        """标记一个阶段开始跑，并落库。

        阶段耗时只在阶段结束时才进 `stage_timings`，中间这段空窗前端只能
        看到上一次的旧数据。这里单独记下「当前阶段 + 起点」，配合读取侧的
        实时换算，用户不刷新也能看到耗时在涨。

        必须自己落库：调用点后面往往要等整个阶段跑完才会有下一次写库。
        """
        checkpoint[_ACTIVE_STAGE_KEY] = {
            "stage": stage,
            "label": STAGE_TIMING_LABELS.get(stage, stage),
            "started_at": _format_time(datetime.now()),
        }
        await cls._save_processing_checkpoint(task_id, checkpoint)

    @staticmethod
    def build_stage_progress(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
        """提取当前正在跑的阶段，供配置顶层镜像。

        只给阶段名和起点，已耗时由读取侧按请求时刻现算 —— 落库时算的数值
        到用户打开页面时早就过期了。
        """
        active = checkpoint.get(_ACTIVE_STAGE_KEY)
        if not isinstance(active, dict) or not active.get("stage"):
            return None
        stage = str(active["stage"])
        return {
            "stage": stage,
            "label": str(active.get("label") or STAGE_TIMING_LABELS.get(stage, stage)),
            "started_at": str(active.get("started_at") or ""),
        }

    @staticmethod
    def _end_stage(checkpoint: dict[str, Any]) -> None:
        """撤掉进行中标记。任务失败或结束时调用，否则前端会一直显示「进行中」。"""
        checkpoint.pop(_ACTIVE_STAGE_KEY, None)

    @staticmethod
    def _record_stage_timing(
        checkpoint: dict[str, Any],
        stage: str,
        *,
        elapsed_seconds: float | None = None,
        parallel: bool = False,
    ) -> None:
        """记录一个处理阶段的耗时，供前端展示各阶段明细。

        起点取上一次打点时刻，没有则取本次尝试开始时间，因此断点续跑时
        被跳过的阶段不会被算进下一个阶段的耗时里。

        `elapsed_seconds` 供与主链并行的阶段使用：耗时由调用方自己给出，
        并且不推进游标 —— 并行时长本来就不占主链时间，推进游标会把后续
        阶段的差值算歪。
        """
        now = datetime.now()
        if elapsed_seconds is None:
            cursor = _parse_time(
                checkpoint.get(_STAGE_TIMING_CURSOR_KEY)
            ) or _parse_time(checkpoint.get(_ATTEMPT_STARTED_AT_KEY))
            elapsed_seconds = (
                round(max((now - cursor).total_seconds(), 0.0), 1) if cursor else 0.0
            )
        timings = [
            item
            for item in checkpoint.get(STAGE_TIMINGS_KEY) or []
            if isinstance(item, dict) and item.get("stage") != stage
        ]
        entry: dict[str, Any] = {
            "stage": stage,
            "label": STAGE_TIMING_LABELS.get(stage, stage),
            "elapsed_seconds": round(max(elapsed_seconds, 0.0), 1),
        }
        if parallel:
            entry["parallel"] = True
        timings.append(entry)
        checkpoint[STAGE_TIMINGS_KEY] = timings
        if not parallel:
            checkpoint[_STAGE_TIMING_CURSOR_KEY] = _format_time(now)
        # 阶段跑完了就撤掉进行中标记；并行的 cover 打点不能误撤主链的阶段。
        active = checkpoint.get(_ACTIVE_STAGE_KEY)
        if isinstance(active, dict) and active.get("stage") == stage:
            checkpoint.pop(_ACTIVE_STAGE_KEY, None)

    @classmethod
    async def _save_processing_checkpoint(
        cls,
        task_id: int,
        checkpoint: dict[str, Any],
    ) -> None:
        """把阶段断点合并写入任务配置。"""
        async with async_db_session() as db:
            async with db.begin():
                await VideoTaskCRUD.update_task_checkpoint_for_worker_crud(
                    db=db,
                    task_id=task_id,
                    checkpoint=checkpoint,
                )

    @classmethod
    async def _persist_final_file(
        cls,
        *,
        task_no: str,
        file_path: Path,
        file_name: str,
        content_type: str,
    ) -> dict[str, Any]:
        """把最终审核文件保存到项目 MinIO。"""
        object_key = VideoObjectStorage.build_object_key(
            task_no=task_no,
            asset_role="review",
            file_name=f"final-{file_name}",
        )
        metadata = await VideoObjectStorage.upload_file(
            object_key=object_key,
            file_path=file_path,
            content_type=content_type,
        )
        return {
            "provider": "minio_final",
            "object_key": object_key,
            "file_name": file_name,
            "content_type": content_type,
            "file_size": int(metadata["file_size"]),
            "etag": str(metadata["etag"]),
        }

    @staticmethod
    def _source_reference_to_checkpoint(source_reference: dict[str, Any]) -> dict[str, Any]:
        """序列化通用视频引用。"""
        return dict(source_reference)

    @staticmethod
    def _source_reference_from_checkpoint(payload: dict[str, Any]) -> dict[str, Any]:
        """从断点恢复通用视频引用。"""
        return dict(payload)

    @staticmethod
    def _bgm_track_from_checkpoint(payload: dict[str, Any]) -> AliyunPublicBgmTrack:
        """从断点恢复已选 BGM，避免重试重新查询曲库。"""
        return AliyunPublicBgmTrack(
            media_id=str(payload["media_id"]),
            title=str(payload["title"]),
            duration_ms=int(payload["duration_ms"]),
            media_tag_id=str(payload["media_tag_id"]),
            media_tag_label=(
                str(payload["media_tag_label"])
                if payload.get("media_tag_label") is not None
                else None
            ),
            volume_gain=float(payload["volume_gain"]),
            preview_url=str(payload["preview_url"]) if payload.get("preview_url") else None,
            media_url=str(payload["media_url"]) if payload.get("media_url") else None,
            cover_url=str(payload["cover_url"]) if payload.get("cover_url") else None,
        )

    @staticmethod
    def _subtitle_cues_from_checkpoint(
        payload: list[dict[str, Any]],
    ) -> list[VolcMediaKitSubtitleCue]:
        """从断点恢复封面和审核阶段使用的字幕 cue。"""
        return [
            VolcMediaKitSubtitleCue(
                subtitle_text=str(item["subtitle_text"]),
                start_time=float(item["start_time"]),
                end_time=float(item["end_time"]),
                speaker=str(item["speaker"]) if item.get("speaker") else None,
                confidence=(
                    float(item["confidence"])
                    if item.get("confidence") is not None
                    else None
                ),
            )
            for item in payload
        ]

    @staticmethod
    def _creative_plan_from_checkpoint(
        payload: dict[str, Any],
    ) -> VideoCreativeEditingPlan:
        """从断点恢复已完成的创意规划结果。"""
        sticker_events = [
            VideoCreativeStickerEvent(
                id=str(item["id"]),
                template_id=str(item["template_id"]),
                start_ms=int(item["start_ms"]),
                end_ms=int(item["end_ms"]),
                text=str(item["text"]),
                placement=str(item["placement"]),
                scale=float(item.get("scale") or 1.0),
                rotation=float(item.get("rotation") or 0.0),
                title_text=str(item["title_text"]) if item.get("title_text") else None,
                body_text=str(item["body_text"]) if item.get("body_text") else None,
                card_style=str(item["card_style"]) if item.get("card_style") else None,
                anchor_text=str(item["anchor_text"]) if item.get("anchor_text") else None,
            )
            for item in payload.get("sticker_events") or []
        ]
        animation_events = [
            VideoCreativeAnimationEvent(
                id=str(item["id"]),
                template_id=str(item["template_id"]),
                start_ms=int(item["start_ms"]),
                end_ms=int(item["end_ms"]),
                description=str(item["description"]),
                placement=str(item["placement"]),
                intensity=str(item.get("intensity") or "medium"),
                scale=float(item.get("scale") or 1.0),
                rotation=float(item.get("rotation") or 0.0),
                anchor_text=str(item["anchor_text"]) if item.get("anchor_text") else None,
            )
            for item in payload.get("animation_events") or []
        ]
        graphic_sticker_events = [
            VideoCreativeGraphicStickerEvent(
                id=str(item["id"]),
                tone=str(item["tone"]),
                start_ms=int(item["start_ms"]),
                end_ms=int(item["end_ms"]),
                placement=str(item["placement"]),
                scale=float(item.get("scale") or 1.0),
                rotation=float(item.get("rotation") or 0.0),
                anchor_text=str(item["anchor_text"]) if item.get("anchor_text") else None,
            )
            for item in payload.get("graphic_sticker_events") or []
        ]
        raw_keywords = payload.get("subtitle_keywords")
        subtitle_keywords = (
            [
                [str(word) for word in group]
                for group in raw_keywords
                if isinstance(group, list)
            ]
            if isinstance(raw_keywords, list)
            else []
        )
        return VideoCreativeEditingPlan(
            summary=str(payload["summary"]) if payload.get("summary") else None,
            sticker_events=sticker_events,
            animation_events=animation_events,
            graphic_sticker_events=graphic_sticker_events,
            subtitle_keywords=subtitle_keywords,
        )

    @staticmethod
    def _next_video_stage(inputs) -> str:
        """计算创意视频产物保存后的下一个断点。"""
        if inputs.ending is not None:
            return "ending"
        if settings.VIDEO_COVER_ENABLED:
            return "cover_plan"
        return "review_output"

    @staticmethod
    def _next_stage_after_ending() -> str:
        """计算片尾完成后的下一个断点。"""
        return "cover_plan" if settings.VIDEO_COVER_ENABLED else "review_output"

    @staticmethod
    def _public_task_stage(resume_stage: str) -> str:
        """把内部细粒度断点映射为现有任务状态阶段。"""
        if resume_stage == "media_analysis":
            return "media_analysis"
        if resume_stage in {"speech_cleanup", "creative_plan"}:
            return "editing"
        if resume_stage in {
            "creative_render",
            "creative_artifact",
            "ending",
            "ending_render",
            "ending_artifact",
        }:
            return "rendering"
        if resume_stage in {
            "cover_plan",
            "cover_generate",
            "cover_download",
            "review_output",
            "asset_create",
        }:
            return "quality_check"
        return "editing"
