"""Test API v1 main router."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAPIRouter:
    """Test API router configuration."""

    def test_api_router_included(self, client):
        """Test that API router is properly included."""
        # 测试根路径
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert data["docs"] == f"{settings.API_V1_STR}/docs"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == settings.APP_NAME
        assert data["version"] == settings.VERSION
        assert "timestamp" in data

    def test_openapi_available(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get(f"{settings.API_V1_STR}/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == settings.APP_NAME
        assert schema["info"]["version"] == settings.VERSION

    def test_docs_available(self, client):
        """Test that docs are available."""
        response = client.get(f"{settings.API_V1_STR}/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text.lower()

    def test_redoc_available(self, client):
        """Test that redoc is available."""
        response = client.get(f"{settings.API_V1_STR}/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()

    def test_all_routers_included(self, client):
        """Test that all expected routers are included."""
        # 获取OpenAPI schema来检查所有路由
        response = client.get(f"{settings.API_V1_STR}/openapi.json")
        schema = response.json()
        paths = schema.get("paths", {})

        # 检查所有预期的路由前缀
        expected_prefixes = [
            f"{settings.API_V1_STR}/auth",
            f"{settings.API_V1_STR}/users",
            f"{settings.API_V1_STR}/chat",
            f"{settings.API_V1_STR}/spaces",
            f"{settings.API_V1_STR}/documents",
            f"{settings.API_V1_STR}/agents",
            f"{settings.API_V1_STR}/notes",
            f"{settings.API_V1_STR}/annotations",
            f"{settings.API_V1_STR}/citations",
            f"{settings.API_V1_STR}/export",
            f"{settings.API_V1_STR}/ollama",
        ]

        for prefix in expected_prefixes:
            # 检查至少有一个路径以该前缀开始
            has_prefix = any(path.startswith(prefix) for path in paths.keys())
            assert has_prefix, f"No routes found with prefix {prefix}"

    def test_router_tags_defined(self):
        """Test that routers are included with proper tags."""
        import app.api.v1.api as api_module

        with open(api_module.__file__, encoding="utf-8") as f:
            content = f.read()

        # 检查所有路由都有tags参数
        expected_tags = [
            'tags=["认证"]',
            'tags=["用户"]',
            'tags=["聊天"]',
            'tags=["空间"]',
            'tags=["文档"]',
            'tags=["代理"]',
            'tags=["笔记"]',
            'tags=["标注"]',
            'tags=["引用"]',
            'tags=["导出"]',
            'tags=["Ollama"]',
        ]

        for tag in expected_tags:
            assert tag in content, f"Tag definition '{tag}' not found in api.py"


class TestRouterIssues:
    """Test for potential issues in router configuration."""

    def test_no_duplicate_imports(self):
        """Test that all modules are imported only once in api.py."""
        import app.api.v1.api as api_module

        with open(api_module.__file__, encoding="utf-8") as f:
            content = f.read()

        # 检查agents是否在导入列表中
        assert "agents," in content, "agents should be in the import list"

        # 确保没有重复的单独导入语句
        assert "from app.api.v1.endpoints import agents" not in content, (
            "agents should not have separate import"
        )

    def test_router_order(self):
        """Test that routers are included in a logical order."""
        import app.api.v1.api as api_module

        with open(api_module.__file__, encoding="utf-8") as f:
            lines = f.readlines()

        # 找出所有include_router调用的顺序
        router_order = []
        for line in lines:
            if "include_router" in line and "prefix=" in line:
                # 提取prefix值
                prefix_start = line.find('prefix="') + 8
                prefix_end = line.find('"', prefix_start)
                if prefix_start > 7 and prefix_end > prefix_start:
                    prefix = line[prefix_start:prefix_end]
                    router_order.append(prefix)

        # 认证应该在最前面
        assert router_order[0] == "/auth", "Auth router should be first"
        # 用户应该在认证之后
        assert router_order[1] == "/users", "Users router should be after auth"
