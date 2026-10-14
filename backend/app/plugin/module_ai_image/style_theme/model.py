# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Boolean, String, DateTime, BigInteger, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class AiStyleThemeModel(ModelMixin, UserMixin):
    """
    AI写真样式主题表
    """

    __tablename__: str = "ai_style_theme"
    __table_args__: dict[str, str] = {"comment": "AI写真样式主题"}
    __loader_options__: list[str] = ["created_by", "updated_by"]

    gender: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="性别(male/female)"
    )
    theme_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="主题名称(如: 井冈山小红军)"
    )
    material: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="材质描述(如: 水洗粗棉布)"
    )
    clothing_style: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="穿着风格描述"
    )
    colors: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="配色方案"
    )
    vibe: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="氛围感关键词"
    )
    remark: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="备注"
    )
