"""Unit tests for Ollama endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.ollama import (
    delete_model,
    get_model_info,
    get_ollama_status,
    get_recommended_models,
    list_ollama_models,
    pull_model,
)
from app.models.models import User
from app.schemas.ollama import (
    OllamaModelInfo,
    OllamaModelListResponse,
    OllamaModelResponse,
    OllamaPullRequest,
    OllamaPullResponse,
)


@pytest.fixture
def mock_user() -> User:
    """Create mock user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def mock_admin_user() -> User:
    """Create mock admin user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "admin"
    user.email = "admin@example.com"
    user.is_active = True
    # Note: is_superuser doesn't exist in User model yet, but code expects it
    return user


@pytest.fixture
def mock_model_response() -> OllamaModelResponse:
    """Create mock Ollama model response."""
    return OllamaModelResponse(
        name="llama2:7b",
        size=3825819648,  # ~3.8GB
        digest="78e26419b4469263f75331927a00a0284ef6544c1975b826b15abdaef17bb962",
        modified_at="2024-01-15T10:30:00Z",
    )


class TestListOllamaModels:
    """Test list Ollama models endpoint."""

    @pytest.mark.asyncio
    async def test_list_models_success(
        self,
        mock_user: User,
        mock_model_response: OllamaModelResponse,
    ) -> None:
        """Test successful listing of Ollama models."""
        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.list_models = AsyncMock(return_value=[mock_model_response])

            result = await list_ollama_models(current_user=mock_user)

            assert isinstance(result, OllamaModelListResponse)
            assert result.total == 1
            assert result.is_available is True
            assert result.error is None
            assert len(result.models) == 1
            assert result.models[0].name == "llama2:7b"

    @pytest.mark.asyncio
    async def test_list_models_service_unavailable(
        self,
        mock_user: User,
    ) -> None:
        """Test listing models when Ollama service is unavailable."""
        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.list_models = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            result = await list_ollama_models(current_user=mock_user)

            assert isinstance(result, OllamaModelListResponse)
            assert result.total == 0
            assert result.is_available is False
            assert result.error == "Connection refused"
            assert len(result.models) == 0

    @pytest.mark.asyncio
    async def test_list_models_empty(
        self,
        mock_user: User,
    ) -> None:
        """Test listing models when no models are installed."""
        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.list_models = AsyncMock(return_value=[])

            result = await list_ollama_models(current_user=mock_user)

            assert isinstance(result, OllamaModelListResponse)
            assert result.total == 0
            assert result.is_available is True
            assert result.error is None
            assert len(result.models) == 0


class TestGetModelInfo:
    """Test get model info endpoint."""

    @pytest.mark.asyncio
    async def test_get_model_info_success(
        self,
        mock_user: User,
    ) -> None:
        """Test successful retrieval of model info."""
        mock_info = OllamaModelInfo(
            name="llama2:7b",
            model_format="gguf",
            family="llama",
            parameter_size="7B",
            quantization_level="Q4_0",
            size=3825819648,
            digest="78e26419b4469263f75331927a00a0284ef6544c1975b826b15abdaef17bb962",
            details={"license": "MIT"},
        )

        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.get_model_info = AsyncMock(return_value=mock_info)

            result = await get_model_info(
                model_name="llama2:7b", current_user=mock_user
            )

            assert isinstance(result, OllamaModelInfo)
            assert result.name == "llama2:7b"
            assert result.parameter_size == "7B"
            assert result.size_human == "3.6 GB"

    @pytest.mark.asyncio
    async def test_get_model_info_not_found(
        self,
        mock_user: User,
    ) -> None:
        """Test get info for non-existent model."""
        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.get_model_info = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_model_info(
                    model_name="nonexistent:model", current_user=mock_user
                )

            assert exc_info.value.status_code == 404
            assert "模型 nonexistent:model 不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_model_info_service_error(
        self,
        mock_user: User,
    ) -> None:
        """Test get model info with service error."""
        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.get_model_info = AsyncMock(
                side_effect=Exception("Service error")
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_model_info(model_name="llama2:7b", current_user=mock_user)

            assert exc_info.value.status_code == 500
            assert "获取模型信息失败: Service error" in str(exc_info.value.detail)


class TestPullModel:
    """Test pull model endpoint."""

    @pytest.mark.asyncio
    async def test_pull_model_success(
        self,
        mock_admin_user: User,
    ) -> None:
        """Test successful model pull by admin."""
        request = OllamaPullRequest(
            model_name="mistral:7b",
            insecure=False,
        )

        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.pull_model = AsyncMock(return_value="task-123")

            result = await pull_model(request=request, current_user=mock_admin_user)

            assert isinstance(result, OllamaPullResponse)
            assert result.task_id == "task-123"
            assert result.status == "pulling"
            assert result.model_name == "mistral:7b"
            assert result.progress == 0
            assert result.message and "开始拉取模型 mistral:7b" in result.message

    @pytest.mark.asyncio
    async def test_pull_model_non_admin(
        self,
        mock_user: User,
    ) -> None:
        """Test pull model by non-admin user."""
        # Since is_superuser doesn't exist, code checks is_active
        mock_user.is_active = False  # Simulate non-admin
        request = OllamaPullRequest(model_name="mistral:7b", insecure=False)

        with pytest.raises(HTTPException) as exc_info:
            await pull_model(request=request, current_user=mock_user)

        assert exc_info.value.status_code == 403
        assert "只有管理员可以拉取新模型" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_pull_model_service_error(
        self,
        mock_admin_user: User,
    ) -> None:
        """Test pull model with service error."""
        request = OllamaPullRequest(model_name="mistral:7b", insecure=False)

        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.pull_model = AsyncMock(side_effect=Exception("Network error"))

            with pytest.raises(HTTPException) as exc_info:
                await pull_model(request=request, current_user=mock_admin_user)

            assert exc_info.value.status_code == 500
            assert "拉取模型失败: Network error" in str(exc_info.value.detail)


class TestDeleteModel:
    """Test delete model endpoint."""

    @pytest.mark.asyncio
    async def test_delete_model_success(
        self,
        mock_admin_user: User,
    ) -> None:
        """Test successful model deletion by admin."""
        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.delete_model = AsyncMock(return_value=True)

            result = await delete_model(
                model_name="old-model:v1", current_user=mock_admin_user
            )

            assert result == {"message": "模型 old-model:v1 已删除"}

    @pytest.mark.asyncio
    async def test_delete_model_non_admin(
        self,
        mock_user: User,
    ) -> None:
        """Test delete model by non-admin user."""
        mock_user.is_active = False  # Simulate non-admin

        with pytest.raises(HTTPException) as exc_info:
            await delete_model(model_name="llama2:7b", current_user=mock_user)

        assert exc_info.value.status_code == 403
        assert "只有管理员可以删除模型" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_model_failed(
        self,
        mock_admin_user: User,
    ) -> None:
        """Test failed model deletion."""
        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.delete_model = AsyncMock(return_value=False)

            with pytest.raises(HTTPException) as exc_info:
                await delete_model(
                    model_name="nonexistent:model", current_user=mock_admin_user
                )

            assert exc_info.value.status_code == 400
            assert "删除模型 nonexistent:model 失败" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_model_service_error(
        self,
        mock_admin_user: User,
    ) -> None:
        """Test delete model with service error."""
        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.delete_model = AsyncMock(
                side_effect=Exception("Permission denied")
            )

            with pytest.raises(HTTPException) as exc_info:
                await delete_model(model_name="llama2:7b", current_user=mock_admin_user)

            assert exc_info.value.status_code == 500
            assert "删除模型失败: Permission denied" in str(exc_info.value.detail)


class TestGetOllamaStatus:
    """Test get Ollama status endpoint."""

    @pytest.mark.asyncio
    async def test_get_status_success(
        self,
        mock_user: User,
    ) -> None:
        """Test successful status retrieval."""
        mock_status = {
            "available": True,
            "version": "0.1.24",
            "models_count": 3,
            "total_size": 11477658624,  # ~11GB
            "gpu_available": True,
            "gpu_info": {"name": "NVIDIA RTX 3090", "memory": "24GB"},
        }

        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.check_status = AsyncMock(return_value=mock_status)

            result = await get_ollama_status(current_user=mock_user)

            assert result["available"] is True
            assert result["version"] == "0.1.24"
            assert result["models_count"] == 3
            assert result["gpu_available"] is True

    @pytest.mark.asyncio
    async def test_get_status_unavailable(
        self,
        mock_user: User,
    ) -> None:
        """Test status when Ollama is unavailable."""
        mock_status = {
            "available": False,
            "version": None,
            "models_count": 0,
            "total_size": 0,
            "gpu_available": False,
            "gpu_info": None,
        }

        with patch("app.api.v1.endpoints.ollama.ollama_service") as mock_service:
            mock_service.check_status = AsyncMock(return_value=mock_status)

            result = await get_ollama_status(current_user=mock_user)

            assert result["available"] is False
            assert result["version"] is None
            assert result["models_count"] == 0


class TestGetRecommendedModels:
    """Test get recommended models endpoint."""

    @pytest.mark.asyncio
    async def test_get_recommended_models(
        self,
        mock_user: User,
    ) -> None:
        """Test get recommended models list."""
        result = await get_recommended_models(current_user=mock_user)

        assert isinstance(result, list)
        assert len(result) == 6  # Based on hardcoded list

        # Check first model
        first_model = result[0]
        assert first_model["name"] == "llama2:7b"
        assert "description" in first_model
        assert "size" in first_model
        assert "capabilities" in first_model
        assert "chat" in first_model["capabilities"]

        # Check for variety of models
        model_names = [m["name"] for m in result]
        assert "deepseek-coder:6.7b" in model_names  # Code model
        assert "nomic-embed-text" in model_names  # Embedding model
        assert "qwen:7b" in model_names  # Chinese model

        # Check capabilities
        code_model = next(m for m in result if m["name"] == "deepseek-coder:6.7b")
        assert "code" in code_model["capabilities"]

        embedding_model = next(m for m in result if m["name"] == "nomic-embed-text")
        assert "embedding" in embedding_model["capabilities"]

        chinese_model = next(m for m in result if m["name"] == "qwen:7b")
        assert "chinese" in chinese_model["capabilities"]

