"""Database models for Second Brain application."""

from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimestampMixin:
    """添加创建和更新时间戳的混合类."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    """用户表."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    # 用户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # 使用统计
    daily_usage: Mapped[int] = mapped_column(Integer, default=0)
    last_reset_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 偏好设置
    preferences: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # 关系
    spaces: Mapped[list["Space"]] = relationship(
        "Space", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="user"
    )
    custom_models: Mapped[list["UserCustomModel"]] = relationship(
        "UserCustomModel", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class APIKey(Base, TimestampMixin):
    """用户API密钥表."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    provider: Mapped[str] = mapped_column(String(50))  # openai, anthropic, google, etc.
    key_name: Mapped[str] = mapped_column(String(100))
    encrypted_key: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "provider", "key_name", name="unique_user_provider_key"
        ),
    )


class Space(Base, TimestampMixin):
    """知识空间表."""

    __tablename__ = "spaces"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(7))  # 十六进制颜色
    icon: Mapped[str | None] = mapped_column(String(50))

    # 空间设置
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_collaboration: Mapped[bool] = mapped_column(Boolean, default=False)

    # 元数据
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    tags: Mapped[list[str] | None] = mapped_column(JSON)

    # 统计信息
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    note_count: Mapped[int] = mapped_column(Integer, default=0)
    total_size: Mapped[int] = mapped_column(BigInteger, default=0)  # 字节

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="spaces")
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="space", cascade="all, delete-orphan"
    )
    notes: Mapped[list["Note"]] = relationship(
        "Note", back_populates="space", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="space"
    )
    collaborations: Mapped[list["SpaceCollaboration"]] = relationship(
        "SpaceCollaboration", back_populates="space", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Space(id={self.id}, name='{self.name}')>"


class SpaceCollaboration(Base, TimestampMixin):
    """空间协作表."""

    __tablename__ = "space_collaborations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    space_id: Mapped[int] = mapped_column(ForeignKey("spaces.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(20))  # viewer, editor, admin
    invited_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, pending, revoked

    # 权限设置
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    can_invite: Mapped[bool] = mapped_column(Boolean, default=False)

    # 关系
    space: Mapped["Space"] = relationship("Space", back_populates="collaborations")
    collaborator: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    inviter: Mapped["User"] = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        UniqueConstraint("space_id", "user_id", name="unique_space_user"),
    )


class Document(Base, TimestampMixin):
    """文档表."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    space_id: Mapped[int] = mapped_column(ForeignKey("spaces.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 文件信息
    filename: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(1000))  # MinIO中的路径
    file_url: Mapped[str | None] = mapped_column(String(1000))
    content_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(BigInteger)
    file_hash: Mapped[str] = mapped_column(String(64))  # SHA256哈希

    # 内容信息
    title: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(10))

    # 处理状态
    processing_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")
    embedding_status: Mapped[str] = mapped_column(String(20), default="pending")

    # 元数据
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    tags: Mapped[list[str] | None] = mapped_column(JSON)

    # 关系和层级
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id")
    )  # 用于翻译文档等

    # 关系
    space: Mapped["Space"] = relationship("Space", back_populates="documents")
    user: Mapped["User"] = relationship("User", back_populates="documents")
    annotations: Mapped[list["Annotation"]] = relationship(
        "Annotation", back_populates="document", cascade="all, delete-orphan"
    )
    children: Mapped[list["Document"]] = relationship(
        "Document", backref="parent", remote_side=[id]
    )

    # 索引
    __table_args__ = (
        Index("idx_document_space_user", "space_id", "user_id"),
        Index("idx_document_hash", "file_hash"),
        Index("idx_document_status", "processing_status"),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"


class Annotation(Base, TimestampMixin):
    """文档标注表."""

    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 标注内容
    type: Mapped[str] = mapped_column(
        String(20)
    )  # highlight, underline, note, bookmark
    content: Mapped[str | None] = mapped_column(Text)
    selected_text: Mapped[str | None] = mapped_column(Text)

    # 位置信息
    page_number: Mapped[int | None] = mapped_column(Integer)
    position_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON
    )  # 存储具体位置信息（坐标、矩形等）

    # 样式
    color: Mapped[str | None] = mapped_column(String(7))

    # 额外属性
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否私密
    tags: Mapped[list[str] | None] = mapped_column(JSON)  # 标签

    # 关系
    document: Mapped["Document"] = relationship(
        "Document", back_populates="annotations"
    )
    user: Mapped["User"] = relationship("User")

    # 索引
    __table_args__ = (
        Index("idx_annotation_document_user", "document_id", "user_id"),
        Index("idx_annotation_type", "type"),
        Index("idx_annotation_page", "document_id", "page_number"),
    )


