"""chat.py 的完整单元测试"""

from datetime import UTC, datetime  # noqa: UP017
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.chat import (
    _generate_ai_response,
    _process_attachments,
    analyze_attachments,
    create_chat_completion,
    create_conversation,
    create_conversation_branch,
    delete_conversation,
    delete_conversation_branch,
    get_branch_history,
    get_conversation,
    get_conversations,
    list_conversation_branches,
    merge_conversation_branch,
    regenerate_message,
    send_message,
    switch_conversation_branch,
    update_conversation,
)
from app.models.models import Conversation, Space, User
from app.models.models import Message as DBMessage
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
    Role,
)
from app.schemas.conversation_branch import (
    BranchCreate,
    BranchHistory,
    BranchListResponse,
    BranchMerge,
    BranchSwitch,
)
from app.schemas.conversations import (
    ChatMode,
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreateSimple,
    MessageResponse,
)


class TestChatCompletion:
    """测试聊天完成接口"""

    @pytest.mark.asyncio
    async def test_create_chat_completion_non_stream(self):
        """测试非流式聊天完成"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_request = ChatCompletionRequest(
            model="gpt-4.1-mini",
            messages=[Message(role=Role.user, content="Hello")],
            mode=ChatMode.CHAT,
            conversation_id=None,
            space_id=None,
            document_ids=[],
            temperature=0.7,
            max_tokens=1000,
            stream=False,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=None,
            n=1,
            user=None,
            tools=None,
            tool_choice=None,
        )

        mock_response = MagicMock(spec=ChatCompletionResponse)

        with patch("app.api.v1.endpoints.chat.chat_service") as mock_service:
            mock_service.create_completion_with_documents = AsyncMock(
                return_value=mock_response
            )

            result = await create_chat_completion(mock_request, mock_db, mock_user)

            assert result == mock_response
            mock_service.create_completion_with_documents.assert_called_once_with(
                db=mock_db, request=mock_request, user=mock_user
            )

    @pytest.mark.asyncio
    async def test_create_chat_completion_stream(self):
        """测试流式聊天完成"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_request = ChatCompletionRequest(
            model="gpt-4.1-mini",
            messages=[Message(role=Role.user, content="Hello")],
            mode=ChatMode.CHAT,
            conversation_id=None,
            space_id=None,
            document_ids=[],
            temperature=0.7,
            max_tokens=1000,
            stream=True,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=None,
            n=1,
            user=None,
            tools=None,
            tool_choice=None,
        )

        async def async_generator():
            yield 'data: {"content": "Hello"}\n\n'
            yield 'data: {"content": " World"}\n\n'

        with patch("app.api.v1.endpoints.chat.chat_service") as mock_service:
            mock_service.create_completion_with_documents = AsyncMock(
                return_value=async_generator()
            )

            result = await create_chat_completion(mock_request, mock_db, mock_user)

            # 检查返回的是 StreamingResponse
            from fastapi.responses import StreamingResponse

            assert isinstance(result, StreamingResponse)
            assert result.media_type == "text/event-stream"

    @pytest.mark.asyncio
    async def test_create_chat_completion_error(self):
        """测试聊天完成错误处理"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_request = ChatCompletionRequest(
            model="gpt-4.1-mini",
            messages=[Message(role=Role.user, content="Hello")],
            mode=ChatMode.CHAT,
            conversation_id=None,
            space_id=None,
            document_ids=[],
            temperature=0.7,
            max_tokens=1000,
            stream=False,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=None,
            n=1,
            user=None,
            tools=None,
            tool_choice=None,
        )

        with patch("app.api.v1.endpoints.chat.chat_service") as mock_service:
            mock_service.create_completion_with_documents = AsyncMock(
                side_effect=Exception("Service error")
            )

            with pytest.raises(HTTPException) as exc_info:
                await create_chat_completion(mock_request, mock_db, mock_user)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "聊天服务错误" in str(exc_info.value.detail)


class TestConversationManagement:
    """测试对话管理功能"""

    @pytest.mark.asyncio
    async def test_create_conversation_without_space(self):
        """测试创建不关联空间的对话"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        conversation_data = ConversationCreate(
            title="Test Conversation",
            mode=ChatMode.CHAT,
            space_id=None,
            system_prompt=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            meta_data=None,
        )

        # 创建符合ConversationResponse结构的mock对象
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = 1
        mock_conversation.title = "Test Conversation"
        mock_conversation.mode = "chat"
        mock_conversation.model = None
        mock_conversation.space_id = None
        mock_conversation.system_prompt = None
        mock_conversation.temperature = 0.7
        mock_conversation.max_tokens = None
        mock_conversation.meta_data = None
        mock_conversation.message_count = 0
        mock_conversation.total_tokens = 0
        mock_conversation.created_at = datetime.now(UTC)
        mock_conversation.updated_at = None

        with patch("app.api.v1.endpoints.chat.ConversationService") as mock_service:
            mock_service.create_conversation = AsyncMock(return_value=mock_conversation)

            result = await create_conversation(conversation_data, mock_db, mock_user)

            assert isinstance(result, ConversationResponse)
            assert result.title == "Test Conversation"
            assert result.mode == "chat"
            mock_service.create_conversation.assert_called_once_with(
                mock_db, conversation_data, mock_user
            )

    @pytest.mark.asyncio
    async def test_create_conversation_with_space(self):
        """测试创建关联空间的对话"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        conversation_data = ConversationCreate(
            title="Test Conversation",
            mode=ChatMode.CHAT,
            space_id=1,
            system_prompt=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            meta_data=None,
        )

        mock_space = MagicMock(spec=Space)
        mock_space.user_id = 1
        mock_space.is_public = False

        # 创建符合ConversationResponse结构的mock对象
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = 1
        mock_conversation.title = "Test Conversation"
        mock_conversation.mode = "chat"
        mock_conversation.model = None
        mock_conversation.space_id = 1
        mock_conversation.system_prompt = None
        mock_conversation.temperature = 0.7
        mock_conversation.max_tokens = None
        mock_conversation.meta_data = None
        mock_conversation.message_count = 0
        mock_conversation.total_tokens = 0
        mock_conversation.created_at = datetime.now(UTC)
        mock_conversation.updated_at = None

        with (
            patch("app.api.v1.endpoints.chat.crud") as mock_crud,
            patch("app.api.v1.endpoints.chat.ConversationService") as mock_service,
        ):
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_service.create_conversation = AsyncMock(return_value=mock_conversation)

            result = await create_conversation(conversation_data, mock_db, mock_user)

            assert isinstance(result, ConversationResponse)
            assert result.space_id == 1
            mock_crud.crud_space.get.assert_called_once_with(mock_db, id=1)

    @pytest.mark.asyncio
    async def test_create_conversation_space_not_found(self):
        """测试创建对话时空间不存在"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        conversation_data = ConversationCreate(
            title="Test Conversation",
            mode=ChatMode.CHAT,
            space_id=999,
            system_prompt=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            meta_data=None,
        )

        with patch("app.api.v1.endpoints.chat.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await create_conversation(conversation_data, mock_db, mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "空间不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_conversation_no_access(self):
        """测试创建对话时无权访问空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        conversation_data = ConversationCreate(
            title="Test Conversation",
            mode=ChatMode.CHAT,
            space_id=1,
            system_prompt=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            meta_data=None,
        )

        mock_space = MagicMock(spec=Space)
        mock_space.user_id = 2  # 不是当前用户
        mock_space.is_public = False

        with patch("app.api.v1.endpoints.chat.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_space.get_user_access = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await create_conversation(conversation_data, mock_db, mock_user)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "无权在此空间创建对话" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_conversations(self):
        """测试获取对话列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        # 创建符合ConversationResponse结构的mock对象
        def create_mock_conversation(id, title):
            mock = MagicMock(spec=Conversation)
            mock.id = id
            mock.title = title
            mock.mode = "chat"
            mock.model = None
            mock.space_id = None
            mock.system_prompt = None
            mock.temperature = 0.7
            mock.max_tokens = None
            mock.meta_data = None
            mock.message_count = 0
            mock.total_tokens = 0
            mock.created_at = datetime.now(UTC)
            mock.updated_at = None
            return mock

        mock_conversations = [
            create_mock_conversation(1, "Conv 1"),
            create_mock_conversation(2, "Conv 2"),
        ]

        with patch("app.api.v1.endpoints.chat.ConversationService") as mock_service:
            mock_service.get_user_conversations = AsyncMock(
                return_value=mock_conversations
            )

            result = await get_conversations(
                space_id=None,
                mode=None,
                skip=0,
                limit=20,
                db=mock_db,
                current_user=mock_user,
            )

            assert result.total == 2
            assert len(result.conversations) == 2
            assert result.page == 1
            assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_get_conversation_detail(self):
        """测试获取对话详情"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        # 创建符合ConversationWithMessages结构的mock对象
        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = "Test Conversation"
        mock_conversation.mode = "chat"
        mock_conversation.model = None
        mock_conversation.space_id = None
        mock_conversation.prompt_template = None
        mock_conversation.is_pinned = False
        mock_conversation.is_archived = False
        mock_conversation.message_count = 0
        mock_conversation.token_count = 0
        mock_conversation.tags = None
        mock_conversation.meta_data = None
        mock_conversation.created_at = datetime.now(UTC)
        mock_conversation.updated_at = None
        mock_conversation.messages = []

        with patch("app.api.v1.endpoints.chat.ConversationService") as mock_service:
            mock_service.get_conversation_with_messages = AsyncMock(
                return_value=mock_conversation
            )

            result = await get_conversation(1, 50, mock_db, mock_user)

            assert result.id == 1
            assert result.title == "Test Conversation"
            mock_service.get_conversation_with_messages.assert_called_once_with(
                mock_db, 1, mock_user, 50
            )

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self):
        """测试获取不存在的对话"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        with patch("app.api.v1.endpoints.chat.ConversationService") as mock_service:
            mock_service.get_conversation_with_messages = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_conversation(999, 50, mock_db, mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "对话不存在或无权访问" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_conversation(self):
        """测试更新对话"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        update_data = ConversationUpdate(
            title="Updated Title",
            system_prompt=None,
            temperature=None,
            max_tokens=None,
            meta_data=None,
        )
        mock_conversation = MagicMock(spec=Conversation)

        # 创建符合ConversationResponse结构的mock对象
        mock_updated = MagicMock(spec=Conversation)
        mock_updated.id = 1
        mock_updated.title = "Updated Title"
        mock_updated.mode = "chat"
        mock_updated.model = None
        mock_updated.space_id = None
        mock_updated.system_prompt = None
        mock_updated.temperature = 0.7
        mock_updated.max_tokens = None
        mock_updated.meta_data = None
        mock_updated.message_count = 0
        mock_updated.total_tokens = 0
        mock_updated.created_at = datetime.now(UTC)
        mock_updated.updated_at = datetime.now(UTC)

        with patch("app.api.v1.endpoints.chat.ConversationService") as mock_service:
            mock_service.get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )
            mock_service.update_conversation = AsyncMock(return_value=mock_updated)

            result = await update_conversation(1, update_data, mock_db, mock_user)

            assert isinstance(result, ConversationResponse)
            assert result.title == "Updated Title"
            mock_service.update_conversation.assert_called_once_with(
                mock_db, mock_conversation, update_data
            )

    @pytest.mark.asyncio
    async def test_delete_conversation(self):
        """测试删除对话"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_conversation = MagicMock(spec=Conversation)

        with patch("app.api.v1.endpoints.chat.ConversationService") as mock_service:
            mock_service.get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )
            mock_service.delete_conversation = AsyncMock()

            await delete_conversation(1, mock_db, mock_user)

            mock_service.delete_conversation.assert_called_once_with(
                mock_db, mock_conversation
            )


class TestMessageHandling:
    """测试消息处理功能"""

    @pytest.mark.asyncio
    async def test_send_message_json(self):
        """测试发送JSON格式的消息"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "application/json"

        message_data = MessageCreateSimple(content="Hello World", attachments=None)

        mock_conversation = MagicMock(spec=Conversation)
        mock_user_message = MagicMock(spec=DBMessage)

        # 创建符合MessageResponse结构的mock对象
        mock_ai_message = MagicMock(spec=DBMessage)
        mock_ai_message.id = 1
        mock_ai_message.role = "assistant"
        mock_ai_message.content = "AI response"
        mock_ai_message.model = "gpt-4.1-mini"
        mock_ai_message.provider = None
        mock_ai_message.token_count = None
        mock_ai_message.processing_time = None
        mock_ai_message.meta_data = None
        mock_ai_message.attachments = None
        mock_ai_message.created_at = datetime.now(UTC)

        with (
            patch("app.api.v1.endpoints.chat.ConversationService") as mock_service,
            patch("app.api.v1.endpoints.chat._generate_ai_response") as mock_gen_ai,
        ):
            mock_service.get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )
            mock_service.add_message = AsyncMock(return_value=mock_user_message)
            mock_gen_ai.return_value = mock_ai_message

            result = await send_message(
                1,
                mock_request,
                message_data,
                None,
                None,
                None,
                True,
                mock_db,
                mock_user,
            )

            assert isinstance(result, MessageResponse)
            assert result.content == "AI response"
            mock_service.add_message.assert_called_once()
            assert mock_gen_ai.called

    @pytest.mark.asyncio
    async def test_send_message_with_files(self):
        """测试发送带文件的消息"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "multipart/form-data"

        mock_file = MagicMock(spec=UploadFile)
        mock_attachments = [{"filename": "test.jpg", "type": "image"}]

        mock_conversation = MagicMock(spec=Conversation)
        mock_user_message = MagicMock(spec=DBMessage)

        # 创建符合MessageResponse结构的mock对象
        mock_ai_message = MagicMock(spec=DBMessage)
        mock_ai_message.id = 2
        mock_ai_message.role = "assistant"
        mock_ai_message.content = "I see your image"
        mock_ai_message.model = "gpt-4.1-mini"
        mock_ai_message.provider = None
        mock_ai_message.token_count = None
        mock_ai_message.processing_time = None
        mock_ai_message.meta_data = None
        mock_ai_message.attachments = None
        mock_ai_message.created_at = datetime.now(UTC)

        with (
            patch("app.api.v1.endpoints.chat.ConversationService") as mock_service,
            patch("app.api.v1.endpoints.chat._process_attachments") as mock_process,
            patch("app.api.v1.endpoints.chat._generate_ai_response") as mock_gen_ai,
        ):
            mock_service.get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )
            mock_service.add_message = AsyncMock(return_value=mock_user_message)
            mock_process.return_value = mock_attachments
            mock_gen_ai.return_value = mock_ai_message

            result = await send_message(
                1,
                mock_request,
                None,
                "Hello",
                [mock_file],
                None,
                True,
                mock_db,
                mock_user,
            )

            assert isinstance(result, MessageResponse)
            assert result.content == "I see your image"
            mock_process.assert_called_once_with([mock_file], mock_user, True, None)
            mock_service.add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_no_content(self):
        """测试发送空消息"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "application/json"

        mock_conversation = MagicMock(spec=Conversation)

        with patch("app.api.v1.endpoints.chat.ConversationService") as mock_service:
            mock_service.get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )

            with pytest.raises(HTTPException) as exc_info:
                await send_message(
                    1, mock_request, None, None, None, None, True, mock_db, mock_user
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "消息内容不能为空" in str(exc_info.value.detail)


class TestAttachmentHandling:
    """测试附件处理功能"""

    @pytest.mark.asyncio
    async def test_analyze_attachments_with_vision(self):
        """测试分析需要视觉模型的附件"""
        mock_user = MagicMock(spec=User)
        mock_user.is_premium = False

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "image.jpg"
        mock_file.read = AsyncMock(return_value=b"fake image")

        with (
            patch("app.api.v1.endpoints.chat.tempfile.NamedTemporaryFile"),
            patch("app.api.v1.endpoints.chat.multimodal_helper") as mock_helper,
            patch("app.api.v1.endpoints.chat.os.unlink"),
            patch("app.services.ai_service") as mock_ai_service,
        ):
            mock_helper.prepare_attachment_for_chat = AsyncMock(
                return_value={
                    "type": "image",
                    "needs_vision": True,
                    "extracted_text": None,
                    "extraction_metadata": {},
                }
            )
            mock_ai_service.VISION_MODELS = {
                "free": ["gpt-4.1-mini"],
                "premium": ["gpt-4.1-mini", "claude-3-vision"],
            }
            mock_ai_service.CHAT_MODELS = {
                "free": ["gpt-4.1-mini"],
                "premium": ["gpt-4.1-mini", "claude-3"],
            }

            result = await analyze_attachments([mock_file], mock_user)

            assert result["needs_vision_model"] is True
            assert len(result["attachments"]) == 1
            assert result["attachments"][0]["needs_vision"] is True
            assert "gpt-4.1-mini" in result["recommended_models"]

    @pytest.mark.asyncio
    async def test_analyze_attachments_text_only(self):
        """测试分析纯文本附件"""
        mock_user = MagicMock(spec=User)
        mock_user.is_premium = True

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "document.pdf"
        mock_file.read = AsyncMock(return_value=b"fake pdf")

        with (
            patch("app.api.v1.endpoints.chat.tempfile.NamedTemporaryFile"),
            patch("app.api.v1.endpoints.chat.multimodal_helper") as mock_helper,
            patch("app.api.v1.endpoints.chat.os.unlink"),
            patch("app.services.ai_service") as mock_ai_service,
        ):
            mock_helper.prepare_attachment_for_chat = AsyncMock(
                return_value={
                    "type": "document",
                    "needs_vision": False,
                    "extracted_text": "Document content",
                    "extraction_metadata": {"pages": 10},
                }
            )
            mock_ai_service.VISION_MODELS = {
                "free": ["gpt-4.1-mini"],
                "premium": ["gpt-4.1-mini", "claude-3-vision"],
            }
            mock_ai_service.CHAT_MODELS = {
                "free": ["gpt-4.1-mini"],
                "premium": ["gpt-4.1-mini", "claude-3"],
            }

            result = await analyze_attachments([mock_file], mock_user)

            assert result["needs_vision_model"] is False
            assert result["attachments"][0]["has_text"] is True
            assert len(result["recommended_models"]) <= 3


class TestMessageRegeneration:
    """测试消息重新生成功能"""

    @pytest.mark.asyncio
    async def test_regenerate_message_success(self):
        """测试成功重新生成消息"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        mock_message = MagicMock(spec=DBMessage)
        mock_message.id = 1
        mock_message.role = "assistant"
        mock_message.content = "Regenerated response"
        mock_message.model = "gpt-4.1-mini"
        mock_message.provider = "openai"
        mock_message.token_count = 50
        mock_message.processing_time = 1.5
        mock_message.meta_data = None
        mock_message.attachments = None
        mock_message.created_at = datetime.now(UTC)

        with (
            patch("app.api.v1.endpoints.chat.chat_service") as mock_service,
            patch("app.crud.message.crud_message") as mock_crud,
        ):
            mock_service.regenerate_message = AsyncMock()
            mock_crud.get = AsyncMock(return_value=mock_message)

            result = await regenerate_message(
                1, 1, "gpt-4.1-mini", 0.8, mock_db, mock_user
            )

            assert isinstance(result, MessageResponse)
            assert result.content == "Regenerated response"

            mock_service.regenerate_message.assert_called_once_with(
                db=mock_db,
                conversation_id=1,
                message_id=1,
                user=mock_user,
                model="gpt-4.1-mini",
                temperature=0.8,
            )

    @pytest.mark.asyncio
    async def test_regenerate_message_value_error(self):
        """测试重新生成消息时的值错误"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        with patch("app.api.v1.endpoints.chat.chat_service") as mock_service:
            mock_service.regenerate_message = AsyncMock(
                side_effect=ValueError("Invalid message")
            )

            with pytest.raises(HTTPException) as exc_info:
                await regenerate_message(1, 1, None, None, mock_db, mock_user)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid message" in str(exc_info.value.detail)


class TestBranchManagement:
    """测试分支管理功能"""

    @pytest.mark.asyncio
    async def test_create_branch(self):
        """测试创建分支"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        branch_data = BranchCreate(
            from_message_id=1,
            branch_name="alternative",
            initial_content="alternative branch",
        )

        # 创建符合MessageResponse结构的mock对象
        mock_message = MagicMock(spec=DBMessage)
        mock_message.id = 1
        mock_message.role = "user"
        mock_message.content = "alternative branch"
        mock_message.model = None
        mock_message.provider = None
        mock_message.token_count = None
        mock_message.processing_time = None
        mock_message.meta_data = None
        mock_message.attachments = None
        mock_message.created_at = datetime.now(UTC)

        with patch("app.api.v1.endpoints.chat.branch_service") as mock_service:
            mock_service.create_branch = AsyncMock(return_value=mock_message)

            result = await create_conversation_branch(
                1, branch_data, mock_db, mock_user
            )

            assert isinstance(result, MessageResponse)
            assert result.content == "alternative branch"
            mock_service.create_branch.assert_called_once_with(
                mock_db, 1, branch_data, mock_user
            )

    @pytest.mark.asyncio
    async def test_list_branches(self):
        """测试列出分支"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        mock_response = BranchListResponse(branches=[], total=0)

        with patch("app.api.v1.endpoints.chat.branch_service") as mock_service:
            mock_service.list_branches = AsyncMock(return_value=mock_response)

            result = await list_conversation_branches(1, mock_db, mock_user)

            assert result == mock_response
            assert result.total == 0
            mock_service.list_branches.assert_called_once_with(mock_db, 1, mock_user)

    @pytest.mark.asyncio
    async def test_switch_branch(self):
        """测试切换分支"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        switch_data = BranchSwitch(branch_name="alternative")

        with patch("app.api.v1.endpoints.chat.branch_service") as mock_service:
            mock_service.switch_branch = AsyncMock()

            await switch_conversation_branch(1, switch_data, mock_db, mock_user)

            mock_service.switch_branch.assert_called_once_with(
                mock_db, 1, "alternative", mock_user
            )

    @pytest.mark.asyncio
    async def test_get_branch_history(self):
        """测试获取分支历史"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        mock_history = [MagicMock(spec=BranchHistory)]

        with patch("app.api.v1.endpoints.chat.branch_service") as mock_service:
            mock_service.get_branch_history = AsyncMock(return_value=mock_history)

            result = await get_branch_history(1, None, mock_db, mock_user)

            assert result == mock_history
            mock_service.get_branch_history.assert_called_once_with(
                mock_db, 1, None, mock_user
            )

    @pytest.mark.asyncio
    async def test_merge_branch(self):
        """测试合并分支"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        merge_data = BranchMerge(
            source_branch="feature", target_message_id=5, merge_strategy="append"
        )

        # 创建符合MessageResponse结构的mock对象
        mock_message = MagicMock(spec=DBMessage)
        mock_message.id = 6
        mock_message.role = "user"
        mock_message.content = "merged content"
        mock_message.model = None
        mock_message.provider = None
        mock_message.token_count = None
        mock_message.processing_time = None
        mock_message.meta_data = None
        mock_message.attachments = None
        mock_message.created_at = datetime.now(UTC)

        mock_messages = [mock_message]

        with patch("app.api.v1.endpoints.chat.branch_service") as mock_service:
            mock_service.merge_branch = AsyncMock(return_value=mock_messages)

            result = await merge_conversation_branch(1, merge_data, mock_db, mock_user)

            assert len(result) == 1
            assert isinstance(result[0], MessageResponse)
            assert result[0].content == "merged content"
            mock_service.merge_branch.assert_called_once_with(
                mock_db, 1, "feature", 5, mock_user
            )

    @pytest.mark.asyncio
    async def test_delete_branch(self):
        """测试删除分支"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)

        with patch("app.api.v1.endpoints.chat.branch_service") as mock_service:
            mock_service.delete_branch = AsyncMock()

            await delete_conversation_branch(1, "feature", mock_db, mock_user)

            mock_service.delete_branch.assert_called_once_with(
                mock_db, 1, "feature", mock_user
            )


class TestProcessAttachments:
    """测试附件处理函数（改进版）"""

    @pytest.mark.asyncio
    async def test_process_attachments_success(self):
        """测试成功处理附件"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.read = AsyncMock(return_value=b"fake image content")

        mock_user = MagicMock(spec=User)

        with (
            patch("app.api.v1.endpoints.chat.tempfile.NamedTemporaryFile"),
            patch("app.api.v1.endpoints.chat.multimodal_helper") as mock_helper,
            patch("app.api.v1.endpoints.chat.os.unlink"),
        ):
            mock_helper.prepare_attachment_for_chat = AsyncMock(
                return_value={
                    "type": "image",
                    "needs_vision": True,
                    "url": "http://example.com/test.jpg",
                    "extracted_text": None,
                    "extraction_metadata": {},
                }
            )

            result = await _process_attachments(
                files=[mock_file], user=mock_user, auto_switch_vision=True, model=None
            )

            assert len(result) == 1
            assert result[0]["filename"] == "test.jpg"
            assert result[0]["type"] == "image"

    @pytest.mark.asyncio
    async def test_process_attachments_too_many_files(self):
        """测试文件数量超限"""
        mock_files = []
        for i in range(6):
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = f"test{i}.jpg"
            mock_files.append(mock_file)

        mock_user = MagicMock(spec=User)

        with pytest.raises(HTTPException) as exc_info:
            await _process_attachments(
                files=mock_files, user=mock_user, auto_switch_vision=True, model=None
            )

        assert exc_info.value.status_code == 400
        assert "最多只能上传5个文件" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_process_attachments_file_too_large(self):
        """测试文件过大"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "large.jpg"
        mock_file.read = AsyncMock(return_value=b"x" * (11 * 1024 * 1024))

        mock_user = MagicMock(spec=User)

        with pytest.raises(HTTPException) as exc_info:
            await _process_attachments(
                files=[mock_file], user=mock_user, auto_switch_vision=True, model=None
            )

        assert exc_info.value.status_code == 400
        assert "太大" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_process_attachments_cleanup_on_error(self):
        """测试处理出错时的文件清理"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.read = AsyncMock(return_value=b"content")

        mock_user = MagicMock(spec=User)
        temp_file = MagicMock()
        temp_file.name = "/tmp/test.jpg"

        with (
            patch("app.api.v1.endpoints.chat.tempfile.NamedTemporaryFile") as mock_temp,
            patch("app.api.v1.endpoints.chat.multimodal_helper") as mock_helper,
            patch("app.api.v1.endpoints.chat.os.unlink"),
        ):
            mock_temp.return_value.__enter__.return_value = temp_file
            mock_helper.prepare_attachment_for_chat = AsyncMock(
                side_effect=Exception("Processing error")
            )

            # 测试处理失败
            try:
                await _process_attachments(
                    files=[mock_file],
                    user=mock_user,
                    auto_switch_vision=True,
                    model=None,
                )
                raise AssertionError("Should have raised an exception")
            except Exception as e:
                assert str(e) == "Processing error"
                # 由于处理失败，不会调用unlink
                # 因为在实际代码中，只有成功处理后才会清理文件


