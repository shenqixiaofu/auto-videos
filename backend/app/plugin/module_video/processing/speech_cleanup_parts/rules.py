from __future__ import annotations

import re
from itertools import pairwise

from app.config.setting import settings

from ..asr_contract import SpeechRecognitionResult, SpeechWord
from .models import VideoTimeRange
from .subtitles import clean_subtitle_text

_filler_word_pattern = re.compile(
    r"^(?:嗯+|呃+|额+|啊+|呀+|吧+|呢+|嘛+|这个|那个|然后|就是|就是说|对吧|是吧|好吧|行吧|可以吧|你知道吧)$"
)
_filler_phrases = (
    "你知道吧",
    "可以吧",
    "就是说",
    "然后",
    "就是",
    "对吧",
    "是吧",
    "好吧",
    "行吧",
    "这个",
    "那个",
)
_repeat_search_word_limit = 8
# 口播里「说半句发现不对、停一下重说」的间隔常超过 1.5 秒，窗口太紧会整片漏检。
_repeat_max_duration_seconds = 3.0
# 压缩长停顿时两端各留一点余量，避免切口生硬或吃掉词尾音。
_pause_keep_margin_seconds = 0.2


def build_removed_intervals(
    result: SpeechRecognitionResult,
) -> tuple[list[VideoTimeRange], int, int, int, int]:
    """根据词级结果，构造水词、重复口语和长停顿的删除范围。"""
    removed_intervals: list[VideoTimeRange] = []
    removed_word_count = 0
    removed_filler_count = 0
    removed_repeat_count = 0
    removed_pause_count = 0
    pause_trim_enabled = settings.VIDEO_SPEECH_PAUSE_TRIM_ENABLED
    min_pause_seconds = settings.VIDEO_SPEECH_PAUSE_MIN_SECONDS
    previous_words: list[SpeechWord] | None = None
    previous_index = -1
    for index, utterance in enumerate(result.utterances):
        cleaned_text = clean_subtitle_text(utterance.text)
        if not cleaned_text and not utterance.words:
            # 没有词级结果且清洗后为空：整句确实没有可用内容，直接删除。
            removed_intervals.append(
                VideoTimeRange(
                    start_seconds=utterance.start_time_ms / 1000,
                    end_seconds=utterance.end_time_ms / 1000,
                )
            )
            removed_filler_count += 1
            previous_words = None
            previous_index = index
            continue

        removed_word_indexes: set[int] = set()
        repeated_ranges = find_repeated_word_ranges(utterance.words)
        for start_index, end_index in repeated_ranges:
            removed_intervals.append(
                VideoTimeRange(
                    start_seconds=utterance.words[start_index].start_time_ms / 1000,
                    end_seconds=utterance.words[end_index].start_time_ms / 1000,
                )
            )
            removed_word_indexes.update(range(start_index, end_index))
        removed_repeat_count += len(repeated_ranges)

        filler_ranges = find_filler_word_ranges(utterance.words)
        for start_index, end_index in filler_ranges:
            removed_intervals.append(
                VideoTimeRange(
                    start_seconds=utterance.words[start_index].start_time_ms / 1000,
                    end_seconds=utterance.words[end_index - 1].end_time_ms / 1000,
                )
            )
            removed_word_indexes.update(range(start_index, end_index))
            removed_filler_count += 1

        removed_word_count += len(removed_word_indexes)

        if pause_trim_enabled and utterance.words:
            pause_ranges = find_pause_ranges(
                utterance.words, min_pause_seconds=min_pause_seconds
            )
            removed_intervals.extend(pause_ranges)
            removed_pause_count += len(pause_ranges)
            # 句间停顿只在原列表相邻时判断，中间夹了无词级结果的句子就跳过，避免误删。
            if previous_words is not None and index == previous_index + 1:
                boundary_range = _pause_range_between(
                    previous_words[-1],
                    utterance.words[0],
                    min_pause_seconds=min_pause_seconds,
                )
                if boundary_range is not None:
                    removed_intervals.append(boundary_range)
                    removed_pause_count += 1

        previous_words = utterance.words or None
        previous_index = index

    return (
        merge_ranges(removed_intervals),
        removed_word_count,
        removed_filler_count,
        removed_repeat_count,
        removed_pause_count,
    )


def find_pause_ranges(
    words: list[SpeechWord],
    *,
    min_pause_seconds: float,
) -> list[VideoTimeRange]:
    """查找同一句内相邻词之间的长停顿。"""
    ranges: list[VideoTimeRange] = []
    for previous_word, next_word in pairwise(words):
        pause_range = _pause_range_between(
            previous_word, next_word, min_pause_seconds=min_pause_seconds
        )
        if pause_range is not None:
            ranges.append(pause_range)
    return ranges


