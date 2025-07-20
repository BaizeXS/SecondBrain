"""Chat endpoints v2 - 完整整合版本，支持文本和多模态聊天."""

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.models import Conversation, User
from app.models.models import Message as DBMessage
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
    Role,
)
from app.schemas.conversation_branch import (
    BranchCreate,
    BranchHistory,
    BranchListResponse,
    BranchMerge,
    BranchSwitch,
)
from app.schemas.conversations import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    ConversationWithMessages,
    MessageCreateSimple,
    MessageResponse,
)
from app.services import ConversationService, multimodal_helper
from app.services.branch_service import branch_service
from app.services.chat_service import chat_service

router = APIRouter()


# ===== OpenAI 兼容接口 =====


@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ChatCompletionResponse | StreamingResponse:
    """创建聊天完成（兼容 OpenAI API），支持文档上下文."""
    try:
        # 使用增强的聊天服务处理请求
        result = await chat_service.create_completion_with_documents(
            db=db, request=request, user=current_user
        )

        # 如果是流式响应，返回StreamingResponse
        if request.stream:
            return StreamingResponse(
                result,  # type: ignore[arg-type]
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            return result  # type: ignore[return-value]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天服务错误: {str(e)}",
        ) from e


# ===== 对话管理 =====


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConversationResponse:
    """创建新对话."""
    # 如果指定了space_id，检查权限
    if conversation_data.space_id:
        space = await crud.crud_space.get(db, id=conversation_data.space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="空间不存在",
            )

        # 检查访问权限
        if space.user_id != current_user.id and not space.is_public:
            access = await crud.crud_space.get_user_access(
                db, space_id=conversation_data.space_id, user_id=current_user.id
            )
            if not access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权在此空间创建对话",
                )

    # 创建对话
    conversation = await ConversationService.create_conversation(
        db, conversation_data, current_user
    )

    return ConversationResponse.model_validate(conversation)


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    space_id: int | None = Query(None, description="空间ID"),
    mode: str | None = Query(None, description="对话模式"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConversationListResponse:
    """获取对话列表."""
    # 检查空间权限
    if space_id:
        space = await crud.crud_space.get(db, id=space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="空间不存在",
            )

        if space.user_id != current_user.id and not space.is_public:
            access = await crud.crud_space.get_user_access(
                db, space_id=space_id, user_id=current_user.id
            )
            if not access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此空间的对话",
                )

    # 获取对话列表
    conversations = await ConversationService.get_user_conversations(
        db,
        user=current_user,
        space_id=space_id,
        mode=mode,
        skip=skip,
        limit=limit,
    )

    # 获取总数
    # 对于毕业设计项目，简单返回当前页的数量
    # 实际项目中应该使用单独的 COUNT 查询
    total = len(conversations)

    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        has_next=total > skip + limit,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    message_limit: int = Query(50, ge=1, le=200, description="返回的消息数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConversationWithMessages:
    """获取对话详情及消息."""
    result = await ConversationService.get_conversation_with_messages(
        db, conversation_id, current_user, message_limit
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在或无权访问",
        )

    conversation, messages = result
    # 构建响应对象
    response_data = {
        "id": conversation.id,
        "title": conversation.title,
        "mode": conversation.mode,
        "model": conversation.model,
        "space_id": conversation.space_id,
        "prompt_template": conversation.system_prompt,
        "is_pinned": False,  # 默认值，因为模型中没有此字段
        "is_archived": False,  # 默认值，因为模型中没有此字段
        "message_count": conversation.message_count,
        "token_count": conversation.total_tokens,
        "tags": None,  # 默认值，因为模型中没有此字段
        "meta_data": conversation.meta_data,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": messages,
    }

    return ConversationWithMessages.model_validate(response_data)


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConversationResponse:
    """更新对话信息."""
    # 获取对话
    conversation = await ConversationService.get_conversation_by_id(
        db, conversation_id, current_user
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在或无权访问",
        )

    # 更新对话
    updated_conversation = await ConversationService.update_conversation(
        db, conversation, conversation_data
    )

    return ConversationResponse.model_validate(updated_conversation)


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除对话."""
    # 获取对话
    conversation = await ConversationService.get_conversation_by_id(
        db, conversation_id, current_user
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在或无权访问",
        )

    # 删除对话
    await ConversationService.delete_conversation(db, conversation)


# ===== 统一的消息发送接口 =====


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: int,
    request: Request,
    # 支持JSON输入
    message_data: MessageCreateSimple | None = Body(None),
    # 支持Form输入（用于文件上传）
    content: str | None = Form(None),
    attachments: list[UploadFile] | None = File(None),
    model: str | None = Form(None),
    auto_switch_vision: bool = Form(True),
    # 通用参数
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """统一的消息发送接口，支持文本和多模态输入."""

    # 检查对话权限
    conversation = await ConversationService.get_conversation_by_id(
        db, conversation_id, current_user
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在或无权访问",
        )

    # 智能识别输入类型
    content_type = request.headers.get("content-type", "")

    processed_attachments = None
    message_content = None

    if "multipart/form-data" in content_type:
        # Form数据，可能包含文件
        message_content = content

        if attachments:
            # 处理多模态附件
            processed_attachments = await _process_attachments(
                attachments, current_user, auto_switch_vision, model
            )
    else:
        # JSON数据
        if message_data:
            message_content = message_data.content
            processed_attachments = message_data.attachments

    if not message_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="消息内容不能为空"
        )

    # 创建用户消息
    user_message = await ConversationService.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=message_content,
        attachments=processed_attachments,
    )

    # 生成AI响应
    ai_response = await _generate_ai_response(
        db=db,
        conversation=conversation,
        user_message=user_message,
        current_user=current_user,
        model=model,
        attachments=processed_attachments,
    )

    return MessageResponse.model_validate(ai_response)


# ===== 附件分析端点 =====


@router.post("/analyze-attachments")
async def analyze_attachments(
    attachments: list[UploadFile] = File(..., description="要分析的附件"),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """分析附件，返回是否需要视觉模型等信息."""

    results = []
    needs_vision = False

    for file in attachments:
        # 临时保存文件
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename or "")[1]
        ) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 准备附件信息
        prepared = await multimodal_helper.prepare_attachment_for_chat(
            file_path=Path(tmp_path),
            filename=file.filename or "unknown",
            prefer_vision=False,  # 获取所有可能的信息
        )

        results.append(
            {
                "filename": file.filename,
                "type": prepared["type"],
                "needs_vision": prepared["needs_vision"],
                "has_text": bool(prepared.get("extracted_text")),
                "extraction_metadata": prepared.get("extraction_metadata", {}),
            }
        )

        if prepared["needs_vision"]:
            needs_vision = True

        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # 忽略清理失败

    # 推荐的模型
    from app.services import ai_service

    recommended_models = []
    if needs_vision:
        if current_user.is_premium:
            recommended_models = ai_service.VISION_MODELS.get("premium", [])[:3]
        else:
            recommended_models = ai_service.VISION_MODELS.get("free", [])
    else:
        if current_user.is_premium:
            recommended_models = ai_service.CHAT_MODELS.get("premium", [])[:3]
        else:
            recommended_models = ai_service.CHAT_MODELS.get("free", [])[:3]

    return {
        "attachments": results,
        "needs_vision_model": needs_vision,
        "recommended_models": recommended_models,
        "auto_switch_available": True,
    }


# ===== 消息重新生成 =====


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/regenerate",
    response_model=MessageResponse,
)
async def regenerate_message(
    conversation_id: int,
    message_id: int,
    model: str | None = Query(None, description="使用的模型"),
    temperature: float | None = Query(None, ge=0, le=2, description="温度参数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """重新生成消息."""
    try:
        # 调用服务重新生成
        await chat_service.regenerate_message(
            db=db,
            conversation_id=conversation_id,
            message_id=message_id,
            user=current_user,
            model=model,
            temperature=temperature,
        )

        # 获取更新后的消息
        from app.crud.message import crud_message

        message = await crud_message.get(db, id=message_id)

        return MessageResponse.model_validate(message)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新生成失败: {str(e)}",
        ) from e


# ===== 分支管理 =====


@router.post(
    "/conversations/{conversation_id}/branches",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation_branch(
    conversation_id: int,
    branch_data: BranchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """在对话中创建新分支."""
    try:
        branch_message = await branch_service.create_branch(
            db, conversation_id, branch_data, current_user
        )
        return MessageResponse.model_validate(branch_message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建分支失败: {str(e)}",
        ) from e


@router.get(
    "/conversations/{conversation_id}/branches", response_model=BranchListResponse
)
async def list_conversation_branches(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BranchListResponse:
    """列出对话的所有分支."""
    try:
        return await branch_service.list_branches(db, conversation_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分支列表失败: {str(e)}",
        ) from e


@router.post(
    "/conversations/{conversation_id}/branches/switch",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def switch_conversation_branch(
    conversation_id: int,
    switch_data: BranchSwitch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """切换到指定分支."""
    try:
        await branch_service.switch_branch(
            db, conversation_id, switch_data.branch_name, current_user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换分支失败: {str(e)}",
        ) from e


@router.get(
    "/conversations/{conversation_id}/branches/history",
    response_model=list[BranchHistory],
)
async def get_branch_history(
    conversation_id: int,
    message_id: int | None = Query(None, description="从指定消息开始的历史"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[BranchHistory]:
    """获取对话的分支历史树."""
    try:
        return await branch_service.get_branch_history(
            db, conversation_id, message_id, current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分支历史失败: {str(e)}",
        ) from e


@router.post(
    "/conversations/{conversation_id}/branches/merge",
    response_model=list[MessageResponse],
)
async def merge_conversation_branch(
    conversation_id: int,
    merge_data: BranchMerge,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[MessageResponse]:
    """合并分支."""
    try:
        merged_messages = await branch_service.merge_branch(
            db,
            conversation_id,
            merge_data.source_branch,
            merge_data.target_message_id,
            current_user,
        )
        return [MessageResponse.model_validate(msg) for msg in merged_messages]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"合并分支失败: {str(e)}",
        ) from e


@router.delete(
    "/conversations/{conversation_id}/branches/{branch_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation_branch(
    conversation_id: int,
    branch_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除分支."""
    try:
        await branch_service.delete_branch(
            db, conversation_id, branch_name, current_user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除分支失败: {str(e)}",
        ) from e


# ===== 辅助函数 =====


async def _process_attachments(
    files: list[UploadFile], user: User, auto_switch_vision: bool, model: str | None
) -> list[dict[str, Any]]:
    """处理上传的附件."""
    # 文件大小和数量限制
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILES = 5

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"最多只能上传{MAX_FILES}个文件",
        )

    processed = []

    for file in files:
        # 检查文件大小
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件 {file.filename} 太大，最大允许 {MAX_FILE_SIZE // 1024 // 1024}MB",
            )

        # 保存文件到临时位置（实际应该使用MinIO等存储服务）
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename or "")[1]
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # 准备附件信息
        attachment_info = await multimodal_helper.prepare_attachment_for_chat(
            file_path=Path(tmp_path),
            filename=file.filename or "unknown",
            prefer_vision=auto_switch_vision,
        )

        processed.append(
            {
                "filename": file.filename,
                "type": attachment_info["type"],
                "url": attachment_info.get("url"),  # 实际应该是MinIO URL
                "extracted_text": attachment_info.get("extracted_text"),
                "metadata": attachment_info.get("extraction_metadata", {}),
            }
        )

        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # 忽略清理失败

    return processed


