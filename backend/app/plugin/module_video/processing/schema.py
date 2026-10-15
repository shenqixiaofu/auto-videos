from datetime import datetime
from typing import Any, Literal

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from app.common.enums import QueueEnum
from app.core.validator import DateTimeStr

from .render_contract import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_STYLE_PRESET,
    VideoAspectRatio,
    VideoStylePreset,
)

VideoTaskStatus = Literal[
    "draft",
    "uploading",
    "queued",
    "processing",
    "reviewing",
    "succeeded",
    "failed",
    "cancelled",
]
VideoTaskStage = Literal[
    "draft",
    "uploading",
    "queued",
    "media_analysis",
    "transcription",
    "editing",
    "rendering",
    "quality_check",
    "reviewing",
    "completed",
]
VideoAssetRole = Literal["source", "cover", "ending", "music", "review", "output", "subtitle"]
VideoInputAssetRole = Literal["source", "ending"]
VideoUploadStatus = Literal["pending", "uploading", "completed", "failed"]
# 封面生图通道：relay=OpenAI 协议中转站，seedream=火山方舟。
VideoCoverImageProvider = Literal["relay", "seedream"]

# 与 pipeline/checkpoint.py 的 _TIME_FORMAT 一致。那边不能反向 import 本模块
# （checkpoint → crud → schema），格式串只能各留一份。
_STAGE_STARTED_AT_FORMATS = ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S")


def _parse_stage_started_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    for fmt in _STAGE_STARTED_AT_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class VideoTaskConfigSchema(BaseModel):
    """自动剪辑配置。"""

    aspect_ratio: VideoAspectRatio = Field(
        default=DEFAULT_ASPECT_RATIO, description="成片画面比例"
    )
    style_preset: VideoStylePreset = Field(
        default=DEFAULT_STYLE_PRESET, description="剪辑风格预设"
    )
    # 建任务时选定的封面生图通道；None 是老任务，实际取值回退到服务端 env 配置。
    cover_image_provider: VideoCoverImageProvider | None = Field(
        default=None, description="封面生图通道"
    )
    subtitle_enabled: bool = Field(default=True, description="是否自动生成字幕")
    attempt_started_time: DateTimeStr | None = Field(
        default=None,
        description="本次尝试开始时间",
    )
    # 一次渲染实际用到的变量摘要，随列表响应下发，省掉为看调试信息再拉详情。
    debug_summary: dict[str, Any] | None = Field(
        default=None, description="渲染调试摘要"
    )
    # 各处理阶段耗时明细，按执行顺序排列。
    stage_timings: list[dict[str, Any]] | None = Field(
        default=None, description="各处理阶段耗时"
    )
    # 当前正在跑的阶段。阶段耗时只在结束后才记录，中途靠这个让用户看到
    # 「跑到哪、已经跑了多久」，不用反复刷新。
    stage_progress: dict[str, Any] | None = Field(
        default=None, description="当前处理阶段与实时耗时"
    )

    @model_validator(mode="after")
    def _fill_stage_elapsed(self) -> Self:
        """按请求时刻现算进行中阶段的已耗时。

        落库时算的数值到用户打开页面时早就过期了，所以只存起点，读的时候
        再减 —— 列表和详情每刷一次都是准的。
        """
        progress = self.stage_progress
        if not isinstance(progress, dict) or progress.get("elapsed_seconds") is not None:
            return self
        started_at = _parse_stage_started_at(progress.get("started_at"))
        if started_at is None:
            return self
        self.stage_progress = {
            **progress,
            "elapsed_seconds": round(
                max((datetime.now() - started_at).total_seconds(), 0.0), 1
            ),
        }
        return self


