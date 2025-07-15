"""Fix metadata column naming

Revision ID: 6bf7957f7aa9
Revises: add_last_login_field
Create Date: 2025-07-14 22:13:28.955550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6bf7957f7aa9'
down_revision: Union[str, None] = 'add_last_login_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Rename metadata columns to meta_data with data preservation ###
    
    # List of tables to process
    tables = ['citations', 'conversations', 'documents', 'messages', 'note_versions', 'notes', 'spaces']
    
    for table in tables:
        # Add new meta_data column
        op.add_column(table, sa.Column('meta_data', sa.JSON(), nullable=True))
        
        # Copy data from metadata to meta_data
        op.execute(f"UPDATE {table} SET meta_data = metadata")
        
        # Drop old metadata column
        op.drop_column(table, 'metadata')


def downgrade() -> None:
    # ### Rename meta_data columns back to metadata with data preservation ###
    
    # List of tables to process (reverse order)
    tables = ['spaces', 'notes', 'note_versions', 'messages', 'documents', 'conversations', 'citations']
    
    for table in tables:
        # Add metadata column back
        op.add_column(table, sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
        
        # Copy data from meta_data to metadata
        op.execute(f"UPDATE {table} SET metadata = meta_data")
        
        # Drop meta_data column
        op.drop_column(table, 'meta_data')