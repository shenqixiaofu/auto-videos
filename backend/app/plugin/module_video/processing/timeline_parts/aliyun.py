from __future__ import annotations

from typing import Any

from app.core.exceptions import CustomException

from ..render_contract import VideoTimeline, VideoTimelineClip
from ..sticker_themes import StickerThemeStyle
from .layout import card_style, card_text, motion_config, placement_config

_subtitle_bottom_y = 140
_subtitle_text_width = 0.72
_subtitle_font_size = 56


def to_aliyun_timeline(timeline: VideoTimeline) -> dict[str, Any]:
    """把中立时间线转换为阿里 IMS Timeline。"""
    video_clips: list[dict[str, Any]] = []
    image_clips: list[dict[str, Any]] = []
    subtitle_track_clips: list[dict[str, Any]] = []
    sticker_track_clips: list[dict[str, Any]] = []
    audio_track_payloads: list[dict[str, Any]] = []
    for track in timeline.tracks:
        for clip in track:
            kind = str(clip.asset.get("kind") or "")
            if kind == "video":
                video_clips.append(to_aliyun_video_clip(clip))
            elif kind == "subtitle":
                subtitle_track_clips.append(to_aliyun_subtitle_clip(clip))
            elif kind == "text_card":
                sticker_track_clips.append(to_aliyun_text_clip(clip))
            elif kind in {"graphic_sticker", "effect_sticker"}:
                image_clips.append(
                    to_aliyun_image_clip(
                        clip,
                        output_width=timeline.output.width,
                        output_height=timeline.output.height,
                    )
                )
            else:
                raise CustomException(msg=f"阿里 Timeline 不支持的资产类型: {kind}")
    for audio_track in timeline.audio_tracks:
        audio_clips: list[dict[str, Any]] = []
        for clip in audio_track:
            kind = str(clip.asset.get("kind") or "")
            if kind != "audio":
                raise CustomException(msg=f"阿里 Timeline 不支持的音频资产类型: {kind}")
            audio_clips.append(to_aliyun_audio_clip(clip))
        if audio_clips:
            audio_track_payloads.append({"AudioTrackClips": audio_clips})

    if not video_clips:
        raise CustomException(msg="阿里 Timeline 缺少视频轨道")
    video_tracks: list[dict[str, Any]] = [{"VideoTrackClips": video_clips}]
    if image_clips:
        # 每个图片 clip 必须独占一条 VideoTracks。同轨多 clip 时，带 Transition 的
        # clip 会把轨内**后面所有 clip 整条吃掉**（实测 3 个 clip 只剩第 1 个），
        # 所以不能图省事合并。19 条轨实测可正常出片。
        video_tracks.extend({"VideoTrackClips": [clip]} for clip in image_clips)
    timeline_payload: dict[str, Any] = {
        "VideoTracks": video_tracks,
    }
    subtitle_tracks: list[dict[str, Any]] = []
    if subtitle_track_clips:
        subtitle_tracks.append({"SubtitleTrackClips": subtitle_track_clips})
    if sticker_track_clips:
        subtitle_tracks.append({"SubtitleTrackClips": sticker_track_clips})
    if subtitle_tracks:
        timeline_payload["SubtitleTracks"] = subtitle_tracks
    if audio_track_payloads:
        timeline_payload["AudioTracks"] = audio_track_payloads
    return timeline_payload


def to_aliyun_video_clip(clip: VideoTimelineClip) -> dict[str, Any]:
    """转换阿里视频轨片段。

    `In`/`Out` 是**素材内部**的裁切点，不是时间线位置 —— 同一条轨上多个 clip
    的先后由数组顺序决定。这里必须用 source_offset_seconds，用 start_seconds
    会让第二个 clip 从素材很靠后的位置开始读（片尾拼接踩过这个坑）。
    """
    source_offset = float(clip.source_offset_seconds)
    payload: dict[str, Any] = {
        "MediaURL": str(clip.asset["src"]),
        "In": round(source_offset, 3),
        "Out": round(source_offset + clip.length_seconds, 3),
    }
    effects: list[dict[str, Any]] = []
    denoise_mode = clip.asset.get("denoise_mode")
    if denoise_mode is not None:
        # 降噪必须放在音量调整前面，避免把噪声和人声一起抬上去。
        effects.append(
            {
                "Type": "ADenoise",
                "Mode": int(denoise_mode),
            }
        )
    voice_gain = clip.asset.get("voice_gain")
    if voice_gain:
        effects.append(
            {
                "Type": "Volume",
                "Gain": round(float(voice_gain), 3),
            }
        )
    loudnorm_effect = loudnorm_effect_payload(clip.asset)
    if loudnorm_effect is not None:
        effects.append(loudnorm_effect)
    if effects:
        payload["Effects"] = effects
    return payload