class VideoTaskCreateSchema(BaseModel):
    """创建自动剪辑任务请求。"""

    title: str = Field(..., min_length=1, max_length=128, description="任务标题")
    aspect_ratio: VideoAspectRatio = Field(
        default=DEFAULT_ASPECT_RATIO, description="成片画面比例"
    )
    style_preset: VideoStylePreset = Field(
        default=DEFAULT_STYLE_PRESET, description="剪辑风格预设"
    )
    cover_image_provider: VideoCoverImageProvider | None = Field(
        default=None, description="封面生图通道，不传则跟随服务端默认"
    )
    batch_id: int | None = Field(default=None, description="所属批次ID")
    batch_index: int = Field(default=1, ge=1, description="批次内顺序")


class VideoTaskBatchCreateSchema(BaseModel):
    """创建自动剪辑批次请求。"""

    batch_name: str = Field(..., min_length=1, max_length=128, description="批次名称")
    batch_type: Literal["single", "folder"] = Field(
        default="folder", description="批次类型"
    )
    expected_count: int = Field(..., ge=1, description="预计子任务数量")


class VideoTaskUpdateSchema(BaseModel):
    """更新任务基础信息请求。"""

    title: str | None = Field(default=None, min_length=1, max_length=128, description="任务标题")
    config: VideoTaskConfigSchema | None = Field(default=None, description="自动剪辑配置")


class VideoTaskStatusSchema(BaseModel):
    """更新任务执行状态请求。"""

    status: VideoTaskStatus = Field(..., description="任务状态")
    progress: int | None = Field(default=None, ge=0, le=100, description="处理进度百分比")
    current_stage: VideoTaskStage | None = Field(default=None, description="当前处理阶段")
    error_message: str | None = Field(default=None, description="任务失败信息")


class VideoTaskActionSchema(BaseModel):
    """用户可执行的任务状态操作。"""

    action: Literal["submit", "cancel", "retry"] = Field(..., description="任务操作")


class VideoTaskReviewSchema(BaseModel):
    """审核待确认成片的操作请求。"""

    action: Literal["approve", "regenerate"] = Field(..., description="审核动作")
    adjustment_prompt: str | None = Field(
        default=None,
        max_length=1000,
        description="重新生成时的调整说明",
    )


class VideoProcessingConfigOutSchema(BaseModel):
    """自动剪辑全局配置（管理员高级设置）。"""

    cover_image_provider: VideoCoverImageProvider = Field(..., description="封面生图通道")
    relay_image_model: str = Field(..., description="中转站生图模型")
    relay_image_size: str = Field(..., description="中转站生图尺寸")
    cover_summary_model: str = Field(..., description="封面策划模型")
    creative_planner_model: str = Field(..., description="创意规划模型")
    # 空 = 用代码内置模板。改坏了可以直接清空回到内置版本。
    cover_prompt_template: str | None = Field(default=None, description="封面提示词模板，空=内置默认")
    planner_prompt_template: str | None = Field(default=None, description="创意规划提示词模板，空=内置默认")
    cover_plan_prompt_template: str | None = Field(
        default=None, description="封面策划 system 提示词模板，空=内置默认"
    )
    cover_plan_user_prompt_template: str | None = Field(
        default=None, description="封面策划 user 提示词模板，空=内置默认"
    )
    cover_style_samples: str | None = Field(
        default=None, description="封面标题风格样本（一行一条），空=内置默认"
    )
    cover_title_max_chars: int = Field(..., description="封面主标题字数上限")
    cover_subtitle_max_chars: int = Field(..., description="封面副标题字数上限")
    cover_badge_max_chars: int = Field(..., description="封面标签字数上限")
    cover_highlight_count: int = Field(..., description="封面高亮词个数上限")
    subtitle_font: str = Field(..., description="底部字幕字体")
    subtitle_font_size: int = Field(..., description="底部字幕字号")
    subtitle_outline_width: int = Field(..., description="底部字幕描边宽度")
    subtitle_bold: bool = Field(..., description="底部字幕是否加粗")
    # 只读：内置默认原文，前端拿它当编辑起点，并据此判断「是否已自定义」。
    cover_prompt_template_default: str = Field(..., description="封面提示词模板的内置默认原文")
    planner_prompt_template_default: str = Field(..., description="创意规划提示词模板的内置默认原文")
    cover_plan_prompt_template_default: str = Field(..., description="封面策划 system 模板的内置默认原文")
    cover_plan_user_prompt_template_default: str = Field(..., description="封面策划 user 模板的内置默认原文")
    cover_style_samples_default: str = Field(..., description="封面标题风格样本的内置默认原文")
    cover_title_max_chars_default: int = Field(..., description="封面主标题字数上限的内置默认值")
    cover_subtitle_max_chars_default: int = Field(..., description="封面副标题字数上限的内置默认值")
    cover_badge_max_chars_default: int = Field(..., description="封面标签字数上限的内置默认值")
    cover_highlight_count_default: int = Field(..., description="封面高亮词个数上限的内置默认值")
    subtitle_font_default: str = Field(..., description="底部字幕字体的内置默认值")
    subtitle_font_size_default: int = Field(..., description="底部字幕字号的内置默认值")
    subtitle_outline_width_default: int = Field(..., description="底部字幕描边宽度的内置默认值")
    subtitle_bold_default: bool = Field(..., description="底部字幕加粗的内置默认值")
    subtitle_font_options: list[str] = Field(..., description="可选内置字体清单（写错阿里静默回落）")
    version: int = Field(..., description="配置版本号")
    updated_time: DateTimeStr | None = Field(default=None, description="最后更新时间")
    updated_by: str | None = Field(default=None, description="最后更新人")


