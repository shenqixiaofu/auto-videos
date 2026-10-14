from __future__ import annotations

import hashlib
from typing import Any

from app.core.exceptions import CustomException
from app.core.logger import log

from ..planner import (
    VideoCreativeAnimationEvent,
    VideoCreativeGraphicStickerEvent,
    VideoCreativeStickerEvent,
)
from ..render_contract import VideoTimelineClip
from ..sticker_library import effect_pool, pick_effect, pick_sticker
from ..sticker_themes import (
    DEFAULT_STICKER_FONT,
    StickerEffectLayer,
    StickerTheme,
    StickerThemeStyle,
    pick_sticker_motion,
)

# 图形贴纸槽位按输出画布归一化存放，由 aliyun.py 换算成像素下发，y 是左上角。
#
# 版式分两条互不重叠的横带，这是「贴纸不压文字」的唯一保证，改槽位必须保持这个次序：
#   装饰带 —— 图形/氛围贴纸，y 起点 >= 0.660（底边最高 0.695*1920 + 324 = 1658）
#   文字带 —— 文字贴纸，y 起点 <= 0.585（最高的两行观点卡，字号 76，底边 1226）
# 两带之间留 41px 硬间隙。图形和文字本来就允许同屏，所以不能再靠「横带避让」兜底 ——
# 旧的 top/mid/bottom 横带模型与真实几何对不上：top_left 图形底边 1284 照样压在
# 观点卡顶边 1152 上（任务 137 第 9 秒就是这么叠的）。图形 y 一旦落回 0.66 以上，
# 重叠会静默回来，成片里才发现。
#
# 字幕实测顶边 1669（0.869），所以装饰带底边上限 = (1669 - 边长) / 1920。
_GRAPHIC_STICKER_SLOTS: dict[str, tuple[float, float]] = {
    "top_left": (0.040, 0.660),
    "top_right": (0.685, 0.660),
    "center": (0.400, 0.668),
    "mid_left": (0.040, 0.678),
    "mid_right": (0.685, 0.678),
    "bottom_left": (0.030, 0.695),
    "bottom_right": (0.685, 0.695),
    "lower_third": (0.685, 0.695),
}
# 贴纸是正方形，边长按画布宽度取比例，0.30 即 1080 宽下 324px。
# 右列 x 必须满足 x + 边长 <= 1（0.685 + 0.30 = 0.985），否则贴纸盒越出画布右边界被裁。
_GRAPHIC_STICKER_SIZE_RATIO = 0.30
# 图形贴纸只做入场过渡，不要 KenBurns：实测 KenBurns 会把 Image clip 连盒子一起
# 放大到约 3 倍撑满画面（1028x1502），版式全毁。Transition 不改尺寸和位置。
_GRAPHIC_STICKER_EFFECTS: tuple[dict[str, Any], ...] = (
    {"Type": "Transition", "SubType": "wiperight", "Duration": 0.6},
)

# 氛围装饰层：effect_pool 里的小装饰 GIF（圆圈/水滴/气泡/云朵/爱心/闪电/光斑），
# 独立一条图片轨，位置和时间都避开图形贴纸，只做「画面在动」的呼吸感。
# 三档全部落在装饰带（y >= 0.660），和图形贴纸一样压在字幕上方。
_EFFECT_STICKER_SLOTS: tuple[tuple[float, float], ...] = (
    (0.055, 0.660),
    (0.760, 0.660),
    (0.045, 0.710),
    (0.760, 0.710),
    (0.060, 0.755),
    (0.760, 0.755),
)
# 边长 0.13（1080 宽下 140px）时池里最小的那几个（小圆点 / 小三角）只剩十几像素、
# 基本看不见，所以放大到 0.20（216px）。最下一档底边 0.755*1920 + 216 = 1666px，
# 仍在字幕顶 1669px 之上；右列 0.760*1080 + 216 = 1037px 不出界。
_EFFECT_STICKER_SIZE_RATIO = 0.20
_EFFECT_STICKER_DURATION_SECONDS = 1.8
_EFFECT_STICKER_MIN_COUNT = 2
_EFFECT_STICKER_MAX_COUNT = 4
_EFFECT_STICKER_SECONDS_PER_SLOT = 22.0
_EFFECT_STICKER_EFFECTS: tuple[dict[str, Any], ...] = (
    {"Type": "Transition", "SubType": "wiperight", "Duration": 0.5},
)


