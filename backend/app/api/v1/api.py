"""API v1 main router."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, documents, notes, spaces, users, annotations, citations, export, ollama

api_router = APIRouter()

# 认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户路由
api_router.include_router(users.router, prefix="/users", tags=["用户"])

# 聊天路由
api_router.include_router(chat.router, prefix="/chat", tags=["聊天"])

# 空间路由
api_router.include_router(spaces.router, prefix="/spaces", tags=["空间"])

# 文档路由
api_router.include_router(documents.router, prefix="/documents", tags=["文档"])

# 代理路由
from app.api.v1.endpoints import agents
api_router.include_router(agents.router, prefix="/agents", tags=["代理"])

# 笔记路由
api_router.include_router(notes.router, prefix="/notes", tags=["笔记"])

# 标注路由
api_router.include_router(annotations.router, prefix="/annotations", tags=["标注"])

# 引用路由
api_router.include_router(citations.router, prefix="/citations", tags=["引用"])

# 导出路由
api_router.include_router(export.router, prefix="/export", tags=["导出"])

# Ollama路由
api_router.include_router(ollama.router, prefix="/ollama", tags=["Ollama"])
