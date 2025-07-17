"""Unit tests for Annotation Service."""

from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Annotation, Document
from app.schemas.annotation import (
    PDFAnnotationData,
    PDFHighlight,
)
from app.services.annotation_service import AnnotationService


@pytest.fixture
def annotation_service():
    """创建标注服务实例."""
    return AnnotationService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话."""
    return Mock(spec=AsyncSession)


@pytest.fixture
def mock_annotation():
    """创建模拟标注."""
    annotation = Mock(spec=Annotation)
    annotation.id = 1
    annotation.document_id = 1
    annotation.user_id = 1
    annotation.type = "highlight"
    annotation.content = "Test note"
    annotation.selected_text = "Test text"
    annotation.page_number = 1
    annotation.position_data = {"page": 1, "rects": [[0, 0, 100, 100]], "text": "Test text"}
    annotation.color = "#FFFF00"
    annotation.created_at = Mock()
    annotation.created_at.isoformat.return_value = "2024-01-01T00:00:00"
    return annotation


@pytest.fixture
def mock_document():
    """创建模拟文档."""
    document = Mock(spec=Document)
    document.id = 1
    document.user_id = 1
    document.title = "Test Document"
    document.filename = "test.pdf"
    return document


@pytest.fixture
def pdf_highlight():
    """创建PDF高亮数据."""
    return PDFHighlight(
        page=1,
        text="Test text",
        rects=[[0, 0, 100, 100]],
        color="#FFFF00",
        note="Test note"
    )


class TestCreatePDFHighlight:
    """测试创建PDF高亮标注."""

    @pytest.mark.asyncio
    async def test_create_pdf_highlight_success(
        self, annotation_service, mock_db, pdf_highlight, mock_annotation
    ):
        """测试成功创建PDF高亮."""
        # Mock CRUD
        from app.crud.annotation import crud_annotation
        crud_annotation.create = AsyncMock(return_value=mock_annotation)

        # 执行
        result = await annotation_service.create_pdf_highlight(
            db=mock_db,
            document_id=1,
            user_id=1,
            highlight=pdf_highlight
        )

        # 验证
        assert result == mock_annotation
        crud_annotation.create.assert_called_once()
        call_args = crud_annotation.create.call_args
        assert call_args.kwargs["user_id"] == 1

        obj_in = call_args.kwargs["obj_in"]
        assert obj_in.document_id == 1
        assert obj_in.type == "highlight"
        assert obj_in.selected_text == "Test text"
        assert obj_in.content == "Test note"
        assert obj_in.page_number == 1
        assert obj_in.color == "#FFFF00"

    @pytest.mark.asyncio
    async def test_create_pdf_highlight_exception(
        self, annotation_service, mock_db, pdf_highlight
    ):
        """测试创建PDF高亮时出现异常."""
        # Mock CRUD 抛出异常
        from app.crud.annotation import crud_annotation
        crud_annotation.create = AsyncMock(side_effect=Exception("Database error"))

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await annotation_service.create_pdf_highlight(
                db=mock_db,
                document_id=1,
                user_id=1,
                highlight=pdf_highlight
            )

        assert "Database error" in str(exc_info.value)


class TestCreatePDFUnderline:
    """测试创建PDF下划线标注."""

    @pytest.mark.asyncio
    async def test_create_pdf_underline_success(
        self, annotation_service, mock_db, pdf_highlight, mock_annotation
    ):
        """测试成功创建PDF下划线."""
        # 修改mock为下划线类型
        mock_annotation.type = "underline"

        # Mock CRUD
        from app.crud.annotation import crud_annotation
        crud_annotation.create = AsyncMock(return_value=mock_annotation)

        # 执行
        result = await annotation_service.create_pdf_underline(
            db=mock_db,
            document_id=1,
            user_id=1,
            underline=pdf_highlight
        )

        # 验证
        assert result == mock_annotation
        crud_annotation.create.assert_called_once()

        obj_in = crud_annotation.create.call_args.kwargs["obj_in"]
        assert obj_in.type == "underline"

    @pytest.mark.asyncio
    async def test_create_pdf_underline_default_color(
        self, annotation_service, mock_db, mock_annotation
    ):
        """测试创建PDF下划线时使用默认颜色."""
        # 创建没有指定颜色的下划线 - 但 PDFHighlight 有默认颜色
        underline = PDFHighlight(
            page=1,
            text="Test text",
            rects=[[0, 0, 100, 100]],
            note="Test note"
        )

        # Mock CRUD
        from app.crud.annotation import crud_annotation
        crud_annotation.create = AsyncMock(return_value=mock_annotation)

        # 执行
        await annotation_service.create_pdf_underline(
            db=mock_db,
            document_id=1,
            user_id=1,
            underline=underline
        )

        # 验证使用了 PDFHighlight 的默认颜色或服务覆盖的颜色
        obj_in = crud_annotation.create.call_args.kwargs["obj_in"]
        # 由于 PDFHighlight 的默认颜色是 #FFFF00，而服务中的逻辑是 color or "#FF0000"
        # 所以实际使用的是 #FFFF00
        assert obj_in.color == "#FFFF00"


class TestBatchCreatePDFAnnotations:
    """测试批量创建PDF标注."""

    @pytest.mark.asyncio
    async def test_batch_create_success(
        self, annotation_service, mock_db, pdf_highlight, mock_annotation
    ):
        """测试成功批量创建标注."""
        # 准备数据
        pdf_data = PDFAnnotationData(
            highlights=[pdf_highlight],
            underlines=[pdf_highlight],
            notes=[{"content": "Note 1", "page": 1, "position": {"x": 0, "y": 0}}],
            bookmarks=[{"title": "Chapter 1", "page": 1, "level": 0}]
        )

        # Mock 服务方法
        annotation_service.create_pdf_highlight = AsyncMock(return_value=mock_annotation)
        annotation_service.create_pdf_underline = AsyncMock(return_value=mock_annotation)

        # Mock CRUD
        from app.crud.annotation import crud_annotation
        crud_annotation.create = AsyncMock(return_value=mock_annotation)

        # 执行
        results = await annotation_service.batch_create_pdf_annotations(
            db=mock_db,
            document_id=1,
            user_id=1,
            pdf_data=pdf_data
        )

        # 验证
        assert len(results) == 4  # 1 highlight + 1 underline + 1 note + 1 bookmark
        annotation_service.create_pdf_highlight.assert_called_once()
        annotation_service.create_pdf_underline.assert_called_once()
        crud_annotation.create.assert_called()  # 为 notes 和 bookmarks 调用

    @pytest.mark.asyncio
    async def test_batch_create_empty_data(
        self, annotation_service, mock_db
    ):
        """测试空数据批量创建."""
        pdf_data = PDFAnnotationData()

        # 执行
        results = await annotation_service.batch_create_pdf_annotations(
            db=mock_db,
            document_id=1,
            user_id=1,
            pdf_data=pdf_data
        )

        # 验证
        assert results == []


class TestGetPDFAnnotationsByPage:
    """测试获取PDF指定页的标注."""

    @pytest.mark.asyncio
    async def test_get_annotations_by_page_success(
        self, annotation_service, mock_db, mock_annotation
    ):
        """测试成功获取指定页标注."""
        # 准备多种类型的标注
        highlight_ann = Mock(spec=Annotation)
        highlight_ann.type = "highlight"
        highlight_ann.page_number = 1
        highlight_ann.selected_text = "Highlighted text"
        highlight_ann.position_data = {"rects": [[0, 0, 100, 100]]}
        highlight_ann.color = "#FFFF00"
        highlight_ann.content = "Highlight note"

        underline_ann = Mock(spec=Annotation)
        underline_ann.type = "underline"
        underline_ann.page_number = 1
        underline_ann.selected_text = "Underlined text"
        underline_ann.position_data = {"rects": [[0, 50, 100, 60]]}
        underline_ann.color = "#FF0000"
        underline_ann.content = "Underline note"

        note_ann = Mock(spec=Annotation)
        note_ann.type = "note"
        note_ann.page_number = 1
        note_ann.content = "Page note"
        note_ann.position_data = {"x": 10, "y": 20}

        bookmark_ann = Mock(spec=Annotation)
        bookmark_ann.type = "bookmark"
        bookmark_ann.page_number = 1
        bookmark_ann.content = "Chapter 1"
        bookmark_ann.position_data = {"level": 1}

        # Mock CRUD
        from app.crud.annotation import crud_annotation
        crud_annotation.get_by_document = AsyncMock(
            return_value=[highlight_ann, underline_ann, note_ann, bookmark_ann]
        )

        # 执行
        result = await annotation_service.get_pdf_annotations_by_page(
            db=mock_db,
            document_id=1,
            user_id=1,
            page_number=1
        )

        # 验证
        assert isinstance(result, PDFAnnotationData)
        assert len(result.highlights) == 1
        assert len(result.underlines) == 1
        assert len(result.notes) == 1
        assert len(result.bookmarks) == 1

        # 验证数据正确转换
        assert result.highlights[0].text == "Highlighted text"
        assert result.underlines[0].text == "Underlined text"
        assert result.notes[0]["content"] == "Page note"
        assert result.bookmarks[0]["title"] == "Chapter 1"

    @pytest.mark.asyncio
    async def test_get_annotations_by_page_no_page_number(
        self, annotation_service, mock_db
    ):
        """测试获取没有页码的标注."""
        # 创建没有页码的标注
        ann = Mock(spec=Annotation)
        ann.type = "highlight"
        ann.page_number = None  # 没有页码
        ann.position_data = {"rects": [[0, 0, 100, 100]]}

        # Mock CRUD
        from app.crud.annotation import crud_annotation
        crud_annotation.get_by_document = AsyncMock(return_value=[ann])

        # 执行
        result = await annotation_service.get_pdf_annotations_by_page(
            db=mock_db,
            document_id=1,
            user_id=1,
            page_number=1
        )

        # 验证 - 没有页码的高亮不会被包含
        assert len(result.highlights) == 0


class TestExportAnnotations:
    """测试导出标注."""

    @pytest.mark.asyncio
    async def test_export_json_format(
        self, annotation_service, mock_db, mock_document, mock_annotation
    ):
        """测试JSON格式导出."""
        # Mock CRUD
        from app.crud.annotation import crud_annotation
        from app.crud.document import crud_document
        crud_document.get = AsyncMock(return_value=mock_document)
        crud_annotation.get_by_document = AsyncMock(return_value=[mock_annotation])

        # 执行
        result = await annotation_service.export_annotations(
            db=mock_db,
            document_id=1,
            user_id=1,
            format="json"
        )

        # 验证
        assert isinstance(result, dict)
        assert result["document"]["id"] == 1
        assert result["document"]["title"] == "Test Document"
        assert len(result["annotations"]) == 1
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_export_markdown_format(
        self, annotation_service, mock_db, mock_document, mock_annotation
    ):
        """测试Markdown格式导出."""
        # Mock CRUD
        from app.crud.annotation import crud_annotation
        from app.crud.document import crud_document
        crud_document.get = AsyncMock(return_value=mock_document)
        crud_annotation.get_by_document = AsyncMock(return_value=[mock_annotation])

        # 执行
        result = await annotation_service.export_annotations(
            db=mock_db,
            document_id=1,
            user_id=1,
            format="markdown"
        )

        # 验证
        assert isinstance(result, str)
        assert "Test Document - 标注汇总" in result
        assert "标注数量: 1" in result
        assert "第 1 页" in result
        assert "高亮" in result

    @pytest.mark.asyncio
    async def test_export_no_access(
        self, annotation_service, mock_db, mock_document
    ):
        """测试无权限访问文档."""
        # 设置不同的用户ID
        mock_document.user_id = 2

        # Mock CRUD
        from app.crud.document import crud_document
        crud_document.get = AsyncMock(return_value=mock_document)

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await annotation_service.export_annotations(
                db=mock_db,
                document_id=1,
                user_id=1,  # 不同的用户
                format="json"
            )

        assert "文档不存在或无权访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_export_unsupported_format(
        self, annotation_service, mock_db, mock_document
    ):
        """测试不支持的导出格式."""
        # Mock CRUD
        from app.crud.annotation import crud_annotation
        from app.crud.document import crud_document
        crud_document.get = AsyncMock(return_value=mock_document)
        crud_annotation.get_by_document = AsyncMock(return_value=[])

        # 执行并验证异常
        with pytest.raises(ValueError) as exc_info:
            await annotation_service.export_annotations(
                db=mock_db,
                document_id=1,
                user_id=1,
                format="xml"  # 不支持的格式
            )

        assert "不支持的导出格式" in str(exc_info.value)


class TestMergeAnnotations:
    """测试合并标注."""

    @pytest.mark.asyncio
    async def test_merge_annotations_success(
        self, annotation_service, mock_db, mock_annotation
    ):
        """测试成功合并标注."""
        # 准备源标注
        source_ann1 = Mock(spec=Annotation)
        source_ann1.page_number = 1
        source_ann1.type = "highlight"
        source_ann1.content = "Note 1"
        source_ann1.selected_text = "Text 1"
        source_ann1.position_data = {"rects": [[0, 0, 100, 100]]}
        source_ann1.color = "#FFFF00"

        source_ann2 = Mock(spec=Annotation)
        source_ann2.page_number = 2
        source_ann2.type = "note"
        source_ann2.content = "Note 2"
        source_ann2.selected_text = None
        source_ann2.position_data = None
        source_ann2.color = None

        # Mock CRUD
        from app.crud.annotation import crud_annotation
        crud_annotation.get_by_document = AsyncMock(
            return_value=[source_ann1, source_ann2]
        )
        crud_annotation.create = AsyncMock(return_value=mock_annotation)

        # 执行
        results = await annotation_service.merge_annotations(
            db=mock_db,
            source_document_id=1,
            target_document_id=2,
            user_id=1,
            page_offset=10  # 页码偏移
        )

        # 验证
        assert len(results) == 2

        # 验证页码调整
        create_calls = crud_annotation.create.call_args_list
        assert len(create_calls) == 2

        # 第一个标注页码应该是 1 + 10 = 11
        first_call_obj = create_calls[0].kwargs["obj_in"]
        assert first_call_obj.page_number == 11

        # 第二个标注页码应该是 2 + 10 = 12
        second_call_obj = create_calls[1].kwargs["obj_in"]
        assert second_call_obj.page_number == 12

    @pytest.mark.asyncio
    async def test_merge_annotations_no_page_number(
        self, annotation_service, mock_db, mock_annotation
    ):
        """测试合并没有页码的标注."""
        # 准备没有页码的标注
        source_ann = Mock(spec=Annotation)
        source_ann.page_number = None
        source_ann.type = "note"
        source_ann.content = "General note"
        source_ann.selected_text = None
        source_ann.position_data = None
        source_ann.color = None

        # Mock CRUD
        from app.crud.annotation import crud_annotation
        crud_annotation.get_by_document = AsyncMock(return_value=[source_ann])
        crud_annotation.create = AsyncMock(return_value=mock_annotation)

        # 执行
        results = await annotation_service.merge_annotations(
            db=mock_db,
            source_document_id=1,
            target_document_id=2,
            user_id=1,
            page_offset=10
        )

        # 验证
        assert len(results) == 1

        # 验证没有页码的标注保持 None
        create_call = crud_annotation.create.call_args
        obj_in = create_call.kwargs["obj_in"]
        assert obj_in.page_number is None


class TestExceptionHandling:
    """测试异常处理覆盖."""

    @pytest.mark.asyncio
    async def test_create_pdf_underline_exception(
        self, annotation_service, mock_db, pdf_highlight
    ):
        """测试创建PDF下划线时出现异常."""
        # Mock CRUD 抛出异常
        from app.crud.annotation import crud_annotation
        crud_annotation.create = AsyncMock(side_effect=Exception("Database error"))

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await annotation_service.create_pdf_underline(
                db=mock_db,
                document_id=1,
                user_id=1,
                underline=pdf_highlight
            )

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_batch_create_exception(
        self, annotation_service, mock_db, pdf_highlight
    ):
        """测试批量创建标注时出现异常."""
        pdf_data = PDFAnnotationData(highlights=[pdf_highlight])

        # Mock 服务方法抛出异常
        annotation_service.create_pdf_highlight = AsyncMock(
            side_effect=Exception("Creation failed")
        )

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await annotation_service.batch_create_pdf_annotations(
                db=mock_db,
                document_id=1,
                user_id=1,
                pdf_data=pdf_data
            )

        assert "Creation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_annotations_by_page_exception(
        self, annotation_service, mock_db
    ):
        """测试获取页面标注时出现异常."""
        # Mock CRUD 抛出异常
        from app.crud.annotation import crud_annotation
        crud_annotation.get_by_document = AsyncMock(
            side_effect=Exception("Query failed")
        )

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await annotation_service.get_pdf_annotations_by_page(
                db=mock_db,
                document_id=1,
                user_id=1,
                page_number=1
            )

        assert "Query failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_merge_annotations_exception(
        self, annotation_service, mock_db
    ):
        """测试合并标注时出现异常."""
        # Mock CRUD 抛出异常
        from app.crud.annotation import crud_annotation
        crud_annotation.get_by_document = AsyncMock(
            side_effect=Exception("Merge failed")
        )

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await annotation_service.merge_annotations(
                db=mock_db,
                source_document_id=1,
                target_document_id=2,
                user_id=1,
                page_offset=0
            )

        assert "Merge failed" in str(exc_info.value)


class TestMarkdownExportAllTypes:
    """测试Markdown导出所有标注类型."""

    @pytest.mark.asyncio
    async def test_export_markdown_all_annotation_types(
        self, annotation_service, mock_db, mock_document
    ):
        """测试Markdown格式导出包含所有类型的标注."""
        # 创建不同类型的标注，包括一个没有页码的
        underline_ann = Mock(spec=Annotation)
        underline_ann.type = "underline"
        underline_ann.page_number = 1
        underline_ann.selected_text = "Underlined text"
        underline_ann.content = "Underline note"
        underline_ann.position_data = None
        underline_ann.color = None
        underline_ann.created_at = Mock()
        underline_ann.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        note_ann = Mock(spec=Annotation)
        note_ann.type = "note"
        note_ann.page_number = 2
        note_ann.selected_text = None
        note_ann.content = "This is a note"
        note_ann.position_data = None
        note_ann.color = None
        note_ann.created_at = Mock()
        note_ann.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        bookmark_ann = Mock(spec=Annotation)
        bookmark_ann.type = "bookmark"
        bookmark_ann.page_number = 3
        bookmark_ann.selected_text = None
        bookmark_ann.content = "Chapter Title"
        bookmark_ann.position_data = None
        bookmark_ann.color = None
        bookmark_ann.created_at = Mock()
        bookmark_ann.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        # 添加一个没有页码的标注
        general_ann = Mock(spec=Annotation)
        general_ann.type = "note"
        general_ann.page_number = None  # 或者 0
        general_ann.selected_text = None
        general_ann.content = "General note without page"
        general_ann.position_data = None
        general_ann.color = None
        general_ann.created_at = Mock()
        general_ann.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        # 添加一个页码为0的标注
        general_ann2 = Mock(spec=Annotation)
        general_ann2.type = "note"
        general_ann2.page_number = 0
        general_ann2.selected_text = None
        general_ann2.content = "Another general note"
        general_ann2.position_data = None
        general_ann2.color = None
        general_ann2.created_at = Mock()
        general_ann2.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        # Mock CRUD
        from app.crud.annotation import crud_annotation
        from app.crud.document import crud_document
        crud_document.get = AsyncMock(return_value=mock_document)
        crud_annotation.get_by_document = AsyncMock(
            return_value=[underline_ann, note_ann, bookmark_ann, general_ann, general_ann2]
        )

        # 执行
        result = await annotation_service.export_annotations(
            db=mock_db,
            document_id=1,
            user_id=1,
            format="markdown"
        )

        # 验证
        assert isinstance(result, str)
        assert "Test Document - 标注汇总" in result
        assert "标注数量: 5" in result

        # 验证所有类型都被包含
        assert "**下划线**: Underlined text" in result
        assert "  - 批注: Underline note" in result
        assert "**笔记**: This is a note" in result
        assert "**书签**: Chapter Title" in result

        # 验证通用标注部分
        assert "## 通用标注" in result
        assert "**笔记**: General note without page" in result

        # 验证页面部分
        assert "## 第 1 页" in result
        assert "## 第 2 页" in result
        assert "## 第 3 页" in result
