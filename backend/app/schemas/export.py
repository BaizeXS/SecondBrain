"""Export schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """导出格式枚举."""

    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


class NoteExportRequest(BaseModel):
    """笔记导出请求."""

    note_ids: list[int] = Field(..., description="要导出的笔记ID列表")
    format: str = Field(ExportFormat.PDF, description="导出格式")
    include_metadata: bool = Field(True, description="是否包含元数据")
    include_versions: bool = Field(False, description="是否包含版本历史")
    include_linked_notes: bool = Field(False, description="是否包含关联笔记")
    merge_into_one: bool = Field(False, description="是否合并为一个文件")


class DocumentExportRequest(BaseModel):
    """文档导出请求."""

    document_ids: list[int] = Field(..., description="要导出的文档ID列表")
    format: str = Field(ExportFormat.PDF, description="导出格式")
    include_annotations: bool = Field(True, description="是否包含标注")
    include_citations: bool = Field(False, description="是否包含引用")
    merge_into_one: bool = Field(False, description="是否合并为一个文件")


class SpaceExportRequest(BaseModel):
    """空间导出请求."""

    space_id: int = Field(..., description="要导出的空间ID")
    format: str = Field(ExportFormat.PDF, description="导出格式")
    include_documents: bool = Field(True, description="是否包含文档")
    include_notes: bool = Field(True, description="是否包含笔记")
    include_content: bool = Field(False, description="是否包含内容（否则只导出列表）")
    include_citations: bool = Field(False, description="是否包含引用")


class ConversationExportRequest(BaseModel):
    """对话导出请求."""

    conversation_ids: list[int] = Field(..., description="要导出的对话ID列表")
    format: str = Field(ExportFormat.PDF, description="导出格式")
    include_metadata: bool = Field(True, description="是否包含元数据")
    include_branches: bool = Field(False, description="是否包含分支")
    merge_into_one: bool = Field(False, description="是否合并为一个文件")
    date_from: str | None = Field(None, description="起始日期")
    date_to: str | None = Field(None, description="结束日期")


class ExportResponse(BaseModel):
    """导出响应."""

    filename: str = Field(..., description="导出的文件名")
    format: str = Field(..., description="导出格式")
    size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="内容类型")
    download_url: str | None = Field(None, description="下载URL（如果保存到服务器）")


class BatchExportStatus(BaseModel):
    """批量导出状态."""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态: pending/processing/completed/failed")
    progress: int = Field(0, ge=0, le=100, description="进度百分比")
    total_items: int = Field(..., description="总项目数")
    completed_items: int = Field(0, description="已完成项目数")
    error_message: str | None = Field(None, description="错误信息")
    result_url: str | None = Field(None, description="结果下载URL")
