"""Unit tests for Ollama Service."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.schemas.ollama import (
    OllamaModelInfo,
    OllamaModelResponse,
)
from app.services.ollama_service import OllamaService


@pytest.fixture
def ollama_service():
    """创建Ollama服务实例."""
    return OllamaService()


@pytest.fixture
def mock_models_response():
    """模拟模型列表响应."""
    return {
        "models": [
            {
                "name": "llama2:7b",
                "size": 3825819519,
                "digest": "fe938a131f40e6f6d40083c9f0f430a515233eb2edaa6d72eb85c50d64f2300e",
                "modified_at": "2023-11-04T14:56:49.277302595-07:00",
            },
            {
                "name": "llama2:13b",
                "size": 7323310500,
                "digest": "d475bf4c50bc5d3d89f8d2db13f13ad2ccf52b4ab8b939e79e2e46afb20467f6",
                "modified_at": "2023-11-05T10:30:00.123456789-07:00",
            },
        ]
    }


@pytest.fixture
def mock_model_info():
    """模拟模型详细信息."""
    return {
        "license": "Apache 2.0",
        "modelfile": "...",
        "parameters": "...",
        "template": "...",
        "size": 3825819519,
        "digest": "fe938a131f40e6f6d40083c9f0f430a515233eb2edaa6d72eb85c50d64f2300e",
        "details": {
            "format": "gguf",
            "family": "llama",
            "parameter_size": "7B",
            "quantization_level": "Q4_0",
        },
    }


class TestCheckStatus:
    """测试检查状态功能."""

    @pytest.mark.asyncio
    async def test_check_status_success(self, ollama_service, mock_models_response):
        """测试成功检查状态."""
        with patch("httpx.AsyncClient") as MockClient:
            # 设置模拟响应
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟tags响应
            mock_tags_response = Mock()
            mock_tags_response.status_code = 200
            mock_tags_response.json.return_value = mock_models_response
            mock_client.get.side_effect = [mock_tags_response]

            # 执行
            result = await ollama_service.check_status()

            # 验证
            assert result["available"] is True
            assert result["models_count"] == 2
            assert result["total_size"] == 3825819519 + 7323310500
            assert result["gpu_available"] is False

    @pytest.mark.asyncio
    async def test_check_status_with_version(
        self, ollama_service, mock_models_response
    ):
        """测试带版本信息的状态检查."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟tags响应
            mock_tags_response = Mock()
            mock_tags_response.status_code = 200
            mock_tags_response.json.return_value = mock_models_response

            # 模拟version响应
            mock_version_response = Mock()
            mock_version_response.status_code = 200
            mock_version_response.json.return_value = {"version": "0.1.15"}

            mock_client.get.side_effect = [mock_tags_response, mock_version_response]

            # 执行
            result = await ollama_service.check_status()

            # 验证
            assert result["available"] is True
            assert result["version"] == "0.1.15"

    @pytest.mark.asyncio
    async def test_check_status_service_unavailable(self, ollama_service):
        """测试服务不可用的情况."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟失败响应
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.get.return_value = mock_response

            # 执行
            result = await ollama_service.check_status()

            # 验证
            assert result["available"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_check_status_exception(self, ollama_service):
        """测试异常情况."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Connection error")

            # 执行
            result = await ollama_service.check_status()

            # 验证
            assert result["available"] is False
            assert result["error"] == "Connection error"