class VideoProcessingConfigUpdateSchema(BaseModel):
    """更新全局配置。只提交要改的字段，传 null 表示恢复默认。"""

    cover_image_provider: VideoCoverImageProvider | None = Field(
        default=None, description="封面生图通道"
    )
    relay_image_model: str | None = Field(default=None, max_length=128, description="中转站生图模型")
    relay_image_size: str | None = Field(default=None, max_length=32, description="中转站生图尺寸")
    cover_summary_model: str | None = Field(default=None, max_length=128, description="封面策划模型")
    creative_planner_model: str | None = Field(
        default=None, max_length=128, description="创意规划模型"
    )
    cover_prompt_template: str | None = Field(default=None, description="封面提示词模板")
    planner_prompt_template: str | None = Field(default=None, description="创意规划提示词模板")
    cover_plan_prompt_template: str | None = Field(
        default=None, description="封面策划 system 提示词模板"
    )
    cover_plan_user_prompt_template: str | None = Field(
        default=None, description="封面策划 user 提示词模板"
    )
    cover_style_samples: str | None = Field(default=None, description="封面标题风格样本")
    # 上限给宽一点但不放开：这些值会直接写进提示词，写太大等于让模型排一屏字。
    cover_title_max_chars: int | None = Field(
        default=None, ge=1, le=40, description="封面主标题字数上限"
    )
    cover_subtitle_max_chars: int | None = Field(
        default=None, ge=1, le=40, description="封面副标题字数上限"
    )
    cover_badge_max_chars: int | None = Field(
        default=None, ge=1, le=12, description="封面标签字数上限"
    )
    cover_highlight_count: int | None = Field(
        default=None, ge=1, le=6, description="封面高亮词个数上限"
    )
    subtitle_font: str | None = Field(default=None, max_length=64, description="底部字幕字体")
    # 字号上限 60 是几何硬约束：超过就会压到贴纸装饰带上，见 processing_config。
    subtitle_font_size: int | None = Field(
        default=None, ge=24, le=60, description="底部字幕字号"
    )
    subtitle_outline_width: int | None = Field(
        default=None, ge=0, le=6, description="底部字幕描边宽度"
    )
    subtitle_bold: bool | None = Field(default=None, description="底部字幕是否加粗")

    @model_validator(mode="after")
    def _blank_to_default(self) -> Self:
        """空白串一律当成 null（= 恢复默认），免得存一堆空字符串进去。"""
        for field in self.model_fields:
            value = getattr(self, field)
            if isinstance(value, str) and not value.strip():
                setattr(self, field, None)
            elif isinstance(value, str):
                setattr(self, field, value.strip())
        return self


