"""Unit tests for chat service."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Document, User
from app.schemas.chat import ChatCompletionRequest, Role
from app.services.chat_service import ChatService


@pytest.fixture
def chat_service():
    """创建测试用的Chat Service."""
    return ChatService()


@pytest.fixture
def mock_user():
    """创建模拟用户."""
    user = Mock(spec=User)
    user.id = 1
    user.is_premium = True
    return user


@pytest.fixture
def mock_db():
    """创建模拟数据库会话."""
    return Mock(spec=AsyncSession)


@pytest.fixture
def sample_request():
    """创建示例请求."""
    return ChatCompletionRequest.model_validate({
        "model": "openrouter/auto",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.7,
        "stream": False
    })


class TestCreateCompletion:
    """测试创建聊天完成功能."""

    @pytest.mark.asyncio
    async def test_basic_completion(self, chat_service, mock_db, mock_user, sample_request):
        """测试基础聊天完成."""
        # Mock AI service response
        with patch('app.services.chat_service.ai_service') as mock_ai_service:
            mock_ai_service.chat = AsyncMock(return_value="I'm doing well, thank you!")

            response = await chat_service.create_completion_with_documents(
                db=mock_db,
                request=sample_request,
                user=mock_user
            )

            # 验证响应
            assert response.model == "openrouter/auto"
            assert len(response.choices) == 1
            assert response.choices[0].message.content == "I'm doing well, thank you!"
            assert response.choices[0].message.role == Role.assistant

            # 验证AI service被调用
            mock_ai_service.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_completion_with_documents(self, chat_service, mock_db, mock_user):
        """测试带文档上下文的聊天完成."""
        # 创建带文档ID的请求
        request = ChatCompletionRequest.model_validate({
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "What's in these documents?"}],
            "document_ids": [1, 2],
            "stream": False
        })

        # Mock文档查询
        mock_doc1 = Mock(spec=Document)
        mock_doc1.id = 1
        mock_doc1.title = "Document 1"
        mock_doc1.content = "This is document 1 content"
        mock_doc1.filename = "doc1.pdf"

        mock_doc2 = Mock(spec=Document)
        mock_doc2.id = 2
        mock_doc2.title = "Document 2"
        mock_doc2.content = "This is document 2 content"
        mock_doc2.filename = "doc2.pdf"

        # Mock数据库查询
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_doc1, mock_doc2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock AI service
        with patch('app.services.chat_service.ai_service') as mock_ai_service:
            mock_ai_service.chat = AsyncMock(return_value="The documents contain...")

            await chat_service.create_completion_with_documents(
                db=mock_db,
                request=request,
                user=mock_user
            )

            # 验证文档被查询
            mock_db.execute.assert_called_once()

            # 验证AI service调用包含文档上下文
            ai_call_args = mock_ai_service.chat.call_args
            messages = ai_call_args[1]['messages']

            # 应该有系统消息包含文档内容
            has_doc_context = any(
                msg.get('role') == 'system' and '文档内容' in msg.get('content', '')
                for msg in messages
            )
            assert has_doc_context

    @pytest.mark.asyncio
    async def test_completion_with_conversation_history(self, chat_service, mock_db, mock_user):
        """测试带对话历史的聊天完成."""
        # 创建带对话ID的请求
        request = ChatCompletionRequest.model_validate({
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "Continue our discussion"}],
            "conversation_id": 123,
            "stream": False
        })

        # Mock对话和历史消息
        mock_conversation = Mock()
        mock_conversation.id = 123
        mock_conversation.user_id = 1

        # Mock历史消息
        mock_message1 = Mock()
        mock_message1.role = "user"
        mock_message1.content = "Previous question"

        mock_message2 = Mock()
        mock_message2.role = "assistant"
        mock_message2.content = "Previous answer"

        # Mock CRUD操作
        with patch('app.services.chat_service.crud_conversation') as mock_crud_conv:
            with patch('app.services.chat_service.crud_message') as mock_crud_msg:
                mock_crud_conv.get = AsyncMock(return_value=mock_conversation)
                mock_crud_msg.get_by_conversation = AsyncMock(
                    return_value=[mock_message2, mock_message1]  # 反向顺序
                )
                mock_crud_msg.create = AsyncMock()

                # Mock AI service
                with patch('app.services.chat_service.ai_service') as mock_ai_service:
                    mock_ai_service.chat = AsyncMock(return_value="Continuing...")

                    await chat_service.create_completion_with_documents(
                        db=mock_db,
                        request=request,
                        user=mock_user
                    )

                    # 验证历史被加载
                    mock_crud_msg.get_by_conversation.assert_called_once_with(
                        mock_db,
                        conversation_id=123,
                        limit=20
                    )

                    # 验证消息被保存
                    assert mock_crud_msg.create.call_count == 2  # 用户消息和AI响应


class TestStreamCompletion:
    """测试流式响应功能."""

    @pytest.mark.asyncio
    async def test_stream_completion(self, chat_service, mock_db, mock_user):
        """测试流式聊天完成."""
        request = ChatCompletionRequest.model_validate({
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True
        })

        # Mock流式响应
        async def mock_stream(*args, **kwargs):
            _ = args, kwargs  # 避免未使用参数警告
            yield "Hello"
            yield " there"
            yield "!"

        with patch('app.services.chat_service.ai_service') as mock_ai_service:
            mock_ai_service.stream_chat = mock_stream

            # 收集流式响应
            chunks = []
            async for chunk in await chat_service.create_completion_with_documents(
                db=mock_db,
                request=request,
                user=mock_user
            ):
                chunks.append(chunk)

            # 验证SSE格式
            assert len(chunks) == 5  # 3个内容块 + 1个结束块 + 1个[DONE]

            # 验证第一个块
            first_chunk = json.loads(chunks[0].replace("data: ", ""))
            assert first_chunk["choices"][0]["delta"]["content"] == "Hello"

            # 验证结束
            assert chunks[-1] == "data: [DONE]\n\n"


class TestSpaceVectorSearch:
    """测试Space内向量搜索功能."""

    @pytest.mark.asyncio
    async def test_space_vector_search(self, chat_service, mock_db, mock_user):
        """测试Space内的向量搜索."""
        request = ChatCompletionRequest.model_validate({
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "Find related content"}],
            "space_id": 456,
            "stream": False
        })

        # Mock向量搜索结果
        search_results = [
            {"document_id": 1, "score": 0.9},
            {"document_id": 2, "score": 0.8}
        ]

        # Mock文档
        mock_doc1 = Mock(spec=Document)
        mock_doc1.id = 1
        mock_doc1.title = "Related Doc 1"
        mock_doc1.content = "Related content 1" * 100  # 长内容
        mock_doc1.filename = "related1.pdf"

        # Mock数据库查询
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_doc1]
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.chat_service.vector_service') as mock_vector:
            mock_vector.search_documents = AsyncMock(return_value=search_results)

            with patch('app.services.chat_service.ai_service') as mock_ai_service:
                mock_ai_service.chat = AsyncMock(return_value="Based on Space content...")

                await chat_service.create_completion_with_documents(
                    db=mock_db,
                    request=request,
                    user=mock_user
                )

                # 验证向量搜索被调用
                mock_vector.search_documents.assert_called_once_with(
                    query="Find related content",
                    limit=3,
                    filter_conditions={"space_id": 456, "user_id": 1}
                )


class TestRegenerateMessage:
    """测试重新生成消息功能."""

    @pytest.mark.asyncio
    async def test_regenerate_message(self, chat_service, mock_db, mock_user):
        """测试重新生成消息."""
        # Mock消息
        mock_message = Mock()
        mock_message.id = 789
        mock_message.conversation_id = 123
        mock_message.role = "assistant"
        mock_message.content = "Old response"
        mock_message.model = "old-model"
        mock_message.meta_data = {}

        # Mock对话
        mock_conversation = Mock()
        mock_conversation.id = 123
        mock_conversation.user_id = 1
        mock_conversation.model = "default-model"

        # Mock历史消息（注意：get_by_conversation返回的顺序是最新的在前）
        mock_history = [
            mock_message,  # 要重新生成的消息（最新）
            Mock(id=788, role="assistant", content="Answer"),
            Mock(id=787, role="user", content="Question")  # 最旧
        ]

        with patch('app.services.chat_service.crud_message') as mock_crud_msg:
            with patch('app.services.chat_service.crud_conversation') as mock_crud_conv:
                mock_crud_msg.get = AsyncMock(return_value=mock_message)
                mock_crud_conv.get = AsyncMock(return_value=mock_conversation)
                mock_crud_msg.get_by_conversation = AsyncMock(return_value=mock_history)

                with patch('app.services.chat_service.ai_service') as mock_ai_service:
                    mock_ai_service.chat = AsyncMock(return_value="New improved response")

                    # Mock数据库操作
                    mock_db.commit = AsyncMock()
                    mock_db.refresh = AsyncMock()

                    result = await chat_service.regenerate_message(
                        db=mock_db,
                        conversation_id=123,
                        message_id=789,
                        user=mock_user,
                        model="new-model",
                        temperature=0.8
                    )

                    assert result == "New improved response"
                    assert mock_message.content == "New improved response"
                    assert mock_message.model == "new-model"
                    assert mock_message.meta_data["regenerated"] is True


class TestHelperMethods:
    """测试辅助方法."""

    def test_get_provider_from_model(self, chat_service):
        """测试模型提供商推断."""
        # OpenRouter格式
        assert chat_service._get_provider_from_model("openai/gpt-4") == "openai"
        assert chat_service._get_provider_from_model("anthropic/claude-3") == "anthropic"
        assert chat_service._get_provider_from_model("perplexity/sonar") == "perplexity"

        # 旧格式兼容
        assert chat_service._get_provider_from_model("gpt-3.5-turbo") == "openai"
        assert chat_service._get_provider_from_model("claude-2") == "anthropic"
        assert chat_service._get_provider_from_model("gemini-pro") == "google"

        # 默认
        assert chat_service._get_provider_from_model("unknown-model") == "openrouter"

    def test_format_documents_context(self, chat_service):
        """测试文档格式化."""
        # 创建模拟文档
        doc1 = Mock()
        doc1.title = "Test Doc 1"
        doc1.filename = "test1.pdf"
        doc1.content = "Short content"

        doc2 = Mock()
        doc2.title = None
        doc2.filename = "test2.pdf"
        doc2.content = "Very long content " * 200  # 超过1500字符

        context = chat_service._format_documents_context([doc1, doc2])

        assert "Test Doc 1" in context
        assert "Short content" in context
        assert "test2.pdf" in context
        assert "..." in context  # 长内容被截断


class TestErrorHandling:
    """测试错误处理."""

    @pytest.mark.asyncio
    async def test_vector_service_unavailable(self, chat_service, mock_db, mock_user):
        """测试向量服务不可用时的处理."""
        request = ChatCompletionRequest.model_validate({
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "Search something"}],
            "space_id": 123,
            "stream": False
        })

        # Mock向量服务抛出AttributeError
        with patch('app.services.chat_service.vector_service') as mock_vector:
            mock_vector.search_documents = AsyncMock(
                side_effect=AttributeError("Vector service not initialized")
            )

            with patch('app.services.chat_service.ai_service') as mock_ai_service:
                mock_ai_service.chat = AsyncMock(return_value="Response without vector search")

                # 应该继续工作，只是没有向量搜索结果
                response = await chat_service.create_completion_with_documents(
                    db=mock_db,
                    request=request,
                    user=mock_user
                )

                assert response.choices[0].message.content == "Response without vector search"

    @pytest.mark.asyncio
    async def test_stream_error_handling(self, chat_service, mock_db, mock_user):
        """测试流式响应错误处理."""
        request = ChatCompletionRequest.model_validate({
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True
        })

        # Mock流式响应抛出错误
        async def mock_stream_error(*args, **kwargs):
            _ = args, kwargs  # 避免未使用参数警告
            yield "Start"
            raise Exception("Stream error")

        with patch('app.services.chat_service.ai_service') as mock_ai_service:
            mock_ai_service.stream_chat = mock_stream_error

            chunks = []
            async for chunk in await chat_service.create_completion_with_documents(
                db=mock_db,
                request=request,
                user=mock_user
            ):
                chunks.append(chunk)

            # 应该包含错误消息
            error_chunk = None
            for chunk in chunks:
                if "error" in chunk:
                    error_chunk = json.loads(chunk.replace("data: ", ""))
                    break

            assert error_chunk is not None
            assert error_chunk["error"]["message"] == "Stream error"

    @pytest.mark.asyncio
    async def test_get_documents_context_no_documents(self, chat_service, mock_db):
        """测试获取文档上下文时没有文档的情况."""
        # Mock空结果
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        context = await chat_service._get_documents_context(
            mock_db, [1, 2], user_id=1
        )

        assert context is None

    @pytest.mark.asyncio
    async def test_get_documents_context_exception(self, chat_service, mock_db):
        """测试获取文档上下文时的异常处理."""
        # Mock数据库异常
        mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

        context = await chat_service._get_documents_context(
            mock_db, [1], user_id=1
        )

        assert context is None

    @pytest.mark.asyncio
    async def test_save_messages_exception(self, chat_service, mock_db):
        """测试保存消息时的异常处理."""
        with patch('app.services.chat_service.crud_message.create') as mock_create:
            # Mock创建消息时异常
            mock_create.side_effect = Exception("Save error")
            mock_db.rollback = AsyncMock()

            # 应该捕获异常，不抛出
            await chat_service._save_messages(
                mock_db,
                conversation_id=1,
                user_message={"role": "user", "content": "Test"},
                assistant_response="Response",
                model="gpt-4"
            )

            # 应该回滚
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_message_not_found(self, chat_service, mock_db, mock_user):
        """测试重新生成不存在的消息."""
        with patch('app.services.chat_service.crud_message.get') as mock_get:
            # 消息不存在
            mock_get.return_value = None

            with pytest.raises(ValueError, match="消息不存在"):
                await chat_service.regenerate_message(
                    mock_db,
                    conversation_id=1,
                    message_id=999,
                    user=mock_user
                )

    @pytest.mark.asyncio
    async def test_create_completion_exception(self, chat_service, mock_db, mock_user, sample_request):
        """测试创建完成时的异常处理."""
        with patch('app.services.chat_service.ai_service.chat') as mock_chat:
            # Mock AI服务异常
            mock_chat.side_effect = Exception("AI error")

            with pytest.raises(Exception, match="AI error"):
                await chat_service.create_completion_with_documents(
                    mock_db, sample_request, mock_user
                )