def _pause_range_between(
    previous_word: SpeechWord,
    next_word: SpeechWord,
    *,
    min_pause_seconds: float,
) -> VideoTimeRange | None:
    """把两个词之间过长的停顿压成删除区间，两端各留一点余量。"""
    pause_seconds = (next_word.start_time_ms - previous_word.end_time_ms) / 1000
    if pause_seconds <= min_pause_seconds:
        return None
    start_seconds = previous_word.end_time_ms / 1000 + _pause_keep_margin_seconds
    end_seconds = next_word.start_time_ms / 1000 - _pause_keep_margin_seconds
    if end_seconds <= start_seconds:
        return None
    return VideoTimeRange(start_seconds, end_seconds)


def find_repeated_word_ranges(words: list[SpeechWord]) -> list[tuple[int, int]]:
    """查找紧邻复述，返回需要删除的前一次表达下标范围。"""
    normalized_words = [normalize_word(word.display_text()) for word in words]
    repeated_ranges: list[tuple[int, int]] = []
    first_index = 0
    while first_index < len(words) - 1:
        best_second_index: int | None = None
        best_common_length = 0
        search_end = min(len(words), first_index + _repeat_search_word_limit + 1)
        for second_index in range(first_index + 1, search_end):
            if not normalized_words[first_index]:
                continue
            if normalized_words[first_index] != normalized_words[second_index]:
                continue
            duration_seconds = (
                words[second_index].start_time_ms - words[first_index].start_time_ms
            ) / 1000
            if duration_seconds > _repeat_max_duration_seconds:
                continue

            common_length = common_word_length(normalized_words, first_index, second_index)
            is_exact_phrase_repeat = common_length >= 2
            # 紧邻的单字/单词重复（"我我"、"这个这个"）也是口误，不限于代词。
            # 只认紧邻，间隔一个词以上不删，避免误伤正常语句。
            is_adjacent_single_repeat = (
                common_length == 1 and second_index - first_index == 1
            )
            if not is_exact_phrase_repeat and not is_adjacent_single_repeat:
                continue
            if common_length > best_common_length:
                best_second_index = second_index
                best_common_length = common_length

        if best_second_index is None:
            first_index += 1
            continue
        repeated_ranges.append((first_index, best_second_index))
        first_index = best_second_index

    return repeated_ranges


def common_word_length(
    normalized_words: list[str],
    first_index: int,
    second_index: int,
) -> int:
    """计算两段词序列从指定位置开始的相同长度。"""
    common_length = 0
    while (
        common_length < _repeat_search_word_limit
        and first_index + common_length < second_index
        and second_index + common_length < len(normalized_words)
        and normalized_words[first_index + common_length]
        and normalized_words[first_index + common_length]
        == normalized_words[second_index + common_length]
    ):
        common_length += 1
    return common_length


def find_filler_word_ranges(words: list[SpeechWord]) -> list[tuple[int, int]]:
    """兼容逐词时间戳，查找单字和多字水词范围。"""
    normalized_words = [normalize_word(word.display_text()) for word in words]
    filler_ranges: list[tuple[int, int]] = []
    word_index = 0
    while word_index < len(words):
        if is_filler_word(normalized_words[word_index]):
            filler_ranges.append((word_index, word_index + 1))
            word_index += 1
            continue

        combined_text = ""
        matched_end_index: int | None = None
        for end_index in range(
            word_index,
            min(len(words), word_index + _repeat_search_word_limit),
        ):
            combined_text += normalized_words[end_index]
            if combined_text in _filler_phrases:
                matched_end_index = end_index + 1
            if not any(phrase.startswith(combined_text) for phrase in _filler_phrases):
                break
        if matched_end_index is None:
            word_index += 1
            continue
        filler_ranges.append((word_index, matched_end_index))
        word_index = matched_end_index

    return filler_ranges


def normalize_word(text: str) -> str:
    """移除词级结果中的空白和标点，保留可比较正文。"""
    return re.sub(r"[，,。！？!?、；;：:\s]+", "", text)


def is_filler_word(text: str) -> bool:
    """判断单个词是否属于口语水词。"""
    cleaned_text = clean_subtitle_text(text)
    if not cleaned_text:
        return True
    return bool(_filler_word_pattern.match(cleaned_text))


def merge_ranges(intervals: list[VideoTimeRange]) -> list[VideoTimeRange]:
    """合并重叠或相连的时间范围。"""
    sorted_intervals = sorted(
        (interval for interval in intervals if interval.end_seconds > interval.start_seconds),
        key=lambda interval: (interval.start_seconds, interval.end_seconds),
    )
    if not sorted_intervals:
        return []

    merged: list[VideoTimeRange] = [sorted_intervals[0]]
    for interval in sorted_intervals[1:]:
        current = merged[-1]
        if interval.start_seconds <= current.end_seconds:
            current.end_seconds = max(current.end_seconds, interval.end_seconds)
            continue
        merged.append(VideoTimeRange(interval.start_seconds, interval.end_seconds))
    return merged