def build_subtitle_clips(
    *,
    utterances: list[dict[str, Any]],
    task_seed: str,
    theme_id: str,
    subtitle_keywords: list[list[str]] | None = None,
) -> list[VideoTimelineClip]:
    """构造底部普通字幕轨。"""
    subtitle_color, outline_colour = pick_subtitle_palette(task_seed)
    highlight_color, highlight_outline_colour = pick_subtitle_highlight_palette(theme_id)
    keyword_groups = subtitle_keywords or []
    subtitle_clips: list[VideoTimelineClip] = []
    for index, utterance in enumerate(utterances, start=1):
        text = str(utterance.get("text") or "").strip()
        start_ms = int(utterance.get("start_ms") or 0)
        end_ms = int(utterance.get("end_ms") or start_ms)
        if not text or end_ms <= start_ms:
            continue
        # 关键词由规划阶段按语义提取，这里只做「原样出现」兜底校验并限两个。
        group = keyword_groups[index - 1] if index <= len(keyword_groups) else []
        highlight_keywords = [keyword for keyword in group if keyword and keyword in text][:2]
        subtitle_clips.append(
            VideoTimelineClip(
                asset={
                    "kind": "subtitle",
                    "text": text,
                    "subtitle_color": subtitle_color,
                    "outline_colour": outline_colour,
                    "highlight_keyword": highlight_keywords[0] if highlight_keywords else None,
                    "highlight_keywords": highlight_keywords,
                    "highlight_color": highlight_color,
                    "highlight_outline_colour": highlight_outline_colour,
                },
                start_seconds=start_ms / 1000,
                length_seconds=(end_ms - start_ms) / 1000,
                metadata={
                    "subtitle_index": index,
                    "subtitle_color": subtitle_color,
                    "highlight_keyword": highlight_keywords[0] if highlight_keywords else None,
                    "highlight_keywords": highlight_keywords,
                },
            )
        )
    return subtitle_clips


def build_audio_tracks(
    *,
    timeline_duration_seconds: float,
    bgm_asset: dict[str, Any] | None,
    loudness: float,
    true_peak: float,
) -> list[list[VideoTimelineClip]]:
    """构造公共版权音乐音频轨。"""
    if bgm_asset is None:
        return []
    # BGM 单独归一化到比人声更低的响度，人声优先靠两条轨的 Loudness 差值表达。
    audio_asset = {
        **bgm_asset,
        "loudness": loudness,
        "true_peak": true_peak,
    }
    # 曲库侧的 Volume 增益会被 ALoudNorm 抹平，移除以免下发无效效果。
    audio_asset.pop("volume_gain", None)
    return [
        [
            VideoTimelineClip(
                asset=audio_asset,
                start_seconds=0.0,
                length_seconds=timeline_duration_seconds,
                metadata={"role": "bgm"},
            )
        ]
    ]


def visible_text_length(text: str) -> int:
    """统计贴纸文字的可见字符数。"""
    return len("".join(text.split()))


def micro_sticker_text_width(asset: dict[str, Any]) -> float:
    """按小贴纸文字长度计算安全文字宽度。"""
    text_length = max(visible_text_length(card_text(asset)), 1)
    # 小贴纸宽度再收紧一档，避免短标签偶发被模型拉成长句时冲出屏幕。
    return round(min(0.46, max(0.28, 0.18 + text_length * 0.04)), 3)


def pick_subtitle_palette(task_seed: str) -> tuple[str, str]:
    """按任务种子稳定抽取字幕配色。"""
    palette_pool = (
        ("#FFD452", "#1B130B"),
        ("#F9E27D", "#22170A"),
        ("#FFE48C", "#24190C"),
        ("#FFF0A8", "#2B1A05"),
        ("#FCE77A", "#23160A"),
    )
    digest = hashlib.sha1(f"{task_seed}:subtitle_palette".encode()).hexdigest()
    return palette_pool[int(digest[:8], 16) % len(palette_pool)]


def pick_subtitle_highlight_palette(theme_id: str) -> tuple[str, str]:
    """按贴纸主题返回同色系字幕高亮配色。"""
    palette_map = {
        # 底部字幕默认是暖黄色系，高亮必须改走强对比色，避免看起来像没生效。
        "citrus_pop": ("#22D3EE", "#083344"),
        "mint_lift": ("#FB7185", "#4C0519"),
        "peach_energy": ("#34D399", "#052E16"),
        "cobalt_spark": ("#F97316", "#431407"),
        "cream_marker": ("#38BDF8", "#082F49"),
        "electric_punch": ("#A3E635", "#1A2E05"),
        "sunset_flash": ("#60A5FA", "#172554"),
        "neon_night": ("#F472B6", "#4A044E"),
    }
    palette = palette_map.get(theme_id)
    if palette is None:
        raise CustomException(msg=f"未知贴纸主题高亮配色: {theme_id}")
    return palette


