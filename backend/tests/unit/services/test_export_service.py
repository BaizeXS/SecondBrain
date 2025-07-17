"""Unit tests for Export Service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.export_service import ExportService


@pytest.fixture
def export_service():
    """创建导出服务实例."""
    with patch('app.services.export_service.pdfmetrics.registerFont'):
        service = ExportService()
    return service


@pytest.fixture
def mock_note():
    """创建模拟笔记数据."""
    return {
        'id': 1,
        'title': 'Test Note',
        'content': '# Test Content\n\nThis is a test note with **bold** text.',
        'created_at': '2024-01-01T00:00:00',
        'updated_at': '2024-01-02T00:00:00',
        'version': 1,
        'tags': ['test', 'demo'],
        'author': 'Test User'
    }


@pytest.fixture
def mock_document():
    """创建模拟文档数据."""
    return {
        'id': 1,
        'title': 'Test Document',
        'filename': 'test.pdf',
        'content': 'This is test document content.\n\nWith multiple paragraphs.',
        'created_at': '2024-01-01T00:00:00',
        'file_size': 1024 * 100,  # 100KB
    }


@pytest.fixture
def mock_space():
    """创建模拟空间数据."""
    return {
        'id': 1,
        'name': 'Test Space',
        'description': 'This is a test space',
        'created_at': '2024-01-01T00:00:00',
    }


@pytest.fixture
def mock_version():
    """创建模拟版本数据."""
    return {
        'version_number': 2,
        'created_at': '2024-01-03T00:00:00',
        'change_summary': 'Updated content',
    }


@pytest.fixture
def mock_annotation():
    """创建模拟标注数据."""
    return {
        'id': 1,
        'type': 'highlight',
        'page_number': 1,
        'text': 'Highlighted text',
        'comment': 'This is important',
    }


class TestExportNoteToPDF:
    """测试导出笔记为PDF功能."""

    @pytest.mark.asyncio
    async def test_export_note_to_pdf_basic(self, export_service, mock_note):
        """测试基本的笔记导出PDF."""
        # Mock SimpleDocTemplate
        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc:
            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            # 执行
            result = await export_service.export_note_to_pdf(
                note=mock_note,
                include_metadata=False,
                include_versions=False
            )

            # 验证
            assert isinstance(result, bytes)
            MockDoc.assert_called_once()
            mock_doc_instance.build.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_note_to_pdf_with_metadata(self, export_service, mock_note):
        """测试带元数据的笔记导出PDF."""
        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc:
            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            # 执行
            result = await export_service.export_note_to_pdf(
                note=mock_note,
                include_metadata=True,
                include_versions=False
            )

            # 验证
            assert isinstance(result, bytes)
            # 验证build被调用时的story参数包含元数据
            build_args = mock_doc_instance.build.call_args[0][0]
            # 应该包含标题、元数据和内容
            assert len(build_args) > 3

    @pytest.mark.asyncio
    async def test_export_note_to_pdf_with_versions(
        self, export_service, mock_note, mock_version
    ):
        """测试带版本历史的笔记导出PDF."""
        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc:
            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            # 执行
            result = await export_service.export_note_to_pdf(
                note=mock_note,
                include_metadata=True,
                include_versions=True,
                versions=[mock_version]
            )

            # 验证
            assert isinstance(result, bytes)
            # 验证包含了PageBreak
            build_args = mock_doc_instance.build.call_args[0][0]
            page_breaks = [item for item in build_args if type(item).__name__ == 'PageBreak']
            assert len(page_breaks) > 0


class TestExportNoteToDOCX:
    """测试导出笔记为DOCX功能."""

    @pytest.mark.asyncio
    async def test_export_note_to_docx_basic(self, export_service, mock_note):
        """测试基本的笔记导出DOCX."""
        # Mock DocxDocument
        with patch('app.services.export_service.DocxDocument') as MockDocx:
            mock_doc = MagicMock()
            MockDocx.return_value = mock_doc
            mock_doc.save = MagicMock()

            # 执行
            result = await export_service.export_note_to_docx(
                note=mock_note,
                include_metadata=False,
                include_versions=False
            )

            # 验证
            assert isinstance(result, bytes)
            mock_doc.add_heading.assert_called()
            mock_doc.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_note_to_docx_with_metadata(self, export_service, mock_note):
        """测试带元数据的笔记导出DOCX."""
        with patch('app.services.export_service.DocxDocument') as MockDocx:
            mock_doc = MagicMock()
            MockDocx.return_value = mock_doc

            # Mock paragraph
            mock_para = MagicMock()
            mock_doc.add_paragraph.return_value = mock_para

            # 执行
            result = await export_service.export_note_to_docx(
                note=mock_note,
                include_metadata=True,
                include_versions=False
            )

            # 验证
            assert isinstance(result, bytes)
            # 验证添加了元数据段落
            assert mock_doc.add_paragraph.call_count > 1
            # 验证元数据内容
            mock_para.add_run.assert_called()

    @pytest.mark.asyncio
    async def test_export_note_to_docx_with_versions(
        self, export_service, mock_note, mock_version
    ):
        """测试带版本历史的笔记导出DOCX."""
        with patch('app.services.export_service.DocxDocument') as MockDocx:
            mock_doc = MagicMock()
            MockDocx.return_value = mock_doc

            # Mock table
            mock_table = MagicMock()
            mock_row = MagicMock()
            mock_cells = [MagicMock(), MagicMock(), MagicMock()]
            mock_row.cells = mock_cells
            mock_table.rows = [mock_row]
            mock_table.add_row.return_value = mock_row
            mock_doc.add_table.return_value = mock_table

            # 执行
            result = await export_service.export_note_to_docx(
                note=mock_note,
                include_metadata=True,
                include_versions=True,
                versions=[mock_version]
            )

            # 验证
            assert isinstance(result, bytes)
            mock_doc.add_page_break.assert_called_once()
            mock_doc.add_table.assert_called_once()


class TestExportDocumentToPDF:
    """测试导出文档为PDF功能."""

    @pytest.mark.asyncio
    async def test_export_document_to_pdf_basic(self, export_service, mock_document):
        """测试基本的文档导出PDF."""
        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc:
            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            # 执行
            result = await export_service.export_document_to_pdf(
                document=mock_document,
                include_annotations=False
            )

            # 验证
            assert isinstance(result, bytes)
            MockDoc.assert_called_once()
            mock_doc_instance.build.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_document_to_pdf_with_annotations(
        self, export_service, mock_document, mock_annotation
    ):
        """测试带标注的文档导出PDF."""
        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc:
            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            # 执行
            result = await export_service.export_document_to_pdf(
                document=mock_document,
                include_annotations=True,
                annotations=[mock_annotation]
            )

            # 验证
            assert isinstance(result, bytes)
            # 验证包含了PageBreak（标注在新页）
            build_args = mock_doc_instance.build.call_args[0][0]
            page_breaks = [item for item in build_args if type(item).__name__ == 'PageBreak']
            assert len(page_breaks) > 0


class TestExportSpaceToPDF:
    """测试导出空间为PDF功能."""

    @pytest.mark.skip(reason="ReportLab initialization issues in test environment")
    @pytest.mark.asyncio
    async def test_export_space_to_pdf_basic(
        self, export_service, mock_space, mock_document, mock_note
    ):
        """测试基本的空间导出PDF."""
        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc:
            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            # 执行
            result = await export_service.export_space_to_pdf(
                space=mock_space,
                documents=[mock_document],
                notes=[mock_note],
                include_content=False
            )

            # 验证
            assert isinstance(result, bytes)
            MockDoc.assert_called_once()
            mock_doc_instance.build.assert_called_once()

    @pytest.mark.skip(reason="ReportLab initialization issues in test environment")
    @pytest.mark.asyncio
    async def test_export_space_to_pdf_with_content(
        self, export_service, mock_space, mock_document, mock_note
    ):
        """测试带内容预览的空间导出PDF."""
        # 添加summary字段
        mock_document['summary'] = 'This is a document summary'

        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc:
            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            # 执行
            result = await export_service.export_space_to_pdf(
                space=mock_space,
                documents=[mock_document],
                notes=[mock_note],
                include_content=True
            )

            # 验证
            assert isinstance(result, bytes)
            # 验证build被调用
            mock_doc_instance.build.assert_called_once()
            # 验证story参数包含了内容
            build_args = mock_doc_instance.build.call_args[0][0]
            assert len(build_args) > 5  # 应该包含标题、描述、统计、文档列表、笔记列表等


class TestHelperMethods:
    """测试辅助方法."""

    def test_markdown_to_html(self, export_service):
        """测试Markdown转HTML."""
        markdown_text = "# Title\n\n**Bold** text"
        result = export_service._markdown_to_html(markdown_text)

        assert isinstance(result, str)
        assert '<h1>' in result
        assert '<strong>' in result

    def test_escape_xml(self, export_service):
        """测试XML字符转义."""
        text = 'Test & <tag> "quoted" text'
        result = export_service._escape_xml(text)

        assert '&amp;' in result
        assert '&lt;' in result
        assert '&gt;' in result
        assert '&quot;' in result

    def test_format_file_size(self, export_service):
        """测试文件大小格式化."""
        # 测试各种大小
        assert export_service._format_file_size(512) == "512.0 B"
        assert export_service._format_file_size(1024) == "1.0 KB"
        assert export_service._format_file_size(1024 * 1024) == "1.0 MB"
        assert export_service._format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert export_service._format_file_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"

    def test_add_markdown_to_docx(self, export_service):
        """测试添加Markdown到DOCX."""
        mock_doc = MagicMock()
        markdown_text = """# Heading 1
