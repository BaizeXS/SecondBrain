"""AI service for handling multiple AI providers and intelligent routing."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import google.generativeai as genai
import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.models import User


class ChatMode(str, Enum):
    """对话模式枚举."""

    CHAT = "chat"
    SEARCH = "search"
    THINK = "think"


class AIProvider(ABC):
    """AI提供商抽象基类."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """同步聊天接口."""
        pass

    @abstractmethod
    async def stream_chat(
        self, messages: List[Dict[str, str]], model: str, **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天接口."""
        pass

    @abstractmethod
    async def get_embedding(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """获取文本嵌入向量."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI提供商."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """同步聊天."""
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式聊天."""
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def get_embedding(
        self, text: str, model: str = "text-embedding-3-small"
    ) -> List[float]:
        """获取文本嵌入向量."""
        response = await self.client.embeddings.create(model=model, input=text)
        return response.data[0].embedding


class AnthropicProvider(AIProvider):
    """Anthropic提供商."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.client = AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        """同步聊天."""
        # 转换消息格式
        system_message = ""
        formatted_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                formatted_messages.append(msg)

        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message if system_message else None,
            messages=formatted_messages,
            **kwargs,
        )
        return response.content[0].text

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式聊天."""
        system_message = ""
        formatted_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                formatted_messages.append(msg)

        async with self.client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message if system_message else None,
            messages=formatted_messages,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def get_embedding(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """Anthropic不支持嵌入，抛出异常."""
        raise NotImplementedError("Anthropic does not support embeddings")


class GoogleProvider(AIProvider):
    """Google Gemini提供商."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        genai.configure(api_key=api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """同步聊天."""
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            formatted_messages.append({"role": role, "parts": [msg["content"]]})

        model_instance = genai.GenerativeModel(model)
        chat = model_instance.start_chat(history=formatted_messages[:-1])

        response = await chat.send_message_async(
            formatted_messages[-1]["parts"][0],
            generation_config=genai.types.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            ),
        )
        return response.text

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式聊天."""
        # Google Gemini流式实现
        formatted_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            formatted_messages.append({"role": role, "parts": [msg["content"]]})

        model_instance = genai.GenerativeModel(model)
        chat = model_instance.start_chat(history=formatted_messages[:-1])

        response = await chat.send_message_async(
            formatted_messages[-1]["parts"][0],
            generation_config=genai.types.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            ),
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def get_embedding(
        self, text: str, model: str = "models/embedding-001"
    ) -> List[float]:
        """获取文本嵌入向量."""
        result = await genai.embed_content_async(
            model=model, content=text, task_type="retrieval_document"
        )
        return result["embedding"]


class DeepSeekProvider(AIProvider):
    """DeepSeek提供商."""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        super().__init__(api_key, base_url)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """同步聊天."""
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式聊天."""
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def get_embedding(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """DeepSeek不支持嵌入，使用OpenAI兼容接口."""
        raise NotImplementedError("DeepSeek does not support embeddings")


class AIService:
    """AI服务主类."""

    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self._init_providers()

    def _init_providers(self):
        """初始化AI提供商."""
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAIProvider(
                settings.OPENAI_API_KEY, settings.OPENAI_BASE_URL
            )

        if settings.ANTHROPIC_API_KEY:
            self.providers["anthropic"] = AnthropicProvider(settings.ANTHROPIC_API_KEY)

        if settings.GOOGLE_API_KEY:
            self.providers["google"] = GoogleProvider(settings.GOOGLE_API_KEY)

        if settings.DEEPSEEK_API_KEY:
            self.providers["deepseek"] = DeepSeekProvider(
                settings.DEEPSEEK_API_KEY, settings.DEEPSEEK_BASE_URL
            )

    def get_provider(self, provider_name: str) -> AIProvider:
        """获取指定的AI提供商."""
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"未支持的AI提供商: {provider_name}")
        return provider

    async def auto_select_model(
        self, mode: ChatMode, message_length: int, user: User
    ) -> Tuple[str, str]:
        """智能选择最合适的模型."""
        # 根据模式和消息长度智能选择模型
        if mode == ChatMode.THINK:
            # 推理模式使用DeepSeek
            if "deepseek" in self.providers:
                return "deepseek", "deepseek-reasoner"
            else:
                return "openai", "gpt-4o"

        elif mode == ChatMode.SEARCH:
            # 搜索模式使用快速模型
            return "openai", "gpt-4o-mini"

        else:  # ChatMode.CHAT
            # 普通聊天根据用户级别选择
            if user.is_premium:
                if message_length > 1000:
                    return "openai", "gpt-4o"
                else:
                    return "openai", "gpt-4o-mini"
            else:
                return "openai", "gpt-4o-mini"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        mode: ChatMode = ChatMode.CHAT,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        user: Optional[User] = None,
        **kwargs,
    ) -> str:
        """同步聊天接口."""
        # 智能路由
        if not provider or not model:
            message_length = sum(len(msg["content"]) for msg in messages)
            provider, model = await self.auto_select_model(mode, message_length, user)

        ai_provider = self.get_provider(provider)
        return await ai_provider.chat(messages, model, **kwargs)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        mode: ChatMode = ChatMode.CHAT,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        user: Optional[User] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式聊天接口."""
        # 智能路由
        if not provider or not model:
            message_length = sum(len(msg["content"]) for msg in messages)
            provider, model = await self.auto_select_model(mode, message_length, user)

        ai_provider = self.get_provider(provider)
        async for chunk in ai_provider.stream_chat(messages, model, **kwargs):
            yield chunk

    async def get_embedding(
        self, text: str, provider: str = "openai", model: Optional[str] = None
    ) -> List[float]:
        """获取文本嵌入向量."""
        ai_provider = self.get_provider(provider)
        if not model:
            model = settings.DEFAULT_EMBEDDING_MODEL
        return await ai_provider.get_embedding(text, model)

    async def search_web(
        self, query: str, search_scope: str = "web", max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """网络搜索功能."""
        # 这里可以集成Perplexity或其他搜索API
        if settings.PERPLEXITY_API_KEY:
            return await self._search_with_perplexity(query, max_results)
        else:
            # 使用其他搜索实现
            return await self._search_with_fallback(query, max_results)

    async def _search_with_perplexity(
        self, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """使用Perplexity搜索."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.PERPLEXITY_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-sonar-huge-128k-online",
                    "messages": [{"role": "user", "content": query}],
                    "max_tokens": 2048,
                    "temperature": 0.2,
                },
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # 解析搜索结果
                return [
                    {
                        "title": "搜索结果",
                        "content": content,
                        "url": "",
                        "snippet": content[:200] + "..."
                        if len(content) > 200
                        else content,
                    }
                ]
            else:
                return []

    async def _search_with_fallback(
        self, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """备用搜索实现."""
        # 这里可以实现其他搜索API的调用
        return [
            {
                "title": f"搜索结果: {query}",
                "content": f"这是关于 '{query}' 的搜索结果",
                "url": "",
                "snippet": f"搜索关键词: {query}",
            }
        ]


# 全局AI服务实例
ai_service = AIService()
