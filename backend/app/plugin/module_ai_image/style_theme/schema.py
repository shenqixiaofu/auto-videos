# -*- coding: utf-8 -*-

from typing import Annotated, Optional
from pydantic import BaseModel, ConfigDict, Field
from fastapi import Query
from app.core.validator import DateTimeStr
from datetime import datetime
from app.core.validator import DateTimeStr
from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema, UserBySchema


class AiStyleThemeCreateSchema(BaseModel):
    """
    AI写真样式主题新增模型
    """

    theme_name: str = Field(default=..., description="主题名称(如: 井冈山小红军)")
    material: str = Field(default=..., description="材质描述(如: 水洗粗棉布)")
    clothing_style: str = Field(default=..., description="穿着风格描述")
    gender: str = Field(default=..., description="性别(male/female)")
    colors: str = Field(default=..., description="配色方案")
    vibe: str = Field(default=..., description="氛围感关键词")
    status: int = Field(default="0", description="状态: 1-启用, 0-禁用")
    remark: Optional[str] = Field(default=None, description="备注")


class AiStyleThemeUpdateSchema(AiStyleThemeCreateSchema):
    """
    AI写真样式主题更新模型
    """

    ...


class AiStyleThemeOutSchema(AiStyleThemeCreateSchema, BaseSchema, UserBySchema):
    """
    AI写真样式主题响应模型
    """

    model_config = ConfigDict(from_attributes=True)


class AiStyleThemeQueryParam:
    """AI写真样式主题查询参数"""

    def __init__(
        self,
        # 使用 Annotated 分离类型声明和默认值
        theme_name: Annotated[
            str | None, Query(description="主题名称(如: 井冈山小红军)")
        ] = None,
        material: Annotated[
            str | None, Query(description="材质描述(如: 水洗粗棉布)")
        ] = None,
        clothing_style: Annotated[str | None, Query(description="穿着风格描述")] = None,
        colors: Annotated[str | None, Query(description="配色方案")] = None,
        vibe: Annotated[str | None, Query(description="氛围感关键词")] = None,
        gender: Annotated[str | None, Query(description="性别(male/female)")] = None,
        status: Annotated[int | None, Query(description="状态: 1-启用, 0-禁用")] = None,
        remark: Annotated[str | None, Query(description="备注")] = None,
        created_id: Annotated[int | None, Query(description="创建人ID")] = None,
        updated_id: Annotated[int | None, Query(description="更新人ID")] = None,
        # 重点看这里，默认值变成了 Python 原生的 = None
        created_time: Annotated[
            list[DateTimeStr] | None,
            Query(
                description="创建时间范围",
                examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"],
            ),
        ] = None,
        updated_time: Annotated[
            list[DateTimeStr] | None,
            Query(
                description="更新时间范围",
                examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"],
            ),
        ] = None,
    ) -> None:
        # 模糊查询字段
        self.theme_name = (QueueEnum.like.value, theme_name)
        # 精确查询字段
        if material:
            self.material = (QueueEnum.eq.value, material)
        # 精确查询字段
        if clothing_style:
            self.clothing_style = (QueueEnum.eq.value, clothing_style)
        # 精确查询字段
        if colors:
            self.colors = (QueueEnum.eq.value, colors)
        # 精确查询字段
        if vibe:
            self.vibe = (QueueEnum.eq.value, vibe)
        # 精确查询字段
        if status:
            self.status = (QueueEnum.eq.value, status)
        # 精确查询字段
        if gender:
            self.gender = (QueueEnum.eq.value, gender)
        if remark:
            self.remark = (QueueEnum.eq.value, remark)
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


class AiStyleThemeGenerateRequest(BaseModel):
    gender: str = Field(..., description="性别(male/female/any)", examples=["female"])
    theme_name: str = Field(..., description="主题名称", examples=["井冈山小红军"])
    remark: str | None = Field(
        None, description="补充说明或特殊要求", examples=["希望更偏向复古胶片感"]
    )
