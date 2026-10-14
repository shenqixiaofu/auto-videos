"""创意事件的解析、归一化、筛选与校验规则。

从 `VideoCreativePlanner` 拎出来的模块级函数：不碰网络、不碰任务上下文，
入参只有模型返回值与事件本身，规则可以脱离编排单独验证。枚举与字数上限集中
在本模块顶部，`VideoCreativePlanner` 的同名类属性直接引用这里，
prompt 与既有取值口径保持一致。
"""

from __future__ import annotations

from typing import Any

from app.core.exceptions import CustomException
from app.core.logger import log

from .planner_models import (
    VideoCreativeAnimationEvent,
    VideoCreativeGraphicStickerEvent,
    VideoCreativeStickerEvent,
)

# 文字贴纸模板与动画模板白名单。
STICKER_TEMPLATES = (
    "opinion_card",
    "micro_sticker",
    "highlight_box",
)
ANIMATION_TEMPLATES = ("soft_pop", "slide_up", "fade_in", "subtle_zoom")
# 图形贴纸的语义轴是情绪基调，不是脚本角色 —— 素材库里纯图形一半以上是
# 装饰，按「开场/强调」这类角色匹配会大面积落空。
TONE_OPTIONS = ("正向", "中性", "负向", "惊讶")
# 文字贴纸允许的位置。**故意不含上方槽位**，见 GRAPHIC_PLACEMENT_OPTIONS。
PLACEMENT_OPTIONS = (
    "lower_third",
    "mid_left",
    "mid_right",
    "bottom_left",
    "bottom_right",
    "center",
)
# 图形贴纸比文字多一档「顶部留白」：文字贴纸永远不会到那里，
# 这是唯一一块既不出画又能和文字同屏的区域。
GRAPHIC_PLACEMENT_OPTIONS = (
    "top_left",
    "top_right",
    "mid_left",
    "mid_right",
    "bottom_left",
    "bottom_right",
    "center",
)
# 图形贴纸和文字贴纸靠**纵向分区**错开，不再按横带避让。分区由
# timeline_parts/layout.py 的槽位保证：装饰带（图形/氛围）y >= 0.660，文字带 y <= 0.585，
# 中间留 41px 硬间隙，所以同屏时物理上不可能重叠。
# 早先那套 top/mid/bottom 横带模型与真实几何对不上：top_left 图形底边 1284px 照样压在
# 观点卡顶边 1152px 上（任务 137 第 9 秒就是这么叠的）。改 layout 槽位时必须同步这里。
OPINION_CARD_TITLE_MAX_CHARS = 4
OPINION_CARD_BODY_MAX_CHARS = 8
MICRO_STICKER_MAX_CHARS = 4
# 小贴纸之间不留额外间隔。
MICRO_STICKER_FOCUS_GAP_MS = 0
# 图形贴纸之间的最小间隔。置 0 时只杀时间重叠：模型按「2s 一个、在屏 1.5s」铺点时
# 贴纸会连续在线（任务 140 前 13.5s 塞 7 个），数量上限管不住节奏，所以用间隔兜。
GRAPHIC_STICKER_FOCUS_GAP_MS = 2000
SUBTITLE_KEYWORD_LIMIT = 2


def parse_sticker_events(
    payload: Any,
    source_duration_ms: int,
) -> list[VideoCreativeStickerEvent]:
    """解析贴纸事件列表。

    单条字段非法只丢这一条，不拖垮整轮创意规划 —— 三类事件全空时上层会兜底报错。
    """
    events: list[VideoCreativeStickerEvent] = []
    if not isinstance(payload, list):
        return events
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue
        try:
            events.append(parse_sticker_event(item, source_duration_ms, index))
        except CustomException as exc:
            log.warning(f"贴纸事件已跳过: index={index}, error={exc}")
    return events


