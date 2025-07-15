"""Unit tests for citation CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_citation.py -v
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.citation import crud_citation
from app.crud.document import crud_document
from app.crud.space import crud_space
from app.crud.user import crud_user
from app.schemas.citation import CitationCreate, CitationUpdate
from app.schemas.documents import DocumentCreate
from app.schemas.spaces import SpaceCreate
from app.schemas.users import UserCreate


def create_citation(**kwargs) -> CitationCreate:
    """Helper function to create CitationCreate with sensible defaults."""
    defaults = {
        "citation_type": "article",
        "bibtex_key": "default_key",
        "title": "Default Title",
        "authors": ["Default Author"],
    }
    defaults.update(kwargs)
    return CitationCreate(**defaults)


@pytest.fixture
async def test_user(async_test_db: AsyncSession):
    """Create a test user."""
    user_in = UserCreate(
        username="citationuser",
        email="citationuser@example.com",
        password="password123",
        full_name="Citation User"
    )
    user = await crud_user.create(async_test_db, obj_in=user_in)
    return user


@pytest.fixture
async def test_space(async_test_db: AsyncSession, test_user):
    """Create a test space."""
    space_in = SpaceCreate(
        name="Test Citation Space",
        description="A space for testing citations"
    )  # type: ignore
    space = await crud_space.create(async_test_db, obj_in=space_in, user_id=test_user.id)
    return space


@pytest.fixture
async def test_document(async_test_db: AsyncSession, test_user, test_space):
    """Create a test document."""
    doc_in = DocumentCreate(
        filename="test_paper.pdf",
        content_type="application/pdf",
        size=2048000,
        space_id=test_space.id
    )  # type: ignore
    document = await crud_document.create(
        async_test_db,
        obj_in=doc_in,
        user_id=test_user.id,
        file_path="test/paper.pdf",
        file_hash="paper_hash"
    )
    return document


class TestCRUDCitation:
    """Test suite for Citation CRUD operations."""

    async def test_create_citation(self, async_test_db: AsyncSession, test_user, test_space, test_document):
        """Test creating a citation."""
        citation_in = create_citation(
            document_id=test_document.id,
            citation_type="article",
            bibtex_key="smith2024ai",
            title="Artificial Intelligence in Modern Computing",
            authors=["John Smith", "Jane Doe"],
            year=2024,
            journal="Journal of AI Research",
            volume="15",
            number="3",
            pages="123-145",
            doi="10.1000/182",
            url="https://example.com/paper",
            abstract="A comprehensive study of AI applications in modern computing systems.",
            keywords=["artificial intelligence", "machine learning", "computing"],
            bibtex_raw="@article{smith2024ai,\n  title={Artificial Intelligence in Modern Computing},\n  author={Smith, John and Doe, Jane},\n  journal={Journal of AI Research},\n  year={2024}\n}",
            meta_data={"source": "manual", "verified": True}
        )

        citation = await crud_citation.create(
            async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
        )

        # Assertions
        assert citation.id is not None
        assert citation.document_id == test_document.id
        assert citation.user_id == test_user.id
        assert citation.space_id == test_space.id
        assert citation.citation_type == "article"
        assert citation.bibtex_key == "smith2024ai"
        assert citation.title == "Artificial Intelligence in Modern Computing"
        assert citation.authors == ["John Smith", "Jane Doe"]
        assert citation.year == 2024
        assert citation.journal == "Journal of AI Research"
        assert citation.volume == "15"
        assert citation.number == "3"
        assert citation.pages == "123-145"
        assert citation.doi == "10.1000/182"
        assert citation.url == "https://example.com/paper"
        assert citation.abstract == "A comprehensive study of AI applications in modern computing systems."
        assert citation.keywords == ["artificial intelligence", "machine learning", "computing"]
        assert citation.meta_data == {"source": "manual", "verified": True}

    async def test_create_citation_without_document(self, async_test_db: AsyncSession, test_user, test_space):
        """Test creating a citation without an associated document."""
        citation_in = create_citation(
            citation_type="book",
            bibtex_key="johnson2023ml",
            title="Machine Learning Fundamentals",
            authors=["Alice Johnson"],
            year=2023,
            publisher="Tech Books Inc"
        )

        citation = await crud_citation.create(
            async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
        )

        assert citation.document_id is None
        assert citation.citation_type == "book"
        assert citation.bibtex_key == "johnson2023ml"
        assert citation.title == "Machine Learning Fundamentals"
        assert citation.publisher == "Tech Books Inc"

    async def test_get_by_bibtex_key(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting citation by BibTeX key."""
        citation_in = create_citation(
            bibtex_key="unique2024key",
            title="Unique Research Paper",
            authors=["Researcher One"]
        )

        created_citation = await crud_citation.create(
            async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
        )

        # Get by BibTeX key
        retrieved_citation = await crud_citation.get_by_bibtex_key(
            async_test_db, bibtex_key="unique2024key", user_id=test_user.id
        )

        assert retrieved_citation is not None
        assert retrieved_citation.id == created_citation.id
        assert retrieved_citation.bibtex_key == "unique2024key"
        assert retrieved_citation.title == "Unique Research Paper"

        # Test non-existent key
        non_existent = await crud_citation.get_by_bibtex_key(
            async_test_db, bibtex_key="nonexistent", user_id=test_user.id
        )
        assert non_existent is None

    async def test_get_by_space(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting citations by space."""
        # Create multiple citations
        citation_data = [
            ("article1", "First Article", 2024),
            ("book1", "First Book", 2023),
            ("article2", "Second Article", 2022),
            ("conference1", "Conference Paper", 2024),
            ("misc1", "Miscellaneous", 2021),
        ]

        for i, (key, title, year) in enumerate(citation_data):
            citation_in = create_citation(
                citation_type="article" if "article" in key else key.split("1")[0],
                bibtex_key=key,
                title=title,
                authors=[f"Author {i+1}"],
                year=year
            )
            await crud_citation.create(
                async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
            )

        # Get all citations for space
        citations = await crud_citation.get_by_space(async_test_db, space_id=test_space.id)
        assert len(citations) == 5

        # Should be ordered by year desc, then created_at desc
        years = [c.year for c in citations if c.year]
        assert years == sorted(years, reverse=True)

        # Test pagination
        first_page = await crud_citation.get_by_space(
            async_test_db, space_id=test_space.id, skip=0, limit=3
        )
        assert len(first_page) == 3

        second_page = await crud_citation.get_by_space(
            async_test_db, space_id=test_space.id, skip=3, limit=3
        )
        assert len(second_page) == 2

    async def test_get_by_document(self, async_test_db: AsyncSession, test_user, test_space, test_document):
        """Test getting citations by document."""
        # Create citations for the document
        for i in range(3):
            citation_in = create_citation(
                document_id=test_document.id,
                citation_type="article",
                bibtex_key=f"doc_citation_{i}",
                title=f"Document Citation {i}",
                authors=[f"Doc Author {i}"]
            )
            await crud_citation.create(
                async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
            )

        # Create a citation without document
        citation_in = create_citation(
            citation_type="book",
            bibtex_key="no_doc_citation",
            title="No Document Citation",
            authors=["Independent Author"]
        )
        await crud_citation.create(
            async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
        )

        # Get citations for document
        doc_citations = await crud_citation.get_by_document(
            async_test_db, document_id=test_document.id
        )
        assert len(doc_citations) == 3
        assert all(c.document_id == test_document.id for c in doc_citations)

    async def test_search_citations(self, async_test_db: AsyncSession, test_user, test_space):
        """Test searching citations."""
        # Create searchable citations
        citations_data = [
            ("python2024", "Python Programming Guide", "programming", ["Python Team"], 2024, "article"),
            ("ai2023", "Artificial Intelligence Research", "ai", ["AI Researcher"], 2023, "article"),
            ("db2022", "Database Design Patterns", "database", ["DB Expert"], 2022, "book"),
            ("web2024", "Web Development with Python", "web", ["Web Dev"], 2024, "book"),
        ]

        for key, title, abstract, authors, year, ctype in citations_data:
            citation_in = create_citation(
                citation_type=ctype,
                bibtex_key=key,
                title=title,
                authors=authors,
                year=year,
                journal="Test Journal" if ctype == "article" else None,
                abstract=abstract
            )
            await crud_citation.create(
                async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
            )

        # Search by title
        python_citations = await crud_citation.search(
            async_test_db, query="Python", user_id=test_user.id
        )
        assert len(python_citations) == 2

        # Search by abstract
        ai_citations = await crud_citation.search(
            async_test_db, query="ai", user_id=test_user.id
        )
        assert len(ai_citations) == 1
        assert "Artificial Intelligence" in ai_citations[0].title

        # Search with type filter
        articles = await crud_citation.search(
            async_test_db, query="", user_id=test_user.id, citation_type="article"
        )
        assert len(articles) == 2
        assert all(c.citation_type == "article" for c in articles)

        # Search with year range
        recent_citations = await crud_citation.search(
            async_test_db, query="", user_id=test_user.id, year_from=2023, year_to=2024
        )
        assert len(recent_citations) == 3

        # Search with author filter
        python_team_citations = await crud_citation.search(
            async_test_db, query="", user_id=test_user.id, authors=["Python Team"]
        )
        assert len(python_team_citations) == 1

        # Search with space filter
        space_citations = await crud_citation.search(
            async_test_db, query="", user_id=test_user.id, space_id=test_space.id
        )
        assert len(space_citations) == 4

    async def test_get_user_citations(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting all user citations."""
        # Create citations
        for i in range(7):
            citation_in = create_citation(
                citation_type="article",
                bibtex_key=f"user_citation_{i}",
                title=f"User Citation {i}",
                authors=[f"User Author {i}"]
            )
            await crud_citation.create(
                async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
            )

        # Get all user citations
        user_citations = await crud_citation.get_user_citations(
            async_test_db, user_id=test_user.id
        )
        assert len(user_citations) == 7

        # Test pagination
        first_page = await crud_citation.get_user_citations(
            async_test_db, user_id=test_user.id, skip=0, limit=5
        )
        assert len(first_page) == 5

        second_page = await crud_citation.get_user_citations(
            async_test_db, user_id=test_user.id, skip=5, limit=5
        )
        assert len(second_page) == 2

    async def test_get_by_ids(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting citations by ID list."""
        # Create citations
        created_citations = []
        for i in range(5):
            citation_in = create_citation(
                citation_type="article",
                bibtex_key=f"id_citation_{i}",
                title=f"ID Citation {i}",
                authors=[f"ID Author {i}"]
            )
            citation = await crud_citation.create(
                async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
            )
            created_citations.append(citation)

        # Get by specific IDs
        target_ids = [created_citations[1].id, created_citations[3].id, created_citations[4].id]
        retrieved_citations = await crud_citation.get_by_ids(
            async_test_db, ids=target_ids, user_id=test_user.id
        )

        assert len(retrieved_citations) == 3
        retrieved_ids = [c.id for c in retrieved_citations]
        assert set(retrieved_ids) == set(target_ids)

        # Test with non-existent IDs
        non_existent_citations = await crud_citation.get_by_ids(
            async_test_db, ids=[99999, 99998], user_id=test_user.id
        )
        assert len(non_existent_citations) == 0

    async def test_count_by_space(self, async_test_db: AsyncSession, test_user, test_space):
        """Test counting citations by space."""
        # Initially should be 0
        count = await crud_citation.count_by_space(async_test_db, space_id=test_space.id)
        assert count == 0

        # Create some citations
        for i in range(8):
            citation_in = create_citation(
                citation_type="article",
                bibtex_key=f"count_citation_{i}",
                title=f"Count Citation {i}",
                authors=[f"Count Author {i}"]
            )
            await crud_citation.create(
                async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
            )

        # Count should be 8
        count = await crud_citation.count_by_space(async_test_db, space_id=test_space.id)
        assert count == 8

    async def test_create_batch(self, async_test_db: AsyncSession, test_user, test_space):
        """Test batch creating citations."""
        citations_data = [
            create_citation(
                citation_type="article",
                bibtex_key="batch1",
                title="Batch Citation 1",
                authors=["Batch Author 1"],
                year=2024
            ),
            create_citation(
                citation_type="book",
                bibtex_key="batch2",
                title="Batch Citation 2",
                authors=["Batch Author 2"],
                year=2023
            ),
            create_citation(
                citation_type="inproceedings",
                bibtex_key="batch3",
                title="Batch Citation 3",
                authors=["Batch Author 3"],
                year=2022
            ),
        ]

        citations = await crud_citation.create_batch(
            async_test_db,
            citations=citations_data,
            user_id=test_user.id,
            space_id=test_space.id
        )

        assert len(citations) == 3
        assert citations[0].title == "Batch Citation 1"
        assert citations[1].title == "Batch Citation 2"
        assert citations[2].title == "Batch Citation 3"

        # Verify all have correct user_id and space_id
        for citation in citations:
            assert citation.user_id == test_user.id
            assert citation.space_id == test_space.id

    async def test_update_citation(self, async_test_db: AsyncSession, test_user, test_space):
        """Test updating a citation."""
        # Create citation
        citation_in = create_citation(
            citation_type="article",
            bibtex_key="update_test",
            title="Original Title",
            authors=["Original Author"],
            year=2020,
            journal="Original Journal"
        )
        citation = await crud_citation.create(
            async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
        )

        # Update citation
        update_data = CitationUpdate(
            title="Updated Title",
            authors=["Updated Author", "Second Author"],
            year=2024,
            journal="Updated Journal",
            abstract="New abstract content",
            meta_data=None
        )
        updated_citation = await crud_citation.update(
            async_test_db, db_obj=citation, obj_in=update_data
        )

        assert updated_citation.title == "Updated Title"
        assert updated_citation.authors == ["Updated Author", "Second Author"]
        assert updated_citation.year == 2024
        assert updated_citation.journal == "Updated Journal"
        assert updated_citation.abstract == "New abstract content"
        # Original fields should remain unchanged
        assert updated_citation.bibtex_key == "update_test"
        assert updated_citation.citation_type == "article"

    async def test_delete_citation(self, async_test_db: AsyncSession, test_user, test_space):
        """Test deleting a citation."""
        # Create citation
        citation_in = create_citation(
            citation_type="article",
            bibtex_key="delete_test",
            title="To Be Deleted",
            authors=["Delete Author"]
        )
        citation = await crud_citation.create(
            async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
        )
        citation_id = citation.id

        # Delete citation
        deleted_citation = await crud_citation.remove(async_test_db, id=citation_id)
        assert deleted_citation is not None

        # Verify deletion
        retrieved_citation = await crud_citation.get(async_test_db, citation_id)
        assert retrieved_citation is None

    async def test_user_isolation(self, async_test_db: AsyncSession, test_space):
        """Test that users can only access their own citations."""
        # Create two users
        user1_in = UserCreate(
            username="cituser1",
            email="cituser1@example.com",
            password="password123",
            full_name="Citation User One"
        )
        user1 = await crud_user.create(async_test_db, obj_in=user1_in)

        user2_in = UserCreate(
            username="cituser2",
            email="cituser2@example.com",
            password="password123",
            full_name="Citation User Two"
        )
        user2 = await crud_user.create(async_test_db, obj_in=user2_in)

        # Create citations for each user
        citation1_in = create_citation(
            citation_type="article",
            bibtex_key="user1_citation",
            title="User 1 Citation",
            authors=["User 1 Author"]
        )
        await crud_citation.create(
            async_test_db, obj_in=citation1_in, user_id=user1.id, space_id=test_space.id
        )

        citation2_in = create_citation(
            citation_type="book",
            bibtex_key="user2_citation",
            title="User 2 Citation",
            authors=["User 2 Author"]
        )
        await crud_citation.create(
            async_test_db, obj_in=citation2_in, user_id=user2.id, space_id=test_space.id
        )

        # Each user should only see their own citations when searching by BibTeX key
        user1_citation = await crud_citation.get_by_bibtex_key(
            async_test_db, bibtex_key="user1_citation", user_id=user1.id
        )
        assert user1_citation is not None
        assert user1_citation.title == "User 1 Citation"

        user1_cannot_see_user2 = await crud_citation.get_by_bibtex_key(
            async_test_db, bibtex_key="user2_citation", user_id=user1.id
        )
        assert user1_cannot_see_user2 is None

        user2_citation = await crud_citation.get_by_bibtex_key(
            async_test_db, bibtex_key="user2_citation", user_id=user2.id
        )
        assert user2_citation is not None
        assert user2_citation.title == "User 2 Citation"

    async def test_citation_types(self, async_test_db: AsyncSession, test_user, test_space):
        """Test different citation types."""
        citation_types = [
            ("article", "Journal Article", {"journal": "Nature"}),
            ("book", "Academic Book", {"publisher": "Academic Press"}),
            ("inproceedings", "Conference Paper", {"booktitle": "ICML 2024"}),
            ("misc", "Miscellaneous Source", {"note": "Preprint"}),
            ("phdthesis", "PhD Thesis", {"school": "MIT"}),
            ("techreport", "Technical Report", {"institution": "Stanford"}),
        ]

        for ctype, title, extra_fields in citation_types:
            citation_data = {
                "citation_type": ctype,
                "bibtex_key": f"{ctype}_test",
                "title": title,
                "authors": [f"{ctype.title()} Author"]
            }
            citation_data.update(extra_fields)

            citation_in = CitationCreate(**citation_data)
            citation = await crud_citation.create(
                async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
            )
            assert citation.citation_type == ctype
            assert citation.title == title

    async def test_complex_search_scenarios(self, async_test_db: AsyncSession, test_user, test_space):
        """Test complex search scenarios."""
        # Create citations for complex searching
        citations = [
            create_citation(
                citation_type="article",
                bibtex_key="ml2024",
                title="Machine Learning in Healthcare",
                authors=["Dr. Smith", "Prof. Johnson"],
                year=2024,
                journal="AI Medicine Journal",
                abstract="Applications of ML in medical diagnosis"
            ),
            create_citation(
                citation_type="article",
                bibtex_key="dl2023",
                title="Deep Learning Architectures",
                authors=["Dr. Smith", "Dr. Williams"],
                year=2023,
                journal="Neural Networks Today",
                abstract="Survey of modern deep learning approaches"
            ),
            create_citation(
                citation_type="book",
                bibtex_key="stats2022",
                title="Statistical Methods for Data Science",
                authors=["Prof. Brown"],
                year=2022,
                publisher="Data Science Press",
                abstract="Comprehensive guide to statistical analysis"
            ),
        ]

        for citation_in in citations:
            await crud_citation.create(
                async_test_db, obj_in=citation_in, user_id=test_user.id, space_id=test_space.id
            )

        # Search by multiple authors
        smith_papers = await crud_citation.search(
            async_test_db, query="", user_id=test_user.id, authors=["Dr. Smith"]
        )
        assert len(smith_papers) == 2

        # Search by year range and type
        recent_articles = await crud_citation.search(
            async_test_db,
            query="",
            user_id=test_user.id,
            citation_type="article",
            year_from=2023,
            year_to=2024
        )
        assert len(recent_articles) == 2

        # Search by journal
        ai_journal_papers = await crud_citation.search(
            async_test_db, query="AI Medicine", user_id=test_user.id
        )
        assert len(ai_journal_papers) == 1

        # Complex query with multiple filters
        filtered_results = await crud_citation.search(
            async_test_db,
            query="Machine",
            user_id=test_user.id,
            citation_type="article",
            year_from=2024,
            authors=["Dr. Smith"]
        )
        assert len(filtered_results) == 1
        assert "Machine Learning" in filtered_results[0].title

    async def test_edge_cases_and_validation(self, async_test_db: AsyncSession, test_user, test_space):
        """Test edge cases and validation scenarios."""
        # Test with minimal required fields
        minimal_citation = create_citation(
            citation_type="misc",
            bibtex_key="minimal_test",
            title="Minimal Citation",
            authors=[]  # Empty authors list
        )
        citation = await crud_citation.create(
            async_test_db, obj_in=minimal_citation, user_id=test_user.id, space_id=test_space.id
        )
        assert citation.authors == []
        assert citation.year is None

        # Test with very long title
        long_title = "A" * 500  # Very long title
        long_citation = create_citation(
            citation_type="article",
            bibtex_key="long_title_test",
            title=long_title,
            authors=["Long Title Author"]
        )
        citation = await crud_citation.create(
            async_test_db, obj_in=long_citation, user_id=test_user.id, space_id=test_space.id
        )
        assert citation.title == long_title

        # Test search with empty query
        all_citations = await crud_citation.search(
            async_test_db, query="", user_id=test_user.id
        )
        assert len(all_citations) >= 2  # At least the citations we just created

        # Test pagination edge cases
        citations = await crud_citation.get_by_space(
            async_test_db, space_id=test_space.id, skip=1000, limit=10
        )
        assert len(citations) == 0  # No results beyond available data
