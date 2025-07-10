"""Simplified AI service for demo purposes."""

from typing import AsyncGenerator, Dict, List, Optional

from app.core.config import settings
from app.schemas.conversations import ChatMode


class SimpleAIService:
    """简化版AI服务（用于Demo）."""

    @staticmethod
    async def chat(
        messages: List[Dict[str, str]], 
        mode: ChatMode = ChatMode.CHAT,
        model: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """简单的聊天响应."""
        # Demo实现，返回固定响应
        user_message = messages[-1]['content'] if messages else "你好"
        return f"这是一个Demo响应。你说的是：{user_message}"

    @staticmethod
    async def stream_chat(
        messages: List[Dict[str, str]], 
        mode: ChatMode = ChatMode.CHAT,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """流式聊天响应."""
        response = await SimpleAIService.chat(messages, mode, model)
        # 模拟流式输出
        for char in response:
            yield char