def parse_animation_events(
    payload: Any,
    source_duration_ms: int,
) -> list[VideoCreativeAnimationEvent]:
    """解析动画事件列表。

    单条字段非法只丢这一条，不拖垮整轮创意规划 —— 三类事件全空时上层会兜底报错。
    """
    events: list[VideoCreativeAnimationEvent] = []
    if not isinstance(payload, list):
        return events
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue
        try:
            events.append(parse_animation_event(item, source_duration_ms, index))
        except CustomException as exc:
            log.warning(f"动画事件已跳过: index={index}, error={exc}")
    return events


def parse_graphic_sticker_events(
    payload: Any,
    source_duration_ms: int,
) -> list[VideoCreativeGraphicStickerEvent]:
    """解析图形贴纸事件列表。

    图形贴纸只是装饰，单条字段非法直接丢掉即可，不拖垮整条创意规划。
    """
    events: list[VideoCreativeGraphicStickerEvent] = []
    if not isinstance(payload, list):
        return events
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue
        try:
            events.append(parse_graphic_sticker_event(item, source_duration_ms, index))
        except CustomException as exc:
            log.warning(f"图形贴纸事件已跳过: index={index}, error={exc}")
    return events


def parse_graphic_sticker_event(
    payload: dict[str, Any],
    source_duration_ms: int,
    index: int,
) -> VideoCreativeGraphicStickerEvent:
    """解析单条图形贴纸事件。

    时间范围非法才整条丢掉；基调和位置写歪都只回落，不丢事件 —— 图形贴纸是
    装饰，因为一个枚举值写错就少一张图，代价比位置不完美大得多。
    """
    start_ms = require_int(payload.get("start_ms"), "start_ms")
    end_ms = require_int(payload.get("end_ms"), "end_ms")
    validate_time_range(start_ms, end_ms, source_duration_ms, "图形贴纸事件")
    event_id = str(payload.get("id") or f"g{index}")
    tone = str(payload.get("tone") or "").strip()
    if tone not in TONE_OPTIONS:
        log.warning(f"图形贴纸基调非法，回落到 正向: tone={tone!r}, id={event_id}")
        tone = TONE_OPTIONS[0]
    placement = normalize_raw_placement(
        placement=payload.get("placement"),
        template_id="graphic_sticker",
        stable_key=event_id,
    )
    if placement not in GRAPHIC_PLACEMENT_OPTIONS:
        log.warning(
            f"图形贴纸位置非法，回落到 top_right: placement={placement!r}, id={event_id}"
        )
        placement = "top_right"
    return VideoCreativeGraphicStickerEvent(
        id=event_id,
        tone=tone,
        start_ms=start_ms,
        end_ms=end_ms,
        placement=placement,
        scale=float(payload.get("scale") or 1.0),
        rotation=float(payload.get("rotation") or 0.0),
        anchor_text=str(payload.get("anchor_text") or "").strip() or None,
    )


def parse_sticker_event(
    payload: dict[str, Any],
    source_duration_ms: int,
    index: int,
) -> VideoCreativeStickerEvent:
    """解析单条贴纸事件。"""
    start_ms = require_int(payload.get("start_ms"), "start_ms")
    end_ms = require_int(payload.get("end_ms"), "end_ms")
    validate_time_range(start_ms, end_ms, source_duration_ms, "贴纸事件")
    template_id = require_choice(payload.get("template_id"), STICKER_TEMPLATES, "template_id")
    event_id = str(payload.get("id") or f"s{index}")
    placement = normalize_raw_placement(
        placement=payload.get("placement"),
        template_id=template_id,
        stable_key=event_id,
    )
    if placement not in PLACEMENT_OPTIONS:
        # 位置只是装饰性字段，认不出来就回落，不抛异常 —— 一个位置词把整轮
        # 创意规划带崩，代价远大于位置不完美。
        log.warning(f"事件位置无法识别，已回落: placement={placement!r}, id={event_id}")
        placement = pick_side_placement(event_id)
    text = str(payload.get("text") or "").strip()
    if not text:
        raise CustomException(msg="贴纸事件缺少 text")
    return VideoCreativeStickerEvent(
        id=event_id,
        template_id=template_id,
        start_ms=start_ms,
        end_ms=end_ms,
        text=text,
        placement=placement,
        scale=float(payload.get("scale") or 1.0),
        rotation=float(payload.get("rotation") or 0.0),
        title_text=str(payload.get("title_text") or "").strip() or None,
        body_text=str(payload.get("body_text") or "").strip() or None,
        card_style=str(payload.get("card_style") or "").strip() or None,
        anchor_text=str(payload.get("anchor_text") or "").strip() or None,
    )


