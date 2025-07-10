"""Chat endpoints v2 - 使用服务层和CRUD层的完整版本."""


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
from app.services import AIService, ConversationService

router = APIRouter()


@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ChatCompletionResponse:
    """创建聊天完成（兼容 OpenAI API）."""
    try:
        # 如果提供了conversation_id，获取对话历史
        messages = request.messages
        if request.conversation_id:
            conversation = await ConversationService.get_conversation_by_id(
                db, request.conversation_id, current_user
            )
            if conversation:
                # 获取历史消息
                history = await ConversationService.get_conversation_messages(
                    db, request.conversation_id, limit=50
                )
                # 将历史消息转换为格式
                history_messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in history
                ]
                # 合并历史消息和新消息
                messages = history_messages + messages

        # 调用AI服务
        ai_service = AIService()

        if request.stream:
            # 流式响应
            async def generate():
                async for chunk in ai_service.chat_stream(
                    messages=messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    user=current_user,
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
            )
        else:
            # 非流式响应
            response = await ai_service.chat(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                user=current_user,
            )

            # 如果有conversation_id，保存消息
            if request.conversation_id and conversation:
                # 保存用户消息
                user_message = request.messages[-1]
                await ConversationService.add_message(
                    db,
                    conversation_id=request.conversation_id,
                    role=user_message["role"],
                    content=user_message["content"],
                )

                # 保存AI响应
                await ConversationService.add_message(
                    db,
                    conversation_id=request.conversation_id,
                    role="assistant",
                    content=response,
                    model=request.model,
                    provider="openai",  # 或从AI服务获取
                )

            return ChatCompletionResponse(
                choices=[{
                    "index": 0,
                    "message": {"role": "assistant", "content": response},
                    "finish_reason": "stop",
                }],
                model=request.model,
                usage={
                    "prompt_tokens": len(str(messages)),
                    "completion_tokens": len(response),
                    "total_tokens": len(str(messages)) + len(response),
                },
            )

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
        space = await crud.space.get(db, id=conversation_data.space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="空间不存在",
            )

        # 检查访问权限
        if space.user_id != current_user.id and not space.is_public:
            access = await crud.space.get_user_access(
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
        space = await crud.space.get(db, id=space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="空间不存在",
            )

        if space.user_id != current_user.id and not space.is_public:
            access = await crud.space.get_user_access(
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
