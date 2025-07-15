"""AI service with OpenRouter and Ollama support."""

import base64
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import httpx
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.models import User
from app.schemas.conversations import ChatMode

logger = logging.getLogger(__name__)


class ContentPart(TypedDict, total=False):
    """Content part for multimodal messages."""

    type: str  # "text", "image_url", or "file"
    text: NotRequired[str]
    image_url: NotRequired[dict[str, str]]  # {"url": "..."}
    file: NotRequired[dict[str, Any]]  # For PDF support


class ChatMessage(TypedDict, total=False):
    """Chat message type definition."""

    role: str
    content: str | list[ContentPart]  # Support both text and multimodal content
    name: NotRequired[str]
    function_call: NotRequired[dict[str, Any]]
    tool_calls: NotRequired[list[dict[str, Any]]]


# Type alias for messages
MessagesType = list[dict[str, Any]]


class OllamaProvider:
    """Ollama本地模型提供商."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def _check_model_available(self, model: str) -> bool:
        """检查模型是否可用."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    available_models = [m["name"] for m in data.get("models", [])]
                    return model in available_models
                return False
        except Exception:
            return False

    async def _list_models(self) -> list[str]:
        """列出所有可用的模型."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
                return []
        except Exception:
            return []

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> str:
        """同步聊天."""
        _ = kwargs  # 避免未使用参数警告
        # 检查模型是否可用
        if not await self._check_model_available(model):
            available_models = await self._list_models()
            if available_models:
                # 使用第一个可用的模型
                model = available_models[0]
            else:
                raise ValueError("Ollama服务不可用或没有安装任何模型")

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens or -1,
                    },
                },
            )

            if response.status_code == 200:
                data = response.json()
                return data["message"]["content"]
            else:
                raise Exception(f"Ollama chat failed: {response.text}")

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式聊天."""
        _ = kwargs  # 避免未使用参数警告
        # 检查模型是否可用
        if not await self._check_model_available(model):
            available_models = await self._list_models()
            if available_models:
                model = available_models[0]
            else:
                raise ValueError("Ollama服务不可用或没有安装任何模型")

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens or -1,
                    },
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            import json

                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue

    async def get_embedding(self, text: str, model: str | None = None) -> list[float]:
        """获取文本嵌入向量."""
        if not model:
            # 尝试使用默认的嵌入模型
            model = "nomic-embed-text"
            if not await self._check_model_available(model):
                # 寻找其他嵌入模型
                available_models = await self._list_models()
                embed_models = [m for m in available_models if "embed" in m]
                if embed_models:
                    model = embed_models[0]
                else:
                    raise ValueError("没有可用的嵌入模型")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return data["embedding"]
            else:
                raise Exception(f"Ollama embedding failed: {response.text}")


