from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from app.core.exceptions import CustomException
from app.core.logger import log

from .asr_contract import (
    SpeechRecognitionProvider,
    SpeechUtterance,
)
from .speech_cleanup_parts import media, rules, subtitles, timing
from .speech_cleanup_parts.models import VideoSpeechCleanupResult, VideoTimeRange

TaskCancelChecker = Callable[[int], Awaitable[None]]


class VideoSpeechCleanupStage:
    """口语清理阶段 facade，具体规则和媒体处理位于 speech_cleanup_parts。"""

    # 口语清理输出采用无转场 concat，元数据与实际视频时长保持一致。
    _transition_seconds = 0.0

    @classmethod
    async def run(
        cls,
        *,
        task_id: int,
        task_no: str,
        provider: SpeechRecognitionProvider,
        source_path: Path,
        output_path: Path,
        source_file_name: str,
        output_file_name: str,
        ensure_not_cancelled: TaskCancelChecker,
    ) -> VideoSpeechCleanupResult:
        """执行 ASR 识别和本地切段。"""
        started_at = time.monotonic()
        await ensure_not_cancelled(task_id)
        log.info(
            "智能视频口语清理开始: "
            f"task_id={task_id}, source_file_name={source_file_name}"
        )

        source_duration_seconds = await media.probe_duration_seconds(source_path)
        audio_path = output_path.with_name(f"{output_path.stem}-asr-source.mp3")
        await media.extract_audio_track(source_path, audio_path)
        audio_file_name = f"{task_no}-speech-cleanup-source.mp3"

        await ensure_not_cancelled(task_id)
        recognition_task_result = await provider.transcribe_audio(
            source_path=audio_path,
            file_name=audio_file_name,
            task_no=task_no,
        )
        recognition_result = recognition_task_result.recognition_result
        (
            removed_intervals,
            removed_word_count,
            removed_filler_count,
            removed_repeat_count,
            removed_pause_count,
        ) = rules.build_removed_intervals(recognition_result)
        kept_intervals = timing.build_kept_intervals(
            removed_intervals,
            source_duration_seconds,
        )
        if not kept_intervals:
            raise CustomException(msg="ASR 识别后没有可保留片段")

        changed = bool(removed_intervals)
        actual_output_path = source_path
        actual_output_file_name = source_file_name
        output_duration_seconds = source_duration_seconds
        if changed:
            actual_output_path = output_path
            actual_output_file_name = output_file_name
            await media.render_output_video(
                source_path=source_path,
                output_path=output_path,
                kept_intervals=kept_intervals,
            )
            # 实测合成产物时长，而不是用保留段求和：成片才是下游时间线真正要引用的素材。
            output_duration_seconds = await media.probe_duration_seconds(actual_output_path)

        result = VideoSpeechCleanupResult(
            enabled=True,
            provider=recognition_result.provider,
            engine=recognition_result.engine,
            model=recognition_result.model,
            changed=changed,
            source_duration_seconds=source_duration_seconds,
            output_duration_seconds=output_duration_seconds,
            audio_file_name=audio_file_name,
            audio_size_bytes=audio_path.stat().st_size,
            audio_object_key=recognition_task_result.source_audio_object_key,
            audio_source_url=recognition_task_result.source_audio_url,
            output_path=actual_output_path,
            output_file_name=actual_output_file_name,
            request_id=recognition_result.request_id,
            log_id=recognition_result.log_id,
            task_id=recognition_result.task_id,
            transcription_url=recognition_result.transcription_url,
            audio_duration_ms=recognition_result.audio_duration_ms,
            recognition_text=recognition_result.text,
            utterance_count=len(recognition_result.utterances),
            word_count=recognition_result.word_count,
            removed_word_count=removed_word_count,
            removed_filler_count=removed_filler_count,
            removed_repeat_count=removed_repeat_count,
            removed_pause_count=removed_pause_count,
            transition_seconds=cls._transition_seconds,
            removed_intervals=removed_intervals,
            kept_intervals=kept_intervals,
            recognition_result=recognition_result,
            elapsed_seconds=time.monotonic() - started_at,
        )
        log.info(
            "智能视频口语清理完成: "
            f"task_id={task_id}, changed={changed}, "
            f"utterance_count={result.utterance_count}, removed_word_count={removed_word_count}, "
            f"removed_filler_count={removed_filler_count}, "
            f"removed_repeat_count={removed_repeat_count}, "
            f"removed_pause_count={removed_pause_count}, "
            f"kept_segment_count={len(kept_intervals)}, "
            f"source_duration={source_duration_seconds:.3f}, "
            f"output_duration={output_duration_seconds:.3f}"
        )
        return result

    @staticmethod
    def remap_utterances_to_output_timeline(
        *,
        utterances: list[SpeechUtterance],
        kept_intervals: list[VideoTimeRange],
    ) -> list[SpeechUtterance]:
        """把句段映射到删词后的输出时间轴。"""
        return timing.remap_utterances_to_output_timeline(
            utterances=utterances,
            kept_intervals=kept_intervals,
        )

    @staticmethod
    def build_subtitle_segments(
        *,
        utterances: list[SpeechUtterance],
    ) -> list[dict[str, object]]:
        """把映射后的句段切成一句一句切换的字幕片段。"""
        return subtitles.build_subtitle_segments(utterances=utterances)


__all__ = [
    "VideoSpeechCleanupResult",
    "VideoSpeechCleanupStage",
    "VideoTimeRange",
]