def card_text(asset: dict[str, Any]) -> str:
    """组合观点卡和贴纸文案。"""
    title_text = str(asset.get("title_text") or "").strip()
    body_text = str(asset.get("body_text") or "").strip()
    if title_text and body_text:
        return f"{title_text}\n{body_text}"
    return str(asset.get("text") or "").strip()


def placement_config(
    *,
    placement: str,
    template_id: str,
    asset: dict[str, Any],
) -> tuple[float, float, float, str]:
    """把业务位置转换为阿里文字轨坐标。

    所有文字贴纸的 y 都收在文字带（<= 0.585），底边最高 1226px，给下面的装饰带
    （图形/氛围贴纸，y >= 0.660）留出 41px 硬间隙。抬高这一档是刻意的：装饰要靠近
    字幕，就只能让文字让出下半区，两者靠纵向分区而不是靠调度错开。
    """
    if template_id == "opinion_card":
        side = str(asset.get("layout_side") or "left")
        # 两行观点卡字号 76，行高 1.35 -> 底边 1018 + 205 = 1223px。
        if side == "right":
            return 0.55, 0.530, 0.42, "TopLeft"
        return 0.12, 0.530, 0.42, "TopLeft"
    if template_id == "micro_sticker":
        text_width = micro_sticker_text_width(asset)
        bubble_slot = str(asset.get("bubble_slot") or "mid")
        side = "right" if placement in {"mid_right", "bottom_right", "lower_third", "center"} else "left"
        # 三档整体上移：单行字号最大 76，底边 1123 + 103 = 1226px，仍不进装饰带。
        slot_y_map = {
            "upper": 0.505,
            "mid": 0.545,
            "lower": 0.585,
        }
        slot_x_jitter_map = {
            "upper": 0.01,
            "mid": 0.03,
            "lower": 0.05,
        }
        y = slot_y_map.get(bubble_slot, 0.545)
        x_jitter = slot_x_jitter_map.get(bubble_slot, 0.03)
        if side == "right":
            return round(max(0.05, 0.95 - text_width - x_jitter), 3), y, text_width, "TopLeft"
        return round(min(0.14, 0.05 + x_jitter), 3), y, text_width, "TopLeft"
    # 其余模板字号 46（行高 62px），底边最高 1123 + 62 = 1185px。
    placement_map = {
        "mid_left": (0.05, 0.530, 0.17, "TopLeft"),
        "mid_right": (0.78, 0.530, 0.17, "TopLeft"),
        "bottom_left": (0.08, 0.585, 0.18, "TopLeft"),
        "bottom_right": (0.74, 0.585, 0.18, "TopLeft"),
        "lower_third": (0.74, 0.585, 0.18, "TopLeft"),
        "center": (0.74, 0.560, 0.18, "TopLeft"),
    }
    return placement_map[placement]


def card_style(asset: dict[str, Any]) -> StickerThemeStyle:
    """读取卡片样式，优先使用模板池下发的视觉配置。"""
    style_payload = asset.get("visual_style")
    if isinstance(style_payload, dict):
        return StickerThemeStyle(
            font_size=int(style_payload["font_size"]),
            font_color=str(style_payload["font_color"]),
            opacity=str(style_payload["opacity"]),
            effects=tuple(
                StickerEffectLayer.from_dict(layer)
                for layer in style_payload.get("effects") or []
            ),
            # 加字体字段之前生成的历史任务没有这个键，回落到默认字体而不是抛错。
            font=str(style_payload.get("font") or DEFAULT_STICKER_FONT),
            word_art_style=str(style_payload.get("word_art_style") or "") or None,
        )
    raise CustomException(msg="贴纸视觉样式缺失")


def motion_config(
    transition_in: str | None,
    transition_out: str | None,
    effect: str | None,
) -> tuple[str, str]:
    """把中立动画名称映射为阿里字幕动画。"""
    effect_motion_pairs = {
        "soft_pop": ("zoomin_i", "fade_out"),
        "slide_up": ("wipe_up_in", "dissolve_out"),
        "fade_in": ("dissolve_in", "dissolve_out"),
        "subtle_zoom": ("zoomin_i", "dissolve_out"),
    }
    if effect in effect_motion_pairs:
        return effect_motion_pairs[effect]
    motion_in = transition_in or "dissolve_in"
    motion_out = transition_out or "dissolve_out"
    return motion_in, motion_out


