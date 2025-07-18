"""
Service layer module for Second Brain application.

This module provides intelligent service selection and exports all available services.
Services are organized by functionality:
- AI Services: Multi-model AI interactions and embeddings
- Document Services: File processing and text extraction
- Vector Services: Vector database operations for semantic search
- Business Logic Services: Conversations, spaces, search, etc.
"""

# AI相关服务
from app.services.ai_service import AIService, ai_service

# 业务逻辑服务
from app.services.conversation_service import ConversationService

# 文档处理服务
from app.services.document_service import DocumentService, document_service
from app.services.multimodal_helper import MultimodalHelper, multimodal_helper
from app.services.search_service import SearchService
from app.services.space_service import SpaceService

# 向量搜索服务
from app.services.vector_service import VectorService, vector_service

# 研究服务
try:
    from app.services.deep_research_service import (
        DeepResearchService,
        deep_research_service,
    )

    _deep_research_available = True
except ImportError:
    _deep_research_available = False
    DeepResearchService = None  # type: ignore
    deep_research_service = None  # type: ignore

# 代理服务（当前处于开发中）
# from app.services.agent_service import AgentService, agent_service

# 创建单例服务实例
conversation_service = ConversationService()
search_service = SearchService()
space_service = SpaceService()


def _check_document_libs_available() -> bool:
    """检查文档处理库是否已安装。

    Returns:
        bool: 如果所有文档处理库都已安装返回 True，否则返回 False
    """
    try:
        import docx  # noqa: F401
        import pdfplumber  # noqa: F401
        import pptx  # noqa: F401

        return True
    except ImportError:
        return False


def get_service_status() -> dict[str, str]:
    """获取当前服务状态信息。

    Returns:
        dict[str, str]: 服务名到状态的映射
            - "full": 服务完全可用
            - "limited": 服务部分可用（缺少某些依赖）
            - "disabled": 服务不可用
    """
    return {
        "ai_service": "full",
        "document_service": "full" if _check_document_libs_available() else "limited",
        "vector_service": "full",
        "conversation_service": "full",
        "search_service": "full",
        "space_service": "full",
        "deep_research_service": "full" if _deep_research_available else "disabled",
        "agent_service": "disabled",  # 当前处于开发中
        "multimodal_helper": "full",
    }


__all__ = [
    # AI服务
    "AIService",
    "ai_service",
    "MultimodalHelper",
    "multimodal_helper",
    # 文档服务
    "DocumentService",
    "document_service",
    # 向量服务
    "VectorService",
    "vector_service",
    # 业务逻辑服务
    "ConversationService",
    "conversation_service",
    "SearchService",
    "search_service",
    "SpaceService",
    "space_service",
    # 研究服务
    "DeepResearchService",
    "deep_research_service",
    # 工具函数
    "get_service_status",
]
