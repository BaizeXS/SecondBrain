"""Enhanced chat endpoint with multimodal support."""

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.chat import ChatRequest, ChatResponse, StreamChatRequest
from app.services import ai_service, multimodal_helper

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat-with-attachments", response_model=ChatResponse)
async def chat_with_attachments(
    message: str = Form(..., description="用户消息"),
    mode: str = Form("chat", description="聊天模式: chat/search"),
    model: str | None = Form(None, description="指定模型"),
    attachments: list[UploadFile] = File(None, description="附件列表"),
    auto_switch_vision: bool = Form(True, description="自动切换到视觉模型"),
    current_user: User = Depends(get_current_active_user),
) -> ChatResponse:
    """带附件的聊天接口，支持图片、PDF和文档."""
    
    try:
        # 准备消息
        prepared_attachments = []
        needs_vision = False
        
        if attachments:
            # 检查是否需要视觉模型
            attachment_infos = [
                {"filename": file.filename} for file in attachments
            ]
            needs_vision = multimodal_helper.check_attachments_need_vision(attachment_infos)
            
            # 保存并准备附件
            for file in attachments:
                # 这里简化处理，实际应该保存到存储服务
                content = await file.read()
                file_path = Path(f"/tmp/{file.filename}")
                
                with open(file_path, "wb") as f:
                    f.write(content)
                
                prepared_attachments.append({
                    "file_path": str(file_path),
                    "filename": file.filename
                })
        
        # 决定是否使用视觉模型
        use_vision = needs_vision and (auto_switch_vision or (model and ai_service._is_vision_model(model)))
        
        # 创建多模态消息
        user_message = await multimodal_helper.create_multimodal_message(
            text=message,
            attachments=prepared_attachments,
            use_vision_model=use_vision
        )
        
        # 调用AI服务
        messages = [user_message]
        
        # 根据模式选择
        from app.services.ai_service import ChatMode
        chat_mode = ChatMode.SEARCH if mode == "search" else ChatMode.CHAT
        
        response = await ai_service.chat(
            messages=messages,
            mode=chat_mode,
            model=model,
            user=current_user,
            auto_switch_vision=auto_switch_vision
        )
        
        # 清理临时文件
        for attachment in prepared_attachments:
            try:
                Path(attachment["file_path"]).unlink()
            except Exception:
                pass
        
        return ChatResponse(
            message=response,
            mode=mode,
            model=model or "auto",
            has_attachments=bool(attachments),
            attachment_count=len(attachments) if attachments else 0
        )
        
    except Exception as e:
        logger.error(f"Chat with attachments failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天失败: {str(e)}"
        )


@router.post("/analyze-attachments")
async def analyze_attachments(
    attachments: list[UploadFile] = File(..., description="要分析的附件"),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """分析附件，返回是否需要视觉模型等信息."""
    
    results = []
    needs_vision = False
    
    for file in attachments:
        # 保存文件（简化处理）
        content = await file.read()
        file_path = Path(f"/tmp/{file.filename}")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 准备附件信息
        prepared = await multimodal_helper.prepare_attachment_for_chat(
            file_path=file_path,
            filename=file.filename,
            prefer_vision=False  # 获取所有可能的信息
        )
        
        results.append({
            "filename": file.filename,
            "type": prepared["type"],
            "needs_vision": prepared["needs_vision"],
            "has_text": bool(prepared["extracted_text"]),
            "extraction_metadata": prepared.get("extraction_metadata", {})
        })
        
        if prepared["needs_vision"]:
            needs_vision = True
        
        # 清理临时文件
        try:
            file_path.unlink()
        except Exception:
            pass
    
    # 推荐的模型
    recommended_models = []
    if needs_vision:
        if current_user.is_premium:
            recommended_models = ai_service.VISION_MODELS["premium"][:3]
        else:
            recommended_models = ai_service.VISION_MODELS["free"]
    else:
        if current_user.is_premium:
            recommended_models = ai_service.CHAT_MODELS["premium"][:3]
        else:
            recommended_models = ai_service.CHAT_MODELS["free"][:3]
    
    return {
        "attachments": results,
        "needs_vision_model": needs_vision,
        "recommended_models": recommended_models,
        "auto_switch_available": True
    }