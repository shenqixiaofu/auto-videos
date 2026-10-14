from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.core.exceptions import CustomException

from .models import VideoTimeRange

_ffmpeg_timeout_seconds = 1800
_tail_limit = 4000


async def extract_audio_track(source_path: Path, audio_path: Path) -> None:
    """把视频里的音轨导出成 ASR 可直接识别的 MP3。"""
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "64k",
        str(audio_path),
    ]
    await run_command(
        command,
        timeout=_ffmpeg_timeout_seconds,
        timeout_message="口语清理音频提取超时",
        error_prefix="口语清理音频提取失败",
    )
    if not audio_path.exists() or audio_path.stat().st_size <= 0:
        raise CustomException(msg="口语清理音频提取未生成有效文件")


async def render_output_video(
    *,
    source_path: Path,
    output_path: Path,
    kept_intervals: list[VideoTimeRange],
) -> None:
    """把保留片段切出后按顺序同步拼接音视频。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    segment_paths: list[Path] = []
    for index, interval in enumerate(kept_intervals, start=1):
        segment_path = output_path.with_name(f"{output_path.stem}-segment-{index}.mp4")
        segment_paths.append(segment_path)
        await render_segment(source_path, segment_path, interval)

    if len(segment_paths) == 1:
        if output_path.exists():
            output_path.unlink()
        segment_paths[0].replace(output_path)
        return

    inputs: list[str] = []
    for segment_path in segment_paths:
        inputs.extend(["-i", str(segment_path)])

    filters: list[str] = []
    concat_inputs: list[str] = []
    for index in range(len(segment_paths)):
        filters.append(f"[{index}:v]setpts=PTS-STARTPTS,format=yuv420p[v{index}]")
        filters.append(f"[{index}:a]asetpts=PTS-STARTPTS[a{index}]")
        concat_inputs.extend([f"[v{index}]", f"[a{index}]"])
    filters.append(
        f"{''.join(concat_inputs)}"
        f"concat=n={len(segment_paths)}:v=1:a=1[vout][aout]"
    )

    command = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[vout]",
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    await run_command(
        command,
        timeout=_ffmpeg_timeout_seconds,
        timeout_message="口语清理视频合成超时",
        error_prefix="口语清理视频合成失败",
    )
    if not output_path.exists() or output_path.stat().st_size <= 0:
        raise CustomException(msg="口语清理视频合成未生成有效输出文件")


async def render_segment(
    source_path: Path,
    segment_path: Path,
    interval: VideoTimeRange,
) -> None:
    """切出单个保留片段。"""
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-filter_complex",
        (
            f"[0:v]trim=start={interval.start_seconds:.3f}:end={interval.end_seconds:.3f},"
            "setpts=PTS-STARTPTS[v];"
            f"[0:a]atrim=start={interval.start_seconds:.3f}:end={interval.end_seconds:.3f},"
            "asetpts=PTS-STARTPTS[a]"
        ),
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(segment_path),
    ]
    await run_command(
        command,
        timeout=_ffmpeg_timeout_seconds,
        timeout_message="口语清理片段切分超时",
        error_prefix="口语清理片段切分失败",
    )
    if not segment_path.exists() or segment_path.stat().st_size <= 0:
        raise CustomException(msg="口语清理片段切分未生成有效文件")


async def probe_duration_seconds(media_path: Path) -> float:
    """读取媒体总时长。"""
    stdout, _ = await run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(media_path),
        ],
        timeout=_ffmpeg_timeout_seconds,
        timeout_message="口语清理读取时长超时",
        error_prefix="口语清理读取时长失败",
    )
    data = json.loads(stdout)
    return float(data["format"]["duration"])


async def run_command(
    command: list[str],
    *,
    timeout: int | float,
    timeout_message: str,
    error_prefix: str,
) -> tuple[str, str]:
    """执行外部命令并统一处理超时。"""
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

    stdout = decode_output(stdout_bytes)
    stderr = decode_output(stderr_bytes)
    if process.returncode != 0:
        raise CustomException(
            msg=f"{error_prefix}: returncode={process.returncode}, stderr={tail(stderr)}"
        )
    return stdout, stderr


def decode_output(output: bytes) -> str:
    """按 UTF-8 读取命令输出。"""
    return output.decode("utf-8", errors="replace").strip()


def tail(text: str) -> str:
    """只保留输出尾部，便于日志查看。"""
    return text[-_tail_limit:] if len(text) > _tail_limit else text
