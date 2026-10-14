from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class VideoCreativeStickerEvent:
    """创意贴纸事件。"""

    id: str
    template_id: str
    start_ms: int
    end_ms: int
    text: str
    placement: str
    scale: float = 1.0
    rotation: float = 0.0
    title_text: str | None = None
    body_text: str | None = None
    card_style: str | None = None
    anchor_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """序列化为可落库的字典。"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "text": self.text,
            "placement": self.placement,
            "scale": self.scale,
            "rotation": self.rotation,
            "title_text": self.title_text,
            "body_text": self.body_text,
            "card_style": self.card_style,
            "anchor_text": self.anchor_text,
        }


@dataclass(slots=True)
class VideoCreativeAnimationEvent:
    """创意动画事件。"""

    id: str
    template_id: str
    start_ms: int
    end_ms: int
    description: str
    placement: str
    intensity: str = "medium"
    scale: float = 1.0
    rotation: float = 0.0
    anchor_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """序列化为可落库的字典。"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "description": self.description,
            "placement": self.placement,
            "intensity": self.intensity,
            "scale": self.scale,
            "rotation": self.rotation,
            "anchor_text": self.anchor_text,
        }


@dataclass(slots=True)
class VideoCreativeGraphicStickerEvent:
    """图形贴纸事件。

    素材来自阿里公共素材库的纯图形贴纸，不带文字，因此无法承载观点，
    只能按情绪基调（tone）挑选，用来烘托画面氛围。
    """

    id: str
    tone: str
    start_ms: int
    end_ms: int
    placement: str
    scale: float = 1.0
    rotation: float = 0.0
    anchor_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """序列化为可落库的字典。"""
        return {
            "id": self.id,
            "tone": self.tone,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "placement": self.placement,
            "scale": self.scale,
            "rotation": self.rotation,
            "anchor_text": self.anchor_text,
        }


@dataclass(slots=True)
class VideoCreativeEditingPlan:
    """创意时间线规划结果。"""

    summary: str | None
    sticker_events: list[VideoCreativeStickerEvent]
    animation_events: list[VideoCreativeAnimationEvent]
    graphic_sticker_events: list[VideoCreativeGraphicStickerEvent] = field(default_factory=list)
    # 按字幕片段顺序对齐的关键词，供底部字幕局部高亮使用。
    subtitle_keywords: list[list[str]] = field(default_factory=list)
    # 本次实际调用的规划模型。全局配置可覆盖 env，调试面板要显示真正生效的那个。
    planner_model: str | None = None
    # 本次实际发给模型的 system / user 提示词全文。提示词可在高级设置里改，
    # 只记模板没法还原「这一条任务当时到底发了什么」，调试必须看到成品串。
    system_prompt: str | None = None
    user_prompt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """序列化为 review 资产元数据。"""
        return {
            "summary": self.summary,
            "sticker_events": [event.to_dict() for event in self.sticker_events],
            "animation_events": [event.to_dict() for event in self.animation_events],
            "graphic_sticker_events": [
                event.to_dict() for event in self.graphic_sticker_events
            ],
            "subtitle_keywords": [list(keywords) for keywords in self.subtitle_keywords],
            "planner_model": self.planner_model,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
        }

    @classmethod
    def empty(cls) -> VideoCreativeEditingPlan:
        """返回空创意计划，供仅字幕/BGM 时间线渲染复用。"""
        return cls(
            summary=None,
            sticker_events=[],
            animation_events=[],
            graphic_sticker_events=[],
            subtitle_keywords=[],
        )


@dataclass(slots=True)
class VideoEditSegment:
    """剪辑片段，记录源视频区间和目标时间线区间。"""

    id: str
    source_start_ms: int
    source_end_ms: int
    target_start_ms: int
    target_end_ms: int

    def to_dict(self) -> dict[str, Any]:
        """序列化为可写入任务元数据的字典。"""
        return {
            "id": self.id,
            "source_start_ms": self.source_start_ms,
            "source_end_ms": self.source_end_ms,
            "target_start_ms": self.target_start_ms,
            "target_end_ms": self.target_end_ms,
        }


@dataclass(slots=True)
class VideoEditPlan:
    """后端生成的处理计划，当前由云端字幕工作流消费。"""

    version: int
    seed: str
    aspect_ratio: str
    style_preset: str
    subtitle_enabled: bool
    adjustment_prompt: str
    source_duration_ms: int
    segments: list[VideoEditSegment]
    transitions: list[dict[str, Any]]
    effects: list[dict[str, Any]]
    sticker_events: list[dict[str, Any]]
    animation_events: list[dict[str, Any]]
    music: dict[str, Any] | None
    intro: dict[str, Any] | None
    ending: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        """序列化为 review 资产元数据，方便审核和重渲染追溯。"""
        return {
            "version": self.version,
            "seed": self.seed,
            "aspect_ratio": self.aspect_ratio,
            "style_preset": self.style_preset,
            "subtitle_enabled": self.subtitle_enabled,
            "adjustment_prompt": self.adjustment_prompt,
            "source_duration_ms": self.source_duration_ms,
            "segments": [segment.to_dict() for segment in self.segments],
            "transitions": self.transitions,
            "effects": self.effects,
            "sticker_events": self.sticker_events,
            "animation_events": self.animation_events,
            "music": self.music,
            "intro": self.intro,
            "ending": self.ending,
        }