class TestListModels:
    """测试列出模型功能."""

    @pytest.mark.asyncio
    async def test_list_models_success(self, ollama_service, mock_models_response):
        """测试成功列出模型."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_models_response
            mock_client.get.return_value = mock_response

            # 执行
            models = await ollama_service.list_models()

            # 验证
            assert len(models) == 2
            assert isinstance(models[0], OllamaModelResponse)
            assert models[0].name == "llama2:7b"
            assert models[0].size == 3825819519
            assert models[1].name == "llama2:13b"

    @pytest.mark.asyncio
    async def test_list_models_empty(self, ollama_service):
        """测试空模型列表."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟空响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_client.get.return_value = mock_response

            # 执行
            models = await ollama_service.list_models()

            # 验证
            assert models == []

    @pytest.mark.asyncio
    async def test_list_models_error(self, ollama_service):
        """测试列出模型时的错误."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("API Error")

            # 执行
            models = await ollama_service.list_models()

            # 验证
            assert models == []


class TestGetModelInfo:
    """测试获取模型信息功能."""

    @pytest.mark.asyncio
    async def test_get_model_info_success(self, ollama_service, mock_model_info):
        """测试成功获取模型信息."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_model_info
            mock_client.post.return_value = mock_response

            # 执行
            info = await ollama_service.get_model_info("llama2:7b")

            # 验证
            assert isinstance(info, OllamaModelInfo)
            assert info.name == "llama2:7b"
            assert info.model_format == "gguf"
            assert info.family == "llama"
            assert info.parameter_size == "7B"
            assert info.size == 3825819519

    @pytest.mark.asyncio
    async def test_get_model_info_not_found(self, ollama_service):
        """测试模型不存在的情况."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟404响应
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.post.return_value = mock_response

            # 执行
            info = await ollama_service.get_model_info("nonexistent:model")

            # 验证
            assert info is None

    @pytest.mark.asyncio
    async def test_get_model_info_error(self, ollama_service):
        """测试获取模型信息时的错误."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Network error")

            # 执行
            info = await ollama_service.get_model_info("llama2:7b")

            # 验证
            assert info is None


class TestPullModel:
    """测试拉取模型功能."""

    @pytest.mark.asyncio
    async def test_pull_model_success(self, ollama_service):
        """测试成功拉取模型."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response

            # 执行
            task_id = await ollama_service.pull_model("llama2:7b")

            # 验证
            assert isinstance(task_id, str)
            assert len(task_id) > 0
            mock_client.post.assert_called_once_with(
                f"{ollama_service.base_url}/api/pull",
                json={"name": "llama2:7b", "insecure": False},
                timeout=None,
            )

    @pytest.mark.asyncio
    async def test_pull_model_with_insecure(self, ollama_service):
        """测试不安全模式拉取模型."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response

            # 执行
            task_id = await ollama_service.pull_model("llama2:7b", insecure=True)

            # 验证
            assert isinstance(task_id, str)
            mock_client.post.assert_called_once_with(
                f"{ollama_service.base_url}/api/pull",
                json={"name": "llama2:7b", "insecure": True},
                timeout=None,
            )

    @pytest.mark.asyncio
    async def test_pull_model_error(self, ollama_service):
        """测试拉取模型时的错误."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟失败响应
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid model name"
            mock_client.post.return_value = mock_response

            # 执行并验证异常
            with pytest.raises(Exception) as exc_info:
                await ollama_service.pull_model("invalid:model")

            assert "Failed to pull model" in str(exc_info.value)


class TestDeleteModel:
    """测试删除模型功能."""

    @pytest.mark.asyncio
    async def test_delete_model_success(self, ollama_service):
        """测试成功删除模型."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.request.return_value = mock_response

            # 执行
            result = await ollama_service.delete_model("llama2:7b")

            # 验证
            assert result is True
            mock_client.request.assert_called_once_with(
                "DELETE",
                f"{ollama_service.base_url}/api/delete",
                json={"name": "llama2:7b"},
            )

    @pytest.mark.asyncio
    async def test_delete_model_not_found(self, ollama_service):
        """测试删除不存在的模型."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟404响应
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.request.return_value = mock_response

            # 执行
            result = await ollama_service.delete_model("nonexistent:model")

            # 验证
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_model_error(self, ollama_service):
        """测试删除模型时的错误."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Connection error")

            # 执行
            result = await ollama_service.delete_model("llama2:7b")

            # 验证
            assert result is False


