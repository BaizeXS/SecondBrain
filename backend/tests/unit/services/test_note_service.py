"""Unit tests for Note Service."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Document, Note, NoteVersion, Space, User
from app.schemas.note import (
    NoteAIGenerateRequest,
    NoteAISummaryRequest,
    NoteCreate,
)
from app.schemas.note_version import NoteVersionDiff, NoteVersionResponse
from app.services.note_service import NoteService


@pytest.fixture
def note_service():
    """创建笔记服务实例."""
    return NoteService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话."""
    db = Mock(spec=AsyncSession)
    db.add = Mock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """创建模拟用户."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_note():
    """创建模拟笔记."""
    note = Mock(spec=Note)
    note.id = 1
    note.space_id = 1
    note.user_id = 1
    note.title = "Test Note"
    note.content = "Test content"
    note.content_type = "markdown"
    note.note_type = "manual"
    note.source_type = "user"
    note.tags = ["test", "demo"]
    note.meta_data = {"key": "value"}
    note.version = 1
    note.created_at = datetime.now()
    note.updated_at = datetime.now()
    return note


@pytest.fixture
def mock_space():
    """创建模拟Space."""
    space = Mock(spec=Space)
    space.id = 1
    space.name = "Test Space"
    space.note_count = 5
    return space


@pytest.fixture
def mock_document():
    """创建模拟文档."""
    document = Mock(spec=Document)
    document.id = 1
    document.title = "Test Document"
    document.filename = "test.pdf"
    document.content = "Document content"
    document.user_id = 1
    return document


@pytest.fixture
def mock_note_version():
    """创建模拟笔记版本."""
    version = Mock(spec=NoteVersion)
    version.id = 1
    version.note_id = 1
    version.version_number = 1
    version.title = "Test Note"
    version.content = "Test content"
    version.tags = ["test"]
    version.word_count = 10
    version.created_at = datetime.now()
    return version


class TestCreateNote:
    """测试创建笔记功能."""

    @pytest.mark.asyncio
    async def test_create_note_success(
        self, note_service, mock_db, mock_note, mock_space
    ):
        """测试成功创建笔记."""
        # 准备数据
        note_data = NoteCreate(
            space_id=1,
            title="Test Note",
            content="Test content",
            content_type="markdown",
            note_type="manual",
            tags=["test"],
            linked_documents=None,
            linked_notes=None,
            meta_data={"key": "value"}
        )

        # Mock数据库操作
        mock_db.get.return_value = mock_space

        # 执行
        result = await note_service.create_note(
            db=mock_db,
            note_data=note_data,
            user_id=1
        )

        # 验证
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called_once()
        assert mock_space.note_count == 6  # 增加了1

    @pytest.mark.asyncio
    async def test_create_note_exception(
        self, note_service, mock_db
    ):
        """测试创建笔记时出现异常."""
        note_data = NoteCreate(
            space_id=1,
            title="Test Note",
            content="Test content",
            tags=None,
            linked_documents=None,
            linked_notes=None,
            meta_data={}
        )

        # Mock数据库操作抛出异常
        mock_db.add.side_effect = Exception("Database error")

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await note_service.create_note(
                db=mock_db,
                note_data=note_data,
                user_id=1
            )

        assert "Database error" in str(exc_info.value)
        mock_db.rollback.assert_called_once()


class TestGenerateAINote:
    """测试AI生成笔记功能."""

    @pytest.mark.asyncio
    async def test_generate_ai_note_success(
        self, note_service, mock_db, mock_user, mock_note
    ):
        """测试成功生成AI笔记."""
        # 准备请求
        request = NoteAIGenerateRequest(
            space_id=1,
            prompt="生成一个总结",
            document_ids=[1, 2],
            note_ids=[3, 4],
            generation_type="summary",
            model="gpt-4",
            temperature=0.7
        )

        # Mock AI服务
        with patch('app.services.note_service.ai_service') as mock_ai:
            mock_ai.chat = AsyncMock(return_value="AI生成的内容")

            # Mock其他方法
            note_service._get_documents_content = AsyncMock(return_value="文档内容")
            note_service._get_notes_content = AsyncMock(return_value="笔记内容")
            note_service._generate_title = AsyncMock(return_value="AI生成的标题")
            note_service.create_note = AsyncMock(return_value=mock_note)

            # 执行
            result = await note_service.generate_ai_note(
                db=mock_db,
                request=request,
                user_id=1,
                user=mock_user
            )

            # 验证
            assert result == mock_note
            mock_ai.chat.assert_called_once()
            note_service._get_documents_content.assert_called_once_with(
                mock_db, [1, 2], 1
            )
            note_service._get_notes_content.assert_called_once_with(
                mock_db, [3, 4], 1
            )

            # 验证AI参数
            assert mock_note.ai_model == "gpt-4"
            assert mock_note.ai_prompt == "生成一个总结"
            assert mock_note.generation_params == {
                "temperature": 0.7,
                "generation_type": "summary"
            }

    @pytest.mark.asyncio
    async def test_generate_ai_note_without_references(
        self, note_service, mock_db, mock_user, mock_note
    ):
        """测试没有参考资料的AI生成."""
        request = NoteAIGenerateRequest(
            space_id=1,
            prompt="生成内容",
            document_ids=None,
            note_ids=None,
            generation_type="outline",
            model="gpt-4"
        )

        with patch('app.services.note_service.ai_service') as mock_ai:
            mock_ai.chat = AsyncMock(return_value="AI内容")
            note_service._generate_title = AsyncMock(return_value="标题")
            note_service.create_note = AsyncMock(return_value=mock_note)

            # 执行
            result = await note_service.generate_ai_note(
                db=mock_db,
                request=request,
                user_id=1,
                user=mock_user
            )

            # 验证
            assert result == mock_note
            # 验证消息中只有系统提示和用户提示
            call_args = mock_ai.chat.call_args
            messages = call_args.kwargs["messages"]
            assert len(messages) == 2  # system + user

    @pytest.mark.asyncio
    async def test_generate_ai_note_exception(
        self, note_service, mock_db, mock_user
    ):
        """测试生成AI笔记时异常处理."""
        # Mock AI service抛出异常
        with patch('app.services.note_service.ai_service') as mock_ai:
            mock_ai.chat = AsyncMock(side_effect=Exception("AI服务错误"))

            request = NoteAIGenerateRequest(
                space_id=1,
                prompt="生成笔记",
                document_ids=None,
                note_ids=None,
                generation_type="summary",
                model="gpt-4"
            )

            # 执行并验证异常
            with pytest.raises(Exception) as exc_info:
                await note_service.generate_ai_note(
                    db=mock_db,
                    request=request,
                    user_id=1,
                    user=mock_user
                )

            assert "AI服务错误" in str(exc_info.value)
            mock_db.rollback.assert_called_once()


class TestCreateAISummary:
    """测试创建AI文档总结功能."""

    @pytest.mark.asyncio
    async def test_create_ai_summary_success(
        self, note_service, mock_db, mock_user, mock_note
    ):
        """测试成功创建AI总结."""
        request = NoteAISummaryRequest(
            document_ids=[1, 2],
            space_id=1,
            summary_type="comprehensive",
            max_length=1000,
            language="zh"
        )

        with patch('app.services.note_service.ai_service') as mock_ai:
            mock_ai.chat = AsyncMock(return_value="文档总结内容")

            note_service._get_documents_content = AsyncMock(return_value="文档内容")
            note_service._get_document_titles = AsyncMock(return_value=["Doc1", "Doc2"])
            note_service.create_note = AsyncMock(return_value=mock_note)

            # 执行
            result = await note_service.create_ai_summary(
                db=mock_db,
                request=request,
                user_id=1,
                user=mock_user
            )

            # 验证
            assert result == mock_note
            assert mock_note.ai_model == "auto"
            assert mock_note.generation_params == {
                "summary_type": "comprehensive",
                "max_length": 1000,
                "language": "zh"
            }

    @pytest.mark.asyncio
    async def test_create_ai_summary_no_content(
        self, note_service, mock_db, mock_user
    ):
        """测试没有文档内容时创建总结."""
        request = NoteAISummaryRequest(
            document_ids=[1],
            space_id=1
        )

        note_service._get_documents_content = AsyncMock(return_value=None)

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await note_service.create_ai_summary(
                db=mock_db,
                request=request,
                user_id=1,
                user=mock_user
            )

        assert "未找到有效的文档内容" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_ai_summary_exception(
        self, note_service, mock_db, mock_user
    ):
        """测试创建AI总结时异常处理."""
        request = NoteAISummaryRequest(
            document_ids=[1],
            space_id=1
        )

        note_service._get_documents_content = AsyncMock(return_value="文档内容")

        with patch('app.services.note_service.ai_service') as mock_ai:
            mock_ai.chat = AsyncMock(side_effect=Exception("AI错误"))

            # 执行并验证异常
            with pytest.raises(Exception, match="AI错误"):
                await note_service.create_ai_summary(
                    db=mock_db,
                    request=request,
                    user_id=1,
                    user=mock_user
                )

            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_ai_summary_many_documents(
        self, note_service, mock_db, mock_user, mock_note
    ):
        """测试创建多文档总结时标题处理."""
        request = NoteAISummaryRequest(
            document_ids=[1, 2, 3, 4, 5],  # 超过3个文档
            space_id=1
        )

        with patch('app.services.note_service.ai_service') as mock_ai:
            mock_ai.chat = AsyncMock(return_value="总结内容")

            note_service._get_documents_content = AsyncMock(return_value="文档内容")
            note_service._get_document_titles = AsyncMock(
                return_value=["Doc1", "Doc2", "Doc3", "Doc4", "Doc5"]
            )
            note_service.create_note = AsyncMock(return_value=mock_note)

            # 执行
            result = await note_service.create_ai_summary(
                db=mock_db,
                request=request,
                user_id=1,
                user=mock_user
            )

            # 验证
            assert result == mock_note
            # 验证标题包含"等5个文档"
            create_call = note_service.create_note.call_args
            note_data = create_call[0][1]  # 第二个位置参数
            assert "等5个文档" in note_data.title


class TestGetDocumentsContent:
    """测试获取文档内容功能."""

    @pytest.mark.asyncio
    async def test_get_documents_content_success(
        self, note_service, mock_db, mock_document
    ):
        """测试成功获取文档内容."""
        # Mock查询结果
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_document]
        mock_db.execute.return_value = mock_result

        # 执行
        result = await note_service._get_documents_content(
            db=mock_db,
            document_ids=[1],
            user_id=1
        )

        # 验证
        assert result is not None
        assert "Test Document" in result
        assert "Document content" in result

    @pytest.mark.asyncio
    async def test_get_documents_content_truncate(
        self, note_service, mock_db
    ):
        """测试文档内容过长时截断."""
        # 创建长内容文档
        long_doc = Mock(spec=Document)
        long_doc.title = "Long Doc"
        long_doc.filename = "long.pdf"
        long_doc.content = "A" * 20000  # 超过默认限制

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [long_doc]
        mock_db.execute.return_value = mock_result

        # 执行
        result = await note_service._get_documents_content(
            db=mock_db,
            document_ids=[1],
            user_id=1,
            max_length=10000
        )

        # 验证
        assert len(result) <= 10000 + 100  # 允许一些额外字符
        assert result.endswith("...\n\n")


class TestGetDocumentTitles:
    """测试获取文档标题功能."""

    @pytest.mark.asyncio
    async def test_get_document_titles_success(
        self, note_service, mock_db
    ):
        """测试成功获取文档标题."""
        # Mock查询结果
        mock_result = Mock()
        mock_result.all.return_value = [
            ("Title 1", "file1.pdf"),
            (None, "file2.pdf"),  # 没有标题的情况
            ("Title 3", "file3.pdf")
        ]
        mock_db.execute.return_value = mock_result

        # 执行
        result = await note_service._get_document_titles(
            db=mock_db,
            document_ids=[1, 2, 3]
        )

        # 验证
        assert result == ["Title 1", "file2.pdf", "Title 3"]

    @pytest.mark.asyncio
    async def test_get_document_titles_exception(
        self, note_service, mock_db
    ):
        """测试获取文档标题时异常处理."""
        mock_db.execute.side_effect = Exception("DB error")

        # 执行
        result = await note_service._get_document_titles(
            db=mock_db,
            document_ids=[1]
        )

        # 验证返回空列表
        assert result == []


class TestGetNotesContent:
    """测试获取笔记内容功能."""

    @pytest.mark.asyncio
    async def test_get_notes_content_success(
        self, note_service, mock_db, mock_note
    ):
        """测试成功获取笔记内容."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_note]
        mock_db.execute.return_value = mock_result

        # 执行
        result = await note_service._get_notes_content(
            db=mock_db,
            note_ids=[1],
            user_id=1
        )

        # 验证
        assert result is not None
        assert "Test Note" in result
        assert "Test content" in result

    @pytest.mark.asyncio
    async def test_get_notes_content_no_notes(
        self, note_service, mock_db
    ):
        """测试没有笔记时返回None."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # 执行
        result = await note_service._get_notes_content(
            db=mock_db,
            note_ids=[1],
            user_id=1
        )

        # 验证
        assert result is None

    @pytest.mark.asyncio
    async def test_get_notes_content_truncate(
        self, note_service, mock_db
    ):
        """测试笔记内容过长时截断."""
        # 创建一个内容很长的笔记
        long_note = Mock()
        long_note.title = "Long Note"
        long_note.content = "x" * 5000  # 5000字符

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [long_note]
        mock_db.execute.return_value = mock_result

        # 执行，max_length默认是5000
        result = await note_service._get_notes_content(
            db=mock_db,
            note_ids=[1],
            user_id=1,
            max_length=100  # 设置小的限制
        )

        # 验证
        assert result is not None
        assert len(result) <= 150  # 标题 + 截断的内容
        assert "..." in result

    @pytest.mark.asyncio
    async def test_get_notes_content_exception(
        self, note_service, mock_db
    ):
        """测试获取笔记内容时异常处理."""
        mock_db.execute.side_effect = Exception("DB error")

        # 执行
        result = await note_service._get_notes_content(
            db=mock_db,
            note_ids=[1],
            user_id=1
        )

        # 验证
        assert result is None


class TestGenerateTitle:
    """测试生成标题功能."""

    @pytest.mark.asyncio
    async def test_generate_title_success(
        self, note_service, mock_user
    ):
        """测试成功生成标题."""
        with patch('app.services.note_service.ai_service') as mock_ai:
            mock_ai.chat = AsyncMock(return_value="生成的标题")

            # 执行
            result = await note_service._generate_title(
                "这是一段内容",
                mock_user
            )

            # 验证
            assert result == "生成的标题"

    @pytest.mark.asyncio
    async def test_generate_title_fallback(
        self, note_service, mock_user
    ):
        """测试生成标题失败时使用默认标题."""
        with patch('app.services.note_service.ai_service') as mock_ai:
            mock_ai.chat = AsyncMock(side_effect=Exception("AI error"))

            # 执行
            result = await note_service._generate_title(
                "内容",
                mock_user
            )

            # 验证
            assert "笔记 -" in result
            assert datetime.now().strftime('%Y-%m-%d') in result

    @pytest.mark.asyncio
    async def test_generate_title_long_title(
        self, note_service, mock_user
    ):
        """测试生成的标题过长时截断."""
        with patch('app.services.note_service.ai_service') as mock_ai:
            # 返回一个超过50字符的标题 (60个'x')
            long_title = "x" * 60
            mock_ai.chat = AsyncMock(return_value=long_title)

            # 执行
            result = await note_service._generate_title(
                "内容",
                mock_user
            )

            # 验证
            assert len(result) == 50  # 47 + 3 ("...")
            assert result.endswith("...")
            assert result[:47] == "x" * 47


class TestSaveVersion:
    """测试保存版本功能."""

    @pytest.mark.asyncio
    async def test_save_version_success(
        self, note_service, mock_db, mock_note, mock_note_version
    ):
        """测试成功保存版本."""
        # Mock CRUD
        from app.crud.note_version import crud_note_version
        crud_note_version.create_version = AsyncMock(return_value=mock_note_version)

        # 执行
        result = await note_service.save_version(
            db=mock_db,
            note=mock_note,
            user_id=1,
            change_summary="测试修改",
            change_type="edit",
            ai_model="gpt-4",
            ai_prompt="提示"
        )

        # 验证
        assert result == mock_note_version
        crud_note_version.create_version.assert_called_once()
        assert mock_note.version == 1
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_version_exception(
        self, note_service, mock_db, mock_note
    ):
        """测试保存版本时异常处理."""
        # Mock CRUD抛出异常
        from app.crud.note_version import crud_note_version
        crud_note_version.create_version = AsyncMock(side_effect=Exception("DB error"))

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await note_service.save_version(
                db=mock_db,
                note=mock_note,
                user_id=1,
                change_summary="测试"
            )

        assert "DB error" in str(exc_info.value)


class TestRestoreVersion:
    """测试恢复版本功能."""

    @pytest.mark.asyncio
    async def test_restore_version_success(
        self, note_service, mock_db, mock_note, mock_note_version
    ):
        """测试成功恢复版本."""
        # Mock CRUD
        from app.crud.note_version import crud_note_version
        crud_note_version.get = AsyncMock(return_value=mock_note_version)

        # Mock save_version
        note_service.save_version = AsyncMock(return_value=mock_note_version)

        # 执行
        result = await note_service.restore_version(
            db=mock_db,
            note=mock_note,
            version_id=1,
            user_id=1,
            create_backup=True
        )

        # 验证
        assert result == mock_note
        # 应该调用两次save_version (备份 + 恢复)
        assert note_service.save_version.call_count == 2

        # 验证内容被恢复
        assert mock_note.title == mock_note_version.title
        assert mock_note.content == mock_note_version.content
        assert mock_note.tags == mock_note_version.tags

    @pytest.mark.asyncio
    async def test_restore_version_invalid(
        self, note_service, mock_db, mock_note
    ):
        """测试恢复无效版本."""
        # Mock CRUD返回None
        from app.crud.note_version import crud_note_version
        crud_note_version.get = AsyncMock(return_value=None)

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await note_service.restore_version(
                db=mock_db,
                note=mock_note,
                version_id=999,
                user_id=1
            )

        assert "版本不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_restore_version_exception(
        self, note_service, mock_db, mock_note, mock_note_version
    ):
        """测试恢复版本时异常处理."""
        # Mock CRUD正常返回版本
        from app.crud.note_version import crud_note_version
        crud_note_version.get = AsyncMock(return_value=mock_note_version)

        # Mock save_version抛出异常
        note_service.save_version = AsyncMock(side_effect=Exception("Save error"))

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await note_service.restore_version(
                db=mock_db,
                note=mock_note,
                version_id=1,
                user_id=1,
                create_backup=True
            )

        assert "Save error" in str(exc_info.value)


class TestCompareVersions:
    """测试比较版本功能."""

    @pytest.mark.asyncio
    async def test_compare_versions_success(
        self, note_service, mock_db
    ):
        """测试成功比较版本."""
        # 创建两个版本
        version1 = Mock(spec=NoteVersion)
        version1.id = 1
        version1.note_id = 1
        version1.version_number = 1
        version1.title = "Title V1"
        version1.content = "Content V1"
        version1.tags = ["tag1"]
        version1.word_count = 10
        version1.user_id = 1
        version1.change_summary = None
        version1.change_type = "edit"
        version1.ai_model = None
        version1.ai_prompt = None
        version1.meta_data = None
        version1.created_at = datetime.now()
        version1.updated_at = datetime.now()
        version1.content_html = None

        version2 = Mock(spec=NoteVersion)
        version2.id = 2
        version2.note_id = 1
        version2.version_number = 2
        version2.title = "Title V2"
        version2.content = "Content V2 Modified"
        version2.tags = ["tag1", "tag2"]
        version2.word_count = 15
        version2.user_id = 1
        version2.change_summary = None
        version2.change_type = "edit"
        version2.ai_model = None
        version2.ai_prompt = None
        version2.meta_data = None
        version2.created_at = datetime.now()
        version2.updated_at = datetime.now()
        version2.content_html = None

        # Mock CRUD
        from app.crud.note_version import crud_note_version
        crud_note_version.get = AsyncMock(side_effect=[version1, version2])

        # 创建合适的响应对象
        version1_response = NoteVersionResponse(
            id=version1.id,
            note_id=version1.note_id,
            user_id=version1.user_id,
            version_number=version1.version_number,
            title=version1.title,
            content=version1.content,
            content_html=version1.content_html,
            change_summary=version1.change_summary,
            change_type=version1.change_type,
            ai_model=version1.ai_model,
            ai_prompt=version1.ai_prompt,
            tags=version1.tags,
            word_count=version1.word_count,
            meta_data=version1.meta_data,
            created_at=version1.created_at,
            updated_at=version1.updated_at
        )

        version2_response = NoteVersionResponse(
            id=version2.id,
            note_id=version2.note_id,
            user_id=version2.user_id,
            version_number=version2.version_number,
            title=version2.title,
            content=version2.content,
            content_html=version2.content_html,
            change_summary=version2.change_summary,
            change_type=version2.change_type,
            ai_model=version2.ai_model,
            ai_prompt=version2.ai_prompt,
            tags=version2.tags,
            word_count=version2.word_count,
            meta_data=version2.meta_data,
            created_at=version2.created_at,
            updated_at=version2.updated_at
        )

        # Mock model_validate
        with patch.object(NoteVersionResponse, 'model_validate') as mock_validate:
            mock_validate.side_effect = [version1_response, version2_response]

            # 执行
            result = await note_service.compare_versions(
                db=mock_db,
                version1_id=1,
                version2_id=2
            )

            # 验证
            assert isinstance(result, NoteVersionDiff)
            assert result.title_changed is True
            assert result.tags_added == ["tag2"]
            assert result.tags_removed == []
            assert result.word_count_change == 5

    @pytest.mark.asyncio
    async def test_compare_versions_not_found(
        self, note_service, mock_db
    ):
        """测试比较版本时版本不存在."""
        # Mock CRUD返回None
        from app.crud.note_version import crud_note_version
        crud_note_version.get = AsyncMock(return_value=None)

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await note_service.compare_versions(
                db=mock_db,
                version1_id=1,
                version2_id=2
            )

        assert "版本不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compare_versions_different_notes(
        self, note_service, mock_db
    ):
        """测试比较不同笔记的版本."""
        # 创建两个属于不同笔记的版本
        version1 = Mock(spec=NoteVersion)
        version1.note_id = 1

        version2 = Mock(spec=NoteVersion)
        version2.note_id = 2  # 不同的笔记ID

        # Mock CRUD
        from app.crud.note_version import crud_note_version
        crud_note_version.get = AsyncMock(side_effect=[version1, version2])

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await note_service.compare_versions(
                db=mock_db,
                version1_id=1,
                version2_id=2
            )

        assert "版本不属于同一篇笔记" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compare_versions_exception(
        self, note_service, mock_db
    ):
        """测试比较版本时异常处理."""
        # Mock CRUD抛出异常
        from app.crud.note_version import crud_note_version
        crud_note_version.get = AsyncMock(side_effect=Exception("DB error"))

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await note_service.compare_versions(
                db=mock_db,
                version1_id=1,
                version2_id=2
            )

        assert "DB error" in str(exc_info.value)


class TestGetVersionHistory:
    """测试获取版本历史功能."""

    @pytest.mark.asyncio
    async def test_get_version_history(
        self, note_service, mock_db, mock_note_version
    ):
        """测试获取版本历史."""
        # Mock CRUD
        from app.crud.note_version import crud_note_version
        crud_note_version.get_by_note = AsyncMock(return_value=[mock_note_version])

        # 执行
        result = await note_service.get_version_history(
            db=mock_db,
            note_id=1,
            skip=0,
            limit=50
        )

        # 验证
        assert result == [mock_note_version]
        crud_note_version.get_by_note.assert_called_once_with(
            mock_db,
            note_id=1,
            skip=0,
            limit=50
        )


class TestGetVersion:
    """测试获取特定版本功能."""

    @pytest.mark.asyncio
    async def test_get_version(
        self, note_service, mock_db, mock_note_version
    ):
        """测试获取特定版本."""
        # Mock CRUD
        from app.crud.note_version import crud_note_version
        crud_note_version.get_by_version_number = AsyncMock(return_value=mock_note_version)

        # 执行
        result = await note_service.get_version(
            db=mock_db,
            note_id=1,
            version_number=1
        )

        # 验证
        assert result == mock_note_version
        crud_note_version.get_by_version_number.assert_called_once_with(
            mock_db,
            note_id=1,
            version_number=1
        )


class TestCleanupOldVersions:
    """测试清理旧版本功能."""

    @pytest.mark.asyncio
    async def test_cleanup_old_versions(
        self, note_service, mock_db
    ):
        """测试清理旧版本."""
        # Mock CRUD
        from app.crud.note_version import crud_note_version
        crud_note_version.cleanup_old_versions = AsyncMock(return_value=5)

        # 执行
        result = await note_service.cleanup_old_versions(
            db=mock_db,
            note_id=1,
            keep_count=10
        )

        # 验证
        assert result == 5
        crud_note_version.cleanup_old_versions.assert_called_once_with(
            mock_db,
            note_id=1,
            keep_count=10
        )


class TestPromptHelpers:
    """测试提示词辅助方法."""

    def test_get_generation_prompt(self, note_service):
        """测试获取生成提示词."""
        # 测试各种类型
        prompts = {
            "summary": "文档总结助手",
            "outline": "大纲生成专家",
            "keypoints": "要点提取专家",
            "mindmap": "思维导图专家",
            "question": "问题生成专家",
        }

        for prompt_type, expected_text in prompts.items():
            result = note_service._get_generation_prompt(prompt_type)
            assert expected_text in result

        # 测试默认值
        result = note_service._get_generation_prompt("unknown")
        assert "文档总结助手" in result

    def test_get_summary_prompt(self, note_service):
        """测试获取总结提示词."""
        result = note_service._get_summary_prompt(
            summary_type="comprehensive",
            max_length=1000,
            language="zh"
        )

        assert "专业的文档总结助手" in result
        assert "全面详细的总结" in result
        assert "1000字" in result
        assert "使用中文输出" in result
        assert "Markdown格式" in result
