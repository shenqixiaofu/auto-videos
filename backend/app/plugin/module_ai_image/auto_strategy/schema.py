# -*- coding: utf-8 -*-

from pydantic import BaseModel, ConfigDict, Field
from fastapi import Query
from datetime import datetime
from app.core.validator import DateTimeStr
from app.core.validator import DateTimeStr
from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema, UserBySchema


class AiImageAutoStrategyCreateSchema(BaseModel):
    """
    AI 24小时自动化生图策略新增模型
    """

    strategy_name: str = Field(
        default=..., description="策略名称(如：千家洞春季汉服巡检)"
    )
    location: str = Field(default=..., description="目标地点(如：千家洞)")
    gender: str = Field(default=..., description="目标性别(男/女/随机)")
    age_min: int = Field(default=..., description="年龄下限")
    theme_ids: list[int] | None = Field(
        default=[],  # 建议默认值给空列表，方便前端处理
        description="关联的主题样式ID列表，传整数数组，例如 [1, 2, 3]",
    )
    background_strategy: str | None = Field(
        default=None,
        max_length=1000,  # 与数据库 String(1000) 对应，防止超长报错
        description="背景描述策略(如：高级感背景肌理、特定的光影氛围)",
        examples=["清冷蓝调时刻，微泛金光的斑驳暗墙，丁达尔光柱中清晰跃动的细腻微尘"],
    )
    age_max: int = Field(default=..., description="年龄上限")
    daily_batch_limit: int = Field(default=..., description="每天最多生成几个Batch")
    priority: int = Field(default=..., description="执行优先级(数字越大越先执行)")
    status: str = Field(default="0", description="状态(0:启用 1:禁用)")


class AiImageAutoStrategyUpdateSchema(AiImageAutoStrategyCreateSchema):
    """
    AI 24小时自动化生图策略更新模型
    """

    ...


class AiImageAutoStrategyOutSchema(
    AiImageAutoStrategyCreateSchema, BaseSchema, UserBySchema
):
    """
    AI 24小时自动化生图策略响应模型
    """

    model_config = ConfigDict(from_attributes=True)


class AiImageAutoStrategyQueryParam:
    """AI 24小时自动化生图策略查询参数"""

    def __init__(
        self,
        strategy_name: str | None = Query(
            None, description="策略名称(如：千家洞春季汉服巡检)"
        ),
        location: str | None = Query(None, description="目标地点(如：千家洞)"),
        gender: str | None = Query(None, description="目标性别(男/女/随机)"),
        age_min: int | None = Query(None, description="年龄下限"),
        age_max: int | None = Query(None, description="年龄上限"),
        daily_batch_limit: int | None = Query(
            None, description="每天最多生成几个Batch"
        ),
        priority: int | None = Query(None, description="执行优先级(数字越大越先执行)"),
        status: str | None = Query(None, description="状态(0:启用 1:禁用)"),
        created_id: int | None = Query(None, description="创建人ID"),
        updated_id: int | None = Query(None, description="更新人ID"),
        created_time: list[DateTimeStr] | None = Query(
            None,
            description="创建时间范围",
            examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"],
        ),
        updated_time: list[DateTimeStr] | None = Query(
            None,
            description="更新时间范围",
            examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"],
        ),
    ) -> None:
        # 模糊查询字段
        self.strategy_name = (QueueEnum.like.value, strategy_name)
        # 精确查询字段
        if location:
            self.location = (QueueEnum.eq.value, location)
        # 精确查询字段
        if gender:
            self.gender = (QueueEnum.eq.value, gender)
        # 精确查询字段
        if age_min:
            self.age_min = (QueueEnum.eq.value, age_min)
        # 精确查询字段
        if age_max:
            self.age_max = (QueueEnum.eq.value, age_max)
        # 精确查询字段
        if daily_batch_limit:
            self.daily_batch_limit = (QueueEnum.eq.value, daily_batch_limit)
        # 精确查询字段
        if priority:
            self.priority = (QueueEnum.eq.value, priority)
        # 精确查询字段
        if status:
            self.status = (QueueEnum.eq.value, status)
        # 精确查询字段
        if created_id:
            self.created_id = (QueueEnum.eq.value, created_id)
        # 精确查询字段
        if updated_id:
            self.updated_id = (QueueEnum.eq.value, updated_id)
        # 时间范围查询
        if created_time and len(created_time) == 2:
            self.created_time = (
                QueueEnum.between.value,
                (created_time[0], created_time[1]),
            )
        if updated_time and len(updated_time) == 2:
            self.updated_time = (
                QueueEnum.between.value,
                (updated_time[0], updated_time[1]),
            )
