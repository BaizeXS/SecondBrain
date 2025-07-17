"""Multimodal helper functions for handling attachments in chat."""

import logging
from pathlib import Path
from typing import Any

from app.services.ai_service import AIService
from app.services.document_content_service import DocumentContentService

logger = logging.getLogger(__name__)


class MultimodalHelper:
    """辅助处理多模态内容的工具类."""

    def __init__(self) -> None:
        self.ai_service = AIService()
        self.content_service = DocumentContentService()

    @staticmethod
    def is_image_file(filename: str) -> bool:
        """检查文件是否为图片."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        return Path(filename).suffix.lower() in image_extensions

    @staticmethod
    def is_pdf_file(filename: str) -> bool:
        """检查文件是否为PDF."""
        return Path(filename).suffix.lower() == '.pdf'

    @staticmethod
    def is_document_file(filename: str) -> bool:
        """检查文件是否为文档（Word, PPT等）."""
        doc_extensions = {'.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls'}
        return Path(filename).suffix.lower() in doc_extensions

    async def prepare_attachment_for_chat(
        self,
        file_path: Path,
        filename: str,
        prefer_vision: bool = True
    ) -> dict[str, Any]:
        """准备附件用于聊天.

        Args:
            file_path: 文件路径
            filename: 文件名
            prefer_vision: 是否优先使用视觉模型

        Returns:
            包含附件信息的字典
        """
        result: dict[str, Any] = {
            "type": "unknown",
            "content": None,
            "needs_vision": False,
            "extracted_text": None,
        }

        if self.is_image_file(filename):
            # 图片文件
            result["type"] = "image"
            result["needs_vision"] = True

            if prefer_vision:
                # 编码为base64用于视觉模型
                result["content"] = self.ai_service.encode_image(file_path)
            else:
                # 仅标记存在图片
                result["extracted_text"] = f"[图片文件: {filename}]"

        elif self.is_pdf_file(filename):
            # PDF文件
            result["type"] = "pdf"
            result["needs_vision"] = True

            if prefer_vision:
                # 编码为base64用于视觉模型
                result["content"] = self.ai_service.encode_pdf(file_path)
            else:
                # 提取文本内容
                try:
                    extraction = await self.content_service.extract_content_enhanced(file_path)
                    result["extracted_text"] = extraction["text"]
                    result["extraction_metadata"] = {
                        "method": extraction["extraction_method"],
                        "has_tables": extraction["has_tables"],
                        "has_formulas": extraction["has_formulas"],
                    }
                except Exception as e:
                    logger.error(f"Failed to extract PDF content: {e}")
                    result["extracted_text"] = f"[PDF文件: {filename} - 内容提取失败]"

        elif self.is_document_file(filename):
            # 其他文档文件
            result["type"] = "document"
            result["needs_vision"] = False

            # 总是提取文本内容
            try:
                extraction = await self.content_service.extract_content_enhanced(file_path)
                result["extracted_text"] = extraction["text"]
                result["extraction_metadata"] = {
                    "method": extraction["extraction_method"],
                    "format": extraction["format"],
                }
            except Exception as e:
                logger.error(f"Failed to extract document content: {e}")
                result["extracted_text"] = f"[文档文件: {filename} - 内容提取失败]"

        return result

    async def create_multimodal_message(
        self,
        text: str,
        attachments: list[dict[str, Any]],
        use_vision_model: bool = True
    ) -> dict[str, Any]:
        """创建多模态消息.

        Args:
            text: 文本内容
            attachments: 附件列表，每个附件包含 file_path 和 filename
            use_vision_model: 是否使用视觉模型

        Returns:
            格式化的消息
        """
        if use_vision_model:
            # 使用视觉模型的消息格式
            content_parts: list[dict[str, Any]] = [{"type": "text", "text": text}]

            for attachment in attachments:
                file_path = Path(attachment["file_path"])
                filename = attachment["filename"]

                prepared = await self.prepare_attachment_for_chat(
                    file_path, filename, prefer_vision=True
                )

                if prepared["type"] == "image" and prepared["content"]:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": prepared["content"]}  # type: ignore[dict-item]
                    })
                elif prepared["type"] == "pdf" and prepared["content"]:
                    content_parts.append({
                        "type": "file",
                        "file": {  # type: ignore[dict-item]
                            "url": prepared["content"],
                            "name": filename
                        }
                    })
                elif prepared["extracted_text"]:
                    # 如果无法使用视觉格式，添加提取的文本
                    text += f"\n\n{prepared['extracted_text']}"

            # 更新第一个文本部分
            if content_parts:
                content_parts[0]["text"] = text

            return {
                "role": "user",
                "content": content_parts
            }
        else:
            # 纯文本模式，提取所有附件内容
            extracted_texts = []

            for attachment in attachments:
                file_path = Path(attachment["file_path"])
                filename = attachment["filename"]

                prepared = await self.prepare_attachment_for_chat(
                    file_path, filename, prefer_vision=False
                )

                if prepared["extracted_text"]:
                    extracted_texts.append(prepared["extracted_text"])

            # 组合所有文本
            full_text = text
            if extracted_texts:
                full_text += "\n\n附件内容：\n" + "\n\n".join(extracted_texts)

            return {
                "role": "user",
                "content": full_text
            }

    def check_attachments_need_vision(self, attachments: list[dict[str, Any]]) -> bool:
        """检查附件是否需要视觉模型.

        Args:
            attachments: 附件列表

        Returns:
            是否需要视觉模型
        """
        for attachment in attachments:
            filename = attachment.get("filename", "")
            if self.is_image_file(filename) or self.is_pdf_file(filename):
                return True
        return False


# 创建全局实例
multimodal_helper = MultimodalHelper()
