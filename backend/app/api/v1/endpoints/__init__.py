"""
API v1 endpoints package.

This package contains all endpoint modules for API v1.
Each module represents a feature domain with related endpoints.

Endpoint Organization:
- auth: Authentication endpoints (login, register, refresh tokens)
- users: User profile and preference management
- chat: AI chat conversations with multi-model support
- agents: AI agents including Deep Research functionality
- spaces: Knowledge space management
- documents: Document upload, processing, and retrieval
- notes: Note creation and version management
- annotations: Document annotations and highlights
- citations: Citation management for documents
- export: Export functionality for various content types
- ollama: Local LLM integration endpoints
"""

# 导入所有端点路由器，方便在 api.py 中统一注册
from app.api.v1.endpoints.agents import router as agents_router
from app.api.v1.endpoints.annotations import router as annotations_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.citations import router as citations_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.export import router as export_router
from app.api.v1.endpoints.notes import router as notes_router
from app.api.v1.endpoints.ollama import router as ollama_router
from app.api.v1.endpoints.spaces import router as spaces_router
from app.api.v1.endpoints.users import router as users_router

__all__ = [
    "agents_router",
    "annotations_router",
    "auth_router",
    "chat_router",
    "citations_router",
    "documents_router",
    "export_router",
    "notes_router",
    "ollama_router",
    "spaces_router",
    "users_router",
]

