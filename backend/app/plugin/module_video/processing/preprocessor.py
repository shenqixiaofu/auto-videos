from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config.setting import settings
from app.core.exceptions import CustomException


@dataclass(slots=True)
class VideoPreprocessResult:
    """视频预处理结果，记录后续上传火山 VOD 的实际输入文件。"""

    enabled: bool
    engine: str
    output_path: Path
    output_file_name: str
    target_resolution: str | None
    command_preview: list[str]
    elapsed_seconds: float
    stdout_tail: str
    stderr_tail: str

    def to_metadata(self) -> dict[str, Any]:
        """序列化为任务资产元数据，方便排查预处理行为。"""
        return {
            "preprocess_enabled": self.enabled,
            "preprocess_engine": self.engine,
            "preprocess_output_file_name": self.output_file_name,
            "preprocess_target_resolution": self.target_resolution,
            "preprocess_command_preview": self.command_preview,
            "preprocess_elapsed_seconds": round(self.elapsed_seconds, 3),
            "preprocess_stdout_tail": self.stdout_tail,
            "preprocess_stderr_tail": self.stderr_tail,
        }


class VideoSourcePreprocessor:
    """源视频预处理器，当前只做方向和编码规整。"""

    _engine = "ffmpeg-normalize"
    _tail_limit = 4000

    @classmethod
    async def preprocess(
        cls,
        *,
        source_path: Path,
        output_path: Path,
        original_file_name: str,
        output_file_name: str,
        target_aspect_ratio: str,
    ) -> VideoPreprocessResult:
        """按配置预处理源视频，返回后续字幕链路实际使用的视频文件。"""
        target_resolution = cls._target_resolution(target_aspect_ratio)
        if not settings.VIDEO_PREPROCESS_ENABLED:
            return VideoPreprocessResult(
                enabled=False,
                engine=cls._engine,
                output_path=source_path,
                output_file_name=original_file_name,
                target_resolution=target_resolution,
                command_preview=[],
                elapsed_seconds=0,
                stdout_tail="",
                stderr_tail="",
            )

        started_at = time.monotonic()
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            "-metadata:s:v:0",
            "rotate=0",
            str(output_path),
        ]
        command_preview = [
            "ffmpeg",
            "-i",
            "<source>",
            # 只规整方向、像素偶数和封装，不再自动裁剪口播时间线。
            "ffmpeg-clear-rotation",
        ]

        stdout, stderr = await cls._run_command(
            command,
            timeout=settings.VIDEO_AUTO_EDITOR_TIMEOUT_SECONDS,
            timeout_message="视频方向和编码规整超时",
            error_prefix="视频方向和编码规整失败",
        )

        if not output_path.exists() or output_path.stat().st_size <= 0:
            raise CustomException(msg="视频输出封装未生成有效输出文件")

        return VideoPreprocessResult(
            enabled=True,
            engine=cls._engine,
            output_path=output_path,
            output_file_name=output_file_name,
            target_resolution=target_resolution,
            command_preview=command_preview,
            elapsed_seconds=time.monotonic() - started_at,
            stdout_tail=cls._tail(stdout),
            stderr_tail=cls._tail(stderr),
        )

    @classmethod
    async def _run_command(
        cls,
        command: list[str],
        *,
        timeout: int,
        timeout_message: str,
        error_prefix: str,
    ) -> tuple[str, str]:
        """执行外部媒体命令，统一处理超时和错误输出。"""
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            process.kill()
            await process.communicate()
            raise CustomException(msg=timeout_message)

        stdout = cls._decode_output(stdout_bytes)
        stderr = cls._decode_output(stderr_bytes)
        if process.returncode != 0:
            raise CustomException(
                msg=f"{error_prefix}: returncode={process.returncode}, stderr={cls._tail(stderr)}"
            )
        return stdout, stderr

    @staticmethod
    def _decode_output(output: bytes) -> str:
        """按 UTF-8 读取命令输出，避免 Windows 中文路径导致异常。"""
        return output.decode("utf-8", errors="replace").strip()

    @staticmethod
    def _target_resolution(aspect_ratio: str) -> str:
        """记录预处理输出画幅策略，当前不改变原视频画面比例。"""
        # 当前只烘焙手机旋转元数据，不改变原视频画面比例。
        return "source-ratio"

    @classmethod
    def _tail(cls, text: str) -> str:
        """只保留命令输出尾部，避免元数据过大。"""
        return text[-cls._tail_limit :] if len(text) > cls._tail_limit else text
