from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class VolcMediaKitSubtitleCue:
    """通用字幕 cue。"""

    subtitle_text: str
    start_time: float
    end_time: float
    speaker: str | None = None
    confidence: float | None = None

    def to_request_dict(self) -> dict[str, object]:
        """转换成视频加字幕接口的字幕入参。"""
        return {
            "subtitle_text": self.subtitle_text,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

    def to_dict(self) -> dict[str, object]:
        """序列化为 review 元数据。"""
        return {
            "subtitle_text": self.subtitle_text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "speaker": self.speaker,
            "confidence": self.confidence,
        }