def parse_animation_event(
    payload: dict[str, Any],
    source_duration_ms: int,
    index: int,
) -> VideoCreativeAnimationEvent:
    """解析单条动画事件。"""
    start_ms = require_int(payload.get("start_ms"), "start_ms")
    end_ms = require_int(payload.get("end_ms"), "end_ms")
    validate_time_range(start_ms, end_ms, source_duration_ms, "动画事件")
    template_id = require_choice(payload.get("template_id"), ANIMATION_TEMPLATES, "template_id")
    event_id = str(payload.get("id") or f"a{index}")
    placement = normalize_raw_placement(
        placement=payload.get("placement"),
        template_id=template_id,
        stable_key=event_id,
    )
    if placement not in PLACEMENT_OPTIONS:
        # 位置只是装饰性字段，认不出来就回落，不抛异常 —— 一个位置词把整轮
        # 创意规划带崩，代价远大于位置不完美。
        log.warning(f"事件位置无法识别，已回落: placement={placement!r}, id={event_id}")
        placement = pick_side_placement(event_id)
    description = str(payload.get("description") or "").strip()
    if not description:
        raise CustomException(msg="动画事件缺少 description")
    return VideoCreativeAnimationEvent(
        id=event_id,
        template_id=template_id,
        start_ms=start_ms,
        end_ms=end_ms,
        description=description,
        placement=placement,
        intensity=str(payload.get("intensity") or "medium").strip() or "medium",
        scale=float(payload.get("scale") or 1.0),
        rotation=float(payload.get("rotation") or 0.0),
        anchor_text=str(payload.get("anchor_text") or "").strip() or None,
    )


def normalize_sticker_events(
    events: list[VideoCreativeStickerEvent],
) -> list[VideoCreativeStickerEvent]:
    """把模型返回的位置压回可执行的安全区，避免中轴和底部堆叠。"""
    for event in events:
        if event.template_id == "micro_sticker":
            # 复用 mid_left/mid_right 枚举承载上侧边缘安全区，避免改动既有协议字段。
            event.placement = normalize_micro_sticker_placement(event.placement, event.id)
            event.text = normalize_micro_sticker_text(event.text)
            continue
        if event.template_id == "opinion_card":
            event.title_text, event.body_text, event.text = normalize_opinion_card_text(
                title_text=event.title_text,
                body_text=event.body_text,
                fallback_text=event.text,
            )
    return events


def normalize_opinion_card_text(
    *,
    title_text: str | None,
    body_text: str | None,
    fallback_text: str,
) -> tuple[str | None, str | None, str]:
    """收紧观点卡文案长度，避免中文花字在安全区内挤成一团。"""
    raw_title = str(title_text or "").strip()
    raw_body = str(body_text or "").strip()
    if not raw_title and not raw_body:
        lines = [segment.strip() for segment in str(fallback_text).splitlines() if segment.strip()]
        raw_title = lines[0] if lines else str(fallback_text).strip()
        raw_body = lines[1] if len(lines) > 1 else ""
    normalized_title = trim_visible_text(raw_title, OPINION_CARD_TITLE_MAX_CHARS)
    normalized_body = trim_visible_text(raw_body, OPINION_CARD_BODY_MAX_CHARS)
    if normalized_title and normalized_body:
        return normalized_title, normalized_body, f"{normalized_title}\n{normalized_body}"
    if normalized_title:
        return normalized_title, None, normalized_title
    normalized_text = trim_visible_text(
        raw_body or fallback_text,
        OPINION_CARD_BODY_MAX_CHARS,
    )
    return None, normalized_text or None, normalized_text


