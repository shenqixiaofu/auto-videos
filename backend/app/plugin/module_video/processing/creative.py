from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.logger import log

from .planner import (
    VideoCreativeEditingPlan,
    VideoCreativePlanner,
    VideoEditPlan,
)
from .render_contract import (
    VideoRenderProvider,
    VideoRenderResult,
    VideoRenderSubmission,
    VideoTimeline,
)
from .rendering import VideoRenderingStage
from .timeline import VideoTimelineBuilder

TaskCancelChecker = Callable[[int], Awaitable[None]]
TaskStatusUpdater = Callable[[int, str, int | None, str | None, str | None], Awaitable[None]]
CreativePlanCheckpointWriter = Callable[[VideoCreativeEditingPlan], Awaitable[None]]
CreativeRenderCheckpointWriter = Callable[
    [VideoCreativeEditingPlan, VideoTimeline, VideoRenderSubmission],
    Awaitable[None],
]


@dataclass(slots=True)
class VideoCreativeEditingResult:
    """创意贴纸和动画阶段结果。"""

    creative_plan: VideoCreativeEditingPlan
    timeline: VideoTimeline
    submit_result: VideoRenderSubmission
    render_result: VideoRenderResult
    enhanced_video_url: str

    def to_metadata(self) -> dict[str, Any]:
        """序列化为任务元数据。"""
        return {
            "creative_plan": self.creative_plan.to_dict(),
            "timeline": self.timeline.to_metadata(),
            "submit_result": self.submit_result.to_metadata(),
            "render_result": self.render_result.to_metadata(),
            "enhanced_video_url": self.enhanced_video_url,
        }


class VideoCreativeEditingStage:
    """创意时间线阶段：贴纸、卡片和动画。"""

    @classmethod
    async def run(
        cls,
        *,
        task_id: int,
        task_no: str,
        task_title: str,
        edit_plan: VideoEditPlan,
        provider: VideoRenderProvider,
        source_url: str,
        source_path: Path,
        utterances: list[dict[str, Any]],
        subtitle_utterances: list[dict[str, Any]],
        bgm_asset: dict[str, Any] | None,
        ensure_not_cancelled: TaskCancelChecker,
        set_task_status: TaskStatusUpdater,
        save_creative_plan: CreativePlanCheckpointWriter,
        save_creative_submission: CreativeRenderCheckpointWriter | None = None,
        creative_plan_override: VideoCreativeEditingPlan | None = None,
        task_label: str = "创意时间线渲染",
        submit_progress: int = 30,
        render_progress: int = 35,
    ) -> VideoCreativeEditingResult:
        """先规划结构化事件，再构建并提交确定性时间线。"""
        if creative_plan_override is not None:
            creative_plan = creative_plan_override
        else:
            creative_plan = await VideoCreativePlanner.build_creative_editing_plan(
                task_no=task_no,
                task_title=task_title,
                style_preset=edit_plan.style_preset,
                adjustment_prompt=edit_plan.adjustment_prompt,
                source_duration_ms=edit_plan.source_duration_ms,
                # 创意规划保持原始句段，避免字幕切分影响贴纸事件。
                utterances=utterances,
            )
            # 关键词提取失败会整体降级为空关键词，只影响高亮，不阻断主链。
            subtitle_keywords = await VideoCreativePlanner.extract_subtitle_keywords(
                task_no=task_no,
                subtitle_utterances=subtitle_utterances,
            )
            creative_plan.subtitle_keywords = subtitle_keywords
        edit_plan.sticker_events = [
            event.to_dict()
            for event in creative_plan.sticker_events
        ]
        edit_plan.animation_events = [
            event.to_dict()
            for event in creative_plan.animation_events
        ]
        edit_plan.effects = [
            *edit_plan.sticker_events,
            *edit_plan.animation_events,
            *[event.to_dict() for event in creative_plan.graphic_sticker_events],
        ]
        # 先保存创意计划，渲染失败时只重提交时间线，不重新调用规划模型。
        await save_creative_plan(creative_plan)
        timeline = VideoTimelineBuilder.build_creative_timeline(
            source_url=source_url,
            edit_plan=edit_plan,
            creative_plan=creative_plan,
            # 时间线字幕只使用已切分的字幕句段。
            subtitle_utterances=subtitle_utterances,
            subtitle_keywords=creative_plan.subtitle_keywords,
            bgm_asset=bgm_asset,
        )
        subtitle_count, subtitle_max_chars = cls._subtitle_metrics(timeline)

        await ensure_not_cancelled(task_id)
        await set_task_status(
            task_id=task_id,
            status="processing",
            progress=submit_progress,
            current_stage="editing",
        )
        submit_result = await provider.submit_timeline_render(
            timeline=timeline,
            client_token=cls._build_client_token(task_no, edit_plan, "creative"),
            source_path=source_path,
        )
        if save_creative_submission is not None:
            # 提交成功后立即持久化渲染 ID 和时间线，失败时也能精确追查到云端任务。
            await save_creative_submission(creative_plan, timeline, submit_result)
        log.info(
            f"{task_label}任务已提交: "
            f"task_id={task_id}, provider={submit_result.provider}, "
            f"render_id={submit_result.render_id}, "
            f"sticker_count={len(creative_plan.sticker_events)}, "
            f"animation_count={len(creative_plan.animation_events)}, "
            f"graphic_sticker_count={len(creative_plan.graphic_sticker_events)}, "
            f"subtitle_count={subtitle_count}, "
            f"subtitle_max_chars={subtitle_max_chars}"
        )
        render_result = await VideoRenderingStage.wait_for_video_output(
            task_id=task_id,
            provider=provider,
            render_id=submit_result.render_id,
            progress=render_progress,
            task_label=task_label,
            ensure_not_cancelled=ensure_not_cancelled,
            set_task_status=set_task_status,
        )
        enhanced_video_url = render_result.ensure_video_url()
        return VideoCreativeEditingResult(
            creative_plan=creative_plan,
            timeline=timeline,
            submit_result=submit_result,
            render_result=render_result,
            enhanced_video_url=enhanced_video_url,
        )

    @staticmethod
    def _subtitle_metrics(timeline: VideoTimeline) -> tuple[int, int]:
        """统计即将提交的实际字幕片段数量和最大可见字符数。"""
        subtitle_clips = [
            clip
            for track in timeline.tracks
            for clip in track
            if clip.asset.get("kind") == "subtitle"
        ]
        subtitle_max_chars = max(
            (
                len("".join(str(clip.asset.get("text") or "").split()))
                for clip in subtitle_clips
            ),
            default=0,
        )
        return len(subtitle_clips), subtitle_max_chars

    @staticmethod
    def _build_client_token(task_no: str, edit_plan: VideoEditPlan, stage: str) -> str:
        """按处理阶段生成稳定的渲染标识。"""
        token_digest = hashlib.sha1(
            f"{edit_plan.seed}:{stage}".encode()
        ).hexdigest()[:12]
        return f"{task_no[:32]}-v{edit_plan.version}-{stage}-{token_digest}"
