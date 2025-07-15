"""Update chat modes - remove think mode

Revision ID: update_chat_modes
Revises: add_last_login_field
Create Date: 2025-01-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'update_chat_modes'
down_revision: Union[str, None] = 'add_last_login_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """将所有 'think' 模式更新为 'chat' 模式"""
    # 更新 conversations 表中的 mode 字段
    op.execute("""
        UPDATE conversations 
        SET mode = 'chat' 
        WHERE mode = 'think'
    """)
    
    # 更新 usage_records 表中的 action 字段
    op.execute("""
        UPDATE usage_records 
        SET action = 'chat' 
        WHERE action = 'think'
    """)


def downgrade() -> None:
    """降级操作 - 这里我们不恢复数据，因为无法区分哪些 'chat' 原本是 'think'"""
    pass