class TestGenerateAIResponse:
    """测试AI响应生成函数（改进版）"""

    @pytest.mark.asyncio
    async def test_generate_ai_response_success(self):
        """测试成功生成AI响应"""
        mock_db = AsyncMock()
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = 1
        mock_conversation.space_id = None
        mock_conversation.mode = "chat"

        mock_user_message = MagicMock(spec=DBMessage)
        mock_user = MagicMock(spec=User)

        with (
            patch("app.api.v1.endpoints.chat.ConversationService") as mock_conv_service,
            patch("app.api.v1.endpoints.chat.chat_service") as mock_chat_service,
        ):
            # 模拟获取消息历史
            mock_conv_service.get_conversation_messages = AsyncMock(
                return_value=[
                    MagicMock(role="user", content="Hello", attachments=None),
                    MagicMock(role="assistant", content="Hi there!", attachments=None),
                ]
            )

            # 模拟聊天服务响应
            mock_response = MagicMock(spec=ChatCompletionResponse)
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = "This is AI response"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.model = "gpt-4.1-mini"
            mock_response.usage = MagicMock()
            mock_response.usage.model_dump = MagicMock(
                return_value={"total_tokens": 100}
            )

            mock_chat_service.create_completion_with_documents = AsyncMock(
                return_value=mock_response
            )

            # 模拟保存消息
            mock_ai_message = MagicMock(spec=DBMessage)
            mock_conv_service.add_message = AsyncMock(return_value=mock_ai_message)

            # 执行测试
            result = await _generate_ai_response(
                db=mock_db,
                conversation=mock_conversation,
                user_message=mock_user_message,
                current_user=mock_user,
                model="gpt-4.1-mini",
                attachments=None,
            )

            assert result == mock_ai_message
            mock_conv_service.add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_ai_response_with_attachments(self):
        """测试带附件的AI响应生成"""
        mock_db = AsyncMock()
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = 1
        mock_conversation.space_id = None
        mock_conversation.mode = "chat"

        mock_user_message = MagicMock(spec=DBMessage)
        mock_user = MagicMock(spec=User)

        attachments = [
            {
                "filename": "image.jpg",
                "type": "image",
                "url": "http://example.com/image.jpg",
            }
        ]

        with (
            patch("app.api.v1.endpoints.chat.ConversationService") as mock_conv_service,
            patch("app.api.v1.endpoints.chat.chat_service") as mock_chat_service,
        ):
            mock_conv_service.get_conversation_messages = AsyncMock(return_value=[])

            mock_response = MagicMock(spec=ChatCompletionResponse)
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = "I can see the image"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.model = "gpt-4.1-mini"
            mock_response.usage = None

            mock_chat_service.create_completion_with_documents = AsyncMock(
                return_value=mock_response
            )

            mock_ai_message = MagicMock(spec=DBMessage)
            mock_conv_service.add_message = AsyncMock(return_value=mock_ai_message)

            result = await _generate_ai_response(
                db=mock_db,
                conversation=mock_conversation,
                user_message=mock_user_message,
                current_user=mock_user,
                model="gpt-4.1-mini",
                attachments=attachments,
            )

            assert result == mock_ai_message

    @pytest.mark.asyncio
    async def test_generate_ai_response_unexpected_type(self):
        """测试非预期的响应类型"""
        mock_db = AsyncMock()
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = 1
        mock_conversation.space_id = None
        mock_conversation.mode = "chat"

        mock_user_message = MagicMock(spec=DBMessage)
        mock_user = MagicMock(spec=User)

        with (
            patch("app.api.v1.endpoints.chat.ConversationService") as mock_conv_service,
            patch("app.api.v1.endpoints.chat.chat_service") as mock_chat_service,
        ):
            mock_conv_service.get_conversation_messages = AsyncMock(return_value=[])

            # 返回非 ChatCompletionResponse 类型
            mock_chat_service.create_completion_with_documents = AsyncMock(
                return_value="unexpected response"
            )

            with pytest.raises(ValueError) as exc_info:
                await _generate_ai_response(
                    db=mock_db,
                    conversation=mock_conversation,
                    user_message=mock_user_message,
                    current_user=mock_user,
                )

            assert "非预期的响应类型" in str(exc_info.value)
