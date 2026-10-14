from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import selectinload

from app.api.v1.module_system.auth.schema import AuthSchema
from app.config.setting import settings
from app.core.exceptions import CustomException
from app.core.logger import log

from .crud import VideoAssetCRUD, VideoTaskBatchCRUD, VideoTaskCRUD
from .model import VideoAssetModel, VideoTaskBatchModel, VideoTaskModel
from .processing_config import (
    COVER_PROMPT_PLACEHOLDERS,
    PLANNER_PROMPT_PLACEHOLDERS,
    check_prompt_template,
    load_processing_config,
    save_processing_config,
    with_prompt_defaults,
)
from .render_contract import DEFAULT_ASPECT_RATIO, DEFAULT_STYLE_PRESET
from .schema import (
    VideoAssetCreateSchema,
    VideoAssetDownloadOutSchema,
    VideoAssetMetadataOutSchema,
    VideoAssetOutSchema,
    VideoAssetUpdateSchema,
    VideoAssetUploadInitOutSchema,
    VideoAssetUploadInitSchema,
    VideoMultipartCompleteSchema,
    VideoMultipartPresignSchema,
    VideoProcessingConfigOutSchema,
    VideoProcessingConfigUpdateSchema,
    VideoTaskBatchCreateSchema,
    VideoTaskBatchDetailOutSchema,
    VideoTaskBatchQueryParam,
    VideoTaskCreateSchema,
    VideoTaskDebugOutSchema,
    VideoTaskDetailOutSchema,
    VideoTaskQueryParam,
    VideoTaskReviewSchema,
    VideoTaskStatusSchema,
)
from .storage import VideoObjectStorage


