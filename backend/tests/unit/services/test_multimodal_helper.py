"""Unit tests for Multimodal Helper."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.multimodal_helper import MultimodalHelper


@pytest.fixture
def multimodal_helper():
    """创建多模态辅助器实例."""
    return MultimodalHelper()


@pytest.fixture
def mock_ai_service():
    """创建模拟的AI服务."""
    service = Mock()
    service.encode_image = Mock(return_value="data:image/png;base64,test_image_data")
    service.encode_pdf = Mock(return_value="data:application/pdf;base64,test_pdf_data")
    return service


@pytest.fixture
def mock_content_service():
    """创建模拟的文档内容服务."""
    service = Mock()
    service.extract_content_enhanced = AsyncMock()
    return service


class TestStaticMethods:
    """测试静态方法."""

    def test_is_image_file(self, multimodal_helper):
        """测试图片文件检测."""
        assert multimodal_helper.is_image_file("test.jpg") is True
        assert multimodal_helper.is_image_file("test.JPEG") is True
        assert multimodal_helper.is_image_file("test.png") is True
        assert multimodal_helper.is_image_file("test.gif") is True
        assert multimodal_helper.is_image_file("test.webp") is True
        assert multimodal_helper.is_image_file("test.bmp") is True
        assert multimodal_helper.is_image_file("test.pdf") is False
        assert multimodal_helper.is_image_file("test.docx") is False

    def test_is_pdf_file(self, multimodal_helper):
        """测试PDF文件检测."""
        assert multimodal_helper.is_pdf_file("test.pdf") is True
        assert multimodal_helper.is_pdf_file("test.PDF") is True
        assert multimodal_helper.is_pdf_file("test.jpg") is False
        assert multimodal_helper.is_pdf_file("test.docx") is False

    def test_is_document_file(self, multimodal_helper):
        """测试文档文件检测."""
        assert multimodal_helper.is_document_file("test.docx") is True
        assert multimodal_helper.is_document_file("test.doc") is True
        assert multimodal_helper.is_document_file("test.pptx") is True
        assert multimodal_helper.is_document_file("test.ppt") is True
        assert multimodal_helper.is_document_file("test.xlsx") is True
        assert multimodal_helper.is_document_file("test.xls") is True
        assert multimodal_helper.is_document_file("test.pdf") is False
        assert multimodal_helper.is_document_file("test.jpg") is False


class TestPrepareAttachmentForChat:
    """测试准备附件功能."""

    @pytest.mark.asyncio
    async def test_prepare_image_with_vision(self, multimodal_helper, mock_ai_service):
        """测试准备图片附件（使用视觉模型）."""
        multimodal_helper.ai_service = mock_ai_service

        result = await multimodal_helper.prepare_attachment_for_chat(
            Path("/tmp/test.jpg"),
            "test.jpg",
            prefer_vision=True
        )

        assert result["type"] == "image"
        assert result["needs_vision"] is True
        assert result["content"] == "data:image/png;base64,test_image_data"
        assert result["extracted_text"] is None

        mock_ai_service.encode_image.assert_called_once_with(Path("/tmp/test.jpg"))

    @pytest.mark.asyncio
    async def test_prepare_image_without_vision(self, multimodal_helper):
        """测试准备图片附件（不使用视觉模型）."""
        result = await multimodal_helper.prepare_attachment_for_chat(
            Path("/tmp/test.jpg"),
            "test.jpg",
            prefer_vision=False
        )

        assert result["type"] == "image"
        assert result["needs_vision"] is True
        assert result["content"] is None
        assert result["extracted_text"] == "[图片文件: test.jpg]"

    @pytest.mark.asyncio
    async def test_prepare_pdf_with_vision(self, multimodal_helper, mock_ai_service):
        """测试准备PDF附件（使用视觉模型）."""
        multimodal_helper.ai_service = mock_ai_service

        result = await multimodal_helper.prepare_attachment_for_chat(
            Path("/tmp/test.pdf"),
            "test.pdf",
            prefer_vision=True
        )

        assert result["type"] == "pdf"
        assert result["needs_vision"] is True
        assert result["content"] == "data:application/pdf;base64,test_pdf_data"
        assert result["extracted_text"] is None

        mock_ai_service.encode_pdf.assert_called_once_with(Path("/tmp/test.pdf"))

    @pytest.mark.asyncio
    async def test_prepare_pdf_without_vision_success(self, multimodal_helper, mock_content_service):
        """测试准备PDF附件（不使用视觉模型，提取成功）."""
        mock_content_service.extract_content_enhanced.return_value = {
            "text": "Extracted PDF content",
            "extraction_method": "markitdown",
            "has_tables": True,
            "has_formulas": False
        }
        multimodal_helper.content_service = mock_content_service

        result = await multimodal_helper.prepare_attachment_for_chat(
            Path("/tmp/test.pdf"),
            "test.pdf",
            prefer_vision=False
        )

        assert result["type"] == "pdf"
        assert result["needs_vision"] is True
        assert result["content"] is None
        assert result["extracted_text"] == "Extracted PDF content"
        assert result["extraction_metadata"]["method"] == "markitdown"
        assert result["extraction_metadata"]["has_tables"] is True
        assert result["extraction_metadata"]["has_formulas"] is False

    @pytest.mark.asyncio
    async def test_prepare_pdf_without_vision_failure(self, multimodal_helper, mock_content_service):
        """测试准备PDF附件（不使用视觉模型，提取失败）."""
        mock_content_service.extract_content_enhanced.side_effect = Exception("Extraction failed")
        multimodal_helper.content_service = mock_content_service

        result = await multimodal_helper.prepare_attachment_for_chat(
            Path("/tmp/test.pdf"),
            "test.pdf",
            prefer_vision=False
        )

        assert result["type"] == "pdf"
        assert result["needs_vision"] is True
        assert result["content"] is None
        assert result["extracted_text"] == "[PDF文件: test.pdf - 内容提取失败]"

    @pytest.mark.asyncio
    async def test_prepare_document_success(self, multimodal_helper, mock_content_service):
        """测试准备文档附件（提取成功）."""
        mock_content_service.extract_content_enhanced.return_value = {
            "text": "Extracted document content",
            "extraction_method": "python-docx",
            "format": "markdown"
        }
        multimodal_helper.content_service = mock_content_service

        result = await multimodal_helper.prepare_attachment_for_chat(
            Path("/tmp/test.docx"),
            "test.docx",
            prefer_vision=True  # 文档文件不使用视觉模型
        )

        assert result["type"] == "document"
        assert result["needs_vision"] is False
        assert result["content"] is None
        assert result["extracted_text"] == "Extracted document content"
        assert result["extraction_metadata"]["method"] == "python-docx"
        assert result["extraction_metadata"]["format"] == "markdown"

    @pytest.mark.asyncio
    async def test_prepare_document_failure(self, multimodal_helper, mock_content_service):
        """测试准备文档附件（提取失败）."""
        mock_content_service.extract_content_enhanced.side_effect = Exception("Extraction failed")
        multimodal_helper.content_service = mock_content_service

        result = await multimodal_helper.prepare_attachment_for_chat(
            Path("/tmp/test.docx"),
            "test.docx",
            prefer_vision=False
        )

        assert result["type"] == "document"
        assert result["needs_vision"] is False
        assert result["content"] is None
        assert result["extracted_text"] == "[文档文件: test.docx - 内容提取失败]"

    @pytest.mark.asyncio
    async def test_prepare_unknown_file(self, multimodal_helper):
        """测试准备未知类型文件."""
        result = await multimodal_helper.prepare_attachment_for_chat(
            Path("/tmp/test.xyz"),
            "test.xyz",
            prefer_vision=True
        )

        assert result["type"] == "unknown"
        assert result["needs_vision"] is False
        assert result["content"] is None
        assert result["extracted_text"] is None


class TestCreateMultimodalMessage:
    """测试创建多模态消息功能."""

    @pytest.mark.asyncio
    async def test_create_message_with_vision_model(self, multimodal_helper, mock_ai_service):
        """测试使用视觉模型创建消息."""
        multimodal_helper.ai_service = mock_ai_service

        attachments = [
            {"file_path": "/tmp/test.jpg", "filename": "test.jpg"},
            {"file_path": "/tmp/test.pdf", "filename": "test.pdf"}
        ]

        result = await multimodal_helper.create_multimodal_message(
            "Test message",
            attachments,
            use_vision_model=True
        )

        assert result["role"] == "user"
        assert isinstance(result["content"], list)
        assert len(result["content"]) == 3  # 文本 + 图片 + PDF

        # 检查文本部分
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "Test message"

        # 检查图片部分
        assert result["content"][1]["type"] == "image_url"
        assert result["content"][1]["image_url"]["url"] == "data:image/png;base64,test_image_data"

        # 检查PDF部分
        assert result["content"][2]["type"] == "file"
        assert result["content"][2]["file"]["url"] == "data:application/pdf;base64,test_pdf_data"
        assert result["content"][2]["file"]["name"] == "test.pdf"

    @pytest.mark.asyncio
    async def test_create_message_with_vision_model_mixed_content(self, multimodal_helper, mock_ai_service, mock_content_service):
        """测试使用视觉模型创建混合内容消息."""
        multimodal_helper.ai_service = mock_ai_service
        mock_content_service.extract_content_enhanced.return_value = {
            "text": "Document content",
            "extraction_method": "default",
            "format": "plain_text"
        }
        multimodal_helper.content_service = mock_content_service

        attachments = [
            {"file_path": "/tmp/test.jpg", "filename": "test.jpg"},
            {"file_path": "/tmp/test.docx", "filename": "test.docx"}
        ]

        result = await multimodal_helper.create_multimodal_message(
            "Test message",
            attachments,
            use_vision_model=True
        )

        assert result["role"] == "user"
        assert isinstance(result["content"], list)

        # 文档内容应该被附加到文本中
        assert "Document content" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_create_message_without_vision_model(self, multimodal_helper, mock_content_service):
        """测试不使用视觉模型创建消息."""
        mock_content_service.extract_content_enhanced.return_value = {
            "text": "Extracted content",
            "extraction_method": "default",
            "format": "plain_text"
        }
        multimodal_helper.content_service = mock_content_service

        attachments = [
            {"file_path": "/tmp/test.pdf", "filename": "test.pdf"},
            {"file_path": "/tmp/test.docx", "filename": "test.docx"}
        ]

        result = await multimodal_helper.create_multimodal_message(
            "Test message",
            attachments,
            use_vision_model=False
        )

        assert result["role"] == "user"
        assert isinstance(result["content"], str)
        assert "Test message" in result["content"]
        assert "附件内容：" in result["content"]
        assert "Extracted content" in result["content"]

    @pytest.mark.asyncio
    async def test_create_message_without_attachments(self, multimodal_helper):
        """测试创建无附件消息."""
        result = await multimodal_helper.create_multimodal_message(
            "Test message",
            [],
            use_vision_model=True
        )

        assert result["role"] == "user"
        assert isinstance(result["content"], list)
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "Test message"

    @pytest.mark.asyncio
    async def test_create_message_text_mode_with_image(self, multimodal_helper):
        """测试文本模式下处理图片."""
        attachments = [
            {"file_path": "/tmp/test.jpg", "filename": "test.jpg"}
        ]

        result = await multimodal_helper.create_multimodal_message(
            "Test message",
            attachments,
            use_vision_model=False
        )

        assert result["role"] == "user"
        assert isinstance(result["content"], str)
        assert "[图片文件: test.jpg]" in result["content"]


class TestCheckAttachmentsNeedVision:
    """测试检查附件是否需要视觉模型功能."""

    def test_check_attachments_need_vision_with_image(self, multimodal_helper):
        """测试包含图片的附件."""
        attachments = [
            {"filename": "test.jpg"},
            {"filename": "test.docx"}
        ]

        assert multimodal_helper.check_attachments_need_vision(attachments) is True

    def test_check_attachments_need_vision_with_pdf(self, multimodal_helper):
        """测试包含PDF的附件."""
        attachments = [
            {"filename": "test.pdf"},
            {"filename": "test.docx"}
        ]

        assert multimodal_helper.check_attachments_need_vision(attachments) is True

    def test_check_attachments_need_vision_without_visual(self, multimodal_helper):
        """测试不包含需要视觉模型的附件."""
        attachments = [
            {"filename": "test.docx"},
            {"filename": "test.xlsx"}
        ]

        assert multimodal_helper.check_attachments_need_vision(attachments) is False

    def test_check_attachments_need_vision_empty(self, multimodal_helper):
        """测试空附件列表."""
        assert multimodal_helper.check_attachments_need_vision([]) is False

    def test_check_attachments_need_vision_missing_filename(self, multimodal_helper):
        """测试缺少文件名的附件."""
        attachments = [
            {"file_path": "/tmp/test.jpg"},  # 没有filename字段
            {"filename": ""}  # 空文件名
        ]

        assert multimodal_helper.check_attachments_need_vision(attachments) is False
