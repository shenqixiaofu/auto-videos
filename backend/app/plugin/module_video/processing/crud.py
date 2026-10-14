import json
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.module_system.auth.schema import AuthSchema
from app.config.setting import settings
from app.core.base_crud import CRUDBase
from app.core.permission import Permission

from .model import (
    VideoAssetModel,
    VideoAssetRoleEnum,
    VideoTaskBatchModel,
    VideoTaskCheckpointModel,
    VideoTaskModel,
    VideoTaskStatusEnum,
    VideoUploadStatusEnum,
)
from .schema import (
    VideoAssetCreateSchema,
    VideoAssetUpdateSchema,
    VideoTaskBatchCreateSchema,
    VideoTaskBatchListOutSchema,
    VideoTaskConfigSchema,
    VideoTaskCreateSchema,
    VideoTaskListOutSchema,
    VideoTaskStatusSchema,
    VideoTaskUpdateSchema,
)
from .storage import VideoObjectStorage

# 批次列表只展示这些字段：不做关系加载的投影查询，列清单与
# VideoTaskBatchListOutSchema 一一对应，改 schema 时同步改这里。
_BATCH_LIST_COLUMNS = (
    VideoTaskBatchModel.id,
    VideoTaskBatchModel.batch_no,
    VideoTaskBatchModel.batch_name,
    VideoTaskBatchModel.batch_type,
    VideoTaskBatchModel.expected_count,
    VideoTaskBatchModel.task_count,
    VideoTaskBatchModel.completed_count,
    VideoTaskBatchModel.process_status,
    VideoTaskBatchModel.progress,
    VideoTaskBatchModel.current_stage,
    VideoTaskBatchModel.error_message,
    VideoTaskBatchModel.created_time,
    VideoTaskBatchModel.updated_time,
)

# 子任务摘要。config 里只剩小字段（断点已搬去 video_task_checkpoint 表），直接选。
_TASK_LIST_COLUMNS = (
    VideoTaskModel.id,
    VideoTaskModel.task_no,
    VideoTaskModel.title,
    VideoTaskModel.batch_id,
    VideoTaskModel.batch_index,
    VideoTaskModel.process_status,
    VideoTaskModel.progress,
    VideoTaskModel.current_stage,
    VideoTaskModel.config,
    VideoTaskModel.error_message,
    VideoTaskModel.created_time,
    VideoTaskModel.updated_time,
)

# 任务详情，列清单与 VideoTaskDetailOutSchema 一一对应。
_DETAIL_TASK_COLUMNS = (
    VideoTaskModel.id,
    VideoTaskModel.task_no,
    VideoTaskModel.title,
    VideoTaskModel.batch_id,
    VideoTaskModel.batch_index,
    VideoTaskModel.process_status,
    VideoTaskModel.progress,
    VideoTaskModel.current_stage,
    VideoTaskModel.config,
    VideoTaskModel.error_message,
    VideoTaskModel.created_time,
    VideoTaskModel.updated_time,
)

# 详情里的素材。**故意不含 file_metadata** —— 那是完整时间线 JSON（单条最大
# 200KB+），前端只在一个折叠区里展示，改成展开时走 assets/{id}/metadata 按需拉。
_DETAIL_ASSET_COLUMNS = (
    VideoAssetModel.id,
    VideoAssetModel.task_id,
    VideoAssetModel.asset_role,
    VideoAssetModel.file_name,
    VideoAssetModel.file_size,
    VideoAssetModel.content_type,
    VideoAssetModel.bucket,
    VideoAssetModel.object_key,
    VideoAssetModel.upload_id,
    VideoAssetModel.upload_status,
    VideoAssetModel.etag,
    VideoAssetModel.created_time,
    VideoAssetModel.updated_time,
)


