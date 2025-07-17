"""Unit tests for Branch Service."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Conversation, Message, User
from app.schemas.conversation_branch import (
    BranchCreate,
    BranchHistory,
    BranchListResponse,
)
from app.services.branch_service import BranchService


@pytest.fixture
def branch_service():
    """创建分支服务实例."""
    return BranchService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话."""
    db = Mock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


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
    return conversation


@pytest.fixture
def mock_message():
    """创建模拟消息."""
    message = Mock(spec=Message)
    message.id = 1
    message.conversation_id = 1
    message.role = "user"
    message.content = "Test message"
    message.model = "gpt-4"
    message.provider = "openai"
    message.parent_message_id = None
    message.branch_name = None
    message.is_active_branch = True
    message.token_count = 10
    message.processing_time = 0.5
    message.meta_data = {"key": "value"}
    message.attachments = None
    message.created_at = datetime.now()
    return message


class TestCreateBranch:
    """测试创建分支功能."""

    @pytest.mark.asyncio
    async def test_create_branch_success(
        self, branch_service, mock_db, mock_user, mock_conversation, mock_message
    ):
        """测试成功创建分支."""
        # 准备数据
        branch_data = BranchCreate(
            from_message_id=1,
            branch_name="feature-branch",
            initial_content="New branch content"
        )

        # Mock CRUD 操作
        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get = AsyncMock(return_value=mock_message)
        crud_message.get_conversation_branches = AsyncMock(return_value=["main"])
        crud_message.create_branch_message = AsyncMock(return_value=mock_message)

        # 执行
        result = await branch_service.create_branch(
            db=mock_db,
            conversation_id=1,
            branch_data=branch_data,
            user=mock_user
        )

        # 验证
        assert result == mock_message
        crud_message.create_branch_message.assert_called_once()
        call_args = crud_message.create_branch_message.call_args
        assert call_args.kwargs["parent_message_id"] == 1
        assert call_args.kwargs["branch_name"] == "feature-branch"

    @pytest.mark.asyncio
    async def test_create_branch_no_access(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试无权限创建分支."""
        # 设置不同的用户ID
        mock_conversation.user_id = 2

        branch_data = BranchCreate(
            from_message_id=1,
            branch_name="feature-branch",
            initial_content="New branch content"
        )

        from app.crud.conversation import crud_conversation
        crud_conversation.get = AsyncMock(return_value=mock_conversation)

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await branch_service.create_branch(
                db=mock_db,
                conversation_id=1,
                branch_data=branch_data,
                user=mock_user
            )

        assert "对话不存在或无权访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_branch_duplicate_name(
        self, branch_service, mock_db, mock_user, mock_conversation, mock_message
    ):
        """测试创建重复名称的分支."""
        branch_data = BranchCreate(
            from_message_id=1,
            branch_name="existing-branch",
            initial_content="New branch content"
        )

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get = AsyncMock(return_value=mock_message)
        crud_message.get_conversation_branches = AsyncMock(
            return_value=["main", "existing-branch"]
        )

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await branch_service.create_branch(
                db=mock_db,
                conversation_id=1,
                branch_data=branch_data,
                user=mock_user
            )

        assert "分支名称 'existing-branch' 已存在" in str(exc_info.value)


class TestListBranches:
    """测试列出分支功能."""

    @pytest.mark.asyncio
    async def test_list_branches_success(
        self, branch_service, mock_db, mock_user, mock_conversation, mock_message
    ):
        """测试成功列出分支."""
        # 准备多个分支的消息
        branch_msg1 = Mock(spec=Message, **vars(mock_message))
        branch_msg1.branch_name = "feature-1"
        branch_msg1.is_active_branch = True

        branch_msg2 = Mock(spec=Message, **vars(mock_message))
        branch_msg2.branch_name = "feature-2"
        branch_msg2.is_active_branch = False

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_conversation_branches = AsyncMock(
            return_value=["feature-1", "feature-2"]
        )
        crud_message.get_branch_messages = AsyncMock(
            side_effect=[[branch_msg1], [branch_msg2]]
        )
        crud_message.get_by_conversation = AsyncMock(return_value=[])

        # 执行
        result = await branch_service.list_branches(
            db=mock_db,
            conversation_id=1,
            user=mock_user
        )

        # 验证
        assert isinstance(result, BranchListResponse)
        assert len(result.branches) == 2
        assert result.active_branch == "feature-1"
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_list_branches_with_main(
        self, branch_service, mock_db, mock_user, mock_conversation, mock_message
    ):
        """测试列出包含主线的分支."""
        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_conversation_branches = AsyncMock(return_value=[])
        crud_message.get_by_conversation = AsyncMock(return_value=[mock_message])

        # 执行
        result = await branch_service.list_branches(
            db=mock_db,
            conversation_id=1,
            user=mock_user
        )

        # 验证
        assert len(result.branches) == 1
        assert result.branches[0].branch_name == "main"
        assert result.active_branch == "main"


class TestSwitchBranch:
    """测试切换分支功能."""

    @pytest.mark.asyncio
    async def test_switch_branch_success(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试成功切换分支."""
        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_conversation_branches = AsyncMock(
            return_value=["main", "feature-1"]
        )
        crud_message.set_active_branch = AsyncMock()

        # 执行
        await branch_service.switch_branch(
            db=mock_db,
            conversation_id=1,
            branch_name="feature-1",
            user=mock_user
        )

        # 验证
        crud_message.set_active_branch.assert_called_once_with(
            mock_db, 1, "feature-1"
        )

    @pytest.mark.asyncio
    async def test_switch_to_nonexistent_branch(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试切换到不存在的分支."""
        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_conversation_branches = AsyncMock(
            return_value=["main", "feature-1"]
        )

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await branch_service.switch_branch(
                db=mock_db,
                conversation_id=1,
                branch_name="nonexistent",
                user=mock_user
            )

        assert "分支 'nonexistent' 不存在" in str(exc_info.value)


class TestGetBranchHistory:
    """测试获取分支历史功能."""

    @pytest.mark.asyncio
    async def test_get_branch_history_full(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试获取完整分支历史."""
        # 准备消息
        msg1 = Mock(spec=Message)
        msg1.id = 1
        msg1.parent_message_id = None
        msg1.branch_name = None
        msg1.role = "user"
        msg1.content = "First message"
        msg1.created_at = datetime.now()
        msg1.child_messages = []

        msg2 = Mock(spec=Message)
        msg2.id = 2
        msg2.parent_message_id = 1
        msg2.branch_name = "feature"
        msg2.role = "assistant"
        msg2.content = "Branch message"
        msg2.created_at = datetime.now()
        msg2.child_messages = []

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_by_conversation = AsyncMock(return_value=[msg1, msg2])
        crud_message.get_branch_point_messages = AsyncMock(return_value=[msg1])

        # 设置分支点的子消息
        msg1.child_messages = [msg2]

        # 执行
        result = await branch_service.get_branch_history(
            db=mock_db,
            conversation_id=1,
            user=mock_user
        )

        # 验证
        assert len(result) == 2
        assert isinstance(result[0], BranchHistory)
        assert result[0].is_branch_point is True
        assert result[1].branch_name == "feature"

    @pytest.mark.asyncio
    async def test_get_branch_history_from_message(
        self, branch_service, mock_db, mock_message
    ):
        """测试从指定消息获取历史."""
        from app.crud.message import crud_message

        crud_message.get_message_history_to_root = AsyncMock(
            return_value=[mock_message]
        )
        crud_message.get_branch_point_messages = AsyncMock(return_value=[])

        # 执行
        result = await branch_service.get_branch_history(
            db=mock_db,
            conversation_id=1,
            message_id=1
        )

        # 验证
        assert len(result) == 1
        assert result[0].message_id == 1
        assert result[0].is_branch_point is False


class TestMergeBranch:
    """测试合并分支功能."""

    @pytest.mark.asyncio
    async def test_merge_branch_success(
        self, branch_service, mock_db, mock_user, mock_conversation, mock_message
    ):
        """测试成功合并分支."""
        # 准备源分支消息
        source_msg = Mock(spec=Message)
        source_msg.id = 2
        source_msg.conversation_id = 1
        source_msg.role = "user"
        source_msg.content = "Branch content"
        source_msg.model = "gpt-4"
        source_msg.provider = "openai"
        source_msg.meta_data = {}
        source_msg.attachments = None

        # 目标消息
        target_msg = Mock(spec=Message)
        target_msg.id = 1
        target_msg.conversation_id = 1
        target_msg.branch_name = "main"

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_branch_messages = AsyncMock(return_value=[source_msg])
        crud_message.get = AsyncMock(return_value=target_msg)
        crud_message.create = AsyncMock(return_value=mock_message)

        # 执行
        result = await branch_service.merge_branch(
            db=mock_db,
            conversation_id=1,
            source_branch="feature",
            target_message_id=1,
            user=mock_user
        )

        # 验证
        assert len(result) == 1
        crud_message.create.assert_called_once()

        # 验证合并元数据
        create_call = crud_message.create.call_args
        obj_in = create_call.kwargs["obj_in"]
        assert obj_in.meta_data["merged_from"] == "feature"
        assert obj_in.meta_data["original_message_id"] == 2

    @pytest.mark.asyncio
    async def test_merge_empty_branch(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试合并空分支."""
        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_branch_messages = AsyncMock(return_value=[])

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await branch_service.merge_branch(
                db=mock_db,
                conversation_id=1,
                source_branch="empty-branch",
                target_message_id=None,
                user=mock_user
            )

        assert "源分支 'empty-branch' 为空" in str(exc_info.value)


class TestDeleteBranch:
    """测试删除分支功能."""

    @pytest.mark.asyncio
    async def test_delete_branch_success(
        self, branch_service, mock_db, mock_user, mock_conversation, mock_message
    ):
        """测试成功删除分支."""
        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_branch_messages = AsyncMock(return_value=[mock_message])
        crud_message.remove = AsyncMock()

        # 执行
        await branch_service.delete_branch(
            db=mock_db,
            conversation_id=1,
            branch_name="feature",
            user=mock_user
        )

        # 验证
        crud_message.remove.assert_called_once_with(mock_db, id=1)

    @pytest.mark.asyncio
    async def test_delete_main_branch(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试删除主分支（应该失败）."""
        from app.crud.conversation import crud_conversation
        crud_conversation.get = AsyncMock(return_value=mock_conversation)

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await branch_service.delete_branch(
                db=mock_db,
                conversation_id=1,
                branch_name="main",
                user=mock_user
            )

        assert "不能删除主分支" in str(exc_info.value)


class TestBranchServiceCoverage:
    """测试Branch Service未覆盖的边缘情况."""

    @pytest.mark.asyncio
    async def test_create_branch_parent_message_not_exists(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试父消息不存在的情况 (line 41)."""
        branch_data = BranchCreate(
            from_message_id=1,
            branch_name="feature-branch",
            initial_content="New branch content"
        )

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get = AsyncMock(return_value=None)  # 父消息不存在

        with pytest.raises(ValueError) as exc_info:
            await branch_service.create_branch(
                db=mock_db,
                conversation_id=1,
                branch_data=branch_data,
                user=mock_user
            )

        assert "父消息不存在或不属于此对话" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_branch_parent_message_wrong_conversation(
        self, branch_service, mock_db, mock_user, mock_conversation, mock_message
    ):
        """测试父消息属于其他对话的情况 (line 41)."""
        branch_data = BranchCreate(
            from_message_id=1,
            branch_name="feature-branch",
            initial_content="New branch content"
        )

        # 设置父消息属于不同的对话
        mock_message.conversation_id = 2

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get = AsyncMock(return_value=mock_message)

        with pytest.raises(ValueError) as exc_info:
            await branch_service.create_branch(
                db=mock_db,
                conversation_id=1,
                branch_data=branch_data,
                user=mock_user
            )

        assert "父消息不存在或不属于此对话" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_branches_no_conversation(
        self, branch_service, mock_db, mock_user
    ):
        """测试对话不存在的情况 (line 78)."""
        from app.crud.conversation import crud_conversation
        crud_conversation.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await branch_service.list_branches(
                db=mock_db,
                conversation_id=1,
                user=mock_user
            )

        assert "对话不存在或无权访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_switch_branch_no_conversation(
        self, branch_service, mock_db, mock_user
    ):
        """测试切换分支时对话不存在的情况 (line 164)."""
        from app.crud.conversation import crud_conversation
        crud_conversation.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await branch_service.switch_branch(
                db=mock_db,
                conversation_id=1,
                branch_name="feature",
                user=mock_user
            )

        assert "对话不存在或无权访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_branch_history_no_conversation(
        self, branch_service, mock_db, mock_user
    ):
        """测试获取历史时对话不存在的情况 (line 188)."""
        from app.crud.conversation import crud_conversation
        crud_conversation.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await branch_service.get_branch_history(
                db=mock_db,
                conversation_id=1,
                user=mock_user
            )

        assert "对话不存在或无权访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_merge_branch_no_conversation(
        self, branch_service, mock_db, mock_user
    ):
        """测试合并分支时对话不存在的情况 (line 241)."""
        from app.crud.conversation import crud_conversation
        crud_conversation.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await branch_service.merge_branch(
                db=mock_db,
                conversation_id=1,
                source_branch="feature",
                target_message_id=None,
                user=mock_user
            )

        assert "对话不存在或无权访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_merge_branch_default_target(
        self, branch_service, mock_db, mock_user, mock_conversation, mock_message
    ):
        """测试合并到默认目标的情况 (lines 255-265)."""
        # 准备源分支消息
        source_msg = Mock(spec=Message)
        source_msg.id = 2
        source_msg.conversation_id = 1
        source_msg.role = "user"
        source_msg.content = "Branch content"
        source_msg.model = "gpt-4"
        source_msg.provider = "openai"
        source_msg.meta_data = {}
        source_msg.attachments = None

        # 主线消息作为默认目标
        main_msg = Mock(spec=Message)
        main_msg.id = 1
        main_msg.conversation_id = 1
        main_msg.branch_name = None

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_branch_messages = AsyncMock(return_value=[source_msg])
        crud_message.get_by_conversation = AsyncMock(return_value=[main_msg])
        crud_message.create = AsyncMock(return_value=mock_message)

        # 执行 - 不指定target_message_id
        result = await branch_service.merge_branch(
            db=mock_db,
            conversation_id=1,
            source_branch="feature",
            target_message_id=None,  # 使用默认目标
            user=mock_user
        )

        # 验证
        assert len(result) == 1
        crud_message.get_by_conversation.assert_called_once()

    @pytest.mark.asyncio
    async def test_merge_branch_no_default_target(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试没有默认合并目标的情况 (line 265)."""
        # 准备源分支消息
        source_msg = Mock(spec=Message)
        source_msg.id = 2
        source_msg.conversation_id = 1
        source_msg.role = "user"
        source_msg.content = "Branch content"

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_branch_messages = AsyncMock(return_value=[source_msg])
        crud_message.get_by_conversation = AsyncMock(return_value=[])  # 没有主线消息

        with pytest.raises(ValueError) as exc_info:
            await branch_service.merge_branch(
                db=mock_db,
                conversation_id=1,
                source_branch="feature",
                target_message_id=None,
                user=mock_user
            )

        assert "无法找到合并目标" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_branch_no_conversation(
        self, branch_service, mock_db, mock_user
    ):
        """测试删除分支时对话不存在的情况 (line 316)."""
        from app.crud.conversation import crud_conversation
        crud_conversation.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await branch_service.delete_branch(
                db=mock_db,
                conversation_id=1,
                branch_name="feature",
                user=mock_user
            )

        assert "对话不存在或无权访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_branch_history_branch_point_with_child_branches(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试获取包含子分支的分支点历史."""
        # 准备分支点消息
        branch_point = Mock(spec=Message)
        branch_point.id = 1
        branch_point.parent_message_id = None
        branch_point.branch_name = None
        branch_point.role = "user"
        branch_point.content = "Branch point"
        branch_point.created_at = datetime.now()

        # 准备子消息
        child1 = Mock(spec=Message)
        child1.branch_name = "feature-1"

        child2 = Mock(spec=Message)
        child2.branch_name = "feature-2"

        branch_point.child_messages = [child1, child2]

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_by_conversation = AsyncMock(return_value=[branch_point])
        crud_message.get_branch_point_messages = AsyncMock(return_value=[branch_point])

        # 执行
        result = await branch_service.get_branch_history(
            db=mock_db,
            conversation_id=1,
            user=mock_user
        )

        # 验证
        assert len(result) == 1
        assert result[0].is_branch_point is True
        assert len(result[0].child_branches) == 2
        assert "feature-1" in result[0].child_branches
        assert "feature-2" in result[0].child_branches

    @pytest.mark.asyncio
    async def test_merge_branch_invalid_target_message(
        self, branch_service, mock_db, mock_user, mock_conversation
    ):
        """测试合并到无效目标消息的情况 (line 255)."""
        # 准备源分支消息
        source_msg = Mock(spec=Message)
        source_msg.id = 2
        source_msg.conversation_id = 1
        source_msg.role = "user"
        source_msg.content = "Branch content"

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_branch_messages = AsyncMock(return_value=[source_msg])
        crud_message.get = AsyncMock(return_value=None)  # 目标消息不存在

        with pytest.raises(ValueError) as exc_info:
            await branch_service.merge_branch(
                db=mock_db,
                conversation_id=1,
                source_branch="feature",
                target_message_id=999,  # 无效的目标消息ID
                user=mock_user
            )

        assert "目标消息不存在或不属于此对话" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_merge_branch_target_message_wrong_conversation(
        self, branch_service, mock_db, mock_user, mock_conversation, mock_message
    ):
        """测试合并到错误对话的目标消息 (line 255)."""
        # 准备源分支消息
        source_msg = Mock(spec=Message)
        source_msg.id = 2
        source_msg.conversation_id = 1
        source_msg.role = "user"
        source_msg.content = "Branch content"

        # 目标消息属于不同的对话
        target_msg = Mock(spec=Message)
        target_msg.id = 999
        target_msg.conversation_id = 2  # 不同的对话

        from app.crud.conversation import crud_conversation
        from app.crud.message import crud_message

        crud_conversation.get = AsyncMock(return_value=mock_conversation)
        crud_message.get_branch_messages = AsyncMock(return_value=[source_msg])
        crud_message.get = AsyncMock(return_value=target_msg)

        with pytest.raises(ValueError) as exc_info:
            await branch_service.merge_branch(
                db=mock_db,
                conversation_id=1,
                source_branch="feature",
                target_message_id=999,
                user=mock_user
            )

        assert "目标消息不存在或不属于此对话" in str(exc_info.value)