def pick_text_motion_duration(template_id: str) -> float:
    """缩短文字贴纸动效时长，让入退场更利落。"""
    return 0.55 if template_id == "micro_sticker" else 0.7


def build_sticker_clips(
    event: VideoCreativeStickerEvent,
    task_theme: StickerTheme,
    task_seed: str,
    *,
    layout_side_override: str | None = None,
    placement_override: str | None = None,
) -> list[VideoTimelineClip]:
    """把单条贴纸事件转换成一个或多个阿里贴纸片段。"""
    style = task_theme.style_for_template(event.template_id)
    motion_variant = pick_sticker_motion(task_seed, event.template_id, event.id)
    layout_side = layout_side_override or (
        pick_edge_side(task_seed, event.id)
        if event.template_id == "opinion_card"
        else pick_bubble_side(task_seed, event.id)
    )
    bubble_slot = (
        pick_bubble_slot(task_seed, event.id)
        if event.template_id == "micro_sticker"
        else None
    )
    placement = placement_override or resolve_sticker_placement(
        event=event,
        task_seed=task_seed,
        layout_side=layout_side,
    )
    adjusted_style = layout_safe_style(
        template_id=event.template_id,
        style=style,
        text=event.text,
    )
    return [
        build_single_sticker_clip(
            event=event,
            style=adjusted_style,
            layout_side=layout_side,
            motion_variant=motion_variant,
            task_theme=task_theme,
            text_mode="word_art_card" if event.template_id == "opinion_card" else "word_art_chip",
            bubble_slot=bubble_slot,
            motion_duration=pick_text_motion_duration(event.template_id),
            placement=placement,
        )
    ]


def build_single_sticker_clip(
    *,
    event: VideoCreativeStickerEvent,
    style: StickerThemeStyle,
    layout_side: str | None,
    motion_variant: Any,
    task_theme: StickerTheme,
    text_mode: str,
    bubble_slot: str | None = None,
    motion_duration: float = 0.7,
    override_text: str | None = None,
    placement: str | None = None,
) -> VideoTimelineClip:
    """构造单个贴纸片段。"""
    return VideoTimelineClip(
        asset={
            "kind": "text_card",
            "template_id": event.template_id,
            "text": override_text or event.text,
            "title_text": event.title_text,
            "body_text": event.body_text,
            "card_style": event.card_style,
            "theme_id": task_theme.id,
            "text_mode": text_mode,
            "bubble_slot": bubble_slot,
            "motion_duration": motion_duration,
            "layout_side": layout_side,
            "visual_style": style.to_dict(),
        },
        start_seconds=event.start_ms / 1000,
        length_seconds=(event.end_ms - event.start_ms) / 1000,
        placement=placement or event.placement,
        scale=event.scale,
        rotation=event.rotation,
        transition_in=motion_variant.motion_in,
        transition_out=motion_variant.motion_out,
        effect=motion_variant.motion_effect,
        metadata={
            "event_id": event.id,
            "template_id": event.template_id,
            "theme_id": task_theme.id,
            "motion_variant_id": motion_variant.id,
            "layout_side": layout_side,
            "bubble_slot": bubble_slot,
            "text_mode": text_mode,
            "anchor_text": event.anchor_text,
        },
    )


def build_graphic_sticker_clip(
    event: VideoCreativeGraphicStickerEvent,
    task_seed: str,
) -> VideoTimelineClip:
    """把一条图形贴纸事件转成图片轨片段。

    抽图种子带事件 id：同一条视频里不同事件能抽到不同图，同一个事件必然稳定，
    可重放性不受影响。
    """
    slot_x, slot_y = _GRAPHIC_STICKER_SLOTS.get(
        event.placement,
        _GRAPHIC_STICKER_SLOTS["top_right"],
    )
    return VideoTimelineClip(
        asset={
            "kind": "graphic_sticker",
            "media_url": pick_sticker(event.tone, f"{task_seed}:{event.id}"),
            "tone": event.tone,
            "slot_x": slot_x,
            "slot_y": slot_y,
            "size_ratio": _GRAPHIC_STICKER_SIZE_RATIO,
            "effects": [dict(effect) for effect in _GRAPHIC_STICKER_EFFECTS],
        },
        start_seconds=event.start_ms / 1000,
        length_seconds=(event.end_ms - event.start_ms) / 1000,
        placement=event.placement,
        scale=event.scale,
        rotation=event.rotation,
        metadata={
            "event_id": event.id,
            "tone": event.tone,
            "anchor_text": event.anchor_text,
        },
    )


