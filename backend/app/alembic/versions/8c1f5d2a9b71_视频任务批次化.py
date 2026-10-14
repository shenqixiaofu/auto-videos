"""迁移脚本

Revision ID: 8c1f5d2a9b71
Revises: 350ed802e74e
Create Date: 2026-08-07 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8c1f5d2a9b71"
down_revision: Union[str, None] = "350ed802e74e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "video_task_batch",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="主键ID"),
        sa.Column("uuid", sa.String(length=64), nullable=False, unique=True, comment="UUID全局唯一标识"),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="0", comment="是否启用(0:启用 1:禁用)"),
        sa.Column("description", sa.Text(), nullable=True, comment="备注/描述"),
        sa.Column("created_time", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_time", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.Column("created_id", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("updated_id", sa.Integer(), nullable=True, comment="更新人ID"),
        sa.Column("batch_no", sa.String(length=64), nullable=False, unique=True, comment="批次编号"),
        sa.Column("batch_name", sa.String(length=128), nullable=False, comment="批次名称"),
        sa.Column("batch_type", sa.String(length=16), nullable=False, server_default="single", comment="批次类型"),
        sa.Column("expected_count", sa.Integer(), nullable=False, server_default="1", comment="预计子任务数量"),
        sa.Column("task_count", sa.Integer(), nullable=False, server_default="0", comment="已创建子任务数量"),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0", comment="已完成子任务数量"),
        sa.Column("process_status", sa.String(length=16), nullable=False, server_default="draft", comment="批次状态"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0", comment="批次处理进度百分比"),
        sa.Column("current_stage", sa.String(length=32), nullable=False, server_default="draft", comment="批次当前阶段"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="批次失败信息"),
        sa.ForeignKeyConstraint(["created_id"], ["sys_user.id"], ondelete="SET NULL", onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["updated_id"], ["sys_user.id"], ondelete="SET NULL", onupdate="CASCADE"),
        mysql_engine="InnoDB",
        comment="自动剪辑任务批次表",
    )
    op.create_index("ix_video_task_batch_batch_no", "video_task_batch", ["batch_no"], unique=True)
    op.create_index("ix_video_task_batch_batch_type", "video_task_batch", ["batch_type"], unique=False)
    op.create_index(
        "ix_video_task_batch_process_status", "video_task_batch", ["process_status"], unique=False
    )
    op.create_index("ix_video_task_batch_created_time", "video_task_batch", ["created_time"], unique=False)

    op.add_column(
        "video_task",
        sa.Column("batch_id", sa.Integer(), nullable=True, comment="所属批次ID"),
    )
    op.add_column(
        "video_task",
        sa.Column(
            "batch_index",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="批次内顺序",
        ),
    )
    op.create_index("ix_video_task_batch_id", "video_task", ["batch_id"], unique=False)

    batch_table = sa.Table("video_task_batch", sa.MetaData(), autoload_with=bind)
    task_table = sa.Table("video_task", sa.MetaData(), autoload_with=bind)

    task_rows = bind.execute(
        sa.select(task_table).order_by(task_table.c.id.asc())
    ).mappings().all()
    terminal_statuses = {"succeeded", "failed", "cancelled"}
    for row in task_rows:
        batch_values = {
            "uuid": str(uuid4()),
            "status": "0",
            "description": None,
            "created_time": row["created_time"],
            "updated_time": row["updated_time"],
            "created_id": row["created_id"],
            "updated_id": row["updated_id"],
            "batch_no": str(row["task_no"]),
            "batch_name": str(row["title"]),
            "batch_type": "single",
            "expected_count": 1,
            "task_count": 1,
            "completed_count": 1 if row["process_status"] in terminal_statuses else 0,
            "process_status": str(row["process_status"]),
            "progress": int(row["progress"] or 0),
            "current_stage": str(row["current_stage"] or "draft"),
            "error_message": row["error_message"],
        }
        result = bind.execute(batch_table.insert().values(**batch_values))
        batch_id = result.inserted_primary_key[0]
        bind.execute(
            task_table.update()
            .where(task_table.c.id == row["id"])
            .values(batch_id=batch_id, batch_index=1)
        )

    op.alter_column(
        "video_task",
        "batch_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_video_task_batch_id_video_task_batch",
        "video_task",
        "video_task_batch",
        ["batch_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_video_task_batch_id_video_task_batch",
        "video_task",
        type_="foreignkey",
    )
    op.drop_index("ix_video_task_batch_id", table_name="video_task")
    op.drop_column("video_task", "batch_index")
    op.drop_column("video_task", "batch_id")
    op.drop_index("ix_video_task_batch_created_time", table_name="video_task_batch")
    op.drop_index("ix_video_task_batch_process_status", table_name="video_task_batch")
    op.drop_index("ix_video_task_batch_batch_type", table_name="video_task_batch")
    op.drop_index("ix_video_task_batch_batch_no", table_name="video_task_batch")
    op.drop_table("video_task_batch")
