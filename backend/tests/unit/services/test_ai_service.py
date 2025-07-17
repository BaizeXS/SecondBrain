"""Updated unit tests for AI service with multimodal support."""

import base64
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.models import User
from app.services.ai_service import AIService, ChatMode


class TestAIServiceBasics:
    """基础功能测试."""

    @pytest.fixture
    def ai_service(self):
        """创建测试用的 AI Service."""
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test_key"
            mock_settings.OPENROUTER_SITE_URL = "http://test.com"
            mock_settings.OPENROUTER_APP_NAME = "TestApp"
            mock_settings.OLLAMA_ENABLED = False

            with patch("app.services.ai_service.AsyncOpenAI"):
                service = AIService()
                return service

    def test_init(self, ai_service):
        """测试服务初始化."""
        assert ai_service.openrouter_client is not None
        assert ai_service.ollama_provider is None

    def test_vision_model_check(self, ai_service):
        """测试视觉模型检查."""
        assert ai_service._is_vision_model("openai/gpt-4.1") is True
        assert ai_service._is_vision_model("anthropic/claude-opus-4") is True
        assert ai_service._is_vision_model("meta-llama/llama-4-maverick:free") is True
        assert ai_service._is_vision_model("some/random-model") is False

    def test_should_use_vision_model(self, ai_service):
        """测试是否需要视觉模型的判断."""
        # 纯文本消息
        messages = [{"role": "user", "content": "Hello"}]
        assert ai_service._should_use_vision_model(messages) is False

        # 包含图片的消息
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
            ]
        }]
        assert ai_service._should_use_vision_model(messages) is True

        # 包含PDF的消息
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this PDF"},
                {"type": "file", "file": {"url": "data:application/pdf;base64,..."}}
            ]
        }]
        assert ai_service._should_use_vision_model(messages) is True

    def test_prepare_multimodal_content(self, ai_service):
        """测试多模态内容准备."""
        # 文本内容
        content = "Hello world"
        result = ai_service._prepare_multimodal_content(content)
        assert result == "Hello world"

        # 多模态内容
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "image_url", "image_url": {"url": "http://example.com/image.png"}},
            {"type": "file", "file": {"url": "http://example.com/doc.pdf", "engine": "native"}}
        ]
        result = ai_service._prepare_multimodal_content(content)
        assert len(result) == 3
        assert result[0] == {"type": "text", "text": "Hello"}
        assert result[1]["type"] == "image_url"
        assert result[2]["type"] == "file"


class TestImageAndPDFEncoding:
    """测试图像和PDF编码功能."""

    def test_encode_image(self, tmp_path):
        """测试图像编码."""
        # 创建测试图像文件
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake png content")

        result = AIService.encode_image(str(image_path))
        assert result.startswith("data:image/png;base64,")

        # 验证base64编码
        base64_part = result.split(",")[1]
        decoded = base64.b64decode(base64_part)
        assert decoded == b"fake png content"

    def test_encode_pdf(self, tmp_path):
        """测试PDF编码."""
        # 创建测试PDF文件
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")

        result = AIService.encode_pdf(str(pdf_path))
        assert result.startswith("data:application/pdf;base64,")

        # 验证base64编码
        base64_part = result.split(",")[1]
        decoded = base64.b64decode(base64_part)
        assert decoded == b"fake pdf content"

    def test_create_image_message(self):
        """测试创建图像消息."""
        text = "What's in these images?"
        image_urls = [
            "http://example.com/image1.png",
            "data:image/png;base64,abc123"
        ]

        message = AIService.create_image_message(text, image_urls)

        assert message["role"] == "user"
        assert len(message["content"]) == 3
        assert message["content"][0] == {"type": "text", "text": text}
        assert message["content"][1]["type"] == "image_url"
        assert message["content"][2]["type"] == "image_url"

    def test_create_pdf_message(self):
        """测试创建PDF消息."""
        text = "Analyze these PDFs"
        pdf_urls = [
            "http://example.com/doc1.pdf",
            "data:application/pdf;base64,abc123"
        ]

        message = AIService.create_pdf_message(text, pdf_urls, pdf_engine="mistral-ocr")

        assert message["role"] == "user"
        assert len(message["content"]) == 3
        assert message["content"][0] == {"type": "text", "text": text}
        assert message["content"][1]["type"] == "file"
        assert message["content"][1]["file"]["engine"] == "mistral-ocr"


