"""
API package for Second Brain Backend.

This package contains all API versions and their endpoints.
Currently supports:
- v1: The main API version with full feature support

The API is organized into the following main categories:
- Authentication & Users: User management and authentication
- AI Features: Chat, agents, and AI-powered functionalities
- Content Management: Spaces, documents, notes
- Content Enhancement: Annotations, citations, exports
"""

# 从 v1 导出主要的 API 路由器，方便在 main.py 中使用
from app.api.v1.api import api_router as v1_router

__all__ = ["v1_router"]

