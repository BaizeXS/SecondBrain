"""
集成测试配置文件。

提供测试数据库、测试客户端和常用的测试工具。
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.main import app
from app.models import User
from app.schemas.users import UserCreate
from app.services import ai_service

# 使用主数据库（简化配置，毕业设计项目不需要独立测试数据库）
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://secondbrain:secondbrain123@localhost:5432/secondbrain",
)

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,  # 测试时不使用连接池
    echo=False,
)

# 创建测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """设置测试数据库。"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """提供测试数据库会话。"""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户。"""
    from app.core.auth import AuthService

    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password="TestPass123!",
    )
    # 手动创建用户并正确哈希密码
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=AuthService.get_password_hash(user_data.password),
        is_active=True,
        is_premium=False,
    )
    db_session.add(db_user)
    await db_session.commit()
    await db_session.refresh(db_user)
    return db_user


@pytest_asyncio.fixture
async def test_premium_user(db_session: AsyncSession) -> User:
    """创建高级测试用户。"""
    from app.core.auth import AuthService

    user_data = UserCreate(
        username="premiumuser",
        email="premium@example.com",
        full_name="Premium User",
        password="PremiumPass123!",
    )
    # 手动创建用户并正确哈希密码
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=AuthService.get_password_hash(user_data.password),
        is_active=True,
        is_premium=True,
    )
    db_session.add(db_user)
    await db_session.commit()
    await db_session.refresh(db_user)
    return db_user


@pytest_asyncio.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """提供测试客户端。"""

    # 覆盖数据库依赖
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # 使用 httpx 的 ASGITransport 进行测试
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """获取认证头部。"""
    # 需要使用表单数据而不是 JSON
    response = await client.post(
        "/api/v1/auth/login", data={"username": "testuser", "password": "TestPass123!"}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(f"Response: {response.text}")
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def premium_auth_headers(client: AsyncClient, test_premium_user: User) -> dict:
    """获取高级用户认证头部。"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "premiumuser", "password": "PremiumPass123!"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_ai_service(monkeypatch):
    """模拟 AI 服务。"""
    from datetime import UTC, datetime

    from app.services import deep_research_service

    async def mock_chat(*args, **kwargs):
        return "This is a mocked AI response."

    async def mock_stream_chat(*args, **kwargs):
        yield "This is "
        yield "a mocked "
        yield "streaming response."

    async def mock_get_embedding(*args, **kwargs):
        return [0.1] * 1536  # OpenAI embedding dimension

    async def mock_deep_research(*args, **kwargs):
        """模拟Deep Research API调用。"""
        return {
            "report": "# Mock Research Report\n\nThis is a mock research report about Knowledge Management Systems.",
            "summary": "Mock research summary about Knowledge Management Systems",
            "citations": [
                {
                    "title": "Mock Source 1",
                    "url": "https://example.com/1",
                    "snippet": "Mock snippet 1",
                    "authors": ["Author 1"],
                    "published_date": "2024-01-01",
                },
                {
                    "title": "Mock Source 2",
                    "url": "https://example.com/2",
                    "snippet": "Mock snippet 2",
                    "authors": ["Author 2"],
                    "published_date": "2024-01-02",
                },
            ],
            "mode": "general",
            "search_time": 0.5,
            "completed_at": datetime.now(UTC).isoformat(),
        }

    async def mock_create_research(*args, **kwargs):
        """模拟Deep Research的create_research方法。"""
        # 从参数中获取必要信息
        query = args[1] if len(args) > 1 else kwargs.get("query", "Test Query")
        user = kwargs.get("user")
        db = kwargs.get("db")

        # 创建测试空间ID
        space_id = 999  # 模拟的空间ID

        return {
            "space_id": space_id,
            "research_id": "mock-research-id-123",
            "status": "completed",
            "query": query,
            "mode": "general",
            "result": {
                "report": "# Mock Research Report\n\nThis is a mock research report.",
                "summary": "Mock research summary",
                "citations": [
                    {
                        "title": "Mock Source 1",
                        "url": "https://example.com/1",
                        "snippet": "Mock snippet 1",
                    }
                ],
            },
        }

    monkeypatch.setattr(ai_service, "chat", mock_chat)
    monkeypatch.setattr(ai_service, "stream_chat", mock_stream_chat)
    monkeypatch.setattr(ai_service, "get_embedding", mock_get_embedding)
    monkeypatch.setattr(deep_research_service, "create_research", mock_create_research)

    return ai_service  # 返回 ai_service 以便测试可以检查它不是 None


# 测试数据
@pytest.fixture
def sample_space_data():
    """示例空间数据。"""
    return {
        "name": "Test Space",
        "description": "A space for testing",
        "color": "#FF5733",
        "icon": "folder",
        "is_public": False,
        "tags": ["test", "integration"],
        "meta_data": {"purpose": "testing"},
    }


@pytest.fixture
def sample_document_data():
    """示例文档数据。"""
    return {
        "filename": "test_document.txt",
        "content_type": "text/plain",
        "size": 1024,
        "description": "A test document",
        "tags": ["test", "document"],
        "meta_data": {"test": True},
    }


@pytest.fixture
def sample_note_data():
    """示例笔记数据。"""
    return {
        "title": "Test Note",
        "content": "This is a test note content.",
        "tags": ["test", "note"],
        "meta_data": {"important": True},
    }


@pytest.fixture
def sample_conversation_data():
    """示例对话数据。"""
    return {
        "title": "Test Conversation",
        "mode": "chat",
        "model": "gpt-3.5-turbo",
        "meta_data": {"test": True},
    }
