from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BIGINT, JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import PermissionFilterStrategy
from app.core.base_model import ModelMixin, UserMixin
from app.utils.common_util import uuid4_str


class VideoTaskStatusEnum(str, enum.Enum):
    """视频任务状态枚举。"""

    DRAFT = "draft"
    UPLOADING = "uploading"
    QUEUED = "queued"
    PROCESSING = "processing"
    REVIEWING = "reviewing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoAssetRoleEnum(str, enum.Enum):
    """视频素材角色枚举。"""

    SOURCE = "source"
    COVER = "cover"
    ENDING = "ending"
    MUSIC = "music"
    REVIEW = "review"
    OUTPUT = "output"
    SUBTITLE = "subtitle"


class VideoUploadStatusEnum(str, enum.Enum):
    """素材上传状态枚举。"""

    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoTaskBatchModel(ModelMixin, UserMixin):
    """自动剪辑任务批次表。"""

    __tablename__: str = "video_task_batch"
    __table_args__: dict[str, str] = {"comment": "自动剪辑任务批次表"}
    __loader_options__: list[str] = ["tasks", "created_by", "updated_by"]
    __permission_strategy__ = PermissionFilterStrategy.SELF_ONLY

    batch_no: Mapped[str] = mapped_column(
        String(64),
        default=uuid4_str,
        nullable=False,
        unique=True,
        index=True,
        comment="批次编号",
    )
    batch_name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="批次名称"
    )
    batch_type: Mapped[str] = mapped_column(
        String(16), default="single", nullable=False, index=True, comment="批次类型"
    )
    expected_count: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="预计子任务数量"
    )
    task_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="已创建子任务数量"
    )
    completed_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="已完成子任务数量"
    )
    process_status: Mapped[str] = mapped_column(
        String(16),
        default=VideoTaskStatusEnum.DRAFT.value,
        nullable=False,
        index=True,
        comment="批次状态",
    )
    progress: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="批次处理进度百分比"
    )
    current_stage: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True, comment="批次当前阶段"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="批次失败信息"
    )

    # 批次删除时同时清理子任务，任务产物由业务层随任务记录一并处理。
    # 故意不带 order_by：selectinload 会把子任务的 config（含断点，MB 级）一起
    # select 出来，一旦再排序，MySQL 就要把整行塞进 sort_buffer 报 1038。
    # 需要顺序的消费点（本类 cover_preview_url、crud.sync_batch_summary_for_db）
    # 都在 Python 里自己排。
    tasks: Mapped[list[VideoTaskModel]] = relationship(
        "VideoTaskModel",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def cover_preview_url(self) -> str | None:
        """返回批次中最早完成封面的预览地址。"""
        for task in sorted(self.tasks, key=lambda item: (item.batch_index, item.id)):
            cover_url = task.cover_preview_url
            if cover_url:
                return cover_url
        return None

    @property
    def finished_time(self) -> datetime | None:
        """返回批次结束时间，优先使用最后一个完成子任务的时间。"""
        finished_tasks = [
            task
            for task in self.tasks
            if task.process_status in {VideoTaskStatusEnum.SUCCEEDED.value, VideoTaskStatusEnum.FAILED.value, VideoTaskStatusEnum.CANCELLED.value}
        ]
        if finished_tasks:
            return max(finished_tasks, key=lambda task: task.updated_time).updated_time
        if self.process_status in {
            VideoTaskStatusEnum.FAILED.value,
            VideoTaskStatusEnum.CANCELLED.value,
            VideoTaskStatusEnum.SUCCEEDED.value,
        }:
            return self.updated_time
        return None


class VideoTaskModel(ModelMixin, UserMixin):
    """自动剪辑任务表。"""

    __tablename__: str = "video_task"
    __table_args__: dict[str, str] = {"comment": "自动剪辑任务表"}
    __loader_options__: list[str] = ["assets", "created_by", "updated_by"]
    __permission_strategy__ = PermissionFilterStrategy.SELF_ONLY

    batch_id: Mapped[int] = mapped_column(
        ForeignKey("video_task_batch.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属批次ID",
    )
    batch_index: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="批次内顺序"
    )
    task_no: Mapped[str] = mapped_column(
        String(64),
        default=uuid4_str,
        nullable=False,
        unique=True,
        index=True,
        comment="任务编号",
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False, comment="任务标题")
    process_status: Mapped[str] = mapped_column(
        String(16),
        default=VideoTaskStatusEnum.DRAFT.value,
        nullable=False,
        index=True,
        comment="业务任务状态",
    )
    progress: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="处理进度百分比"
    )
    current_stage: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True, comment="当前处理阶段"
    )
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False, comment="自动剪辑配置")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="任务失败信息")

    # 任务删除时同时清理数据库中的素材记录，MinIO 对象由业务层处理。
    assets: Mapped[list[VideoAssetModel]] = relationship(
        "VideoAssetModel",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    batch: Mapped[VideoTaskBatchModel] = relationship(
        "VideoTaskBatchModel",
        back_populates="tasks",
        lazy="selectin",
    )

    @property
    def finished_time(self) -> datetime | None:
        """返回任务处理结束时间，避免把人工审核通过时间误认为成片生成时间。"""
        current_review_version = int(self.config.get("review_version") or 1)
        review_assets = [
            asset
            for asset in self.assets
            if asset.asset_role == VideoAssetRoleEnum.REVIEW.value
            and asset.upload_status == VideoUploadStatusEnum.COMPLETED.value
            # 重新生成期间只看当前版本，避免展示上一版成片时间。
            and int(asset.file_metadata.get("review_version") or 0) == current_review_version
        ]
        if review_assets:
            return max(review_assets, key=lambda asset: asset.created_time).created_time
        if self.process_status in {
            VideoTaskStatusEnum.FAILED.value,
            VideoTaskStatusEnum.CANCELLED.value,
        }:
            return self.updated_time
        return None

    @property
    def cover_preview_url(self) -> str | None:
        """返回任务封面预览地址，供列表展开直接展示缩略图。"""
        cover_assets = [
            asset
            for asset in self.assets
            if asset.asset_role == VideoAssetRoleEnum.COVER.value
            and asset.upload_status == VideoUploadStatusEnum.COMPLETED.value
        ]
        if not cover_assets:
            return None
        latest_cover = max(cover_assets, key=lambda asset: asset.created_time)
        from .storage import VideoObjectStorage

        # 展示优先用 JPEG 缩略图，旧任务没有缩略图就回落原图 PNG。
        metadata = latest_cover.file_metadata or {}
        return VideoObjectStorage.presign_download(
            object_key=metadata.get("cover_thumbnail_key") or latest_cover.object_key,
            file_name=latest_cover.file_name,
            attachment=False,
        )


class VideoAssetModel(ModelMixin, UserMixin):
    """视频任务素材及产物表。"""

    __tablename__: str = "video_asset"
    __table_args__: dict[str, str] = {"comment": "视频任务素材及产物表"}
    __loader_options__: list[str] = ["created_by", "updated_by"]
    __permission_strategy__ = PermissionFilterStrategy.SELF_ONLY

    task_id: Mapped[int] = mapped_column(
        ForeignKey("video_task.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属任务ID",
    )
    asset_role: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="素材角色"
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    file_size: Mapped[int] = mapped_column(BIGINT, nullable=False, comment="文件大小（字节）")
    content_type: Mapped[str] = mapped_column(String(128), nullable=False, comment="文件媒体类型")
    file_metadata: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False, comment="文件媒体元数据"
    )
    bucket: Mapped[str] = mapped_column(String(128), nullable=False, comment="MinIO存储桶")
    object_key: Mapped[str] = mapped_column(
        String(512), nullable=False, index=True, comment="MinIO对象键"
    )
    upload_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True, comment="Multipart上传ID"
    )
    upload_status: Mapped[str] = mapped_column(
        String(16),
        default=VideoUploadStatusEnum.PENDING.value,
        nullable=False,
        index=True,
        comment="上传状态",
    )
    etag: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="已完成对象ETag")

    task: Mapped[VideoTaskModel] = relationship(
        "VideoTaskModel", back_populates="assets", lazy="selectin"
    )