class VideoCoverImageModelOutSchema(BaseModel):
    """中转站当前支持生图的模型，供高级设置里的下拉选择。"""

    name: str = Field(..., description="模型名")
    endpoint_types: list[str] = Field(default_factory=list, description="支持的端点类型")


class VideoAssetUploadInitSchema(BaseModel):
    """初始化素材 Multipart 上传请求。"""

    file_name: str = Field(..., min_length=1, max_length=255, description="原始文件名")
    file_size: int = Field(..., gt=0, description="文件大小（字节）")
    content_type: str = Field(..., min_length=1, max_length=128, description="文件媒体类型")
    asset_role: VideoInputAssetRole = Field(..., description="输入素材角色")


class VideoAssetCreateSchema(BaseModel):
    """素材上传初始化后的入库模型。"""

    task_id: int = Field(..., description="所属任务ID")
    asset_role: VideoAssetRole = Field(..., description="素材角色")
    file_name: str = Field(..., min_length=1, max_length=255, description="原始文件名")
    file_size: int = Field(..., gt=0, description="文件大小（字节）")
    content_type: str = Field(..., min_length=1, max_length=128, description="文件媒体类型")
    file_metadata: dict[str, Any] = Field(default_factory=dict, description="文件媒体元数据")
    bucket: str = Field(..., min_length=1, max_length=128, description="MinIO存储桶")
    object_key: str = Field(..., min_length=1, max_length=512, description="MinIO对象键")
    upload_id: str | None = Field(default=None, max_length=255, description="Multipart上传ID")
    upload_status: VideoUploadStatus = Field(default="uploading", description="上传状态")
    etag: str | None = Field(default=None, max_length=128, description="对象ETag")


class VideoAssetUpdateSchema(BaseModel):
    """更新素材上传结果与媒体元数据。"""

    upload_id: str | None = Field(default=None, max_length=255, description="Multipart上传ID")
    upload_status: VideoUploadStatus | None = Field(default=None, description="上传状态")
    etag: str | None = Field(default=None, max_length=128, description="对象ETag")
    file_metadata: dict[str, Any] | None = Field(default=None, description="文件媒体元数据")


class VideoMultipartUploadPartSchema(BaseModel):
    """待上传分片及其预签名地址。"""

    part_number: int = Field(..., ge=1, description="分片序号")
    upload_url: str = Field(..., description="分片预签名上传地址")


class VideoAssetUploadInitOutSchema(BaseModel):
    """初始化素材 Multipart 上传响应。"""

    asset_id: int = Field(..., description="素材ID")
    upload_id: str = Field(..., description="Multipart上传ID")
    bucket: str = Field(..., description="MinIO存储桶")
    object_key: str = Field(..., description="MinIO对象键")
    part_size: int = Field(..., gt=0, description="分片大小（字节）")
    parts: list[VideoMultipartUploadPartSchema] = Field(
        default_factory=list, description="待上传分片列表"
    )


class VideoAssetDownloadOutSchema(BaseModel):
    """成片或字幕的短时访问地址。"""

    url: str = Field(..., description="短时预签名访问地址")
    expires_in: int = Field(..., gt=0, description="地址有效期（秒）")


class VideoMultipartPartSchema(BaseModel):
    """已上传 Multipart 分片。"""

    part_number: int = Field(..., ge=1, description="分片序号")
    etag: str = Field(..., min_length=1, max_length=128, description="分片ETag")


class VideoMultipartCompleteSchema(BaseModel):
    """完成素材 Multipart 上传请求。"""

    upload_id: str = Field(..., min_length=1, max_length=255, description="Multipart上传ID")
    parts: list[VideoMultipartPartSchema] = Field(..., min_length=1, description="已上传分片列表")


