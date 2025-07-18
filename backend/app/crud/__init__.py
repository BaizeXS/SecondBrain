"""
CRUD operations module for Second Brain application.

This module provides database operations for all models following the CRUD pattern:
- Create: 创建新记录
- Read: 读取记录（单个或多个）
- Update: 更新现有记录
- Delete: 删除记录

All CRUD classes inherit from CRUDBase which provides common operations.
"""

# Base CRUD class
# CRUD instances for each model
from app.crud.annotation import crud_annotation
from app.crud.base import CRUDBase
from app.crud.citation import crud_citation
from app.crud.conversation import crud_conversation
from app.crud.document import crud_document
from app.crud.message import crud_message
from app.crud.note import crud_note
from app.crud.note_version import crud_note_version
from app.crud.space import crud_space
from app.crud.user import crud_user

# Note: The following models don't have dedicated CRUD classes yet:
# - APIKey: Managed directly in auth endpoints
# - SpaceCollaboration: Managed through space CRUD
# - Agent: Uses custom service layer
# - AgentExecution: Uses custom service layer
# - UsageLog: Write-only model
# - UserCustomModel: Future feature

__all__ = [
    # Base class
    "CRUDBase",
    # User related
    "crud_user",
    # Space (knowledge base) related
    "crud_space",
    # Document related
    "crud_document",
    "crud_annotation",
    "crud_citation",
    # Note related
    "crud_note",
    "crud_note_version",
    # Conversation related
    "crud_conversation",
    "crud_message",
]

