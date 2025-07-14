"""CRUD operations module."""

from app.crud.annotation import crud_annotation
from app.crud.citation import crud_citation
from app.crud.conversation import crud_conversation
from app.crud.document import crud_document
from app.crud.message import crud_message
from app.crud.note import crud_note
from app.crud.note_version import crud_note_version
from app.crud.space import crud_space
from app.crud.user import crud_user

__all__ = [
    "crud_user",
    "crud_space",
    "crud_document",
    "crud_conversation",
    "crud_message",
    "crud_annotation",
    "crud_citation",
    "crud_note",
    "crud_note_version",
]
