"""Application configuration settings."""

from typing import Any

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # 基础配置
    APP_NAME: str = "Second Brain"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False  # 是否启用调试模式

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True  # 是否自动重载（开发时设为True）

    # 安全配置
    SECRET_KEY: str = Field(..., description="Secret key for JWT token signing")
    ALGORITHM: str = "HS256"  # 加密算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 访问令牌过期时间（分钟）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 刷新令牌过期时间（天）

    # 数据库配置
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    DATABASE_ECHO: bool = False  # 是否打印SQL语句（调试用）

    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )
    REDIS_EXPIRE_TIME: int = 3600  # 1小时

    # 对象存储配置
    MINIO_ENDPOINT: str = Field(
        default="localhost:9000", description="MinIO server endpoint"
    )
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", description="MinIO secret key")
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "secondbrain"

    # 向量数据库配置
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None

    # API限流配置
    RATE_LIMIT_FREE_USER: int = 20  # 免费用户每日限制
    RATE_LIMIT_PREMIUM_USER: int = 200  # 付费用户每日限制
    RATE_LIMIT_BURST: int = 10  # 突发请求限制

    # AI服务配置 - OpenRouter（推荐）
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_SITE_URL: str | None = None  # 您的应用 URL
    OPENROUTER_APP_NAME: str = "SecondBrain"  # 您的应用名称
    
    # AI服务配置 - 传统提供商（保留以便兼容）
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None

    ANTHROPIC_API_KEY: str | None = None

    GOOGLE_API_KEY: str | None = None

    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    PERPLEXITY_API_KEY: str | None = None
    PERPLEXITY_BASE_URL: str = "https://api.perplexity.ai"

    # Ollama配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_ENABLED: bool = True

    # 默认AI模型配置
    DEFAULT_CHAT_MODEL: str = "openrouter/auto"
    DEFAULT_SEARCH_MODEL: str = "perplexity/sonar"
    DEFAULT_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"

    # 文件上传配置
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_FILE_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/markdown",
        "text/csv",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    # CORS配置
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    ALLOWED_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    ALLOWED_HEADERS: list[str] = ["*"]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str | None = None

    # 监控配置
    ENABLE_METRICS: bool = False

    # WebSocket配置
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    WEBSOCKET_TIMEOUT: int = 300

    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: str | None) -> Any:
        if isinstance(v, str):
            return v
        raise ValueError("DATABASE_URL must be provided")

    @property
    def cors_origins(self) -> list[str]:
        """将 ALLOWED_ORIGINS 字符串转换为列表"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [i.strip() for i in self.ALLOWED_ORIGINS.split(",")]
        return []

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow",  # 允许额外的环境变量
    )


# 全局设置实例
settings = Settings()


# 数据库配置
DATABASE_CONFIG = {
    "echo": settings.DATABASE_ECHO,
    "pool_size": 20,
    "max_overflow": 40,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

# Redis配置
REDIS_CONFIG = {
    "decode_responses": True,
    "retry_on_timeout": True,
    "socket_keepalive": True,
    "socket_keepalive_options": {},
}

# AI模型配置映射（已弃用 - 现在使用 OpenRouter 统一管理）
# 保留此配置仅用于向后兼容
AI_MODEL_CONFIGS = {
    "openai": {
        "api_key": settings.OPENAI_API_KEY,
        "base_url": settings.OPENAI_BASE_URL,
        "models": {
            "chat": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "embedding": [
                "text-embedding-3-large",
                "text-embedding-3-small",
                "text-embedding-ada-002",
            ],
        },
    },
    "anthropic": {
        "api_key": settings.ANTHROPIC_API_KEY,
        "models": {
            "chat": [
                "claude-3-5-sonnet-20241022",
                "claude-3-haiku-20240307",
                "claude-3-opus-20240229",
            ]
        },
    },
    "google": {
        "api_key": settings.GOOGLE_API_KEY,
        "models": {
            "chat": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
        },
    },
    "deepseek": {
        "api_key": settings.DEEPSEEK_API_KEY,
        "base_url": settings.DEEPSEEK_BASE_URL,
        "models": {
            "chat": ["deepseek-chat", "deepseek-reasoner"],
            "reasoning": ["deepseek-reasoner"],
        },
    },
    "ollama": {
        "base_url": settings.OLLAMA_BASE_URL,
        "models": {
            "chat": ["llama2:7b", "mistral:7b", "qwen:7b", "gemma:2b"],
            "embedding": ["nomic-embed-text"],
            "code": ["deepseek-coder:6.7b"],
        },
    },
}