class TestGenerateEmbedding:
    """测试生成嵌入功能."""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, ollama_service):
        """测试成功生成嵌入."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
            }
            mock_client.post.return_value = mock_response

            # 执行
            embedding = await ollama_service.generate_embedding(
                "llama2:7b", "Hello world"
            )

            # 验证
            assert isinstance(embedding, list)
            assert len(embedding) == 5
            assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]

    @pytest.mark.asyncio
    async def test_generate_embedding_empty(self, ollama_service):
        """测试生成空嵌入."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embedding": []}
            mock_client.post.return_value = mock_response

            # 执行
            embedding = await ollama_service.generate_embedding("llama2:7b", "")

            # 验证
            assert embedding == []

    @pytest.mark.asyncio
    async def test_generate_embedding_error(self, ollama_service):
        """测试生成嵌入时的错误."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟失败响应
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_client.post.return_value = mock_response

            # 执行并验证异常
            with pytest.raises(Exception) as exc_info:
                await ollama_service.generate_embedding("llama2:7b", "Hello")

            assert "Failed to generate embedding" in str(exc_info.value)


class TestChatCompletion:
    """测试聊天补全功能."""

    @pytest.mark.asyncio
    async def test_chat_completion_non_stream(self, ollama_service):
        """测试非流式聊天补全."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "model": "llama2:7b",
                "created_at": "2023-08-04T08:52:19.385406455-07:00",
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you today?",
                },
                "done": True,
            }
            mock_client.post.return_value = mock_response

            # 执行
            messages = [{"role": "user", "content": "Hello"}]
            async for response in ollama_service.chat_completion(
                "llama2:7b", messages, stream=False
            ):
                # 验证
                assert isinstance(response, dict)
                assert response["model"] == "llama2:7b"
                assert response["done"] is True
                assert response["message"]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_chat_completion_stream(self, ollama_service):
        """测试流式聊天补全."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟流式响应
            mock_response = Mock()
            mock_response.status_code = 200

            # 模拟流式数据
            async def mock_aiter_lines():
                yield json.dumps(
                    {"message": {"content": "Hello"}, "done": False}
                )
                yield json.dumps(
                    {"message": {"content": " world!"}, "done": True}
                )

            mock_response.aiter_lines = mock_aiter_lines
            mock_client.post.return_value = mock_response

            # 执行
            messages = [{"role": "user", "content": "Hello"}]
            responses = []
            async for response in ollama_service.chat_completion(
                "llama2:7b", messages, stream=True
            ):
                responses.append(response)

            # 验证
            assert len(responses) == 2
            assert responses[0]["done"] is False
            assert responses[1]["done"] is True

    @pytest.mark.asyncio
    async def test_chat_completion_with_options(self, ollama_service):
        """测试带选项的聊天补全."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"done": True}
            mock_client.post.return_value = mock_response

            # 执行
            messages = [{"role": "user", "content": "Hello"}]
            async for _ in ollama_service.chat_completion(
                "llama2:7b",
                messages,
                stream=False,
                temperature=0.8,
                max_tokens=100,
            ):
                pass

            # 验证调用参数
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            json_data = call_args.kwargs["json"]
            assert json_data["temperature"] == 0.8
            assert json_data["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_chat_completion_error(self, ollama_service):
        """测试聊天补全时的错误."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟失败响应
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad request"
            mock_client.post.return_value = mock_response

            # 执行并验证异常
            messages = [{"role": "user", "content": "Hello"}]
            with pytest.raises(Exception) as exc_info:
                async for _ in ollama_service.chat_completion(
                    "llama2:7b", messages
                ):
                    pass

            assert "Chat completion failed" in str(exc_info.value)


class TestHelperMethods:
    """测试辅助方法."""

    def test_check_gpu_support(self, ollama_service):
        """测试GPU支持检查."""
        # 当前实现总是返回False
        result = ollama_service._check_gpu_support()
        assert result is False


class TestOllamaModelResponse:
    """测试OllamaModelResponse模式."""

    def test_size_human_property(self):
        """测试人类可读的文件大小属性."""
        # 测试各种大小
        model = OllamaModelResponse(
            name="test",
            size=512,
            digest="abc123",
            modified_at="2023-01-01",
        )
        assert model.size_human == "512.0 B"

        model.size = 1024
        assert model.size_human == "1.0 KB"

        model.size = 1024 * 1024
        assert model.size_human == "1.0 MB"

        model.size = 1024 * 1024 * 1024
        assert model.size_human == "1.0 GB"

        model.size = 1024 * 1024 * 1024 * 1024
        assert model.size_human == "1.0 TB"

        model.size = 1024 * 1024 * 1024 * 1024 * 1024
        assert model.size_human == "1.0 PB"


class TestOllamaModelInfo:
    """测试OllamaModelInfo模式."""

    def test_size_human_property(self):
        """测试人类可读的文件大小属性."""
        info = OllamaModelInfo(
            name="test",
            model_format="gguf",
            family="llama",
            parameter_size="7B",
            quantization_level="Q4_0",
            size=3825819519,
            digest="abc123",
        )
        assert info.size_human == "3.6 GB"