def _build_batch_conditions(search: dict[str, Any] | None) -> list[Any]:
    """把批次查询参数转成 SQL 条件。

    与 CRUDBase 的同名私有实现语义一致，只实现批次查询用得到的操作符；
    那边新增操作符时这里要同步。
    """
    conditions: list[Any] = []
    for key, value in (search or {}).items():
        if value is None or value == "":
            continue
        attr = getattr(VideoTaskBatchModel, key)
        if not isinstance(value, tuple):
            conditions.append(attr == value)
            continue
        operation, operand = value
        if operand is None or operand == "":
            continue
        if operation == "like":
            conditions.append(attr.like(f"%{operand}%"))
        elif operation == "between" and isinstance(operand, (list, tuple)) and len(operand) == 2:
            conditions.append(attr.between(operand[0], operand[1]))
        elif operation == "in":
            conditions.append(attr.in_(operand))
        elif operation in {"==", "eq"}:
            conditions.append(attr == operand)
        elif operation in {"!=", "ne"}:
            conditions.append(attr != operand)
    return conditions


def _load_json_object(value: Any) -> dict[str, Any]:
    """把 JSON_REMOVE 之类函数表达式返回的原始字符串还原成 dict。"""
    if isinstance(value, dict):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _pick_cover_url(covers: list[dict[str, Any]]) -> str | None:
    """取最新已完成封面的预览地址，口径同 VideoTaskModel.cover_preview_url。

    预览优先用 JPEG 缩略图（前端展示用），旧任务没有缩略图就回落原图。
    用户点「下载封面」走的是 asset 的 object_key（原图 PNG），不经过这里。
    """
    completed = [
        cover
        for cover in covers
        if cover["upload_status"] == VideoUploadStatusEnum.COMPLETED.value
    ]
    if not completed:
        return None
    latest = max(completed, key=lambda cover: cover["created_time"])
    return VideoObjectStorage.presign_download(
        object_key=latest.get("cover_thumbnail_key") or latest["object_key"],
        file_name=latest["file_name"],
        attachment=False,
    )


def _pick_task_finished_time(
    task: dict[str, Any], reviews: list[dict[str, Any]]
) -> datetime | None:
    """口径同 VideoTaskModel.finished_time：只认当前版本的已完成审核产物。"""
    current_version = int(task["config"].get("review_version") or 1)
    matched = [
        review
        for review in reviews
        if review["upload_status"] == VideoUploadStatusEnum.COMPLETED.value
        and int(review["review_version"] or 0) == current_version
    ]
    if matched:
        return max(matched, key=lambda review: review["created_time"])["created_time"]
    if task["process_status"] in {
        VideoTaskStatusEnum.FAILED.value,
        VideoTaskStatusEnum.CANCELLED.value,
    }:
        return task["updated_time"]
    return None


def _pick_batch_finished_time(
    batch: dict[str, Any], tasks: list[dict[str, Any]]
) -> datetime | None:
    """口径同 VideoTaskBatchModel.finished_time。"""
    finished_statuses = {
        VideoTaskStatusEnum.SUCCEEDED.value,
        VideoTaskStatusEnum.FAILED.value,
        VideoTaskStatusEnum.CANCELLED.value,
    }
    finished_tasks = [
        task for task in tasks if task["process_status"] in finished_statuses
    ]
    if finished_tasks:
        return max(finished_tasks, key=lambda task: task["updated_time"])["updated_time"]
    if batch["process_status"] in finished_statuses:
        return batch["updated_time"]
    return None


