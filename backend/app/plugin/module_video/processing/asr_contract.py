from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(slots=True)
class SpeechWord:
    """统一的词级时间戳结构。"""

    text: str
    start_time_ms: int
    end_time_ms: int
    punctuation: str | None = None
    confidence: float | None = None

    def display_text(self) -> str:
        """返回适合重组字幕的词文本。"""
        return f"{self.text}{self.punctuation or ''}"

    def to_dict(self) -> dict[str, Any]:
        """序列化为元数据。"""
        return {
            "text": self.text,
            "start_time_ms": self.start_time_ms,
            "end_time_ms": self.end_time_ms,
            "punctuation": self.punctuation,
            "confidence": self.confidence,
        }


@dataclass(slots=True)
class SpeechUtterance:
    """统一的句级时间戳结构。"""

    text: str
    start_time_ms: int
    end_time_ms: int
    words: list[SpeechWord]
    speaker_id: int | None = None
    language: str | None = None
    emotion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """序列化为元数据。"""
        return {
            "text": self.text,
            "start_time_ms": self.start_time_ms,
            "end_time_ms": self.end_time_ms,
            "speaker_id": self.speaker_id,
            "language": self.language,
            "emotion": self.emotion,
            "words": [word.to_dict() for word in self.words],
        }


@dataclass(slots=True)
class SpeechRecognitionResult:
    """统一的识别结果结构。"""

    provider: str
    engine: str
    model: str
    task_id: str
    request_id: str
    log_id: str | None
    audio_duration_ms: int | None
    text: str
    utterances: list[SpeechUtterance]
    transcription_url: str

    @property
    def word_count(self) -> int:
        """返回词级条数。"""
        return sum(len(utterance.words) for utterance in self.utterances)

    def to_metadata(self) -> dict[str, Any]:
        """序列化为元数据。"""
        return {
            "provider": self.provider,
            "engine": self.engine,
            "model": self.model,
            "task_id": self.task_id,
            "request_id": self.request_id,
            "log_id": self.log_id,
            "audio_duration_ms": self.audio_duration_ms,
            "text": self.text,
            "utterance_count": len(self.utterances),
            "word_count": self.word_count,
            "transcription_url": self.transcription_url,
            "utterances": [utterance.to_dict() for utterance in self.utterances],
        }


@dataclass(slots=True)
class SpeechRecognitionTaskResult:
    """统一的识别任务结果，包含上传音频来源。"""

    source_audio_object_key: str
    source_audio_url: str
    recognition_result: SpeechRecognitionResult

    def to_metadata(self) -> dict[str, Any]:
        """序列化为元数据。"""
        return {
            "source_audio_object_key": self.source_audio_object_key,
            "source_audio_url": self.source_audio_url,
            "recognition_result": self.recognition_result.to_metadata(),
        }


class SpeechRecognitionProvider(Protocol):
    """统一的音频识别 provider。"""

    provider_name: str

    async def transcribe_audio(
        self,
        *,
        source_path: Path,
        file_name: str,
        task_no: str,
    ) -> SpeechRecognitionTaskResult:
        """上传并转写本地音频文件。"""
