"""API v1 main router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    auth,
    chat,
    documents,
    spaces,
    users,
)

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
api_router.include_router(agents.router, prefix="/agents", tags=["代理"])
