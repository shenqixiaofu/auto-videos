from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class VideoInputAsset:
    """worker 处理输入素材所需的最小信息。"""

    id: int
    asset_role: str
    object_key: str
    file_name: str
    file_metadata: dict


@dataclass(slots=True)
class VideoTaskInputs:
    """worker 处理单个任务所需的输入素材集合。"""

    task_no: str
    title: str
    config: dict
    checkpoint: dict
    source: VideoInputAsset
    ending: VideoInputAsset | None


class VideoTaskCancelled(Exception):
    """任务已被用户取消，worker 停止后续处理。"""
