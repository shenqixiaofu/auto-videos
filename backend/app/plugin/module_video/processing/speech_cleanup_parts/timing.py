from __future__ import annotations

from ..asr_contract import SpeechUtterance, SpeechWord
from .models import VideoTimeRange
from .rules import merge_ranges
from .subtitles import rebuild_text_from_words

# 口语清理输出采用无转场 concat，字幕时间轴不再扣减片段过渡时长。
_transition_seconds = 0.0


def remap_utterances_to_output_timeline(
    *,
    utterances: list[SpeechUtterance],
    kept_intervals: list[VideoTimeRange],
) -> list[SpeechUtterance]:
    """把原视频句段时间映射到删词后的输出时间轴。"""
    if not kept_intervals:
        return []

    output_offsets = build_output_offsets(kept_intervals)
    remapped: list[SpeechUtterance] = []
    for utterance in utterances:
        mapped_words = remap_words_to_output_timeline(
            words=utterance.words,
            kept_intervals=kept_intervals,
            output_offsets=output_offsets,
        )
        if mapped_words:
            text = rebuild_text_from_words(mapped_words).strip()
            remapped.append(
                SpeechUtterance(
                    text=text,
                    start_time_ms=mapped_words[0].start_time_ms,
                    end_time_ms=mapped_words[-1].end_time_ms,
                    words=mapped_words,
                    speaker_id=utterance.speaker_id,
                    language=utterance.language,
                    emotion=utterance.emotion,
                )
            )
            continue

        remapped_range = remap_range_to_output_timeline(
            start_seconds=utterance.start_time_ms / 1000,
            end_seconds=utterance.end_time_ms / 1000,
            kept_intervals=kept_intervals,
            output_offsets=output_offsets,
        )
        if remapped_range is None:
            continue
        text = str(utterance.text or "").strip()
        if not text:
            continue
        remapped.append(
            SpeechUtterance(
                text=text,
                start_time_ms=round(remapped_range[0] * 1000),
                end_time_ms=round(remapped_range[1] * 1000),
                words=[],
                speaker_id=utterance.speaker_id,
                language=utterance.language,
                emotion=utterance.emotion,
            )
        )
    return remapped


def build_kept_intervals(
    removed_intervals: list[VideoTimeRange],
    source_duration_seconds: float,
) -> list[VideoTimeRange]:
    """把删除范围取反，得到最终保留片段。"""
    if source_duration_seconds <= 0:
        return []

    clipped_removed = [
        VideoTimeRange(
            start_seconds=max(0.0, min(interval.start_seconds, source_duration_seconds)),
            end_seconds=max(0.0, min(interval.end_seconds, source_duration_seconds)),
        )
        for interval in removed_intervals
        if interval.end_seconds > interval.start_seconds
    ]
    merged_removed = merge_ranges(clipped_removed)
    if not merged_removed:
        return [VideoTimeRange(0.0, source_duration_seconds)]

    kept_intervals: list[VideoTimeRange] = []
    cursor = 0.0
    for interval in merged_removed:
        if interval.start_seconds > cursor:
            kept_intervals.append(VideoTimeRange(cursor, interval.start_seconds))
        cursor = max(cursor, interval.end_seconds)
    if cursor < source_duration_seconds:
        kept_intervals.append(VideoTimeRange(cursor, source_duration_seconds))

    return [interval for interval in kept_intervals if interval.duration_seconds > 0.05]


def adaptive_transition_seconds(durations: list[float]) -> float:
    """根据片段长度自动收缩转场时长，避免短片段报错。"""
    shortest = min(durations)
    transition_seconds = _transition_seconds
    if shortest <= transition_seconds * 2:
        transition_seconds = max(shortest / 3, 0.04)
    return round(transition_seconds, 3)


def build_output_offsets(kept_intervals: list[VideoTimeRange]) -> list[float]:
    """根据保留片段长度计算输出时间轴偏移。"""
    durations = [interval.duration_seconds for interval in kept_intervals]
    transition_seconds = adaptive_transition_seconds(durations) if len(kept_intervals) > 1 else 0.0
    output_offsets: list[float] = []
    output_cursor = 0.0
    for index, duration_seconds in enumerate(durations):
        output_offsets.append(output_cursor)
        output_cursor += duration_seconds
        if index < len(durations) - 1:
            output_cursor -= transition_seconds
    return output_offsets


def remap_words_to_output_timeline(
    *,
    words: list[SpeechWord],
    kept_intervals: list[VideoTimeRange],
    output_offsets: list[float],
) -> list[SpeechWord]:
    """把保留词映射到删词后的输出时间轴。"""
    remapped_words: list[SpeechWord] = []
    for word in words:
        remapped_range = remap_range_to_output_timeline(
            start_seconds=word.start_time_ms / 1000,
            end_seconds=word.end_time_ms / 1000,
            kept_intervals=kept_intervals,
            output_offsets=output_offsets,
        )
        if remapped_range is None:
            continue
        remapped_words.append(
            SpeechWord(
                text=word.text,
                start_time_ms=round(remapped_range[0] * 1000),
                end_time_ms=round(remapped_range[1] * 1000),
                punctuation=word.punctuation,
                confidence=word.confidence,
            )
        )
    return remapped_words


def remap_range_to_output_timeline(
    *,
    start_seconds: float,
    end_seconds: float,
    kept_intervals: list[VideoTimeRange],
    output_offsets: list[float],
) -> tuple[float, float] | None:
    """把单个时间范围映射到输出时间轴。"""
    mapped_start: float | None = None
    mapped_end: float | None = None
    for interval, output_offset in zip(kept_intervals, output_offsets, strict=True):
        overlap_start = max(start_seconds, interval.start_seconds)
        overlap_end = min(end_seconds, interval.end_seconds)
        if overlap_end <= overlap_start:
            continue
        current_start = output_offset + overlap_start - interval.start_seconds
        current_end = output_offset + overlap_end - interval.start_seconds
        mapped_start = current_start if mapped_start is None else min(mapped_start, current_start)
        mapped_end = current_end if mapped_end is None else max(mapped_end, current_end)

    if mapped_start is None or mapped_end is None or mapped_end <= mapped_start:
        return None
    return mapped_start, mapped_end
