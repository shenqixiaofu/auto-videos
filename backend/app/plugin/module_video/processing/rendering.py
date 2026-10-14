from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable

import httpx

from app.config.setting import settings
from app.core.exceptions import CustomException
from app.core.logger import log

from .render_contract import VideoOutputProvider, VideoRenderResult

TaskCancelChecker = Callable[[int], Awaitable[None]]
TaskStatusUpdater = Callable[[int, str, int | None, str | None, str | None], Awaitable[None]]


class VideoRenderingStage:
    """通用的视频输出轮询辅助。"""

    @classmethod
    async def wait_for_video_output(
        cls,
        *,
        task_id: int,
        provider: VideoOutputProvider,
        render_id: str,
        progress: int,
        task_label: str,
        ensure_not_cancelled: TaskCancelChecker,
        set_task_status: TaskStatusUpdater,
    ) -> VideoRenderResult:
        """轮询标准视频渲染任务，直到拿到云端输出 URL。"""
        deadline = time.monotonic() + settings.VIDEO_WORKER_TASK_TIMEOUT_SECONDS
        started_at = time.monotonic()
        log.info(
            f"{provider.provider_name} {task_label}开始轮询: "
            f"task_id={task_id}, render_id={render_id}"
        )
        while time.monotonic() < deadline:
            await ensure_not_cancelled(task_id)
            await set_task_status(
                task_id=task_id,
                status="processing",
                progress=progress,
                current_stage="rendering",
            )

            try:
                result = await provider.get_video_output_result(render_id)
            except httpx.TimeoutException as exc:
                elapsed_seconds = time.monotonic() - started_at
                raise CustomException(
                    msg=(
                        f"{provider.provider_name} {task_label}查询超时: "
                        f"task_id={task_id}, render_id={render_id}, "
                        f"已等待 {elapsed_seconds:.1f} 秒"
                    )
                ) from exc
            log.debug(
                f"{provider.provider_name} 视频任务轮询状态: "
                f"task_id={task_id}, label={task_label}, render_id={render_id}, "
                f"status={result.status}, "
                f"has_video_url={bool(result.video_url)}"
            )
            if result.status == "completed":
                result.ensure_video_url()
                log.info(
                    f"{provider.provider_name} {task_label}轮询完成: "
                    f"task_id={task_id}, render_id={render_id}"
                )
                return result
            if result.status == "failed":
                raise CustomException(
                    msg=result.error_message(f"{provider.provider_name} {task_label}失败")
                )
            if result.status not in {"queued", "rendering"}:
                raise CustomException(
                    msg=f"{provider.provider_name} 返回未知状态: {result.status}"
                )
            await asyncio.sleep(settings.VIDEO_RENDER_POLL_INTERVAL_SECONDS)

        elapsed_seconds = time.monotonic() - started_at
        raise CustomException(
            msg=(
                f"{provider.provider_name} {task_label}任务超时: "
                f"task_id={task_id}, render_id={render_id}, "
                f"已等待 {elapsed_seconds:.1f} 秒"
            )
        )
