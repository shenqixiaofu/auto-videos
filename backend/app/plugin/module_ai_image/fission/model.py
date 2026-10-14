from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import ModelMixin, UserMixin


class AIImageBatch(ModelMixin, UserMixin):
    """
    AI人设模版批次表 (Action A & B)
    """

    __tablename__: str = "ai_image_batch"
    __table_args__: dict = {"comment": "AI提示词生成批次表"}

    # 业务字段
    batch_sn: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False, comment="批次唯一编号"
    )
    strategy_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_image_auto_strategy.id"),
        nullable=True,
        comment="关联的自动化策略ID",
    )
    input_location: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False, comment="初始输入地点"
    )

    theme: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Python预设的策划主题名称"
    )
    gender: Mapped[str] = mapped_column(String(10), default="女", comment="性别")
    age: Mapped[int] = mapped_column(Integer, default=20, comment="年龄数字")

    # LLM 决策字段
    selected_scene: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="LLM生成的具体场景"
    )
    selected_style: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="LLM生成的具体风格"
    )
    task_count: Mapped[int] = mapped_column(
        Integer, default=10, comment="批次生成的任务数量"
    )

    status: Mapped[int] = mapped_column(Integer, default=1, comment="1:生图中 2:已完成")

    # 关联关系：一对多到 Task
    tasks: Mapped[List["AIImageTask"]] = relationship(
        "AIImageTask",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",  # 框架推荐的预加载方式
    )


class AIImageTask(ModelMixin, UserMixin):
    """
    AI生图任务明细表 (Action C & Agent执行)
    """

    __tablename__: str = "ai_image_task"
    __table_args__: dict = {"comment": "AI生图任务明细表"}

    batch_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ai_image_batch.id", ondelete="CASCADE"), nullable=False
    )
    task_sn: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False, comment="任务唯一编号"
    )

    # 冗余字段：为了查询提效，不用 JOIN
    location: Mapped[str | None] = mapped_column(
        String(100), index=True, comment="大地点"
    )
    style_tag: Mapped[str | None] = mapped_column(
        String(100), index=True, comment="风格标签"
    )
    gender: Mapped[str | None] = mapped_column(String(10), comment="性别")
    age: Mapped[int | None] = mapped_column(Integer, comment="年龄数字")
    version_history: Mapped[list | None] = mapped_column(
        JSON, default=list, comment="版本演进历史记录"
    )
    current_version: Mapped[int] = mapped_column(
        Integer, default=1, comment="当前展示的版本号"
    )
    swapped_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="火山引擎换脸生成的最终结果图"
    )

    # 可选：记录换脸时间，方便后台统计性能
    swapped_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="换脸操作完成时间"
    )

    bg_version_history: Mapped[list | None] = mapped_column(
        JSON, default=list, comment="换背景(瞬移)演进历史记录"
    )
    current_bg_version: Mapped[int] = mapped_column(
        Integer, default=0, comment="当前选中的背景版本号 (0代表保持原图未换背景)"
    )
    # 为了前端瀑布流展示提效，单独冗余一个最新背景图的 URL（避免每次都要解析 JSON）
    current_bg_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="当前生效的换背景结果图URL"
    )

    # Action C 裂变内容
    view_type: Mapped[str | None] = mapped_column(String(50), comment="景别")
    action_desc: Mapped[str | None] = mapped_column(String(255), comment="动作简述")
    positive_prompt: Mapped[str] = mapped_column(
        Text, nullable=False, comment="完整的黄金模板提示词"
    )

    # 业务执行状态 (区别于框架自带的 status)
    # 0:待抢单, 1:生成中, 2:成功, 3:失败
    process_status: Mapped[int] = mapped_column(
        Integer, default=0, index=True, comment="业务处理状态"
    )
    agent_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="执行任务的机器ID"
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="生成的图片URL"
    )

    # 时间监控
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="Agent开始抢单时间"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="任务完成时间"
    )

    # 反向关联
    batch: Mapped["AIImageBatch"] = relationship("AIImageBatch", back_populates="tasks")
