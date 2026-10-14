from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Any


# 1. --- 执行裂变的输入请求 (Action A/B/C 的触发器) ---
class FissionCreateSchema(BaseModel):
    location: str = Field(
        ..., min_length=1, max_length=100, description="初始输入地点，如：桂林"
    )
    gender: str = Field(default="年轻女性", max_length=10, description="性别")
    age: int = Field(default=20, ge=1, le=120, description="年龄")

    model_config = ConfigDict(from_attributes=True)


# 2. --- 批次列表的查询参数 ---
class FissionQueryParam(BaseModel):
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, description="每页数量")
    input_location: Optional[str] = None
    selected_scene: Optional[str] = None
    selected_style: Optional[str] = None
    theme: Optional[str] = None
    status: Optional[str] = None
    batch_sn: Optional[str] = None
    gender: Optional[str] = None


# 3. --- 批次详情输出 (Action A & B 的结果) ---
class BatchOutSchema(BaseModel):
    id: int
    uuid: str
    batch_sn: str
    input_location: str
    gender: str
    age: int
    theme: Optional[str] = None
    selected_scene: Optional[str] = None
    selected_style: Optional[str] = None
    task_count: int
    created_time: datetime

    model_config = ConfigDict(from_attributes=True)


# 4. --- 任务明细输出 (Action C & 结果展示) ---
class TaskOutSchema(BaseModel):
    id: int
    uuid: str
    task_sn: str
    batch_id: int
    view_type: Optional[str] = None
    action_desc: Optional[str] = None
    swapped_url: Optional[str] = None
    positive_prompt: str
    current_version: int
    version_history: Optional[list] = None
    bg_version_history: Optional[list] = None
    current_bg_version: int
    current_bg_url: Optional[str] = None
    process_status: int = Field(description="0:待抢单 1:生成中 2:成功 3:失败")
    image_url: Optional[str] = None
    agent_id: Optional[str] = None
    created_time: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# 5. --- 更新模型 (符合 CRUDBase 要求) ---
class BatchUpdateSchema(BaseModel):
    selected_scene: Optional[str] = None
    selected_style: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TaskUpdateSchema(BaseModel):
    process_status: Optional[int] = None
    image_url: Optional[str] = None
    agent_id: Optional[str] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClaimTaskSchema(BaseModel):
    """Agent 抢单请求体"""

    agent_id: str = Field(..., description="抢单节点的唯一标识，如：comfy-worker-01")


class TaskCallbackSchema(BaseModel):
    """Agent 生图结果回传请求体"""

    task_id: int = Field(..., description="任务的主键ID")
    process_status: int = Field(..., description="状态码：2=成功，3=失败")
    image_url: str | None = Field(default=None, description="生成的图片OSS链接")
    seed: int | None = Field(default=None, description="随机数种子")
    error_msg: str | None = Field(default=None, description="失败时的错误信息")


class UpscaleCreateSchema(BaseModel):
    """
    一键高清 (图像超分) 请求参数模型
    """

    task_id: int = Field(..., description="需要进行高清放大的子任务 (Task) ID")

    target_url: str = Field(..., description="需要放大的图片 URL")

    # --- 以下为高阶控制参数，设置了最稳妥的默认值，前端可以不传 ---

    model_quality: Literal["HQ", "MQ", "LQ"] = Field(
        default="MQ",
        description="模型质量偏好：LQ(低质原图适用), MQ(中等质量适用，最均衡), HQ(高质原图适用)。推荐 MQ",
    )

    result_format: Literal[0, 1] = Field(
        default=0,
        description="输出图片格式：0 代表 PNG (无损，适合超分后保留细节)，1 代表 JPEG",
    )

    jpg_quality: int = Field(
        default=95,
        ge=1,
        le=100,
        description="JPEG 压缩质量 (1-100)，值越高越清晰。仅在 result_format=1 时生效",
    )


class InferBackgroundSchema(BaseModel):
    image_url: str = Field(None, description="用户上传的参考背景图直链")
    location: str = Field(None, description="大地点")


class RegenerateTaskSchema(BaseModel):
    task_id: int = Field(..., description="需要进化的原子任务 ID")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="用户微调的参数字典 (对应 params_snapshot)"
    )
    is_new_version: bool = Field(default=True, description="是否生成全新的版本 (v2/v3)")


class FaceSwapSchema(BaseModel):
    task_id: int = Field(..., description="要作为底图的原子任务 ID")
    target_face_url: str = Field(..., description="用户上传的真人面部图 URL")
    target_url: str = Field(..., description="用户上传的真人面部图 URL")


class BackgroundFusionSchema(BaseModel):
    task_id: int = Field(..., description="任务 ID")
    bg_image_url: str = Field(..., description="用户上传的背景参考图 URL")
    custom_prompt: str | None = Field(
        default=None, description="用户自定义的提示语，如：在背景中，在背景中，在背景中"
    )
    model: str | None = Field(
        default=None,
        description="背景融合使用的模型，如：volcengine_seedream_direct_fusion",
    )


class FissionManualCreateSchema(BaseModel):
    """手动创建批次的入参校验"""

    input_location: str = Field(..., description="大地点", example="阳朔西街")
    gender: str = Field("年轻女性", description="人群性别")
    age: int = Field(20, description="年龄")
    theme: str = Field(..., description="策划主题")
    selected_scene: str = Field(..., description="具体场景")
    selected_style: str = Field(..., description="具体风格")
    image_urls: List[str] = Field(..., min_items=1, description="MinIO 图片 URL 列表")

    class Config:
        json_schema_extra = {
            "example": {
                "input_location": "桂林",
                "gender": "年轻女性",
                "age": 25,
                "theme": "古风旅拍",
                "selected_scene": "遇龙河畔",
                "selected_style": "唯美清新",
                "image_urls": [
                    "http://minio/bucket/1.jpg",
                    "http://minio/bucket/2.jpg",
                ],
            }
        }


class BrainstormExpertRequest(BaseModel):
    location: str = Field(..., description="大地点，如：桂林阳朔")
    gender: str = Field(..., description="目标性别，如：女孩")
    age: int = Field(..., description="年龄")
    extra_command: Optional[str] = Field("", description="附加的导演指令或背景反推特征")
    theme: Optional[Dict[str, Any]] = Field(None, description="用户选定的风格主题字典")


class ExpertTaskItem(BaseModel):
    view_type: str
    action_desc: str
    positive_prompt: str


class SubmitExpertBatchRequest(BaseModel):
    location: str
    gender: str
    age: int
    theme: Optional[str] = ""
    selected_scene: str = ""  # 👈 新增：接住前端传来的场景
    selected_style: str = ""  # 👈 新增：接住前端传来的风格
    tasks: List[ExpertTaskItem]
