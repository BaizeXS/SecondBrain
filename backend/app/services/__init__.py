"""Service layer module with intelligent service selection."""

import os
from typing import TYPE_CHECKING

from app.services.ai_service import AIService, ai_service

# 在文件顶部导入所有需要的服务
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService, document_service
from app.services.multimodal_helper import MultimodalHelper, multimodal_helper
from app.services.search_service import SearchService
from app.services.space_service import SpaceService
from app.services.vector_service import VectorService

# 以下服务被注释掉，可能还在开发中
# from app.services.agent_service import AgentService

def _check_document_libs_available() -> bool:
    """检查文档处理库是否已安装."""
    try:
        import docx  # noqa: F401
        import pdfplumber  # noqa: F401
        import pptx  # noqa: F401
        return True
    except ImportError:
        return False

__all__ = [
    "AIService",
    "ai_service",
    "DocumentService",
    "document_service",
    "MultimodalHelper",
    "multimodal_helper",
    "ConversationService",
    "SearchService",
    "SpaceService",
    "VectorService",
    "get_service_status",
]


def get_service_status() -> dict[str, str]:
    """获取当前服务状态信息."""
    return {
        "ai_service": "full",
        "document_service": "full" if _check_document_libs_available() else "limited",
        "agent_service": "disabled",  # 当前被注释掉
        "conversation_service": "full",
        "search_service": "full",
        "space_service": "full",
        "vector_service": "full",
    }