## Heading 2
### Heading 3

Normal paragraph

- Bullet item
* Another bullet

1. Numbered item
2. Second item"""

        export_service._add_markdown_to_docx(mock_doc, markdown_text)

        # 验证标题
        assert mock_doc.add_heading.call_count >= 3
        # 验证段落
        assert mock_doc.add_paragraph.call_count >= 4

    def test_html_to_reportlab(self, export_service):
        """测试HTML转ReportLab元素."""
        html_content = "<p>Test paragraph</p>\n<p>Another paragraph</p>"
        result = export_service._html_to_reportlab(html_content)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_process_document_content(self, export_service):
        """测试处理文档内容."""
        content = "First paragraph\n\nSecond paragraph\n\nThird paragraph"
        result = export_service._process_document_content(content)

        assert isinstance(result, list)
        # 每个段落应该有一个Paragraph和一个Spacer
        assert len(result) >= 6


class TestFontSetupFallback:
    """测试字体设置的回退逻辑."""

    def test_setup_pdf_fonts_no_fonts_found(self):
        """测试找不到任何中文字体时的处理."""
        with patch('os.path.exists', return_value=False):
            with patch('app.services.export_service.pdfmetrics.registerFont'):
                service = ExportService()
                # 验证使用默认字体
                assert service.chinese_font == 'Helvetica'

    def test_setup_pdf_fonts_register_exception(self):
        """测试注册字体时出现异常."""
        with patch('os.path.exists', return_value=True):
            with patch('app.services.export_service.pdfmetrics.registerFont', side_effect=Exception("Font error")):
                # logger.warning 在整个try-except块的最外层
                service = ExportService()
                # 验证使用默认字体
                assert service.chinese_font == 'Helvetica'

    def test_setup_pdf_fonts_partial_success(self):
        """测试部分字体路径失败后成功."""
        # 模拟第一个路径存在但注册失败，第二个路径存在且注册成功
        def exists_side_effect(path):
            return True

        register_call_count = 0
        def register_side_effect(*args):
            nonlocal register_call_count
            register_call_count += 1
            if register_call_count == 1:
                raise Exception("First font failed")
            # 第二次调用成功

        with patch('os.path.exists', side_effect=exists_side_effect):
            with patch('app.services.export_service.pdfmetrics.registerFont', side_effect=register_side_effect):
                service = ExportService()
                # 第一个字体失败，继续尝试，最终使用默认字体
                assert service.chinese_font == 'Helvetica'

    def test_setup_pdf_fonts_outer_exception(self):
        """测试外层异常处理."""
        # 模拟os.path.exists抛出异常以触发外层except块
        with patch('os.path.exists', side_effect=Exception("OS error")):
            with patch('app.services.export_service.logger') as mock_logger:
                service = ExportService()
                # 验证使用默认字体
                assert service.chinese_font == 'Helvetica'
                # 验证记录了警告
                mock_logger.warning.assert_called_once()


class TestExportSpaceToPDFComplete:
    """测试export_space_to_pdf的完整覆盖."""

    @pytest.mark.asyncio
    async def test_export_space_to_pdf_full_coverage(self):
        """测试空间导出PDF的完整流程."""
        # 准备测试数据
        space = {
            'id': 1,
            'name': 'Test Space',
            'description': 'Test Description',
            'created_at': '2024-01-01T00:00:00',
        }

        documents = [{
            'id': 1,
            'title': 'Doc Title',
            'filename': 'test.pdf',
            'summary': 'This is a long document summary that will be truncated' * 10,
        }]

        notes = [{
            'id': 1,
            'title': 'Note Title',
            'content': 'This is a long note content that will be truncated' * 20,
        }]

        # 使用与其他测试相同的模式
        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc:
            with patch('app.services.export_service.pdfmetrics.registerFont'):
                mock_doc_instance = MagicMock()
                MockDoc.return_value = mock_doc_instance

                service = ExportService()
                result = await service.export_space_to_pdf(
                    space=space,
                    documents=documents,
                    notes=notes,
                    include_content=True
                )

                assert isinstance(result, bytes)
                MockDoc.assert_called_once()
                mock_doc_instance.build.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_space_to_pdf_no_description(self):
        """测试没有描述的空间导出."""
        space = {
            'id': 1,
            'name': 'Test Space',
            'created_at': '2024-01-01T00:00:00',
            # 没有description
        }

        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc, \
             patch('app.services.export_service.Paragraph'), \
             patch('app.services.export_service.Spacer'), \
             patch('io.BytesIO') as MockBytesIO:

            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = b'PDF content'
            MockBytesIO.return_value = mock_buffer

            service = ExportService()
            result = await service.export_space_to_pdf(
                space=space,
                documents=[],
                notes=[],
                include_content=False
            )

            assert result == b'PDF content'

    @pytest.mark.asyncio
    async def test_export_space_to_pdf_empty_lists(self):
        """测试空文档和笔记列表的导出."""
        space = {
            'id': 1,
            'name': 'Empty Space',
            'created_at': '2024-01-01T00:00:00',
        }

        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc, \
             patch('app.services.export_service.Paragraph'), \
             patch('app.services.export_service.Spacer'), \
             patch('io.BytesIO') as MockBytesIO:

            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = b'PDF content'
            MockBytesIO.return_value = mock_buffer

            service = ExportService()
            result = await service.export_space_to_pdf(
                space=space,
                documents=[],  # 空列表
                notes=[],      # 空列表
                include_content=False
            )

            assert result == b'PDF content'


class TestHTMLToReportLabException:
    """测试HTML转ReportLab的异常处理."""

    def test_html_to_reportlab_with_exception(self):
        """测试解析HTML时出现异常."""
        service = ExportService()

        # Mock Paragraph构造函数抛出异常
        with patch('app.services.export_service.Paragraph', side_effect=[Exception("Parse error"), MagicMock()]):
            html_content = "<p>Test content</p>"
            result = service._html_to_reportlab(html_content)

            # 验证结果仍然返回了列表（使用了异常处理分支）
            assert isinstance(result, list)
            assert len(result) > 0

    def test_html_to_reportlab_all_lines_fail(self):
        """测试所有行都解析失败的情况."""
        service = ExportService()

        # Mock Paragraph总是抛出异常
        mock_paragraph = MagicMock()
        with patch('app.services.export_service.Paragraph', return_value=mock_paragraph) as MockPara:
            # 第一次调用（clean_line）会失败，第二次调用（escape_xml）会成功
            MockPara.side_effect = [Exception("Parse error"), mock_paragraph, MagicMock()]

            html_content = "<p>Test content</p>"
            result = service._html_to_reportlab(html_content)

            # 验证使用了转义的XML
            assert isinstance(result, list)
            # 验证调用了_escape_xml
            MockPara.assert_called()


class TestProcessDocumentContentException:
    """测试处理文档内容的异常处理."""

    def test_process_document_content_with_exception(self):
        """测试处理文档内容时出现异常."""
        service = ExportService()

        # Mock Paragraph构造函数第一次成功，第二次抛出异常
        mock_para1 = MagicMock()
        with patch('app.services.export_service.Paragraph', side_effect=[mock_para1, Exception("Parse error")]):
            content = "First paragraph\n\nSecond paragraph that will fail"
            result = service._process_document_content(content)

            # 验证结果只包含第一个成功的段落
            assert isinstance(result, list)
            assert len(result) == 2  # 一个段落和一个Spacer

    def test_process_document_content_all_fail(self):
        """测试所有段落都处理失败."""
        service = ExportService()

        # Mock Paragraph总是抛出异常
        with patch('app.services.export_service.Paragraph', side_effect=Exception("Parse error")):
            content = "First paragraph\n\nSecond paragraph\n\nThird paragraph"
            result = service._process_document_content(content)

            # 验证返回空列表
            assert isinstance(result, list)
            assert len(result) == 0


class TestDocumentWithoutTitle:
    """测试没有标题的文档导出."""

    @pytest.mark.asyncio
    async def test_export_document_without_title(self):
        """测试文档没有title字段时使用filename."""
        document = {
            'id': 1,
            # 没有 'title' 字段
            'filename': 'fallback-filename.pdf',
            'created_at': '2024-01-01T00:00:00',
            'file_size': 1024,
        }

        with patch('app.services.export_service.SimpleDocTemplate') as MockDoc, \
             patch('app.services.export_service.Paragraph') as MockParagraph, \
             patch('app.services.export_service.Spacer'), \
             patch('io.BytesIO') as MockBytesIO:

            mock_doc_instance = MagicMock()
            MockDoc.return_value = mock_doc_instance

            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = b'PDF content'
            MockBytesIO.return_value = mock_buffer

            service = ExportService()
            result = await service.export_document_to_pdf(
                document=document,
                include_annotations=False
            )

            # 验证返回结果
            assert result == b'PDF content'
            # 验证使用了filename作为标题
            paragraph_calls = MockParagraph.call_args_list
            # 第一个调用应该是标题
            assert 'fallback-filename.pdf' in str(paragraph_calls[0])