def to_aliyun_audio_clip(clip: VideoTimelineClip) -> dict[str, Any]:
    """转换阿里音频轨片段。"""
    media_url = str(clip.asset.get("media_url") or "").strip()
    if not media_url:
        raise CustomException(msg="阿里音频片段缺少正式 media_url")
    loop_mode = bool(clip.asset.get("loop_mode"))
    payload: dict[str, Any] = {
        "MediaURL": media_url,
        "TimelineIn": round(clip.start_seconds, 3),
        "TimelineOut": round(clip.start_seconds + clip.length_seconds, 3),
        "LoopMode": loop_mode,
    }
    duration_seconds = clip.asset.get("duration_seconds")
    if duration_seconds and not loop_mode:
        # 循环 BGM 交给阿里按时间线自动铺满，避免单曲时长略短于成片时触发生产失败。
        payload["In"] = 0
        payload["Out"] = round(float(duration_seconds), 3)
    effects = audio_effects_payload(clip)
    if effects:
        payload["Effects"] = effects
    return payload


def to_aliyun_image_clip(
    clip: VideoTimelineClip,
    *,
    output_width: int,
    output_height: int,
) -> dict[str, Any]:
    """转换阿里图片轨片段（公共素材库图形贴纸）。

    两条实测约束，改之前先看这里：
    1. MediaURL 带查询串会让这一整帧变灰，只能用无签名公开地址；
    2. 只吃 GIF，PNG/JPEG/WebP 同样会让整帧变灰，1 帧 GIF 就够，不需要动画。
    """
    media_url = str(clip.asset.get("media_url") or "").strip()
    if not media_url:
        raise CustomException(msg="阿里图形贴纸片段缺少 media_url")
    if "?" in media_url:
        raise CustomException(msg=f"阿里图形贴纸 MediaURL 不能带查询串: {media_url}")
    size_px = max(2, round(output_width * float(clip.asset.get("size_ratio") or 0.30)))
    payload: dict[str, Any] = {
        "MediaURL": media_url,
        "Type": "Image",
        "X": max(0, round(output_width * float(clip.asset.get("slot_x") or 0.0))),
        "Y": max(0, round(output_height * float(clip.asset.get("slot_y") or 0.0))),
        "Width": size_px,
        "Height": size_px,
        "TimelineIn": round(clip.start_seconds, 3),
        "TimelineOut": round(clip.start_seconds + clip.length_seconds, 3),
    }
    # Image 类型不支持 AaiMotion（那是 SubtitleTrackClip 的字段），要动效只能走 Effects。
    effects = clip.asset.get("effects")
    if effects:
        payload["Effects"] = [dict(effect) for effect in effects]
    return payload


def to_aliyun_text_clip(clip: VideoTimelineClip) -> dict[str, Any]:
    """转换阿里文字卡片片段。"""
    template_id = str(clip.asset.get("template_id") or "")
    text_mode = str(clip.asset.get("text_mode") or "")
    is_chip = text_mode == "word_art_chip"
    motion_duration = float(clip.asset.get("motion_duration") or (0.55 if is_chip else 0.7))
    text = card_text(clip.asset)
    x, y, text_width, alignment = placement_config(
        placement=clip.placement,
        template_id=template_id,
        asset=clip.asset,
    )
    style = card_style(clip.asset)
    motion_in, motion_out = motion_config(
        clip.transition_in,
        clip.transition_out,
        clip.effect,
    )
    payload: dict[str, Any] = {
        "TimelineIn": round(clip.start_seconds, 3),
        "TimelineOut": round(clip.start_seconds + clip.length_seconds, 3),
        "Type": "Text",
        "X": x,
        "Y": y,
        "Content": text,
        "AdaptMode": "AutoScale" if is_chip else "AutoWrap",
        "TextWidth": text_width,
        "Alignment": alignment,
        "FontSize": style.font_size,
        **text_effect_payload(style),
    }
    payload["AaiMotionInEffect"] = motion_in
    payload["AaiMotionIn"] = motion_duration
    payload["AaiMotionOutEffect"] = motion_out
    payload["AaiMotionOut"] = motion_duration
    return payload


def to_aliyun_subtitle_clip(clip: VideoTimelineClip) -> dict[str, Any]:
    """转换阿里底部静态普通字幕片段。"""
    text = str(clip.asset.get("text") or "").strip()
    if not text:
        raise CustomException(msg="阿里字幕片段缺少 text")
    highlight_keywords = [
        str(keyword).strip()
        for keyword in (clip.asset.get("highlight_keywords") or [])
        if str(keyword).strip()
    ]
    if not highlight_keywords:
        highlight_keyword = str(clip.asset.get("highlight_keyword") or "").strip()
        if highlight_keyword:
            highlight_keywords = [highlight_keyword]
    return {
        "TimelineIn": round(clip.start_seconds, 3),
        "TimelineOut": round(clip.start_seconds + clip.length_seconds, 3),
        "Type": "Text",
        "X": 0,
        "Y": _subtitle_bottom_y,
        # 底部字幕对 1 到 2 个命中片段做局部 override，高亮不到就回退原文。
        "Content": apply_subtitle_highlight_override(
            text=text,
            keywords=highlight_keywords,
            highlight_color=str(clip.asset.get("highlight_color") or "#6EE7FF"),
            outline_color=str(clip.asset.get("highlight_outline_colour") or "#0F172A"),
        ),
        "Font": "HappyZcool-2016",
        "AdaptMode": "AutoWrap",
        "TextWidth": _subtitle_text_width,
        "Alignment": "BottomCenter",
        "FontSize": _subtitle_font_size,
        "FontColor": str(clip.asset.get("subtitle_color") or "#FFD452"),
        "Outline": 2,
        "OutlineColour": str(clip.asset.get("outline_colour") or "#1B130B"),
        "FontFace": {"Bold": True},
    }