class VideoProcessingConfigModel(ModelMixin):
    """自动剪辑全局配置表（单行）。

    全链路只读写 id=1 这一行。做成独立表而不是塞进 env 或 sys_param：env 改一次
    要重启进程；sys_param 的 config_value 是 String(500)，放不下上千字符的提示词。
    整份配置存 JSON，后续加字段不用再动表结构。

    不带 UserMixin：`updated_by` 关系会触发 selectin 级联，而这份配置是每次处理
    任务都要读的热路径。更新人只存 `updated_id`，要显示用户名时单独查一次。
    """

    __tablename__: str = "video_processing_config"
    __table_args__: dict[str, str] = {"comment": "自动剪辑全局配置表"}
    __loader_options__: list[str] = []
    __permission_strategy__ = PermissionFilterStrategy.DATA_SCOPE

    config: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False, comment="全局配置（模型、提示词、生图通道）"
    )
    updated_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="最后更新人ID",
    )


class VideoTaskCheckpointModel(ModelMixin):
    """自动剪辑任务处理断点表。

    断点含完整时间线与各阶段中间产物，单任务 80~160KB。原先塞在
    `video_task.config` 里，把 video_task 变成宽表 —— MySQL 的 filesort 会把
    整行塞进 sort_buffer，只要查询读了 config 又带 ORDER BY（且没 LIMIT），
    单行超过约 140KB 就报 `1038 Out of sort memory`。搬到独立表后
    video_task 单行回到 ~1KB，这类报错从结构上消失。

    故意不挂 relationship、不进 `__loader_options__`：断点只有 worker 链路
    需要，任何 selectinload 都不该顺带把它拉出来。
    """

    __tablename__: str = "video_task_checkpoint"
    __table_args__: dict[str, str] = {"comment": "自动剪辑任务处理断点表"}
    __loader_options__: list[str] = []
    __permission_strategy__ = PermissionFilterStrategy.SELF_ONLY

    task_id: Mapped[int] = mapped_column(
        ForeignKey("video_task.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="所属任务ID",
    )
    checkpoint: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False, comment="阶段断点"
    )
