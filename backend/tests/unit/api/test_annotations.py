"""Unit tests for annotations endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.annotations import (
    batch_create_annotations,
    batch_create_pdf_annotations,
    copy_annotations,
    create_annotation,
    delete_annotation,
    export_annotations,
    get_annotation,
    get_annotation_statistics,
    get_annotations_by_pages,
    get_document_annotations,
    get_my_annotations,
    get_pdf_page_annotations,
    update_annotation,
)
from app.models.models import Document, User
from app.schemas.annotation import (
    AnnotationBatchCreate,
    AnnotationCreate,
    AnnotationExportRequest,
    AnnotationUpdate,
    PDFAnnotationData,
)


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.is_active = True
    return user


@pytest.fixture
def mock_document():
    """Create mock document."""
    document = MagicMock(spec=Document)
    document.id = 1
    document.user_id = 1
    document.space_id = 1
    document.title = "Test Document"
    document.file_type = "pdf"
    return document


@pytest.fixture
def mock_annotation():
    """Create mock annotation."""
    annotation = MagicMock()
    annotation.id = 1
    annotation.document_id = 1
    annotation.user_id = 1
    annotation.type = "highlight"
    annotation.content = "Test annotation"
    annotation.selected_text = "Selected text"
    annotation.page_number = 1
    annotation.position_data = {"x": 100, "y": 200, "width": 300, "height": 50}
    annotation.color = "#ffff00"
    annotation.created_at = datetime.now(UTC)
    annotation.updated_at = datetime.now(UTC)
    return annotation


class TestGetDocumentAnnotations:
    """Test get document annotations endpoint."""

    @pytest.mark.asyncio
    async def test_get_document_annotations_success(
        self,
        mock_user: User,
        mock_document: Document,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful retrieval of document annotations."""
        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            with patch(
                "app.api.v1.endpoints.annotations.crud_annotation"
            ) as mock_crud_ann:
                mock_crud_doc.get = AsyncMock(return_value=mock_document)
                mock_crud_ann.get_by_document = AsyncMock(
                    return_value=[mock_annotation]
                )

                result = await get_document_annotations(
                    document_id=1,
                    page_number=None,
                    annotation_type=None,
                    skip=0,
                    limit=50,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert result.total == 1
                assert len(result.annotations) == 1
                assert result.page == 1
                assert result.page_size == 50
                assert result.has_next is False

    @pytest.mark.asyncio
    async def test_get_document_annotations_no_permission(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test get annotations without permission."""
        other_user_doc = MagicMock(spec=Document)
        other_user_doc.id = 1
        other_user_doc.user_id = 999  # Different user

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=other_user_doc)

            with pytest.raises(HTTPException) as exc_info:
                await get_document_annotations(
                    document_id=1,
                    page_number=None,
                    annotation_type=None,
                    skip=0,
                    limit=50,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "文档不存在或无权访问" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_document_annotations_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test get annotations for non-existent document."""
        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_document_annotations(
                    document_id=999,
                    page_number=None,
                    annotation_type=None,
                    skip=0,
                    limit=50,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "文档不存在或无权访问" in str(exc_info.value.detail)


class TestGetAnnotationsByPages:
    """Test get annotations by pages endpoint."""

    @pytest.mark.asyncio
    async def test_get_annotations_by_pages_success(
        self,
        mock_user: User,
        mock_document: Document,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful retrieval of annotations by page range."""
        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            with patch(
                "app.api.v1.endpoints.annotations.crud_annotation"
            ) as mock_crud_ann:
                mock_crud_doc.get = AsyncMock(return_value=mock_document)
                mock_crud_ann.get_by_document_pages = AsyncMock(
                    return_value=[mock_annotation]
                )

                result = await get_annotations_by_pages(
                    document_id=1,
                    start_page=1,
                    end_page=5,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert len(result) == 1
                assert result[0].id == 1

    @pytest.mark.asyncio
    async def test_get_annotations_by_pages_invalid_range(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test get annotations with invalid page range."""
        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=mock_document)

            with pytest.raises(HTTPException) as exc_info:
                await get_annotations_by_pages(
                    document_id=1,
                    start_page=5,
                    end_page=1,  # Invalid range
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert "起始页码不能大于结束页码" in str(exc_info.value.detail)


class TestGetPDFAnnotations:
    """Test get PDF annotations endpoint."""

    @pytest.mark.asyncio
    async def test_get_pdf_annotations_success(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test successful retrieval of PDF annotations."""
        mock_document.content_type = "application/pdf"

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            with patch(
                "app.api.v1.endpoints.annotations.crud_annotation"
            ):
                mock_crud_doc.get = AsyncMock(return_value=mock_document)
                mock_service = MagicMock()
                mock_service.get_pdf_annotations_by_page = AsyncMock(
                    return_value={
                        "page": 1,
                        "annotations": [
                            {
                                "id": 1,
                                "type": "highlight",
                                "content": "Test",
                                "bounds": [100, 200, 400, 250],
                            }
                        ],
                    }
                )

                with patch(
                    "app.api.v1.endpoints.annotations.annotation_service", mock_service
                ):
                    result = await get_pdf_page_annotations(
                        document_id=1,
                        page_number=1,
                        db=async_test_db,
                        current_user=mock_user,
                    )

                    assert isinstance(result, dict)
                    assert "page" in result
                    assert result["page"] == 1
                    assert len(result["annotations"]) == 1


class TestCreateAnnotation:
    """Test create annotation endpoint."""

    @pytest.mark.asyncio
    async def test_create_annotation_success(
        self,
        mock_user: User,
        mock_document: Document,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful annotation creation."""
        annotation_data = AnnotationCreate(
            document_id=1,
            type="highlight",
            content="New annotation",
            page_number=1,
            selected_text="Selected text",
        )

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            with patch(
                "app.api.v1.endpoints.annotations.crud_annotation"
            ) as mock_crud_ann:
                mock_crud_doc.get = AsyncMock(return_value=mock_document)
                mock_crud_ann.create = AsyncMock(return_value=mock_annotation)

                result = await create_annotation(
                    annotation_data=annotation_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert result.id == 1
                assert result.content == "Test annotation"

    @pytest.mark.asyncio
    async def test_create_annotation_no_permission(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test create annotation without permission."""
        other_user_doc = MagicMock(spec=Document)
        other_user_doc.id = 1
        other_user_doc.user_id = 999

        annotation_data = AnnotationCreate(
            document_id=1,
            type="highlight",
            content="New annotation",
        )

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=other_user_doc)

            with pytest.raises(HTTPException) as exc_info:
                await create_annotation(
                    annotation_data=annotation_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "文档不存在或无权访问" in str(exc_info.value.detail)


class TestUpdateAnnotation:
    """Test update annotation endpoint."""

    @pytest.mark.asyncio
    async def test_update_annotation_success(
        self,
        mock_user: User,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful annotation update."""
        update_data = AnnotationUpdate(
            content="Updated content",
            color="#ff0000",
            position_data=None
        )

        # 给 updated_annotation 添加必要的属性，以便 model_validate 可以工作
        updated_annotation = MagicMock()
        updated_annotation.id = 1
        updated_annotation.document_id = 1
        updated_annotation.user_id = 1
        updated_annotation.type = "highlight"
        updated_annotation.content = "Updated content"
        updated_annotation.selected_text = "Selected text"
        updated_annotation.page_number = 1
        updated_annotation.position_data = {"x": 100, "y": 200}
        updated_annotation.color = "#ff0000"
        updated_annotation.created_at = datetime.now(UTC)
        updated_annotation.updated_at = datetime.now(UTC)

        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get = AsyncMock(return_value=mock_annotation)
            mock_crud_ann.update = AsyncMock(return_value=updated_annotation)

            result = await update_annotation(
                annotation_id=1,
                annotation_update=update_data,
                db=async_test_db,
                current_user=mock_user,
            )

            assert result.content == "Updated content"

    @pytest.mark.asyncio
    async def test_update_annotation_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test update non-existent annotation."""
        update_data = AnnotationUpdate(
            content="Updated",
            color=None,
            position_data=None
        )

        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await update_annotation(
                    annotation_id=999,
                    annotation_update=update_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "标注不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_annotation_no_permission(
        self,
        mock_user: User,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test update annotation without permission."""
        mock_annotation.user_id = 999  # Different user
        update_data = AnnotationUpdate(
            content="Updated",
            color=None,
            position_data=None
        )

        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get = AsyncMock(return_value=mock_annotation)

            with pytest.raises(HTTPException) as exc_info:
                await update_annotation(
                    annotation_id=1,
                    annotation_update=update_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权修改此标注" in str(exc_info.value.detail)


class TestDeleteAnnotation:
    """Test delete annotation endpoint."""

    @pytest.mark.asyncio
    async def test_delete_annotation_success(
        self,
        mock_user: User,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful annotation deletion."""
        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get = AsyncMock(return_value=mock_annotation)
            mock_crud_ann.remove = AsyncMock(return_value=None)

            result = await delete_annotation(
                annotation_id=1,
                db=async_test_db,
                current_user=mock_user,
            )

            # delete 端点返回 None，只要没有抛出异常就表示成功
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_annotation_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test delete non-existent annotation."""
        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await delete_annotation(
                    annotation_id=999,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "标注不存在" in str(exc_info.value.detail)


class TestExportAnnotations:
    """Test export annotations endpoint."""

    @pytest.mark.asyncio
    async def test_export_annotations_markdown(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test export annotations as markdown."""
        export_request = AnnotationExportRequest(document_ids=[1], format="markdown")

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            with patch(
                "app.api.v1.endpoints.annotations.annotation_service"
            ) as mock_service:
                mock_crud_doc.get = AsyncMock(return_value=mock_document)
                mock_service.export_annotations = AsyncMock(
                    return_value="# Annotations\n\n- Test annotation"
                )

                result = await export_annotations(
                    request=export_request,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert result["format"] == "markdown"
                assert "content" in result

    @pytest.mark.asyncio
    async def test_export_multiple_documents_not_supported(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test export with multiple documents (not supported)."""
        export_request = AnnotationExportRequest(
            document_ids=[1, 2, 3], format="markdown"
        )

        # 检查第一个文档的权限
        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=mock_document)

            with pytest.raises(HTTPException) as exc_info:
                await export_annotations(
                    request=export_request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert "暂不支持多文档批量导出" in str(exc_info.value.detail)


class TestCopyAnnotations:
    """Test copy annotations endpoint."""

    @pytest.mark.asyncio
    async def test_copy_annotations_success(
        self,
        mock_user: User,
        mock_document: Document,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful annotation copying."""
        target_doc = MagicMock(spec=Document)
        target_doc.id = 2
        target_doc.user_id = 1

        new_annotation = MagicMock()
        new_annotation.id = 2
        new_annotation.document_id = 2
        new_annotation.user_id = 1
        new_annotation.type = "highlight"
        new_annotation.content = "Test annotation"
        new_annotation.selected_text = "Selected text"
        new_annotation.page_number = 1
        new_annotation.position_data = {"x": 100, "y": 200}
        new_annotation.color = "#ffff00"
        new_annotation.created_at = datetime.now(UTC)
        new_annotation.updated_at = datetime.now(UTC)

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            with patch(
                "app.api.v1.endpoints.annotations.crud_annotation"
            ) as mock_crud_ann:
                mock_crud_doc.get = AsyncMock(side_effect=[mock_document, target_doc])
                mock_crud_ann.copy_annotations = AsyncMock(
                    return_value=[new_annotation]
                )

                result = await copy_annotations(
                    source_document_id=1,
                    target_document_id=2,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert len(result) == 1
                assert result[0].document_id == 2

    @pytest.mark.asyncio
    async def test_copy_annotations_no_source_permission(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test copy annotations without source document permission."""
        other_user_doc = MagicMock(spec=Document)
        other_user_doc.id = 1
        other_user_doc.user_id = 999

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=other_user_doc)

            with pytest.raises(HTTPException) as exc_info:
                await copy_annotations(
                    source_document_id=1,
                    target_document_id=2,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "源文档不存在或无权访问" in str(exc_info.value.detail)


class TestGetMyAnnotations:
    """Test get my annotations endpoint."""

    @pytest.mark.asyncio
    async def test_get_my_annotations_success(
        self,
        mock_user: User,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful retrieval of user annotations."""
        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get_user_annotations = AsyncMock(
                return_value=([mock_annotation], 1)
            )

            result = await get_my_annotations(
                annotation_type=None,
                skip=0,
                limit=20,
                db=async_test_db,
                current_user=mock_user,
            )

            assert result.total == 1
            assert len(result.annotations) == 1
            assert result.page == 1
            assert result.has_next is False

    @pytest.mark.asyncio
    async def test_get_my_annotations_with_type_filter(
        self,
        mock_user: User,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test get my annotations with type filter."""
        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get_user_annotations = AsyncMock(
                return_value=([mock_annotation], 1)
            )

            await get_my_annotations(
                annotation_type="highlight",
                skip=0,
                limit=20,
                db=async_test_db,
                current_user=mock_user,
            )

            mock_crud_ann.get_user_annotations.assert_called_once_with(
                db=async_test_db,
                user_id=1,
                annotation_type="highlight",
                skip=0,
                limit=20,
            )


class TestGetAnnotationStatistics:
    """Test get annotation statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_statistics_all_documents(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test get statistics for all user documents."""
        stats = {
            "total_annotations": 100,
            "by_type": {"highlight": 60, "note": 30, "bookmark": 10},
            "by_document": {"doc1": 50, "doc2": 50},
        }

        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get_statistics = AsyncMock(return_value=stats)

            result = await get_annotation_statistics(
                document_id=None,
                db=async_test_db,
                current_user=mock_user,
            )

            assert result.total_annotations == 100
            assert result.by_type["highlight"] == 60

    @pytest.mark.asyncio
    async def test_get_statistics_specific_document(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test get statistics for specific document."""
        stats = {
            "total_annotations": 20,
            "by_type": {"highlight": 15, "note": 5},
        }

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            with patch(
                "app.api.v1.endpoints.annotations.crud_annotation"
            ) as mock_crud_ann:
                mock_crud_doc.get = AsyncMock(return_value=mock_document)
                mock_crud_ann.get_statistics = AsyncMock(return_value=stats)

                result = await get_annotation_statistics(
                    document_id=1,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert result.total_annotations == 20

    @pytest.mark.asyncio
    async def test_get_statistics_document_no_permission(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test get statistics for document without permission."""
        other_user_doc = MagicMock(spec=Document)
        other_user_doc.id = 1
        other_user_doc.user_id = 999

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=other_user_doc)

            with pytest.raises(HTTPException) as exc_info:
                await get_annotation_statistics(
                    document_id=1,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "文档不存在或无权访问" in str(exc_info.value.detail)


class TestGetAnnotation:
    """Test get annotation detail endpoint."""

    @pytest.mark.asyncio
    async def test_get_annotation_success(
        self,
        mock_user: User,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful get annotation detail."""
        # 给 mock_annotation 添加 document 属性
        mock_annotation.document = MagicMock()
        mock_annotation.document.title = "Test Document"
        mock_annotation.document.filename = "test.pdf"

        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get = AsyncMock(return_value=mock_annotation)

            result = await get_annotation(
                annotation_id=1,
                db=async_test_db,
                current_user=mock_user,
            )

            assert result.id == 1
            assert result.document_title == "Test Document"
            assert result.document_filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_get_annotation_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test get non-existent annotation."""
        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_annotation(
                    annotation_id=999,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "标注不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_annotation_no_permission(
        self,
        mock_user: User,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test get annotation without permission."""
        mock_annotation.user_id = 999

        with patch("app.api.v1.endpoints.annotations.crud_annotation") as mock_crud_ann:
            mock_crud_ann.get = AsyncMock(return_value=mock_annotation)

            with pytest.raises(HTTPException) as exc_info:
                await get_annotation(
                    annotation_id=1,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权访问此标注" in str(exc_info.value.detail)


class TestBatchCreateAnnotations:
    """Test batch create annotations endpoint."""

    @pytest.mark.asyncio
    async def test_batch_create_success(
        self,
        mock_user: User,
        mock_document: Document,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful batch annotation creation."""
        from app.schemas.annotation import AnnotationBase

        batch_data = AnnotationBatchCreate(
            document_id=1,
            annotations=[
                AnnotationBase(
                    type="highlight",
                    content="Annotation 1",
                    page_number=1,
                ),
                AnnotationBase(
                    type="note",
                    content="Annotation 2",
                    page_number=2,
                ),
            ],
        )

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            with patch(
                "app.api.v1.endpoints.annotations.crud_annotation"
            ) as mock_crud_ann:
                mock_crud_doc.get = AsyncMock(return_value=mock_document)
                mock_crud_ann.batch_create = AsyncMock(
                    return_value=[mock_annotation, mock_annotation]
                )

                result = await batch_create_annotations(
                    batch_data=batch_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert len(result) == 2

    @pytest.mark.asyncio
    async def test_batch_create_no_permission(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test batch create without document permission."""
        other_user_doc = MagicMock(spec=Document)
        other_user_doc.id = 1
        other_user_doc.user_id = 999

        from app.schemas.annotation import AnnotationBase

        batch_data = AnnotationBatchCreate(
            document_id=1,
            annotations=[
                AnnotationBase(
                    type="highlight",
                    content="Test",
                ),
            ],
        )

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=other_user_doc)

            with pytest.raises(HTTPException) as exc_info:
                await batch_create_annotations(
                    batch_data=batch_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "文档不存在或无权访问" in str(exc_info.value.detail)


class TestBatchCreatePDFAnnotations:
    """Test batch create PDF annotations endpoint."""

    @pytest.mark.asyncio
    async def test_batch_create_pdf_success(
        self,
        mock_user: User,
        mock_document: Document,
        mock_annotation,
        async_test_db: AsyncSession,
    ):
        """Test successful batch PDF annotation creation."""
        mock_document.content_type = "application/pdf"

        from app.schemas.annotation import PDFHighlight

        pdf_data = PDFAnnotationData(
            highlights=[
                PDFHighlight(
                    page=1,
                    text="Test highlight",
                    rects=[[100, 200, 300, 250]],
                    color="#FFFF00",
                    note="Test note",
                )
            ]
        )

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            with patch(
                "app.api.v1.endpoints.annotations.annotation_service"
            ) as mock_service:
                mock_crud_doc.get = AsyncMock(return_value=mock_document)
                mock_service.batch_create_pdf_annotations = AsyncMock(
                    return_value=[mock_annotation]
                )

                result = await batch_create_pdf_annotations(
                    document_id=1,
                    pdf_data=pdf_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_batch_create_pdf_non_pdf_document(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test batch create PDF annotations for non-PDF document."""
        mock_document.content_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        pdf_data = PDFAnnotationData(highlights=[])

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=mock_document)

            with pytest.raises(HTTPException) as exc_info:
                await batch_create_pdf_annotations(
                    document_id=1,
                    pdf_data=pdf_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert "此文档不是PDF格式" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_batch_create_pdf_no_permission(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test batch create PDF annotations without permission."""
        other_user_doc = MagicMock(spec=Document)
        other_user_doc.id = 1
        other_user_doc.user_id = 999

        pdf_data = PDFAnnotationData(highlights=[])

        with patch("app.api.v1.endpoints.annotations.crud_document") as mock_crud_doc:
            mock_crud_doc.get = AsyncMock(return_value=other_user_doc)

            with pytest.raises(HTTPException) as exc_info:
                await batch_create_pdf_annotations(
                    document_id=1,
                    pdf_data=pdf_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "文档不存在或无权访问" in str(exc_info.value.detail)
