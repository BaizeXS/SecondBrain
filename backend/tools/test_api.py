#!/usr/bin/env python3
"""
完整API测试工具
测试所有已实现的API端点
用法: uv run python tools/test_api.py
"""

import asyncio
import json
from datetime import datetime

import httpx

# API配置
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {"username": "demo_user", "password": "Demo123456!"}

# 测试结果统计
results = {"total": 0, "passed": 0, "failed": 0, "details": []}


def record_result(endpoint, method, success, message="", response_code=None):
    """记录测试结果"""
    results["total"] += 1
    if success:
        results["passed"] += 1
        emoji = "✅"
    else:
        results["failed"] += 1
        emoji = "❌"

    detail = f"{emoji} {method:6} {endpoint:50} "
    if response_code:
        detail += f"[{response_code}] "
    if message:
        detail += f"- {message}"

    print(detail)
    results["details"].append(
        {
            "endpoint": endpoint,
            "method": method,
            "success": success,
            "message": message,
            "response_code": response_code,
        }
    )


async def test_public_endpoints():
    """测试公开端点（不需要认证）"""
    print("\n🌐 测试公开端点...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 健康检查
        try:
            response = await client.get(f"{BASE_URL}/health")
            record_result(
                "/health", "GET", response.status_code == 200, "", response.status_code
            )
        except Exception as e:
            record_result("/health", "GET", False, str(e))


async def test_auth_endpoints():
    """测试认证相关端点"""
    print("\n🔐 测试认证端点...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 测试注册（可能失败如果用户已存在）
        test_user_reg = {
            "username": f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
            "password": "Test123456!",
            "full_name": "测试用户",
        }

        try:
            response = await client.post(
                f"{BASE_URL}/auth/register", json=test_user_reg
            )
            record_result(
                "/auth/register",
                "POST",
                response.status_code == 201,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/auth/register", "POST", False, str(e))

        # 测试登录
        try:
            response = await client.post(f"{BASE_URL}/auth/login", data=TEST_USER)
            success = response.status_code == 200
            record_result("/auth/login", "POST", success, "", response.status_code)

            if success:
                token_data = response.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                return access_token, refresh_token
            return None, None
        except Exception as e:
            record_result("/auth/login", "POST", False, str(e))
            return None, None


async def test_authenticated_endpoints(token):
    """测试需要认证的端点"""
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 用户相关
        print("\n👤 测试用户端点...")

        # GET /users/me
        try:
            response = await client.get(f"{BASE_URL}/users/me", headers=headers)
            record_result(
                "/users/me",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/users/me", "GET", False, str(e))

        # PUT /users/me
        try:
            update_data = {"full_name": "更新的演示用户"}
            response = await client.put(
                f"{BASE_URL}/users/me", headers=headers, json=update_data
            )
            record_result(
                "/users/me",
                "PUT",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/users/me", "PUT", False, str(e))

        # GET /users/me/stats
        try:
            response = await client.get(f"{BASE_URL}/users/me/stats", headers=headers)
            record_result(
                "/users/me/stats",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/users/me/stats", "GET", False, str(e))

        # 空间相关
        print("\n📁 测试空间端点...")
        space_id = None

        # POST /spaces
        try:
            space_data = {
                "name": f"测试空间 {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "description": "API测试创建的空间",
            }
            response = await client.post(
                f"{BASE_URL}/spaces", headers=headers, json=space_data
            )
            record_result(
                "/spaces", "POST", response.status_code == 201, "", response.status_code
            )
            if response.status_code == 201:
                space_id = response.json()["id"]
        except Exception as e:
            record_result("/spaces", "POST", False, str(e))

        # GET /spaces
        try:
            response = await client.get(f"{BASE_URL}/spaces", headers=headers)
            record_result(
                "/spaces", "GET", response.status_code == 200, "", response.status_code
            )
            if response.status_code == 200 and not space_id:
                spaces = response.json()
                if spaces:
                    space_id = spaces[0]["id"]
        except Exception as e:
            record_result("/spaces", "GET", False, str(e))

        if space_id:
            # GET /spaces/{space_id}
            try:
                response = await client.get(
                    f"{BASE_URL}/spaces/{space_id}", headers=headers
                )
                record_result(
                    f"/spaces/{space_id}",
                    "GET",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/spaces/{space_id}", "GET", False, str(e))

            # PUT /spaces/{space_id}
            try:
                update_data = {"name": "更新的测试空间"}
                response = await client.put(
                    f"{BASE_URL}/spaces/{space_id}", headers=headers, json=update_data
                )
                record_result(
                    f"/spaces/{space_id}",
                    "PUT",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/spaces/{space_id}", "PUT", False, str(e))

        # 笔记相关
        print("\n📝 测试笔记端点...")
        note_id = None

        # POST /notes
        if space_id:
            try:
                note_data = {
                    "title": "测试笔记",
                    "content": "这是一个测试笔记内容",
                    "space_id": space_id,
                    "note_type": "manual",
                }
                response = await client.post(
                    f"{BASE_URL}/notes", headers=headers, json=note_data
                )
                record_result(
                    "/notes",
                    "POST",
                    response.status_code == 201,
                    "",
                    response.status_code,
                )
                if response.status_code == 201:
                    note_id = response.json()["id"]
            except Exception as e:
                record_result("/notes", "POST", False, str(e))

        # GET /notes
        try:
            response = await client.get(f"{BASE_URL}/notes", headers=headers)
            record_result(
                "/notes", "GET", response.status_code == 200, "", response.status_code
            )
        except Exception as e:
            record_result("/notes", "GET", False, str(e))

        # GET /notes/recent
        try:
            response = await client.get(f"{BASE_URL}/notes/recent", headers=headers)
            record_result(
                "/notes/recent", "GET", response.status_code == 200, "", response.status_code
            )
        except Exception as e:
            record_result("/notes/recent", "GET", False, str(e))

        # POST /notes/search
        try:
            search_data = {"query": "测试"}
            response = await client.post(
                f"{BASE_URL}/notes/search", headers=headers, json=search_data
            )
            record_result(
                "/notes/search", "POST", response.status_code == 200, "", response.status_code
            )
        except Exception as e:
            record_result("/notes/search", "POST", False, str(e))

        # GET /notes/tags/all
        try:
            response = await client.get(f"{BASE_URL}/notes/tags/all", headers=headers)
            record_result(
                "/notes/tags/all", "GET", response.status_code == 200, "", response.status_code
            )
        except Exception as e:
            record_result("/notes/tags/all", "GET", False, str(e))

        if note_id:
            # GET /notes/{note_id}
            try:
                response = await client.get(
                    f"{BASE_URL}/notes/{note_id}", headers=headers
                )
                record_result(
                    f"/notes/{note_id}",
                    "GET",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/notes/{note_id}", "GET", False, str(e))

            # PUT /notes/{note_id}
            try:
                update_data = {"content": "更新的测试笔记内容"}
                response = await client.put(
                    f"{BASE_URL}/notes/{note_id}", headers=headers, json=update_data
                )
                record_result(
                    f"/notes/{note_id}",
                    "PUT",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/notes/{note_id}", "PUT", False, str(e))

            # GET /notes/{note_id}/versions
            try:
                response = await client.get(
                    f"{BASE_URL}/notes/{note_id}/versions", headers=headers
                )
                record_result(
                    f"/notes/{note_id}/versions",
                    "GET",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/notes/{note_id}/versions", "GET", False, str(e))

        # 对话相关
        print("\n💬 测试对话端点...")
        conversation_id = None

        # POST /chat/conversations
        if space_id:
            try:
                conv_data = {"space_id": space_id}
                response = await client.post(
                    f"{BASE_URL}/chat/conversations", headers=headers, json=conv_data
                )
                record_result(
                    "/chat/conversations",
                    "POST",
                    response.status_code == 201,
                    "",
                    response.status_code,
                )
                if response.status_code == 201:
                    conversation_id = response.json()["id"]
            except Exception as e:
                record_result("/chat/conversations", "POST", False, str(e))

        # GET /chat/conversations
        try:
            response = await client.get(
                f"{BASE_URL}/chat/conversations", headers=headers
            )
            record_result(
                "/chat/conversations",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
            if response.status_code == 200 and not conversation_id:
                conversations = response.json()
                if conversations:
                    conversation_id = conversations[0]["id"]
        except Exception as e:
            record_result("/chat/conversations", "GET", False, str(e))

        if conversation_id:
            # GET /chat/conversations/{conversation_id}
            try:
                response = await client.get(
                    f"{BASE_URL}/chat/conversations/{conversation_id}", headers=headers
                )
                record_result(
                    f"/chat/conversations/{conversation_id}",
                    "GET",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/chat/conversations/{conversation_id}", "GET", False, str(e))

            # PUT /chat/conversations/{conversation_id}
            try:
                update_data = {"title": "更新的对话标题"}
                response = await client.put(
                    f"{BASE_URL}/chat/conversations/{conversation_id}",
                    headers=headers,
                    json=update_data
                )
                record_result(
                    f"/chat/conversations/{conversation_id}",
                    "PUT",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/chat/conversations/{conversation_id}", "PUT", False, str(e))

        # GET /chat/models
        try:
            response = await client.get(f"{BASE_URL}/chat/models", headers=headers)
            record_result(
                "/chat/models",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/chat/models", "GET", False, str(e))

        # POST /chat/messages
        if conversation_id:
            try:
                message_data = {
                    "conversation_id": conversation_id,
                    "content": "测试消息",
                    "model": "openrouter/auto",
                    "mode": "chat",
                }
                response = await client.post(
                    f"{BASE_URL}/chat/messages", headers=headers, json=message_data
                )
                record_result(
                    "/chat/messages",
                    "POST",
                    response.status_code == 201,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result("/chat/messages", "POST", False, str(e))

        # GET /chat/messages
        try:
            params = {"conversation_id": conversation_id} if conversation_id else {}
            response = await client.get(
                f"{BASE_URL}/chat/messages", headers=headers, params=params
            )
            record_result(
                "/chat/messages",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/chat/messages", "GET", False, str(e))

        # POST /chat/search
        try:
            search_data = {
                "query": "测试搜索",
                "model": "openrouter/perplexity/sonar-online"
            }
            response = await client.post(
                f"{BASE_URL}/chat/search", headers=headers, json=search_data
            )
            record_result(
                "/chat/search",
                "POST",
                response.status_code in [201, 400],  # 可能需要特定配置
                "AI搜索",
                response.status_code,
            )
        except Exception as e:
            record_result("/chat/search", "POST", False, str(e))

        # 文档相关
        print("\n📄 测试文档端点...")

        # GET /documents
        try:
            response = await client.get(f"{BASE_URL}/documents", headers=headers)
            record_result(
                "/documents",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/documents", "GET", False, str(e))

        # POST /documents/search
        try:
            search_data = {"query": "测试", "space_id": space_id if space_id else None}
            response = await client.post(
                f"{BASE_URL}/documents/search",
                headers=headers,
                json=search_data,
            )
            record_result(
                "/documents/search",
                "POST",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/documents/search", "POST", False, str(e))

        # POST /documents/web-import
        if space_id:
            try:
                import_data = {"url": "https://example.com", "space_id": space_id}
                response = await client.post(
                    f"{BASE_URL}/documents/web-import",
                    headers=headers,
                    json=import_data,
                )
                # 可能失败，但记录结果
                record_result(
                    "/documents/web-import",
                    "POST",
                    response.status_code in [201, 400, 422],
                    "URL导入测试",
                    response.status_code,
                )
            except Exception as e:
                record_result("/documents/web-import", "POST", False, str(e))

        # POST /documents/analyze-url
        try:
            analyze_data = {"url": "https://example.com"}
            response = await client.post(
                f"{BASE_URL}/documents/analyze-url",
                headers=headers,
                json=analyze_data,
            )
            record_result(
                "/documents/analyze-url",
                "POST",
                response.status_code in [200, 400],
                "URL分析",
                response.status_code,
            )
        except Exception as e:
            record_result("/documents/analyze-url", "POST", False, str(e))

        # 标注相关
        print("\n🔖 测试标注端点...")

        # GET /annotations/my
        try:
            response = await client.get(f"{BASE_URL}/annotations/my", headers=headers)
            record_result(
                "/annotations/my",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/annotations/my", "GET", False, str(e))

        # GET /annotations/statistics
        try:
            response = await client.get(f"{BASE_URL}/annotations/statistics", headers=headers)
            record_result(
                "/annotations/statistics",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/annotations/statistics", "GET", False, str(e))

        # 引用相关
        print("\n📚 测试引用端点...")

        # GET /citations
        try:
            response = await client.get(f"{BASE_URL}/citations", headers=headers)
            record_result(
                "/citations",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/citations", "GET", False, str(e))

        # POST /citations
        citation_id = None
        if space_id:
            try:
                citation_data = {
                    "title": "测试引用",
                    "authors": ["测试作者"],
                    "year": 2024,
                    "space_id": space_id,
                    "citation_type": "article"
                }
                response = await client.post(
                    f"{BASE_URL}/citations", headers=headers, json=citation_data
                )
                record_result(
                    "/citations",
                    "POST",
                    response.status_code == 201,
                    "",
                    response.status_code,
                )
                if response.status_code == 201:
                    citation_id = response.json()["id"]
            except Exception as e:
                record_result("/citations", "POST", False, str(e))

        # POST /citations/search
        try:
            search_data = {"query": "测试"}
            response = await client.post(
                f"{BASE_URL}/citations/search", headers=headers, json=search_data
            )
            record_result(
                "/citations/search",
                "POST",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/citations/search", "POST", False, str(e))

        # POST /citations/export
        if space_id:
            try:
                export_data = {"space_id": space_id, "format": "bibtex"}
                response = await client.post(
                    f"{BASE_URL}/citations/export", headers=headers, json=export_data
                )
                record_result(
                    "/citations/export",
                    "POST",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result("/citations/export", "POST", False, str(e))

        # 导出相关
        print("\n📤 测试导出端点...")

        if space_id:
            # POST /export/space
            try:
                export_data = {"space_id": space_id, "format": "markdown"}
                response = await client.post(
                    f"{BASE_URL}/export/space", headers=headers, json=export_data
                )
                record_result(
                    "/export/space",
                    "POST",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result("/export/space", "POST", False, str(e))

        if note_id:
            # POST /export/notes
            try:
                export_data = {"note_ids": [note_id], "format": "markdown"}
                response = await client.post(
                    f"{BASE_URL}/export/notes", headers=headers, json=export_data
                )
                record_result(
                    "/export/notes",
                    "POST",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result("/export/notes", "POST", False, str(e))

        if conversation_id:
            # POST /export/conversations
            try:
                export_data = {"conversation_ids": [conversation_id], "format": "markdown"}
                response = await client.post(
                    f"{BASE_URL}/export/conversations", headers=headers, json=export_data
                )
                record_result(
                    "/export/conversations",
                    "POST",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result("/export/conversations", "POST", False, str(e))


        # Ollama相关
        print("\n🤖 测试Ollama端点...")

        # GET /ollama/models
        try:
            response = await client.get(f"{BASE_URL}/ollama/models", headers=headers)
            # Ollama可能未安装，所以200或503都可接受
            record_result(
                "/ollama/models",
                "GET",
                response.status_code in [200, 503],
                "Ollama模型列表",
                response.status_code,
            )
        except Exception as e:
            record_result("/ollama/models", "GET", False, str(e))

        # GET /ollama/status
        try:
            response = await client.get(f"{BASE_URL}/ollama/status", headers=headers)
            record_result(
                "/ollama/status",
                "GET",
                response.status_code in [200, 503],
                "Ollama状态",
                response.status_code,
            )
        except Exception as e:
            record_result("/ollama/status", "GET", False, str(e))

        # GET /ollama/recommended-models
        try:
            response = await client.get(f"{BASE_URL}/ollama/recommended-models", headers=headers)
            record_result(
                "/ollama/recommended-models",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/ollama/recommended-models", "GET", False, str(e))

        # 代理相关
        print("\n🤖 测试AI代理端点...")

        # POST /agents/deep-research
        if space_id:
            try:
                research_data = {
                    "query": "测试深度研究",
                    "space_id": space_id,
                    "research_type": "general"
                }
                response = await client.post(
                    f"{BASE_URL}/agents/deep-research", headers=headers, json=research_data
                )
                record_result(
                    "/agents/deep-research",
                    "POST",
                    response.status_code in [201, 400, 503],  # 可能需要配置
                    "深度研究",
                    response.status_code,
                )
            except Exception as e:
                record_result("/agents/deep-research", "POST", False, str(e))

        # GET /agents/tasks
        try:
            response = await client.get(f"{BASE_URL}/agents/tasks", headers=headers)
            record_result(
                "/agents/tasks",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/agents/tasks", "GET", False, str(e))

        # GET /agents/
        try:
            response = await client.get(f"{BASE_URL}/agents/", headers=headers)
            record_result(
                "/agents/",
                "GET",
                response.status_code == 200,
                "",
                response.status_code,
            )
        except Exception as e:
            record_result("/agents/", "GET", False, str(e))

        # 清理测试数据
        print("\n🧹 清理测试数据...")

        if citation_id:
            try:
                response = await client.delete(
                    f"{BASE_URL}/citations/{citation_id}", headers=headers
                )
                record_result(
                    f"/citations/{citation_id}",
                    "DELETE",
                    response.status_code == 204,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/citations/{citation_id}", "DELETE", False, str(e))

        if note_id:
            try:
                response = await client.delete(
                    f"{BASE_URL}/notes/{note_id}", headers=headers
                )
                record_result(
                    f"/notes/{note_id}",
                    "DELETE",
                    response.status_code == 204,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/notes/{note_id}", "DELETE", False, str(e))

        if conversation_id:
            try:
                response = await client.delete(
                    f"{BASE_URL}/chat/conversations/{conversation_id}", headers=headers
                )
                record_result(
                    f"/chat/conversations/{conversation_id}",
                    "DELETE",
                    response.status_code == 204,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(
                    f"/chat/conversations/{conversation_id}", "DELETE", False, str(e)
                )

        if space_id:
            try:
                response = await client.delete(
                    f"{BASE_URL}/spaces/{space_id}", headers=headers
                )
                record_result(
                    f"/spaces/{space_id}",
                    "DELETE",
                    response.status_code == 204,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result(f"/spaces/{space_id}", "DELETE", False, str(e))


async def main():
    """主测试函数"""
    print("🚀 开始完整API测试...\n")
    print("=" * 80)

    # 测试公开端点
    await test_public_endpoints()

    # 测试认证
    access_token, refresh_token = await test_auth_endpoints()

    if not access_token:
        print("\n❌ 无法获取认证令牌，请确保演示数据已创建")
        print("   运行: docker-compose exec backend python tools/demo_data.py create")
        return

    # 测试需要认证的端点
    await test_authenticated_endpoints(access_token)

    # 测试其他认证相关端点
    print("\n🔐 测试其他认证端点...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Authorization": f"Bearer {access_token}"}

        # POST /auth/change-password
        try:
            change_pwd_data = {
                "current_password": "Demo123456!",
                "new_password": "Demo123456!"  # 改回相同密码
            }
            response = await client.post(
                f"{BASE_URL}/auth/change-password",
                headers=headers,
                json=change_pwd_data
            )
            record_result(
                "/auth/change-password",
                "POST",
                response.status_code in [200, 400],  # 可能密码相同
                "修改密码",
                response.status_code
            )
        except Exception as e:
            record_result("/auth/change-password", "POST", False, str(e))

        # POST /auth/reset-password (测试请求重置)
        try:
            reset_data = {"email": "demo@example.com"}
            response = await client.post(
                f"{BASE_URL}/auth/reset-password",
                json=reset_data
            )
            record_result(
                "/auth/reset-password",
                "POST",
                response.status_code in [200, 404],  # 可能邮箱不存在
                "请求重置密码",
                response.status_code
            )
        except Exception as e:
            record_result("/auth/reset-password", "POST", False, str(e))

        # POST /auth/logout
        try:
            response = await client.post(
                f"{BASE_URL}/auth/logout",
                headers=headers
            )
            record_result(
                "/auth/logout",
                "POST",
                response.status_code == 200,
                "",
                response.status_code
            )
        except Exception as e:
            record_result("/auth/logout", "POST", False, str(e))

    # 测试刷新令牌
    if refresh_token:
        print("\n🔄 测试令牌刷新...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token}
                )
                record_result(
                    "/auth/refresh",
                    "POST",
                    response.status_code == 200,
                    "",
                    response.status_code,
                )
            except Exception as e:
                record_result("/auth/refresh", "POST", False, str(e))

    # 打印总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print(f"总测试数: {results['total']}")
    print(f"✅ 通过: {results['passed']}")
    print(f"❌ 失败: {results['failed']}")
    print(f"成功率: {results['passed'] / results['total'] * 100:.1f}%")

    if results["failed"] > 0:
        print("\n失败的测试:")
        for detail in results["details"]:
            if not detail["success"]:
                print(
                    f"  - {detail['method']} {detail['endpoint']}: {detail['message']}"
                )

    # 保存详细结果到文件
    with open("api_test_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n详细结果已保存到 api_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