def normalize_micro_sticker_text(text: str) -> str:
    """把小贴纸强制压成超短标签，避免一条花字承载整句观点。"""
    normalized = trim_visible_text(text.replace("\n", ""), MICRO_STICKER_MAX_CHARS)
    return normalized or "重点"


def pick_side_placement(stable_key: str) -> str:
    """没有左右信息时的确定性落点：左右中段二选一，不出画也不压中央。"""
    return "mid_right" if sum(ord(char) for char in stable_key) % 2 else "mid_left"


def normalize_micro_sticker_placement(placement: str, stable_key: str) -> str:
    """把小贴纸统一归一到左右边缘车道，彻底禁掉中央区域。"""
    if "left" in placement:
        return "mid_left"
    if "right" in placement:
        return "mid_right"
    return pick_side_placement(stable_key)


def normalize_raw_placement(
    *,
    placement: Any,
    template_id: str,
    stable_key: str,
) -> str:
    """在白名单校验前把模型同义位置转换成内部位置枚举。"""
    normalized = str(placement or "").strip()
    if not normalized:
        return normalized
    if template_id == "micro_sticker":
        return normalize_micro_sticker_placement(normalized, stable_key)
    if template_id == "graphic_sticker":
        # 模型习惯写 upper_left / top 这类词，多接几个同义词，少丢事件。
        return {
            "upper_left": "top_left",
            "upper_right": "top_right",
            "upper_third": "top_left",
            "top": "top_right",
            "lower_left": "bottom_left",
            "lower_right": "bottom_right",
            "lower": "bottom_right",
        }.get(normalized, normalized)
    # 文字贴纸没有上方槽位（top_* 是图形贴纸专用），而模型会把两套枚举串用。
    # 这里下移一档接住，别让一个位置词连累整轮创意规划。
    return {
        "lower_left": "bottom_left",
        "lower_right": "bottom_right",
        "upper_left": "mid_left",
        "top_left": "mid_left",
        "upper_right": "mid_right",
        "top_right": "mid_right",
    }.get(normalized, normalized)


def normalize_subtitle_keywords(
    *,
    raw_keywords: Any,
    subtitle_utterances: list[dict[str, Any]],
) -> list[list[str]]:
    """按字幕下标对齐关键词，并丢弃不在字幕里原样出现的词。"""
    by_index: dict[int, list[str]] = {}
    if isinstance(raw_keywords, list):
        for item in raw_keywords:
            if not isinstance(item, dict):
                continue
            try:
                index = int(item.get("index"))
            except (TypeError, ValueError):
                continue
            raw_words = item.get("keywords")
            by_index[index] = (
                [str(word).strip() for word in raw_words]
                if isinstance(raw_words, list)
                else []
            )
    result: list[list[str]] = []
    for index, utterance in enumerate(subtitle_utterances, start=1):
        text = str(utterance.get("text") or "")
        selected: list[str] = []
        for candidate in by_index.get(index) or []:
            # 关键词必须原样出现在字幕里，否则高亮会命中不到。
            if not candidate or candidate in selected or candidate not in text:
                continue
            selected.append(candidate)
            if len(selected) >= SUBTITLE_KEYWORD_LIMIT:
                break
        result.append(selected)
    return result