class VideoMultipartPresignSchema(BaseModel):
    """刷新指定 Multipart 分片签名请求。"""

    upload_id: str = Field(..., min_length=1, max_length=255, description="Multipart上传ID")
    part_numbers: list[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="需要刷新签名的分片序号",
    )


class VideoAssetOutSchema(BaseModel):
    """视频素材或产物响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="素材ID")
    task_id: int = Field(..., description="所属任务ID")
    asset_role: VideoAssetRole = Field(..., description="素材角色")
    file_name: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件媒体类型")
    file_metadata: dict[str, Any] = Field(default_factory=dict, description="文件媒体元数据")
    bucket: str = Field(..., description="MinIO存储桶")
    object_key: str = Field(..., description="MinIO对象键")
    upload_id: str | None = Field(default=None, description="Multipart上传ID")
    upload_status: VideoUploadStatus = Field(..., description="上传状态")
    etag: str | None = Field(default=None, description="对象ETag")
    created_time: DateTimeStr = Field(..., description="创建时间")
    updated_time: DateTimeStr = Field(..., description="更新时间")


class VideoAssetMetadataOutSchema(BaseModel):
    """单个素材的完整媒体元数据响应。

    详情接口不再下发 file_metadata（完整时间线 JSON 动辄 200KB），
    前端展开「完整渲染元数据」折叠区时再按素材单独取。
    """

    model_config = ConfigDict(from_attributes=True)

    asset_id: int = Field(..., description="素材ID")
    asset_role: VideoAssetRole = Field(..., description="素材角色")
    file_metadata: dict[str, Any] = Field(default_factory=dict, description="文件媒体元数据")


class VideoTaskListOutSchema(BaseModel):
    """自动剪辑任务列表响应。"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(..., description="任务ID")
    task_no: str = Field(..., description="任务编号")
    title: str = Field(..., description="任务标题")
    batch_id: int = Field(..., description="所属批次ID")
    batch_index: int = Field(..., description="批次内顺序")
    status: VideoTaskStatus = Field(..., validation_alias="process_status", description="任务状态")
    progress: int = Field(..., ge=0, le=100, description="处理进度百分比")
    current_stage: VideoTaskStage = Field(..., description="当前处理阶段")
    config: VideoTaskConfigSchema = Field(..., description="自动剪辑配置")
    error_message: str | None = Field(default=None, description="任务失败信息")
    cover_preview_url: str | None = Field(default=None, description="封面预览地址")
    created_time: DateTimeStr = Field(..., description="创建时间")
    updated_time: DateTimeStr = Field(..., description="更新时间")
    finished_time: DateTimeStr | None = Field(default=None, description="处理结束时间")


class VideoTaskDetailOutSchema(VideoTaskListOutSchema):
    """自动剪辑任务详情响应。"""

    assets: list[VideoAssetOutSchema] = Field(default_factory=list, description="任务素材与产物")


