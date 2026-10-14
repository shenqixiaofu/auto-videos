from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..asr_contract import SpeechRecognitionResult


@dataclass(slots=True)
class VideoTimeRange:
    """视频时间范围，统一用秒记录。"""

    start_seconds: float
    end_seconds: float

    @property
    def duration_seconds(self) -> float:
        """返回时长。"""
        return max(self.end_seconds - self.start_seconds, 0.0)

    def to_dict(self) -> dict[str, Any]:
        """序列化为元数据。"""
        return {
            "start_seconds": round(self.start_seconds, 3),
            "end_seconds": round(self.end_seconds, 3),
            "duration_seconds": round(self.duration_seconds, 3),
        }


@dataclass(slots=True)
class VideoSpeechCleanupResult:
    """口语清理后的本地视频结果。"""

    enabled: bool
    provider: str
    engine: str
    model: str
    changed: bool
    source_duration_seconds: float
    output_duration_seconds: float
    audio_file_name: str
    audio_size_bytes: int
    audio_object_key: str
    audio_source_url: str
    output_path: Path
    output_file_name: str
    request_id: str
    log_id: str | None
    task_id: str
    transcription_url: str
    audio_duration_ms: int | None
    recognition_text: str
    utterance_count: int
    word_count: int
    removed_word_count: int
    removed_filler_count: int
    removed_repeat_count: int
    removed_pause_count: int
    transition_seconds: float
    removed_intervals: list[VideoTimeRange]
    kept_intervals: list[VideoTimeRange]
    recognition_result: SpeechRecognitionResult
    elapsed_seconds: float

    def to_metadata(self) -> dict[str, Any]:
        """序列化为任务元数据。"""
        return {
            "speech_cleanup_enabled": self.enabled,
            "speech_cleanup_provider": self.provider,
            "speech_cleanup_engine": self.engine,
            "speech_cleanup_model": self.model,
            "speech_cleanup_changed": self.changed,
            "speech_cleanup_source_duration_seconds": round(self.source_duration_seconds, 3),
            # 时间线必须按清理后的实际时长渲染，按源时长会把删掉的口播算成定格画面。
            "speech_cleanup_output_duration_seconds": round(self.output_duration_seconds, 3),
            "speech_cleanup_audio_file_name": self.audio_file_name,
            "speech_cleanup_audio_size_bytes": self.audio_size_bytes,
            "speech_cleanup_asr_audio_object_key": self.audio_object_key,
            "speech_cleanup_asr_audio_source_url": self.audio_source_url,
            "speech_cleanup_output_file_name": self.output_file_name,
            "speech_cleanup_output_path": str(self.output_path),
            "speech_cleanup_asr_request_id": self.request_id,
            "speech_cleanup_asr_log_id": self.log_id,
            "speech_cleanup_asr_task_id": self.task_id,
            "speech_cleanup_asr_transcription_url": self.transcription_url,
            "speech_cleanup_asr_audio_duration_ms": self.audio_duration_ms,
            "speech_cleanup_asr_text": self.recognition_text,
            "speech_cleanup_utterance_count": self.utterance_count,
            "speech_cleanup_word_count": self.word_count,
            "speech_cleanup_removed_word_count": self.removed_word_count,
            "speech_cleanup_removed_filler_count": self.removed_filler_count,
            "speech_cleanup_removed_repeat_count": self.removed_repeat_count,
            "speech_cleanup_removed_pause_count": self.removed_pause_count,
            "speech_cleanup_transition_seconds": round(self.transition_seconds, 3),
            "speech_cleanup_removed_intervals": [
                interval.to_dict() for interval in self.removed_intervals
            ],
            "speech_cleanup_kept_intervals": [interval.to_dict() for interval in self.kept_intervals],
            "speech_cleanup_asr_result": self.recognition_result.to_metadata(),
            "speech_cleanup_elapsed_seconds": round(self.elapsed_seconds, 3),
        }
