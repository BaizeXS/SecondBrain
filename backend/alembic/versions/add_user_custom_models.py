"""add user custom models table

Revision ID: add_user_custom_models
Revises: add_last_login_field
Create Date: 2025-01-14 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_user_custom_models'
down_revision = 'add_last_login_field'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_custom_models table
    op.create_table(
        'user_custom_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=True),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_custom_model_name')
    )
    op.create_index('idx_user_custom_model_user', 'user_custom_models', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_user_custom_model_user', table_name='user_custom_models')
    op.drop_table('user_custom_models')