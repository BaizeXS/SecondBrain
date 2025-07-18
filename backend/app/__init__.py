"""
Second Brain Backend Application.

An AI-powered knowledge management system with:
- AI Chat: Multi-model conversations with Chat and Search modes
- Intelligent Agents: Deep Research automation using Perplexity API
- Knowledge Base (Space): Document management with AI-enhanced interactions
"""

__version__ = "0.1.0"

# Make key components easily accessible at package level
from app.core import get_db, settings
from app.models import Conversation, Document, Message, Space, User
from app.schemas import DocumentResponse, SpaceResponse, UserResponse

__all__ = [
    "__version__",
    # Core exports
    "settings",
    "get_db",
    # Model exports
    "User",
    "Space",
    "Document",
    "Conversation",
    "Message",
    # Schema exports
    "UserResponse",
    "SpaceResponse",
    "DocumentResponse",
]
