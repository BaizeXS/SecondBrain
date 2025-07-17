"""Ollama service for managing local models."""

import json
import logging
import uuid
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.ollama import (
    OllamaModelInfo,
    OllamaModelResponse,
)

logger = logging.getLogger(__name__)


class OllamaService:
    """Ollama服务类."""

    def __init__(self) -> None:
        """初始化Ollama服务."""
        self.base_url = settings.OLLAMA_BASE_URL
        self.timeout = httpx.Timeout(300.0, connect=10.0)

    async def check_status(self) -> dict[str, Any]:
        """检查Ollama服务状态."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 检查服务是否运行
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return {
                        "available": False,
                        "error": "Ollama服务不可用",
                    }

                # 获取模型列表
                data = response.json()
                models = data.get("models", [])

                # 计算总大小
                total_size = sum(model.get("size", 0) for model in models)

                # 尝试获取版本信息
                version = None
                try:
                    version_response = await client.get(f"{self.base_url}/api/version")
                    if version_response.status_code == 200:
                        version_data = version_response.json()
                        version = version_data.get("version")
                except Exception:
                    pass

                return {
                    "available": True,
                    "version": version,
                    "models_count": len(models),
                    "total_size": total_size,
                    "gpu_available": self._check_gpu_support(),
                }

        except Exception as e:
            logger.error(f"Failed to check Ollama status: {e}")
            return {
                "available": False,
                "error": str(e),
            }

    async def list_models(self) -> list[OllamaModelResponse]:
        """列出所有已安装的模型."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model_data in data.get("models", []):
                        models.append(OllamaModelResponse(
                            name=model_data["name"],
                            size=model_data["size"],
                            digest=model_data["digest"],
                            modified_at=model_data["modified_at"],
                        ))
                    return models
                return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def get_model_info(self, model_name: str) -> OllamaModelInfo | None:
        """获取模型详细信息."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_name}
                )
                if response.status_code == 200:
                    data = response.json()

                    # 解析模型信息
                    details = data.get("details", {})

                    return OllamaModelInfo(
                        name=model_name,
                        model_format=details.get("format", "unknown"),
                        family=details.get("family", "unknown"),
                        parameter_size=details.get("parameter_size", "unknown"),
                        quantization_level=details.get("quantization_level", "unknown"),
                        size=data.get("size", 0),
                        digest=data.get("digest", ""),
                        details=details,
                    )
                return None
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return None

    async def pull_model(self, model_name: str, insecure: bool = False) -> str:
        """拉取模型（异步任务）."""
        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 简化处理，直接调用API（适合毕设项目）
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as client:
                # 启动拉取
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={
                        "name": model_name,
                        "insecure": insecure,
                    },
                    timeout=None,  # 拉取可能需要很长时间
                )

                if response.status_code == 200:
                    return task_id
                else:
                    raise Exception(f"Failed to pull model: {response.text}")

        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            raise

    async def delete_model(self, model_name: str) -> bool:
        """删除模型."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    "DELETE",
                    f"{self.base_url}/api/delete",
                    json={"name": model_name}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            return False

    async def generate_embedding(
        self,
        model: str,
        prompt: str,
    ) -> list[float]:
        """生成文本嵌入."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": model,
                        "prompt": prompt,
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding", [])
                else:
                    raise Exception(f"Failed to generate embedding: {response.text}")

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def _check_gpu_support(self) -> bool:
        """检查是否支持GPU."""
        # TODO: 实际检查GPU支持
        # 可以通过调用Ollama API或检查系统信息
        return False

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        stream: bool = False,
        **kwargs: Any
    ) -> Any:
        """聊天补全接口."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": stream,
                        **kwargs
                    }
                )

                if response.status_code == 200:
                    if stream:
                        # 流式响应
                        async for line in response.aiter_lines():
                            if line:
                                data = json.loads(line)
                                yield data
                    else:
                        # 非流式响应
                        yield response.json()
                else:
                    raise Exception(f"Chat completion failed: {response.text}")

        except Exception as e:
            logger.error(f"Failed to complete chat: {e}")
            raise


# 创建全局实例
ollama_service = OllamaService()
