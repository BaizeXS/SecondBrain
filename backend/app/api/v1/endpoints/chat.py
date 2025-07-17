"""Chat endpoints v2 - 使用服务层和CRUD层的完整版本."""


from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from app.schemas.conversations import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    ConversationWithMessages,
    MessageCreate,
    MessageResponse,
)
from app.services import ConversationService
from app.services.chat_service import chat_service
from app.services.branch_service import branch_service
from app.schemas.conversation_branch import (
    BranchCreate,
    BranchListResponse,
    BranchSwitch,
    BranchMerge,
    BranchHistory,
)

router = APIRouter()


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
            db=db,
            request=request,
            user=current_user
        )

        # 如果是流式响应，返回StreamingResponse
        if request.stream:
            return StreamingResponse(
                result,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                }
            )
        else:
            return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天服务错误: {str(e)}",
        )


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
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
    conversation = await ConversationService.get_conversation_with_messages(
        db, conversation_id, current_user, message_limit
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在或无权访问",
        )

    return ConversationWithMessages.model_validate(conversation)


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


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: int,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """向对话添加消息."""
    # 检查对话权限
    conversation = await ConversationService.get_conversation_by_id(
        db, conversation_id, current_user
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在或无权访问",
        )

    # 添加消息
    message = await ConversationService.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=message_data.content,
        attachments=message_data.attachments,
    )

    return MessageResponse.model_validate(message)


@router.post("/conversations/{conversation_id}/messages/{message_id}/regenerate", response_model=MessageResponse)
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
        new_content = await chat_service.regenerate_message(
            db=db,
            conversation_id=conversation_id,
            message_id=message_id,
            user=current_user,
            model=model,
            temperature=temperature
        )

        # 获取更新后的消息
        from app.crud.message import crud_message
        message = await crud_message.get(db, id=message_id)

        return MessageResponse.model_validate(message)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新生成失败: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/branches", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建分支失败: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/branches", response_model=BranchListResponse)
async def list_conversation_branches(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BranchListResponse:
    """列出对话的所有分支."""
    try:
        return await branch_service.list_branches(db, conversation_id, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分支列表失败: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/branches/switch", status_code=status.HTTP_204_NO_CONTENT)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换分支失败: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/branches/history", response_model=List[BranchHistory])
async def get_branch_history(
    conversation_id: int,
    message_id: int | None = Query(None, description="从指定消息开始的历史"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[BranchHistory]:
    """获取对话的分支历史树."""
    try:
        return await branch_service.get_branch_history(
            db, conversation_id, message_id, current_user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分支历史失败: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/branches/merge", response_model=List[MessageResponse])
async def merge_conversation_branch(
    conversation_id: int,
    merge_data: BranchMerge,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[MessageResponse]:
    """合并分支."""
    try:
        merged_messages = await branch_service.merge_branch(
            db,
            conversation_id,
            merge_data.source_branch,
            merge_data.target_message_id,
            current_user
        )
        return [MessageResponse.model_validate(msg) for msg in merged_messages]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"合并分支失败: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}/branches/{branch_name}", status_code=status.HTTP_204_NO_CONTENT)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除分支失败: {str(e)}"
        )
