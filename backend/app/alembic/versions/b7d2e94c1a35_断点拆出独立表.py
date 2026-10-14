"""断点拆出独立表

Revision ID: b7d2e94c1a35
Revises: c4f7a8b9d012
Create Date: 2026-10-10 15:30:00.000000

"""
from __future__ import annotations

import json
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b7d2e94c1a35"
down_revision: Union[str, None] = "c4f7a8b9d012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# config 里那个键的历史名字，搬迁和回滚都认它。
_LEGACY_KEY = "processing_checkpoint"
_TABLE = "video_task_checkpoint"
_TASK_ID_INDEX = "ix_video_task_checkpoint_task_id"


def upgrade() -> None:
    # 断点（单任务 80~160KB，脏数据到过 6MB）从 video_task.config 搬到独立表。
    # 留在 config 里会把 video_task 变成宽表：MySQL 的 filesort 要把整行塞进
    # sort_buffer，只要查询读了 config 又带 ORDER BY，单行超过约 140KB 就报
    # 1038 Out of sort memory。搬走后 video_task 单行回到 ~1KB。
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 应用启动时的 create_all（core/database.py）会先把这张表建出来，之后这里再
    # create_table 必然撞「表已存在」。所以以库里实际状态为准，只补缺的部分。
    if not inspector.has_table(_TABLE):
        op.create_table(
            _TABLE,
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="主键ID"),
            sa.Column("uuid", sa.String(length=64), nullable=False, unique=True, comment="UUID全局唯一标识"),
            sa.Column("status", sa.String(length=10), nullable=False, server_default="0", comment="是否启用(0:启用 1:禁用)"),
            sa.Column("description", sa.Text(), nullable=True, comment="备注/描述"),
            sa.Column("created_time", sa.DateTime(), nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(), nullable=False, comment="更新时间"),
            sa.Column("task_id", sa.Integer(), nullable=False, comment="所属任务ID"),
            sa.Column("checkpoint", sa.JSON(), nullable=False, comment="阶段断点"),
            sa.ForeignKeyConstraint(["task_id"], ["video_task.id"], ondelete="CASCADE"),
            mysql_engine="InnoDB",
            comment="自动剪辑任务处理断点表",
        )
        op.create_index(_TASK_ID_INDEX, _TABLE, ["task_id"], unique=True)
    elif _TASK_ID_INDEX not in {item["name"] for item in inspector.get_indexes(_TABLE)}:
        op.create_index(_TASK_ID_INDEX, _TABLE, ["task_id"], unique=True)

    # 逐行搬：走 bind 而不是 SQL 方言函数，MySQL / postgres 都能跑。
    task_table = sa.Table("video_task", sa.MetaData(), autoload_with=bind)
    checkpoint_table = sa.Table(_TABLE, sa.MetaData(), autoload_with=bind)
    # 表里已有行的是新代码自己写进去的，比 config 里那份旧副本新，保留不动。
    migrated_task_ids = {row[0] for row in bind.execute(sa.select(checkpoint_table.c.task_id))}

    rows = (
        bind.execute(
            sa.select(
                task_table.c.id,
                task_table.c.config,
                task_table.c.created_time,
                task_table.c.updated_time,
            )
        )
        .mappings()
        .all()
    )
    for row in rows:
        config = row["config"]
        if isinstance(config, (str, bytes, bytearray)):
            config = json.loads(config)
        if not isinstance(config, dict) or _LEGACY_KEY not in config:
            continue
        checkpoint = config.get(_LEGACY_KEY)
        if isinstance(checkpoint, dict) and row["id"] not in migrated_task_ids:
            bind.execute(
                checkpoint_table.insert().values(
                    uuid=str(uuid4()),
                    status="0",
                    description="迁移自 video_task.config.processing_checkpoint",
                    created_time=row["created_time"],
                    updated_time=row["updated_time"],
                    task_id=row["id"],
                    checkpoint=checkpoint,
                )
            )
        # config 只摘掉断点键，其余小字段（aspect_ratio / stage_timings 等）原样保留。
        bind.execute(
            task_table.update()
            .where(task_table.c.id == row["id"])
            .values(config={k: v for k, v in config.items() if k != _LEGACY_KEY})
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(_TABLE):
        return

    task_table = sa.Table("video_task", sa.MetaData(), autoload_with=bind)
    checkpoint_table = sa.Table(_TABLE, sa.MetaData(), autoload_with=bind)

    rows = (
        bind.execute(sa.select(checkpoint_table.c.task_id, checkpoint_table.c.checkpoint))
        .mappings()
        .all()
    )
    for row in rows:
        current = bind.execute(
            sa.select(task_table.c.config).where(task_table.c.id == row["task_id"])
        ).first()
        if current is None:
            continue
        config = current[0]
        if isinstance(config, (str, bytes, bytearray)):
            config = json.loads(config)
        merged = dict(config or {})
        merged[_LEGACY_KEY] = row["checkpoint"]
        bind.execute(
            task_table.update()
            .where(task_table.c.id == row["task_id"])
            .values(config=merged)
        )

    if _TASK_ID_INDEX in {item["name"] for item in inspector.get_indexes(_TABLE)}:
        op.drop_index(_TASK_ID_INDEX, table_name=_TABLE)
    op.drop_table(_TABLE)
