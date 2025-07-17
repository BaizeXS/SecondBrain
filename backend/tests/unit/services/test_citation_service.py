"""Unit tests for Citation Service."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Citation, User
from app.services.citation_service import CitationService


@pytest.fixture
def citation_service():
    """创建引用服务实例."""
    return CitationService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话."""
    db = Mock(spec=AsyncSession)
    db.commit = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """创建模拟用户."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_citation():
    """创建模拟引用."""
    citation = Mock(spec=Citation)
    citation.id = 1
    citation.citation_type = "article"
    citation.bibtex_key = "test2024"
    citation.title = "Test Article"
    citation.authors = ["Test Author"]
    citation.year = 2024
    citation.journal = "Test Journal"
    citation.volume = "1"
    citation.number = "1"
    citation.pages = "1-10"
    citation.publisher = "Test Publisher"
    citation.booktitle = None
    citation.doi = "10.1234/test"
    citation.isbn = None
    citation.url = "https://example.com/test"
    citation.abstract = "Test abstract"
    citation.keywords = ["test", "citation"]
    citation.bibtex_raw = "@article{test2024, ...}"
    citation.created_at = Mock()
    citation.created_at.isoformat.return_value = "2024-01-01T00:00:00"
    citation.updated_at = Mock()
    citation.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
    return citation


@pytest.fixture
def bibtex_entry():
    """创建BibTeX条目."""
    return {
        'citation_type': 'article',
        'bibtex_key': 'test2024',
        'title': 'Test Article',
        'authors': ['Test Author'],
        'year': 2024,
        'journal': 'Test Journal',
        'volume': '1',
        'number': '1',
        'pages': '1-10',
        'doi': '10.1234/test',
        'url': 'https://example.com/test',
        'abstract': 'Test abstract',
        'keywords': ['test', 'citation'],
        'bibtex_raw': '@article{test2024, ...}',
        'fields': {'custom': 'value'}
    }


class TestImportBibTeX:
    """测试BibTeX导入功能."""

    @pytest.mark.asyncio
    async def test_import_bibtex_success(
        self, citation_service, mock_db, mock_user, mock_citation, bibtex_entry
    ):
        """测试成功导入BibTeX."""
        # Mock解析器
        with patch('app.services.bibtex_service.bibtex_parser.parse_bibtex') as mock_parse:
            mock_parse.return_value = [bibtex_entry]

            # Mock CRUD
            from app.crud.citation import crud_citation
            crud_citation.get_by_bibtex_key = AsyncMock(return_value=None)
            crud_citation.create = AsyncMock(return_value=mock_citation)

            # 执行
            result = await citation_service.import_bibtex(
                db=mock_db,
                bibtex_content="@article{test2024, ...}",
                space_id=1,
                user=mock_user,
                create_documents=False,
                tags=["test"]
            )

            # 验证
            assert result["imported_count"] == 1
            assert result["failed_count"] == 0
            assert len(result["citations"]) == 1
            assert result["citations"][0] == mock_citation

    @pytest.mark.asyncio
    async def test_import_bibtex_duplicate(
        self, citation_service, mock_db, mock_user, mock_citation, bibtex_entry
    ):
        """测试导入重复的BibTeX."""
        # Mock解析器
        with patch('app.services.bibtex_service.bibtex_parser.parse_bibtex') as mock_parse:
            mock_parse.return_value = [bibtex_entry]

            # Mock CRUD - 返回已存在的引用
            from app.crud.citation import crud_citation
            crud_citation.get_by_bibtex_key = AsyncMock(return_value=mock_citation)

            # 执行
            result = await citation_service.import_bibtex(
                db=mock_db,
                bibtex_content="@article{test2024, ...}",
                space_id=1,
                user=mock_user
            )

            # 验证
            assert result["imported_count"] == 0
            assert result["failed_count"] == 1  # 重复会计入失败计数
            assert len(result["errors"]) == 1
            assert "引用已存在" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_import_bibtex_parse_error(
        self, citation_service, mock_db, mock_user
    ):
        """测试解析BibTeX时出错."""
        # Mock解析器抛出异常
        with patch('app.services.bibtex_service.bibtex_parser.parse_bibtex') as mock_parse:
            mock_parse.side_effect = Exception("Parse error")

            # 执行
            result = await citation_service.import_bibtex(
                db=mock_db,
                bibtex_content="invalid bibtex",
                space_id=1,
                user=mock_user
            )

            # 验证
            assert result["imported_count"] == 0
            assert result["failed_count"] == 1
            assert "解析错误" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_import_bibtex_with_document_creation(
        self, citation_service, mock_db, mock_user, mock_citation, bibtex_entry
    ):
        """测试导入BibTeX并创建文档."""
        # Mock解析器
        with patch('app.services.bibtex_service.bibtex_parser.parse_bibtex') as mock_parse:
            mock_parse.return_value = [bibtex_entry]

            # Mock CRUD
            from app.crud.citation import crud_citation
            crud_citation.get_by_bibtex_key = AsyncMock(return_value=None)
            crud_citation.create = AsyncMock(return_value=mock_citation)

            # Mock文档创建
            citation_service._create_document_from_citation = AsyncMock()

            # 执行
            result = await citation_service.import_bibtex(
                db=mock_db,
                bibtex_content="@article{test2024, ...}",
                space_id=1,
                user=mock_user,
                create_documents=True
            )

            # 验证
            assert result["imported_count"] == 1
            citation_service._create_document_from_citation.assert_called_once()


class TestCreateDocumentFromCitation:
    """测试从引用创建文档."""

    @pytest.mark.asyncio
    async def test_create_document_from_citation_success(
        self, citation_service, mock_db, mock_user, mock_citation
    ):
        """测试成功创建文档."""
        # Mock文档服务
        with patch('app.services.document_service.document_service') as mock_doc_service:
            mock_doc_service.import_from_url = AsyncMock(
                return_value={"status": "success", "document_id": 10}
            )

            # 执行
            await citation_service._create_document_from_citation(
                db=mock_db,
                citation=mock_citation,
                space_id=1,
                user=mock_user,
                tags=["test"]
            )

            # 验证
            mock_doc_service.import_from_url.assert_called_once()
            assert mock_citation.document_id == 10
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_no_url(
        self, citation_service, mock_db, mock_user
    ):
        """测试引用没有URL时不创建文档."""
        # 创建没有URL的引用
        citation = Mock(spec=Citation)
        citation.url = None

        # Mock文档服务
        with patch('app.services.document_service.document_service') as mock_doc_service:
            # 执行
            await citation_service._create_document_from_citation(
                db=mock_db,
                citation=citation,
                space_id=1,
                user=mock_user
            )

            # 验证 - 不应该调用导入
            mock_doc_service.import_from_url.assert_not_called()


class TestExportCitations:
    """测试导出引用功能."""

    @pytest.mark.asyncio
    async def test_export_bibtex_format(
        self, citation_service, mock_db, mock_user, mock_citation
    ):
        """测试BibTeX格式导出."""
        # Mock CRUD
        from app.crud.citation import crud_citation
        crud_citation.get_by_ids = AsyncMock(return_value=[mock_citation])

        # Mock导出方法
        citation_service._export_as_bibtex = Mock(return_value="@article{...}")

        # 执行
        result = await citation_service.export_citations(
            db=mock_db,
            user=mock_user,
            citation_ids=[1],
            format="bibtex"
        )

        # 验证
        assert result == "@article{...}"
        crud_citation.get_by_ids.assert_called_once()
        citation_service._export_as_bibtex.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_json_format(
        self, citation_service, mock_db, mock_user, mock_citation
    ):
        """测试JSON格式导出."""
        # Mock CRUD
        from app.crud.citation import crud_citation
        crud_citation.get_user_citations = AsyncMock(return_value=[mock_citation])

        # 执行
        result = await citation_service.export_citations(
            db=mock_db,
            user=mock_user,
            format="json"
        )

        # 验证
        assert isinstance(result, str)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_export_csv_format(
        self, citation_service, mock_db, mock_user, mock_citation
    ):
        """测试CSV格式导出."""
        # Mock CRUD
        from app.crud.citation import crud_citation
        crud_citation.get_by_space = AsyncMock(return_value=[mock_citation])

        # 执行
        result = await citation_service.export_citations(
            db=mock_db,
            user=mock_user,
            space_id=1,
            format="csv"
        )

        # 验证
        assert isinstance(result, str)
        assert "bibtex_key" in result  # CSV header
        assert "test2024" in result  # Data


class TestFormatCitations:
    """测试格式化引用功能."""

    @pytest.mark.asyncio
    async def test_format_citations_apa_style(
        self, citation_service, mock_db, mock_user, mock_citation
    ):
        """测试APA格式化."""
        # Mock CRUD
        from app.crud.citation import crud_citation
        crud_citation.get_by_ids = AsyncMock(return_value=[mock_citation])

        # Mock格式化
        with patch('app.services.bibtex_service.bibtex_parser.format_citation') as mock_format:
            mock_format.return_value = "Test Author (2024). Test Article. Test Journal, 1(1), 1-10."

            # 执行
            result = await citation_service.format_citations(
                db=mock_db,
                citation_ids=[1],
                style="apa",
                user=mock_user
            )

            # 验证
            assert len(result) == 1
            assert result[0]["citation_id"] == 1
            assert result[0]["style"] == "apa"
            assert "Test Author (2024)" in result[0]["formatted_text"]


class TestSearchCitations:
    """测试搜索引用功能."""

    @pytest.mark.asyncio
    async def test_search_citations(
        self, citation_service, mock_db, mock_user, mock_citation
    ):
        """测试搜索引用."""
        # Mock CRUD
        from app.crud.citation import crud_citation
        crud_citation.search = AsyncMock(return_value=[mock_citation])

        # 执行
        results = await citation_service.search_citations(
            db=mock_db,
            query="test",
            user=mock_user,
            space_id=1,
            citation_type="article",
            year_from=2020,
            year_to=2024,
            authors=["Test Author"],
            skip=0,
            limit=20
        )

        # 验证
        assert len(results) == 1
        assert results[0] == mock_citation
        crud_citation.search.assert_called_once_with(
            mock_db,
            query="test",
            user_id=1,
            space_id=1,
            citation_type="article",
            year_from=2020,
            year_to=2024,
            authors=["Test Author"],
            skip=0,
            limit=20
        )


class TestExportHelpers:
    """测试导出辅助方法."""

    def test_export_as_bibtex(self, citation_service, mock_citation):
        """测试导出为BibTeX格式."""
        with patch('app.services.bibtex_service.bibtex_parser.export_bibtex') as mock_export:
            mock_export.return_value = "@article{test2024, ...}"

            result = citation_service._export_as_bibtex([mock_citation])

            assert result == "@article{test2024, ...}"
            mock_export.assert_called_once()

            # 验证传递的数据
            call_args = mock_export.call_args[0][0]
            assert len(call_args) == 1
            assert call_args[0]['bibtex_key'] == 'test2024'

    def test_export_as_json(self, citation_service, mock_citation):
        """测试导出为JSON格式."""
        result = citation_service._export_as_json([mock_citation])

        assert isinstance(result, str)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["title"] == "Test Article"
        assert data[0]["authors"] == ["Test Author"]

    def test_export_as_csv(self, citation_service, mock_citation):
        """测试导出为CSV格式."""
        result = citation_service._export_as_csv([mock_citation])

        assert isinstance(result, str)
        lines = result.strip().split('\n')
        assert len(lines) == 2  # Header + 1 data row

        # 检查header
        assert "bibtex_key" in lines[0]
        assert "title" in lines[0]

        # 检查数据
        assert "test2024" in lines[1]
        assert "Test Article" in lines[1]
        assert "Test Author" in lines[1]


class TestImportBibTeXEdgeCases:
    """测试BibTeX导入的边缘情况."""

    @pytest.mark.asyncio
    async def test_import_bibtex_empty_entries(
        self, citation_service, mock_db, mock_user
    ):
        """测试解析结果为空时的处理."""
        # Mock解析器返回空列表
        with patch('app.services.bibtex_service.bibtex_parser.parse_bibtex') as mock_parse:
            mock_parse.return_value = []

            # 执行
            result = await citation_service.import_bibtex(
                db=mock_db,
                bibtex_content="",
                space_id=1,
                user=mock_user
            )

            # 验证
            assert result["imported_count"] == 0
            assert result["failed_count"] == 0
            assert len(result["citations"]) == 0
            assert "未找到有效的BibTeX条目" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_import_bibtex_creation_error(
        self, citation_service, mock_db, mock_user, bibtex_entry
    ):
        """测试创建引用时出现异常."""
        # Mock解析器
        with patch('app.services.bibtex_service.bibtex_parser.parse_bibtex') as mock_parse:
            mock_parse.return_value = [bibtex_entry]

            # Mock CRUD
            from app.crud.citation import crud_citation
            crud_citation.get_by_bibtex_key = AsyncMock(return_value=None)
            crud_citation.create = AsyncMock(side_effect=Exception("Database error"))

            # 执行
            result = await citation_service.import_bibtex(
                db=mock_db,
                bibtex_content="@article{test2024, ...}",
                space_id=1,
                user=mock_user
            )

            # 验证
            assert result["imported_count"] == 0
            assert result["failed_count"] == 1
            assert len(result["errors"]) == 1
            assert "Database error" in result["errors"][0]["error"]
            assert result["errors"][0]["bibtex_key"] == "test2024"


class TestCreateDocumentFromCitationException:
    """测试从引用创建文档的异常情况."""

    @pytest.mark.asyncio
    async def test_create_document_exception(
        self, citation_service, mock_db, mock_user, mock_citation
    ):
        """测试创建文档时出现异常."""
        # Mock文档服务抛出异常
        with patch('app.services.document_service.document_service') as mock_doc_service:
            mock_doc_service.import_from_url = AsyncMock(
                side_effect=Exception("Network error")
            )

            # 执行 - 不应该抛出异常，而是静默处理
            await citation_service._create_document_from_citation(
                db=mock_db,
                citation=mock_citation,
                space_id=1,
                user=mock_user,
                tags=["test"]
            )

            # 验证 - 文档ID不应该被设置
            assert not hasattr(mock_citation, 'document_id') or mock_citation.document_id != 10
            mock_db.commit.assert_not_called()


class TestExportCitationsDefaultFormat:
    """测试导出引用的默认格式."""

    @pytest.mark.asyncio
    async def test_export_unknown_format_defaults_to_bibtex(
        self, citation_service, mock_db, mock_user, mock_citation
    ):
        """测试未知格式时默认使用BibTeX."""
        # Mock CRUD
        from app.crud.citation import crud_citation
        crud_citation.get_by_ids = AsyncMock(return_value=[mock_citation])

        # Mock导出方法
        citation_service._export_as_bibtex = Mock(return_value="@article{...}")

        # 执行 - 使用未知格式
        result = await citation_service.export_citations(
            db=mock_db,
            user=mock_user,
            citation_ids=[1],
            format="unknown_format"  # 未知格式
        )

        # 验证 - 应该调用BibTeX导出
        assert result == "@article{...}"
        citation_service._export_as_bibtex.assert_called_once()
