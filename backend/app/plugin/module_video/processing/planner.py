"""创意规划门面。

实现拆在 `planner_models`（事件模型）与 `planner_creative`（模型编排）里，
本模块只保留 `VideoEditPlanner` 并对外转发原有符号，调用方无需改动。
"""

from __future__ import annotations

from typing import Any

from .planner_creative import VideoCreativePlanner
from .planner_models import (
    VideoCreativeAnimationEvent,
    VideoCreativeEditingPlan,
    VideoCreativeGraphicStickerEvent,
    VideoCreativeStickerEvent,
    VideoEditPlan,
    VideoEditSegment,
)
from .render_contract import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_STYLE_PRESET,
    STYLE_PRESET_LABELS,
)

__all__ = [
    "VideoCreativeAnimationEvent",
    "VideoCreativeEditingPlan",
    "VideoCreativeGraphicStickerEvent",
    "VideoCreativePlanner",
    "VideoCreativeStickerEvent",
    "VideoEditPlan",
    "VideoEditPlanner",
    "VideoEditSegment",
]


class VideoEditPlanner:
    """智能视频剪辑计划生成器。"""

    @staticmethod
    def build_source_only_plan(
        task_no: str,
        config: dict[str, Any],
        source_duration_ms: int,
    ) -> VideoEditPlan:
        """生成当前 MVP 的源视频目标计划，素材扩展不作为用户前置要求。"""
        version = int(config.get("review_version") or 1)
        # 风格是装饰性字段：库里出现历史值或未知值时回落默认，不让响应 schema 校验炸掉列表。
        style_preset = str(config.get("style_preset") or "")
        if style_preset not in STYLE_PRESET_LABELS:
            style_preset = DEFAULT_STYLE_PRESET
        seed = str(config.get("review_seed") or f"{task_no}:v{version}:{style_preset}")
        adjustment_prompt = str(config.get("adjustment_prompt") or "")

        return VideoEditPlan(
            version=version,
            seed=seed,
            aspect_ratio=DEFAULT_ASPECT_RATIO,
            style_preset=style_preset,
            # 当前成片固定带字幕，历史配置里的旧开关不再生效。
            subtitle_enabled=True,
            adjustment_prompt=adjustment_prompt,
            source_duration_ms=source_duration_ms,
            segments=[
                VideoEditSegment(
                    id="source-full",
                    source_start_ms=0,
                    source_end_ms=source_duration_ms,
                    target_start_ms=0,
                    target_end_ms=source_duration_ms,
                )
            ],
            transitions=[],
            effects=[],
            sticker_events=[],
            animation_events=[],
            # 当前字幕 MVP 不主动添加 BGM，避免火山自动引用不可用的音乐媒资。
            music=None,
            intro=None,
            ending=None,
        )