class TestAutoModelSelection:
    """测试自动模型选择."""

    @pytest.fixture
    def ai_service(self):
        """创建测试用的 AI Service."""
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test_key"
            mock_settings.OLLAMA_ENABLED = False

            with patch("app.services.ai_service.AsyncOpenAI"):
                service = AIService()
                return service

    @pytest.mark.asyncio
    async def test_auto_select_search_mode(self, ai_service):
        """测试搜索模式的自动选择."""
        # 付费用户
        user = Mock(spec=User, is_premium=True)
        provider, model = await ai_service.auto_select_model(ChatMode.SEARCH, 100, user)
        assert provider == "openrouter"
        assert model == "perplexity/sonar-pro"

        # 免费用户
        provider, model = await ai_service.auto_select_model(ChatMode.SEARCH, 100, None)
        assert provider == "openrouter"
        assert model == "perplexity/sonar"

    @pytest.mark.asyncio
    async def test_auto_select_vision_model(self, ai_service):
        """测试视觉模型的自动选择 - 简化版."""
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "What's this?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
            ]
        }]

        # 现在无论是否有视觉内容，都返回 AUTO_MODEL
        user = Mock(spec=User, is_premium=True)
        provider, model = await ai_service.auto_select_model(ChatMode.CHAT, 100, user, messages)
        assert provider == "openrouter"
        assert model == "openrouter/auto"  # 让 OpenRouter 决定是否使用视觉模型

        # 免费用户也一样
        provider, model = await ai_service.auto_select_model(ChatMode.CHAT, 100, None, messages)
        assert provider == "openrouter"
        assert model == "openrouter/auto"

    @pytest.mark.asyncio
    async def test_auto_select_chat_mode(self, ai_service):
        """测试聊天模式的自动选择."""
        # 现在所有聊天模式都应该返回 AUTO_MODEL
        user = Mock(spec=User, is_premium=True)
        provider, model = await ai_service.auto_select_model(ChatMode.CHAT, 5000, user)
        assert provider == "openrouter"
        assert model == "openrouter/auto"

        # 免费用户也使用 AUTO
        provider, model = await ai_service.auto_select_model(ChatMode.CHAT, 1000, None)
        assert provider == "openrouter"
        assert model == "openrouter/auto"


class TestChatFunctions:
    """测试聊天功能."""

    @pytest.fixture
    def ai_service(self):
        """创建测试用的 AI Service."""
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test_key"
            mock_settings.OLLAMA_ENABLED = False

            with patch("app.services.ai_service.AsyncOpenAI"):
                service = AIService()
                # Mock response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Test response"
                service.openrouter_client = Mock()
                service.openrouter_client.chat.completions.create = AsyncMock(
                    return_value=mock_response
                )
                return service

    @pytest.mark.asyncio
    async def test_chat_basic(self, ai_service):
        """测试基础聊天功能."""
        messages = [{"role": "user", "content": "Hello"}]
        result = await ai_service.chat(messages)

        assert result == "Test response"
        ai_service.openrouter_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_web_search(self, ai_service):
        """测试带网络搜索的聊天."""
        messages = [{"role": "user", "content": "Search for latest news"}]
        result = await ai_service.chat(
            messages,
            mode=ChatMode.CHAT,
            web_search=True
        )

        assert result == "Test response"

        # 验证添加了 :online 后缀
        call_args = ai_service.openrouter_client.chat.completions.create.call_args
        model = call_args[1]["model"]
        assert ":online" in model

    @pytest.mark.asyncio
    async def test_chat_with_pdf_engine(self, ai_service):
        """测试带PDF引擎的聊天."""
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this PDF"},
                {"type": "file", "file": {"url": "data:application/pdf;base64,..."}}
            ]
        }]

        result = await ai_service.chat(
            messages,
            pdf_engine="mistral-ocr"
        )

        assert result == "Test response"

        # 验证设置了PDF引擎
        call_args = ai_service.openrouter_client.chat.completions.create.call_args
        assert call_args[1]["pdf_engine"] == "mistral-ocr"

    @pytest.mark.asyncio
    async def test_chat_with_search_context_size(self, ai_service):
        """测试带搜索上下文大小的聊天."""
        messages = [{"role": "user", "content": "Search something"}]
        result = await ai_service.chat(
            messages,
            mode=ChatMode.SEARCH,
            search_context_size="high"
        )

        assert result == "Test response"

        # 验证设置了搜索上下文大小
        call_args = ai_service.openrouter_client.chat.completions.create.call_args
        assert call_args[1]["search_context_size"] == "high"

    @pytest.mark.asyncio
    async def test_chat_auto_vision_switch(self, ai_service):
        """测试自动切换视觉模型."""
        # Mock _is_vision_model to return False for the test model
        ai_service._is_vision_model = Mock(return_value=False)

        # Mock handle_non_vision_model_with_attachments
        ai_service.handle_non_vision_model_with_attachments = AsyncMock(
            return_value=("openrouter", "openai/gpt-4.1", [{"role": "user", "content": "processed"}])
        )

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "What's this?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
            ]
        }]

        result = await ai_service.chat(
            messages,
            model="some/non-vision-model",
            provider="openrouter",
            auto_switch_vision=True
        )

        assert result == "Test response"
        ai_service.handle_non_vision_model_with_attachments.assert_called_once()