class VideoTaskBatchListOutSchema(BaseModel):
    """自动剪辑批次列表响应。"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(..., description="批次ID")
    batch_no: str = Field(..., description="批次编号")
    batch_name: str = Field(..., description="批次名称")
    batch_type: Literal["single", "folder"] = Field(..., description="批次类型")
    expected_count: int = Field(..., ge=1, description="预计子任务数量")
    task_count: int = Field(..., ge=0, description="已创建子任务数量")
    completed_count: int = Field(..., ge=0, description="已完成子任务数量")
    status: VideoTaskStatus = Field(..., validation_alias="process_status", description="批次状态")
    progress: int = Field(..., ge=0, le=100, description="批次处理进度百分比")
    current_stage: VideoTaskStage = Field(..., description="当前处理阶段")
    error_message: str | None = Field(default=None, description="批次失败信息")
    cover_preview_url: str | None = Field(default=None, description="批次封面预览地址")
    created_time: DateTimeStr = Field(..., description="创建时间")
    updated_time: DateTimeStr = Field(..., description="更新时间")
    finished_time: DateTimeStr | None = Field(default=None, description="处理结束时间")
    # 列表只带任务摘要：详情级的 assets/file_metadata 含完整时间线 JSON，
    # 全量塞进列表会让批次分页响应膨胀到几 MB。
    tasks: list[VideoTaskListOutSchema] = Field(default_factory=list, description="批次子任务")


class VideoTaskBatchDetailOutSchema(VideoTaskBatchListOutSchema):
    """自动剪辑批次详情响应，携带子任务的素材与产物。"""

    tasks: list[VideoTaskDetailOutSchema] = Field(default_factory=list, description="批次子任务")


class VideoTaskDebugOutSchema(BaseModel):
    """任务调试信息：本次实际用到的提示词与生图参考帧。

    提示词可在高级设置里改，任务上必须留一份成品串的快照，否则事后没法回答
    「这一条任务当时到底发了什么」。老任务没有这些字段，一律为 null。
    """

    planner_model: str | None = Field(default=None, description="创意规划实际使用的模型")
    planner_system_prompt: str | None = Field(default=None, description="创意规划 system 提示词全文")
    planner_user_prompt: str | None = Field(default=None, description="创意规划 user 提示词全文")
    cover_image_provider: str | None = Field(default=None, description="封面生图实际通道")
    cover_image_model: str | None = Field(default=None, description="封面生图实际模型")
    cover_image_size: str | None = Field(default=None, description="封面生图实际尺寸")
    cover_summary_model: str | None = Field(default=None, description="封面策划实际模型")
    cover_image_prompt: str | None = Field(default=None, description="封面生图提示词全文")
    cover_prompt: str | None = Field(default=None, description="封面策划给的排版氛围说明")
    cover_reference_url: str | None = Field(default=None, description="生图参考帧的短时访问地址")
    cover_reference_name: str | None = Field(default=None, description="生图参考帧文件名")


class VideoTaskQueryParam:
    """自动剪辑任务查询参数。"""

    def __init__(
        self,
        task_no: str | None = Query(default=None, description="任务编号"),
        keyword: str | None = Query(default=None, description="任务标题关键词"),
        status: VideoTaskStatus | None = Query(default=None, description="任务状态"),
        current_stage: VideoTaskStage | None = Query(default=None, description="当前处理阶段"),
        created_time: list[DateTimeStr] | None = Query(
            default=None,
            description="创建时间范围",
            examples=["2026-01-01 00:00:00", "2026-12-31 23:59:59"],
        ),
    ) -> None:
        # 标题使用模糊查询，其余字段使用精确查询。
        self.task_no = (QueueEnum.eq.value, task_no)
        self.title = (QueueEnum.like.value, keyword)
        # API 查询名保持 status，数据库字段使用 process_status。
        self.process_status = (QueueEnum.eq.value, status)
        self.current_stage = (QueueEnum.eq.value, current_stage)
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))


class VideoTaskBatchQueryParam:
    """自动剪辑批次查询参数。"""

    def __init__(
        self,
        batch_no: str | None = Query(default=None, description="批次编号"),
        keyword: str | None = Query(default=None, description="批次名称关键词"),
        status: VideoTaskStatus | None = Query(default=None, description="批次状态"),
        batch_type: Literal["single", "folder"] | None = Query(
            default=None, description="批次类型"
        ),
        created_time: list[DateTimeStr] | None = Query(
            default=None,
            description="创建时间范围",
            examples=["2026-01-01 00:00:00", "2026-12-31 23:59:59"],
        ),
    ) -> None:
        self.batch_no = (QueueEnum.eq.value, batch_no)
        self.batch_name = (QueueEnum.like.value, keyword)
        self.process_status = (QueueEnum.eq.value, status)
        self.batch_type = (QueueEnum.eq.value, batch_type)
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))