def build_effect_sticker_clips(
    *,
    timeline_duration_seconds: float,
    blocked_windows: list[tuple[float, float]],
    task_seed: str,
) -> list[VideoTimelineClip]:
    """构造氛围装饰层片段。

    素材池是公共库里的迷你装饰动图，只负责「画面在动」，不承载语义，
    所以时间上只要避开图形贴纸即可，不需要和事件对齐。
    """
    if not effect_pool() or timeline_duration_seconds <= 0:
        return []
    count = max(
        _EFFECT_STICKER_MIN_COUNT,
        min(_EFFECT_STICKER_MAX_COUNT, round(timeline_duration_seconds / _EFFECT_STICKER_SECONDS_PER_SLOT)),
    )
    segment = timeline_duration_seconds / count
    # 装饰之间也互斥：不然贴纸密集时它们会一起被推到最后一个空档，全挤在同一时刻。
    occupied = list(blocked_windows)
    clips: list[VideoTimelineClip] = []
    for index in range(count):
        digest = hashlib.sha1(f"{task_seed}:effect_slot:{index}".encode()).hexdigest()
        ratio = 0.15 + (int(digest[:8], 16) % 1000) / 1000 * 0.5
        start = _shift_past_blocked(
            index * segment + segment * ratio,
            duration=_EFFECT_STICKER_DURATION_SECONDS,
            blocked_windows=occupied,
            limit=timeline_duration_seconds,
        )
        if start is None:
            continue
        occupied.append((start, start + _EFFECT_STICKER_DURATION_SECONDS))
        slot_x, slot_y = _EFFECT_STICKER_SLOTS[int(digest[8:16], 16) % len(_EFFECT_STICKER_SLOTS)]
        clips.append(
            VideoTimelineClip(
                asset={
                    "kind": "effect_sticker",
                    "media_url": pick_effect(f"{task_seed}:effect:{index}"),
                    "slot_x": slot_x,
                    "slot_y": slot_y,
                    "size_ratio": _EFFECT_STICKER_SIZE_RATIO,
                    "effects": [dict(effect) for effect in _EFFECT_STICKER_EFFECTS],
                },
                start_seconds=round(start, 3),
                length_seconds=_EFFECT_STICKER_DURATION_SECONDS,
                metadata={"effect_slot": index},
            )
        )
    return clips


def _shift_past_blocked(
    start: float,
    *,
    duration: float,
    blocked_windows: list[tuple[float, float]],
    limit: float,
) -> float | None:
    """把装饰片段起点往后推到不与任何占用时段重叠；推不进就返回 None。"""
    cursor = max(0.0, start)
    for _ in range(len(blocked_windows) + 1):
        hit = next(
            (
                (block_start, block_end)
                for block_start, block_end in blocked_windows
                if cursor < block_end and block_start < cursor + duration
            ),
            None,
        )
        if hit is None:
            break
        cursor = hit[1]
    if cursor + duration > limit:
        return None
    return cursor


def apply_animation_events(
    *,
    sticker_clips: list[VideoTimelineClip],
    animation_events: list[VideoCreativeAnimationEvent],
    animation_effects: dict[str, str],
) -> None:
    """把动画事件绑定到时间范围最接近的实际贴纸片段。"""
    for event in animation_events:
        candidates = [
            clip
            for clip in sticker_clips
            if ranges_overlap(
                clip.start_seconds,
                clip.start_seconds + clip.length_seconds,
                event.start_ms / 1000,
                event.end_ms / 1000,
            )
        ]
        if not candidates:
            # 规划结果和最终贴纸集可能因筛选发生偏差，执行层直接跳过失配动画避免整条任务失败。
            log.warning(
                "动画事件已跳过，未找到可绑定的贴纸片段: "
                f"event_id={event.id}, start_ms={event.start_ms}, end_ms={event.end_ms}"
            )
            continue
        target_clip = min(
            candidates,
            key=lambda clip: (
                0 if str(clip.asset.get("text_mode") or "") == "word_art_card" else 1,
                abs(clip.start_seconds - event.start_ms / 1000),
            ),
        )
        target_clip.effect = animation_effects[event.template_id]
        if str(target_clip.asset.get("template_id") or "") == "opinion_card":
            target_clip.transition_in = "wipe_up_in"
            target_clip.transition_out = "dissolve_out"
        target_clip.metadata["animation_event"] = event.to_dict()


