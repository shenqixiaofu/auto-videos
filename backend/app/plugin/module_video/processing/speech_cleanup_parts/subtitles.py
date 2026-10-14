from __future__ import annotations

import re

from ..asr_contract import SpeechUtterance, SpeechWord

_subtitle_hard_punctuation = frozenset({"。", "！", "？", "；", "!", "?", ";"})
_subtitle_soft_punctuation = frozenset({"，", ",", "、", "：", ":"})
_subtitle_min_char_limit = 7
# 上限按底部字幕单行容量定：FontSize=56、TextWidth=0.72，1080 宽下单行约 13 个汉字。
# 收到 8 个会在词中间硬切（「听得懂」「留言」被劈开）并留下单字尾段。
_subtitle_max_char_limit = 13
_subtitle_max_duration_ms = 3600
_punctuation_chars = "，,。！？!?、；;：:"
_duplicate_punctuation_pattern = re.compile(r"([，,。！？!?、；;：:])\1+")
_edge_punctuation_pattern = re.compile(r"^[，,。！？!?、；;：:\s]+|[，,。！？!?、；;：:\s]+$")


def build_subtitle_segments(*, utterances: list[SpeechUtterance]) -> list[dict[str, object]]:
    """把映射后的句段切成一句一句切换的字幕片段。"""
    segments: list[dict[str, object]] = []
    for utterance in utterances:
        if utterance.words:
            current_words: list[SpeechWord] = []
            for word in utterance.words:
                current_words.append(word)
                if should_flush_subtitle_segment(current_words):
                    append_subtitle_segment(segments, current_words)
                    current_words = []
            if current_words:
                append_subtitle_segment(segments, current_words)
            continue

        segments.extend(
            split_text_without_words(
                text=utterance.text,
                start_ms=utterance.start_time_ms,
                end_ms=utterance.end_time_ms,
            )
        )
    return segments


def should_flush_subtitle_segment(words: list[SpeechWord]) -> bool:
    """判断当前词组是否应该切成单条字幕。"""
    if not words:
        return False
    punctuation = words[-1].punctuation or ""
    char_count = visible_char_count(rebuild_text_from_words(words))
    duration_ms = words[-1].end_time_ms - words[0].start_time_ms
    if any(char in _subtitle_hard_punctuation for char in punctuation):
        return True
    if any(char in _subtitle_soft_punctuation for char in punctuation):
        return char_count >= _subtitle_min_char_limit
    if char_count >= _subtitle_max_char_limit:
        return True
    if duration_ms >= _subtitle_max_duration_ms and char_count >= _subtitle_min_char_limit:
        return True
    return False


def append_subtitle_segment(
    segments: list[dict[str, object]],
    words: list[SpeechWord],
) -> None:
    """把一组词安全写成一条字幕片段。"""
    if not words:
        return
    text = normalize_subtitle_text(rebuild_text_from_words(words))
    if not text:
        return
    start_ms = words[0].start_time_ms
    end_ms = words[-1].end_time_ms
    if end_ms <= start_ms:
        return
    segments.append(
        {
            "start_ms": start_ms,
            "end_ms": end_ms,
            "text": text,
        }
    )


def rebuild_text_from_words(words: list[SpeechWord]) -> str:
    """按词级结果重组文本。"""
    return "".join(word.display_text() for word in words)


def visible_char_count(text: str) -> int:
    """统计字幕正文长度，空白不计入切分阈值。"""
    return len(re.sub(r"\s+", "", text))


def split_text_without_words(
    *,
    text: str,
    start_ms: int,
    end_ms: int,
) -> list[dict[str, object]]:
    """没有词级时间戳时，按标点和字数切分并分配时间。"""
    if end_ms <= start_ms:
        return []
    cleaned_text = normalize_subtitle_text(text)
    if not cleaned_text:
        return []

    chunks: list[str] = []
    current: list[str] = []
    for char in cleaned_text:
        current.append(char)
        current_length = visible_char_count("".join(current))
        if char in _subtitle_hard_punctuation:
            chunks.append("".join(current))
            current = []
        elif char in _subtitle_soft_punctuation and current_length >= _subtitle_min_char_limit:
            chunks.append("".join(current))
            current = []
        elif current_length >= _subtitle_max_char_limit:
            chunks.append("".join(current))
            current = []
    if current:
        chunks.append("".join(current))

    total_char_count = max(visible_char_count(cleaned_text), 1)
    total_duration_ms = end_ms - start_ms
    segments: list[dict[str, object]] = []
    cursor_ms = start_ms
    for index, chunk in enumerate(chunks):
        chunk_text = normalize_subtitle_text(chunk)
        if not chunk_text:
            continue
        if index == len(chunks) - 1:
            chunk_end_ms = end_ms
        else:
            chunk_duration_ms = round(
                total_duration_ms * visible_char_count(chunk) / total_char_count
            )
            chunk_end_ms = min(end_ms, cursor_ms + max(chunk_duration_ms, 1))
        if chunk_end_ms <= cursor_ms:
            continue
        segments.append(
            {
                "start_ms": cursor_ms,
                "end_ms": chunk_end_ms,
                "text": chunk_text,
            }
        )
        cursor_ms = chunk_end_ms
    return segments


def normalize_subtitle_text(text: str) -> str:
    """统一清理重复标点，避免字幕结尾出现双符号。"""
    cleaned_text = clean_subtitle_text(text)
    return cleaned_text.strip(_punctuation_chars + " ")


def clean_subtitle_text(text: str) -> str:
    """清理字幕文本里的水词和重复标点。"""
    cleaned_text = text.strip()
    previous_text = ""
    while cleaned_text and cleaned_text != previous_text:
        previous_text = cleaned_text
        cleaned_text = re.sub(
            r"^(?:[，,。！？!?、\s]*(?:嗯+|呃+|额+|啊+|这个|那个|然后|就是|就是说))+",
            "",
            cleaned_text,
        )
        cleaned_text = re.sub(
            r"(?:[，,。！？!?、\s]*(?:嗯+|呃+|额+|啊+|呀+|对吧|是吧|好吧|行吧|可以吧|你知道吧))+[，,。！？!?、\s]*$",
            "",
            cleaned_text,
        )
        cleaned_text = re.sub(
            r"([，,。！？!?、\s])(?:嗯+|呃+|额+|啊+|这个|那个|然后|就是|就是说)(?=[，,。！？!?、\s])",
            r"\1",
            cleaned_text,
        )
        # 字幕优先干净，直接去掉整句里的常见水词。
        cleaned_text = re.sub(
            r"(?:你知道吧|可以吧|就是说|对吧|是吧|好吧|行吧|这个|那个|然后|就是|嗯+|呃+|额+|啊+|呀+|吧+|呢+|嘛+)",
            "",
            cleaned_text,
        )
        cleaned_text = cleaned_text.replace("的的", "的")
        cleaned_text = re.sub(
            r"([，,。！？!?、；;：:])\1+",
            r"\1",
            cleaned_text,
        )
        cleaned_text = _duplicate_punctuation_pattern.sub(r"\1", cleaned_text)
        cleaned_text = _edge_punctuation_pattern.sub("", cleaned_text)
    return cleaned_text.strip()
