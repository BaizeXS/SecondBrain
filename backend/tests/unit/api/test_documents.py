"""documents.py 的完整单元测试"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.documents import (
    analyze_url,
    batch_import_urls,
    delete_document,
    download_document,
    get_document,
    get_document_content,
    get_document_preview,
    get_documents,
    get_web_snapshot,
    import_url,
    update_document,
    upload_document,
)
from app.models.models import Document, Space, User
from app.schemas.documents import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
)
from app.schemas.web_import import (
    BatchURLImportRequest,
    URLAnalysisRequest,
    URLAnalysisResponse,
    URLImportRequest,
    URLImportResponse,
    WebSnapshotResponse,
)


def create_mock_document(
    id: int = 1,
    space_id: int = 1,
    filename: str = "test.txt",
    title: str = "Test Document",
    content: str = "Test content",
    user_id: int = 1,
    **kwargs,
) -> MagicMock:
    """创建一个符合DocumentResponse schema的mock Document对象"""
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = id
    mock_doc.space_id = space_id
    mock_doc.filename = filename
    mock_doc.title = title
    mock_doc.content = content
    mock_doc.content_type = kwargs.get("content_type", "text/plain")
    mock_doc.file_size = kwargs.get("file_size", len(content) if content else 0)
    mock_doc.processing_status = kwargs.get("processing_status", "completed")
    mock_doc.tags = kwargs.get("tags", None)
    mock_doc.language = kwargs.get("language", "en")
    mock_doc.summary = kwargs.get("summary", None)
    mock_doc.meta_data = kwargs.get("meta_data", None)
    mock_doc.original_filename = kwargs.get("original_filename", None)
    mock_doc.file_url = kwargs.get("file_url", None)
    mock_doc.extraction_status = kwargs.get("extraction_status", "completed")
    mock_doc.embedding_status = kwargs.get("embedding_status", "completed")
    mock_doc.user_id = user_id
    mock_doc.parent_id = kwargs.get("parent_id", None)
    mock_doc.created_at = kwargs.get("created_at", datetime.now(UTC))
    mock_doc.updated_at = kwargs.get("updated_at", None)
    return mock_doc


class TestUploadDocument:
    """测试文档上传功能"""

    @pytest.mark.asyncio
    async def test_upload_document_success(self):
        """测试成功上传文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1  # 用户是所有者

        # 创建模拟文件
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"Test content")

        mock_document = create_mock_document(
            id=1,
            space_id=1,
            filename="test.txt",
            title="Test Document",
            content="Test content",
            user_id=1,
            tags=["test"],
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.update = AsyncMock(return_value=mock_document)

            with patch(
                "app.api.v1.endpoints.documents.document_service"
            ) as mock_service:
                mock_service.create_document = AsyncMock(return_value=mock_document)

                result = await upload_document(
                    space_id=1,
                    file=mock_file,
                    title="Test Document",
                    tags="test",
                    db=mock_db,
                    current_user=mock_user,
                )

                assert isinstance(result, DocumentResponse)
                assert result.id == 1
                assert result.filename == "test.txt"
                assert result.title == "Test Document"

    @pytest.mark.asyncio
    async def test_upload_document_space_not_found(self):
        """测试上传文档到不存在的空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await upload_document(
                    space_id=999,
                    file=mock_file,
                    title=None,
                    tags=None,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "空间不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_document_no_permission(self):
        """测试无权限上传文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1  # 其他用户是所有者

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_space.get_user_access = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await upload_document(
                    space_id=1,
                    file=mock_file,
                    title=None,
                    tags=None,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "无权在此空间上传文档" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_document_invalid_file_type(self):
        """测试上传不支持的文件类型"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.exe"
        mock_file.content_type = "application/x-executable"

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

            with pytest.raises(HTTPException) as exc_info:
                await upload_document(
                    space_id=1,
                    file=mock_file,
                    title=None,
                    tags=None,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "不支持的文件类型" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_document_file_too_large(self):
        """测试上传超大文件"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "large.txt"
        mock_file.content_type = "text/plain"
        # 创建超大内容
        mock_file.read = AsyncMock(return_value=b"x" * (1024 * 1024 * 101))  # 101MB

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

            with pytest.raises(HTTPException) as exc_info:
                await upload_document(
                    space_id=1,
                    file=mock_file,
                    title=None,
                    tags=None,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert (
                exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
            assert "文件大小超过限制" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_document_empty_file(self):
        """测试上传空文件"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "empty.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"")

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

            with pytest.raises(HTTPException) as exc_info:
                await upload_document(
                    space_id=1,
                    file=mock_file,
                    title=None,
                    tags=None,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "文件为空" in str(exc_info.value.detail)


class TestGetDocuments:
    """测试获取文档列表功能"""

    @pytest.mark.asyncio
    async def test_get_documents_by_space(self):
        """测试按空间获取文档列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1
        mock_space.is_public = False

        mock_documents = []
        for i in range(3):
            mock_doc = create_mock_document(
                id=i + 1,
                space_id=1,
                filename=f"doc{i + 1}.txt",
                title=f"Document {i + 1}",
                content=f"Content {i + 1}",
                user_id=1,
                file_size=100,
            )
            mock_documents.append(mock_doc)

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.get_by_space = AsyncMock(
                return_value=mock_documents
            )

            result = await get_documents(
                space_id=1,
                skip=0,
                limit=20,
                search=None,
                db=mock_db,
                current_user=mock_user,
            )

            assert isinstance(result, DocumentListResponse)
            assert result.total == 3
            assert len(result.documents) == 3
            assert result.page == 1

    @pytest.mark.asyncio
    async def test_get_documents_all_user_documents(self):
        """测试获取用户所有文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_documents = []
        for i in range(5):
            mock_doc = create_mock_document(
                id=i + 1,
                space_id=i % 2 + 1,
                filename=f"doc{i + 1}.txt",
                title=f"Document {i + 1}",
                content=f"Content {i + 1}",
                user_id=1,
                file_size=100,
            )
            mock_documents.append(mock_doc)

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get_user_documents = AsyncMock(
                return_value=mock_documents
            )

            result = await get_documents(
                space_id=0,
                skip=0,
                limit=20,
                search=None,
                processing_status=None,
                db=mock_db,
                current_user=mock_user,
            )

            assert isinstance(result, DocumentListResponse)
            assert result.total == 5
            assert len(result.documents) == 5
            assert result.page == 1
            assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_get_documents_with_search(self):
        """测试搜索文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1
        mock_space.is_public = False

        mock_documents = []
        mock_doc = create_mock_document(
            id=1,
            space_id=1,
            filename="important.txt",
            title="Important Document",
            content="This is important content",
            user_id=1,
            file_size=100,
        )
        mock_documents.append(mock_doc)

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.search = AsyncMock(return_value=mock_documents)

            result = await get_documents(
                space_id=1,
                skip=0,
                limit=20,
                search="important",
                db=mock_db,
                current_user=mock_user,
            )

            assert result.total == 1
            assert result.documents[0].title == "Important Document"

    @pytest.mark.asyncio
    async def test_get_documents_no_access(self):
        """测试无权限访问空间文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1
        mock_space.is_public = False

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_space.get_user_access = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_documents(
                    space_id=1,
                    skip=0,
                    limit=20,
                    search=None,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "无权访问此空间" in str(exc_info.value.detail)


class TestGetDocument:
    """测试获取单个文档功能"""

    @pytest.mark.asyncio
    async def test_get_document_success(self):
        """测试成功获取文档详情"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            space_id=1,
            filename="test.txt",
            title="Test Document",
            content="Test content",
            user_id=1,
            tags=["test"],
        )

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=mock_document)

            result = await get_document(
                document_id=1, db=mock_db, current_user=mock_user
            )

            assert isinstance(result, DocumentResponse)
            assert result.id == 1
            assert result.title == "Test Document"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self):
        """测试获取不存在的文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_document(document_id=999, db=mock_db, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "文档不存在或无权访问" in str(exc_info.value.detail)


class TestUpdateDocument:
    """测试更新文档功能"""

    @pytest.mark.asyncio
    async def test_update_document_success(self):
        """测试成功更新文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            space_id=1,
            user_id=1,
        )

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        document_update = DocumentUpdate(
            filename="updated_file.pdf",
            tags=["updated", "test"],
        )

        mock_updated_doc = create_mock_document(
            id=1,
            space_id=1,
            filename="test.txt",
            title="Updated Title",
            content="Test content",
            user_id=1,
            tags=["updated", "test"],
            updated_at=datetime.now(UTC),
        )

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=mock_document)

            with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
                mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
                mock_crud.crud_document.update = AsyncMock(
                    return_value=mock_updated_doc
                )

                result = await update_document(
                    document_id=1,
                    document_data=document_update,
                    db=mock_db,
                    current_user=mock_user,
                )

                assert result.title == "Updated Title"
                assert result.tags == ["updated", "test"]

    @pytest.mark.asyncio
    async def test_update_document_no_permission(self):
        """测试无权限更新文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2

        mock_document = create_mock_document(
            id=1,
            space_id=1,
            user_id=1,
        )

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        document_update = DocumentUpdate(filename="hacked.pdf")

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=mock_document)

            with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
                mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
                mock_crud.crud_space.get_user_access = AsyncMock(return_value=None)

                with pytest.raises(HTTPException) as exc_info:
                    await update_document(
                        document_id=1,
                        document_data=document_update,
                        db=mock_db,
                        current_user=mock_user,
                    )

                assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
                assert "无权编辑此文档" in str(exc_info.value.detail)


class TestDeleteDocument:
    """测试删除文档功能"""

    @pytest.mark.asyncio
    async def test_delete_document_success(self):
        """测试成功删除文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            space_id=1,
            user_id=1,
        )

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=mock_document)
            mock_service.delete_document = AsyncMock(return_value=None)

            with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
                mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

                # 应该成功删除，无返回值
                await delete_document(document_id=1, db=mock_db, current_user=mock_user)

                mock_service.delete_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_no_permission(self):
        """测试无权限删除文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2

        mock_document = create_mock_document(
            id=1,
            space_id=1,
            user_id=1,
        )

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        mock_access = MagicMock()
        mock_access.can_delete = False

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=mock_document)

            with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
                mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
                mock_crud.crud_space.get_user_access = AsyncMock(
                    return_value=mock_access
                )

                with pytest.raises(HTTPException) as exc_info:
                    await delete_document(
                        document_id=1, db=mock_db, current_user=mock_user
                    )

                assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
                assert "无权删除此文档" in str(exc_info.value.detail)


class TestDownloadDocument:
    """测试下载文档功能"""

    @pytest.mark.asyncio
    async def test_download_document_success(self):
        """测试成功下载文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            filename="test.txt",
            content="Test content",
            content_type="text/plain",
        )

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=mock_document)

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_file = MagicMock()
                mock_file.name = "/tmp/test_test.txt"
                mock_file.__enter__ = MagicMock(return_value=mock_file)
                mock_file.__exit__ = MagicMock(return_value=None)
                mock_temp.return_value = mock_file

                result = await download_document(
                    document_id=1, db=mock_db, current_user=mock_user
                )

                assert isinstance(result, FileResponse)
                assert result.filename == "test.txt"
                assert result.media_type == "text/plain"

    @pytest.mark.asyncio
    async def test_download_document_no_content(self):
        """测试下载无内容的文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            filename="empty.txt",
            content="",
        )

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=mock_document)

            with pytest.raises(HTTPException) as exc_info:
                await download_document(
                    document_id=1, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "文档内容不存在" in str(exc_info.value.detail)


class TestGetDocumentPreview:
    """测试文档预览功能"""

    @pytest.mark.asyncio
    async def test_preview_pdf_document(self):
        """测试预览PDF文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            user_id=1,
            space_id=0,
            filename="test.pdf",
            title="Test PDF",
            content_type="application/pdf",
            content="Extracted PDF text",
            file_url=None,
            meta_data={"page_count": 10},
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get = AsyncMock(return_value=mock_document)

            result = await get_document_preview(
                document_id=1,
                page=1,
                format="html",
                db=mock_db,
                current_user=mock_user,
            )

            assert result["type"] == "pdf"
            assert result["filename"] == "test.pdf"
            assert result["page_count"] == 10
            assert result["current_page"] == 1

    @pytest.mark.asyncio
    async def test_preview_image_document(self):
        """测试预览图片文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            user_id=1,
            space_id=0,
            filename="test.jpg",
            title="Test Image",
            content_type="image/jpeg",
            content="",
            file_url=None,
            meta_data={"width": 1920, "height": 1080},
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get = AsyncMock(return_value=mock_document)

            result = await get_document_preview(
                document_id=1,
                page=None,
                format="html",
                db=mock_db,
                current_user=mock_user,
            )

            assert result["type"] == "image"
            assert result["filename"] == "test.jpg"
            assert result["width"] == 1920
            assert result["height"] == 1080

    @pytest.mark.asyncio
    async def test_preview_text_document_html(self):
        """测试预览文本文档为HTML格式"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            user_id=1,
            space_id=0,
            filename="test.md",
            title="Test Markdown",
            content_type="text/markdown",
            content="# Test\n\nThis is a test.",
            language="en",
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get = AsyncMock(return_value=mock_document)

            result = await get_document_preview(
                document_id=1,
                page=None,
                format="html",
                db=mock_db,
                current_user=mock_user,
            )

            assert result["type"] == "text"
            assert result["format"] == "html"
            assert "<pre>" in result["content"] or "<h1>" in result["content"]

    @pytest.mark.asyncio
    async def test_preview_no_permission(self):
        """测试无权限预览文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2

        mock_document = create_mock_document(
            id=1,
            user_id=1,
            space_id=1,
        )

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.is_public = False
        mock_space.user_id = 1

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get = AsyncMock(return_value=mock_document)
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_space.get_user_access = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_document_preview(
                    document_id=1,
                    page=None,
                    format="html",
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "无权访问此文档" in str(exc_info.value.detail)


class TestGetDocumentContent:
    """测试获取文档内容功能"""

    @pytest.mark.asyncio
    async def test_get_document_content_success(self):
        """测试成功获取文档内容片段"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            user_id=1,
            space_id=0,
            title="Test Document",
            content="This is a very long document content that needs pagination.",
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get = AsyncMock(return_value=mock_document)

            result = await get_document_content(
                document_id=1,
                start=0,
                length=20,
                db=mock_db,
                current_user=mock_user,
            )

            assert result["document_id"] == 1
            assert result["content"] == "This is a very long "
            assert result["start"] == 0
            assert result["end"] == 20
            assert result["has_more"] is True

    @pytest.mark.asyncio
    async def test_get_document_content_no_content(self):
        """测试获取无内容文档"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(
            id=1,
            user_id=1,
            content="",
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get = AsyncMock(return_value=mock_document)

            with pytest.raises(HTTPException) as exc_info:
                await get_document_content(
                    document_id=1,
                    start=0,
                    length=100,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "没有可用的文本内容" in str(exc_info.value.detail)


class TestImportURL:
    """测试URL导入功能"""

    @pytest.mark.asyncio
    async def test_import_url_success(self):
        """测试成功导入URL"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        import_request = URLImportRequest(
            url=HttpUrl("https://example.com/article"),
            space_id=1,
            title="Example Article",
            tags=["web", "import"],
            save_snapshot=True,
            extract_links=False,
        )

        mock_document = create_mock_document(
            id=1,
            title="Example Article",
        )

        import_result = {
            "status": "success",
            "document_id": 1,
            "metadata": {
                "url": "https://example.com/article",
                "domain": "example.com",
                "title": "Example Article",
                "author": "John Doe",
                "published_time": "2024-01-01",
                "fetched_at": datetime.now(UTC),
            },
        }

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.get = AsyncMock(return_value=mock_document)

            with patch(
                "app.api.v1.endpoints.documents.document_service"
            ) as mock_service:
                mock_service.import_from_url = AsyncMock(return_value=import_result)

                result = await import_url(
                    import_data=import_request,
                    db=mock_db,
                    current_user=mock_user,
                )

                assert isinstance(result, URLImportResponse)
                assert result.document_id == 1
                assert result.status == "success"
                assert result.title == "Example Article"

    @pytest.mark.asyncio
    async def test_import_url_failed(self):
        """测试导入URL失败"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        import_request = URLImportRequest(
            url=HttpUrl("https://invalid.com/404"),
            space_id=1,
            title=None,
            tags=None,
            save_snapshot=True,
            extract_links=False,
        )

        import_result = {
            "status": "error",
            "error": "Failed to fetch URL: 404 Not Found",
        }

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

            with patch(
                "app.api.v1.endpoints.documents.document_service"
            ) as mock_service:
                mock_service.import_from_url = AsyncMock(return_value=import_result)

                with pytest.raises(HTTPException) as exc_info:
                    await import_url(
                        import_data=import_request,
                        db=mock_db,
                        current_user=mock_user,
                    )

                assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
                assert "Failed to fetch URL" in str(exc_info.value.detail)


class TestBatchImportURLs:
    """测试批量URL导入功能"""

    @pytest.mark.asyncio
    async def test_batch_import_urls_success(self):
        """测试成功批量导入URLs"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        batch_request = BatchURLImportRequest(
            urls=[
                HttpUrl("https://example.com/article1"),
                HttpUrl("https://example.com/article2"),
            ],
            space_id=1,
            tags=["batch", "import"],
            save_snapshot=False,
        )

        mock_doc1 = create_mock_document(id=1, title="Article 1")
        mock_doc2 = create_mock_document(id=2, title="Article 2")

        batch_results = [
            {
                "status": "success",
                "document_id": 1,
                "url": "https://example.com/article1",
                "metadata": {
                    "url": "https://example.com/article1",
                    "domain": "example.com",
                    "title": "Article 1",
                    "fetched_at": datetime.now(UTC),
                },
            },
            {
                "status": "success",
                "document_id": 2,
                "url": "https://example.com/article2",
                "metadata": {
                    "url": "https://example.com/article2",
                    "domain": "example.com",
                    "title": "Article 2",
                    "fetched_at": datetime.now(UTC),
                },
            },
        ]

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.get = AsyncMock(side_effect=[mock_doc1, mock_doc2])

            with patch(
                "app.api.v1.endpoints.documents.document_service"
            ) as mock_service:
                mock_service.batch_import_urls = AsyncMock(return_value=batch_results)

                results = await batch_import_urls(
                    import_data=batch_request,
                    db=mock_db,
                    current_user=mock_user,
                )

                assert len(results) == 2
                assert all(r.status == "success" for r in results)
                assert results[0].title == "Article 1"
                assert results[1].title == "Article 2"

    @pytest.mark.asyncio
    async def test_batch_import_urls_partial_failure(self):
        """测试批量导入部分失败"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        batch_request = BatchURLImportRequest(
            urls=[
                HttpUrl("https://example.com/article1"),
                HttpUrl("https://invalid.com/404"),
            ],
            space_id=1,
            tags=None,
            save_snapshot=True,
        )

        mock_doc1 = create_mock_document(id=1, title="Article 1")

        batch_results = [
            {
                "status": "success",
                "document_id": 1,
                "url": "https://example.com/article1",
                "metadata": {
                    "url": "https://example.com/article1",
                    "domain": "example.com",
                    "title": "Article 1",
                    "fetched_at": datetime.now(UTC),
                },
            },
            {
                "status": "error",
                "url": "https://invalid.com/404",
                "error": "404 Not Found",
            },
        ]

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.get = AsyncMock(return_value=mock_doc1)

            with patch(
                "app.api.v1.endpoints.documents.document_service"
            ) as mock_service:
                mock_service.batch_import_urls = AsyncMock(return_value=batch_results)

                results = await batch_import_urls(
                    import_data=batch_request,
                    db=mock_db,
                    current_user=mock_user,
                )

                assert len(results) == 2
                assert results[0].status == "success"
                assert results[1].status == "error"
                assert results[1].error == "404 Not Found"


class TestGetWebSnapshot:
    """测试获取网页快照功能"""

    @pytest.mark.asyncio
    async def test_get_web_snapshot_success(self):
        """测试成功获取网页快照"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        snapshot_data = {
            "document_id": 1,
            "url": "https://example.com",
            "title": "Example Page",
            "snapshot_html": "<html><body>Snapshot</body></html>",
            "snapshot_markdown": "# Example Page\nSnapshot",
            "metadata": {"title": "Example Page", "description": "Example description"},
            "created_at": datetime.now(UTC),
        }

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_web_snapshot = AsyncMock(return_value=snapshot_data)

            result = await get_web_snapshot(
                document_id=1, db=mock_db, current_user=mock_user
            )

            assert isinstance(result, WebSnapshotResponse)
            assert result.document_id == 1
            assert result.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_get_web_snapshot_not_found(self):
        """测试获取不存在的快照"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_web_snapshot = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_web_snapshot(
                    document_id=1, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "快照不存在" in str(exc_info.value.detail)


class TestAnalyzeURL:
    """测试URL分析功能"""

    @pytest.mark.asyncio
    async def test_analyze_url_success(self):
        """测试成功分析URL"""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        analysis_request = URLAnalysisRequest(url=HttpUrl("https://example.com/article"))

        analysis_result = {
            "url": "https://example.com/article",
            "can_import": True,
            "title": "Example Article",
            "description": "This is an example article",
            "content_preview": "This is an example article preview...",
            "metadata": {
                "url": "https://example.com/article",
                "domain": "example.com",
                "title": "Example Article",
                "description": "This is an example article",
                "author": "John Doe",
                "published_time": "2024-01-01",
                "fetched_at": datetime.now(UTC),
            },
            "word_count": 500,
            "links_count": 10,
            "images_count": 3,
            "suggested_tags": ["article", "example"],
        }

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.analyze_url = AsyncMock(return_value=analysis_result)

            result = await analyze_url(
                analysis_data=analysis_request,
                current_user=mock_user,
            )

            assert isinstance(result, URLAnalysisResponse)
            assert result.can_import is True
            assert result.title == "Example Article"

    @pytest.mark.asyncio
    async def test_analyze_url_cannot_import(self):
        """测试分析无法导入的URL"""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        analysis_request = URLAnalysisRequest(url=HttpUrl("https://example.com/blocked"))

        analysis_result = {
            "url": "https://example.com/blocked",
            "can_import": False,
            "error": "Access denied by robots.txt",
        }

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.analyze_url = AsyncMock(return_value=analysis_result)

            with pytest.raises(HTTPException) as exc_info:
                await analyze_url(
                    analysis_data=analysis_request,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Access denied" in str(exc_info.value.detail)


class TestAdditionalCoverage:
    """Additional tests to improve code coverage"""

    @pytest.mark.asyncio
    async def test_upload_document_no_content_type(self):
        """Test uploading file without content type"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = None  # No content type

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

            with pytest.raises(HTTPException) as exc_info:
                await upload_document(
                    space_id=1,
                    file=mock_file,
                    title=None,
                    tags=None,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "无法识别文件类型" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_document_service_error(self):
        """Test upload document with service error"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"Test content")

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

            with patch(
                "app.api.v1.endpoints.documents.document_service"
            ) as mock_service:
                mock_service.create_document = AsyncMock(
                    side_effect=Exception("Service error")
                )

                with pytest.raises(HTTPException) as exc_info:
                    await upload_document(
                        space_id=1,
                        file=mock_file,
                        title=None,
                        tags=None,
                        db=mock_db,
                        current_user=mock_user,
                    )

                assert (
                    exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                assert "上传文档失败" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_documents_space_not_found(self):
        """Test getting documents from non-existent space"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_documents(
                    space_id=999,
                    skip=0,
                    limit=20,
                    search=None,
                    processing_status=None,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "空间不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_documents_all_with_search(self):
        """Test getting all user documents with search filter"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_documents = [
            create_mock_document(
                id=1, title="Important Document", content="Important content"
            ),
            create_mock_document(id=2, title="Other Doc", content="Other content"),
        ]

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get_user_documents = AsyncMock(
                return_value=mock_documents
            )

            result = await get_documents(
                space_id=0,
                skip=0,
                limit=20,
                search="Important",
                processing_status=None,
                db=mock_db,
                current_user=mock_user,
            )

            assert result.total == 1
            assert result.documents[0].title == "Important Document"

    @pytest.mark.asyncio
    async def test_get_documents_all_with_processing_status(self):
        """Test getting all user documents with processing status filter"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_documents = [
            create_mock_document(id=1, processing_status="completed"),
            create_mock_document(id=2, processing_status="processing"),
        ]

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get_user_documents = AsyncMock(
                return_value=mock_documents
            )

            result = await get_documents(
                space_id=0,
                skip=0,
                limit=20,
                search=None,
                processing_status="processing",
                db=mock_db,
                current_user=mock_user,
            )

            assert result.total == 1
            assert result.documents[0].processing_status == "processing"

    @pytest.mark.asyncio
    async def test_update_document_not_found(self):
        """Test updating non-existent document"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        document_update = DocumentUpdate(filename="new_title.pdf")

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await update_document(
                    document_id=999,
                    document_data=document_update,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "文档不存在或无权访问" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_document_service_error(self):
        """Test update document with service error"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(id=1, space_id=1, user_id=1)
        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        document_update = DocumentUpdate(filename="new_title.pdf")

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=mock_document)

            with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
                mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
                mock_crud.crud_document.update = AsyncMock(
                    side_effect=Exception("Update failed")
                )

                with pytest.raises(HTTPException) as exc_info:
                    await update_document(
                        document_id=1,
                        document_data=document_update,
                        db=mock_db,
                        current_user=mock_user,
                    )

                assert (
                    exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                assert "更新文档失败" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self):
        """Test deleting non-existent document"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await delete_document(
                    document_id=999,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "文档不存在或无权访问" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_document_service_error(self):
        """Test delete document with service error"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_document = create_mock_document(id=1, space_id=1, user_id=1)
        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=mock_document)
            mock_service.delete_document = AsyncMock(
                side_effect=Exception("Delete failed")
            )

            with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
                mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

                with pytest.raises(HTTPException) as exc_info:
                    await delete_document(
                        document_id=1,
                        db=mock_db,
                        current_user=mock_user,
                    )

                assert (
                    exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                assert "删除文档失败" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_download_document_not_found(self):
        """Test downloading non-existent document"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with patch("app.api.v1.endpoints.documents.document_service") as mock_service:
            mock_service.get_document_by_id = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await download_document(
                    document_id=999,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "文档不存在或无权访问" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_document_preview_not_found(self):
        """Test getting preview of non-existent document"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_document_preview(
                    document_id=999,
                    page=None,
                    format="html",
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "文档不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_document_content_not_found(self):
        """Test getting content of non-existent document"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_document.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_document_content(
                    document_id=999,
                    start=0,
                    length=100,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "文档不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_import_url_space_not_found(self):
        """Test importing URL to non-existent space"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        import_request = URLImportRequest(
            url=HttpUrl("https://example.com"),
            space_id=999,
            title=None,
            tags=None,
            save_snapshot=True,
            extract_links=False,
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await import_url(
                    import_data=import_request,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "空间不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_import_url_no_permission(self):
        """Test importing URL without permission"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        import_request = URLImportRequest(
            url=HttpUrl("https://example.com"),
            space_id=1,
            title=None,
            tags=None,
            save_snapshot=True,
            extract_links=False,
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_space.get_user_access = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await import_url(
                    import_data=import_request,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "无权在此空间导入文档" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_import_url_no_document_created(self):
        """Test URL import but document creation failed"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        import_request = URLImportRequest(
            url=HttpUrl("https://example.com"),
            space_id=1,
            title=None,
            tags=None,
            save_snapshot=True,
            extract_links=False,
        )

        import_result = {
            "status": "success",
            "document_id": 1,
        }

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.get = AsyncMock(
                return_value=None
            )  # Document not found

            with patch(
                "app.api.v1.endpoints.documents.document_service"
            ) as mock_service:
                mock_service.import_from_url = AsyncMock(return_value=import_result)

                with pytest.raises(HTTPException) as exc_info:
                    await import_url(
                        import_data=import_request,
                        db=mock_db,
                        current_user=mock_user,
                    )

                assert (
                    exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                assert "文档创建失败" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_batch_import_urls_space_not_found(self):
        """Test batch importing URLs to non-existent space"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        batch_request = BatchURLImportRequest(
            urls=[HttpUrl("https://example.com")],
            space_id=999,
            tags=None,
            save_snapshot=True,
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await batch_import_urls(
                    import_data=batch_request,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "空间不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_batch_import_urls_no_permission(self):
        """Test batch importing URLs without permission"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        batch_request = BatchURLImportRequest(
            urls=[HttpUrl("https://example.com")],
            space_id=1,
            tags=None,
            save_snapshot=True,
        )

        with patch("app.api.v1.endpoints.documents.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_space.get_user_access = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await batch_import_urls(
                    import_data=batch_request,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "无权在此空间导入文档" in str(exc_info.value.detail)
