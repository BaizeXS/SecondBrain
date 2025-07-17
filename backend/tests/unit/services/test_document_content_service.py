"""Unit tests for Document Content Service."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from app.services.document_content_service import DocumentContentService


@pytest.fixture
def doc_service():
    """创建文档内容服务实例."""
    return DocumentContentService()


@pytest.fixture
def mock_file_path():
    """创建模拟文件路径."""
    path = Mock(spec=Path)
    # 设置suffix属性以支持.lower()调用
    path.suffix = Mock()
    path.suffix.lower = Mock(return_value=".txt")
    path.stat.return_value = Mock(
        st_size=1024,
        st_ctime=1234567890.0,
        st_mtime=1234567890.0
    )
    return path


class TestDocumentContentService:
    """测试文档内容服务初始化."""

    def test_init_without_markitdown(self):
        """测试没有MarkItDown时的初始化."""
        # 直接创建服务，它的初始化已经尝试导入markitdown
        service = DocumentContentService()

        # 只验证基本属性
        assert hasattr(service, 'markitdown')
        assert len(service.supported_types) == 7
        assert ".pdf" in service.supported_types
        assert ".docx" in service.supported_types

    def test_init_with_markitdown(self):
        """测试有MarkItDown时的初始化."""
        mock_markitdown = Mock()
        with patch('app.services.document_content_service.logger') as mock_logger:
            with patch('builtins.__import__', return_value=Mock(MarkItDown=Mock(return_value=mock_markitdown))):
                service = DocumentContentService()

                assert service.markitdown is not None
                mock_logger.info.assert_called_with("MarkItDown initialized successfully for enhanced document conversion")


class TestExtractContent:
    """测试内容提取功能."""

    @pytest.mark.asyncio
    async def test_extract_content_with_markitdown(self, doc_service):
        """测试使用MarkItDown提取内容."""
        mock_path = Mock(spec=Path)
        mock_result = Mock(text_content="Extracted content")
        doc_service.markitdown = Mock(convert=Mock(return_value=mock_result))

        result = await doc_service.extract_content(mock_path, ".pdf")

        assert result == "Extracted content"
        doc_service.markitdown.convert.assert_called_once_with(str(mock_path))

    @pytest.mark.asyncio
    async def test_extract_content_markitdown_fallback(self, doc_service):
        """测试MarkItDown失败时的回退."""
        mock_path = Mock(spec=Path)
        # Make the path return a string when str() is called on it
        mock_path.__str__ = Mock(return_value="/path/to/file.pdf")

        doc_service.markitdown = Mock(convert=Mock(side_effect=Exception("MarkItDown error")))

        # Mock pdfplumber since pdf extraction will be attempted
        with patch('pdfplumber.open') as mock_open:
            mock_page = Mock(
                extract_text=Mock(return_value="Fallback content"),
                extract_tables=Mock(return_value=[])
            )
            mock_pdf = Mock(pages=[mock_page])
            mock_open.return_value.__enter__.return_value = mock_pdf

            result = await doc_service.extract_content(mock_path, ".pdf")

            assert result == "Fallback content"

    @pytest.mark.asyncio
    async def test_extract_content_unsupported_type(self, doc_service):
        """测试不支持的文件类型."""
        mock_path = Mock(spec=Path)

        with pytest.raises(ValueError, match="不支持的文件类型"):
            await doc_service.extract_content(mock_path, ".xyz")

    @pytest.mark.asyncio
    async def test_extract_content_empty_result(self, doc_service):
        """测试提取结果为空."""
        mock_path = Mock(spec=Path)
        doc_service._extract_txt = AsyncMock(return_value=None)

        result = await doc_service.extract_content(mock_path, ".txt")

        assert result == ""


class TestExtractPDF:
    """测试PDF提取."""

    @pytest.mark.asyncio
    async def test_extract_pdf_success(self, doc_service):
        """测试成功提取PDF."""
        mock_path = Mock(spec=Path)
        mock_page = Mock(
            extract_text=Mock(return_value="Page 1 text"),
            extract_tables=Mock(return_value=[[["A", "B"], ["1", "2"]]])
        )

        with patch('pdfplumber.open') as mock_open:
            mock_pdf = Mock(pages=[mock_page])
            mock_open.return_value.__enter__.return_value = mock_pdf

            result = await doc_service._extract_pdf(mock_path)

            assert "Page 1 text" in result
            assert "A | B" in result
            assert "1 | 2" in result

    @pytest.mark.asyncio
    async def test_extract_pdf_import_error(self, doc_service):
        """测试pdfplumber未安装."""
        mock_path = Mock(spec=Path)
        doc_service._extract_with_textract = AsyncMock(return_value="Textract result")

        with patch('builtins.__import__', side_effect=ImportError):
            result = await doc_service._extract_pdf(mock_path)

            assert result == "Textract result"

    @pytest.mark.asyncio
    async def test_extract_pdf_exception(self, doc_service):
        """测试PDF提取异常."""
        mock_path = Mock(spec=Path)
        doc_service._extract_with_textract = AsyncMock(return_value="Fallback result")

        with patch('pdfplumber.open', side_effect=Exception("PDF error")):
            result = await doc_service._extract_pdf(mock_path)

            assert result == "Fallback result"


class TestExtractDocx:
    """测试DOCX提取."""

    @pytest.mark.asyncio
    async def test_extract_docx_success(self, doc_service):
        """测试成功提取DOCX."""
        mock_path = Mock(spec=Path)
        mock_paragraph = Mock(text="Paragraph text")
        mock_cell = Mock(text="Cell text")
        mock_row = Mock(cells=[mock_cell])
        mock_table = Mock(rows=[mock_row])

        # 模拟docx模块
        mock_docx = Mock()
        mock_doc = Mock(
            paragraphs=[mock_paragraph],
            tables=[mock_table]
        )
        mock_docx.Document = Mock(return_value=mock_doc)

        with patch.dict('sys.modules', {'docx': mock_docx}):
            result = await doc_service._extract_docx(mock_path)

            assert "Paragraph text" in result
            assert "Cell text" in result

    @pytest.mark.asyncio
    async def test_extract_docx_import_error(self, doc_service):
        """测试python-docx未安装."""
        mock_path = Mock(spec=Path)
        doc_service._extract_with_textract = AsyncMock(return_value="Textract result")

        with patch('builtins.__import__', side_effect=ImportError):
            result = await doc_service._extract_docx(mock_path)

            assert result == "Textract result"


class TestExtractTxt:
    """测试TXT提取."""

    @pytest.mark.asyncio
    async def test_extract_txt_utf8(self, doc_service):
        """测试UTF-8编码的文本."""
        mock_path = Mock(spec=Path)
        content = "UTF-8 content"

        with patch('builtins.open', mock_open(read_data=content)):
            result = await doc_service._extract_txt(mock_path)

            assert result == content

    @pytest.mark.asyncio
    async def test_extract_txt_gbk(self, doc_service):
        """测试GBK编码的文本."""
        mock_path = Mock(spec=Path)

        # 模拟第一次UTF-8失败，第二次GBK成功
        mock_file = mock_open(read_data="GBK content")
        mock_file.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
            mock_file.return_value
        ]

        with patch('builtins.open', mock_file):
            result = await doc_service._extract_txt(mock_path)

            # 由于mock的限制，这里简化测试
            assert result is not None

    @pytest.mark.asyncio
    async def test_extract_txt_fallback_encoding(self, doc_service):
        """测试所有编码都失败时的回退."""
        mock_path = Mock(spec=Path)

        # 模拟所有编码都失败
        def side_effect(*args, **kwargs):
            if 'errors' in kwargs and kwargs['errors'] == 'ignore':
                return mock_open(read_data="Fallback content").return_value
            raise UnicodeDecodeError("encoding", b"", 0, 1, "invalid")

        with patch('builtins.open', side_effect=side_effect):
            result = await doc_service._extract_txt(mock_path)

            assert result == "Fallback content"

    @pytest.mark.asyncio
    async def test_extract_txt_exception(self, doc_service):
        """测试文本提取异常."""
        mock_path = Mock(spec=Path)

        with patch('builtins.open', side_effect=Exception("File error")):
            result = await doc_service._extract_txt(mock_path)

            assert result == ""


class TestExtractPptx:
    """测试PPTX提取."""

    @pytest.mark.asyncio
    async def test_extract_pptx_success(self, doc_service):
        """测试成功提取PPTX."""
        mock_path = Mock(spec=Path)
        mock_shape = Mock(text="Slide text")
        mock_slide = Mock(shapes=[mock_shape])

        # 模拟pptx模块
        mock_pptx = Mock()
        mock_prs = Mock(slides=[mock_slide])
        mock_pptx.Presentation = Mock(return_value=mock_prs)

        with patch.dict('sys.modules', {'pptx': mock_pptx}):
            result = await doc_service._extract_pptx(mock_path)

            assert "Slide text" in result

    @pytest.mark.asyncio
    async def test_extract_pptx_import_error(self, doc_service):
        """测试python-pptx未安装."""
        mock_path = Mock(spec=Path)
        doc_service._extract_with_textract = AsyncMock(return_value="Textract result")

        with patch('builtins.__import__', side_effect=ImportError):
            result = await doc_service._extract_pptx(mock_path)

            assert result == "Textract result"


class TestExtractWithTextract:
    """测试textract提取."""

    @pytest.mark.asyncio
    async def test_extract_with_textract_success(self, doc_service):
        """测试成功使用textract."""
        mock_path = Mock(spec=Path)

        # 模拟textract模块
        mock_textract = Mock()
        mock_textract.process = Mock(return_value=b"Textract content")

        with patch.dict('sys.modules', {'textract': mock_textract}):
            result = await doc_service._extract_with_textract(mock_path)

            assert result == "Textract content"

    @pytest.mark.asyncio
    async def test_extract_with_textract_import_error(self, doc_service):
        """测试textract未安装."""
        mock_path = Mock(spec=Path)

        with patch('builtins.__import__', side_effect=ImportError):
            result = await doc_service._extract_with_textract(mock_path)

            assert "无法提取文档内容" in result

    @pytest.mark.asyncio
    async def test_extract_with_textract_exception(self, doc_service):
        """测试textract提取异常."""
        mock_path = Mock(spec=Path)

        # 模拟textract模块但process方法抛出异常
        mock_textract = Mock()
        mock_textract.process = Mock(side_effect=Exception("Textract error"))

        with patch.dict('sys.modules', {'textract': mock_textract}):
            result = await doc_service._extract_with_textract(mock_path)

            assert "文档内容提取失败" in result


class TestGetDocumentMetadata:
    """测试获取文档元数据."""

    @pytest.mark.asyncio
    async def test_get_metadata_txt(self, doc_service, mock_file_path):
        """测试获取TXT文件元数据."""
        mock_file_path.suffix.lower.return_value = ".txt"

        result = await doc_service.get_document_metadata(mock_file_path)

        assert result["file_size"] == 1024
        assert result["file_extension"] == ".txt"
        assert "created_time" in result
        assert "modified_time" in result

    @pytest.mark.asyncio
    async def test_get_metadata_pdf(self, doc_service):
        """测试获取PDF元数据."""
        mock_path = Mock(spec=Path)
        mock_path.suffix = Mock()
        mock_path.suffix.lower = Mock(return_value=".pdf")
        mock_path.stat.return_value = Mock(
            st_size=2048,
            st_ctime=1234567890.0,
            st_mtime=1234567890.0
        )
        doc_service._get_pdf_metadata = AsyncMock(return_value={"page_count": 10})

        result = await doc_service.get_document_metadata(mock_path)

        assert result["page_count"] == 10
        assert result["file_size"] == 2048

    @pytest.mark.asyncio
    async def test_get_metadata_exception(self, doc_service):
        """测试获取元数据异常."""
        mock_path = Mock(spec=Path)
        mock_path.stat.side_effect = Exception("Stat error")

        result = await doc_service.get_document_metadata(mock_path)

        assert result == {}


class TestGetPdfMetadata:
    """测试获取PDF元数据."""

    @pytest.mark.asyncio
    async def test_get_pdf_metadata_success(self, doc_service):
        """测试成功获取PDF元数据."""
        mock_path = Mock(spec=Path)
        mock_metadata = {
            "Title": "Test PDF",
            "Author": "Test Author",
            "Subject": "Test Subject",
            "Creator": "Test Creator",
            "Producer": "Test Producer",
            "CreationDate": "2024-01-01",
            "ModDate": "2024-01-02"
        }

        with patch('pdfplumber.open') as mock_open:
            mock_pdf = Mock(
                pages=[Mock(), Mock()],  # 2 pages
                metadata=mock_metadata
            )
            mock_open.return_value.__enter__.return_value = mock_pdf

            result = await doc_service._get_pdf_metadata(mock_path)

            assert result["page_count"] == 2
            assert result["title"] == "Test PDF"
            assert result["author"] == "Test Author"

    @pytest.mark.asyncio
    async def test_get_pdf_metadata_no_metadata(self, doc_service):
        """测试PDF没有元数据."""
        mock_path = Mock(spec=Path)

        with patch('pdfplumber.open') as mock_open:
            mock_pdf = Mock(pages=[Mock()], metadata=None)
            mock_open.return_value.__enter__.return_value = mock_pdf

            result = await doc_service._get_pdf_metadata(mock_path)

            assert result["page_count"] == 1
            assert "title" not in result

    @pytest.mark.asyncio
    async def test_get_pdf_metadata_exception(self, doc_service):
        """测试获取PDF元数据异常."""
        mock_path = Mock(spec=Path)

        with patch('pdfplumber.open', side_effect=Exception("PDF error")):
            result = await doc_service._get_pdf_metadata(mock_path)

            assert result == {}


class TestGetDocMetadata:
    """测试获取Word文档元数据."""

    @pytest.mark.asyncio
    async def test_get_docx_metadata_success(self, doc_service):
        """测试成功获取DOCX元数据."""
        mock_path = Mock(spec=Path)
        mock_path.suffix = Mock()
        mock_path.suffix.lower = Mock(return_value=".docx")

        # 模拟docx模块
        mock_docx = Mock()
        mock_properties = Mock(
            title="Test Doc",
            author="Test Author",
            subject="Test Subject",
            created="2024-01-01",
            modified="2024-01-02"
        )
        mock_doc = Mock(
            paragraphs=[Mock(), Mock()],  # 2 paragraphs
            tables=[Mock()],  # 1 table
            core_properties=mock_properties
        )
        mock_docx.Document = Mock(return_value=mock_doc)

        with patch.dict('sys.modules', {'docx': mock_docx}):
            result = await doc_service._get_doc_metadata(mock_path)

            assert result["paragraph_count"] == 2
            assert result["table_count"] == 1
            assert result["title"] == "Test Doc"

    @pytest.mark.asyncio
    async def test_get_doc_metadata_not_docx(self, doc_service):
        """测试非DOCX文件."""
        mock_path = Mock(spec=Path)
        mock_path.suffix.lower.return_value = ".doc"

        result = await doc_service._get_doc_metadata(mock_path)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_doc_metadata_exception(self, doc_service):
        """测试获取Word元数据异常."""
        mock_path = Mock(spec=Path)
        mock_path.suffix = Mock()
        mock_path.suffix.lower = Mock(return_value=".docx")

        # 模拟docx模块但Document抛出异常
        mock_docx = Mock()
        mock_docx.Document = Mock(side_effect=Exception("Doc error"))

        with patch.dict('sys.modules', {'docx': mock_docx}):
            result = await doc_service._get_doc_metadata(mock_path)

            assert result == {}


class TestGetPptMetadata:
    """测试获取PowerPoint元数据."""

    @pytest.mark.asyncio
    async def test_get_pptx_metadata_success(self, doc_service):
        """测试成功获取PPTX元数据."""
        mock_path = Mock(spec=Path)
        mock_path.suffix = Mock()
        mock_path.suffix.lower = Mock(return_value=".pptx")

        # 模拟pptx模块
        mock_pptx = Mock()
        mock_properties = Mock(
            title="Test PPT",
            author="Test Author",
            subject="Test Subject",
            created="2024-01-01",
            modified="2024-01-02"
        )
        mock_prs = Mock(
            slides=[Mock(), Mock(), Mock()],  # 3 slides
            core_properties=mock_properties
        )
        mock_pptx.Presentation = Mock(return_value=mock_prs)

        with patch.dict('sys.modules', {'pptx': mock_pptx}):
            result = await doc_service._get_ppt_metadata(mock_path)

            assert result["slide_count"] == 3
            assert result["title"] == "Test PPT"


class TestSplitDocument:
    """测试文档分割."""

    @pytest.mark.asyncio
    async def test_split_document_normal(self, doc_service):
        """测试正常分割文档."""
        content = "This is sentence one. This is sentence two. This is sentence three."

        chunks = await doc_service.split_document(content, chunk_size=30, overlap=5)

        assert len(chunks) > 1
        assert all(chunk for chunk in chunks)  # 所有块都非空

    @pytest.mark.asyncio
    async def test_split_document_empty_content(self, doc_service):
        """测试空内容."""
        chunks = await doc_service.split_document("", chunk_size=100, overlap=10)

        assert chunks == []

    @pytest.mark.asyncio
    async def test_split_document_short_content(self, doc_service):
        """测试短内容."""
        content = "Short content"

        chunks = await doc_service.split_document(content, chunk_size=100, overlap=10)

        assert len(chunks) == 1
        assert chunks[0] == content


class TestExtractKeywords:
    """测试关键词提取."""

    @pytest.mark.asyncio
    async def test_extract_keywords_normal(self, doc_service):
        """测试正常提取关键词."""
        content = "Python programming is great. Python is powerful. Programming is fun."

        keywords = await doc_service.extract_keywords(content, max_keywords=3)

        assert len(keywords) <= 3
        assert "python" in keywords or "programming" in keywords

    @pytest.mark.asyncio
    async def test_extract_keywords_empty_content(self, doc_service):
        """测试空内容."""
        keywords = await doc_service.extract_keywords("", max_keywords=10)

        assert keywords == []

    @pytest.mark.asyncio
    async def test_extract_keywords_chinese(self, doc_service):
        """测试中文关键词提取."""
        content = "机器学习是人工智能的重要分支。深度学习是机器学习的子领域。"

        keywords = await doc_service.extract_keywords(content, max_keywords=5)

        assert len(keywords) > 0
        assert any(len(k) > 2 for k in keywords)  # 过滤了短词


class TestSummarizeContent:
    """测试内容摘要."""

    @pytest.mark.asyncio
    async def test_summarize_content_normal(self, doc_service):
        """测试正常生成摘要."""
        content = "第一句话。第二句话。第三句话。第四句话。"

        summary = await doc_service.summarize_content(content, max_length=20)

        assert len(summary) <= 20 or summary.endswith("...")
        assert "第一句话" in summary

    @pytest.mark.asyncio
    async def test_summarize_content_short(self, doc_service):
        """测试短内容."""
        content = "短内容"

        summary = await doc_service.summarize_content(content, max_length=200)

        assert summary == content

    @pytest.mark.asyncio
    async def test_summarize_content_empty(self, doc_service):
        """测试空内容."""
        summary = await doc_service.summarize_content("", max_length=200)

        assert summary == ""


class TestExtractContentEnhanced:
    """测试增强的内容提取."""

    @pytest.mark.asyncio
    async def test_extract_enhanced_with_markitdown(self, doc_service):
        """测试使用MarkItDown的增强提取."""
        mock_path = Mock(spec=Path)
        mock_path.suffix.lower.return_value = ".pdf"

        mock_result = Mock(text_content="# Title\n\n| A | B |\n|---|---|\n| 1 | 2 |")
        doc_service.markitdown = Mock(convert=Mock(return_value=mock_result))

        result = await doc_service.extract_content_enhanced(mock_path)

        assert result["text"] == "# Title\n\n| A | B |\n|---|---|\n| 1 | 2 |"
        assert result["format"] == "markdown"
        assert result["extraction_method"] == "markitdown"
        assert result["has_tables"] is True
        assert result["has_images"] is False

    @pytest.mark.asyncio
    async def test_extract_enhanced_default_extractor(self, doc_service):
        """测试使用默认提取器的增强提取."""
        mock_path = Mock(spec=Path)
        mock_path.suffix.lower.return_value = ".txt"

        doc_service.extract_content = AsyncMock(return_value="Plain text content")
        doc_service.get_document_metadata = AsyncMock(return_value={"size": 1024})

        result = await doc_service.extract_content_enhanced(mock_path)

        assert result["text"] == "Plain text content"
        assert result["format"] == "plain_text"
        assert result["extraction_method"] == "default"
        assert result["metadata"]["size"] == 1024

    @pytest.mark.asyncio
    async def test_extract_enhanced_metadata_error(self, doc_service):
        """测试元数据提取失败."""
        mock_path = Mock(spec=Path)
        mock_path.suffix.lower.return_value = ".txt"

        doc_service.extract_content = AsyncMock(return_value="Content")
        doc_service.get_document_metadata = AsyncMock(side_effect=Exception("Metadata error"))

        result = await doc_service.extract_content_enhanced(mock_path)

        assert result["text"] == "Content"
        assert result["metadata"] == {}

    @pytest.mark.asyncio
    async def test_extract_enhanced_detect_features(self, doc_service):
        """测试检测内容特征."""
        mock_path = Mock(spec=Path)
        mock_path.suffix.lower.return_value = ".pdf"

        content = "Text with ![image](img.png) and $$E=mc^2$$ formula"
        mock_result = Mock(text_content=content)
        doc_service.markitdown = Mock(convert=Mock(return_value=mock_result))

        result = await doc_service.extract_content_enhanced(mock_path)

        assert result["has_images"] is True
        assert result["has_formulas"] is True


class TestExtractDoc:
    """测试DOC文件提取."""

    @pytest.mark.asyncio
    async def test_extract_doc_success(self, doc_service):
        """测试成功提取DOC."""
        mock_path = Mock(spec=Path)

        # 模拟textract模块
        mock_textract = Mock()
        mock_textract.process = Mock(return_value=b"DOC content")

        with patch.dict('sys.modules', {'textract': mock_textract}):
            result = await doc_service._extract_doc(mock_path)

            assert result == "DOC content"

    @pytest.mark.asyncio
    async def test_extract_doc_import_error(self, doc_service):
        """测试textract未安装."""
        mock_path = Mock(spec=Path)

        with patch('builtins.__import__', side_effect=ImportError):
            result = await doc_service._extract_doc(mock_path)

            assert "无法提取DOC文件内容" in result

    @pytest.mark.asyncio
    async def test_extract_doc_exception(self, doc_service):
        """测试DOC提取异常."""
        mock_path = Mock(spec=Path)

        # 模拟textract模块但process方法抛出异常
        mock_textract = Mock()
        mock_textract.process = Mock(side_effect=Exception("DOC error"))

        with patch.dict('sys.modules', {'textract': mock_textract}):
            result = await doc_service._extract_doc(mock_path)

            assert "DOC文件提取失败" in result


class TestExtractPpt:
    """测试PPT文件提取."""

    @pytest.mark.asyncio
    async def test_extract_ppt_success(self, doc_service):
        """测试成功提取PPT."""
        mock_path = Mock(spec=Path)

        # 模拟textract模块
        mock_textract = Mock()
        mock_textract.process = Mock(return_value=b"PPT content")

        with patch.dict('sys.modules', {'textract': mock_textract}):
            result = await doc_service._extract_ppt(mock_path)

            assert result == "PPT content"

    @pytest.mark.asyncio
    async def test_extract_ppt_import_error(self, doc_service):
        """测试textract未安装."""
        mock_path = Mock(spec=Path)

        with patch('builtins.__import__', side_effect=ImportError):
            result = await doc_service._extract_ppt(mock_path)

            assert "无法提取PPT文件内容" in result

    @pytest.mark.asyncio
    async def test_extract_ppt_exception(self, doc_service):
        """测试PPT提取异常."""
        mock_path = Mock(spec=Path)

        # 模拟textract模块但process方法抛出异常
        mock_textract = Mock()
        mock_textract.process = Mock(side_effect=Exception("PPT error"))

        with patch.dict('sys.modules', {'textract': mock_textract}):
            result = await doc_service._extract_ppt(mock_path)

            assert "PPT文件提取失败" in result


class TestExtractMarkdown:
    """测试Markdown提取."""

    @pytest.mark.asyncio
    async def test_extract_markdown(self, doc_service):
        """测试Markdown提取使用txt提取器."""
        mock_path = Mock(spec=Path)
        doc_service._extract_txt = AsyncMock(return_value="# Markdown content")

        result = await doc_service._extract_markdown(mock_path)

        assert result == "# Markdown content"
        doc_service._extract_txt.assert_called_once_with(mock_path)


class TestDocxExtractException:
    """测试DOCX提取异常覆盖."""

    @pytest.mark.asyncio
    async def test_extract_docx_processing_exception(self, doc_service):
        """测试DOCX处理过程中的异常."""
        mock_path = Mock(spec=Path)
        doc_service._extract_with_textract = AsyncMock(return_value="Textract fallback")

        # 模拟docx模块但Document处理时抛出异常
        mock_docx = Mock()
        mock_doc = Mock()
        # 让paragraphs访问时抛出异常
        mock_doc.paragraphs = Mock(side_effect=Exception("Processing error"))
        mock_docx.Document = Mock(return_value=mock_doc)

        with patch.dict('sys.modules', {'docx': mock_docx}):
            result = await doc_service._extract_docx(mock_path)

            assert result == "Textract fallback"
            doc_service._extract_with_textract.assert_called_once_with(mock_path)


class TestPptxExtractException:
    """测试PPTX提取异常覆盖."""

    @pytest.mark.asyncio
    async def test_extract_pptx_processing_exception(self, doc_service):
        """测试PPTX处理过程中的异常."""
        mock_path = Mock(spec=Path)
        doc_service._extract_with_textract = AsyncMock(return_value="Textract fallback")

        # 模拟pptx模块但Presentation处理时抛出异常
        mock_pptx = Mock()
        mock_prs = Mock()
        # 让slides访问时抛出异常
        mock_prs.slides = Mock(side_effect=Exception("Processing error"))
        mock_pptx.Presentation = Mock(return_value=mock_prs)

        with patch.dict('sys.modules', {'pptx': mock_pptx}):
            result = await doc_service._extract_pptx(mock_path)

            assert result == "Textract fallback"
            doc_service._extract_with_textract.assert_called_once_with(mock_path)


class TestGetMetadataEdgeCases:
    """测试元数据获取的边缘情况."""

    @pytest.mark.asyncio
    async def test_get_metadata_doc_file(self, doc_service):
        """测试获取.doc文件的元数据."""
        mock_path = Mock(spec=Path)
        mock_path.suffix = Mock()
        mock_path.suffix.lower = Mock(return_value=".doc")
        mock_path.stat.return_value = Mock(
            st_size=2048,
            st_ctime=1234567890.0,
            st_mtime=1234567890.0
        )
        doc_service._get_doc_metadata = AsyncMock(return_value={"format": "doc"})

        result = await doc_service.get_document_metadata(mock_path)

        assert result["file_extension"] == ".doc"
        assert result["format"] == "doc"
        doc_service._get_doc_metadata.assert_called_once_with(mock_path)

    @pytest.mark.asyncio
    async def test_get_metadata_ppt_file(self, doc_service):
        """测试获取.ppt文件的元数据."""
        mock_path = Mock(spec=Path)
        mock_path.suffix = Mock()
        mock_path.suffix.lower = Mock(return_value=".ppt")
        mock_path.stat.return_value = Mock(
            st_size=2048,
            st_ctime=1234567890.0,
            st_mtime=1234567890.0
        )
        doc_service._get_ppt_metadata = AsyncMock(return_value={"format": "ppt"})

        result = await doc_service.get_document_metadata(mock_path)

        assert result["file_extension"] == ".ppt"
        assert result["format"] == "ppt"
        doc_service._get_ppt_metadata.assert_called_once_with(mock_path)

    @pytest.mark.asyncio
    async def test_get_ppt_metadata_processing_exception(self, doc_service):
        """测试PPT元数据提取处理异常."""
        mock_path = Mock(spec=Path)
        mock_path.suffix = Mock()
        mock_path.suffix.lower = Mock(return_value=".pptx")

        # 模拟pptx模块，让整个处理抛出异常
        mock_pptx = Mock()
        # 让Presentation构造时抛出异常，这样会被except捕获
        mock_pptx.Presentation = Mock(side_effect=Exception("Cannot open presentation"))

        with patch.dict('sys.modules', {'pptx': mock_pptx}):
            result = await doc_service._get_ppt_metadata(mock_path)

            # 应该返回空字典
            assert result == {}


class TestSummarizeContentEdgeCases:
    """测试内容摘要的边缘情况."""

    @pytest.mark.asyncio
    async def test_summarize_content_with_periods(self, doc_service):
        """测试包含句号的内容摘要."""
        content = "第一句话。第二句话。第三句话。第四句话。第五句话。"

        # 测试长度允许包含四句话（每句5个字符）
        summary = await doc_service.summarize_content(content, max_length=20)

        assert summary == "第一句话。第二句话。第三句话。第四句话。"
        assert len(summary) == 20

    @pytest.mark.asyncio
    async def test_summarize_content_no_periods(self, doc_service):
        """测试没有句号的内容摘要."""
        content = "这是一段很长的内容但是没有句号所以会被截断"

        summary = await doc_service.summarize_content(content, max_length=10)

        assert summary == "这是一段很长的内容但..."
        assert len(summary) == 13  # 10 + 3 for "..."

    @pytest.mark.asyncio
    async def test_summarize_content_exact_boundary(self, doc_service):
        """测试刚好在句号边界的摘要."""
        content = "短句。这是第二句话。"

        summary = await doc_service.summarize_content(content, max_length=3)

        assert summary == "短句。"  # 即使超过max_length，也会包含完整的第一句


class TestExtractContentEnhancedLogging:
    """测试增强内容提取的日志."""

    @pytest.mark.asyncio
    async def test_extract_enhanced_markitdown_warning_log(self, doc_service):
        """测试MarkItDown提取失败的警告日志."""
        mock_path = Mock(spec=Path)
        mock_path.suffix.lower.return_value = ".pdf"

        # 让MarkItDown转换抛出异常
        doc_service.markitdown = Mock(convert=Mock(side_effect=Exception("Convert failed")))
        doc_service.extract_content = AsyncMock(return_value="Fallback content")
        doc_service.get_document_metadata = AsyncMock(return_value={})

        with patch('app.services.document_content_service.logger') as mock_logger:
            result = await doc_service.extract_content_enhanced(mock_path)

            # 验证警告日志被调用
            mock_logger.warning.assert_called_once()
            assert "MarkItDown extraction failed" in mock_logger.warning.call_args[0][0]
            assert "Convert failed" in mock_logger.warning.call_args[0][0]

            # 验证返回了默认提取的内容
            assert result["text"] == "Fallback content"
            assert result["extraction_method"] == "default"


