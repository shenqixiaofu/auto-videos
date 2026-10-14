"""视频任务配置收敛为竖屏vlog

Revision ID: 9d4a7f6b2c31
Revises: 350ed802e74e
Create Date: 2026-07-30 16:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9d4a7f6b2c31"
down_revision: Union[str, None] = "350ed802e74e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 历史任务配置统一收敛到当前唯一产品模式，避免响应 schema 校验旧枚举失败。
    op.execute(
        sa.text(
            """
            UPDATE video_task
            SET config = JSON_SET(
                COALESCE(config, JSON_OBJECT()),
                '$.aspect_ratio',
                '9:16',
                '$.style_preset',
                'vlog'
            )
            """
        )
    )


def downgrade() -> None:
    # 数据收敛不可逆，不恢复历史多风格配置。
    pass
