"""Add last_login field to users table

Revision ID: add_last_login_field
Revises: 3e579dc16df9
Create Date: 2025-07-12 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_last_login_field'
down_revision: Union[str, None] = '3e579dc16df9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_login column to users table
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove last_login column from users table
    op.drop_column('users', 'last_login')