class TestStreamChat:
    """测试流式聊天功能."""

    @pytest.fixture
    def ai_service(self):
        """创建测试用的 AI Service."""
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test_key"
            mock_settings.OLLAMA_ENABLED = False

            with patch("app.services.ai_service.AsyncOpenAI"):
                service = AIService()
                return service

    @pytest.mark.asyncio
    async def test_stream_chat_basic(self, ai_service):
        """测试基础流式聊天."""
        # Mock streaming response
        async def mock_stream():
            chunks = [
                Mock(choices=[Mock(delta=Mock(content="Hello"))]),
                Mock(choices=[Mock(delta=Mock(content=" world"))]),
                Mock(choices=[Mock(delta=Mock(content=None))])
            ]
            for chunk in chunks:
                yield chunk

        ai_service.openrouter_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )

        messages = [{"role": "user", "content": "Hello"}]
        result = []
        async for chunk in ai_service.stream_chat(messages):
            result.append(chunk)

        assert result == ["Hello", " world"]


class TestEmbeddings:
    """测试嵌入向量功能."""

    @pytest.fixture
    def ai_service(self):
        """创建测试用的 AI Service."""
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test_key"
            mock_settings.OLLAMA_ENABLED = False

            with patch("app.services.ai_service.AsyncOpenAI"):
                service = AIService()
                # Mock response
                mock_response = Mock()
                mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
                service.openrouter_client = Mock()
                service.openrouter_client.embeddings.create = AsyncMock(
                    return_value=mock_response
                )
                return service

    @pytest.mark.asyncio
    async def test_get_embedding_default(self, ai_service):
        """测试获取嵌入向量 - 默认模型."""
        result = await ai_service.get_embedding("test text")

        assert result == [0.1, 0.2, 0.3]

        # 验证使用了默认模型
        call_args = ai_service.openrouter_client.embeddings.create.call_args
        assert call_args[1]["model"] == "openai/text-embedding-3-small"
        assert call_args[1]["input"] == "test text"

    @pytest.mark.asyncio
    async def test_get_embedding_custom_model(self, ai_service):
        """测试获取嵌入向量 - 自定义模型."""
        result = await ai_service.get_embedding(
            "test text",
            model="openai/text-embedding-3-large"
        )

        assert result == [0.1, 0.2, 0.3]

        # 验证使用了指定模型
        call_args = ai_service.openrouter_client.embeddings.create.call_args
        assert call_args[1]["model"] == "openai/text-embedding-3-large"


class TestHandleAttachments:
    """测试附件处理功能."""

    @pytest.fixture
    def ai_service(self):
        """创建测试用的 AI Service."""
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test_key"
            mock_settings.OLLAMA_ENABLED = False

            with patch("app.services.ai_service.AsyncOpenAI"):
                service = AIService()
                return service

    @pytest.mark.asyncio
    async def test_handle_non_vision_model_auto_switch(self, ai_service):
        """测试非视觉模型自动切换."""
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "What's this?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
            ]
        }]

        user = Mock(spec=User, is_premium=True)

        provider, model, processed_messages = await ai_service.handle_non_vision_model_with_attachments(
            messages,
            "some/non-vision-model",
            "openrouter",
            user,
            auto_switch=True
        )

        assert provider == "openrouter"
        assert model in ai_service.VISION_MODELS["premium"]
        assert processed_messages == messages

    @pytest.mark.asyncio
    async def test_handle_non_vision_model_extract_text(self, ai_service):
        """测试非视觉模型提取文本."""
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "What's this?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
                {"type": "file", "file": {"url": "data:application/pdf;base64,...", "name": "test.pdf"}}
            ]
        }]

        provider, model, processed_messages = await ai_service.handle_non_vision_model_with_attachments(
            messages,
            "some/non-vision-model",
            "openrouter",
            None,
            auto_switch=False
        )

        assert provider == "openrouter"
        assert model == "some/non-vision-model"
        assert len(processed_messages) == 1
        assert processed_messages[0]["role"] == "user"
        assert isinstance(processed_messages[0]["content"], str)
        assert "What's this?" in processed_messages[0]["content"]
        assert "[图片内容：" in processed_messages[0]["content"]
        assert "[文件内容：test.pdf" in processed_messages[0]["content"]


