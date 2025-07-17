"""Unit tests for Vector Service."""

from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from app.services.vector_service import VectorService


@pytest.fixture
def vector_service():
    """创建向量服务实例."""
    return VectorService()


@pytest.fixture
def mock_qdrant_client():
    """创建模拟的 Qdrant 客户端."""
    client = Mock()
    # 配置集合响应
    collections_response = Mock()
    collections_response.collections = []
    client.get_collections.return_value = collections_response
    return client


@pytest.fixture
def mock_embedding_model():
    """创建模拟的嵌入模型."""
    model = Mock()
    # 模拟 encode 方法返回 numpy 数组
    model.encode.return_value = np.random.rand(10, 384)  # 返回多个384维向量
    return model


class TestInitialization:
    """测试初始化功能."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, vector_service):
        """测试成功初始化."""
        with patch('qdrant_client.QdrantClient') as mock_client_class:
            # 配置模拟
            mock_client = Mock()
            mock_collections = Mock()
            mock_collections.collections = []
            mock_client.get_collections.return_value = mock_collections
            mock_client_class.return_value = mock_client

            # 执行初始化
            await vector_service.initialize()

            # 验证
            assert vector_service.client is not None
            assert vector_service.embedding_model is not None
            mock_client_class.assert_called_once_with(url="http://localhost:6333")

    @pytest.mark.asyncio
    async def test_initialize_without_qdrant(self, vector_service):
        """测试没有安装 qdrant_client 时的处理."""
        # Mock 导入失败
        with patch.object(vector_service, 'initialize', side_effect=ImportError("qdrant_client 未安装")):
            with pytest.raises(ImportError):
                await vector_service.initialize()

    @pytest.mark.asyncio
    async def test_create_collection_if_not_exists(self, vector_service, mock_qdrant_client):
        """测试创建集合."""
        vector_service.client = mock_qdrant_client

        await vector_service._create_collection_if_not_exists()

        # 验证创建集合被调用
        mock_qdrant_client.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_embedding_model_fallback(self, vector_service):
        """测试嵌入模型加载失败时使用后备方案."""
        with patch('sentence_transformers.SentenceTransformer', side_effect=ImportError):
            await vector_service._initialize_embedding_model()

            # 验证使用后备方案
            assert vector_service.embedding_model is None


class TestDocumentOperations:
    """测试文档操作功能."""

    @pytest.mark.asyncio
    async def test_add_document_success(self, vector_service, mock_qdrant_client):
        """测试成功添加文档."""
        vector_service.client = mock_qdrant_client

        # 创建模拟的嵌入模型，返回正确数量的嵌入向量
        mock_embed_model = Mock()
        # 模拟文本分割后会产生多个块，每个块需要一个嵌入向量
        def mock_encode(texts):
            # 返回与输入文本数量相同的嵌入向量
            return np.random.rand(len(texts), 384)
        mock_embed_model.encode = Mock(side_effect=mock_encode)
        vector_service.embedding_model = mock_embed_model

        # 测试数据
        document_id = 1
        content = "这是一个测试文档内容。" * 100  # 足够长的内容
        metadata = {"space_id": 1, "user_id": 1}

        # 执行添加
        result = await vector_service.add_document(
            document_id=document_id,
            content=content,
            metadata=metadata,
            chunk_size=100,
            overlap=20
        )

        # 验证
        assert result is True
        mock_embed_model.encode.assert_called()
        mock_qdrant_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_document_no_client(self, vector_service):
        """测试没有客户端时添加文档."""
        vector_service.client = None

        result = await vector_service.add_document(
            document_id=1,
            content="test",
            metadata={}
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_add_document_empty_content(self, vector_service, mock_qdrant_client):
        """测试空内容时添加文档."""
        vector_service.client = mock_qdrant_client

        result = await vector_service.add_document(
            document_id=1,
            content="",
            metadata={}
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_document(self, vector_service, mock_qdrant_client):
        """测试删除文档."""
        vector_service.client = mock_qdrant_client

        result = await vector_service.delete_document(document_id=1)

        assert result is True
        mock_qdrant_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_stats(self, vector_service, mock_qdrant_client):
        """测试获取文档统计."""
        vector_service.client = mock_qdrant_client

        # 模拟滚动结果
        mock_points = [
            Mock(payload={"content": "chunk1"}),
            Mock(payload={"content": "chunk2"}),
        ]
        mock_qdrant_client.scroll.return_value = (mock_points, None)

        stats = await vector_service.get_document_stats(document_id=1)

        assert stats["document_id"] == 1
        assert stats["chunk_count"] == 2
        assert stats["total_characters"] == 12  # len("chunk1") + len("chunk2")


class TestSearchOperations:
    """测试搜索操作功能."""

    @pytest.mark.asyncio
    async def test_search_documents_success(self, vector_service, mock_qdrant_client):
        """测试成功搜索文档."""
        vector_service.client = mock_qdrant_client
        # 创建一个专门用于搜索的模拟嵌入模型
        mock_embed_model = Mock()
        # 为单个查询文本返回一个嵌入向量
        mock_embed_model.encode.return_value = np.array([[0.1] * 384])  # 1x384 数组
        vector_service.embedding_model = mock_embed_model

        # 模拟搜索结果
        mock_results = [
            Mock(
                id="1_0",
                score=0.9,
                payload={
                    "document_id": 1,
                    "content": "相关内容",
                    "space_id": 1,
                    "user_id": 1
                }
            )
        ]
        mock_qdrant_client.search.return_value = mock_results

        # 执行搜索
        results = await vector_service.search_documents(
            query="测试查询",
            limit=10,
            score_threshold=0.5
        )

        # 验证
        assert len(results) == 1
        assert results[0]["score"] == 0.9
        assert results[0]["document_id"] == 1
        mock_embed_model.encode.assert_called_once_with(["测试查询"])

    @pytest.mark.asyncio
    async def test_search_documents_with_filter(self, vector_service, mock_qdrant_client):
        """测试带过滤条件的搜索."""
        vector_service.client = mock_qdrant_client
        mock_embed_model = Mock()
        mock_embed_model.encode.return_value = np.array([[0.2] * 384])  # 1x384 数组
        vector_service.embedding_model = mock_embed_model

        mock_qdrant_client.search.return_value = []

        # 执行搜索
        results = await vector_service.search_documents(
            query="测试",
            filter_conditions={"space_id": 1, "user_id": 1}
        )

        # 验证结果
        assert results == []
        # 验证 search 被调用时包含过滤条件
        assert mock_qdrant_client.search.called
        call_args = mock_qdrant_client.search.call_args
        assert call_args.kwargs.get("query_filter") is not None

    @pytest.mark.asyncio
    async def test_search_no_client(self, vector_service):
        """测试没有客户端时搜索."""
        vector_service.client = None

        results = await vector_service.search_documents(query="test")

        assert results == []

    @pytest.mark.asyncio
    async def test_similarity_search_with_space(self, vector_service):
        """测试空间内的相似性搜索."""
        # Mock search_documents 方法
        vector_service.search_documents = AsyncMock(return_value=[{"id": 1}])

        results = await vector_service.similarity_search_with_space(
            query="测试",
            space_id=1,
            limit=5
        )

        # 验证结果
        assert results == [{"id": 1}]
        # 验证调用了 search_documents 并传递了正确的过滤条件
        vector_service.search_documents.assert_called_once_with(
            query="测试",
            limit=5,
            score_threshold=0.5,
            filter_conditions={"space_id": 1}
        )


class TestTextProcessing:
    """测试文本处理功能."""

    @pytest.mark.asyncio
    async def test_split_text(self, vector_service):
        """测试文本分割."""
        text = "这是第一句话。这是第二句话。这是第三句话。" * 10

        chunks = await vector_service._split_text(text, chunk_size=50, overlap=10)

        assert len(chunks) > 1
        assert all(len(chunk) <= 50 for chunk in chunks)

    @pytest.mark.asyncio
    async def test_split_text_empty(self, vector_service):
        """测试空文本分割."""
        chunks = await vector_service._split_text("", chunk_size=100, overlap=10)

        assert chunks == []

    @pytest.mark.asyncio
    async def test_generate_embeddings_with_model(self, vector_service, mock_embedding_model):
        """测试使用模型生成嵌入."""
        vector_service.embedding_model = mock_embedding_model

        embeddings = await vector_service._generate_embeddings(["test1", "test2"])

        assert embeddings is not None
        mock_embedding_model.encode.assert_called_once_with(["test1", "test2"])

    @pytest.mark.asyncio
    async def test_generate_embeddings_fallback(self, vector_service):
        """测试使用后备方案生成嵌入."""
        vector_service.embedding_model = None

        embeddings = await vector_service._generate_embeddings(["test"])

        assert embeddings is not None
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 384

    @pytest.mark.asyncio
    async def test_simple_text_embedding(self, vector_service):
        """测试简单文本嵌入."""
        embeddings = await vector_service._simple_text_embedding(["hello", "world"])

        assert len(embeddings) == 2
        assert all(len(emb) == 384 for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)


class TestHealthAndStats:
    """测试健康检查和统计功能."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, vector_service, mock_qdrant_client):
        """测试健康状态检查."""
        vector_service.client = mock_qdrant_client
        vector_service.embedding_model = Mock()

        # 模拟集合信息
        mock_collections = Mock()
        # 需要创建一个具有 name 属性的集合对象
        mock_collection = Mock()
        mock_collection.name = "documents"
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections

        mock_collection_info = Mock()
        mock_collection_info.points_count = 100
        mock_collection_info.vectors_count = 100
        mock_qdrant_client.get_collection.return_value = mock_collection_info

        result = await vector_service.health_check()

        assert result["status"] == "healthy"
        assert result["points_count"] == 100
        assert result["embedding_model"] == "sentence-transformers"

    @pytest.mark.asyncio
    async def test_health_check_no_client(self, vector_service):
        """测试没有客户端时的健康检查."""
        vector_service.client = None

        result = await vector_service.health_check()

        assert result["status"] == "error"
        assert "客户端未初始化" in result["message"]

    @pytest.mark.asyncio
    async def test_get_space_stats(self, vector_service, mock_qdrant_client):
        """测试获取空间统计."""
        vector_service.client = mock_qdrant_client

        # 模拟点数据
        mock_points = [
            Mock(payload={"document_id": 1, "content": "content1"}),
            Mock(payload={"document_id": 1, "content": "content2"}),
            Mock(payload={"document_id": 2, "content": "content3"}),
        ]
        mock_qdrant_client.scroll.return_value = (mock_points, None)

        stats = await vector_service.get_space_stats(space_id=1)

        assert stats["space_id"] == 1
        assert stats["document_count"] == 2  # 两个不同的文档
        assert stats["chunk_count"] == 3
        assert stats["total_characters"] == 24  # 总字符数
