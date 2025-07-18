"""Unit tests for citations endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.citations import (
    create_citation,
    delete_citation,
    export_citations,
    format_citations,
    get_citation,
    get_citations,
    import_bibtex,
    search_citations,
    update_citation,
)
from app.models.models import Citation, Space, User
from app.schemas.citation import (
    BibTeXExportRequest,
    BibTeXImportRequest,
    BibTeXImportResponse,
    CitationCreate,
    CitationListResponse,
    CitationResponse,
    CitationSearchRequest,
    CitationStyleFormat,
    CitationUpdate,
    FormattedCitation,
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
def mock_space():
    """Create mock space."""
    space = MagicMock(spec=Space)
    space.id = 1
    space.user_id = 1
    space.name = "Test Space"
    space.is_public = False
    return space


@pytest.fixture
def mock_citation():
    """Create mock citation."""
    citation = MagicMock(spec=Citation)
    citation.id = 1
    citation.user_id = 1
    citation.space_id = 1
    citation.document_id = None
    citation.bibtex_key = "test2024"
    citation.title = "Test Citation"
    citation.authors = ["Test Author"]
    citation.year = 2024
    citation.citation_type = "article"
    citation.journal = None
    citation.volume = None
    citation.number = None
    citation.pages = None
    citation.publisher = None
    citation.doi = None
    citation.url = None
    citation.abstract = None
    citation.keywords = None
    citation.bibtex_raw = None
    citation.meta_data = None
    citation.created_at = datetime.now(UTC)
    citation.updated_at = datetime.now(UTC)
    return citation


class TestImportBibTeX:
    """Test import BibTeX endpoint."""

    @pytest.mark.asyncio
    async def test_import_bibtex_success(
        self,
        mock_user: User,
        mock_space: Space,
        async_test_db: AsyncSession,
    ):
        """Test successful BibTeX import."""
        import_data = BibTeXImportRequest(
            bibtex_content="@article{test2024,\n  title={Test},\n  author={Test},\n  year={2024}\n}",
            space_id=1,
            create_documents=False,
            tags=["imported"],
        )

        with patch("app.api.v1.endpoints.citations.crud.crud_space") as mock_crud_space:
            with patch(
                "app.api.v1.endpoints.citations.citation_service"
            ) as mock_service:
                mock_crud_space.get = AsyncMock(return_value=mock_space)
                mock_service.import_bibtex = AsyncMock(
                    return_value={
                        "imported_count": 1,
                        "failed_count": 0,
                        "citations": [],
                        "errors": [],
                    }
                )

                result = await import_bibtex(
                    import_data=import_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert isinstance(result, BibTeXImportResponse)
                assert result.imported_count == 1
                assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_import_bibtex_space_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test import to non-existent space."""
        import_data = BibTeXImportRequest(
            bibtex_content="@article{test2024}",
            space_id=999,
            create_documents=False,
            tags=None,
        )

        with patch("app.api.v1.endpoints.citations.crud.crud_space") as mock_crud_space:
            mock_crud_space.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await import_bibtex(
                    import_data=import_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "空间不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_import_bibtex_no_permission(
        self,
        mock_user: User,
        mock_space: Space,
        async_test_db: AsyncSession,
    ):
        """Test import without permission."""
        mock_space.user_id = 999  # Different user
        import_data = BibTeXImportRequest(
            bibtex_content="@article{test2024}",
            space_id=1,
            create_documents=False,
            tags=None,
        )

        with patch("app.api.v1.endpoints.citations.crud.crud_space") as mock_crud_space:
            mock_crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud_space.get_user_access = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await import_bibtex(
                    import_data=import_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权在此空间导入引用" in str(exc_info.value.detail)


class TestGetCitations:
    """Test get citations endpoint."""

    @pytest.mark.asyncio
    async def test_get_citations_by_document(
        self,
        mock_user: User,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test get citations by document."""
        mock_document = MagicMock()
        mock_document.id = 1

        with patch("app.services.DocumentService") as mock_doc_service_class:
            with patch(
                "app.api.v1.endpoints.citations.crud.crud_citation"
            ) as mock_crud_citation:
                mock_doc_service = MagicMock()
                mock_doc_service_class.return_value = mock_doc_service
                mock_doc_service.get_document_by_id = AsyncMock(
                    return_value=mock_document
                )
                mock_crud_citation.get_by_document = AsyncMock(
                    return_value=[mock_citation]
                )

                result = await get_citations(
                    space_id=None,
                    document_id=1,
                    skip=0,
                    limit=20,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert isinstance(result, CitationListResponse)
                assert result.total == 1
                assert len(result.citations) == 1
                assert result.page == 1

    @pytest.mark.asyncio
    async def test_get_citations_by_space(
        self,
        mock_user: User,
        mock_space: Space,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test get citations by space."""
        with patch("app.api.v1.endpoints.citations.crud.crud_space") as mock_crud_space:
            with patch(
                "app.api.v1.endpoints.citations.crud.crud_citation"
            ) as mock_crud_citation:
                mock_crud_space.get = AsyncMock(return_value=mock_space)
                mock_crud_citation.get_by_space = AsyncMock(
                    return_value=[mock_citation]
                )
                mock_crud_citation.count_by_space = AsyncMock(return_value=1)

                result = await get_citations(
                    space_id=1,
                    document_id=None,
                    skip=0,
                    limit=20,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert isinstance(result, CitationListResponse)
                assert result.total == 1
                assert len(result.citations) == 1

    @pytest.mark.asyncio
    async def test_get_citations_user_all(
        self,
        mock_user: User,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test get all user citations."""
        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            mock_crud_citation.get_user_citations = AsyncMock(
                return_value=[mock_citation, mock_citation]
            )

            # Mock the database execute call for counting
            mock_result = MagicMock()
            mock_result.scalar.return_value = 2
            async_test_db.execute = AsyncMock(return_value=mock_result)

            result = await get_citations(
                space_id=None,
                document_id=None,
                skip=0,
                limit=20,
                db=async_test_db,
                current_user=mock_user,
            )

            assert isinstance(result, CitationListResponse)
            assert result.total == 2
            assert len(result.citations) == 2

    @pytest.mark.asyncio
    async def test_get_citations_document_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test get citations with non-existent document."""
        with patch("app.services.DocumentService") as mock_doc_service_class:
            mock_doc_service = MagicMock()
            mock_doc_service_class.return_value = mock_doc_service
            mock_doc_service.get_document_by_id = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_citations(
                    space_id=None,
                    document_id=999,
                    skip=0,
                    limit=20,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "文档不存在或无权访问" in str(exc_info.value.detail)


class TestGetCitation:
    """Test get citation detail endpoint."""

    @pytest.mark.asyncio
    async def test_get_citation_success(
        self,
        mock_user: User,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test successful get citation."""
        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            mock_crud_citation.get = AsyncMock(return_value=mock_citation)

            result = await get_citation(
                citation_id=1,
                db=async_test_db,
                current_user=mock_user,
            )

            assert isinstance(result, CitationResponse)
            assert result.id == 1
            assert result.title == "Test Citation"

    @pytest.mark.asyncio
    async def test_get_citation_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test get non-existent citation."""
        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            mock_crud_citation.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_citation(
                    citation_id=999,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "引用不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_citation_no_permission(
        self,
        mock_user: User,
        mock_citation,
        mock_space: Space,
        async_test_db: AsyncSession,
    ):
        """Test get citation without permission."""
        mock_citation.user_id = 999
        mock_space.user_id = 999
        mock_space.is_public = False

        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            with patch(
                "app.api.v1.endpoints.citations.crud.crud_space"
            ) as mock_crud_space:
                mock_crud_citation.get = AsyncMock(return_value=mock_citation)
                mock_crud_space.get = AsyncMock(return_value=mock_space)
                mock_crud_space.get_user_access = AsyncMock(return_value=None)

                with pytest.raises(HTTPException) as exc_info:
                    await get_citation(
                        citation_id=1,
                        db=async_test_db,
                        current_user=mock_user,
                    )

                assert exc_info.value.status_code == 403
                assert "无权访问此引用" in str(exc_info.value.detail)


class TestCreateCitation:
    """Test create citation endpoint."""

    @pytest.mark.asyncio
    async def test_create_citation_success(
        self,
        mock_user: User,
        mock_space: Space,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test successful citation creation."""
        citation_data = CitationCreate(
            bibtex_key="new2024",
            title="New Citation",
            authors=["New Author"],
            year=2024,
            citation_type="article",
        )

        with patch("app.api.v1.endpoints.citations.crud.crud_space") as mock_crud_space:
            with patch(
                "app.api.v1.endpoints.citations.crud.crud_citation"
            ) as mock_crud_citation:
                mock_crud_space.get = AsyncMock(return_value=mock_space)
                mock_crud_citation.get_by_bibtex_key = AsyncMock(return_value=None)
                mock_crud_citation.create = AsyncMock(return_value=mock_citation)

                result = await create_citation(
                    citation_data=citation_data,
                    space_id=1,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert isinstance(result, CitationResponse)
                assert result.id == 1
                assert result.title == "Test Citation"

    @pytest.mark.asyncio
    async def test_create_citation_duplicate_key(
        self,
        mock_user: User,
        mock_space: Space,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test create citation with duplicate bibtex key."""
        citation_data = CitationCreate(
            bibtex_key="existing2024",
            title="New Citation",
            authors=["New Author"],
            year=2024,
            citation_type="article",
        )

        with patch("app.api.v1.endpoints.citations.crud.crud_space") as mock_crud_space:
            with patch(
                "app.api.v1.endpoints.citations.crud.crud_citation"
            ) as mock_crud_citation:
                mock_crud_space.get = AsyncMock(return_value=mock_space)
                mock_crud_citation.get_by_bibtex_key = AsyncMock(
                    return_value=mock_citation
                )

                with pytest.raises(HTTPException) as exc_info:
                    await create_citation(
                        citation_data=citation_data,
                        space_id=1,
                        db=async_test_db,
                        current_user=mock_user,
                    )

                assert exc_info.value.status_code == 400
                assert "引用键已存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_citation_no_permission(
        self,
        mock_user: User,
        mock_space: Space,
        async_test_db: AsyncSession,
    ):
        """Test create citation without permission."""
        mock_space.user_id = 999
        citation_data = CitationCreate(
            bibtex_key="new2024",
            title="New Citation",
            authors=["New Author"],
            year=2024,
            citation_type="article",
        )

        with patch("app.api.v1.endpoints.citations.crud.crud_space") as mock_crud_space:
            mock_crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud_space.get_user_access = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await create_citation(
                    citation_data=citation_data,
                    space_id=1,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权在此空间创建引用" in str(exc_info.value.detail)


class TestUpdateCitation:
    """Test update citation endpoint."""

    @pytest.mark.asyncio
    async def test_update_citation_success(
        self,
        mock_user: User,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test successful citation update."""
        update_data = CitationUpdate(
            title="Updated Title",
            year=2025,
            meta_data=None,
        )

        updated_citation = MagicMock(spec=Citation)
        updated_citation.id = 1
        updated_citation.user_id = 1
        updated_citation.space_id = 1
        updated_citation.document_id = None
        updated_citation.bibtex_key = "test2024"
        updated_citation.title = "Updated Title"
        updated_citation.authors = ["Test Author"]
        updated_citation.year = 2025
        updated_citation.citation_type = "article"
        updated_citation.journal = None
        updated_citation.volume = None
        updated_citation.number = None
        updated_citation.pages = None
        updated_citation.publisher = None
        updated_citation.doi = None
        updated_citation.url = None
        updated_citation.abstract = None
        updated_citation.keywords = None
        updated_citation.bibtex_raw = None
        updated_citation.meta_data = None
        updated_citation.created_at = datetime.now(UTC)
        updated_citation.updated_at = datetime.now(UTC)

        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            mock_crud_citation.get = AsyncMock(return_value=mock_citation)
            mock_crud_citation.update = AsyncMock(return_value=updated_citation)

            result = await update_citation(
                citation_id=1,
                citation_data=update_data,
                db=async_test_db,
                current_user=mock_user,
            )

            assert isinstance(result, CitationResponse)
            assert result.title == "Updated Title"
            assert result.year == 2025

    @pytest.mark.asyncio
    async def test_update_citation_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test update non-existent citation."""
        update_data = CitationUpdate(title="Updated", meta_data=None)

        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            mock_crud_citation.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await update_citation(
                    citation_id=999,
                    citation_data=update_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "引用不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_citation_no_permission(
        self,
        mock_user: User,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test update citation without permission."""
        mock_citation.user_id = 999
        update_data = CitationUpdate(title="Updated", meta_data=None)

        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            mock_crud_citation.get = AsyncMock(return_value=mock_citation)

            with pytest.raises(HTTPException) as exc_info:
                await update_citation(
                    citation_id=1,
                    citation_data=update_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权编辑此引用" in str(exc_info.value.detail)


class TestDeleteCitation:
    """Test delete citation endpoint."""

    @pytest.mark.asyncio
    async def test_delete_citation_success(
        self,
        mock_user: User,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test successful citation deletion."""
        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            mock_crud_citation.get = AsyncMock(return_value=mock_citation)
            mock_crud_citation.remove = AsyncMock(return_value=None)

            result = await delete_citation(
                citation_id=1,
                db=async_test_db,
                current_user=mock_user,
            )

            assert result is None
            mock_crud_citation.remove.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_citation_not_found(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test delete non-existent citation."""
        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            mock_crud_citation.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await delete_citation(
                    citation_id=999,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 404
            assert "引用不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_citation_no_permission(
        self,
        mock_user: User,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test delete citation without permission."""
        mock_citation.user_id = 999

        with patch(
            "app.api.v1.endpoints.citations.crud.crud_citation"
        ) as mock_crud_citation:
            mock_crud_citation.get = AsyncMock(return_value=mock_citation)

            with pytest.raises(HTTPException) as exc_info:
                await delete_citation(
                    citation_id=1,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权删除此引用" in str(exc_info.value.detail)


class TestSearchCitations:
    """Test search citations endpoint."""

    @pytest.mark.asyncio
    async def test_search_citations_success(
        self,
        mock_user: User,
        mock_citation,
        async_test_db: AsyncSession,
    ):
        """Test successful citation search."""
        search_data = CitationSearchRequest(
            query="test",
            space_id=1,
            citation_type="article",
            year_from=2020,
            year_to=2024,
            authors=["Test Author"],
        )

        with patch("app.api.v1.endpoints.citations.citation_service") as mock_service:
            mock_service.search_citations = AsyncMock(
                return_value=[mock_citation, mock_citation]
            )

            result = await search_citations(
                search_data=search_data,
                skip=0,
                limit=20,
                db=async_test_db,
                current_user=mock_user,
            )

            assert isinstance(result, CitationListResponse)
            assert result.total == 2
            assert len(result.citations) == 2
            mock_service.search_citations.assert_called_once_with(
                async_test_db,
                query="test",
                user=mock_user,
                space_id=1,
                citation_type="article",
                year_from=2020,
                year_to=2024,
                authors=["Test Author"],
                skip=0,
                limit=20,
            )


class TestExportCitations:
    """Test export citations endpoint."""

    @pytest.mark.asyncio
    async def test_export_citations_bibtex(
        self,
        mock_user: User,
        mock_space: Space,
        async_test_db: AsyncSession,
    ):
        """Test export citations as BibTeX."""
        export_data = BibTeXExportRequest(
            citation_ids=[1, 2, 3],
            space_id=1,
            format="bibtex",
        )

        with patch("app.api.v1.endpoints.citations.crud.crud_space") as mock_crud_space:
            with patch(
                "app.api.v1.endpoints.citations.citation_service"
            ) as mock_service:
                mock_crud_space.get = AsyncMock(return_value=mock_space)
                mock_service.export_citations = AsyncMock(
                    return_value="@article{test2024,\n  title={Test},\n}"
                )

                result = await export_citations(
                    export_data=export_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

                assert result.status_code == 200
                assert result.media_type == "text/plain"
                assert (
                    "filename=references.bib" in result.headers["Content-Disposition"]
                )

    @pytest.mark.asyncio
    async def test_export_citations_json(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test export citations as JSON."""
        export_data = BibTeXExportRequest(
            citation_ids=[1, 2],
            format="json",
            space_id=None,
        )

        with patch("app.api.v1.endpoints.citations.citation_service") as mock_service:
            mock_service.export_citations = AsyncMock(
                return_value='[{"id": 1, "title": "Test"}]'
            )

            result = await export_citations(
                export_data=export_data,
                db=async_test_db,
                current_user=mock_user,
            )

            assert result.status_code == 200
            assert result.media_type == "application/json"
            assert "filename=references.json" in result.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_export_citations_no_permission(
        self,
        mock_user: User,
        mock_space: Space,
        async_test_db: AsyncSession,
    ):
        """Test export without space permission."""
        mock_space.user_id = 999
        mock_space.is_public = False
        export_data = BibTeXExportRequest(
            citation_ids=[1],
            space_id=1,
            format="bibtex",
        )

        with patch("app.api.v1.endpoints.citations.crud.crud_space") as mock_crud_space:
            mock_crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud_space.get_user_access = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await export_citations(
                    export_data=export_data,
                    db=async_test_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 403
            assert "无权访问此空间" in str(exc_info.value.detail)


class TestFormatCitations:
    """Test format citations endpoint."""

    @pytest.mark.asyncio
    async def test_format_citations_apa(
        self,
        mock_user: User,
        async_test_db: AsyncSession,
    ):
        """Test format citations in APA style."""
        format_data = CitationStyleFormat(
            citation_ids=[1, 2],
            style="apa",
        )

        with patch("app.api.v1.endpoints.citations.citation_service") as mock_service:
            mock_service.format_citations = AsyncMock(
                return_value=[
                    {
                        "citation_id": 1,
                        "formatted_text": "Author, T. (2024). Test Citation. Journal.",
                        "style": "apa",
                    },
                    {
                        "citation_id": 2,
                        "formatted_text": "Author2, T. (2024). Test Citation 2. Journal.",
                        "style": "apa",
                    },
                ]
            )

            result = await format_citations(
                format_data=format_data,
                db=async_test_db,
                current_user=mock_user,
            )

            assert len(result) == 2
            assert isinstance(result[0], FormattedCitation)
            assert result[0].citation_id == 1
            assert "Author, T. (2024)" in result[0].formatted_text
