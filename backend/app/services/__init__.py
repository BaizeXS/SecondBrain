"""Service layer module with intelligent service selection."""

import os
from typing import TYPE_CHECKING


# 检查AI服务是否可用
def _check_ai_service_available() -> bool:
    """检查是否有可用的AI API密钥."""
    ai_keys = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "DEEPSEEK_API_KEY"
    ]
    return any(
        os.getenv(key) and os.getenv(key).lower() not in ['none', '', 'your_api_key']
        for key in ai_keys
    )

# 检查文档处理库是否可用
def _check_document_libs_available() -> bool:
    """检查文档处理库是否已安装."""
    try:
        import docx
        import pptx
        import pypdf
        return True
    except ImportError:
        return False

# 导入服务
if _check_ai_service_available():
    from app.services.ai_service import AIService
else:
    # 如果没有配置 AI 服务，使用简化版本
    from app.services.ai_service_simple import SimpleAIService as AIService

# 文档服务使用带 CRUD 的版本（目前在 document_service_simple.py 中）
# 其他服务正常导入（没有简化版本）
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService
from app.services.document_service_simple import DocumentService
from app.services.search_service import SearchService
from app.services.space_service import SpaceService
from app.services.vector_service import VectorService

# 导出所有服务
__all__ = [
    "AIService",
    "DocumentService",
    "AgentService",
    "ConversationService",
    "SearchService",
    "SpaceService",
    "VectorService",
]

# 服务状态信息
def get_service_status():
    """获取当前服务状态信息."""
    return {
        "ai_service": "full" if _check_ai_service_available() else "simple",
        "document_service": "full" if _check_document_libs_available() else "simple",
        "agent_service": "full",
        "conversation_service": "full",
        "search_service": "full",
        "space_service": "full",
        "vector_service": "full",
    }
