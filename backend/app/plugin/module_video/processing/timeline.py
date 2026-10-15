from __future__ import annotations

from typing import Any

from app.core.exceptions import CustomException

from .planner import VideoCreativeEditingPlan
from .render_contract import VideoRenderOutput, VideoTimeline, VideoTimelineClip
from .sticker_themes import pick_sticker_theme
from .timeline_parts.aliyun import to_aliyun_timeline
from .timeline_parts.layout import (
    apply_animation_events,
    build_audio_tracks,
    build_effect_sticker_clips,
    build_graphic_sticker_clip,
    build_sticker_clips,
    build_subtitle_clips,
    plan_sticker_layouts,
)


class VideoTimelineBuilder:
    """时间线构建 facade，细节拆分到 timeline_parts。"""

    # 人声优先靠两条轨的 Loudness 差值表达，而不是 Volume 增益。
    # 平台效果顺序固定为 ADenoise > Volume > ALoudNorm，ALoudNorm 在最后，
    # 用 Volume 抬人声会被它抹平，所以差值只能写在 Loudness target 上。
    _voice_loudness_target = -16.0
    _bgm_loudness_target = -24.0
    _audio_true_peak = -2.0
    _output_sizes = {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1080, 1080),
    }
    _animation_effects = {
        "soft_pop": "soft_pop",
        "slide_up": "slide_up",
        "fade_in": "fade_in",
        "subtle_zoom": "subtle_zoom",
    }

    @classmethod
    def build_creative_timeline(
        cls,
        *,
        source_url: str,
        edit_plan,
        creative_plan: VideoCreativeEditingPlan,
        subtitle_utterances: list[dict[str, Any]],
        subtitle_keywords: list[list[str]] | None = None,
        bgm_asset: dict[str, Any] | None = None,
        subtitle_style: dict[str, Any] | None = None,
    ) -> VideoTimeline:
        """生成源视频加创意覆盖层的完整时间线。"""
        if not source_url:
            raise CustomException(msg="时间线渲染缺少 source_url")

        width, height = cls._output_sizes[edit_plan.aspect_ratio]
        duration_seconds = edit_plan.source_duration_ms / 1000
        task_theme = pick_sticker_theme(edit_plan.seed, edit_plan.style_preset)
        source_clip = VideoTimelineClip(
            asset={
                "kind": "video",
                "src": source_url,
                # 原视频先降噪，再按人声 Loudness target 做归一化。
                "denoise_mode": 3,
                "loudness": cls._voice_loudness_target,
                "true_peak": cls._audio_true_peak,
            },
            start_seconds=0.0,
            length_seconds=duration_seconds,
            metadata={"role": "source"},
        )
        subtitle_clips = build_subtitle_clips(
            # 字幕轨使用切分后的句段，贴纸规划仍在上层使用原始句段。
            utterances=subtitle_utterances,
            task_seed=edit_plan.seed,
            theme_id=task_theme.id,
            subtitle_keywords=subtitle_keywords,
        )
        sticker_layouts = plan_sticker_layouts(
            events=creative_plan.sticker_events,
            task_seed=edit_plan.seed,
        )
        sticker_clips: list[VideoTimelineClip] = []
        for event in creative_plan.sticker_events:
            layout_side, placement = sticker_layouts.get(event.id, (None, None))
            sticker_clips.extend(
                build_sticker_clips(
                    event,
                    task_theme,
                    edit_plan.seed,
                    layout_side_override=layout_side,
                    placement_override=placement,
                )
            )
        apply_animation_events(
            sticker_clips=sticker_clips,
            animation_events=creative_plan.animation_events,
            animation_effects=cls._animation_effects,
        )
        # 图形贴纸走独立的图片轨，不和文字贴纸共用 SubtitleTracks。
        graphic_sticker_clips = [
            build_graphic_sticker_clip(event, edit_plan.seed)
            for event in creative_plan.graphic_sticker_events
        ]
        # 氛围装饰再单独一条轨，时间上避开所有贴纸，互不挤压。
        effect_sticker_clips = build_effect_sticker_clips(
            timeline_duration_seconds=duration_seconds,
            blocked_windows=[
                (event.start_ms / 1000, event.end_ms / 1000)
                for event in (
                    creative_plan.graphic_sticker_events + creative_plan.sticker_events
                )
            ],
            task_seed=edit_plan.seed,
        )
        audio_tracks = build_audio_tracks(
            timeline_duration_seconds=duration_seconds,
            bgm_asset=bgm_asset,
            loudness=cls._bgm_loudness_target,
            true_peak=cls._audio_true_peak,
        )
        return VideoTimeline(
            duration_seconds=duration_seconds,
            tracks=[
                [source_clip],
                subtitle_clips,
                sticker_clips,
                graphic_sticker_clips,
                effect_sticker_clips,
            ],
            output=VideoRenderOutput(
                width=width,
                height=height,
                fps=25,
                aspect_ratio=edit_plan.aspect_ratio,
            ),
            audio_tracks=audio_tracks,
            metadata={
                "builder": "video-timeline-v1",
                "style_preset": edit_plan.style_preset,
                # 字幕样式是渲染参数，跟着时间线走：阿里侧只从 metadata 取，不再回查配置。
                "subtitle_style": dict(subtitle_style or {}),
                "sticker_theme_id": task_theme.id,
                "sticker_count": len(creative_plan.sticker_events),
                "animation_count": len(creative_plan.animation_events),
                "graphic_sticker_count": len(creative_plan.graphic_sticker_events),
                "effect_sticker_count": len(effect_sticker_clips),
                "bgm_enabled": bgm_asset is not None,
                "audio_mix": {
                    "voice_loudness_target": cls._voice_loudness_target,
                    "bgm_loudness_target": cls._bgm_loudness_target,
                    "true_peak": cls._audio_true_peak,
                },
            },
        )

    @staticmethod
    def to_aliyun_timeline(timeline: VideoTimeline) -> dict[str, Any]:
        """把中立时间线转换为阿里 IMS Timeline。"""
        return to_aliyun_timeline(timeline)


def timeline_to_provider_metadata(timeline: VideoTimeline) -> dict[str, Any]:
    """提供统一入口保存时间线元数据。"""
    return timeline.to_metadata()
