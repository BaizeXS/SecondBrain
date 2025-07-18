"""Ollama model management endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models.models import User
from app.schemas.ollama import (
    OllamaModelInfo,
    OllamaModelListResponse,
    OllamaPullRequest,
    OllamaPullResponse,
)
from app.services.ollama_service import ollama_service

router = APIRouter()


@router.get("/models", response_model=OllamaModelListResponse)
async def list_ollama_models(
    current_user: User = Depends(get_current_active_user),
) -> OllamaModelListResponse:
    """列出所有可用的Ollama模型."""
    try:
        models = await ollama_service.list_models()
        return OllamaModelListResponse(
            models=models,
            total=len(models),
            is_available=True,
            error=None,
        )
    except Exception as e:
        return OllamaModelListResponse(
            models=[],
            total=0,
            is_available=False,
            error=str(e),
        )


@router.get("/models/{model_name}", response_model=OllamaModelInfo)
async def get_model_info(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
) -> OllamaModelInfo:
    """获取特定模型的详细信息."""
    try:
        info = await ollama_service.get_model_info(model_name)
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 {model_name} 不存在",
            )
        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型信息失败: {str(e)}",
        ) from e


@router.post("/pull", response_model=OllamaPullResponse)
async def pull_model(
    request: OllamaPullRequest,
    current_user: User = Depends(get_current_active_user),
) -> OllamaPullResponse:
    """拉取新的Ollama模型."""
    # 只有管理员可以拉取新模型
    if not current_user.is_active:  # TODO: Add is_superuser field to User model
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以拉取新模型",
        )

    try:
        # 启动拉取任务
        task_id = await ollama_service.pull_model(
            request.model_name,
            insecure=request.insecure,
        )

        return OllamaPullResponse(
            task_id=task_id,
            status="pulling",
            model_name=request.model_name,
            progress=0,
            message=f"开始拉取模型 {request.model_name}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"拉取模型失败: {str(e)}",
        ) from e


@router.delete("/models/{model_name}")
async def delete_model(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """删除Ollama模型."""
    # 只有管理员可以删除模型
    if not current_user.is_active:  # TODO: Add is_superuser field to User model
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除模型",
        )

    try:
        success = await ollama_service.delete_model(model_name)
        if success:
            return {"message": f"模型 {model_name} 已删除"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"删除模型 {model_name} 失败",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除模型失败: {str(e)}",
        ) from e


@router.get("/status")
async def get_ollama_status(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取Ollama服务状态."""
    _ = current_user  # Ensure user is authenticated
    status = await ollama_service.check_status()
    return status


@router.get("/recommended-models")
async def get_recommended_models(
    current_user: User = Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    """获取推荐的模型列表."""
    _ = current_user  # Ensure user is authenticated
    return [
        {
            "name": "llama2:7b",
            "description": "Meta的Llama 2模型，7B参数，适合一般对话",
            "size": "3.8GB",
            "capabilities": ["chat", "generation"],
        },
        {
            "name": "mistral:7b",
            "description": "Mistral AI的7B模型，性能优异",
            "size": "4.1GB",
            "capabilities": ["chat", "generation"],
        },
        {
            "name": "deepseek-coder:6.7b",
            "description": "DeepSeek的代码模型，适合编程任务",
            "size": "3.8GB",
            "capabilities": ["code", "chat"],
        },
        {
            "name": "nomic-embed-text",
            "description": "高质量的文本嵌入模型",
            "size": "274MB",
            "capabilities": ["embedding"],
        },
        {
            "name": "qwen:7b",
            "description": "阿里通义千问模型，中文能力强",
            "size": "4.1GB",
            "capabilities": ["chat", "generation", "chinese"],
        },
        {
            "name": "gemma:2b",
            "description": "Google的轻量级模型，适合资源受限环境",
            "size": "1.4GB",
            "capabilities": ["chat", "generation"],
        },
    ]
