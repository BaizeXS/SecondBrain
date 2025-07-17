"""Unit tests for document service."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Document, Space, User
from app.services.document_service import DocumentService


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Mock user."""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user


@pytest.fixture
def mock_document():
    """Mock document."""
    doc = Mock(spec=Document)
    doc.id = 1
    doc.space_id = 1
    doc.user_id = 1
    doc.filename = "test.pdf"
    doc.content_type = "application/pdf"
    doc.file_size = 1024
    doc.file_hash = "testhash123"
    doc.content = "Test content"
    doc.meta_data = {"title": "Test Document"}
    doc.created_at = datetime.now()
    return doc


@pytest.fixture
def mock_space():
    """Mock space."""
    space = Mock(spec=Space)
    space.id = 1
    space.user_id = 1
    space.is_public = False
    return space


@pytest.fixture
def document_service():
    """Create document service instance."""
    service = DocumentService()
    # Mock the content service
    service.content_service = Mock()
    return service


class TestDocumentService:
    """Test document service."""

    @pytest.mark.asyncio
    async def test_create_document(self, document_service, mock_db, mock_user):
        """Test creating a document."""
        # Mock dependencies
        with patch("app.crud.crud_document.get_by_hash") as mock_get_by_hash:
            with patch("app.crud.crud_document.create") as mock_create:
                with patch("app.crud.crud_space.update_stats") as mock_update_stats:
                    # Setup mocks
                    mock_get_by_hash.return_value = None
                    mock_create.return_value = Mock(
                        id=1,
                        filename="test.txt",
                        file_size=100
                    )

                    # Call method
                    result = await document_service.create_document(
                        db=mock_db,
                        space_id=1,
                        filename="test.txt",
                        content="Test content",
                        content_type="text/plain",
                        file_size=100,
                        user=mock_user
                    )

                    # Assertions
                    assert result.id == 1
                    assert result.filename == "test.txt"
                    mock_get_by_hash.assert_called_once()
                    mock_create.assert_called_once()
                    mock_update_stats.assert_called_once_with(
                        mock_db, space_id=1, document_delta=1, size_delta=100
                    )

    @pytest.mark.asyncio
    async def test_create_document_already_exists(self, document_service, mock_db, mock_user, mock_document):
        """Test creating a document that already exists."""
        with patch("app.crud.crud_document.get_by_hash") as mock_get_by_hash:
            # Setup mock to return existing document
            mock_get_by_hash.return_value = mock_document

            # Call method
            result = await document_service.create_document(
                db=mock_db,
                space_id=1,
                filename="test.txt",
                content="Test content",
                content_type="text/plain",
                file_size=100,
                user=mock_user
            )

            # Should return existing document
            assert result == mock_document
            mock_get_by_hash.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_space_documents(self, document_service, mock_db):
        """Test getting documents in a space."""
        with patch("app.crud.crud_document.get_by_space") as mock_get_by_space:
            # Setup mock
            mock_docs = [Mock(id=1), Mock(id=2)]
            mock_get_by_space.return_value = mock_docs

            # Call method
            result = await document_service.get_space_documents(
                mock_db, space_id=1, skip=0, limit=20
            )

            # Assertions
            assert result == mock_docs
            mock_get_by_space.assert_called_once_with(
                mock_db, space_id=1, skip=0, limit=20
            )

    @pytest.mark.asyncio
    async def test_get_document_by_id_owner(self, document_service, mock_db, mock_user, mock_document, mock_space):
        """Test getting document by ID as owner."""
        with patch("app.crud.crud_document.get") as mock_get:
            with patch("app.crud.crud_space.get") as mock_get_space:
                # Setup mocks
                mock_get.return_value = mock_document
                mock_get_space.return_value = mock_space

                # Call method
                result = await document_service.get_document_by_id(
                    mock_db, document_id=1, user=mock_user
                )

                # Assertions
                assert result == mock_document
                mock_get.assert_called_once_with(mock_db, id=1)
                mock_get_space.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_by_id_public_space(self, document_service, mock_db, mock_user, mock_document):
        """Test getting document in public space."""
        with patch("app.crud.crud_document.get") as mock_get:
            with patch("app.crud.crud_space.get") as mock_get_space:
                # Setup mocks
                mock_get.return_value = mock_document
                mock_space = Mock(user_id=999, is_public=True)  # Different user but public
                mock_get_space.return_value = mock_space

                # Call method
                result = await document_service.get_document_by_id(
                    mock_db, document_id=1, user=mock_user
                )

                # Should return document because space is public
                assert result == mock_document

    @pytest.mark.asyncio
    async def test_get_document_by_id_with_access(self, document_service, mock_db, mock_user, mock_document):
        """Test getting document with collaboration access."""
        with patch("app.crud.crud_document.get") as mock_get:
            with patch("app.crud.crud_space.get") as mock_get_space:
                with patch("app.crud.crud_space.get_user_access") as mock_get_access:
                    # Setup mocks
                    mock_get.return_value = mock_document
                    mock_space = Mock(user_id=999, is_public=False)  # Different user, not public
                    mock_get_space.return_value = mock_space
                    mock_get_access.return_value = Mock()  # Has access

                    # Call method
                    result = await document_service.get_document_by_id(
                        mock_db, document_id=1, user=mock_user
                    )

                    # Should return document because user has access
                    assert result == mock_document
                    mock_get_access.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_by_id_no_access(self, document_service, mock_db, mock_user, mock_document):
        """Test getting document without access."""
        with patch("app.crud.crud_document.get") as mock_get:
            with patch("app.crud.crud_space.get") as mock_get_space:
                with patch("app.crud.crud_space.get_user_access") as mock_get_access:
                    # Setup mocks
                    mock_get.return_value = mock_document
                    mock_space = Mock(user_id=999, is_public=False)
                    mock_get_space.return_value = mock_space
                    mock_get_access.return_value = None  # No access

                    # Call method
                    result = await document_service.get_document_by_id(
                        mock_db, document_id=1, user=mock_user
                    )

                    # Should return None because no access
                    assert result is None

    @pytest.mark.asyncio
    async def test_get_document_by_id_not_found(self, document_service, mock_db, mock_user):
        """Test getting non-existent document."""
        with patch("app.crud.crud_document.get") as mock_get:
            # Setup mock
            mock_get.return_value = None

            # Call method
            result = await document_service.get_document_by_id(
                mock_db, document_id=999, user=mock_user
            )

            # Should return None
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_document(self, document_service, mock_db, mock_document):
        """Test deleting a document."""
        with patch("app.crud.crud_space.update_stats") as mock_update_stats:
            with patch("app.crud.crud_document.remove") as mock_remove:
                # Call method
                result = await document_service.delete_document(mock_db, mock_document)

                # Assertions
                assert result is True
                mock_update_stats.assert_called_once_with(
                    mock_db,
                    space_id=mock_document.space_id,
                    document_delta=-1,
                    size_delta=-mock_document.file_size
                )
                mock_remove.assert_called_once_with(mock_db, id=mock_document.id)

    @pytest.mark.asyncio
    async def test_search_documents(self, document_service, mock_db):
        """Test searching documents."""
        with patch("app.crud.crud_document.search") as mock_search:
            # Setup mock
            mock_docs = [Mock(id=1), Mock(id=2)]
            mock_search.return_value = mock_docs

            # Call method
            result = await document_service.search_documents(
                mock_db, space_id=1, query="test", skip=0, limit=20
            )

            # Assertions
            assert result == mock_docs
            mock_search.assert_called_once_with(
                mock_db, space_id=1, query="test", skip=0, limit=20
            )

    @pytest.mark.asyncio
    async def test_update_processing_status(self, document_service, mock_db):
        """Test updating processing status."""
        with patch("app.crud.crud_document.update_processing_status") as mock_update:
            # Setup mock
            mock_doc = Mock(id=1, processing_status="completed")
            mock_update.return_value = mock_doc

            # Call method
            result = await document_service.update_processing_status(
                mock_db,
                document_id=1,
                processing_status="completed",
                extraction_status="completed"
            )

            # Assertions
            assert result == mock_doc
            mock_update.assert_called_once_with(
                mock_db,
                document_id=1,
                processing_status="completed",
                extraction_status="completed",
                embedding_status=None
            )

    @pytest.mark.asyncio
    async def test_import_from_url_success(self, document_service, mock_db, mock_user):
        """Test importing from URL successfully."""
        with patch("app.services.document_service.web_scraper_service.fetch_webpage") as mock_fetch:
            with patch("app.crud.crud_document.create") as mock_create:
                with patch("app.crud.crud_space.update_stats") as mock_update_stats:
                    # Setup mocks
                    mock_fetch.return_value = {
                        "status": "success",
                        "content": "Web content",
                        "metadata": {"title": "Web Page", "description": "Test page"},
                        "snapshot_html": "<html>Test</html>"
                    }
                    mock_create.return_value = Mock(
                        id=1,
                        title="Web Page",
                        file_size=11  # len("Web content")
                    )

                    # Call method
                    result = await document_service.import_from_url(
                        mock_db,
                        url="https://example.com",
                        space_id=1,
                        user=mock_user,
                        tags=["web", "test"]
                    )

                    # Assertions
                    assert result["status"] == "success"
                    assert result["document_id"] == 1
                    assert result["url"] == "https://example.com"
                    assert result["title"] == "Web Page"
                    mock_fetch.assert_called_once_with("https://example.com")
                    mock_create.assert_called_once()
                    mock_update_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_from_url_fetch_failed(self, document_service, mock_db, mock_user):
        """Test importing from URL when fetch fails."""
        with patch("app.services.document_service.web_scraper_service.fetch_webpage") as mock_fetch:
            # Setup mock
            mock_fetch.return_value = {
                "status": "error",
                "error": "Connection timeout"
            }

            # Call method
            result = await document_service.import_from_url(
                mock_db,
                url="https://example.com",
                space_id=1,
                user=mock_user
            )

            # Assertions
            assert result["status"] == "error"
            assert result["error"] == "Connection timeout"
            assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_import_from_url_exception(self, document_service, mock_db, mock_user):
        """Test importing from URL with exception."""
        with patch("app.services.document_service.web_scraper_service.fetch_webpage") as mock_fetch:
            # Setup mock to raise exception
            mock_fetch.side_effect = Exception("Network error")

            # Call method
            result = await document_service.import_from_url(
                mock_db,
                url="https://example.com",
                space_id=1,
                user=mock_user
            )

            # Assertions
            assert result["status"] == "error"
            assert "Network error" in result["error"]

    @pytest.mark.asyncio
    async def test_batch_import_urls(self, document_service, mock_db, mock_user):
        """Test batch importing URLs."""
        # Mock import_from_url
        async def mock_import(db, url, space_id, user, tags=None, save_snapshot=True):
            return {"status": "success", "url": url, "document_id": 1}

        document_service.import_from_url = mock_import

        # Call method
        urls = ["https://example1.com", "https://example2.com"]
        results = await document_service.batch_import_urls(
            mock_db, urls, space_id=1, user=mock_user
        )

        # Assertions
        assert len(results) == 2
        assert all(r["status"] == "success" for r in results)

    @pytest.mark.asyncio
    async def test_get_web_snapshot(self, document_service, mock_db, mock_user, mock_document):
        """Test getting web snapshot."""
        # Setup mock document with web metadata
        mock_document.meta_data = {
            "source_url": "https://example.com",
            "snapshot_html": "<html>Test</html>"
        }
        mock_document.title = "Web Page"
        mock_document.created_at = datetime.now()

        # Mock get_document_by_id
        document_service.get_document_by_id = AsyncMock(return_value=mock_document)

        with patch("app.services.document_service.web_scraper_service.convert_to_markdown") as mock_convert:
            # Setup mock
            mock_convert.return_value = "# Test"

            # Call method
            result = await document_service.get_web_snapshot(
                mock_db, document_id=1, user=mock_user
            )

            # Assertions
            assert result is not None
            assert result["document_id"] == 1
            assert result["url"] == "https://example.com"
            assert result["snapshot_html"] == "<html>Test</html>"
            assert result["snapshot_markdown"] == "# Test"
            mock_convert.assert_called_once_with("<html>Test</html>")

    @pytest.mark.asyncio
    async def test_get_web_snapshot_not_web_document(self, document_service, mock_db, mock_user, mock_document):
        """Test getting snapshot for non-web document."""
        # Setup mock document without web metadata
        mock_document.meta_data = {"title": "Regular Doc"}

        # Mock get_document_by_id
        document_service.get_document_by_id = AsyncMock(return_value=mock_document)

        # Call method
        result = await document_service.get_web_snapshot(
            mock_db, document_id=1, user=mock_user
        )

        # Should return None
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_url_success(self, document_service):
        """Test analyzing URL successfully."""
        with patch("app.services.document_service.web_scraper_service.fetch_webpage") as mock_fetch:
            with patch("app.services.document_service.web_scraper_service.extract_links") as mock_extract:
                # Setup mocks
                mock_fetch.return_value = {
                    "status": "success",
                    "content": "Python programming tutorial content",
                    "metadata": {
                        "title": "Python Tutorial",
                        "description": "Learn Python programming"
                    },
                    "snapshot_html": "<html>Test</html>"
                }
                mock_extract.return_value = ["link1", "link2", "link3"]

                # Call method
                result = await document_service.analyze_url("https://example.com")

                # Assertions
                assert result["can_import"] is True
                assert result["title"] == "Python Tutorial"
                assert result["word_count"] == 4  # "Python programming tutorial content"
                assert result["links_count"] == 3
                assert "python" in result["suggested_tags"]

    @pytest.mark.asyncio
    async def test_analyze_url_failure(self, document_service):
        """Test analyzing URL with failure."""
        with patch("app.services.document_service.web_scraper_service.fetch_webpage") as mock_fetch:
            # Setup mock
            mock_fetch.return_value = {
                "status": "error",
                "error": "404 Not Found"
            }

            # Call method
            result = await document_service.analyze_url("https://example.com")

            # Assertions
            assert result["can_import"] is False
            assert "404 Not Found" in result["error"]

    @pytest.mark.asyncio
    async def test_create_document_from_file(self, document_service, mock_db, mock_user):
        """Test creating document from file."""
        with patch("app.crud.crud_document.get_by_hash") as mock_get_by_hash:
            with patch("app.crud.crud_document.create") as mock_create:
                with patch("app.crud.crud_space.update_stats") as mock_update_stats:
                    # Setup mocks
                    mock_get_by_hash.return_value = None
                    mock_create.return_value = Mock(id=1, filename="test.pdf")

                    # Mock content service
                    document_service.content_service.extract_content_enhanced = AsyncMock(
                        return_value={
                            "text": "PDF content",
                            "metadata": {"title": "Test PDF"},
                            "extraction_method": "pdfplumber",
                            "format": "text",
                            "has_tables": False,
                            "has_images": False,
                            "has_formulas": False
                        }
                    )

                    # Create mock path
                    mock_path = Mock(spec=Path)
                    mock_path.suffix = ".pdf"
                    mock_path.stat.return_value = Mock(st_size=1024)
                    mock_path.name = "test.pdf"

                    # Call method
                    result = await document_service.create_document_from_file(
                        mock_db,
                        space_id=1,
                        file_path=mock_path,
                        user=mock_user,
                        title="Custom Title"
                    )

                    # Assertions
                    assert result.id == 1
                    assert result.filename == "test.pdf"
                    mock_create.assert_called_once()
                    mock_update_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_from_file_already_exists(self, document_service, mock_db, mock_user, mock_document):
        """Test creating document from file that already exists."""
        with patch("app.crud.crud_document.get_by_hash") as mock_get_by_hash:
            # Setup mocks
            mock_get_by_hash.return_value = mock_document

            # Mock content service
            document_service.content_service.extract_content_enhanced = AsyncMock(
                return_value={
                    "text": "PDF content",
                    "metadata": {},
                    "extraction_method": "pdfplumber",
                    "format": "text",
                    "has_tables": False,
                    "has_images": False,
                    "has_formulas": False
                }
            )

            # Create mock path
            mock_path = Mock(spec=Path)
            mock_path.suffix = ".pdf"
            mock_path.stat.return_value = Mock(st_size=1024)
            mock_path.name = "test.pdf"

            # Call method
            result = await document_service.create_document_from_file(
                mock_db,
                space_id=1,
                file_path=mock_path,
                user=mock_user
            )

            # Should return existing document
            assert result == mock_document

    @pytest.mark.asyncio
    async def test_extract_document_content(self, document_service):
        """Test extracting document content."""
        # Mock content service
        document_service.content_service.extract_content = AsyncMock(
            return_value="Extracted content"
        )

        # Create mock path
        mock_path = Mock(spec=Path)
        mock_path.suffix = ".txt"

        # Call method
        result = await document_service.extract_document_content(mock_path)

        # Assertions
        assert result == "Extracted content"
        document_service.content_service.extract_content.assert_called_once_with(
            mock_path, ".txt"
        )

    @pytest.mark.asyncio
    async def test_get_document_metadata(self, document_service):
        """Test getting document metadata."""
        # Mock content service
        metadata = {"title": "Test", "author": "Author"}
        document_service.content_service.get_document_metadata = AsyncMock(
            return_value=metadata
        )

        # Create mock path
        mock_path = Mock(spec=Path)

        # Call method
        result = await document_service.get_document_metadata(mock_path)

        # Assertions
        assert result == metadata

    @pytest.mark.asyncio
    async def test_split_document_content(self, document_service):
        """Test splitting document content."""
        # Mock content service
        chunks = ["chunk1", "chunk2", "chunk3"]
        document_service.content_service.split_document = AsyncMock(
            return_value=chunks
        )

        # Call method
        result = await document_service.split_document_content(
            "Long content", chunk_size=100, overlap=20
        )

        # Assertions
        assert result == chunks
        document_service.content_service.split_document.assert_called_once_with(
            "Long content", 100, 20
        )

    @pytest.mark.asyncio
    async def test_extract_keywords(self, document_service):
        """Test extracting keywords."""
        # Mock content service
        keywords = ["python", "programming", "tutorial"]
        document_service.content_service.extract_keywords = AsyncMock(
            return_value=keywords
        )

        # Call method
        result = await document_service.extract_keywords(
            "Python programming tutorial", max_keywords=5
        )

        # Assertions
        assert result == keywords

    @pytest.mark.asyncio
    async def test_summarize_content(self, document_service):
        """Test summarizing content."""
        # Mock content service
        summary = "This is a summary"
        document_service.content_service.summarize_content = AsyncMock(
            return_value=summary
        )

        # Call method
        result = await document_service.summarize_content(
            "Long content...", max_length=100
        )

        # Assertions
        assert result == summary

    def test_get_content_type(self, document_service):
        """Test getting content type from extension."""
        assert document_service._get_content_type(".pdf") == "application/pdf"
        assert document_service._get_content_type(".DOCX") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert document_service._get_content_type(".txt") == "text/plain"
        assert document_service._get_content_type(".md") == "text/markdown"
        assert document_service._get_content_type(".unknown") == "application/octet-stream"
