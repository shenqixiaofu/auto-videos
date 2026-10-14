"""自动剪辑全局配置表

Revision ID: c3f1a9d24b70
Revises: b7d2e94c1a35
Create Date: 2026-10-12 09:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3f1a9d24b70"
down_revision: Union[str, None] = "b7d2e94c1a35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "video_processing_config"


def upgrade() -> None:
    # 全局配置（模型名、提示词模板、生图通道）只有一行 id=1。做成表而不是塞进
    # env 或 sys_param：env 改一次要重启；sys_param 的 config_value 是 String(500)，
    # 放不下上千字符的提示词。
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 应用启动时的 create_all（core/database.py）会先把这张表建出来，之后这里再
    # create_table 必然撞「表已存在」。以库里实际状态为准，只补缺的。
    if not inspector.has_table(_TABLE):
        op.create_table(
            _TABLE,
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="主键ID"),
            sa.Column("uuid", sa.String(length=64), nullable=False, unique=True, comment="UUID全局唯一标识"),
            sa.Column("status", sa.String(length=10), nullable=False, server_default="0", comment="是否启用(0:启用 1:禁用)"),
            sa.Column("description", sa.Text(), nullable=True, comment="备注/描述"),
            sa.Column("created_time", sa.DateTime(), nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(), nullable=False, comment="更新时间"),
            sa.Column("config", sa.JSON(), nullable=False, comment="全局配置（模型、提示词、生图通道）"),
            sa.Column("updated_id", sa.Integer(), nullable=True, comment="最后更新人ID"),
            sa.ForeignKeyConstraint(["updated_id"], ["sys_user.id"], ondelete="SET NULL"),
            mysql_engine="InnoDB",
            comment="自动剪辑全局配置表",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table(_TABLE):
        op.drop_table(_TABLE)