def text_effect_payload(style: StickerThemeStyle) -> dict[str, Any]:
    """下发花字样式。

    两条互斥路线，别同时用：
    - 主题配了 `word_art_style` -> 走官方花字预设（`EffectColorStyle`），预设自带多层描边；
    - 否则走自绘 `SubtitleEffects` 三层（发光 + 深色压边 + 亮色内圈）。
    同时下发会描边套描边，颜色发脏。
    """
    payload: dict[str, Any] = {
        "Font": style.font,
        "FontColor": style.font_color,
        "FontFace": {"Bold": True},
    }
    if style.word_art_style:
        # 官方花字字段名是 EffectColorStyle，不是 EffectColorStyleId，写错静默不生效。
        payload["EffectColorStyle"] = style.word_art_style
    elif style.effects:
        payload["SubtitleEffects"] = [layer.to_dict() for layer in style.effects]
    opacity = parse_opacity(style.opacity)
    if opacity is not None:
        payload["FontColorOpacity"] = opacity
    return payload


def parse_opacity(opacity: str | None) -> float | None:
    """把主题里的不透明度字符串转成阿里需要的浮点数。"""
    if not opacity:
        return None
    try:
        return round(float(opacity), 3)
    except ValueError:
        return None


def apply_subtitle_highlight_override(
    *,
    text: str,
    keywords: list[str],
    highlight_color: str,
    outline_color: str,
) -> str:
    """把命中的关键词包装成阿里字幕局部高亮文本。"""
    normalized_keywords = [keyword for keyword in dict.fromkeys(keywords) if keyword and keyword in text]
    if not normalized_keywords:
        return text
    # 只做变色加粗，不动字号：同屏字号突变会撑开行高，看起来比不变色还差。
    keyword_prefix = (
        "{"
        f"\\1c&H{rgb_hex_to_bgr(highlight_color)}&"
        f"\\3c&H{rgb_hex_to_bgr(outline_color)}&"
        "\\b1"
        "}"
    )
    keyword_suffix = "{\\1c\\3c\\b0}"
    highlighted = text
    for keyword in sorted(normalized_keywords, key=len, reverse=True)[:2]:
        highlighted = highlighted.replace(keyword, f"{keyword_prefix}{keyword}{keyword_suffix}", 1)
    return highlighted


def rgb_hex_to_bgr(colour: str) -> str:
    """把 #RRGGBB 转成阿里字幕 override 需要的 BGR 十六进制。"""
    normalized = str(colour).strip().lstrip("#")
    if len(normalized) != 6:
        raise CustomException(msg=f"字幕高亮颜色格式错误: {colour}")
    return f"{normalized[4:6]}{normalized[2:4]}{normalized[0:2]}".upper()


def audio_effects_payload(clip: VideoTimelineClip) -> list[dict[str, Any]]:
    """输出阿里音频轨的音量和淡入淡出效果。"""
    effects: list[dict[str, Any]] = []
    volume_gain = clip.asset.get("volume_gain")
    if volume_gain is not None and float(volume_gain) != 1.0:
        effects.append(
            {
                "Type": "Volume",
                "Gain": round(float(volume_gain), 3),
            }
        )
    loudnorm_effect = loudnorm_effect_payload(clip.asset)
    if loudnorm_effect is not None:
        effects.append(loudnorm_effect)
    fade_in_seconds = float(clip.asset.get("fade_in_seconds") or 0)
    fade_out_seconds = float(clip.asset.get("fade_out_seconds") or 0)
    if fade_in_seconds > 0:
        effects.append(
            {
                "Type": "AFade",
                "SubType": "In",
                "Duration": round(fade_in_seconds, 3),
                "Curve": "tri",
            }
        )
    if fade_out_seconds > 0:
        effects.append(
            {
                "Type": "AFade",
                "SubType": "Out",
                "Duration": round(fade_out_seconds, 3),
                "Curve": "tri",
            }
        )
    return effects


def loudnorm_effect_payload(asset: dict[str, Any]) -> dict[str, Any] | None:
    """构造阿里响度归一化效果。"""
    loudness = asset.get("loudness")
    if loudness is None:
        return None
    payload: dict[str, Any] = {
        "Type": "ALoudNorm",
        "Loudness": round(float(loudness), 1),
    }
    true_peak = asset.get("true_peak")
    if true_peak is not None:
        payload["TruePeak"] = round(float(true_peak), 1)
    return payload
