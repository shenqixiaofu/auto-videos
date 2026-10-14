# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import JSON, DateTime, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class AiImageAutoStrategyModel(ModelMixin, UserMixin):
    """
    AI 24小时自动化生图策略表
    """

    __tablename__: str = "ai_image_auto_strategy"
    __table_args__: dict[str, str] = {"comment": "AI 24小时自动化生图策略"}
    __loader_options__: list[str] = ["created_by", "updated_by"]

    strategy_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="策略名称(如：千家洞春季汉服巡检)"
    )
    theme_ids: Mapped[list[int] | None] = mapped_column(
        JSON, nullable=True, comment="关联的主题样式ID列表(如：[1,2,3])"
    )
    location: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="目标地点(如：千家洞)"
    )
    gender: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="目标性别(男/女/随机)"
    )
    background_strategy: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="背景描述策略(如：高级感背景肌理、特定的光影氛围或需要屏蔽的杂乱元素)",
    )
    age_min: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="年龄下限"
    )
    age_max: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="年龄上限"
    )
    daily_batch_limit: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="每天最多生成几个Batch"
    )
    priority: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="执行优先级(数字越大越先执行)"
    )