def pick_edge_side(task_seed: str, event_id: str) -> str:
    """为观点卡稳定挑选左侧或右侧贴边布局。"""
    digest = hashlib.sha1(f"{task_seed}:{event_id}:lane".encode()).hexdigest()
    return "right" if int(digest[:8], 16) % 2 else "left"


def plan_sticker_layouts(
    *,
    events: list[VideoCreativeStickerEvent],
    task_seed: str,
) -> dict[str, tuple[str, str]]:
    """预先规划左右车道，避免重叠期间观点卡和气泡字同侧堆叠。"""
    opinion_events = [event for event in events if event.template_id == "opinion_card"]
    layouts: dict[str, tuple[str, str]] = {}
    for event in opinion_events:
        side = pick_edge_side(task_seed, event.id)
        layouts[event.id] = (side, "bottom_right" if side == "right" else "bottom_left")

    for event in events:
        if event.template_id != "micro_sticker":
            continue
        preferred_side = pick_bubble_side(task_seed, event.id)
        occupied_sides = {
            layouts[opinion_event.id][0]
            for opinion_event in opinion_events
            if ranges_overlap(
                event.start_ms / 1000,
                event.end_ms / 1000,
                opinion_event.start_ms / 1000,
                opinion_event.end_ms / 1000,
            )
        }
        available_sides = {"left", "right"} - occupied_sides
        if available_sides and preferred_side not in available_sides:
            preferred_side = "right" if "right" in available_sides else "left"
        layouts[event.id] = (
            preferred_side,
            "mid_right" if preferred_side == "right" else "mid_left",
        )
    return layouts


def resolve_sticker_placement(
    *,
    event: VideoCreativeStickerEvent,
    task_seed: str,
    layout_side: str | None,
) -> str:
    """按类型收敛贴纸布局，避免观点卡和气泡字挤在同一块区域。"""
    if event.template_id == "opinion_card":
        side = layout_side or pick_edge_side(task_seed, event.id)
        return "bottom_right" if side == "right" else "bottom_left"
    bubble_side = layout_side or pick_bubble_side(task_seed, event.id)
    return "mid_right" if bubble_side == "right" else "mid_left"


def layout_safe_style(
    *,
    template_id: str,
    style: StickerThemeStyle,
    text: str,
) -> StickerThemeStyle:
    """按文案长度收紧字号，避免中文花字挤出安全区。"""
    text_length = visible_text_length(text)
    if template_id == "opinion_card":
        return StickerThemeStyle(
            # 观点卡短词放大一点，避免看起来像贴在角落里。
            font_size=max(style.font_size, 76 if text_length <= 6 else 68),
            font_color=style.font_color,
            opacity=style.opacity,
            effects=style.effects,
            font=style.font,
            word_art_style=style.word_art_style,
        )
    if template_id != "micro_sticker":
        return style
    return StickerThemeStyle(
        # 小贴纸短词直接放大，尽量让它看起来像真正的花字。
        font_size=max(int(style.font_size), 76 if text_length <= 2 else 68 if text_length <= 4 else 58),
        font_color=style.font_color,
        opacity=style.opacity,
        effects=style.effects,
        font=style.font,
        word_art_style=style.word_art_style,
    )


def pick_bubble_side(task_seed: str, event_id: str) -> str:
    """让气泡字稳定贴边，并和观点卡车道自然错开。"""
    digest = hashlib.sha1(f"{task_seed}:{event_id}:bubble_lane".encode()).hexdigest()
    return "right" if int(digest[:8], 16) % 2 else "left"


def pick_bubble_slot(task_seed: str, event_id: str) -> str:
    """让气泡字在安全区内稳定换行，避免每次都钉死同一条水平线。"""
    slot_ids = ("upper", "mid", "lower")
    digest = hashlib.sha1(f"{task_seed}:{event_id}:bubble_slot".encode()).hexdigest()
    return slot_ids[int(digest[:8], 16) % len(slot_ids)]


def ranges_overlap(
    left_start: float,
    left_end: float,
    right_start: float,
    right_end: float,
) -> bool:
    """判断两个时间范围是否重叠。"""
    return left_start < right_end and right_start < left_end
