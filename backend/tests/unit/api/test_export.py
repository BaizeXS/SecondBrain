"""Unit tests for export endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.export import (
    export_conversations,
    export_documents,
    export_notes,
    export_space,
)
from app.models.models import Conversation, Document, Note, Space, User
from app.schemas.export import (
    ConversationExportRequest,
    DocumentExportRequest,
    NoteExportRequest,
    SpaceExportRequest,
)


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def mock_note():
    """Create mock note."""
    note = MagicMock(spec=Note)
    note.id = 1
    note.user_id = 1
    note.title = "Test Note"
    note.content = "Test content"
    note.created_at = datetime.now(UTC)
    note.updated_at = datetime.now(UTC)
    note.version = 1
    note.tags = ["test", "export"]
    note.space = None  # 可以为None或者mock space
    return note


@pytest.fixture
def mock_document():
    """Create mock document."""
    document = MagicMock(spec=Document)
    document.id = 1
    document.user_id = 1
    document.title = "Test Document"
    document.filename = "test.pdf"
    document.content = "Test document content"
    document.content_type = "application/pdf"
    document.created_at = datetime.now(UTC)
    document.file_size = 1024
    document.summary = "Test summary"
    document.tags = ["test", "export"]
    document.space = None  # 可以为None或者mock space
    return document


@pytest.fixture
def mock_space():
    """Create mock space."""
    space = MagicMock(spec=Space)
    space.id = 1
    space.user_id = 1
    space.name = "Test Space"
    space.description = "Test space description"
    space.created_at = datetime.now(UTC)
    return space


@pytest.fixture
def mock_conversation():
    """Create mock conversation."""
    conversation = MagicMock(spec=Conversation)
    conversation.id = 1
    conversation.user_id = 1
    conversation.title = "Test Conversation"
    conversation.created_at = datetime.now(UTC)
    return conversation


class TestExportNotes:
    """Test export notes endpoint."""

    @pytest.mark.asyncio
    async def test_export_single_note_to_pdf(
        self,
        mock_user: User,
        mock_note: Note,
        async_test_db: AsyncSession,
    ):
        """Test successful single note export to PDF."""
        request = NoteExportRequest(
            note_ids=[1],
            format="pdf",
            include_metadata=True,
            include_versions=False,
            include_linked_notes=False,
            merge_into_one=False,
        )

        with patch("app.api.v1.endpoints.export.crud_note") as mock_crud:
            with patch("app.api.v1.endpoints.export.export_service") as mock_service:
                mock_crud.get = AsyncMock(return_value=mock_note)
                mock_service.export_note_to_pdf = AsyncMock(return_value=b"PDF content")

                result = await export_notes(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert isinstance(result, StreamingResponse)
                assert result.media_type == "application/pdf"
                assert "Content-Disposition" in result.headers
                assert "Test_Note.pdf" in result.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_export_note_with_versions(
        self,
        mock_user: User,
        mock_note: Note,
        async_test_db: AsyncSession,
    ):
        """Test export note with version history."""
        request = NoteExportRequest(
            note_ids=[1],
            format="pdf",
            include_metadata=True,
            include_versions=True,
            include_linked_notes=False,
            merge_into_one=False,
        )

        mock_version = MagicMock()
        mock_version.version_number = 2
        mock_version.created_at = datetime.now(UTC)
        mock_version.change_summary = "Updated content"

        with patch("app.api.v1.endpoints.export.crud_note") as mock_crud:
            with patch("app.api.v1.endpoints.export.note_service") as mock_note_svc:
                with patch("app.api.v1.endpoints.export.export_service") as mock_export:
                    mock_crud.get = AsyncMock(return_value=mock_note)
                    mock_note_svc.get_version_history = AsyncMock(
                        return_value=[mock_version]
                    )
                    mock_export.export_note_to_pdf = AsyncMock(
                        return_value=b"PDF with versions"
                    )

                    result = await export_notes(
                        request=request,
                        db=async_test_db,
                        current_user=mock_user,
                    )

                    mock_note_svc.get_version_history.assert_called_once()
                    assert isinstance(result, StreamingResponse)

    @pytest.mark.asyncio
    async def test_export_note_to_docx(
        self,
        mock_user: User,
        mock_note: Note,
        async_test_db: AsyncSession,
    ):
        """Test export note to DOCX format."""
        request = NoteExportRequest(
            note_ids=[1],
            format="docx",
            include_metadata=True,
            include_versions=False,
            include_linked_notes=False,
            merge_into_one=False,
        )

        with patch("app.api.v1.endpoints.export.crud_note") as mock_crud:
            with patch("app.api.v1.endpoints.export.export_service") as mock_service:
                mock_crud.get = AsyncMock(return_value=mock_note)
                mock_service.export_note_to_docx = AsyncMock(
                    return_value=b"DOCX content"
                )

                result = await export_notes(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert isinstance(result, StreamingResponse)
                assert (
                    result.media_type
                    == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                assert "Test_Note.docx" in result.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_export_note_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test export non-existent note."""
        request = NoteExportRequest(
            note_ids=[999],
            format="pdf",
            include_metadata=True,
            include_versions=False,
            include_linked_notes=False,
            merge_into_one=False,
        )

        with patch("app.api.v1.endpoints.export.crud_note") as mock_crud:
            mock_crud.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await export_notes(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "笔记 999 不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_note_no_permission(
        self,
        mock_user: User,
        mock_note: Note,
        async_test_db: AsyncSession,
    ):
        """Test export note without permission."""
        mock_note.user_id = 999  # Different user
        request = NoteExportRequest(
            note_ids=[1],
            format="pdf",
            include_metadata=True,
            include_versions=False,
            include_linked_notes=False,
            merge_into_one=False,
        )

        with patch("app.api.v1.endpoints.export.crud_note") as mock_crud:
            mock_crud.get = AsyncMock(return_value=mock_note)

            with pytest.raises(HTTPException) as exc_info:
                await export_notes(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权访问笔记 1" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_merge_notes_success(
        self,
        mock_user: User,
        mock_note: Note,
        async_test_db: AsyncSession,
    ):
        """Test merge multiple notes successfully."""
        request = NoteExportRequest(
            note_ids=[1, 2],
            format="pdf",
            include_metadata=True,
            include_versions=False,
            include_linked_notes=False,
            merge_into_one=True,
        )

        # Create second note
        mock_note2 = MagicMock(spec=Note)
        mock_note2.id = 2
        mock_note2.user_id = 1
        mock_note2.title = "Test Note 2"
        mock_note2.content = "Test content 2"
        mock_note2.created_at = datetime.now(UTC)
        mock_note2.updated_at = datetime.now(UTC)
        mock_note2.version = 1
        mock_note2.tags = ["test", "export"]
        mock_note2.space = None

        with (
            patch("app.api.v1.endpoints.export.crud_note") as mock_crud,
            patch("app.api.v1.endpoints.export.export_service") as mock_service,
        ):
            # Mock crud to return different notes for different IDs
            def mock_get(db, id):
                if id == 1:
                    return mock_note
                elif id == 2:
                    return mock_note2
                return None

            mock_crud.get = AsyncMock(side_effect=mock_get)
            mock_service.export_notes_to_pdf = AsyncMock(
                return_value=b"Merged PDF content"
            )

            result = await export_notes(
                request=request,
                db=async_test_db,
                current_user=mock_user,
            )

            assert isinstance(result, StreamingResponse)
            assert result.media_type == "application/pdf"
            assert "notes_collection.pdf" in result.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_export_unsupported_format(
        self,
        mock_user: User,
        mock_note: Note,
        async_test_db: AsyncSession,
    ):
        """Test export with unsupported format."""
        request = NoteExportRequest(
            note_ids=[1],
            format="unsupported",
            include_metadata=True,
            include_versions=False,
            include_linked_notes=False,
            merge_into_one=False,
        )

        with patch("app.api.v1.endpoints.export.crud_note") as mock_crud:
            mock_crud.get = AsyncMock(return_value=mock_note)

            with pytest.raises(HTTPException) as exc_info:
                await export_notes(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert "不支持的导出格式: unsupported" in str(exc_info.value.detail)


class TestExportDocuments:
    """Test export documents endpoint."""

    @pytest.mark.asyncio
    async def test_export_single_document_to_pdf(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test successful single document export to PDF."""
        request = DocumentExportRequest(
            document_ids=[1],
            format="pdf",
            include_annotations=False,
            include_citations=False,
            merge_into_one=False,
        )

        with patch("app.api.v1.endpoints.export.crud_document") as mock_crud:
            with patch("app.api.v1.endpoints.export.export_service") as mock_service:
                mock_crud.get = AsyncMock(return_value=mock_document)
                mock_service.export_document_to_pdf = AsyncMock(
                    return_value=b"PDF content"
                )

                result = await export_documents(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert isinstance(result, StreamingResponse)
                assert result.media_type == "application/pdf"
                assert "Test Document.pdf" in result.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_export_document_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test export non-existent document."""
        request = DocumentExportRequest(
            document_ids=[999],
            format="pdf",
            include_annotations=True,
            include_citations=False,
            merge_into_one=False,
        )

        with patch("app.api.v1.endpoints.export.crud_document") as mock_crud:
            mock_crud.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await export_documents(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "文档 999 不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_document_no_permission(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test export document without permission."""
        mock_document.user_id = 999
        request = DocumentExportRequest(
            document_ids=[1],
            format="pdf",
            include_annotations=True,
            include_citations=False,
            merge_into_one=False,
        )

        with patch("app.api.v1.endpoints.export.crud_document") as mock_crud:
            mock_crud.get = AsyncMock(return_value=mock_document)

            with pytest.raises(HTTPException) as exc_info:
                await export_documents(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权访问文档 1" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_merge_documents_success(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test merge multiple documents successfully."""
        request = DocumentExportRequest(
            document_ids=[1, 2],
            format="pdf",
            include_annotations=True,
            include_citations=False,
            merge_into_one=True,
        )

        # Create second document
        mock_document2 = MagicMock(spec=Document)
        mock_document2.id = 2
        mock_document2.user_id = 1
        mock_document2.title = "Test Document 2"
        mock_document2.filename = "test2.pdf"
        mock_document2.content = "Test document content 2"
        mock_document2.content_type = "application/pdf"
        mock_document2.created_at = datetime.now(UTC)
        mock_document2.file_size = 2048
        mock_document2.summary = "Test summary 2"
        mock_document2.tags = ["test", "export"]
        mock_document2.space = None

        with (
            patch("app.api.v1.endpoints.export.crud_document") as mock_crud,
            patch("app.api.v1.endpoints.export.export_service") as mock_service,
        ):
            # Mock crud to return different documents for different IDs
            def mock_get(db, id):
                if id == 1:
                    return mock_document
                elif id == 2:
                    return mock_document2
                return None

            mock_crud.get = AsyncMock(side_effect=mock_get)
            mock_service.export_documents_to_pdf = AsyncMock(
                return_value=b"Merged Documents PDF content"
            )

            result = await export_documents(
                request=request,
                db=async_test_db,
                current_user=mock_user,
            )

            assert isinstance(result, StreamingResponse)
            assert result.media_type == "application/pdf"
            assert "documents_collection.pdf" in result.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_export_document_unsupported_format(
        self,
        mock_user: User,
        mock_document: Document,
        async_test_db: AsyncSession,
    ):
        """Test export document with unsupported format."""
        request = DocumentExportRequest(
            document_ids=[1],
            format="html",  # Not supported for documents
            include_annotations=True,
            include_citations=False,
            merge_into_one=False,
        )

        with patch("app.api.v1.endpoints.export.crud_document") as mock_crud:
            mock_crud.get = AsyncMock(return_value=mock_document)

            with pytest.raises(HTTPException) as exc_info:
                await export_documents(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert "不支持的导出格式: html" in str(exc_info.value.detail)


class TestExportSpace:
    """Test export space endpoint."""

    @pytest.mark.asyncio
    async def test_export_space_to_pdf(
        self,
        mock_user: User,
        mock_space: Space,
        mock_document: Document,
        mock_note: Note,
        async_test_db: AsyncSession,
    ):
        """Test successful space export to PDF."""
        request = SpaceExportRequest(
            space_id=1,
            format="pdf",
            include_documents=True,
            include_notes=True,
            include_content=True,
            include_citations=False,
        )

        with patch("app.api.v1.endpoints.export.crud_space") as mock_crud_space:
            with patch("app.api.v1.endpoints.export.crud_document") as mock_crud_doc:
                with patch("app.api.v1.endpoints.export.crud_note") as mock_crud_note:
                    with patch(
                        "app.api.v1.endpoints.export.export_service"
                    ) as mock_service:
                        mock_crud_space.get = AsyncMock(return_value=mock_space)
                        mock_crud_doc.get_by_space = AsyncMock(
                            return_value=[mock_document]
                        )
                        mock_crud_note.get_by_space = AsyncMock(
                            return_value=[mock_note]
                        )
                        mock_service.export_space_to_pdf = AsyncMock(
                            return_value=b"Space PDF"
                        )

                        result = await export_space(
                            request=request,
                            db=async_test_db,
                            current_user=mock_user,
                        )

                        assert isinstance(result, StreamingResponse)
                        assert result.media_type == "application/pdf"
                        assert (
                            "Test_Space_export.pdf"
                            in result.headers["Content-Disposition"]
                        )

    @pytest.mark.asyncio
    async def test_export_space_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test export non-existent space."""
        request = SpaceExportRequest(
            space_id=999,
            format="pdf",
            include_documents=True,
            include_notes=True,
            include_content=False,
            include_citations=False,
        )

        with patch("app.api.v1.endpoints.export.crud_space") as mock_crud:
            mock_crud.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await export_space(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "空间不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_space_no_permission(
        self,
        mock_user: User,
        mock_space: Space,
        async_test_db: AsyncSession,
    ):
        """Test export space without permission."""
        mock_space.user_id = 999
        request = SpaceExportRequest(
            space_id=1,
            format="pdf",
            include_documents=True,
            include_notes=True,
            include_content=False,
            include_citations=False,
        )

        with patch("app.api.v1.endpoints.export.crud_space") as mock_crud:
            mock_crud.get = AsyncMock(return_value=mock_space)

            with pytest.raises(HTTPException) as exc_info:
                await export_space(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权访问此空间" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_space_without_content(
        self,
        mock_user: User,
        mock_space: Space,
        mock_document: Document,
        mock_note: Note,
        async_test_db: AsyncSession,
    ):
        """Test export space without including content."""
        request = SpaceExportRequest(
            space_id=1,
            format="pdf",
            include_documents=True,
            include_notes=True,
            include_content=False,  # Only export list
            include_citations=False,
        )

        with patch("app.api.v1.endpoints.export.crud_space") as mock_crud_space:
            with patch("app.api.v1.endpoints.export.crud_document") as mock_crud_doc:
                with patch("app.api.v1.endpoints.export.crud_note") as mock_crud_note:
                    with patch(
                        "app.api.v1.endpoints.export.export_service"
                    ) as mock_service:
                        mock_crud_space.get = AsyncMock(return_value=mock_space)
                        mock_crud_doc.get_by_space = AsyncMock(
                            return_value=[mock_document]
                        )
                        mock_crud_note.get_by_space = AsyncMock(
                            return_value=[mock_note]
                        )
                        mock_service.export_space_to_pdf = AsyncMock(
                            return_value=b"Space list PDF"
                        )

                        result = await export_space(
                            request=request,
                            db=async_test_db,
                            current_user=mock_user,
                        )

                        # Verify the service was called with include_content=False
                        assert isinstance(result, StreamingResponse)
                        call_args = mock_service.export_space_to_pdf.call_args[1]
                        assert call_args["include_content"] is False

    @pytest.mark.asyncio
    async def test_export_space_unsupported_format(
        self,
        mock_user: User,
        mock_space: Space,
        async_test_db: AsyncSession,
    ):
        """Test export space with unsupported format."""
        request = SpaceExportRequest(
            space_id=1,
            format="json",  # Not supported for spaces
            include_documents=True,
            include_notes=True,
            include_content=False,
            include_citations=False,
        )

        with patch("app.api.v1.endpoints.export.crud_space") as mock_crud:
            mock_crud.get = AsyncMock(return_value=mock_space)

            with pytest.raises(HTTPException) as exc_info:
                await export_space(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert "不支持的导出格式: json" in str(exc_info.value.detail)


class TestExportConversations:
    """Test export conversations endpoint."""

    @pytest.mark.asyncio
    async def test_export_conversations_unsupported_format(
        self,
        mock_user: User,
        mock_conversation: Conversation,
        async_test_db: AsyncSession,
    ):
        """Test export conversations with unsupported format (PDF not supported for conversations)."""
        request = ConversationExportRequest(
            conversation_ids=[1],
            format="pdf",
            include_metadata=True,
            include_branches=False,
            merge_into_one=False,
            date_from=None,
            date_to=None,
        )

        with patch("app.api.v1.endpoints.export.crud_conversation") as mock_crud:
            mock_crud.get = AsyncMock(return_value=mock_conversation)

            with pytest.raises(HTTPException) as exc_info:
                await export_conversations(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 400
            assert "不支持的导出格式: pdf" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_conversation_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test export non-existent conversation."""
        request = ConversationExportRequest(
            conversation_ids=[999],
            format="pdf",
            include_metadata=True,
            include_branches=False,
            merge_into_one=False,
            date_from=None,
            date_to=None,
        )

        with patch("app.api.v1.endpoints.export.crud_conversation") as mock_crud:
            mock_crud.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await export_conversations(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "对话 999 不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_conversation_no_permission(
        self,
        mock_user: User,
        mock_conversation: Conversation,
        async_test_db: AsyncSession,
    ):
        """Test export conversation without permission."""
        mock_conversation.user_id = 999
        request = ConversationExportRequest(
            conversation_ids=[1],
            format="pdf",
            include_metadata=True,
            include_branches=False,
            merge_into_one=False,
            date_from=None,
            date_to=None,
        )

        with patch("app.api.v1.endpoints.export.crud_conversation") as mock_crud:
            mock_crud.get = AsyncMock(return_value=mock_conversation)

            with pytest.raises(HTTPException) as exc_info:
                await export_conversations(
                    request=request,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权访问对话 1" in str(exc_info.value.detail)