class VideoTaskBatchCRUD(
    CRUDBase[VideoTaskBatchModel, VideoTaskBatchCreateSchema, VideoTaskBatchCreateSchema]
):
    """自动剪辑批次数据层。"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=VideoTaskBatchModel, auth=auth)

    async def create_batch_crud(self, data: VideoTaskBatchCreateSchema) -> VideoTaskBatchModel:
        """创建批次记录。"""
        batch = await self.create(data=data)
        await self.sync_batch_summary_for_db(self.auth.db, batch.id)
        refreshed = await self.get_batch_by_id_crud(batch.id, preload=[])
        return refreshed or batch

    async def get_batch_by_id_crud(
        self, id: int, preload: list[str | Any] | None = None
    ) -> VideoTaskBatchModel | None:
        """查询当前用户的批次详情。"""
        return await self.get(id=id, created_id=self.auth.user.id, preload=preload)

    async def page_batches_crud(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
    ) -> dict:
        """分页查询当前用户的批次列表。

        列表字段比详情少得多，但关系是 mapper 级 lazy="selectin" —— 只要加载
        批次实体，tasks / assets / created_by 就会连带拉出来，created_by 指向
        的 user 又级联出 dept / roles / positions。实测这样一条列表要发 45 条
        SQL，其中 42 条是权限表，而列表 schema 里连 created_by 都不下发。

        所以这里不走基类的 ORM 分页，改为投影查询：三次取数，不加载关系、
        也不实例化 ORM 对象，关系部分在内存里按 schema 需要拼。
        """
        conditions = _build_batch_conditions(search)
        permission = Permission(model=VideoTaskBatchModel, auth=self.auth)
        db = self.auth.db

        count_stmt = await permission.filter_query(
            select(func.count(VideoTaskBatchModel.id))
            .select_from(VideoTaskBatchModel)
            .where(*conditions)
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        page_stmt = await permission.filter_query(
            select(*_BATCH_LIST_COLUMNS)
            .where(*conditions)
            .order_by(VideoTaskBatchModel.created_time.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await db.execute(page_stmt)).all()
        batches = [dict(row._mapping) for row in rows]
        if batches:
            await self._fill_batch_list_relations(batches)

        return {
            "page_no": offset // limit + 1 if limit else 1,
            "page_size": limit or 10,
            "total": total,
            "has_next": offset + limit < total,
            "items": [
                VideoTaskBatchListOutSchema.model_validate(batch).model_dump()
                for batch in batches
            ],
        }

    async def _fill_batch_list_relations(self, batches: list[dict[str, Any]]) -> None:
        """就地补齐列表要展示的关系数据：子任务摘要与封面、完成时间。"""
        db = self.auth.db
        batch_ids = [batch["id"] for batch in batches]

        # 排序放在内存里：MySQL 的 filesort 要把整行塞进 sort_buffer（默认 256KB，
        # 实测阈值约 140KB），一旦有宽字段就报 1038 Out of sort memory。行数只有
        # 一页批次那么多，不值当冒这个险。
        task_rows = (
            await db.execute(
                select(*_TASK_LIST_COLUMNS).where(VideoTaskModel.batch_id.in_(batch_ids))
            )
        ).all()
        tasks = [dict(row._mapping) for row in task_rows]
        tasks.sort(key=lambda task: (int(task["batch_index"] or 0), task["id"]))
        tasks_by_batch: dict[int, list[dict[str, Any]]] = {}
        for task in tasks:
            task["config"] = _load_json_object(task["config"])
            tasks_by_batch.setdefault(task["batch_id"], []).append(task)

        related_assets = await self._load_batch_list_assets([task["id"] for task in tasks])
        for task in tasks:
            assets = related_assets.get(task["id"], {"cover": [], "review": []})
            task["cover_preview_url"] = _pick_cover_url(assets["cover"])
            task["finished_time"] = _pick_task_finished_time(task, assets["review"])

        for batch in batches:
            batch_tasks = tasks_by_batch.get(batch["id"], [])
            batch["tasks"] = batch_tasks
            batch["cover_preview_url"] = next(
                (
                    task["cover_preview_url"]
                    for task in batch_tasks
                    if task["cover_preview_url"]
                ),
                None,
            )
            batch["finished_time"] = _pick_batch_finished_time(batch, batch_tasks)

    async def _load_batch_list_assets(
        self, task_ids: list[int]
    ) -> dict[int, dict[str, list[dict[str, Any]]]]:
        """按任务取封面与审核素材的最小字段，够算缩略图和完成时间即可。"""
        if not task_ids:
            return {}
        rows = (
            await self.auth.db.execute(
                select(
                    VideoAssetModel.id,
                    VideoAssetModel.task_id,
                    VideoAssetModel.asset_role,
                    VideoAssetModel.upload_status,
                    VideoAssetModel.object_key,
                    VideoAssetModel.file_name,
                    VideoAssetModel.created_time,
                    # 只要版本号和缩略图 key，不打整份 file_metadata —— 里面是完整时间线 JSON。
                    func.json_unquote(
                        func.json_extract(VideoAssetModel.file_metadata, "$.review_version")
                    ).label("review_version"),
                    func.json_unquote(
                        func.json_extract(
                            VideoAssetModel.file_metadata, "$.cover_thumbnail_key"
                        )
                    ).label("cover_thumbnail_key"),
                )
                .where(
                    VideoAssetModel.task_id.in_(task_ids),
                    VideoAssetModel.asset_role.in_(
                        [
                            VideoAssetRoleEnum.COVER.value,
                            VideoAssetRoleEnum.REVIEW.value,
                        ]
                    ),
                )
                # 同样不排序：file_metadata 是 200KB+ 的宽 JSON 列，带上排序会踩 1038。
                # 下游 _pick_cover_url / _pick_task_finished_time 都按时间戳取 max，与顺序无关。
            )
        ).all()

        grouped: dict[int, dict[str, list[dict[str, Any]]]] = {}
        for row in rows:
            asset = dict(row._mapping)
            bucket = grouped.setdefault(asset["task_id"], {"cover": [], "review": []})
            key = "cover" if asset["asset_role"] == VideoAssetRoleEnum.COVER.value else "review"
            bucket[key].append(asset)
        return grouped

    @staticmethod
    async def get_batch_for_worker_crud(
        db: AsyncSession, batch_id: int
    ) -> VideoTaskBatchModel | None:
        """worker 按 ID 读取批次与子任务，不套用户权限过滤。"""
        statement = (
            select(VideoTaskBatchModel)
            .where(VideoTaskBatchModel.id == batch_id)
            .options(selectinload(VideoTaskBatchModel.tasks).selectinload(VideoTaskModel.assets))
        )
        result = await db.execute(statement)
        return result.scalars().first()

    @staticmethod
    async def sync_batch_summary_for_db(
        db: AsyncSession,
        batch_id: int | None,
    ) -> VideoTaskBatchModel | None:
        """根据子任务状态同步批次汇总字段。"""
        if batch_id is None:
            return None

        batch = await VideoTaskBatchCRUD.get_batch_for_worker_crud(db, batch_id)
        if batch is None:
            return None

        tasks = sorted(
            batch.tasks,
            key=lambda task: (int(task.batch_index or 0), task.id),
        )
        expected_count = max(int(batch.expected_count or 0), 1)
        batch.task_count = len(tasks)
        batch.completed_count = sum(
            1
            for task in tasks
            if task.process_status
            in {
                "succeeded",
                "failed",
                "cancelled",
            }
        )
        batch.progress = min(
            100,
            max(
                0,
                round(
                    sum(int(task.progress or 0) for task in tasks) / expected_count
                ),
            ),
        )

        active_tasks = [
            task
            for task in tasks
            if task.process_status in {"uploading", "queued", "processing", "reviewing"}
        ]
        if active_tasks:
            current_task = active_tasks[0]
            batch.process_status = current_task.process_status
            batch.current_stage = current_task.current_stage
            batch.error_message = None
        elif not tasks:
            batch.process_status = "draft"
            batch.current_stage = "draft"
            batch.error_message = None
        elif any(task.process_status == "failed" for task in tasks):
            failed_task = next(task for task in tasks if task.process_status == "failed")
            batch.process_status = "failed"
            batch.current_stage = failed_task.current_stage
            batch.error_message = failed_task.error_message
        elif any(task.process_status == "cancelled" for task in tasks):
            cancelled_task = next(task for task in tasks if task.process_status == "cancelled")
            batch.process_status = "cancelled"
            batch.current_stage = cancelled_task.current_stage
            batch.error_message = cancelled_task.error_message
        elif all(task.process_status == "succeeded" for task in tasks):
            batch.process_status = "succeeded"
            batch.current_stage = "completed"
            batch.error_message = None
        else:
            batch.process_status = "draft"
            batch.current_stage = "draft"
            batch.error_message = None

        await db.flush()
        await db.refresh(batch, attribute_names=["tasks"])
        return batch


class VideoTaskCRUD(CRUDBase[VideoTaskModel, VideoTaskCreateSchema, VideoTaskUpdateSchema]):
    """自动剪辑任务数据层。"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=VideoTaskModel, auth=auth)

    async def create_task_crud(
        self, data: VideoTaskCreateSchema | dict[str, Any]
    ) -> VideoTaskModel:
        """创建草稿任务，并将固定剪辑选项写入配置字段。"""
        data_dict = data if isinstance(data, dict) else data.model_dump()
        config = VideoTaskConfigSchema(
            aspect_ratio=data_dict["aspect_ratio"],
            style_preset=data_dict["style_preset"],
            cover_image_provider=data_dict.get("cover_image_provider"),
            # 当前成片固定带字幕，不再暴露用户开关。
            subtitle_enabled=True,
        )
        task = await self.create(
            data={
                "batch_id": data_dict["batch_id"],
                "batch_index": int(data_dict.get("batch_index") or 1),
                "title": data_dict["title"],
                "config": config.model_dump(),
                "process_status": "draft",
                "progress": 0,
                "current_stage": "draft",
            }
        )
        await VideoTaskBatchCRUD.sync_batch_summary_for_db(self.auth.db, task.batch_id)
        refreshed = await self.get_task_by_id_crud(task.id, preload=["assets"])
        return refreshed or task

    async def get_task_by_id_crud(
        self, id: int, preload: list[str | Any] | None = None
    ) -> VideoTaskModel | None:
        """查询当前用户的任务详情。"""
        return await self.get(id=id, created_id=self.auth.user.id, preload=preload)

    async def get_task_detail_crud(self, id: int) -> dict[str, Any] | None:
        """投影查询任务详情，不加载关系也不实例化 ORM 对象。

        详情 schema 里没有 created_by / updated_by，但 model 的
        __loader_options__ 会连带拉出 user → dept / roles / positions；assets
        又是 mapper 级 lazy="selectin"。实测走 ORM 取一条详情要发 45 条 SQL，
        其中 42 条是权限表。关系部分在内存里按 schema 需要拼。
        """
        db = self.auth.db
        permission = Permission(model=VideoTaskModel, auth=self.auth)
        task_stmt = await permission.filter_query(
            select(*_DETAIL_TASK_COLUMNS).where(
                VideoTaskModel.id == id,
                VideoTaskModel.created_id == self.auth.user.id,
            )
        )
        row = (await db.execute(task_stmt)).first()
        if row is None:
            return None
        task = dict(row._mapping)
        task["config"] = _load_json_object(task["config"])

        asset_rows = (
            await db.execute(
                select(
                    *_DETAIL_ASSET_COLUMNS,
                    # 完成时间要按审核版本比对；缩略图 key 给封面预览用，都只取单键。
                    func.json_unquote(
                        func.json_extract(VideoAssetModel.file_metadata, "$.review_version")
                    ).label("review_version"),
                    func.json_unquote(
                        func.json_extract(
                            VideoAssetModel.file_metadata, "$.cover_thumbnail_key"
                        )
                    ).label("cover_thumbnail_key"),
                )
                .where(VideoAssetModel.task_id == id)
                # 排序挪到内存：select 里带 file_metadata 的 JSON 表达式，交给 MySQL
                # 排序会把整行塞进 sort_buffer，宽素材照样报 1038。
            )
        ).all()
        assets = [dict(asset_row._mapping) for asset_row in asset_rows]
        assets.sort(key=lambda asset: asset["id"])

        covers = [asset for asset in assets if asset["asset_role"] == VideoAssetRoleEnum.COVER.value]
        reviews = [
            asset for asset in assets if asset["asset_role"] == VideoAssetRoleEnum.REVIEW.value
        ]
        task["cover_preview_url"] = _pick_cover_url(covers)
        task["finished_time"] = _pick_task_finished_time(task, reviews)
        task["assets"] = assets
        return task

    async def get_asset_metadata_crud(self, task_id: int, asset_id: int) -> dict[str, Any] | None:
        """按需取单个素材的完整媒体元数据，含完整时间线 JSON。"""
        permission = Permission(model=VideoTaskModel, auth=self.auth)
        stmt = await permission.filter_query(
            select(
                VideoAssetModel.id.label("asset_id"),
                VideoAssetModel.asset_role,
                VideoAssetModel.file_metadata,
            )
            .join(VideoTaskModel, VideoTaskModel.id == VideoAssetModel.task_id)
            .where(
                VideoAssetModel.id == asset_id,
                VideoTaskModel.id == task_id,
                VideoTaskModel.created_id == self.auth.user.id,
            )
        )
        row = (await self.auth.db.execute(stmt)).first()
        if row is None:
            return None
        asset = dict(row._mapping)
        asset["file_metadata"] = _load_json_object(asset["file_metadata"])
        return asset

    async def list_tasks_crud(
        self,
        search: dict[str, Any] | None = None,
        order_by: list[dict[str, str]] | None = None,
        preload: list[str | Any] | None = None,
    ) -> Sequence[VideoTaskModel]:
        """查询当前用户的任务列表。"""
        owned_search = dict(search or {})
        owned_search["created_id"] = self.auth.user.id
        return await self.list(search=owned_search, order_by=order_by, preload=preload)

    async def page_tasks_crud(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        """分页查询当前用户的任务列表。"""
        owned_search = dict(search or {})
        owned_search["created_id"] = self.auth.user.id
        return await self.page(
            offset=offset,
            limit=limit,
            order_by=order_by or [{"created_time": "desc"}],
            search=owned_search,
            out_schema=VideoTaskListOutSchema,
            # 列表需要素材创建时间来计算成片生成结束时间。
            preload=["assets"],
        )

    async def update_task_crud(self, id: int, data: VideoTaskUpdateSchema) -> VideoTaskModel | None:
        """更新当前用户的任务基础信息。"""
        task = await self.get_task_by_id_crud(id=id, preload=[])
        if task is None:
            return None
        updated = await self.update(id=id, data=data)
        await VideoTaskBatchCRUD.sync_batch_summary_for_db(self.auth.db, task.batch_id)
        return updated

    async def update_task_status_crud(
        self, id: int, data: VideoTaskStatusSchema
    ) -> VideoTaskModel | None:
        """更新当前用户任务的执行状态与进度。"""
        task = await self.get_task_by_id_crud(id=id, preload=[])
        if task is None:
            return None
        status_data = data.model_dump(exclude_unset=True)
        status_data["process_status"] = status_data.pop("status")
        updated = await self.update(id=id, data=status_data)
        await VideoTaskBatchCRUD.sync_batch_summary_for_db(self.auth.db, task.batch_id)
        return updated

    async def delete_tasks_crud(self, ids: list[int]) -> None:
        """删除当前用户的任务记录。"""
        statement = delete(VideoTaskModel).where(
            VideoTaskModel.id.in_(ids),
            VideoTaskModel.created_id == self.auth.user.id,
        )
        await self.auth.db.execute(statement)
        await self.auth.db.flush()

    @staticmethod
    async def claim_queued_task_for_worker_crud(db: AsyncSession) -> VideoTaskModel | None:
        """worker 领取最早的 queued 任务，并立即标记为 processing。"""
        active_task_counts = (
            select(
                VideoTaskModel.batch_id.label("batch_id"),
                func.count(VideoTaskModel.id).label("active_count"),
            )
            .where(VideoTaskModel.process_status == "processing")
            .group_by(VideoTaskModel.batch_id)
            .subquery()
        )
        statement = (
            select(VideoTaskModel)
            .join(VideoTaskBatchModel, VideoTaskBatchModel.id == VideoTaskModel.batch_id)
            .outerjoin(
                active_task_counts,
                active_task_counts.c.batch_id == VideoTaskModel.batch_id,
            )
            .where(VideoTaskModel.process_status == "queued")
            .where(
                func.coalesce(active_task_counts.c.active_count, 0)
                < settings.VIDEO_BATCH_CONCURRENCY
            )
            .order_by(VideoTaskModel.id.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
            .options(selectinload(VideoTaskModel.assets))
        )
        result = await db.execute(statement)
        task = result.scalars().first()
        if task is None:
            return None

        task.process_status = "processing"
        task.progress = 1
        task.current_stage = "media_analysis"
        task.error_message = None
        # 任务真正被 worker 领取时，记录本次尝试的开始时间。
        task.config = {
            **dict(task.config or {}),
            "attempt_started_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        await db.flush()
        await db.refresh(task, attribute_names=["assets"])
        await VideoTaskBatchCRUD.sync_batch_summary_for_db(db, task.batch_id)
        return task

    @staticmethod
    async def requeue_stale_processing_tasks_for_worker_crud(
        db: AsyncSession,
        *,
        stale_seconds: int,
        exclude_ids: Sequence[int],
    ) -> list[int]:
        """把被后端重启打断的 processing 任务重新放回队列。

        渲染轮询跑在进程内的 asyncio Task 里，重启就没了，DB 会永远停在 processing；
        而领取只认 queued、重试接口只认 failed/cancelled，不回收就只能改库。
        判据用 `updated_time`：正常跑的任务每轮轮询都写进度，只有真没人写了才会变旧。
        断点（`resume_stage`）原样保留，重新领取后从断点续跑。
        """
        deadline = datetime.now() - timedelta(seconds=stale_seconds)
        statement = (
            select(VideoTaskModel)
            .where(VideoTaskModel.process_status == "processing")
            .where(VideoTaskModel.updated_time < deadline)
            .order_by(VideoTaskModel.id.asc())
        )
        if exclude_ids:
            statement = statement.where(VideoTaskModel.id.not_in(exclude_ids))
        tasks = list((await db.execute(statement)).scalars().all())
        if not tasks:
            return []

        for task in tasks:
            task.process_status = "queued"
            task.progress = 0
            task.current_stage = "queued"
            task.error_message = None
        await db.flush()
        for batch_id in {task.batch_id for task in tasks}:
            await VideoTaskBatchCRUD.sync_batch_summary_for_db(db, batch_id)
        return [task.id for task in tasks]

    @staticmethod
    async def get_task_for_worker_crud(db: AsyncSession, task_id: int) -> VideoTaskModel | None:
        """worker 按 ID 读取任务和素材，不套用户权限过滤。"""
        statement = (
            select(VideoTaskModel)
            .where(VideoTaskModel.id == task_id)
            .options(selectinload(VideoTaskModel.assets))
        )
        result = await db.execute(statement)
        return result.scalars().first()

    @staticmethod
    async def update_task_status_for_worker_crud(
        db: AsyncSession,
        task_id: int,
        status: str,
        progress: int | None = None,
        current_stage: str | None = None,
        error_message: str | None = None,
    ) -> VideoTaskModel | None:
        """worker 更新任务进度和阶段。"""
        task = await VideoTaskCRUD.get_task_for_worker_crud(db, task_id)
        if task is None:
            return None
        task.process_status = status
        if progress is not None:
            task.progress = progress
        if current_stage is not None:
            task.current_stage = current_stage
        task.error_message = error_message
        await db.flush()
        await db.refresh(task, attribute_names=["assets"])
        await VideoTaskBatchCRUD.sync_batch_summary_for_db(db, task.batch_id)
        return task

    @staticmethod
    async def get_latest_asset_metadata_crud(
        db: AsyncSession, task_id: int, asset_role: str
    ) -> dict[str, Any] | None:
        """取某角色最新一条已完成素材的 file_metadata，用于调试信息拼装。

        只选 file_metadata 单列，不走 ORM —— 详情页那条路径刻意不下发它（体积大），
        这里按需取一份小的（封面）或按需取大的（review）都由调用方决定。
        """
        row = (
            await db.execute(
                select(VideoAssetModel.file_metadata)
                .where(
                    VideoAssetModel.task_id == task_id,
                    VideoAssetModel.asset_role == asset_role,
                    VideoAssetModel.upload_status == VideoUploadStatusEnum.COMPLETED.value,
                )
                .order_by(VideoAssetModel.id.desc())
                .limit(1)
            )
        ).first()
        return _load_json_object(row[0]) if row is not None else None

    @staticmethod
    async def get_task_checkpoint_for_worker_crud(
        db: AsyncSession, task_id: int
    ) -> dict[str, Any] | None:
        """按任务读阶段断点，没有则返回 None。"""
        payload = await db.scalar(
            select(VideoTaskCheckpointModel.checkpoint).where(
                VideoTaskCheckpointModel.task_id == task_id
            )
        )
        return payload if isinstance(payload, dict) else None

    @staticmethod
    async def delete_task_checkpoint_crud(db: AsyncSession, task_id: int) -> None:
        """删掉任务的阶段断点，下次处理从首阶段重跑。"""
        await db.execute(
            delete(VideoTaskCheckpointModel).where(
                VideoTaskCheckpointModel.task_id == task_id
            )
        )

    @staticmethod
    async def update_task_checkpoint_for_worker_crud(
        db: AsyncSession,
        task_id: int,
        checkpoint: dict[str, Any],
    ) -> VideoTaskModel | None:
        """持久化 worker 阶段断点，不覆盖任务其他配置。"""
        task = await VideoTaskCRUD.get_task_for_worker_crud(db, task_id)
        if task is None:
            return None
        # 延迟导入：checkpoint 模块反过来依赖本模块，顶层导入会成环。
        from .pipeline.checkpoint import ProcessingCheckpointMixin

        # 断点独占一张表；先查后写，不依赖 MySQL 专有的 ON DUPLICATE KEY，
        # 免得换 postgres/sqlite 时静默失效。
        row = (
            (
                await db.execute(
                    select(VideoTaskCheckpointModel).where(
                        VideoTaskCheckpointModel.task_id == task_id
                    )
                )
            )
            .scalars()
            .first()
        )
        # 传副本而不是原对象：同一 session 里再存一次时，SQLAlchemy 靠对象身份
        # 判断有没有变，传原对象会被当成「没改」而漏掉 UPDATE。
        if row is None:
            db.add(
                VideoTaskCheckpointModel(task_id=task_id, checkpoint=dict(checkpoint))
            )
        else:
            row.checkpoint = dict(checkpoint)

        task.config = {
            **dict(task.config or {}),
            # 阶段耗时镜像到配置顶层，列表和详情不用展开断点就能展示。
            "stage_timings": checkpoint.get("stage_timings") or [],
            "stage_progress": ProcessingCheckpointMixin.build_stage_progress(checkpoint),
        }
        await db.flush()
        return task


class VideoAssetCRUD(CRUDBase[VideoAssetModel, VideoAssetCreateSchema, VideoAssetUpdateSchema]):
    """视频素材与产物数据层。"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=VideoAssetModel, auth=auth)

    async def create_asset_crud(self, data: VideoAssetCreateSchema) -> VideoAssetModel:
        """创建素材或产物记录。"""
        return await self.create(data=data)

    async def get_asset_by_id_crud(
        self, id: int, preload: list[str | Any] | None = None
    ) -> VideoAssetModel | None:
        """按ID查询当前用户的素材。"""
        return await self.get(id=id, created_id=self.auth.user.id, preload=preload)

    async def get_asset_by_upload_id_crud(
        self, upload_id: str, preload: list[str | Any] | None = None
    ) -> VideoAssetModel | None:
        """按Multipart上传ID查询当前用户的素材。"""
        return await self.get(
            upload_id=upload_id,
            created_id=self.auth.user.id,
            preload=preload,
        )

    async def list_task_assets_crud(
        self,
        task_id: int,
        asset_role: str | None = None,
        preload: list[str | Any] | None = None,
    ) -> Sequence[VideoAssetModel]:
        """查询当前用户指定任务下的素材与产物。"""
        search: dict[str, Any] = {
            "task_id": task_id,
            "created_id": self.auth.user.id,
        }
        if asset_role is not None:
            search["asset_role"] = asset_role
        return await self.list(
            search=search,
            order_by=[{"id": "asc"}],
            preload=preload,
        )

    async def update_asset_crud(
        self, id: int, data: VideoAssetUpdateSchema
    ) -> VideoAssetModel | None:
        """更新当前用户素材的上传结果和媒体元数据。"""
        asset = await self.get_asset_by_id_crud(id=id, preload=[])
        if asset is None:
            return None
        return await self.update(id=id, data=data)

    @staticmethod
    async def create_asset_for_worker_crud(
        db: AsyncSession,
        task: VideoTaskModel,
        data: VideoAssetCreateSchema,
    ) -> VideoAssetModel:
        """worker 创建成片或字幕资产，并继承任务创建人用于页面权限过滤。"""
        asset = VideoAssetModel(**data.model_dump())
        asset.created_id = task.created_id
        asset.updated_id = task.created_id
        db.add(asset)
        await db.flush()
        await db.refresh(asset)
        return asset

    @staticmethod
    async def update_asset_metadata_for_worker_crud(
        db: AsyncSession,
        asset_id: int,
        metadata: dict[str, Any],
    ) -> VideoAssetModel | None:
        """worker 更新素材元数据，用于记录云端媒资信息。"""
        asset = await db.get(VideoAssetModel, asset_id)
        if asset is None:
            return None
        asset.file_metadata = metadata
        await db.flush()
        await db.refresh(asset)
        return asset