class Note(Base, TimestampMixin):
    """笔记表."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    space_id: Mapped[int] = mapped_column(ForeignKey("spaces.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 笔记内容
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(
        String(20), default="markdown"
    )  # markdown, html, plain

    # 笔记类型和来源
    note_type: Mapped[str] = mapped_column(
        String(20), default="manual"
    )  # manual, ai, linked
    source_type: Mapped[str | None] = mapped_column(
        String(20)
    )  # user, ai, research, summary
    source_id: Mapped[str | None] = mapped_column(String(100))  # 来源ID

    # AI生成相关
    ai_model: Mapped[str | None] = mapped_column(String(100))  # 使用的AI模型
    ai_prompt: Mapped[str | None] = mapped_column(Text)  # AI生成时的提示词
    generation_params: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # 生成参数

    # 元数据
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # 关系链接
    linked_documents: Mapped[list[int] | None] = mapped_column(JSON)  # 关联的文档ID
    linked_notes: Mapped[list[int] | None] = mapped_column(JSON)  # 关联的笔记ID

    # 版本控制
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)

    # 关系
    space: Mapped["Space"] = relationship("Space", back_populates="notes")
    user: Mapped["User"] = relationship("User")
    versions: Mapped[list["NoteVersion"]] = relationship(
        "NoteVersion", back_populates="note", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_note_space_user", "space_id", "user_id"),
        Index("idx_note_type", "note_type"),
        Index("idx_note_created", "created_at"),
    )

    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"


class Conversation(Base, TimestampMixin):
    """对话表."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    space_id: Mapped[int | None] = mapped_column(ForeignKey("spaces.id"))

    # 对话信息
    title: Mapped[str] = mapped_column(String(500))
    mode: Mapped[str] = mapped_column(String(20))  # chat, search
    model: Mapped[str | None] = mapped_column(String(100))

    # 对话设置
    system_prompt: Mapped[str | None] = mapped_column(Text)
    temperature: Mapped[float | None] = mapped_column(Float)
    max_tokens: Mapped[int | None] = mapped_column(Integer)

    # 元数据
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # 统计信息
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    space: Mapped[Optional["Space"]] = relationship(
        "Space", back_populates="conversations"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}')>"


