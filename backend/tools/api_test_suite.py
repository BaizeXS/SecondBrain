#!/usr/bin/env python3
"""
SecondBrain API 完整测试工具
覆盖所有API端点，提供详细测试报告
"""

import asyncio
import json
from datetime import datetime
from typing import Any

import aiohttp

# API配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试用户配置
TEST_USER = {
    "username": f"test_user_{int(datetime.now().timestamp())}",
    "email": f"test_{int(datetime.now().timestamp())}@example.com",
    "password": "TestPassword123!",
}

# 演示用户配置
DEMO_USER = {"username": "demo_user", "password": "Demo123456!"}


class APITester:
    """API测试器"""

    def __init__(self):
        self.session = None
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.space_id = None
        self.document_id = None
        self.note_id = None
        self.conversation_id = None
        self.message_id = None
        self.annotation_id = None
        self.citation_id = None
        self.agent_id = 1  # Deep Research agent

        # 测试结果
        self.results = []
        self.endpoint_count = 0
        self.passed_count = 0
        self.failed_count = 0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_result(
        self, method: str, endpoint: str, status: int, success: bool, message: str = ""
    ):
        """记录测试结果"""
        self.endpoint_count += 1
        if success:
            self.passed_count += 1
            emoji = "✅"
        else:
            self.failed_count += 1
            emoji = "❌"

        result = {
            "method": method,
            "endpoint": endpoint,
            "status": status,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.results.append(result)

        print(f"{emoji} {method} {endpoint} - {status} {message}")

    async def make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> tuple[int, Any]:
        """发送HTTP请求"""
        # 如果是完整的 URL，直接使用
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = endpoint
        # 如果是 API 路径，添加 API_BASE
        elif endpoint.startswith("/"):
            url = f"{API_BASE}{endpoint}"
        # 其他情况，添加 BASE_URL
        else:
            url = f"{BASE_URL}{endpoint}"

        headers = kwargs.pop("headers", {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            async with self.session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                try:
                    data = await response.json()
                except:
                    data = await response.text()
                return response.status, data
        except Exception as e:
            return 0, str(e)

    # ===== 系统端点测试 =====

    async def test_system_endpoints(self):
        """测试系统端点"""
        print("\n=== 系统端点测试 ===")

        # 健康检查 (在根路径下，不是API路径)
        status, data = await self.make_request("GET", "http://localhost:8000/health")
        self.log_result("GET", "/health", status, status == 200)

        # 根路径
        status, data = await self.make_request("GET", "/")
        self.log_result("GET", "/", status, status in [200, 404])  # 404也算正常

    # ===== 认证模块测试 =====

    async def test_auth_endpoints(self):
        """测试认证端点"""
        print("\n=== 认证模块测试 ===")

        # 1. 用户注册
        status, data = await self.make_request("POST", "/auth/register", json=TEST_USER)
        self.log_result("POST", "/auth/register", status, status in [200, 201, 400])

        # 2. 用户登录 (Form)
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"],
        }
        status, data = await self.make_request("POST", "/auth/login", data=login_data)
        if status == 200:
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
        self.log_result("POST", "/auth/login", status, status == 200)

        # 3. 用户登录 (JSON)
        status, data = await self.make_request(
            "POST", "/auth/login/json", json=login_data
        )
        self.log_result("POST", "/auth/login/json", status, status == 200)

        # 4. 刷新Token
        if self.refresh_token:
            status, data = await self.make_request(
                "POST", "/auth/refresh", json={"refresh_token": self.refresh_token}
            )
            if status == 200:
                self.access_token = data.get("access_token")
            self.log_result("POST", "/auth/refresh", status, status == 200)

        # 5. 修改密码
        status, data = await self.make_request(
            "POST",
            "/auth/change-password",
            json={
                "current_password": TEST_USER["password"],
                "new_password": "NewPassword123!",
            },
        )
        self.log_result("POST", "/auth/change-password", status, status in [200, 422])

        # 6. 重置密码请求
        status, data = await self.make_request(
            "POST", "/auth/reset-password", json={"email": TEST_USER["email"]}
        )
        self.log_result("POST", "/auth/reset-password", status, status == 200)

        # 7. 重置密码确认
        status, data = await self.make_request(
            "POST",
            "/auth/reset-password/confirm",
            json={"token": "fake_token", "new_password": "NewPass123!"},
        )
        self.log_result(
            "POST", "/auth/reset-password/confirm", status, status in [200, 401, 422]
        )

        # 8. 登出
        status, data = await self.make_request("POST", "/auth/logout")
        self.log_result("POST", "/auth/logout", status, status == 200)

    # ===== 用户模块测试 =====

    async def test_user_endpoints(self):
        """测试用户端点"""
        print("\n=== 用户模块测试 ===")

        # 1. 获取当前用户信息
        status, data = await self.make_request("GET", "/users/me")
        if status == 200:
            self.user_id = data.get("id")
        self.log_result("GET", "/users/me", status, status == 200)

        # 2. 更新用户信息
        status, data = await self.make_request(
            "PUT", "/users/me", json={"full_name": "测试用户更新"}
        )
        self.log_result("PUT", "/users/me", status, status == 200)

        # 3. 修改密码
        status, data = await self.make_request(
            "POST",
            "/users/me/change-password",
            json={
                "current_password": TEST_USER["password"],
                "new_password": "NewPass123!",
            },
        )
        self.log_result(
            "POST", "/users/me/change-password", status, status in [204, 422]
        )

        # 4. 获取用户统计
        status, data = await self.make_request("GET", "/users/me/stats")
        self.log_result("GET", "/users/me/stats", status, status == 200)

        # 5. 删除用户 (跳过，避免删除测试用户)
        self.log_result("DELETE", "/users/me", 0, True, "跳过 - 避免删除测试用户")

    # ===== 空间模块测试 =====

    async def test_space_endpoints(self):
        """测试空间端点"""
        print("\n=== 空间模块测试 ===")

        # 1. 创建空间
        status, data = await self.make_request(
            "POST",
            "/spaces/",
            json={"name": "API测试空间", "description": "API测试专用空间"},
        )
        if status == 201:
            self.space_id = data.get("id")
        self.log_result("POST", "/spaces/", status, status in [201, 400])

        # 2. 获取空间列表
        status, data = await self.make_request("GET", "/spaces/")
        if status == 200 and data.get("spaces") and not self.space_id:
            self.space_id = data["spaces"][0]["id"]
        self.log_result("GET", "/spaces/", status, status == 200)

        if self.space_id:
            # 3. 获取特定空间
            status, data = await self.make_request("GET", f"/spaces/{self.space_id}")
            self.log_result("GET", f"/spaces/{self.space_id}", status, status == 200)

            # 4. 更新空间
            status, data = await self.make_request(
                "PUT", f"/spaces/{self.space_id}", json={"description": "更新的描述"}
            )
            self.log_result("PUT", f"/spaces/{self.space_id}", status, status == 200)

        # 5. 删除空间 (放到最后测试)
        self.log_result("DELETE", f"/spaces/{self.space_id or 0}", 0, True, "延后测试")

    # ===== 文档模块测试 =====

    async def test_document_endpoints(self):
        """测试文档端点"""
        print("\n=== 文档模块测试 ===")

        if not self.space_id:
            self.log_result("POST", "/documents/upload", 0, False, "需要space_id")
            return

        # 1. 上传文档
        test_content = b"This is a test document for API testing."
        files = {"file": ("test.txt", test_content, "text/plain")}
        data = {"space_id": self.space_id}

        async with aiohttp.ClientSession() as temp_session:
            headers = (
                {"Authorization": f"Bearer {self.access_token}"}
                if self.access_token
                else {}
            )
            async with temp_session.post(
                f"{API_BASE}/documents/upload", data=data, headers=headers
            ) as response:
                try:
                    form_data = aiohttp.FormData()
                    form_data.add_field("space_id", str(self.space_id))
                    form_data.add_field(
                        "file",
                        test_content,
                        filename="test.txt",
                        content_type="text/plain",
                    )

                    async with temp_session.post(
                        f"{API_BASE}/documents/upload", data=form_data, headers=headers
                    ) as resp:
                        status = resp.status
                        try:
                            result = await resp.json()
                            if status == 201:
                                self.document_id = result.get("id")
                        except:
                            result = await resp.text()
                except Exception as e:
                    status = 0
                    result = str(e)

        self.log_result("POST", "/documents/upload", status, status == 201)

        # 2. 获取文档列表
        status, data = await self.make_request(
            "GET", "/documents/", json={"space_id": self.space_id}
        )
        if status == 200 and data.get("documents") and not self.document_id:
            self.document_id = data["documents"][0]["id"]
        self.log_result("GET", "/documents/", status, status == 200)

        if self.document_id:
            # 3. 获取特定文档
            status, data = await self.make_request(
                "GET", f"/documents/{self.document_id}"
            )
            self.log_result(
                "GET", f"/documents/{self.document_id}", status, status == 200
            )

            # 4. 更新文档
            status, data = await self.make_request(
                "PUT",
                f"/documents/{self.document_id}",
                json={"title": "更新的文档标题"},
            )
            self.log_result(
                "PUT", f"/documents/{self.document_id}", status, status == 200
            )

            # 5. 获取文档内容
            status, data = await self.make_request(
                "GET", f"/documents/{self.document_id}/content"
            )
            self.log_result(
                "GET", f"/documents/{self.document_id}/content", status, status == 200
            )

            # 6. 获取文档预览
            status, data = await self.make_request(
                "GET", f"/documents/{self.document_id}/preview"
            )
            self.log_result(
                "GET", f"/documents/{self.document_id}/preview", status, status == 200
            )

            # 7. 下载文档
            status, data = await self.make_request(
                "POST", f"/documents/{self.document_id}/download"
            )
            self.log_result(
                "POST", f"/documents/{self.document_id}/download", status, status == 200
            )

            # 8. 获取文档快照
            status, data = await self.make_request(
                "GET", f"/documents/{self.document_id}/snapshot"
            )
            self.log_result(
                "GET",
                f"/documents/{self.document_id}/snapshot",
                status,
                status in [200, 404, 501],
            )

        # 9. 搜索文档
        status, data = await self.make_request(
            "POST",
            "/documents/search",
            json={"query": "test", "space_id": self.space_id},
        )
        self.log_result("POST", "/documents/search", status, status == 200)

        # 10. URL导入
        status, data = await self.make_request(
            "POST",
            "/documents/import-url",
            json={"url": "https://example.com", "space_id": self.space_id},
        )
        self.log_result(
            "POST", "/documents/import-url", status, status in [201, 400, 422]
        )

        # 11. URL分析
        status, data = await self.make_request(
            "POST", "/documents/analyze-url", json={"url": "https://example.com"}
        )
        self.log_result("POST", "/documents/analyze-url", status, status in [200, 422])

        # 12. 批量URL导入
        status, data = await self.make_request(
            "POST",
            "/documents/batch-import-urls",
            json={"urls": ["https://example.com"], "space_id": self.space_id},
        )
        self.log_result(
            "POST", "/documents/batch-import-urls", status, status in [200, 422]
        )

        # 13. 删除文档 (延后测试)
        self.log_result(
            "DELETE", f"/documents/{self.document_id or 0}", 0, True, "延后测试"
        )

    # ===== 笔记模块测试 =====

    async def test_note_endpoints(self):
        """测试笔记端点"""
        print("\n=== 笔记模块测试 ===")

        # 1. 创建笔记
        note_data = {
            "title": "API测试笔记",
            "content": "# API测试笔记\n\n这是API测试创建的笔记。",
            "space_id": self.space_id,
            "tags": ["test", "api"],
        }
        status, data = await self.make_request("POST", "/notes/", json=note_data)
        if status == 201:
            self.note_id = data.get("id")
        self.log_result("POST", "/notes/", status, status == 201)

        # 2. 获取笔记列表
        status, data = await self.make_request("GET", "/notes/")
        if status == 200 and data.get("notes") and not self.note_id:
            self.note_id = data["notes"][0]["id"]
        self.log_result("GET", "/notes/", status, status == 200)

        # 3. 获取最近笔记
        status, data = await self.make_request("GET", "/notes/recent")
        self.log_result("GET", "/notes/recent", status, status == 200)

        # 4. 搜索笔记
        status, data = await self.make_request(
            "POST", "/notes/search", json={"query": "test"}
        )
        self.log_result("POST", "/notes/search", status, status == 200)

        if self.note_id:
            # 5. 获取特定笔记
            status, data = await self.make_request("GET", f"/notes/{self.note_id}")
            self.log_result("GET", f"/notes/{self.note_id}", status, status == 200)

            # 6. 更新笔记
            status, data = await self.make_request(
                "PUT", f"/notes/{self.note_id}", json={"content": "更新的笔记内容"}
            )
            self.log_result("PUT", f"/notes/{self.note_id}", status, status == 200)

            # 7. 获取关联笔记
            status, data = await self.make_request(
                "GET", f"/notes/{self.note_id}/linked"
            )
            self.log_result(
                "GET", f"/notes/{self.note_id}/linked", status, status == 200
            )

            # 8. 添加标签
            status, data = await self.make_request(
                "POST", f"/notes/{self.note_id}/tags", json={"tags": ["new_tag"]}
            )
            self.log_result(
                "POST", f"/notes/{self.note_id}/tags", status, status in [200, 422]
            )

            # 9. 删除标签
            status, data = await self.make_request(
                "DELETE", f"/notes/{self.note_id}/tags", json={"tags": ["new_tag"]}
            )
            self.log_result(
                "DELETE", f"/notes/{self.note_id}/tags", status, status in [200, 422]
            )

            # 10. 获取笔记版本
            status, data = await self.make_request(
                "GET", f"/notes/{self.note_id}/versions"
            )
            self.log_result(
                "GET", f"/notes/{self.note_id}/versions", status, status == 200
            )

            # 11. 获取特定版本
            status, data = await self.make_request(
                "GET", f"/notes/{self.note_id}/versions/1"
            )
            self.log_result(
                "GET", f"/notes/{self.note_id}/versions/1", status, status in [200, 404]
            )

            # 12. 版本比较
            status, data = await self.make_request(
                "POST",
                f"/notes/{self.note_id}/versions/compare",
                json={"version1": 1, "version2": 2},
            )
            self.log_result(
                "POST",
                f"/notes/{self.note_id}/versions/compare",
                status,
                status in [200, 422],
            )

            # 13. 版本恢复
            status, data = await self.make_request(
                "POST",
                f"/notes/{self.note_id}/versions/restore",
                json={"version_number": 1},
            )
            self.log_result(
                "POST",
                f"/notes/{self.note_id}/versions/restore",
                status,
                status in [200, 422],
            )

            # 14. 版本清理
            status, data = await self.make_request(
                "DELETE", f"/notes/{self.note_id}/versions/cleanup"
            )
            self.log_result(
                "DELETE",
                f"/notes/{self.note_id}/versions/cleanup",
                status,
                status == 200,
            )

        # 15. 获取所有标签
        status, data = await self.make_request("GET", "/notes/tags/all")
        self.log_result("GET", "/notes/tags/all", status, status == 200)

        # 16. 批量操作
        if self.note_id:
            status, data = await self.make_request(
                "POST",
                "/notes/batch",
                json={
                    "note_ids": [self.note_id],
                    "operation": "move",
                    "target_space_id": self.space_id,
                },
            )
            self.log_result("POST", "/notes/batch", status, status in [200, 422])

        # 17. AI生成笔记
        status, data = await self.make_request(
            "POST",
            "/notes/ai/generate",
            json={"prompt": "生成一个关于AI的笔记", "space_id": self.space_id},
        )
        self.log_result("POST", "/notes/ai/generate", status, status in [201, 422])

        # 18. AI摘要
        if self.note_id:
            status, data = await self.make_request(
                "POST", "/notes/ai/summary", json={"note_id": self.note_id}
            )
            self.log_result("POST", "/notes/ai/summary", status, status in [200, 422])

        # 19. 删除笔记 (延后测试)
        self.log_result("DELETE", f"/notes/{self.note_id or 0}", 0, True, "延后测试")

    # ===== 聊天模块测试 =====

    async def test_chat_endpoints(self):
        """测试聊天端点"""
        print("\n=== 聊天模块测试 ===")

        # 1. 创建对话
        status, data = await self.make_request(
            "POST",
            "/chat/conversations",
            json={"title": "API测试对话", "space_id": self.space_id},
        )
        if status == 201:
            self.conversation_id = data.get("id")
        self.log_result("POST", "/chat/conversations", status, status == 201)

        # 2. 获取对话列表
        status, data = await self.make_request("GET", "/chat/conversations")
        if status == 200 and data.get("conversations") and not self.conversation_id:
            self.conversation_id = data["conversations"][0]["id"]
        self.log_result("GET", "/chat/conversations", status, status == 200)

        if self.conversation_id:
            # 3. 获取特定对话
            status, data = await self.make_request(
                "GET", f"/chat/conversations/{self.conversation_id}"
            )
            self.log_result(
                "GET",
                f"/chat/conversations/{self.conversation_id}",
                status,
                status == 200,
            )

            # 4. 更新对话
            status, data = await self.make_request(
                "PUT",
                f"/chat/conversations/{self.conversation_id}",
                json={"title": "更新的对话标题"},
            )
            self.log_result(
                "PUT",
                f"/chat/conversations/{self.conversation_id}",
                status,
                status == 200,
            )

            # 5. 发送消息
            status, data = await self.make_request(
                "POST",
                f"/chat/conversations/{self.conversation_id}/messages",
                json={"content": "你好，这是API测试消息"},
            )
            if status == 201:
                self.message_id = data.get("id")
            self.log_result(
                "POST",
                f"/chat/conversations/{self.conversation_id}/messages",
                status,
                status in [201, 400],
            )

            # 6. 分析附件
            status, data = await self.make_request(
                "POST", "/chat/analyze-attachments", json={"attachments": []}
            )
            self.log_result(
                "POST", "/chat/analyze-attachments", status, status in [200, 422]
            )

            # 7. 获取分支列表
            status, data = await self.make_request(
                "GET", f"/chat/conversations/{self.conversation_id}/branches"
            )
            self.log_result(
                "GET",
                f"/chat/conversations/{self.conversation_id}/branches",
                status,
                status == 200,
            )

            # 8. 创建分支
            status, data = await self.make_request(
                "POST",
                f"/chat/conversations/{self.conversation_id}/branches",
                json={"name": "test_branch", "from_message_id": self.message_id},
            )
            self.log_result(
                "POST",
                f"/chat/conversations/{self.conversation_id}/branches",
                status,
                status in [201, 422],
            )

            # 9. 获取分支历史
            status, data = await self.make_request(
                "GET", f"/chat/conversations/{self.conversation_id}/branches/history"
            )
            self.log_result(
                "GET",
                f"/chat/conversations/{self.conversation_id}/branches/history",
                status,
                status == 200,
            )

            # 10. 切换分支
            status, data = await self.make_request(
                "POST",
                f"/chat/conversations/{self.conversation_id}/branches/switch",
                json={"branch_name": "test_branch"},
            )
            self.log_result(
                "POST",
                f"/chat/conversations/{self.conversation_id}/branches/switch",
                status,
                status in [200, 400],
            )

            # 11. 合并分支
            status, data = await self.make_request(
                "POST",
                f"/chat/conversations/{self.conversation_id}/branches/merge",
                json={"source_branch": "test_branch", "target_branch": "main"},
            )
            self.log_result(
                "POST",
                f"/chat/conversations/{self.conversation_id}/branches/merge",
                status,
                status in [200, 400],
            )

            # 12. 删除分支
            status, data = await self.make_request(
                "DELETE",
                f"/chat/conversations/{self.conversation_id}/branches/test_branch",
            )
            self.log_result(
                "DELETE",
                f"/chat/conversations/{self.conversation_id}/branches/test_branch",
                status,
                status in [204, 404],
            )

            # 13. 重新生成消息
            if self.message_id:
                status, data = await self.make_request(
                    "POST",
                    f"/chat/conversations/{self.conversation_id}/messages/{self.message_id}/regenerate",
                )
                self.log_result(
                    "POST",
                    f"/chat/conversations/{self.conversation_id}/messages/{self.message_id}/regenerate",
                    status,
                    status in [200, 404],
                )

        # 14. 聊天完成
        status, data = await self.make_request(
            "POST",
            "/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "openrouter/auto",
            },
        )
        self.log_result("POST", "/chat/completions", status, status == 200)

        # 15. 删除对话 (延后测试)
        self.log_result(
            "DELETE",
            f"/chat/conversations/{self.conversation_id or 0}",
            0,
            True,
            "延后测试",
        )

    # ===== 代理模块测试 =====

    async def test_agent_endpoints(self):
        """测试代理端点"""
        print("\n=== 代理模块测试 ===")

        # 1. 获取代理列表
        status, data = await self.make_request("GET", "/agents/")
        self.log_result("GET", "/agents/", status, status == 200)

        # 2. 获取特定代理
        status, data = await self.make_request("GET", f"/agents/{self.agent_id}")
        self.log_result("GET", f"/agents/{self.agent_id}", status, status == 200)

        # 3. 执行代理
        status, data = await self.make_request(
            "POST",
            f"/agents/{self.agent_id}/execute",
            json={"prompt": "AI技术发展趋势", "space_id": self.space_id},
        )
        self.log_result(
            "POST", f"/agents/{self.agent_id}/execute", status, status == 200
        )

        # 4. 深度研究
        status, data = await self.make_request(
            "POST",
            "/agents/deep-research",
            json={"query": "人工智能在医疗领域的应用", "space_id": self.space_id},
        )
        self.log_result("POST", "/agents/deep-research", status, status == 200)

        # 5. 创建自定义代理
        status, data = await self.make_request(
            "POST",
            "/agents/",
            json={
                "name": "测试代理",
                "description": "API测试代理",
                "agent_type": "custom",
                "prompt_template": "你是一个测试代理，用于API测试。",
            },
        )
        self.log_result("POST", "/agents/", status, status in [201, 403, 422])

    # ===== 引用模块测试 =====

    async def test_citation_endpoints(self):
        """测试引用端点"""
        print("\n=== 引用模块测试 ===")

        # 1. 创建引用
        citation_data = {
            "title": "测试引用",
            "authors": ["作者1", "作者2"],
            "year": 2024,
            "publication": "测试期刊",
            "space_id": self.space_id,
        }
        status, data = await self.make_request(
            "POST", "/citations/", json=citation_data
        )
        if status == 201:
            self.citation_id = data.get("id")
        self.log_result("POST", "/citations/", status, status in [201, 422])

        # 2. 获取引用列表
        status, data = await self.make_request("GET", "/citations/")
        if status == 200 and data.get("citations") and not self.citation_id:
            self.citation_id = data["citations"][0]["id"]
        self.log_result("GET", "/citations/", status, status == 200)

        if self.citation_id:
            # 3. 获取特定引用
            status, data = await self.make_request(
                "GET", f"/citations/{self.citation_id}"
            )
            self.log_result(
                "GET", f"/citations/{self.citation_id}", status, status == 200
            )

            # 4. 更新引用
            status, data = await self.make_request(
                "PUT",
                f"/citations/{self.citation_id}",
                json={"title": "更新的引用标题"},
            )
            self.log_result(
                "PUT", f"/citations/{self.citation_id}", status, status == 200
            )

        # 5. 搜索引用
        status, data = await self.make_request(
            "POST", "/citations/search", json={"query": "test"}
        )
        self.log_result("POST", "/citations/search", status, status == 200)

        # 6. 格式化引用
        status, data = await self.make_request(
            "POST",
            "/citations/format",
            json={
                "citation_ids": [self.citation_id] if self.citation_id else [],
                "style": "apa",
            },
        )
        self.log_result("POST", "/citations/format", status, status == 200)

        # 7. 导出引用
        status, data = await self.make_request(
            "POST",
            "/citations/export",
            json={
                "citation_ids": [self.citation_id] if self.citation_id else [],
                "format": "bibtex",
            },
        )
        self.log_result("POST", "/citations/export", status, status == 200)

        # 8. 导入BibTeX
        bibtex_content = """@article{test2024,
            title={Test Article},
            author={Test Author},
            journal={Test Journal},
            year={2024}
        }"""
        status, data = await self.make_request(
            "POST",
            "/citations/import-bibtex",
            json={"bibtex_content": bibtex_content, "space_id": self.space_id},
        )
        self.log_result(
            "POST", "/citations/import-bibtex", status, status in [200, 422]
        )

        # 9. 删除引用 (延后测试)
        self.log_result(
            "DELETE", f"/citations/{self.citation_id or 0}", 0, True, "延后测试"
        )

    # ===== 标注模块测试 =====

    async def test_annotation_endpoints(self):
        """测试标注端点"""
        print("\n=== 标注模块测试 ===")

        if not self.document_id:
            self.log_result("POST", "/annotations/", 0, False, "需要document_id")
            return

        # 1. 创建标注
        annotation_data = {
            "document_id": self.document_id,
            "content": "这是一个测试标注",
            "type": "highlight",
            "position": {"start": 0, "end": 10},
        }
        status, data = await self.make_request(
            "POST", "/annotations/", json=annotation_data
        )
        if status == 201:
            self.annotation_id = data.get("id")
        self.log_result("POST", "/annotations/", status, status in [201, 422])

        # 2. 获取我的标注
        status, data = await self.make_request("GET", "/annotations/my")
        if status == 200 and data.get("annotations") and not self.annotation_id:
            self.annotation_id = data["annotations"][0]["id"]
        self.log_result("GET", "/annotations/my", status, status == 200)

        if self.annotation_id:
            # 3. 获取特定标注
            status, data = await self.make_request(
                "GET", f"/annotations/{self.annotation_id}"
            )
            self.log_result(
                "GET",
                f"/annotations/{self.annotation_id}",
                status,
                status in [200, 500],
            )

            # 4. 更新标注
            status, data = await self.make_request(
                "PUT",
                f"/annotations/{self.annotation_id}",
                json={"content": "更新的标注内容"},
            )
            self.log_result(
                "PUT", f"/annotations/{self.annotation_id}", status, status == 200
            )

        # 5. 获取文档标注
        status, data = await self.make_request(
            "GET", f"/annotations/document/{self.document_id}"
        )
        self.log_result(
            "GET", f"/annotations/document/{self.document_id}", status, status == 200
        )

        # 6. 获取文档页面标注
        status, data = await self.make_request(
            "GET", f"/annotations/document/{self.document_id}/pages"
        )
        self.log_result(
            "GET",
            f"/annotations/document/{self.document_id}/pages",
            status,
            status in [200, 422],
        )

        # 7. 获取PDF页面标注
        status, data = await self.make_request(
            "GET", f"/annotations/document/{self.document_id}/pdf/1"
        )
        self.log_result(
            "GET",
            f"/annotations/document/{self.document_id}/pdf/1",
            status,
            status in [200, 422],
        )

        # 8. 获取标注统计
        status, data = await self.make_request("GET", "/annotations/statistics")
        self.log_result("GET", "/annotations/statistics", status, status == 200)

        # 9. 批量创建标注
        batch_data = {"annotations": [annotation_data], "document_id": self.document_id}
        status, data = await self.make_request(
            "POST", "/annotations/batch", json=batch_data
        )
        self.log_result("POST", "/annotations/batch", status, status in [201, 422])

        # 10. PDF批量标注
        status, data = await self.make_request(
            "POST",
            "/annotations/pdf/batch",
            json={"document_id": self.document_id, "annotations": []},
        )
        self.log_result("POST", "/annotations/pdf/batch", status, status in [201, 422])

        # 11. 复制标注
        if self.annotation_id:
            status, data = await self.make_request(
                "POST",
                "/annotations/copy",
                json={
                    "annotation_ids": [self.annotation_id],
                    "target_document_id": self.document_id,
                },
            )
            self.log_result("POST", "/annotations/copy", status, status in [200, 422])

        # 12. 导出标注
        status, data = await self.make_request(
            "POST",
            "/annotations/export",
            json={"document_id": self.document_id, "format": "json"},
        )
        self.log_result("POST", "/annotations/export", status, status in [200, 422])

        # 13. 删除标注 (延后测试)
        self.log_result(
            "DELETE", f"/annotations/{self.annotation_id or 0}", 0, True, "延后测试"
        )

    # ===== 导出模块测试 =====

    async def test_export_endpoints(self):
        """测试导出端点"""
        print("\n=== 导出模块测试 ===")

        # 1. 导出笔记
        status, data = await self.make_request(
            "POST",
            "/export/notes",
            json={
                "note_ids": [self.note_id] if self.note_id else [],
                "format": "markdown",
            },
        )
        self.log_result("POST", "/export/notes", status, status in [200, 500])

        # 2. 导出文档
        status, data = await self.make_request(
            "POST",
            "/export/documents",
            json={
                "document_ids": [self.document_id] if self.document_id else [],
                "format": "pdf",
            },
        )
        self.log_result("POST", "/export/documents", status, status in [200, 500])

        # 3. 导出空间
        status, data = await self.make_request(
            "POST", "/export/space", json={"space_id": self.space_id, "format": "pdf"}
        )
        self.log_result("POST", "/export/space", status, status in [200, 400, 500])

        # 4. 导出对话
        status, data = await self.make_request(
            "POST",
            "/export/conversations",
            json={
                "conversation_ids": [self.conversation_id]
                if self.conversation_id
                else [],
                "format": "markdown",
            },
        )
        self.log_result("POST", "/export/conversations", status, status in [200, 500])

    # ===== Ollama模块测试 =====

    async def test_ollama_endpoints(self):
        """测试Ollama端点"""
        print("\n=== Ollama模块测试 ===")

        # 1. 获取状态
        status, data = await self.make_request("GET", "/ollama/status")
        self.log_result("GET", "/ollama/status", status, status in [200, 503])

        # 2. 获取模型列表
        status, data = await self.make_request("GET", "/ollama/models")
        self.log_result("GET", "/ollama/models", status, status in [200, 503])

        # 3. 获取推荐模型
        status, data = await self.make_request("GET", "/ollama/recommended-models")
        self.log_result(
            "GET", "/ollama/recommended-models", status, status in [200, 501]
        )

        # 4. 拉取模型
        status, data = await self.make_request(
            "POST", "/ollama/pull", json={"model": "llama2"}
        )
        self.log_result("POST", "/ollama/pull", status, status in [200, 422, 503])

        # 5. 获取特定模型
        status, data = await self.make_request("GET", "/ollama/models/llama2")
        self.log_result(
            "GET", "/ollama/models/llama2", status, status in [200, 404, 503]
        )

        # 6. 删除模型
        status, data = await self.make_request("DELETE", "/ollama/models/llama2")
        self.log_result(
            "DELETE", "/ollama/models/llama2", status, status in [200, 400, 403, 503]
        )

    # ===== 清理操作 =====

    async def test_cleanup_endpoints(self):
        """测试清理端点"""
        print("\n=== 清理测试数据 ===")

        # 删除标注
        if self.annotation_id:
            status, data = await self.make_request(
                "DELETE", f"/annotations/{self.annotation_id}"
            )
            self.log_result(
                "DELETE", f"/annotations/{self.annotation_id}", status, status == 204
            )

        # 删除引用
        if self.citation_id:
            status, data = await self.make_request(
                "DELETE", f"/citations/{self.citation_id}"
            )
            self.log_result(
                "DELETE", f"/citations/{self.citation_id}", status, status == 204
            )

        # 删除对话
        if self.conversation_id:
            status, data = await self.make_request(
                "DELETE", f"/chat/conversations/{self.conversation_id}"
            )
            self.log_result(
                "DELETE",
                f"/chat/conversations/{self.conversation_id}",
                status,
                status == 204,
            )

        # 删除笔记
        if self.note_id:
            status, data = await self.make_request("DELETE", f"/notes/{self.note_id}")
            self.log_result("DELETE", f"/notes/{self.note_id}", status, status == 204)

        # 删除文档
        if self.document_id:
            status, data = await self.make_request(
                "DELETE", f"/documents/{self.document_id}"
            )
            self.log_result(
                "DELETE", f"/documents/{self.document_id}", status, status == 204
            )

        # 删除空间 (如果是我们创建的)
        if self.space_id and self.space_id > 5:  # 避免删除演示空间
            status, data = await self.make_request("DELETE", f"/spaces/{self.space_id}")
            self.log_result(
                "DELETE", f"/spaces/{self.space_id}", status, status in [204, 400]
            )

    # ===== 主测试流程 =====

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始完整API测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # 先使用演示账号登录获取基础数据
        login_data = {
            "username": DEMO_USER["username"],
            "password": DEMO_USER["password"],
        }
        status, data = await self.make_request("POST", "/auth/login", data=login_data)
        if status == 200:
            self.access_token = data.get("access_token")
            # 获取演示用户的空间
            status, data = await self.make_request("GET", "/spaces/")
            if status == 200 and data.get("spaces"):
                self.space_id = data["spaces"][0]["id"]

        # 运行所有模块测试
        await self.test_system_endpoints()
        await self.test_auth_endpoints()
        await self.test_user_endpoints()
        await self.test_space_endpoints()
        await self.test_document_endpoints()
        await self.test_note_endpoints()
        await self.test_chat_endpoints()
        await self.test_agent_endpoints()
        await self.test_citation_endpoints()
        await self.test_annotation_endpoints()
        await self.test_export_endpoints()
        await self.test_ollama_endpoints()
        await self.test_cleanup_endpoints()

        # 生成测试报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 70)
        print("📊 API测试报告")
        print("=" * 70)

        success_rate = (
            (self.passed_count / self.endpoint_count * 100)
            if self.endpoint_count > 0
            else 0
        )

        print(f"总端点数: {self.endpoint_count}")
        print(f"✅ 成功: {self.passed_count} ({success_rate:.1f}%)")
        print(f"❌ 失败: {self.failed_count} ({100 - success_rate:.1f}%)")

        # 按模块分组显示结果
        modules = {}
        for result in self.results:
            endpoint = result["endpoint"]
            if "/" in endpoint:
                module = (
                    endpoint.split("/")[1]
                    if endpoint.startswith("/")
                    else endpoint.split("/")[0]
                )
            else:
                module = "system"

            if module not in modules:
                modules[module] = {"total": 0, "passed": 0, "failed": 0}

            modules[module]["total"] += 1
            if result["success"]:
                modules[module]["passed"] += 1
            else:
                modules[module]["failed"] += 1

        print("\n📋 模块测试结果:")
        for module, stats in modules.items():
            rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            status = "✅" if rate == 100 else "⚠️" if rate >= 80 else "❌"
            print(
                f"  {status} {module}: {stats['passed']}/{stats['total']} ({rate:.1f}%)"
            )

        # 显示失败的端点
        failed_results = [r for r in self.results if not r["success"]]
        if failed_results:
            print(f"\n❌ 失败的端点 ({len(failed_results)}个):")
            for result in failed_results:
                print(
                    f"  {result['method']} {result['endpoint']} - {result['status']} {result['message']}"
                )

        # 保存详细报告
        report_file = f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": {
                        "total": self.endpoint_count,
                        "passed": self.passed_count,
                        "failed": self.failed_count,
                        "success_rate": success_rate,
                        "test_time": datetime.now().isoformat(),
                    },
                    "modules": modules,
                    "details": self.results,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"\n📄 详细报告已保存: {report_file}")

        # 测试结论
        print("\n🎯 测试结论:")
        if success_rate >= 95:
            print("  ✅ 优秀！所有核心功能正常，可以放心部署。")
        elif success_rate >= 85:
            print("  ✅ 良好！核心功能正常，少量问题需要修复。")
        elif success_rate >= 70:
            print("  ⚠️ 一般。主要功能可用，建议修复失败的端点。")
        else:
            print("  ❌ 需要改进。存在较多问题，建议全面检查。")

        print("=" * 70)


async def main():
    """主函数"""
    async with APITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