async def _generate_ai_response(
    db: AsyncSession,
    conversation: Conversation,
    user_message: DBMessage,
    current_user: User,
    model: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> DBMessage:
    """生成AI响应."""
    # 获取对话历史
    messages = await ConversationService.get_conversation_messages(
        db, conversation.id, limit=10
    )

    # 构建消息列表
    chat_messages = []
    for msg in reversed(messages):
        chat_messages.append(
            {"role": msg.role, "content": msg.content, "attachments": msg.attachments}
        )

    # 创建聊天请求
    completion_request = ChatCompletionRequest(
        model=model or "gpt-3.5-turbo",  # 提供默认模型
        messages=[
            Message(
                role=Role(msg["role"]),
                content=str(msg.get("content") or ""),  # 确保 content 是字符串
            )
            for msg in chat_messages
        ],
        conversation_id=conversation.id,
        space_id=conversation.space_id,
        mode=conversation.mode or "chat",
        stream=False,  # 消息接口不支持流式
        document_ids=[],
        temperature=0.7,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=None,
        n=1,
        user=None,
        tools=None,
        tool_choice=None,
    )

    # 调用聊天服务
    response = await chat_service.create_completion_with_documents(
        db=db, request=completion_request, user=current_user
    )

    # 保存AI响应
    # response 是 ChatCompletionResponse 类型，因为 stream=False
    if isinstance(response, ChatCompletionResponse):
        ai_message = await ConversationService.add_message(
            db,
            conversation_id=conversation.id,
            role="assistant",
            content=response.choices[0].message.content,
            model=response.model,
            meta_data={
                "usage": response.usage.model_dump() if response.usage else None,
                "finish_reason": response.choices[0].finish_reason,
            },
        )
        return ai_message
    else:
        # 不应该发生，因为 stream=False
        raise ValueError("非预期的响应类型")
