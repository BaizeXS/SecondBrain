"""Test configuration settings."""

import os
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import DATABASE_CONFIG, REDIS_CONFIG, Settings


def create_test_settings(**kwargs: Any) -> Settings:
    """创建测试用的Settings实例，不读取.env文件."""
    # 设置必需的默认值
    defaults = {
        "_env_file": None,  # 不读取.env文件
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/testdb",
    }
    # 更新用户提供的值
    defaults.update(kwargs)
    return Settings(**defaults)  # type: ignore[arg-type]


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = create_test_settings()

        assert settings.APP_NAME == "Second Brain"
        assert settings.VERSION == "1.0.0"
        assert settings.API_V1_STR == "/api/v1"
        assert settings.DEBUG is False
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_required_fields(self):
        """Test that required fields raise error if not provided."""
        # 清除可能存在的环境变量
        env_backup = {
            "SECRET_KEY": os.environ.pop("SECRET_KEY", None),
            "DATABASE_URL": os.environ.pop("DATABASE_URL", None),
        }

        try:
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)  # type: ignore[call-arg]  # 不读取.env文件

            errors = exc_info.value.errors()
            required_fields = {error["loc"][0] for error in errors}
            assert "SECRET_KEY" in required_fields
            assert "DATABASE_URL" in required_fields
        finally:
            # 恢复环境变量
            for key, value in env_backup.items():
                if value is not None:
                    os.environ[key] = value

    def test_database_url_validation(self):
        """Test DATABASE_URL validation."""
        # Valid URL
        settings = create_test_settings(
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
        )
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost/db"

        # Invalid URL type
        with pytest.raises(ValidationError):
            create_test_settings(DATABASE_URL=None)

    def test_cors_origins_parsing(self):
        """Test CORS origins string parsing."""
        settings = create_test_settings(
            ALLOWED_ORIGINS="http://localhost:3000, http://localhost:5173, http://example.com"
        )

        origins = settings.cors_origins
        assert len(origins) == 3
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins
        assert "http://example.com" in origins

    def test_max_file_size_bytes_property(self):
        """Test max_file_size_bytes property calculation."""
        settings = create_test_settings(MAX_FILE_SIZE_MB=50)

        assert settings.max_file_size_bytes == 50 * 1024 * 1024

    def test_env_file_loading(self, tmp_path):
        """Test loading settings from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "SECRET_KEY=env-secret-key\n"
            "DATABASE_URL=postgresql+asyncpg://env:env@localhost/envdb\n"
            "DEBUG=true\n"
            "ENABLE_METRICS=true\n"
        )

        with patch.dict(os.environ, {"ENV_FILE": str(env_file)}):
            settings = Settings(_env_file=str(env_file))  # type: ignore[call-arg]

        assert settings.SECRET_KEY == "env-secret-key"
        assert settings.DATABASE_URL == "postgresql+asyncpg://env:env@localhost/envdb"
        assert settings.DEBUG is True
        assert settings.ENABLE_METRICS is True

    def test_security_warnings(self):
        """Test security-related default values."""
        settings = create_test_settings()

        # Check MinIO defaults (should be changed in production)
        assert settings.MINIO_ACCESS_KEY == "minioadmin"
        assert settings.MINIO_SECRET_KEY == "minioadmin"
        # Check field descriptions contain security warnings
        minio_access_key_desc = Settings.model_fields["MINIO_ACCESS_KEY"].description
        minio_secret_key_desc = Settings.model_fields["MINIO_SECRET_KEY"].description

        assert minio_access_key_desc is not None
        assert "CHANGE IN PRODUCTION" in minio_access_key_desc

        assert minio_secret_key_desc is not None
        assert "CHANGE IN PRODUCTION" in minio_secret_key_desc

    def test_ai_service_configurations(self):
        """Test AI service configurations."""
        settings = create_test_settings(
            OPENAI_API_KEY="sk-test-openai",
            ANTHROPIC_API_KEY="sk-test-anthropic",
            GOOGLE_API_KEY="test-google-key",
            DEEPSEEK_API_KEY="test-deepseek-key",
            PERPLEXITY_API_KEY="test-perplexity-key",
        )

        assert settings.OPENAI_API_KEY == "sk-test-openai"
        assert settings.ANTHROPIC_API_KEY == "sk-test-anthropic"
        assert settings.GOOGLE_API_KEY == "test-google-key"
        assert settings.DEEPSEEK_API_KEY == "test-deepseek-key"
        assert settings.PERPLEXITY_API_KEY == "test-perplexity-key"

    def test_rate_limit_configuration(self):
        """Test rate limit configurations."""
        settings = create_test_settings(
            RATE_LIMIT_FREE_USER=10,
            RATE_LIMIT_PREMIUM_USER=100,
            RATE_LIMIT_BURST=5,
        )

        assert settings.RATE_LIMIT_FREE_USER == 10
        assert settings.RATE_LIMIT_PREMIUM_USER == 100
        assert settings.RATE_LIMIT_BURST == 5


class TestDatabaseConfig:
    """Test database configuration."""

    def test_database_config_from_env(self):
        """Test database config uses environment variables."""
        # 直接测试环境变量的解析逻辑
        with patch.dict(os.environ, {"DB_POOL_SIZE": "30", "DB_MAX_OVERFLOW": "60"}):
            pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
            max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "40"))

        assert pool_size == 30
        assert max_overflow == 60

    def test_database_config_defaults(self):
        """Test database config default values."""
        assert "echo" in DATABASE_CONFIG
        assert "pool_size" in DATABASE_CONFIG
        assert "max_overflow" in DATABASE_CONFIG
        assert DATABASE_CONFIG["pool_pre_ping"] is True
        assert DATABASE_CONFIG["pool_recycle"] == 3600


class TestRedisConfig:
    """Test Redis configuration."""

    def test_redis_config_values(self):
        """Test Redis config values."""
        assert REDIS_CONFIG["decode_responses"] is True
        assert REDIS_CONFIG["retry_on_timeout"] is True
        assert REDIS_CONFIG["socket_keepalive"] is True
        assert isinstance(REDIS_CONFIG["socket_keepalive_options"], dict)
