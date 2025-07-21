"""Chat service with document context support."""

import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.conversation import crud_conversation
from app.crud.message import crud_message
from app.models.models import Document, User
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    Role,
    Usage,
)
from app.schemas.conversations import ChatMode, MessageCreate
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务类，支持文档上下文."""

    def __init__(self) -> None:
        """初始化聊天服务."""
        pass

    async def create_completion_with_documents(
        self,
        db: AsyncSession,
        request: ChatCompletionRequest,
        user: User,
    ) -> ChatCompletionResponse | AsyncGenerator[str, None]:
        """创建包含文档上下文的聊天完成."""
        try:
            # 将Message对象转换为字典
            messages: list[dict[str, Any]] = []
            for msg in request.messages:
                if isinstance(msg, dict):
                    messages.append(msg)
                else:
                    messages.append(msg.model_dump())

            # 如果提供了文档ID，获取文档内容
            if request.document_ids:
                logger.info(f"🔍 ChatService收到文档ID请求: {request.document_ids}, user_id={user.id}")
                
                context = await self._get_documents_context(
                    db, request.document_ids, user.id
                )
                
                if context:
                    logger.info(f"✅ 获取到文档上下文，长度: {len(context)} 字符")
                    
                    # 在用户消息前插入文档上下文
                    context_message = {
                        "role": "system",
                        "content": f"以下是相关文档内容，请基于这些内容回答用户问题：\n\n{context}"
                    }
                    # 找到第一个用户消息的位置
                    user_msg_index = next(
                        (i for i, msg in enumerate(messages) if msg.get("role") == "user"),
                        len(messages)
                    )
                    messages.insert(user_msg_index, context_message)
                    logger.info(f"📝 文档上下文已插入到消息列表，位置: {user_msg_index}")
                else:
                    logger.warning(f"❌ 无法获取文档上下文: document_ids={request.document_ids}")
                    
                    # 记录详细的调试信息
                    logger.warning(f"🔍 调试信息: user_id={user.id}, conversation_id={request.conversation_id}, space_id={request.space_id}")

            # 如果有对话ID，加载历史消息
            if request.conversation_id:
                history = await self._get_conversation_history(
                    db, request.conversation_id, user.id
                )
                if history:
                    # 合并历史消息（保留系统消息在前）
                    system_msgs = [m for m in messages if m.get("role") == "system"]
                    other_msgs = [m for m in messages if m.get("role") != "system"]
                    messages = system_msgs + history + other_msgs

            # 如果是Space内的对话，可能需要向量搜索相关内容
            if request.space_id and not request.document_ids:
                # 从最后一条用户消息中提取查询
                user_query: str | None = None
                for msg_dict in reversed(messages):
                    if isinstance(msg_dict, dict) and msg_dict.get("role") == "user":
                        user_query = msg_dict.get("content", "")
                        break

                if user_query:
                    # 向量搜索相关文档
                    relevant_docs = await self._search_relevant_documents(
                        db, user_query, request.space_id, user.id
                    )
                    if relevant_docs:
                        context = self._format_documents_context(relevant_docs)
                        context_message = {
                            "role": "system",
                            "content": f"以下是Space中的相关内容：\n\n{context}"
                        }
                        # 在用户消息前插入
                        user_msg_index = next(
                            (i for i, msg in enumerate(messages) if msg.get("role") == "user"),
                            len(messages)
                        )
                        messages.insert(user_msg_index, context_message)

            # 确定聊天模式
            mode = ChatMode.CHAT
            if request.mode:
                mode = ChatMode[request.mode.upper()]

            # 调用AI服务
            if request.stream:
                return self._stream_completion(
                    messages, request, mode, user, db
                )
            else:
                response = await ai_service.chat(
                    messages=messages,
                    mode=mode,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    user=user,
                )

                # 保存消息到对话历史
                if request.conversation_id:
                    # 获取最后一条用户消息并转换为字典
                    last_message = request.messages[-1]
                    if hasattr(last_message, 'model_dump'):
                        user_msg_dict = last_message.model_dump()
                    else:
                        user_msg_dict = dict(last_message) if not isinstance(last_message, dict) else last_message

                    await self._save_messages(
                        db,
                        request.conversation_id,
                        user_msg_dict,  # 用户消息
                        response,  # AI响应
                        request.model,
                        request.document_ids
                    )

                # 构建响应
                from app.schemas.chat import Message as ChatMessage
                return ChatCompletionResponse(
                    id=f"chatcmpl-{uuid4().hex[:8]}",
                    created=int(datetime.now().timestamp()),
                    model=request.model,
                    choices=[Choice(
                        index=0,
                        message=ChatMessage(role=Role.assistant, content=response),
                        finish_reason="stop"
                    )],
                    usage=Usage(
                        prompt_tokens=sum(len(m.get("content", "")) for m in messages) // 4,
                        completion_tokens=len(response) // 4,
                        total_tokens=(sum(len(m.get("content", "")) for m in messages) + len(response)) // 4
                    )
                )

        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def _stream_completion(
        self,
        messages: list[dict[str, Any]],
        request: ChatCompletionRequest,
        mode: ChatMode,
        user: User,
        db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """流式生成聊天响应."""
        try:
            response_content = ""
            chunk_id = f"chatcmpl-{uuid4().hex[:8]}"

            async for chunk in ai_service.stream_chat(
                messages=messages,
                mode=mode,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                user=user,
            ):
                response_content += chunk

                # 构建流式响应块
                chunk_data = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": chunk},
                        "finish_reason": None
                    }]
                }

                yield f"data: {json.dumps(chunk_data)}\n\n"

            # 发送结束块
            final_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

            # 保存消息
            if request.conversation_id and response_content:
                # 获取最后一条用户消息并转换为字典
                last_message = request.messages[-1]
                if hasattr(last_message, 'model_dump'):
                    user_msg_dict = last_message.model_dump()
                else:
                    user_msg_dict = dict(last_message) if not isinstance(last_message, dict) else last_message

                await self._save_messages(
                    db,
                    request.conversation_id,
                    user_msg_dict,
                    response_content,
                    request.model,
                    request.document_ids
                )

        except Exception as e:
            logger.error(f"Stream completion error: {str(e)}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "internal_error",
                    "code": "stream_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

    async def _get_documents_context(
        self,
        db: AsyncSession,
        document_ids: list[int],
        user_id: int,
        max_length: int = 8000
    ) -> str | None:
        """获取文档内容作为上下文."""
        try:
            logger.info(f"🔍 获取文档上下文: document_ids={document_ids}, user_id={user_id}")
            
            # 查询文档
            stmt = select(Document).where(
                Document.id.in_(document_ids),
                Document.user_id == user_id,
                Document.content.isnot(None)
            )
            result = await db.execute(stmt)
            documents = result.scalars().all()
            
            logger.info(f"📊 查询结果: 找到 {len(documents)} 个文档")
            
            if not documents:
                # 再次查询所有文档（包括content为None的）来调试
                stmt_debug = select(Document).where(
                    Document.id.in_(document_ids),
                    Document.user_id == user_id
                )
                result_debug = await db.execute(stmt_debug)
                all_docs = result_debug.scalars().all()
                
                logger.warning(f"🔍 调试查询: 找到 {len(all_docs)} 个文档（包括content为None）")
                for doc in all_docs:
                    logger.warning(f"📄 文档 {doc.id}: filename={doc.filename}, content_length={len(doc.content) if doc.content else 0}, content_is_none={doc.content is None}")
                
                return None

            # 构建上下文
            contexts = []
            total_length = 0

            for doc in documents:
                logger.info(f"📄 处理文档 {doc.id}: filename={doc.filename}, content_length={len(doc.content) if doc.content else 0}")
                
                if doc.content:
                    doc_context = f"### 文档：{doc.title or doc.filename}\n{doc.content}\n"

                    # 检查长度限制
                    if total_length + len(doc_context) > max_length:
                        remaining = max_length - total_length
                        if remaining > 100:  # 至少保留100字符
                            doc_context = doc_context[:remaining] + "...\n"
                            contexts.append(doc_context)
                        break

                    contexts.append(doc_context)
                    total_length += len(doc_context)
                    logger.info(f"✅ 文档 {doc.id} 内容已添加到上下文，长度: {len(doc_context)}")
                else:
                    logger.warning(f"⚠️ 文档 {doc.id} 没有内容")

            context_result = "\n".join(contexts) if contexts else None
            logger.info(f"🎯 最终上下文长度: {len(context_result) if context_result else 0}")
            
            return context_result

        except Exception as e:
            logger.error(f"Error getting documents context: {str(e)}")
            return None

    async def _get_conversation_history(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """获取对话历史."""
        try:
            # 获取对话
            conversation = await crud_conversation.get(db, id=conversation_id)
            if not conversation or conversation.user_id != user_id:
                return []

            # 获取历史消息
            messages = await crud_message.get_by_conversation(
                db,
                conversation_id=conversation_id,
                limit=limit
            )

            # 转换为消息格式
            history = []
            for message in reversed(messages):  # 按时间顺序
                history.append({
                    "role": message.role,
                    "content": message.content
                })

            return history

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    async def _search_relevant_documents(
        self,
        db: AsyncSession,
        query: str,
        space_id: int,
        user_id: int,
        limit: int = 3
    ) -> list[Document]:
        """搜索相关文档."""
        try:
            # 使用向量搜索
            # 构建过滤条件
            filter_conditions = {
                "space_id": space_id,
                "user_id": user_id
            }

            search_results = await vector_service.search_documents(
                query=query,
                limit=limit,
                filter_conditions=filter_conditions
            )

            if not search_results:
                return []

            # 获取文档ID
            doc_ids = [result["document_id"] for result in search_results]

            # 查询文档
            stmt = select(Document).where(
                Document.id.in_(doc_ids),
                Document.user_id == user_id
            )
            result = await db.execute(stmt)
            documents = result.scalars().all()

            # 按相关性排序
            doc_map = {doc.id: doc for doc in documents}
            sorted_docs = []
            for search_result in search_results:
                doc_id = search_result["document_id"]
                if doc_id in doc_map:
                    sorted_docs.append(doc_map[doc_id])

            return sorted_docs

        except AttributeError as e:
            # 向量服务未初始化或不可用
            logger.warning(f"Vector service not available: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error searching relevant documents: {str(e)}")
            return []

    def _format_documents_context(self, documents: list[Document]) -> str:
        """格式化文档内容为上下文."""
        contexts = []

        for doc in documents:
            if doc.content:
                # 截取文档的关键部分
                content_preview = doc.content[:1500]
                if len(doc.content) > 1500:
                    content_preview += "..."

                contexts.append(
                    f"**{doc.title or doc.filename}**\n{content_preview}"
                )

        return "\n\n---\n\n".join(contexts)

    async def _save_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_message: dict[str, Any],
        assistant_response: str,
        model: str,
        document_ids: list[int] | None = None
    ) -> None:
        """保存消息到对话历史."""
        try:
            # 保存用户消息
            await crud_message.create(
                db,
                obj_in=MessageCreate(
                    conversation_id=conversation_id,
                    role=user_message.get("role", "user"),
                    content=user_message.get("content", ""),
                    model=None,
                    provider=None,
                    meta_data={"document_ids": document_ids} if document_ids else None,
                    attachments=None
                )
            )

            # 保存助手响应
            await crud_message.create(
                db,
                obj_in=MessageCreate(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=assistant_response,
                    model=model,
                    provider=self._get_provider_from_model(model),
                    meta_data={"referenced_documents": document_ids} if document_ids else None,
                    attachments=None
                )
            )

            # 更新对话的消息计数
            conversation = await crud_conversation.get(db, id=conversation_id)
            if conversation:
                conversation.message_count += 2
                await db.commit()

        except Exception as e:
            logger.error(f"Error saving messages: {str(e)}")
            await db.rollback()

    def _get_provider_from_model(self, model: str) -> str:
        """从模型名称推断提供商."""
        # 首先检查是否是OpenRouter格式的模型
        if "/" in model:
            # OpenRouter格式: provider/model
            parts = model.split("/", 1)
            if len(parts) == 2:
                provider = parts[0].lower()
                # 映射常见的OpenRouter提供商名称
                provider_map = {
                    "openai": "openai",
                    "anthropic": "anthropic",
                    "google": "google",
                    "meta-llama": "meta",
                    "perplexity": "perplexity",
                    "deepseek": "deepseek",
                    "openrouter": "openrouter",
                }
                return provider_map.get(provider, provider)

        # 兼容旧的推断逻辑
        model_lower = model.lower()
        if "gpt" in model_lower:
            return "openai"
        elif "claude" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower:
            return "google"
        elif "deepseek" in model_lower:
            return "deepseek"
        elif "llama" in model_lower or "sonar" in model_lower:
            return "perplexity"
        else:
            return "openrouter"  # 默认使用OpenRouter

    async def regenerate_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        message_id: int,
        user: User,
        model: str | None = None,
        temperature: float | None = None
    ) -> str:
        """重新生成指定消息."""
        try:
            # 获取消息
            message = await crud_message.get(db, id=message_id)
            if not message or message.conversation_id != conversation_id:
                raise ValueError("消息不存在")

            # 获取对话
            conversation = await crud_conversation.get(db, id=conversation_id)
            if not conversation or conversation.user_id != user.id:
                raise ValueError("无权访问此对话")

            # 获取该消息之前的所有消息作为上下文
            all_messages = await crud_message.get_by_conversation(
                db, conversation_id=conversation_id, limit=100
            )

            # 构建消息历史（到目标消息的前一条为止）
            messages: list[dict[str, Any]] = []
            for msg in reversed(all_messages):
                if msg.id == message_id:
                    break
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # 确保有上下文
            if not messages:
                raise ValueError("没有足够的上下文来重新生成")

            # 使用指定的模型或原模型
            use_model = model or message.model or conversation.model
            use_temperature = temperature if temperature is not None else 0.7

            # 重新生成
            new_response = await ai_service.chat(
                messages=messages,
                model=use_model,
                temperature=use_temperature,
                user=user
            )

            # 更新消息内容
            message.content = new_response
            message.model = use_model
            message.meta_data = message.meta_data or {}
            message.meta_data["regenerated"] = True
            message.meta_data["regenerated_at"] = datetime.now().isoformat()

            await db.commit()
            await db.refresh(message)

            return new_response

        except Exception as e:
            logger.error(f"Error regenerating message: {str(e)}")
            raise


# 全局聊天服务实例
chat_service = ChatService()