def pick_spread_events(events: list[Any], max_count: int) -> list[Any]:
    """均匀抽取少量事件，避免贴纸和动画过密。"""
    if max_count <= 0:
        return []
    if len(events) <= max_count:
        return events
    if max_count == 1:
        return [events[len(events) // 2]]
    picked_indexes = {
        round(index * (len(events) - 1) / (max_count - 1))
        for index in range(max_count)
    }
    return [event for index, event in enumerate(events) if index in picked_indexes]


def filter_micro_stickers_for_focus(
    *,
    micro_stickers: list[VideoCreativeStickerEvent],
    blocking_events: list[VideoCreativeStickerEvent],
) -> list[VideoCreativeStickerEvent]:
    """过滤会和其他贴纸同屏抢视线的小贴纸，保证同一时刻只有一个焦点。"""
    kept_micro_stickers: list[VideoCreativeStickerEvent] = []
    sorted_blocking_events = sorted(
        blocking_events,
        key=lambda item: (item.start_ms, item.end_ms, item.id),
    )
    for event in sorted(micro_stickers, key=lambda item: (item.start_ms, item.end_ms, item.id)):
        if any(
            time_ranges_overlap(
                event.start_ms,
                event.end_ms,
                blocking.start_ms,
                blocking.end_ms,
                MICRO_STICKER_FOCUS_GAP_MS,
            )
            for blocking in [*sorted_blocking_events, *kept_micro_stickers]
        ):
            continue
        kept_micro_stickers.append(event)
    return kept_micro_stickers


def filter_graphic_stickers_for_focus(
    *,
    graphic_stickers: list[VideoCreativeGraphicStickerEvent],
) -> list[VideoCreativeGraphicStickerEvent]:
    """同一时刻最多保留一个图形贴纸。

    图形贴纸和文字贴纸允许同屏 —— 两者纵向分区不重叠（装饰带 y >= 0.660，
    文字带 y <= 0.585），不需要也不应该再按位置避让；早先按横带避让的规则
    与真实几何对不上，等于没避。这里只剩图形之间互斥：同屏叠两个图形会糊成一团。
    """
    kept_graphic_stickers: list[VideoCreativeGraphicStickerEvent] = []
    for event in sorted(graphic_stickers, key=lambda item: (item.start_ms, item.end_ms, item.id)):
        if any(
            time_ranges_overlap(
                event.start_ms,
                event.end_ms,
                kept.start_ms,
                kept.end_ms,
                GRAPHIC_STICKER_FOCUS_GAP_MS,
            )
            for kept in kept_graphic_stickers
        ):
            continue
        kept_graphic_stickers.append(event)
    return kept_graphic_stickers


def filter_animation_events_by_stickers(
    *,
    animation_events: list[VideoCreativeAnimationEvent],
    sticker_events: list[VideoCreativeStickerEvent],
) -> list[VideoCreativeAnimationEvent]:
    """只保留仍能绑定到最终贴纸集的动画事件，避免贴纸裁剪后出现失配动画。"""
    if not animation_events or not sticker_events:
        return []
    kept_animation_events: list[VideoCreativeAnimationEvent] = []
    for event in animation_events:
        if any(
            time_ranges_overlap(
                event.start_ms,
                event.end_ms,
                sticker.start_ms,
                sticker.end_ms,
            )
            for sticker in sticker_events
        ):
            kept_animation_events.append(event)
    return kept_animation_events


def trim_visible_text(text: str, max_chars: int) -> str:
    """按可见字符数截断文本，保留原有字符顺序，去掉多余空白。"""
    normalized = "".join(str(text or "").split())
    return normalized[:max_chars]


def time_ranges_overlap(
    left_start_ms: int,
    left_end_ms: int,
    right_start_ms: int,
    right_end_ms: int,
    padding_ms: int = 0,
) -> bool:
    """判断两个时间范围是否重叠，并允许附加少量安全间隔。"""
    return (
        left_start_ms < right_end_ms + padding_ms
        and right_start_ms < left_end_ms + padding_ms
    )


def require_int(value: Any, field_name: str) -> int:
    """把模型返回的数字字段转成整数。"""
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise CustomException(msg=f"创意编排结果缺少有效的 {field_name}") from exc


def require_choice(value: Any, choices: tuple[str, ...], field_name: str) -> str:
    """校验模型返回值是否在白名单中。"""
    choice = str(value or "").strip()
    if choice not in choices:
        raise CustomException(msg=f"创意编排结果的 {field_name} 非法: {choice}")
    return choice


def validate_time_range(
    start_ms: int,
    end_ms: int,
    source_duration_ms: int,
    label: str,
) -> None:
    """校验事件时间范围是否落在视频时长内。"""
    if start_ms < 0 or end_ms <= start_ms or end_ms > source_duration_ms:
        raise CustomException(
            msg=(
                f"{label}时间范围非法: "
                f"start_ms={start_ms}, end_ms={end_ms}, source_duration_ms={source_duration_ms}"
            )
        )
