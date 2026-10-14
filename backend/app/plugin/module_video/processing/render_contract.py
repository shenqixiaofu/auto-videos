from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

from app.core.exceptions import CustomException

VideoRenderStatus = Literal["queued", "rendering", "completed", "failed"]

# 当前产品收敛为竖屏日常 Vlog，开放更多规格时只改这一处。
VideoAspectRatio = Literal["9:16"]
VideoStylePreset = Literal["vlog"]
DEFAULT_ASPECT_RATIO: VideoAspectRatio = "9:16"
DEFAULT_STYLE_PRESET: VideoStylePreset = "vlog"


@dataclass(frozen=True, slots=True)
class VideoRenderOutput:
    """标准渲染输出规格。"""

    width: int
    height: int
    fps: int
    format: str = "mp4"
    aspect_ratio: str = DEFAULT_ASPECT_RATIO

    def to_dict(self) -> dict[str, Any]:
        """序列化输出规格。"""
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "format": self.format,
            "aspect_ratio": self.aspect_ratio,
        }


@dataclass(slots=True)
class VideoTimelineClip:
    """与具体云厂商无关的时间线片段。"""

    asset: dict[str, Any]
    start_seconds: float
    length_seconds: float
    # 从素材内部第几秒开始取。同一条轨上多个 clip 的时间线位置由顺序隐含，
    # start_seconds 不承担这个语义 —— 混用会让第二个 clip 从素材第 67 秒开始读，
    # 片尾拼接就是这么失效的。
    source_offset_seconds: float = 0.0
    placement: str = "center"
    offset_x: float = 0.0
    offset_y: float = 0.0
    scale: float = 1.0
    rotation: float = 0.0
    transition_in: str | None = None
    transition_out: str | None = None
    effect: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        """序列化时间线片段，供审核和重渲染追溯。"""
        return {
            "asset": self.asset,
            "start_seconds": round(self.start_seconds, 3),
            "length_seconds": round(self.length_seconds, 3),
            "source_offset_seconds": round(self.source_offset_seconds, 3),
            "placement": self.placement,
            "offset_x": round(self.offset_x, 4),
            "offset_y": round(self.offset_y, 4),
            "scale": round(self.scale, 4),
            "rotation": round(self.rotation, 3),
            "transition_in": self.transition_in,
            "transition_out": self.transition_out,
            "effect": self.effect,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class VideoTimeline:
    """标准视频时间线。"""

    duration_seconds: float
    tracks: list[list[VideoTimelineClip]]
    output: VideoRenderOutput
    audio_tracks: list[list[VideoTimelineClip]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        """序列化时间线，供任务元数据保存。"""
        return {
            "duration_seconds": round(self.duration_seconds, 3),
            "tracks": [
                [clip.to_metadata() for clip in track]
                for track in self.tracks
            ],
            "audio_tracks": [
                [clip.to_metadata() for clip in track]
                for track in self.audio_tracks
            ],
            "output": self.output.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class VideoRenderSubmission:
    """标准异步渲染提交结果。"""

    provider: str
    render_id: str
    request_id: str | None
    status: VideoRenderStatus
    raw: dict[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        """序列化提交结果。"""
        return {
            "provider": self.provider,
            "render_id": self.render_id,
            "request_id": self.request_id,
            "status": self.status,
            "raw": self.raw,
        }


@dataclass(slots=True)
class VideoRenderResult:
    """标准异步渲染查询结果。"""

    provider: str
    render_id: str
    status: VideoRenderStatus
    video_url: str | None
    error: str | None
    raw: dict[str, Any]

    def ensure_video_url(self) -> str:
        """确认渲染完成后返回了视频地址。"""
        if not self.video_url:
            raise CustomException(
                msg=f"{self.provider} 视频渲染已完成但未返回 video_url: render_id={self.render_id}"
            )
        return self.video_url

    def error_message(self, default_message: str) -> str:
        """返回标准化错误信息。"""
        return self.error or default_message

    def to_metadata(self) -> dict[str, Any]:
        """序列化查询结果。"""
        return {
            "provider": self.provider,
            "render_id": self.render_id,
            "status": self.status,
            "video_url": self.video_url,
            "error": self.error,
            "raw": self.raw,
        }


class VideoOutputProvider(Protocol):
    """能够查询异步视频输出的 provider。"""

    provider_name: str

    async def get_video_output_result(self, render_id: str) -> VideoRenderResult:
        """查询异步视频输出结果。"""


class VideoRenderProvider(VideoOutputProvider, Protocol):
    """能够提交和查询时间线渲染的 provider。"""

    async def submit_timeline_render(
        self,
        *,
        timeline: VideoTimeline,
        client_token: str,
        source_path: Path | None = None,
    ) -> VideoRenderSubmission:
        """提交标准时间线渲染任务。"""
