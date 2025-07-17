"""Unit tests for Conversation Service."""

from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Conversation, Message, Space, User
from app.schemas.conversations import ChatMode, ConversationCreate, ConversationUpdate
from app.services.conversation_service import ConversationService


@pytest.fixture
def mock_db():
    """创建模拟数据库会话."""
    return Mock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """创建模拟用户."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_conversation():
    """创建模拟对话."""
    conversation = Mock(spec=Conversation)
    conversation.id = 1
    conversation.user_id = 1
    conversation.title = "Test Conversation"
    conversation.mode = "chat"
    conversation.space_id = None
    conversation.message_count = 0
    conversation.total_tokens = 0
    return conversation


@pytest.fixture
def mock_message():
    """创建模拟消息."""
    message = Mock(spec=Message)
    message.id = 1
    message.conversation_id = 1
    message.role = "user"
    message.content = "Test message"
    message.branch_name = "main"
    message.parent_message_id = None
    message.is_active_branch = True
    return message


class TestCreateConversation:
    """测试创建对话功能."""

    @pytest.mark.asyncio
    async def test_create_conversation_success(self, mock_db, mock_user, mock_conversation):
        """测试成功创建对话."""
        # Mock CRUD
        from app import crud
        crud.crud_conversation.create = AsyncMock(return_value=mock_conversation)

        # 创建请求数据
        conversation_data = ConversationCreate(
            title="New Conversation",
            mode=ChatMode.CHAT,
            space_id=None,
            system_prompt=None,
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=None,
            meta_data={}
        )

        # 调用服务
        result = await ConversationService.create_conversation(
            mock_db, conversation_data, mock_user
        )

        # 验证
        assert result.id == 1
        assert result.title == "Test Conversation"
        crud.crud_conversation.create.assert_called_once_with(
            mock_db, obj_in=conversation_data, user_id=1
        )


class TestGetUserConversations:
    """测试获取用户对话列表功能."""

    @pytest.mark.asyncio
    async def test_get_user_conversations(self, mock_db, mock_user):
        """测试获取用户对话列表."""
        # Mock CRUD
        from app import crud
        mock_conversations = [Mock(spec=Conversation) for _ in range(3)]
        crud.crud_conversation.get_user_conversations = AsyncMock(
            return_value=mock_conversations
        )

        # 调用服务
        result = await ConversationService.get_user_conversations(
            mock_db, mock_user, space_id=None, mode="chat", skip=0, limit=20
        )

        # 验证
        assert len(result) == 3
        crud.crud_conversation.get_user_conversations.assert_called_once_with(
            mock_db,
            user_id=1,
            space_id=None,
            mode="chat",
            skip=0,
            limit=20
        )


class TestGetConversationById:
    """测试根据ID获取对话功能."""

    @pytest.mark.asyncio
    async def test_get_own_conversation(self, mock_db, mock_user, mock_conversation):
        """测试获取自己的对话."""
        # Mock CRUD
        from app import crud
        crud.crud_conversation.get = AsyncMock(return_value=mock_conversation)

        # 调用服务
        result = await ConversationService.get_conversation_by_id(
            mock_db, conversation_id=1, user=mock_user
        )

        # 验证
        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_public_space_conversation(self, mock_db, mock_user):
        """测试获取公共空间的对话."""
        # Mock对话和空间
        conversation = Mock(spec=Conversation)
        conversation.id = 2
        conversation.user_id = 2  # 其他用户
        conversation.space_id = 10

        space = Mock(spec=Space)
        space.id = 10
        space.is_public = True

        # Mock CRUD
        from app import crud
        crud.crud_conversation.get = AsyncMock(return_value=conversation)
        crud.crud_space.get = AsyncMock(return_value=space)

        # 调用服务
        result = await ConversationService.get_conversation_by_id(
            mock_db, conversation_id=2, user=mock_user
        )

        # 验证
        assert result is not None
        assert result.id == 2

    @pytest.mark.asyncio
    async def test_get_conversation_with_access(self, mock_db, mock_user):
        """测试获取有协作权限的对话."""
        # Mock对话
        conversation = Mock(spec=Conversation)
        conversation.id = 3
        conversation.user_id = 2  # 其他用户
        conversation.space_id = 20

        space = Mock(spec=Space)
        space.id = 20
        space.is_public = False

        # Mock访问权限
        access = Mock()

        # Mock CRUD
        from app import crud
        crud.crud_conversation.get = AsyncMock(return_value=conversation)
        crud.crud_space.get = AsyncMock(return_value=space)
        crud.crud_space.get_user_access = AsyncMock(return_value=access)

        # 调用服务
        result = await ConversationService.get_conversation_by_id(
            mock_db, conversation_id=3, user=mock_user
        )

        # 验证
        assert result is not None
        assert result.id == 3

    @pytest.mark.asyncio
    async def test_get_conversation_no_access(self, mock_db, mock_user):
        """测试无权限访问对话."""
        # Mock对话
        conversation = Mock(spec=Conversation)
        conversation.id = 4
        conversation.user_id = 2  # 其他用户
        conversation.space_id = None

        # Mock CRUD
        from app import crud
        crud.crud_conversation.get = AsyncMock(return_value=conversation)

        # 调用服务
        result = await ConversationService.get_conversation_by_id(
            mock_db, conversation_id=4, user=mock_user
        )

        # 验证
        assert result is None


class TestGetConversationWithMessages:
    """测试获取对话及其消息功能."""

    @pytest.mark.asyncio
    async def test_get_conversation_with_messages_success(
        self, mock_db, mock_user, mock_conversation
    ):
        """测试成功获取对话及消息."""
        # Mock消息
        messages = [Mock(spec=Message) for _ in range(5)]

        # Mock服务和CRUD
        ConversationService.get_conversation_by_id = AsyncMock(
            return_value=mock_conversation
        )
        from app import crud
        crud.crud_conversation.get_with_messages = AsyncMock(
            return_value=(mock_conversation, messages)
        )

        # 调用服务
        result = await ConversationService.get_conversation_with_messages(
            mock_db, conversation_id=1, user=mock_user, message_limit=50
        )

        # 验证
        assert result is not None
        assert result[0].id == 1
        assert len(result[1]) == 5

    @pytest.mark.asyncio
    async def test_get_conversation_with_messages_no_access(self, mock_db, mock_user):
        """测试无权限时返回None."""
        # Mock服务
        ConversationService.get_conversation_by_id = AsyncMock(return_value=None)

        # 调用服务
        result = await ConversationService.get_conversation_with_messages(
            mock_db, conversation_id=999, user=mock_user
        )

        # 验证
        assert result is None

    @pytest.mark.asyncio
    async def test_get_conversation_with_messages_crud_returns_none(
        self, mock_db, mock_user, mock_conversation
    ):
        """测试CRUD返回None时的处理."""
        # Mock服务和CRUD
        ConversationService.get_conversation_by_id = AsyncMock(
            return_value=mock_conversation
        )
        from app import crud
        # 模拟get_with_messages返回(None, None)的情况
        crud.crud_conversation.get_with_messages = AsyncMock(
            return_value=(None, None)
        )

        # 调用服务
        result = await ConversationService.get_conversation_with_messages(
            mock_db, conversation_id=1, user=mock_user
        )

        # 验证
        assert result is None


class TestUpdateConversation:
    """测试更新对话功能."""

    @pytest.mark.asyncio
    async def test_update_conversation(self, mock_db, mock_conversation):
        """测试更新对话信息."""
        # Mock CRUD
        from app import crud
        updated_conversation = Mock(spec=Conversation)
        updated_conversation.title = "Updated Title"
        crud.crud_conversation.update = AsyncMock(return_value=updated_conversation)

        # 创建更新数据
        update_data = ConversationUpdate(
            title="Updated Title",
            system_prompt=None,
            temperature=None,
            max_tokens=None,
            meta_data=None
        )

        # 调用服务
        result = await ConversationService.update_conversation(
            mock_db, mock_conversation, update_data
        )

        # 验证
        assert result.title == "Updated Title"
        crud.crud_conversation.update.assert_called_once_with(
            mock_db, db_obj=mock_conversation, obj_in=update_data
        )


class TestDeleteConversation:
    """测试删除对话功能."""

    @pytest.mark.asyncio
    async def test_delete_conversation(self, mock_db, mock_conversation):
        """测试删除对话."""
        # Mock CRUD
        from app import crud
        crud.crud_conversation.remove = AsyncMock()

        # 调用服务
        result = await ConversationService.delete_conversation(mock_db, mock_conversation)

        # 验证
        assert result is True
        crud.crud_conversation.remove.assert_called_once_with(mock_db, id=1)


class TestAddMessage:
    """测试添加消息功能."""

    @pytest.mark.asyncio
    async def test_add_message_basic(self, mock_db, mock_message):
        """测试添加基本消息."""
        # Mock CRUD
        from app import crud
        from app.crud.message import crud_message
        crud_message.create = AsyncMock(return_value=mock_message)
        crud.crud_conversation.update_stats = AsyncMock()

        # Mock数据库操作
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # 调用服务
        result = await ConversationService.add_message(
            mock_db,
            conversation_id=1,
            role="user",
            content="Test message",
            model="gpt-3.5-turbo",
            provider="openai",
            token_count=10
        )

        # 验证
        assert result.id == 1
        assert result.content == "Test message"
        crud.crud_conversation.update_stats.assert_called_once_with(
            mock_db,
            conversation_id=1,
            message_delta=1,
            token_delta=10
        )

    @pytest.mark.asyncio
    async def test_add_message_with_parent(self, mock_db, mock_message):
        """测试添加带父消息的消息."""
        # Mock父消息
        parent_message = Mock(spec=Message)
        parent_message.id = 99
        parent_message.conversation_id = 1
        parent_message.branch_name = "feature-branch"

        # Mock CRUD
        from app import crud
        from app.crud.message import crud_message
        crud_message.get = AsyncMock(return_value=parent_message)
        crud_message.create = AsyncMock(return_value=mock_message)
        crud.crud_conversation.update_stats = AsyncMock()

        # Mock数据库操作
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # 调用服务
        result = await ConversationService.add_message(
            mock_db,
            conversation_id=1,
            role="assistant",
            content="Reply message",
            parent_message_id=99
        )

        # 验证
        assert result is not None
        crud_message.get.assert_called_once_with(mock_db, id=99)


class TestGetConversationMessages:
    """测试获取对话消息列表功能."""

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, mock_db):
        """测试获取对话消息."""
        # Mock消息列表
        messages = [Mock(spec=Message) for _ in range(10)]

        # Mock CRUD
        from app.crud.message import crud_message
        crud_message.get_by_conversation = AsyncMock(return_value=messages)

        # 调用服务
        result = await ConversationService.get_conversation_messages(
            mock_db, conversation_id=1, skip=0, limit=100
        )

        # 验证
        assert len(result) == 10
        crud_message.get_by_conversation.assert_called_once_with(
            mock_db, conversation_id=1, skip=0, limit=100
        )


class TestSearchConversations:
    """测试搜索对话功能."""

    @pytest.mark.asyncio
    async def test_search_conversations(self, mock_db, mock_user):
        """测试搜索对话."""
        # Mock搜索结果
        search_results = [Mock(spec=Conversation) for _ in range(5)]

        # Mock CRUD
        from app import crud
        crud.crud_conversation.search_by_title = AsyncMock(return_value=search_results)

        # 调用服务
        result = await ConversationService.search_conversations(
            mock_db, mock_user, query="test", skip=0, limit=20
        )

        # 验证
        assert len(result) == 5
        crud.crud_conversation.search_by_title.assert_called_once_with(
            mock_db, user_id=1, query="test", skip=0, limit=20
        )