class CustomProvider:
    """自定义AI提供商基类."""

    def __init__(self, name: str, endpoint: str, api_key: str | None = None):
        self.name = name
        self.endpoint = endpoint
        self.api_key = api_key
        self.client = AsyncOpenAI(
            api_key=api_key or "dummy",  # 本地模型可能不需要 API key
            base_url=endpoint,
        )

    async def chat(self, messages: list[dict[str, Any]], model: str, **kwargs) -> str:
        """聊天接口."""
        response = await self.client.chat.completions.create(
            model=model, messages=messages, **kwargs  # type: ignore
        )
        return response.choices[0].message.content or ""

    async def stream_chat(
        self, messages: list[dict[str, Any]], model: str, **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天接口."""
        stream = await self.client.chat.completions.create(
            model=model, messages=messages, stream=True, **kwargs  # type: ignore
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def list_models(self) -> list[str]:
        """列出可用模型."""
        try:
            response = await self.client.models.list()
            return [model.id for model in response.data]
        except Exception:
            return []


class AIService:
    """AI服务主类 - 使用OpenRouter作为主要提供商."""

    # OpenRouter Auto 模型 - 元模型，自动路由到最合适的模型
    AUTO_MODEL = "openrouter/auto"

    # 模型提供商类型
    MODEL_PROVIDERS = {
        "openrouter": "OpenRouter (推荐)",
        "ollama": "Ollama (本地)",
        "openai": "OpenAI (直连)",
        "anthropic": "Anthropic (直连)",
        "custom": "自定义 API",
    }

    # 聊天模型列表（按优先级排序）
    CHAT_MODELS = {
        "premium": [
            # OpenAI 最新模型
            "openai/gpt-4.1",
            "openai/gpt-4.1-mini",
            "openai/o4-mini-high",
            "openai/o1-pro",
            # Claude 最新模型
            "anthropic/claude-opus-4",
            "anthropic/claude-sonnet-4",
            "anthropic/claude-3.7-sonnet:beta",
            "anthropic/claude-3.5-haiku:beta",
            # Google 模型
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash",
            # xAI
            "x-ai/grok-4",
            # 其他付费模型
            "minimax/minimax-m1",
            "thudm/glm-4.1v-9b-thinking",
        ],
        "free": [
            # Qwen 免费模型
            "qwen/qwen3-235b-a22b:free",
            "qwen/qwen3-30b-a3b:free",
            "qwen/qwen3-32b:free",
            "deepseek/deepseek-r1-0528-qwen3-8b:free",
            # Deepseek 免费模型
            "deepseek/deepseek-r1-0528:free",
            "deepseek/deepseek-chat-v3-0324:free",
            # Llama4 免费模型
            "meta-llama/llama-4-maverick:free",
            "meta-llama/llama-4-scout:free",
            # Moonshot 免费模型
            "moonshotai/kimi-k2:free",
        ],
    }

    # 搜索模型列表
    SEARCH_MODELS = {
        "openai": [
            "openai/gpt-4.1",
            "openai/gpt-4.1-mini",
        ],
        "perplexity": [
            "perplexity/sonar",
            "perplexity/sonar-reasoning",
            "perplexity/sonar-pro",
            "perplexity/sonar-reasoning-pro",
        ],
    }

    # 搜索上下文大小选项
    SEARCH_CONTEXT_SIZES = ["low", "medium", "high"]

    # 深度研究模型（保留供将来使用）
    DEEP_RESEARCH_MODEL = "perplexity/sonar-deep-research"

    # 视觉模型列表（支持图像输入）
    VISION_MODELS = {
        "premium": [
            # OpenAI
            "openai/gpt-4.1",
            "openai/gpt-4.1-mini",
            "openai/o4-mini-high",
            "openai/o1-pro",
            # Claude
            "anthropic/claude-opus-4",
            "anthropic/claude-sonnet-4",
            "anthropic/claude-3.7-sonnet:beta",
            "anthropic/claude-3.5-haiku:beta",
            # Google
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash",
            # xAI
            "x-ai/grok-4",
            # MiniMax
            "minimax/minimax-01",
            # THUDM
            "thudm/glm-4.1v-9b-thinking",
        ],
        "free": [
            # Llama4
            "meta-llama/llama-4-maverick:free",
            "meta-llama/llama-4-scout:free",
            # Moonshot
            "moonshotai/kimi-vl-a3b-thinking:free",
        ],
    }

    # PDF处理引擎
    PDF_ENGINES = {
        "pdf-text": "Free, best for clear text documents",
        "mistral-ocr": "$2/1000 pages, best for scanned/image PDFs",
        "native": "Model-specific native processing",
    }

    def __init__(self):
        self.openrouter_client = None
        self.ollama_provider = None
        self.custom_providers = {}  # 存储自定义提供商
        self._init_providers()

    def _init_providers(self):
        """初始化提供商."""
        # 初始化 OpenRouter（如果有 API key）
        if settings.OPENROUTER_API_KEY:
            self.openrouter_client = AsyncOpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": settings.OPENROUTER_SITE_URL
                    or "http://localhost:3000",
                    "X-Title": settings.OPENROUTER_APP_NAME or "SecondBrain",
                },
            )

        # 初始化 Ollama（如果启用）
        if settings.OLLAMA_ENABLED:
            self.ollama_provider = OllamaProvider(settings.OLLAMA_BASE_URL)

    def add_custom_provider(
        self, name: str, endpoint: str, api_key: str | None = None
    ) -> None:
        """添加自定义模型提供商.

        Args:
            name: 提供商名称
            endpoint: API endpoint URL
            api_key: API密钥（可选）
        """
        self.custom_providers[name] = CustomProvider(name, endpoint, api_key)

    def remove_custom_provider(self, name: str) -> bool:
        """移除自定义提供商.

        Args:
            name: 提供商名称

        Returns:
            是否成功移除
        """
        if name in self.custom_providers:
            del self.custom_providers[name]
            return True
        return False

    async def list_custom_providers(self) -> dict[str, dict[str, Any]]:
        """列出所有自定义提供商及其模型.

        Returns:
            自定义提供商信息
        """
        result = {}
        for name, provider in self.custom_providers.items():
            models = await provider.list_models()
            result[name] = {
                "endpoint": provider.endpoint,
                "models": models,
                "has_api_key": bool(provider.api_key),
            }
        return result

    def _get_openrouter_model(self, model: str) -> str:
        """获取 OpenRouter 格式的模型名称."""
        # 如果已经是 OpenRouter 格式（包含斜杠），直接返回
        if "/" in model:
            return model
        # 否则假设它已经是正确的格式，直接返回
        return model

    def _is_vision_model(self, model: str) -> bool:
        """检查模型是否支持视觉输入."""
        all_vision_models = self.VISION_MODELS["premium"] + self.VISION_MODELS["free"]
        return model in all_vision_models

    def _should_use_vision_model(self, messages: list[dict[str, Any]]) -> bool:
        """检查消息是否包含需要视觉模型的内容."""
        for msg in messages:
            if isinstance(msg.get("content"), list):
                for part in msg["content"]:
                    if part.get("type") in ["image_url", "file"]:
                        return True
        return False

    def _prepare_multimodal_content(
        self, content: str | list[ContentPart]
    ) -> str | list[ContentPart]:
        """准备多模态内容，确保格式正确."""
        if isinstance(content, str):
            return content

        # 验证内容部分的格式
        prepared_parts = []
        for part in content:
            if part.get("type") == "text":
                prepared_parts.append({"type": "text", "text": part.get("text", "")})
            elif part.get("type") == "image_url":
                image_url = part.get("image_url", {})
                prepared_parts.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url.get("url", "")},
                    }
                )
            elif part.get("type") == "file":
                file_info = part.get("file", {})
                prepared_parts.append({"type": "file", "file": file_info})

        return prepared_parts

    async def auto_select_model(
        self,
        mode: ChatMode,
        message_length: int,
        user: User | None,
        messages: list[dict[str, Any]] | None = None,
    ) -> tuple[str, str]:
        """智能模型选择 - 优先使用 OpenRouter Auto."""
        # 检查可用的提供商
        has_openrouter = self.openrouter_client is not None
        has_ollama = self.ollama_provider is not None
        has_custom = len(self.custom_providers) > 0

        if not has_openrouter and not has_ollama and not has_custom:
            raise ValueError("没有可用的AI提供商")

        # 如果有 OpenRouter，优先使用
        if has_openrouter:
            # 特殊情况：搜索模式需要特定的搜索模型
            if mode == ChatMode.SEARCH:
                if user and user.is_premium:
                    return "openrouter", "perplexity/sonar-pro"
                else:
                    return "openrouter", "perplexity/sonar"
            else:
                # 其他所有情况都使用 Auto，让 OpenRouter 智能选择
                return "openrouter", self.AUTO_MODEL

        # 如果有自定义提供商，使用第一个
        elif has_custom:
            provider_name = list(self.custom_providers.keys())[0]
            provider = self.custom_providers[provider_name]
            models = await provider.list_models()
            if models:
                return f"custom:{provider_name}", models[0]
            else:
                # 如果列不出模型，使用默认模型名
                return f"custom:{provider_name}", "default"

        # 最后尝试 Ollama
        elif has_ollama and self.ollama_provider:
            models = await self.ollama_provider._list_models()
            if models:
                return "ollama", models[0]

        raise ValueError("没有可用的模型")

    async def chat(
        self,
        messages: list[dict[str, Any]],
        mode: ChatMode = ChatMode.CHAT,
        model: str | None = None,
        provider: str | None = None,
        user: User | None = None,
        web_search: bool = False,
        pdf_engine: str = "native",
        search_context_size: str = "medium",
        auto_switch_vision: bool = True,
        **kwargs,
    ) -> str:
        """同步聊天接口.

        Args:
            messages: 消息列表，支持文本和多模态内容
            mode: 聊天模式
            model: 指定模型
            provider: 指定提供商
            user: 用户对象
            web_search: 是否启用网页搜索
            pdf_engine: PDF处理引擎 (native, pdf-text, mistral-ocr)
            search_context_size: 搜索上下文大小 (low, medium, high)
            auto_switch_vision: 是否自动切换到视觉模型
            **kwargs: 其他参数 (temperature, max_tokens等)
        """
        # 处理多模态内容
        processed_messages = []
        for msg in messages:
            processed_msg = msg.copy()
            if "content" in processed_msg:
                processed_msg["content"] = self._prepare_multimodal_content(
                    msg["content"]
                )
            processed_messages.append(processed_msg)

        # 智能路由
        if not provider or not model:
            # 计算消息长度（处理多模态内容）
            message_length = 0
            for msg in messages:
                if isinstance(msg.get("content"), str):
                    message_length += len(msg["content"])
                elif isinstance(msg.get("content"), list):
                    for part in msg["content"]:
                        if part.get("type") == "text":
                            message_length += len(part.get("text", ""))

            provider, model = await self.auto_select_model(
                mode, message_length, user, messages
            )

        # 检查是否需要处理非视觉模型的附件情况
        if (
            auto_switch_vision
            and not self._is_vision_model(model)
            and self._should_use_vision_model(processed_messages)
        ):
            (
                provider,
                model,
                processed_messages,
            ) = await self.handle_non_vision_model_with_attachments(
                processed_messages, model, provider, user, auto_switch_vision
            )

        # 处理自定义提供商
        if provider and provider.startswith("custom:"):
            provider_name = provider.split(":", 1)[1]
            if provider_name not in self.custom_providers:
                raise ValueError(f"自定义提供商 {provider_name} 不存在")
            return await self.custom_providers[provider_name].chat(
                processed_messages, model, **kwargs
            )

        # 处理 Ollama
        elif provider == "ollama":
            if not self.ollama_provider:
                raise ValueError("Ollama 未启用")
            return await self.ollama_provider.chat(processed_messages, model, **kwargs)

        # 默认使用 OpenRouter
        else:
            if not self.openrouter_client:
                raise ValueError("OpenRouter 未配置")

            # 转换为 OpenRouter 模型格式
            openrouter_model = self._get_openrouter_model(model)

            # 如果启用网页搜索，添加 :online 后缀
            if web_search and ":online" not in openrouter_model:
                openrouter_model = f"{openrouter_model}:online"

            # 准备额外参数
            extra_params = kwargs.copy()

            # 如果有PDF内容，设置PDF引擎
            if any(
                isinstance(msg.get("content"), list)
                and any(part.get("type") == "file" for part in msg.get("content", []))
                for msg in processed_messages
            ):
                extra_params["pdf_engine"] = pdf_engine

            # 如果是搜索模式或启用网页搜索，设置搜索上下文大小
            if mode == ChatMode.SEARCH or web_search:
                if search_context_size in self.SEARCH_CONTEXT_SIZES:
                    extra_params["search_context_size"] = search_context_size

            response = await self.openrouter_client.chat.completions.create(
                model=openrouter_model,
                messages=processed_messages,  # type: ignore
                **extra_params,
            )
            return response.choices[0].message.content or ""

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        mode: ChatMode = ChatMode.CHAT,
        model: str | None = None,
        provider: str | None = None,
        user: User | None = None,
        web_search: bool = False,
        pdf_engine: str = "native",
        search_context_size: str = "medium",
        auto_switch_vision: bool = True,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式聊天接口.

        Args:
            messages: 消息列表，支持文本和多模态内容
            mode: 聊天模式
            model: 指定模型
            provider: 指定提供商
            user: 用户对象
            web_search: 是否启用网页搜索
            pdf_engine: PDF处理引擎
            search_context_size: 搜索上下文大小 (low, medium, high)
            **kwargs: 其他参数
        """
        # 处理多模态内容
        processed_messages = []
        for msg in messages:
            processed_msg = msg.copy()
            if "content" in processed_msg:
                processed_msg["content"] = self._prepare_multimodal_content(
                    msg["content"]
                )
            processed_messages.append(processed_msg)

        # 智能路由
        if not provider or not model:
            # 计算消息长度（处理多模态内容）
            message_length = 0
            for msg in messages:
                if isinstance(msg.get("content"), str):
                    message_length += len(msg["content"])
                elif isinstance(msg.get("content"), list):
                    for part in msg["content"]:
                        if part.get("type") == "text":
                            message_length += len(part.get("text", ""))

            provider, model = await self.auto_select_model(
                mode, message_length, user, messages
            )

        # 检查是否需要处理非视觉模型的附件情况
        if (
            auto_switch_vision
            and not self._is_vision_model(model)
            and self._should_use_vision_model(processed_messages)
        ):
            (
                provider,
                model,
                processed_messages,
            ) = await self.handle_non_vision_model_with_attachments(
                processed_messages, model, provider, user, auto_switch_vision
            )

        # 处理自定义提供商
        if provider and provider.startswith("custom:"):
            provider_name = provider.split(":", 1)[1]
            if provider_name not in self.custom_providers:
                raise ValueError(f"自定义提供商 {provider_name} 不存在")
            async for chunk in self.custom_providers[provider_name].stream_chat(
                processed_messages, model, **kwargs
            ):
                yield chunk

        # 处理 Ollama
        elif provider == "ollama":
            if not self.ollama_provider:
                raise ValueError("Ollama 未启用")
            async for chunk in self.ollama_provider.stream_chat(
                processed_messages, model, **kwargs
            ):
                yield chunk

        # 默认使用 OpenRouter
        else:
            if not self.openrouter_client:
                raise ValueError("OpenRouter 未配置")

            # 转换为 OpenRouter 模型格式
            openrouter_model = self._get_openrouter_model(model)

            # 如果启用网页搜索，添加 :online 后缀
            if web_search and ":online" not in openrouter_model:
                openrouter_model = f"{openrouter_model}:online"

            # 准备额外参数
            extra_params = kwargs.copy()

            # 如果有PDF内容，设置PDF引擎
            if any(
                isinstance(msg.get("content"), list)
                and any(part.get("type") == "file" for part in msg.get("content", []))
                for msg in processed_messages
            ):
                extra_params["pdf_engine"] = pdf_engine

            # 如果是搜索模式或启用网页搜索，设置搜索上下文大小
            if mode == ChatMode.SEARCH or web_search:
                if search_context_size in self.SEARCH_CONTEXT_SIZES:
                    extra_params["search_context_size"] = search_context_size

            stream = await self.openrouter_client.chat.completions.create(
                model=openrouter_model,
                messages=processed_messages,  # type: ignore
                stream=True,
                **extra_params,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

    async def get_embedding(
        self, text: str, provider: str = "openrouter", model: str | None = None
    ) -> list[float]:
        """获取文本嵌入向量."""
        if provider == "ollama":
            if not self.ollama_provider:
                raise ValueError("Ollama 未启用")
            return await self.ollama_provider.get_embedding(text, model)
        else:  # openrouter
            if not self.openrouter_client:
                raise ValueError("OpenRouter 未配置")

            # OpenRouter 使用 OpenAI 的嵌入模型
            embed_model = model or "openai/text-embedding-3-small"

            response = await self.openrouter_client.embeddings.create(
                model=embed_model,
                input=text,
            )
            return response.data[0].embedding

    async def list_available_models(self) -> dict[str, Any]:
        """列出所有可用的模型."""
        models = {
            "providers": self.MODEL_PROVIDERS,
            "models": {
                "openrouter": {
                    "auto": self.AUTO_MODEL,
                    "chat": {
                        "premium": self.CHAT_MODELS["premium"],
                        "free": self.CHAT_MODELS["free"],
                    },
                    "vision": {
                        "premium": self.VISION_MODELS["premium"],
                        "free": self.VISION_MODELS["free"],
                    },
                    "search": self.SEARCH_MODELS,
                    "deep_research": [self.DEEP_RESEARCH_MODEL],
                },
                "ollama": [],
                "custom": {},
            },
        }

        # Ollama 模型（动态获取）
        if self.ollama_provider:
            models["models"]["ollama"] = await self.ollama_provider._list_models()

        # 自定义提供商模型
        if self.custom_providers:
            for name, provider in self.custom_providers.items():
                provider_models = await provider.list_models()
                models["models"]["custom"][name] = provider_models

        return models

    async def get_model_info(self, model: str) -> dict[str, Any]:
        """获取模型信息."""
        # 可以通过 OpenRouter API 获取模型详细信息
        if self.openrouter_client and "/" in model:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://openrouter.ai/api/v1/models/{model}",
                        headers={
                            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        },
                    )
                    if response.status_code == 200:
                        return response.json()
            except Exception:
                pass

        # 返回基本信息
        return {
            "id": model,
            "name": model,
            "description": "Model information not available",
        }

    @staticmethod
    def encode_image(image_path: str | Path) -> str:
        """将图像文件编码为base64字符串.

        Args:
            image_path: 图像文件路径

        Returns:
            base64编码的图像数据URL
        """
        image_path = Path(image_path)
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")

        # 根据文件扩展名确定MIME类型
        mime_type = "image/jpeg"
        if image_path.suffix.lower() == ".png":
            mime_type = "image/png"
        elif image_path.suffix.lower() == ".webp":
            mime_type = "image/webp"

        return f"data:{mime_type};base64,{encoded}"

    @staticmethod
    def encode_pdf(pdf_path: str | Path) -> str:
        """将PDF文件编码为base64字符串.

        Args:
            pdf_path: PDF文件路径

        Returns:
            base64编码的PDF数据URL
        """
        pdf_path = Path(pdf_path)
        with open(pdf_path, "rb") as pdf_file:
            encoded = base64.b64encode(pdf_file.read()).decode("utf-8")
        return f"data:application/pdf;base64,{encoded}"

    @staticmethod
    def create_image_message(text: str, image_urls: list[str]) -> dict[str, Any]:
        """创建包含图像的消息.

        Args:
            text: 文本提示
            image_urls: 图像URL列表（可以是HTTP URL或base64数据URL）

        Returns:
            格式化的消息字典
        """
        content_parts = [{"type": "text", "text": text}]

        for url in image_urls:
            content_parts.append({"type": "image_url", "image_url": {"url": url}})  # type: ignore

        return {"role": "user", "content": content_parts}

    @staticmethod
    def create_pdf_message(
        text: str, pdf_urls: list[str], pdf_engine: str = "native"
    ) -> dict[str, Any]:
        """创建包含PDF的消息.

        Args:
            text: 文本提示
            pdf_urls: PDF URL列表（可以是HTTP URL或base64数据URL）
            pdf_engine: PDF处理引擎

        Returns:
            格式化的消息字典
        """
        content_parts = [{"type": "text", "text": text}]

        for url in pdf_urls:
            content_parts.append(
                {"type": "file", "file": {"url": url, "engine": pdf_engine}}  # type: ignore
            )

        return {"role": "user", "content": content_parts}

    async def handle_non_vision_model_with_attachments(
        self,
        messages: list[dict[str, Any]],
        model: str,
        provider: str,
        user: User | None = None,
        auto_switch: bool = True,
    ) -> tuple[str, str, list[dict[str, Any]]]:
        """处理非视觉模型接收到附件的情况.

        Args:
            messages: 包含附件的消息
            model: 当前选择的模型
            provider: 当前提供商
            user: 用户对象
            auto_switch: 是否自动切换到视觉模型

        Returns:
            (provider, model, processed_messages) 元组
        """
        if not self._should_use_vision_model(messages):
            return provider, model, messages

        if auto_switch:
            # 自动切换到视觉模型
            if user and user.is_premium:
                # 付费用户使用最好的视觉模型
                new_model = self.VISION_MODELS["premium"][0]
            else:
                # 免费用户使用免费视觉模型
                if self.VISION_MODELS["free"]:
                    new_model = self.VISION_MODELS["free"][0]
                else:
                    # 如果没有免费视觉模型，降级处理
                    return (
                        provider,
                        model,
                        await self._extract_attachments_as_text(messages),
                    )

            # 记录模型切换（可用于前端提示）
            logger.info(f"自动切换模型: {model} -> {new_model} (检测到视觉内容)")
            return "openrouter", new_model, messages
        else:
            # 提取附件内容为文本
            return provider, model, await self._extract_attachments_as_text(messages)

    async def _extract_attachments_as_text(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """将消息中的附件提取为文本内容.

        这是一个降级方案，当模型不支持视觉时使用。
        """
        processed_messages = []

        for msg in messages:
            if isinstance(msg.get("content"), list):
                text_parts = []
                attachment_texts = []

                for part in msg["content"]:
                    if part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif part.get("type") == "image_url":
                        # 图片降级处理
                        attachment_texts.append(
                            "[图片内容：由于当前模型不支持视觉，无法直接分析图片]"
                        )
                    elif part.get("type") == "file":
                        # PDF等文件降级处理
                        file_info = part.get("file", {})
                        attachment_texts.append(
                            f"[文件内容：{file_info.get('name', '未知文件')} - 由于当前模型限制，仅能处理文本内容]"
                        )

                # 组合文本内容
                combined_text = "\n".join(text_parts)
                if attachment_texts:
                    combined_text += "\n\n附件信息：\n" + "\n".join(attachment_texts)

                processed_messages.append(
                    {"role": msg["role"], "content": combined_text}
                )
            else:
                processed_messages.append(msg)

        return processed_messages


# 全局AI服务实例
ai_service = AIService()
