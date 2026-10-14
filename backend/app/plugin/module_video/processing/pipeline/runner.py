from __future__ import annotations

import asyncio
import hashlib
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import httpx
from apscheduler.triggers.interval import IntervalTrigger
from redis.asyncio import Redis

from app.config.setting import settings
from app.core.database import async_db_session
from app.core.logger import log
from app.core.redis_crud import RedisCURD

from ..asr_contract import SpeechUtterance
from ..mediakit_types import VolcMediaKitSubtitleCue
from ..planner import VideoEditPlan, VideoEditPlanner
from ..providers import build_asr_provider, build_public_media_provider
from ..storage import VideoObjectStorage
from .checkpoint import INITIAL_CHECKPOINT, ProcessingCheckpointMixin
from .context import (
    VideoInputAsset,
    VideoTaskCancelled,
    VideoTaskInputs,
)
from .stages.finalize import (
    create_review_asset,
    load_input_assets,
    record_media_cloud_metadata,
)
from .stages.media import prepare_processing_context
from .stages.render import run_processing_tail


class VideoProcessingWorker(ProcessingCheckpointMixin):
    """智能视频后台 worker，只负责调度和阶段编排。"""

    _job_id = "module_video_processing_worker"
    _claim_lock_key = "video:processing:claim"
    _running_tasks: dict[int, asyncio.Task] = {}

    @classmethod
    def register(cls, redis: Redis) -> None:
        """在 APScheduler 中注册智能视频扫描任务。"""
        if not settings.VIDEO_WORKER_ENABLED:
            log.info("智能视频 Worker 未启用，自动剪辑任务将停留在 queued")
            return

        from app.core.ap_scheduler import scheduler

        scheduler.add_job(
            func=cls.dispatch,
            trigger=IntervalTrigger(seconds=settings.VIDEO_WORKER_SCAN_INTERVAL_SECONDS),
            kwargs={"redis": redis},
            id=cls._job_id,
            name="智能视频任务扫描",
            coalesce=True,
            max_instances=1,
            replace_existing=True,
            jobstore="default",
            executor="default",
        )
        log.info("智能视频 Worker 已注册")

    @classmethod
    async def shutdown(cls) -> None:
        """关闭智能视频 worker 并取消本进程内仍在运行的任务。"""
        from app.core.ap_scheduler import scheduler

        job = scheduler.get_job(cls._job_id)
        if job is not None:
            scheduler.remove_job(job.id)

        running_tasks = list(cls._running_tasks.values())
        for task in running_tasks:
            task.cancel()
        if running_tasks:
            await asyncio.gather(*running_tasks, return_exceptions=True)
        cls._running_tasks.clear()

    @classmethod
    async def dispatch(cls, redis: Redis) -> None:
        """回收卡住的任务，再按并发上限领取 queued 任务交给后台协程。"""
        cls._running_tasks = {
            task_id: task
            for task_id, task in cls._running_tasks.items()
            if not task.done()
        }
        await cls._requeue_stale_tasks()
        available_slots = settings.VIDEO_WORKER_CONCURRENCY - len(cls._running_tasks)
        if available_slots <= 0:
            return

        for _ in range(available_slots):
            task_id = await cls._claim_next_task(redis)
            if task_id is None:
                return
            task = asyncio.create_task(cls._process_claimed_task(task_id))
            task.add_done_callback(
                lambda _task, claimed_id=task_id: cls._running_tasks.pop(claimed_id, None)
            )
            cls._running_tasks[task_id] = task

    @classmethod
    async def _requeue_stale_tasks(cls) -> None:
        """回收被后端重启打断的 processing 任务，让它们靠断点续跑。

        阈值直接复用任务超时：正常任务每轮轮询都写进度，`updated_time` 不会变旧，
        超过这个时长还没人写就必然是死了。排除本进程正在跑的任务只是兜底防重跑。
        回收失败不能拖垮扫描，否则一次 DB 抖动会让整个队列停摆。
        """
        from ..crud import VideoTaskCRUD

        try:
            async with async_db_session() as db:
                async with db.begin():
                    requeued = (
                        await VideoTaskCRUD.requeue_stale_processing_tasks_for_worker_crud(
                            db,
                            stale_seconds=settings.VIDEO_WORKER_TASK_TIMEOUT_SECONDS,
                            exclude_ids=list(cls._running_tasks),
                        )
                    )
        except Exception:
            log.exception("智能视频卡住任务回收失败")
            return
        if requeued:
            log.warning(f"智能视频回收卡住的 processing 任务并重新入队: task_ids={requeued}")

    @classmethod
    async def _claim_next_task(cls, redis: Redis) -> int | None:
        """使用 Redis 扫描锁和数据库行锁领取一个 queued 任务。"""
        redis_crud = RedisCURD(redis)
        locked, lock_value = await redis_crud.lock(cls._claim_lock_key, expire=30)
        if not locked:
            return None

        try:
            async with async_db_session() as db:
                async with db.begin():
                    task = await cls._claim_next_task_from_db(db)
                    return task.id if task is not None else None
        finally:
            await redis_crud.unlock(cls._claim_lock_key, lock_value)

    @staticmethod
    async def _claim_next_task_from_db(db):
        """从数据库领取一个 queued 任务。"""
        from ..crud import VideoTaskCRUD

        return await VideoTaskCRUD.claim_queued_task_for_worker_crud(db)

    @classmethod
    async def _process_claimed_task(cls, task_id: int) -> None:
        """按持久化断点执行云端自动剪辑流程。"""
        checkpoint: dict[str, Any] = dict(INITIAL_CHECKPOINT)
        try:
            speech_provider = build_asr_provider()
            public_bgm_provider = build_public_media_provider()
            inputs = await load_input_assets(task_id=task_id)
            checkpoint = cls._load_processing_checkpoint(inputs.checkpoint)
            cls._start_stage_timings(checkpoint)

            with tempfile.TemporaryDirectory(prefix="auto-nexus-video-") as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                context = await prepare_processing_context(
                    worker_cls=cls,
                    task_id=task_id,
                    inputs=inputs,
                    checkpoint=checkpoint,
                    temp_dir=temp_dir,
                    speech_provider=speech_provider,
                    public_bgm_provider=public_bgm_provider,
                )
                await run_processing_tail(
                    worker_cls=cls,
                    task_id=task_id,
                    inputs=inputs,
                    checkpoint=checkpoint,
                    context=context,
                    temp_dir=temp_dir,
                )

            await cls._set_task_status(task_id, "reviewing", 100, "reviewing")

        except VideoTaskCancelled:
            log.info(f"智能视频任务已取消，worker 停止处理: task_id={task_id}")
        except Exception as exc:
            log.exception(f"智能视频任务处理失败: task_id={task_id}, error={exc!s}")
            checkpoint["last_failed_stage"] = str(
                checkpoint.get("resume_stage") or "media_analysis"
            )
            checkpoint["last_error"] = str(exc)
            # 阶段没跑完就挂了，不清标记前端会一直显示「进行中」。
            cls._end_stage(checkpoint)
            try:
                await cls._save_processing_checkpoint(task_id, checkpoint)
            except Exception:
                log.exception(f"智能视频任务失败断点保存失败: task_id={task_id}")
            await cls._set_task_status(
                task_id,
                "failed",
                None,
                cls._public_task_stage(
                    str(checkpoint.get("resume_stage") or "media_analysis")
                ),
                str(exc),
            )

    @classmethod
    async def _load_input_assets(cls, task_id: int) -> VideoTaskInputs:
        """保留 worker 内部调用入口，实际读取逻辑位于 finalize 阶段。"""
        return await load_input_assets(task_id=task_id)

    @classmethod
    async def _record_media_cloud_metadata(
        cls,
        *,
        task_id: int,
        asset: VideoInputAsset,
        cloud_media: dict[str, Any],
        preprocess_metadata: dict[str, Any],
        speech_cleanup_metadata: dict[str, Any],
    ) -> None:
        """保留媒资记录入口，实际逻辑位于 finalize 阶段。"""
        await record_media_cloud_metadata(
            worker_cls=cls,
            task_id=task_id,
            asset=asset,
            cloud_media=cloud_media,
            preprocess_metadata=preprocess_metadata,
            speech_cleanup_metadata=speech_cleanup_metadata,
        )

    @classmethod
    async def _create_review_asset(cls, **kwargs: Any) -> None:
        """保留审核资产入口，实际逻辑位于 finalize 阶段。"""
        await create_review_asset(worker_cls=cls, **kwargs)

    @staticmethod
    def _build_edit_plan(
        *,
        task_no: str,
        config: dict[str, Any],
        source_duration_ms: int,
    ) -> VideoEditPlan:
        """生成可重复构建的源视频计划。"""
        return VideoEditPlanner.build_source_only_plan(
            task_no=task_no,
            config=config,
            source_duration_ms=source_duration_ms,
        )

    @staticmethod
    def _temp_asset_path(temp_dir: Path, asset: VideoInputAsset) -> Path:
        """按素材角色生成本地临时文件路径。"""
        suffix = PurePosixPath(asset.file_name).suffix or ".bin"
        return temp_dir / f"{asset.asset_role}-{asset.id}{suffix}"

    @staticmethod
    async def _download_input_asset(asset: VideoInputAsset, target_path: Path) -> None:
        """下载输入素材到阶段临时目录。"""
        await VideoObjectStorage.download_object_to_file(
            object_key=asset.object_key,
            target_path=target_path,
        )

    @staticmethod
    def _preprocessed_file_name(file_name: str) -> str:
        """生成预处理后文件名。"""
        stem = PurePosixPath(file_name).stem or "source"
        return f"{stem}-preprocessed.mp4"

    @staticmethod
    def _speech_cleanup_file_name(file_name: str) -> str:
        """生成口语清理后文件名。"""
        stem = PurePosixPath(file_name).stem or "source"
        return f"{stem}-speech-cleaned.mp4"

    @staticmethod
    def _ending_file_name(file_name: str) -> str:
        """统一片尾文件名。"""
        stem = PurePosixPath(file_name).stem or "ending"
        return f"{stem}-ending.mp4"

    @staticmethod
    def _build_media_kit_client_token(
        task_no: str,
        edit_plan: VideoEditPlan,
        stage: str,
    ) -> str:
        """按处理阶段生成 MediaKit 幂等凭证。"""
        token_digest = hashlib.sha1(
            f"{edit_plan.seed}:{stage}".encode()
        ).hexdigest()[:12]
        return f"{task_no[:32]}-v{edit_plan.version}-{stage}-{token_digest}"

    @staticmethod
    async def _download_cloud_file(url: str, target_path: Path) -> None:
        """将云端输出文件流式下载到本地临时文件。"""
        timeout = httpx.Timeout(connect=30.0, read=None, write=30.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with target_path.open("wb") as target_file:
                    async for chunk in response.aiter_bytes():
                        target_file.write(chunk)

    @staticmethod
    def _serialize_utterances_for_timeline(
        utterances: list[SpeechUtterance],
    ) -> list[dict[str, object]]:
        """把映射后的句段转换成时间线规划使用的轻量结构。"""
        return [
            {
                "start_ms": utterance.start_time_ms,
                "end_ms": utterance.end_time_ms,
                "text": utterance.text,
            }
            for utterance in utterances
            if utterance.text.strip() and utterance.end_time_ms > utterance.start_time_ms
        ]

    @staticmethod
    def _build_subtitle_cues_from_utterances(
        utterances: list[dict[str, object]],
    ) -> list[VolcMediaKitSubtitleCue]:
        """把时间线句段转换成统一字幕对象。"""
        return [
            VolcMediaKitSubtitleCue(
                subtitle_text=str(utterance["text"]),
                start_time=int(utterance["start_ms"]) / 1000,
                end_time=int(utterance["end_ms"]) / 1000,
            )
            for utterance in utterances
            if str(utterance.get("text") or "").strip()
        ]

    @classmethod
    async def _set_task_status(
        cls,
        task_id: int,
        status: str,
        progress: int | None = None,
        current_stage: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """更新 worker 任务状态。"""
        from ..crud import VideoTaskCRUD

        async with async_db_session() as db:
            async with db.begin():
                await VideoTaskCRUD.update_task_status_for_worker_crud(
                    db=db,
                    task_id=task_id,
                    status=status,
                    progress=progress,
                    current_stage=current_stage,
                    error_message=error_message,
                )

    @staticmethod
    async def _ensure_not_cancelled(task_id: int, db=None) -> None:
        """在长流程阶段边界确认用户未取消任务。"""
        from ..crud import VideoTaskCRUD

        if db is not None:
            task = await VideoTaskCRUD.get_task_for_worker_crud(db, task_id)
            if task is not None and task.process_status == "cancelled":
                raise VideoTaskCancelled
            return

        async with async_db_session() as session:
            task = await VideoTaskCRUD.get_task_for_worker_crud(session, task_id)
            if task is not None and task.process_status == "cancelled":
                raise VideoTaskCancelled
