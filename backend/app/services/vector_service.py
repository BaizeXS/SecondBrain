"""Vector storage service using Qdrant."""

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class VectorService:
    """向量存储服务."""

    def __init__(self, qdrant_url: str = "http://localhost:6333") -> None:
        """初始化向量服务."""
        self.qdrant_url = qdrant_url
        self.client: Any | None = None  # QdrantClient
        self.embedding_model: Any | None = None  # SentenceTransformer
        self.collection_name = "documents"

    async def initialize(self) -> None:
        """初始化连接."""
        try:
            from qdrant_client import QdrantClient

            self.client = QdrantClient(url=self.qdrant_url)

            # 创建集合（如果不存在）
            try:
                await self._create_collection_if_not_exists()
            except Exception as e:
                logger.warning(f"创建集合失败: {str(e)}")

            # 初始化嵌入模型
            await self._initialize_embedding_model()

            logger.info("向量服务初始化成功")

        except ImportError:
            logger.error("qdrant_client 未安装")
            raise
        except Exception as e:
            logger.error(f"向量服务初始化失败: {str(e)}")
            raise

    async def _create_collection_if_not_exists(self) -> None:
        """创建集合（如果不存在）."""
        from qdrant_client.models import Distance, VectorParams

        try:
            # 检查集合是否存在
            if not self.client:
                raise Exception("客户端未初始化")

            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                # 创建集合
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # sentence-transformers/all-MiniLM-L6-v2 的维度
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"创建集合: {self.collection_name}")
            else:
                logger.info(f"集合已存在: {self.collection_name}")

        except Exception as e:
            logger.error(f"创建集合失败: {str(e)}")
            raise

    async def _initialize_embedding_model(self) -> None:
        """初始化嵌入模型."""
        try:
            from sentence_transformers import SentenceTransformer

            # 使用轻量级的中文嵌入模型
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.embedding_model = SentenceTransformer(model_name)

            logger.info(f"嵌入模型加载成功: {model_name}")

        except ImportError:
            logger.error("sentence_transformers 未安装")
            # 使用简单的文本嵌入作为后备
            self.embedding_model = None
        except Exception as e:
            logger.error(f"嵌入模型加载失败: {str(e)}")
            self.embedding_model = None

    async def add_document(
        self,
        document_id: int,
        content: str,
        metadata: dict[str, Any],
        chunk_size: int = 1000,
        overlap: int = 100,
    ) -> bool:
        """添加文档到向量数据库."""
        try:
            if not self.client or not content:
                return False

            # 分割文档
            chunks = await self._split_text(content, chunk_size, overlap)

            # 生成嵌入
            embeddings = await self._generate_embeddings(chunks)

            if embeddings is None or len(embeddings) == 0:
                return False

            # 准备点数据
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
                point_id = f"{document_id}_{i}"

                point_metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk,
                    **metadata,
                }

                points.append(
                    {
                        "id": point_id,
                        "vector": embedding.tolist()
                        if isinstance(embedding, np.ndarray)
                        else embedding,
                        "payload": point_metadata,
                    }
                )

            # 批量插入
            from qdrant_client.models import PointStruct

            qdrant_points = [
                PointStruct(
                    id=point["id"], vector=point["vector"], payload=point["payload"]
                )
                for point in points
            ]

            self.client.upsert(
                collection_name=self.collection_name, points=qdrant_points
            )

            logger.info(f"文档 {document_id} 添加成功，共 {len(chunks)} 个片段")
            return True

        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            return False

    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.5,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """搜索相似文档."""
        try:
            if not self.client or not query:
                return []

            # 生成查询嵌入
            query_embedding = await self._generate_embeddings([query])
            if query_embedding is None or len(query_embedding) == 0:
                return []

            # 构建过滤条件
            search_filter = None
            if filter_conditions:
                from qdrant_client.models import FieldCondition, Filter, MatchValue

                conditions: list[Any] = []  # FieldCondition
                for field, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(key=field, match=MatchValue(value=value))
                    )

                if conditions:
                    search_filter = Filter(must=conditions)

            # 执行搜索
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding[0].tolist()
                if isinstance(query_embedding[0], np.ndarray)
                else query_embedding[0],
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter,
                with_payload=True,
            )

            # 处理结果
            results = []
            for result in search_results:
                results.append(
                    {
                        "id": result.id,
                        "score": result.score,
                        "document_id": result.payload.get("document_id"),
                        "content": result.payload.get("content"),
                        "metadata": {
                            k: v
                            for k, v in result.payload.items()
                            if k not in ["document_id", "chunk_index", "content"]
                        },
                    }
                )

            return results

        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}")
            return []

    async def delete_document(self, document_id: int) -> bool:
        """删除文档的所有向量."""
        try:
            if not self.client:
                return False

            from qdrant_client.models import FieldCondition, Filter, MatchValue

            # 删除所有属于该文档的点
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=document_id)
                        )
                    ]
                ),
            )

            logger.info(f"文档 {document_id} 的向量已删除")
            return True

        except Exception as e:
            logger.error(f"删除文档向量失败: {str(e)}")
            return False

    async def get_document_stats(self, document_id: int) -> dict[str, Any]:
        """获取文档向量统计信息."""
        try:
            if not self.client:
                return {}

            from qdrant_client.models import FieldCondition, Filter, MatchValue

            # 查询文档的所有点
            search_results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=1000,
                with_payload=True,
            )

            points = search_results[0]  # 第一个元素是点列表

            return {
                "document_id": document_id,
                "chunk_count": len(points),
                "total_characters": sum(
                    len(point.payload.get("content", "")) for point in points
                ),
            }

        except Exception as e:
            logger.error(f"获取文档统计失败: {str(e)}")
            return {}

    async def _split_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """分割文本."""
        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # 如果不是最后一块，尝试在句号或换行符处分割
            if end < len(text):
                # 寻找最近的句号或换行符
                for i in range(end, max(start + chunk_size // 2, start), -1):
                    if text[i] in ".。\n":
                        end = i + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap if end < len(text) else end

        return chunks

    async def _generate_embeddings(self, texts: list[str]) -> list[Any] | None:
        """生成文本嵌入."""
        try:
            if not texts:
                return None

            if self.embedding_model:
                # 使用sentence-transformers
                embeddings = self.embedding_model.encode(texts)
                return embeddings
            else:
                # 简单的文本嵌入（作为后备）
                return await self._simple_text_embedding(texts)

        except Exception as e:
            logger.error(f"生成嵌入失败: {str(e)}")
            return None

    async def _simple_text_embedding(self, texts: list[str]) -> list[list[float]]:
        """简单的文本嵌入（基于字符频率）."""
        try:
            import hashlib
            from collections import Counter

            embeddings = []

            for text in texts:
                # 基于字符频率的简单嵌入
                char_counts = Counter(text.lower())

                # 创建384维向量
                embedding = [0.0] * 384

                # 使用哈希值分布到不同维度
                for char, count in char_counts.items():
                    hash_val = int(hashlib.md5(char.encode()).hexdigest(), 16)
                    index = hash_val % 384
                    embedding[index] += count / len(text)

                # 归一化
                norm = sum(x * x for x in embedding) ** 0.5
                if norm > 0:
                    embedding = [x / norm for x in embedding]

                embeddings.append(embedding)

            return embeddings

        except Exception as e:
            logger.error(f"简单嵌入生成失败: {str(e)}")
            return [[0.0] * 384 for _ in texts]

    async def health_check(self) -> dict[str, Any]:
        """健康检查."""
        try:
            if not self.client:
                return {"status": "error", "message": "客户端未初始化"}

            # 检查集合状态
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                return {"status": "error", "message": "集合不存在"}

            # 获取集合信息
            collection_info = self.client.get_collection(self.collection_name)

            return {
                "status": "healthy",
                "collection": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "embedding_model": "sentence-transformers"
                if self.embedding_model
                else "simple",
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def similarity_search_with_space(
        self, query: str, space_id: int, limit: int = 10, score_threshold: float = 0.5
    ) -> list[dict[str, Any]]:
        """在指定空间中搜索相似文档."""
        filter_conditions = {"space_id": space_id}
        return await self.search_documents(
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            filter_conditions=filter_conditions,
        )

    async def get_space_stats(self, space_id: int) -> dict[str, Any]:
        """获取空间向量统计."""
        try:
            if not self.client:
                return {}

            from qdrant_client.models import FieldCondition, Filter, MatchValue

            # 查询空间的所有点
            search_results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="space_id", match=MatchValue(value=space_id))
                    ]
                ),
                limit=10000,
                with_payload=True,
            )

            points = search_results[0]

            # 统计文档数量
            document_ids = set()
            total_chunks = len(points)
            total_characters = 0

            for point in points:
                document_ids.add(point.payload.get("document_id"))
                total_characters += len(point.payload.get("content", ""))

            return {
                "space_id": space_id,
                "document_count": len(document_ids),
                "chunk_count": total_chunks,
                "total_characters": total_characters,
            }

        except Exception as e:
            logger.error(f"获取空间统计失败: {str(e)}")
            return {}


# 全局向量服务实例
vector_service = VectorService()