class TestModelInfo:
    """测试模型信息功能."""

    @pytest.fixture
    def ai_service(self):
        """创建测试用的 AI Service."""
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test_key"
            mock_settings.OLLAMA_ENABLED = False

            with patch("app.services.ai_service.AsyncOpenAI"):
                service = AIService()
                return service

    @pytest.mark.asyncio
    async def test_list_available_models(self, ai_service):
        """测试列出可用模型 - 更新后的结构."""
        models = await ai_service.list_available_models()

        assert "providers" in models
        assert "models" in models

        # 验证提供商列表
        assert "openrouter" in models["providers"]
        assert "ollama" in models["providers"]
        assert "custom" in models["providers"]

        # 验证 OpenRouter 模型结构
        openrouter_models = models["models"]["openrouter"]
        assert openrouter_models["auto"] == "openrouter/auto"
        assert "premium" in openrouter_models["chat"]
        assert "free" in openrouter_models["chat"]
        assert "premium" in openrouter_models["vision"]
        assert "free" in openrouter_models["vision"]

    @pytest.mark.asyncio
    async def test_get_model_info_basic(self, ai_service):
        """测试获取模型信息 - 基本情况."""
        info = await ai_service.get_model_info("test-model")

        assert info["id"] == "test-model"
        assert info["name"] == "test-model"
        assert info["description"] == "Model information not available"


class TestCustomProviders:
    """测试自定义提供商功能."""

    @pytest.fixture
    def ai_service(self):
        """创建测试用的 AI Service."""
        with patch("app.services.ai_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = None
            mock_settings.OLLAMA_ENABLED = False

            service = AIService()
            return service

    def test_add_custom_provider(self, ai_service):
        """测试添加自定义提供商."""
        ai_service.add_custom_provider(
            name="my-local-llm",
            endpoint="http://localhost:8080/v1",
            api_key=None
        )

        assert "my-local-llm" in ai_service.custom_providers
        provider = ai_service.custom_providers["my-local-llm"]
        assert provider.name == "my-local-llm"
        assert provider.endpoint == "http://localhost:8080/v1"

    def test_remove_custom_provider(self, ai_service):
        """测试移除自定义提供商."""
        # 先添加
        ai_service.add_custom_provider(
            name="test-provider",
            endpoint="http://example.com/api"
        )

        # 再移除
        result = ai_service.remove_custom_provider("test-provider")
        assert result is True
        assert "test-provider" not in ai_service.custom_providers

        # 移除不存在的提供商
        result = ai_service.remove_custom_provider("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_custom_providers(self, ai_service):
        """测试列出自定义提供商."""
        # 添加提供商
        ai_service.add_custom_provider(
            name="provider1",
            endpoint="http://localhost:8080/v1",
            api_key="test-key"
        )

        # Mock list_models
        ai_service.custom_providers["provider1"].list_models = AsyncMock(
            return_value=["model1", "model2"]
        )

        result = await ai_service.list_custom_providers()

        assert "provider1" in result
        assert result["provider1"]["endpoint"] == "http://localhost:8080/v1"
        assert result["provider1"]["models"] == ["model1", "model2"]
        assert result["provider1"]["has_api_key"] is True

    @pytest.mark.asyncio
    async def test_auto_select_with_custom_provider(self, ai_service):
        """测试使用自定义提供商的自动选择."""
        # 添加自定义提供商
        ai_service.add_custom_provider(
            name="my-provider",
            endpoint="http://localhost:8080/v1"
        )

        # Mock list_models
        ai_service.custom_providers["my-provider"].list_models = AsyncMock(
            return_value=["custom-model-1"]
        )

        # 没有 OpenRouter 时应该选择自定义提供商
        provider, model = await ai_service.auto_select_model(
            ChatMode.CHAT, 1000, None
        )

        assert provider == "custom:my-provider"
        assert model == "custom-model-1"

    @pytest.mark.asyncio
    async def test_chat_with_custom_provider(self, ai_service):
        """测试使用自定义提供商聊天."""
        # 添加自定义提供商
        ai_service.add_custom_provider(
            name="test-llm",
            endpoint="http://localhost:8080/v1"
        )

        # Mock chat response
        ai_service.custom_providers["test-llm"].chat = AsyncMock(
            return_value="Custom response"
        )

        messages = [{"role": "user", "content": "Hello"}]
        result = await ai_service.chat(
            messages,
            provider="custom:test-llm",
            model="test-model"
        )

        assert result == "Custom response"
        ai_service.custom_providers["test-llm"].chat.assert_called_once()
