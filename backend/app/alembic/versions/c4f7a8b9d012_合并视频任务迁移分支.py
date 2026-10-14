"""合并视频任务迁移分支

Revision ID: c4f7a8b9d012
Revises: 8c1f5d2a9b71, 9d4a7f6b2c31
Create Date: 2026-09-01 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# Alembic revision identifiers.
revision: str = "c4f7a8b9d012"
down_revision: Union[str, Sequence[str], None] = ("8c1f5d2a9b71", "9d4a7f6b2c31")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 合并批次化迁移与视频配置迁移，恢复单一 head。
    pass


def downgrade() -> None:
    # 合并迁移不包含独立数据库操作。
    pass