class Message(Base, TimestampMixin):
    """消息表."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))

    # 消息内容
    role: Mapped[str] = mapped_column(String(20))  # user, assistant, system
    content: Mapped[str] = mapped_column(Text)

    # AI模型信息
    model: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(50))

    # 消息统计
    token_count: Mapped[int | None] = mapped_column(Integer)
    processing_time: Mapped[float | None] = mapped_column(Float)  # 秒

    # 分支管理
    parent_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"))
    branch_name: Mapped[str | None] = mapped_column(String(100))
    is_active_branch: Mapped[bool] = mapped_column(Boolean, default=True)

    # 元数据（包含引用、来源等）
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    attachments: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)

    # 关系
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )
    parent_message: Mapped[Optional["Message"]] = relationship(
        "Message", remote_side=[id], back_populates="child_messages"
    )
    child_messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="parent_message"
    )

    # 索引
    __table_args__ = (
        Index("idx_message_conversation", "conversation_id"),
        Index("idx_message_created", "created_at"),
        Index("idx_message_parent", "parent_message_id"),
        Index("idx_message_branch", "branch_name"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}')>"


class Agent(Base, TimestampMixin):
    """AI代理表."""

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id")
    )  # None表示系统内置代理

    # 代理信息
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    # 代理配置
    agent_type: Mapped[str] = mapped_column(
        String(50)
    )  # research, analysis, wiki, custom
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    prompt_template: Mapped[str] = mapped_column(Text)

    # 能力设置
    capabilities: Mapped[list[str]] = mapped_column(
        JSON
    )  # search, analysis, generation等
    tools: Mapped[list[str] | None] = mapped_column(JSON)

    # 发布状态
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 统计信息
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)

    # 关系
    creator: Mapped[Optional["User"]] = relationship("User")
    executions: Mapped[list["AgentExecution"]] = relationship(
        "AgentExecution", back_populates="agent"
    )

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}')>"


class AgentExecution(Base, TimestampMixin):
    """代理执行记录表."""

    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"))

    # 执行信息
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20), default="running"
    )  # running, completed, failed
    error_message: Mapped[str | None] = mapped_column(Text)

    # 执行统计
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration: Mapped[float | None] = mapped_column(Float)  # 秒
    token_usage: Mapped[int | None] = mapped_column(Integer)

    # 关系
    agent: Mapped["Agent"] = relationship("Agent", back_populates="executions")
    user: Mapped["User"] = relationship("User")
    conversation: Mapped[Optional["Conversation"]] = relationship("Conversation")


class UsageLog(Base, TimestampMixin):
    """使用日志表."""

    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 使用信息
    action: Mapped[str] = mapped_column(String(50))  # chat, search, upload, etc.
    resource_type: Mapped[str] = mapped_column(
        String(50)
    )  # conversation, document, space
    resource_id: Mapped[int | None] = mapped_column(Integer)

    # 详细信息
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # AI使用统计
    model: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(50))
    token_count: Mapped[int | None] = mapped_column(Integer)
    cost: Mapped[float | None] = mapped_column(Float)  # 美元

    # 关系
    user: Mapped["User"] = relationship("User")

    # 索引
    __table_args__ = (
        Index("idx_usage_user_date", "user_id", "created_at"),
        Index("idx_usage_action", "action"),
    )


class Citation(Base, TimestampMixin):
    """引用表（BibTeX管理）."""

    __tablename__ = "citations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"))
    space_id: Mapped[int] = mapped_column(ForeignKey("spaces.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # BibTeX基本信息
    citation_type: Mapped[str] = mapped_column(String(50))  # article, book, etc.
    bibtex_key: Mapped[str] = mapped_column(String(200), unique=True)
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[list[str]] = mapped_column(JSON)  # 作者列表
    year: Mapped[int | None] = mapped_column(Integer)

    # 期刊/会议信息
    journal: Mapped[str | None] = mapped_column(String(500))
    volume: Mapped[str | None] = mapped_column(String(50))
    number: Mapped[str | None] = mapped_column(String(50))
    pages: Mapped[str | None] = mapped_column(String(100))
    publisher: Mapped[str | None] = mapped_column(String(500))
    booktitle: Mapped[str | None] = mapped_column(String(500))  # 会议论文集

    # 标识符
    doi: Mapped[str | None] = mapped_column(String(200))
    isbn: Mapped[str | None] = mapped_column(String(50))
    url: Mapped[str | None] = mapped_column(String(1000))

    # 内容
    abstract: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[str] | None] = mapped_column(JSON)

    # 原始BibTeX
    bibtex_raw: Mapped[str | None] = mapped_column(Text)

    # 元数据
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # 关系
    document: Mapped[Optional["Document"]] = relationship("Document")
    space: Mapped["Space"] = relationship("Space")
    user: Mapped["User"] = relationship("User")

    # 索引
    __table_args__ = (
        Index("idx_citation_space", "space_id"),
        Index("idx_citation_user", "user_id"),
        Index("idx_citation_type", "citation_type"),
        Index("idx_citation_year", "year"),
        Index("idx_citation_bibtex_key", "bibtex_key"),
    )

    def __repr__(self):
        return f"<Citation(id={self.id}, key={self.bibtex_key}, title='{self.title[:50] if self.title else ''}...')>"


class NoteVersion(Base, TimestampMixin):
    """笔记版本历史表."""

    __tablename__ = "note_versions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 版本信息
    version_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    content_html: Mapped[str | None] = mapped_column(Text)

    # 变更信息
    change_summary: Mapped[str | None] = mapped_column(String(500))
    change_type: Mapped[str] = mapped_column(String(50))  # edit, ai_generate, restore

    # AI生成相关（如果是AI生成的版本）
    ai_model: Mapped[str | None] = mapped_column(String(100))
    ai_prompt: Mapped[str | None] = mapped_column(Text)

    # 元数据
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # 关系
    note: Mapped["Note"] = relationship("Note", back_populates="versions")
    user: Mapped["User"] = relationship("User")

    # 索引
    __table_args__ = (
        Index("idx_note_version_note", "note_id"),
        Index("idx_note_version_created", "created_at"),
        UniqueConstraint("note_id", "version_number", name="uq_note_version"),
    )

    def __repr__(self):
        return f"<NoteVersion(id={self.id}, note_id={self.note_id}, version={self.version_number})>"


class UserCustomModel(Base):
    """用户自定义模型配置."""

    __tablename__ = "user_custom_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(
        String, nullable=False
    )  # custom, ollama, openai, anthropic
    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    api_key: Mapped[str | None] = mapped_column(String)  # 应该加密存储
    model_id: Mapped[str] = mapped_column(String, nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(
        JSON, default=list
    )  # ["chat", "vision", "embedding"]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )  # 额外配置信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="custom_models")

    # 索引
    __table_args__ = (
        Index("idx_user_custom_model_user", "user_id"),
        UniqueConstraint("user_id", "name", name="uq_user_custom_model_name"),
    )

    def __repr__(self):
        return f"<UserCustomModel(id={self.id}, name={self.name}, provider={self.provider})>"
