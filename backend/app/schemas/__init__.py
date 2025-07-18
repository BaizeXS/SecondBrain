"""
Schemas package for Second Brain application.

This module exports all Pydantic schemas used for API request/response validation.
"""

# Agent schemas
from app.schemas.agents import (
    AgentCreate,
    AgentDetail,
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentListResponse,
    AgentResponse,
    AgentUpdate,
    DeepResearchRequest,
    DeepResearchResponse,
)

# Authentication schemas
from app.schemas.auth import (
    ChangePasswordRequest,
    RefreshTokenRequest,
    ResetPasswordConfirm,
    ResetPasswordRequest,
    Token,
    TokenData,
    UserLogin,
    UserRegister,
)

# Conversation schemas
from app.schemas.conversations import (
    ChatMode,  # Enum
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    MessageUpdate,
)

# Document schemas
from app.schemas.documents import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
    DocumentCreate,
    DocumentDetail,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadRequest,
)

# Space schemas
from app.schemas.spaces import (
    SpaceCollaborationCreate,
    SpaceCollaborationResponse,
    SpaceCreate,
    SpaceDetail,
    SpaceListResponse,
    SpaceResponse,
    SpaceStats,
    SpaceUpdate,
)

# User schemas
from app.schemas.users import (
    APIKeyCreate,
    APIKeyResponse,
    UserBase,
    UserCreate,
    UserProfile,
    UserResponse,
    UserStats,
    UserUpdate,
)

__all__ = [
    # Agent schemas
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "AgentDetail",
    "AgentListResponse",
    "AgentExecuteRequest",
    "AgentExecuteResponse",
    "DeepResearchRequest",
    "DeepResearchResponse",
    # Auth schemas
    "UserLogin",
    "UserRegister",
    "Token",
    "TokenData",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    "ResetPasswordConfirm",
    # Conversation schemas
    "MessageCreate",
    "MessageUpdate",
    "MessageResponse",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationDetail",
    "ChatRequest",
    "ChatResponse",
    "ChatMode",
    # Document schemas
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentDetail",
    "DocumentListResponse",
    "DocumentUploadRequest",
    "AnnotationCreate",
    "AnnotationUpdate",
    "AnnotationResponse",
    # Space schemas
    "SpaceCreate",
    "SpaceUpdate",
    "SpaceResponse",
    "SpaceDetail",
    "SpaceListResponse",
    "SpaceCollaborationCreate",
    "SpaceCollaborationResponse",
    "SpaceStats",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    "APIKeyCreate",
    "APIKeyResponse",
    "UserStats",
]