class VideoProcessingService:
    """智能视频输入、任务状态和成片输出服务。"""

    _INPUT_CONTENT_PREFIXES = {
        "source": "video/",
        "ending": "video/",
    }

    @classmethod
    async def create_task_service(
        cls, auth: AuthSchema, data: VideoTaskCreateSchema
    ) -> dict[str, Any]:
        """创建等待素材上传的自动剪辑任务。"""
        batch_crud = VideoTaskBatchCRUD(auth)
        task_crud = VideoTaskCRUD(auth)
        task_data = data.model_dump()
        batch_id = task_data.get("batch_id")
        if batch_id is None:
            batch = await batch_crud.create_batch_crud(
                VideoTaskBatchCreateSchema(
                    batch_name=task_data["title"],
                    batch_type="single",
                    expected_count=1,
                )
            )
            batch_id = batch.id
        else:
            await cls._require_batch(auth, batch_id)

        if int(task_data.get("batch_index") or 0) <= 0:
            task_data["batch_index"] = 1
        task_data["batch_id"] = batch_id
        task = await task_crud.create_task_crud(task_data)
        return await cls.get_task_service(auth, task.id)

    @classmethod
    async def create_batch_service(
        cls, auth: AuthSchema, data: VideoTaskBatchCreateSchema
    ) -> dict[str, Any]:
        """创建视频导入批次。"""
        batch = await VideoTaskBatchCRUD(auth).create_batch_crud(data)
        return await cls.get_batch_service(auth, batch.id)

    @classmethod
    async def list_tasks_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: VideoTaskQueryParam,
    ) -> dict[str, Any]:
        """分页查询当前用户的自动剪辑任务。"""
        return await VideoTaskCRUD(auth).page_tasks_crud(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            search=search.__dict__,
        )

    @classmethod
    async def list_batches_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: VideoTaskBatchQueryParam,
    ) -> dict[str, Any]:
        """分页查询当前用户的自动剪辑批次。"""
        return await VideoTaskBatchCRUD(auth).page_batches_crud(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            search=search.__dict__,
        )

    @classmethod
    async def get_task_service(cls, auth: AuthSchema, task_id: int) -> dict[str, Any]:
        """查询任务及全部输入输出素材。"""
        detail = await VideoTaskCRUD(auth).get_task_detail_crud(task_id)
        if detail is None:
            raise CustomException(msg="自动剪辑任务不存在")
        return VideoTaskDetailOutSchema.model_validate(detail).model_dump()

    @classmethod
    async def get_asset_metadata_service(
        cls, auth: AuthSchema, task_id: int, asset_id: int
    ) -> dict[str, Any]:
        """按需查询单个素材的完整媒体元数据。"""
        asset = await VideoTaskCRUD(auth).get_asset_metadata_crud(task_id, asset_id)
        if asset is None:
            raise CustomException(msg="视频素材不存在")
        return VideoAssetMetadataOutSchema.model_validate(asset).model_dump()

    @classmethod
    async def get_batch_service(cls, auth: AuthSchema, batch_id: int) -> dict[str, Any]:
        """查询批次及其全部子任务。"""
        batch = await cls._require_batch(
            auth,
            batch_id,
            preload=[
                selectinload(VideoTaskBatchModel.tasks).selectinload(VideoTaskModel.assets)
            ],
        )
        return VideoTaskBatchDetailOutSchema.model_validate(batch).model_dump()

    @classmethod
    async def initiate_asset_service(
        cls,
        auth: AuthSchema,
        task_id: int,
        data: VideoAssetUploadInitSchema,
    ) -> dict[str, Any]:
        """为单个输入素材创建 Multipart 会话。"""
        task = await cls._require_task(auth, task_id)
        if task.process_status not in {"draft", "uploading"}:
            raise CustomException(msg="当前任务状态不允许继续上传素材")

        expected_prefix = cls._INPUT_CONTENT_PREFIXES[data.asset_role]
        if not data.content_type.lower().startswith(expected_prefix):
            raise CustomException(msg=f"{data.asset_role} 素材类型与文件内容不匹配")

        object_key = VideoObjectStorage.build_object_key(
            task_no=task.task_no,
            asset_role=data.asset_role,
            file_name=data.file_name,
        )
        upload_session = await VideoObjectStorage.initiate_multipart(
            object_key=object_key,
            file_size=data.file_size,
            content_type=data.content_type,
        )

        try:
            asset = await VideoAssetCRUD(auth).create_asset_crud(
                VideoAssetCreateSchema(
                    task_id=task.id,
                    asset_role=data.asset_role,
                    file_name=data.file_name,
                    file_size=data.file_size,
                    content_type=data.content_type,
                    file_metadata={
                        "part_count": upload_session["part_count"],
                        "part_size": upload_session["part_size"],
                    },
                    bucket=settings.MINIO_BUCKET_NAME,
                    object_key=object_key,
                    upload_id=upload_session["upload_id"],
                    upload_status="uploading",
                )
            )
        except Exception:
            await VideoObjectStorage.abort_multipart(
                object_key=object_key,
                upload_id=upload_session["upload_id"],
            )
            raise

        await VideoTaskCRUD(auth).update_task_status_crud(
            id=task.id,
            data=VideoTaskStatusSchema(
                status="uploading",
                progress=0,
                current_stage="uploading",
                error_message=None,
            ),
        )
        return VideoAssetUploadInitOutSchema(
            asset_id=asset.id,
            upload_id=upload_session["upload_id"],
            bucket=settings.MINIO_BUCKET_NAME,
            object_key=object_key,
            part_size=upload_session["part_size"],
            parts=upload_session["parts"],
        ).model_dump()

    @classmethod
    async def complete_asset_service(
        cls,
        auth: AuthSchema,
        task_id: int,
        asset_id: int,
        data: VideoMultipartCompleteSchema,
    ) -> dict[str, Any]:
        """合并分片并将素材标记为可处理。"""
        await cls._require_task(auth, task_id)
        asset = await VideoAssetCRUD(auth).get_asset_by_id_crud(asset_id, preload=[])
        if asset is None or asset.task_id != task_id:
            raise CustomException(msg="视频素材不存在")
        if asset.upload_status != "uploading" or asset.upload_id != data.upload_id:
            raise CustomException(msg="视频素材上传会话无效")

        existing_object = await VideoObjectStorage.get_object_metadata(asset.object_key)
        if existing_object is not None:
            if existing_object["file_size"] != asset.file_size:
                raise CustomException(msg="视频对象已存在，但文件大小与素材记录不一致")
            return await cls._mark_asset_completed(
                auth=auth,
                asset=asset,
                etag=existing_object["etag"],
                verified_size=existing_object["file_size"],
            )

        expected_part_count = int(asset.file_metadata["part_count"])
        part_size = int(asset.file_metadata["part_size"])
        part_numbers = sorted(part.part_number for part in data.parts)
        if part_numbers != list(range(1, expected_part_count + 1)):
            raise CustomException(msg="视频素材分片不完整")

        uploaded_parts = await VideoObjectStorage.list_multipart_parts(
            object_key=asset.object_key,
            upload_id=data.upload_id,
        )
        uploaded_by_number = {part["part_number"]: part for part in uploaded_parts}
        if sorted(uploaded_by_number) != part_numbers:
            raise CustomException(msg="MinIO 实际接收的视频分片不完整")
        uploaded_size = sum(part["size"] for part in uploaded_parts)
        if uploaded_size != asset.file_size:
            raise CustomException(msg="MinIO 实际接收的视频文件大小不一致")

        expected_last_size = asset.file_size - part_size * (expected_part_count - 1)
        for part_number in part_numbers:
            expected_size = part_size if part_number < expected_part_count else expected_last_size
            if uploaded_by_number[part_number]["size"] != expected_size:
                raise CustomException(msg=f"视频素材第 {part_number} 个分片大小不一致")

        submitted_etags = {part.part_number: part.etag.strip('"') for part in data.parts}
        if any(
            submitted_etags[part_number] != uploaded_by_number[part_number]["etag"]
            for part_number in part_numbers
        ):
            raise CustomException(msg="视频素材分片 ETag 校验失败")

        completed = await VideoObjectStorage.complete_multipart(
            object_key=asset.object_key,
            upload_id=data.upload_id,
            parts=[part.model_dump() for part in data.parts],
        )
        return await cls._mark_asset_completed(
            auth=auth,
            asset=asset,
            etag=completed["etag"],
            verified_size=uploaded_size,
        )

    @staticmethod
    async def _mark_asset_completed(
        auth: AuthSchema,
        asset: VideoAssetModel,
        etag: str | None,
        verified_size: int,
    ) -> dict[str, Any]:
        """统一写入素材完成状态，供正常合并与幂等恢复复用。"""
        updated_asset = await VideoAssetCRUD(auth).update_asset_crud(
            id=asset.id,
            data=VideoAssetUpdateSchema(
                upload_status="completed",
                etag=etag,
                file_metadata={
                    **asset.file_metadata,
                    "verified_size": verified_size,
                },
            ),
        )
        if updated_asset is None:
            raise CustomException(msg="更新视频素材状态失败")
        return VideoAssetOutSchema.model_validate(updated_asset).model_dump()

    @staticmethod
    async def _require_batch(
        auth: AuthSchema,
        batch_id: int,
        preload: list[Any] | None = None,
    ) -> VideoTaskBatchModel:
        """按当前用户权限读取批次。"""
        batch = await VideoTaskBatchCRUD(auth).get_batch_by_id_crud(batch_id, preload=preload)
        if batch is None:
            raise CustomException(msg="视频批次不存在")
        return batch

    @classmethod
    async def refresh_asset_parts_service(
        cls,
        auth: AuthSchema,
        task_id: int,
        asset_id: int,
        data: VideoMultipartPresignSchema,
    ) -> list[dict[str, Any]]:
        """为长时间上传任务刷新尚未上传分片的短时签名。"""
        await cls._require_task(auth, task_id)
        asset = await VideoAssetCRUD(auth).get_asset_by_id_crud(asset_id, preload=[])
        if asset is None or asset.task_id != task_id:
            raise CustomException(msg="视频素材不存在")
        if asset.upload_status != "uploading" or asset.upload_id != data.upload_id:
            raise CustomException(msg="视频素材上传会话无效")

        part_count = int(asset.file_metadata["part_count"])
        part_numbers = sorted(set(data.part_numbers))
        if len(part_numbers) != len(data.part_numbers):
            raise CustomException(msg="刷新签名的分片序号不能重复")
        if part_numbers[0] < 1 or part_numbers[-1] > part_count:
            raise CustomException(msg="刷新签名的分片序号超出范围")
        return VideoObjectStorage.presign_upload_parts(
            object_key=asset.object_key,
            upload_id=data.upload_id,
            part_numbers=part_numbers,
        )

    @classmethod
    async def abort_asset_service(
        cls,
        auth: AuthSchema,
        task_id: int,
        asset_id: int,
    ) -> dict[str, Any]:
        """中止单个失败素材的 Multipart 会话并释放分片。"""
        await cls._require_task(auth, task_id)
        asset = await VideoAssetCRUD(auth).get_asset_by_id_crud(asset_id, preload=[])
        if asset is None or asset.task_id != task_id:
            raise CustomException(msg="视频素材不存在")
        if asset.upload_status != "uploading" or not asset.upload_id:
            raise CustomException(msg="视频素材没有可中止的上传会话")

        await VideoObjectStorage.abort_multipart(asset.object_key, asset.upload_id)
        updated_asset = await VideoAssetCRUD(auth).update_asset_crud(
            asset.id,
            VideoAssetUpdateSchema(upload_status="failed"),
        )
        if updated_asset is None:
            raise CustomException(msg="更新视频素材状态失败")
        return VideoAssetOutSchema.model_validate(updated_asset).model_dump()

    @classmethod
    async def submit_task_service(cls, auth: AuthSchema, task_id: int) -> dict[str, Any]:
        """校验输入素材完整后，将任务交给后续处理 worker。"""
        task = await cls._require_task(auth, task_id)
        if task.process_status not in {"draft", "uploading"}:
            raise CustomException(msg="当前任务状态不允许提交")
        if not any(
            asset.asset_role == "source" and asset.upload_status == "completed"
            for asset in task.assets
        ):
            raise CustomException(msg="至少需要一个已上传完成的原视频")
        if any(asset.upload_status != "completed" for asset in task.assets):
            raise CustomException(msg="仍有素材尚未上传完成")

        task.config = cls._reset_attempt_started_time(task.config)
        await auth.db.flush()
        await VideoTaskCRUD(auth).update_task_status_crud(
            id=task.id,
            data=VideoTaskStatusSchema(
                status="queued",
                progress=0,
                current_stage="queued",
                error_message=None,
            ),
        )
        return await cls.get_task_service(auth, task.id)

    @classmethod
    async def cancel_task_service(cls, auth: AuthSchema, task_id: int) -> dict[str, Any]:
        """取消任务，并清理仍未合并的 MinIO 分片。"""
        task = await cls._require_task(auth, task_id)
        if task.process_status in {"succeeded", "cancelled"}:
            raise CustomException(msg="当前任务状态不允许取消")

        asset_crud = VideoAssetCRUD(auth)
        for asset in task.assets:
            if asset.upload_status == "uploading" and asset.upload_id:
                await VideoObjectStorage.abort_multipart(asset.object_key, asset.upload_id)
                await asset_crud.update_asset_crud(
                    asset.id,
                    VideoAssetUpdateSchema(upload_status="failed"),
                )

        await VideoTaskCRUD(auth).update_task_status_crud(
            id=task.id,
            data=VideoTaskStatusSchema(status="cancelled"),
        )
        return await cls.get_task_service(auth, task.id)

    @classmethod
    async def retry_task_service(cls, auth: AuthSchema, task_id: int) -> dict[str, Any]:
        """将保留完整原视频的失败任务重新放入队列。"""
        task = await cls._require_task(auth, task_id)
        if task.process_status not in {"failed", "cancelled"}:
            raise CustomException(msg="只有失败或已取消的任务可以重试")
        if not any(
            asset.asset_role == "source" and asset.upload_status == "completed"
            for asset in task.assets
        ):
            raise CustomException(msg="原视频不完整，无法重试任务")

        task.config = cls._reset_attempt_started_time(task.config)
        await auth.db.flush()
        await VideoTaskCRUD(auth).update_task_status_crud(
            id=task.id,
            data=VideoTaskStatusSchema(
                status="queued",
                progress=0,
                current_stage="queued",
                error_message=None,
            ),
        )
        return await cls.get_task_service(auth, task.id)

    @classmethod
    async def review_task_service(
        cls,
        auth: AuthSchema,
        task_id: int,
        data: VideoTaskReviewSchema,
    ) -> dict[str, Any]:
        """处理待审核成片的通过或重新生成动作。"""
        if data.action == "approve":
            return await cls._approve_review_service(auth, task_id)
        return await cls._regenerate_review_service(auth, task_id, data)

    @classmethod
    async def _approve_review_service(cls, auth: AuthSchema, task_id: int) -> dict[str, Any]:
        """将最新待审核稿确认为最终成片。"""
        task = await cls._require_task(auth, task_id)
        if task.process_status != "reviewing":
            raise CustomException(msg="只有待审核任务可以确认成片")

        review_asset = cls._latest_completed_asset(task, "review")
        if review_asset is None:
            raise CustomException(msg="当前任务没有可确认的待审核成片")

        await VideoAssetCRUD(auth).create_asset_crud(
            VideoAssetCreateSchema(
                task_id=task.id,
                asset_role="output",
                file_name=f"{task.task_no}-output.mp4",
                file_size=review_asset.file_size,
                content_type=review_asset.content_type,
                file_metadata={
                    **review_asset.file_metadata,
                    "approved_review_asset_id": review_asset.id,
                },
                bucket=review_asset.bucket,
                object_key=review_asset.object_key,
                upload_id=None,
                upload_status="completed",
                etag=review_asset.etag,
            )
        )
        await VideoTaskCRUD(auth).update_task_status_crud(
            id=task.id,
            data=VideoTaskStatusSchema(
                status="succeeded",
                progress=100,
                current_stage="completed",
                error_message=None,
            ),
        )
        return await cls.get_task_service(auth, task.id)

    @classmethod
    async def _regenerate_review_service(
        cls,
        auth: AuthSchema,
        task_id: int,
        data: VideoTaskReviewSchema,
    ) -> dict[str, Any]:
        """基于源视频和历史审核意见重新排队生成新版本。

        `reviewing` 是「这一版不满意」，`succeeded` 是「改了全局配置想重跑」；
        两者都是重出一版，区别只在用户从哪个状态点进来。
        """
        task = await cls._require_task(auth, task_id)
        if task.process_status not in {"reviewing", "succeeded"}:
            raise CustomException(msg="只有待审核或已完成的任务可以重新生成")
        if not any(
            asset.asset_role == "source" and asset.upload_status == "completed"
            for asset in task.assets
        ):
            raise CustomException(msg="原视频不完整，无法重新生成")

        config = dict(task.config or {})
        current_version = int(config.get("review_version") or 1)
        next_version = current_version + 1
        review_history = list(config.get("review_history") or [])
        review_history.append({
            "version": current_version,
            "action": "regenerate",
            "adjustment_prompt": data.adjustment_prompt or "",
        })
        config["review_version"] = next_version
        # 重新生成仍固定使用竖屏日常 Vlog 模式，只更新版本和审核意见。
        config["aspect_ratio"] = DEFAULT_ASPECT_RATIO
        config["style_preset"] = DEFAULT_STYLE_PRESET
        config["review_seed"] = (
            f"{task.task_no}:v{next_version}:{DEFAULT_STYLE_PRESET}"
        )
        config["adjustment_prompt"] = data.adjustment_prompt or ""
        config["review_history"] = review_history
        config["attempt_started_time"] = None
        # 生图通道已收归全局配置，老任务里冻结的任务级值会盖掉管理员的新设置，清掉。
        config.pop("cover_image_provider", None)
        # 审核重新生成是新版本，不继承上一版本的处理断点：断点在独立表里，删行；
        # config 里的旧键是迁移前的遗留，顺手清掉。
        await VideoTaskCRUD.delete_task_checkpoint_crud(auth.db, task.id)
        config.pop("processing_checkpoint", None)

        # 重新生成复用源素材和历史配置，只把任务重新放回 worker 队列。
        task.config = config
        task.process_status = "queued"
        task.progress = 0
        task.current_stage = "queued"
        task.error_message = None
        await auth.db.flush()
        # 批次汇总不会自己跟着子任务变：不同步的话「已完成」的批次不会重新进轮询。
        await VideoTaskBatchCRUD.sync_batch_summary_for_db(auth.db, task.batch_id)
        return await cls.get_task_service(auth, task.id)

    @staticmethod
    def _reset_attempt_started_time(config: dict[str, Any] | None) -> dict[str, Any]:
        """重置本次尝试开始时间，等待 worker 真正领取任务后再写入。"""
        next_config = dict(config or {})
        next_config["attempt_started_time"] = None
        return next_config

    @classmethod
    async def get_asset_download_service(
        cls,
        auth: AuthSchema,
        task_id: int,
        asset_id: int,
        download: bool,
    ) -> dict[str, Any]:
        """为当前用户的成片、字幕或封面生成短时读取地址。"""
        await cls._require_task(auth, task_id)
        asset = await VideoAssetCRUD(auth).get_asset_by_id_crud(asset_id, preload=[])
        if asset is None or asset.task_id != task_id:
            raise CustomException(msg="视频产物不存在")
        if asset.asset_role not in {"review", "output", "subtitle", "cover", "ending"}:
            raise CustomException(msg="该素材不是可下载产物")
        if asset.upload_status != "completed":
            raise CustomException(msg="视频产物尚未生成完成")

        return VideoAssetDownloadOutSchema(
            url=VideoObjectStorage.presign_download(
                object_key=asset.object_key,
                file_name=asset.file_name,
                attachment=download,
            ),
            expires_in=settings.MINIO_PRESIGNED_EXPIRE_SECONDS,
        ).model_dump()

    @classmethod
    async def get_task_debug_service(cls, auth: AuthSchema, task_id: int) -> dict[str, Any]:
        """汇总本次任务实际用到的提示词与生图参考帧，供详情页调试。

        提示词可在高级设置里改，只有任务上留的这份快照能回答「当时发了什么」。
        老任务没有这些字段，一律返回 null，前端按「未记录」展示。
        """
        task = await VideoTaskCRUD(auth).get_task_by_id_crud(id=task_id, preload=[])
        if task is None:
            raise CustomException(msg="自动剪辑任务不存在")

        review_metadata = await VideoTaskCRUD.get_latest_asset_metadata_crud(
            auth.db, task_id, "review"
        )
        cover_metadata = await VideoTaskCRUD.get_latest_asset_metadata_crud(
            auth.db, task_id, "cover"
        )
        creative_plan = dict((review_metadata or {}).get("timeline_render_plan") or {})
        cover = dict(cover_metadata or {})
        if not cover:
            # 封面素材被清理时，review 元数据里还嵌着一份封面信息。
            cover = dict(
                ((review_metadata or {}).get("video_enhancements") or {}).get("cover") or {}
            )

        reference_key = cover.get("cover_reference_object_key")
        reference_url = (
            VideoObjectStorage.presign_download(
                object_key=str(reference_key),
                file_name=str(cover.get("cover_source_frame_name") or "cover-reference.jpg"),
                attachment=False,
            )
            if reference_key
            else None
        )
        return VideoTaskDebugOutSchema(
            planner_model=creative_plan.get("planner_model"),
            planner_system_prompt=creative_plan.get("system_prompt"),
            planner_user_prompt=creative_plan.get("user_prompt"),
            cover_image_provider=cover.get("cover_image_provider"),
            cover_image_model=cover.get("cover_image_model"),
            cover_image_size=cover.get("cover_image_size"),
            cover_summary_model=cover.get("cover_summary_model"),
            cover_image_prompt=cover.get("cover_image_prompt"),
            cover_prompt=cover.get("cover_prompt"),
            cover_reference_url=reference_url,
            cover_reference_name=cover.get("cover_source_frame_name"),
        ).model_dump()

    @classmethod
    async def get_processing_config_service(cls, auth: AuthSchema) -> dict[str, Any]:
        """读取自动剪辑全局配置（管理员高级设置）。"""
        return cls._config_out(await load_processing_config())

    @classmethod
    async def update_processing_config_service(
        cls,
        auth: AuthSchema,
        data: VideoProcessingConfigUpdateSchema,
    ) -> dict[str, Any]:
        """保存全局配置，只覆盖显式提交的字段。

        不提交的字段保持原值；提交 null 表示恢复默认（读取时回落到 env / 内置值）。
        """
        payload = data.model_dump(exclude_unset=True)
        cls._validate_prompt_templates(payload)
        saved = await save_processing_config(
            auth.db,
            payload,
            auth.user.id if auth.user else None,
        )
        log.info(
            "自动剪辑全局配置已更新: "
            f"version={saved.get('version')}, "
            f"changed={sorted(payload.keys())}, "
            f"updated_by={saved.get('updated_by')}"
        )
        return cls._config_out(saved)

    @staticmethod
    def _config_out(config: dict[str, Any]) -> dict[str, Any]:
        """全局配置的统一出口：补上内置默认提示词原文。"""
        return VideoProcessingConfigOutSchema.model_validate(
            with_prompt_defaults(config)
        ).model_dump()

    @classmethod
    async def list_cover_image_models_service(cls, auth: AuthSchema) -> list[dict[str, Any]]:
        """列出中转站支持生图的模型，供高级设置的模型下拉使用。

        中转站的公开模型清单挂在站点根的 `/api/pricing`，不需要密钥。拉不到就返回
        空数组，前端回落成手填输入框 —— 只是少个便利，不该把高级设置整块打不开。
        """
        base_url = str(settings.COVER_RELAY_API_URL or "").rstrip("/")
        # COVER_RELAY_API_URL 指向 /v1，模型清单在站点根上。
        if base_url.endswith("/v1"):
            base_url = base_url[: -len("/v1")]
        if not base_url:
            return []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(f"{base_url}/api/pricing")
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning(f"获取中转站生图模型清单失败: {exc}")
            return []

        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            return []
        models: list[dict[str, Any]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            name = str(item.get("model_name") or "").strip()
            endpoints = [str(entry) for entry in (item.get("supported_endpoint_types") or [])]
            # 只要支持生图端点的；纯对话模型不给选，避免误填到生图配置上。
            if name and "image-generation" in endpoints:
                models.append({"name": name, "endpoint_types": endpoints})
        models.sort(key=lambda item: item["name"])
        return models

    @staticmethod
    def _validate_prompt_templates(payload: dict[str, Any]) -> None:
        """校验提示词模板里的契约占位符。

        占位符由代码注入枚举清单、时长预算、构图安全区。删掉或写错会让模型
        吐出枚举外的值，下游解析只是静默丢弃、不报错 —— 与其等成片出来才发现，
        不如在保存这一步直接拒掉。空串/null 表示恢复默认，不校验。
        """
        checks = (
            ("cover_prompt_template", COVER_PROMPT_PLACEHOLDERS),
            ("planner_prompt_template", PLANNER_PROMPT_PLACEHOLDERS),
        )
        for field, required in checks:
            template = payload.get(field)
            if not isinstance(template, str) or not template.strip():
                continue
            missing, unknown = check_prompt_template(template, required)
            if missing:
                names = "、".join("{{" + name + "}}" for name in missing)
                raise CustomException(msg=f"{field} 缺少必需占位符: {names}")
            if unknown:
                names = "、".join("{{" + name + "}}" for name in unknown)
                raise CustomException(msg=f"{field} 含未知占位符: {names}")

    @staticmethod
    async def _require_task(auth: AuthSchema, task_id: int) -> VideoTaskModel:
        """读取当前用户任务，统一处理越权和不存在场景。"""
        task = await VideoTaskCRUD(auth).get_task_by_id_crud(
            id=task_id,
            preload=["assets"],
        )
        if task is None:
            raise CustomException(msg="自动剪辑任务不存在")
        return task

    @staticmethod
    def _latest_completed_asset(
        task: VideoTaskModel,
        asset_role: str,
    ) -> VideoAssetModel | None:
        """读取指定角色的最新完成资产，用于审核稿确认和预览。"""
        completed_assets = [
            asset
            for asset in task.assets
            if asset.asset_role == asset_role and asset.upload_status == "completed"
        ]
        if not completed_assets:
            return None
        return max(completed_assets, key=lambda asset: asset.id)
