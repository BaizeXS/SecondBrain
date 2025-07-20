#!/usr/bin/env python3
"""
SecondBrain 后端完整功能测试（最终版）
测试所有API端点的真实功能，确保系统正常工作
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any

import aiohttp

# API配置
API_BASE = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"

# 测试账号
TEST_USER = {
    "username": "test_user_" + str(int(time.time())),
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "full_name": "测试用户",
}

# 演示账号（已存在）
DEMO_USER = {"username": "demo_user", "password": "Demo123456!"}


class APITester:
    def __init__(self):
        self.session = None
        self.access_token = None
        self.user_id = None
        self.conversation_id = None
        self.space_id = None
        self.document_id = None
        self.note_id = None
        self.agent_id = None
        self.test_results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def add_result(
        self, test_name: str, success: bool, message: str, details: Any = None
    ):
        """记录测试结果"""
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "message": message,
                "details": details,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # 实时输出
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   详情: {details}")

    async def test_health_check(self):
        """测试健康检查"""
        try:
            async with self.session.get(HEALTH_URL) as response:
                data = await response.json()
                if response.status == 200:
                    self.add_result("健康检查", True, "后端服务正常运行", data)
                else:
                    self.add_result(
                        "健康检查", False, f"状态码: {response.status}", data
                    )
        except Exception as e:
            self.add_result("健康检查", False, f"连接失败: {str(e)}")

    async def test_user_registration(self):
        """测试用户注册"""
        try:
            async with self.session.post(
                f"{API_BASE}/auth/register", json=TEST_USER
            ) as response:
                data = await response.json()
                if response.status in [200, 201]:
                    self.user_id = data.get("id")
                    self.add_result(
                        "用户注册",
                        True,
                        f"注册成功: {TEST_USER['username']}",
                        {"user_id": self.user_id, "username": data.get("username")},
                    )
                else:
                    self.add_result(
                        "用户注册",
                        False,
                        f"注册失败: {data.get('detail', '未知错误')}",
                        data,
                    )
        except Exception as e:
            self.add_result("用户注册", False, f"请求失败: {str(e)}")

    async def test_user_login(self, use_demo=False):
        """测试用户登录"""
        user = DEMO_USER if use_demo else TEST_USER
        test_name = "演示账号登录" if use_demo else "新用户登录"

        try:
            # 登录使用 FormData
            form_data = aiohttp.FormData()
            form_data.add_field("username", user["username"])
            form_data.add_field("password", user["password"])

            async with self.session.post(
                f"{API_BASE}/auth/login", data=form_data
            ) as response:
                data = await response.json()
                if response.status == 200:
                    self.access_token = data.get("access_token")
                    self.add_result(
                        test_name,
                        True,
                        f"登录成功: {user['username']}",
                        {
                            "token_type": data.get("token_type"),
                            "has_access_token": bool(self.access_token),
                        },
                    )
                else:
                    self.add_result(
                        test_name,
                        False,
                        f"登录失败: {data.get('detail', '未知错误')}",
                        data,
                    )
        except Exception as e:
            self.add_result(test_name, False, f"请求失败: {str(e)}")

    async def test_get_user_info(self):
        """测试获取用户信息"""
        if not self.access_token:
            self.add_result("获取用户信息", False, "需要先登录")
            return

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(
                f"{API_BASE}/users/me", headers=headers
            ) as response:
                data = await response.json()
                if response.status == 200:
                    self.add_result(
                        "获取用户信息",
                        True,
                        f"用户: {data.get('username')}",
                        {
                            "id": data.get("id"),
                            "username": data.get("username"),
                            "email": data.get("email"),
                        },
                    )
                else:
                    self.add_result(
                        "获取用户信息", False, f"获取失败: {data.get('detail')}", data
                    )
        except Exception as e:
            self.add_result("获取用户信息", False, f"请求失败: {str(e)}")

    async def test_create_conversation(self):
        """测试创建对话"""
        if not self.access_token:
            self.add_result("创建对话", False, "需要先登录")
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "title": f"测试对话 {datetime.now().strftime('%H:%M:%S')}",
                "mode": "chat",
                "model": "openrouter/auto",
            }

            async with self.session.post(
                f"{API_BASE}/chat/conversations", headers=headers, json=payload
            ) as response:
                data = await response.json()
                if response.status in [200, 201]:
                    self.conversation_id = data.get("id")
                    self.add_result(
                        "创建对话",
                        True,
                        f"对话ID: {self.conversation_id}",
                        {
                            "id": self.conversation_id,
                            "title": data.get("title"),
                            "mode": data.get("mode"),
                        },
                    )
                else:
                    self.add_result(
                        "创建对话", False, f"创建失败: {data.get('detail')}", data
                    )
        except Exception as e:
            self.add_result("创建对话", False, f"请求失败: {str(e)}")

    async def test_send_message(self):
        """测试发送消息（非流式）"""
        if not self.conversation_id:
            self.add_result("发送消息", False, "需要先创建对话")
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "conversation_id": self.conversation_id,
                "messages": [
                    {"role": "user", "content": "什么是人工智能？请用一句话回答。"}
                ],
                "model": "openrouter/auto",
                "stream": False,
            }

            start_time = time.time()
            async with self.session.post(
                f"{API_BASE}/chat/completions", headers=headers, json=payload
            ) as response:
                elapsed = time.time() - start_time
                data = await response.json()

                if response.status == 200:
                    ai_response = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    self.add_result(
                        "发送消息",
                        True,
                        f"AI响应成功 (耗时: {elapsed:.2f}秒)",
                        {
                            "问题": "什么是人工智能？",
                            "回答": ai_response[:100] + "..."
                            if len(ai_response) > 100
                            else ai_response,
                            "model": data.get("model"),
                            "usage": data.get("usage"),
                        },
                    )
                else:
                    self.add_result(
                        "发送消息", False, f"发送失败: {data.get('detail')}", data
                    )
        except Exception as e:
            self.add_result("发送消息", False, f"请求失败: {str(e)}")

    async def test_stream_message(self):
        """测试流式消息"""
        if not self.conversation_id:
            self.add_result("流式消息", False, "需要先创建对话")
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "conversation_id": self.conversation_id,
                "messages": [
                    {"role": "user", "content": "介绍一下Python编程语言的特点"}
                ],
                "model": "openrouter/auto",
                "stream": True,
            }

            chunks_received = 0
            full_response = ""

            async with self.session.post(
                f"{API_BASE}/chat/completions", headers=headers, json=payload
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            line_str = line.decode("utf-8").strip()
                            if line_str.startswith("data: "):
                                try:
                                    data = json.loads(line_str[6:])
                                    if "content" in data:
                                        chunks_received += 1
                                        full_response += data["content"]
                                except json.JSONDecodeError:
                                    pass

                    self.add_result(
                        "流式消息",
                        True,
                        f"接收到 {chunks_received} 个数据块",
                        {
                            "响应长度": len(full_response),
                            "响应预览": full_response[:100] + "..."
                            if len(full_response) > 100
                            else full_response,
                        },
                    )
                else:
                    error_data = await response.json()
                    self.add_result(
                        "流式消息",
                        False,
                        f"流式响应失败: {error_data.get('detail')}",
                        error_data,
                    )
        except Exception as e:
            self.add_result("流式消息", False, f"请求失败: {str(e)}")

    async def test_create_space(self):
        """测试创建空间"""
        if not self.access_token:
            self.add_result("创建空间", False, "需要先登录")
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "name": f"测试空间 {datetime.now().strftime('%H:%M:%S')}",
                "description": "这是一个功能测试空间",
                "is_public": False,
            }

            async with self.session.post(
                f"{API_BASE}/spaces/", headers=headers, json=payload
            ) as response:
                data = await response.json()
                if response.status in [200, 201]:
                    self.space_id = data.get("id")
                    self.add_result(
                        "创建空间",
                        True,
                        f"空间ID: {self.space_id}",
                        {
                            "id": self.space_id,
                            "name": data.get("name"),
                            "description": data.get("description"),
                        },
                    )
                else:
                    self.add_result(
                        "创建空间", False, f"创建失败: {data.get('detail')}", data
                    )
        except Exception as e:
            self.add_result("创建空间", False, f"请求失败: {str(e)}")

    async def test_upload_document(self):
        """测试上传文档"""
        if not self.space_id:
            self.add_result("上传文档", False, "需要先创建空间")
            return

        try:
            # 创建测试文件
            test_content = """# 测试文档

这是一个用于测试的Markdown文档。

## 主要内容

1. 人工智能是计算机科学的一个分支
2. 它致力于创建能够执行通常需要人类智能的任务的系统
3. 包括机器学习、深度学习、自然语言处理等技术

## 应用领域

- 图像识别
- 语音识别
- 自然语言处理
- 推荐系统
"""

            # 创建 FormData
            form = aiohttp.FormData()
            form.add_field(
                "file",
                test_content.encode("utf-8"),
                filename="test_document.md",
                content_type="text/markdown",
            )
            form.add_field("space_id", str(self.space_id))

            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with self.session.post(
                f"{API_BASE}/documents/upload", headers=headers, data=form
            ) as response:
                data = await response.json()
                if response.status in [200, 201]:
                    self.document_id = data.get("id")
                    self.add_result(
                        "上传文档",
                        True,
                        f"文档ID: {self.document_id}",
                        {
                            "id": self.document_id,
                            "filename": data.get("filename"),
                            "size": data.get("file_size"),
                            "chunks": len(data.get("chunks", [])),
                        },
                    )
                else:
                    self.add_result(
                        "上传文档", False, f"上传失败: {data.get('detail')}", data
                    )
        except Exception as e:
            self.add_result("上传文档", False, f"请求失败: {str(e)}")

    async def test_search_documents(self):
        """测试文档搜索"""
        if not self.space_id:
            self.add_result("文档搜索", False, "需要先创建空间")
            return

        # 等待一下让向量索引更新
        await asyncio.sleep(2)

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            # 使用 POST 请求进行搜索
            payload = {"query": "人工智能", "space_id": self.space_id, "limit": 5}

            async with self.session.post(
                f"{API_BASE}/documents/search", headers=headers, json=payload
            ) as response:
                data = await response.json()
                if response.status == 200:
                    results = data.get("results", [])
                    self.add_result(
                        "文档搜索",
                        True,
                        f"找到 {len(results)} 个结果",
                        {
                            "query": "人工智能",
                            "results_count": len(results),
                            "first_result": results[0] if results else None,
                        },
                    )
                else:
                    self.add_result(
                        "文档搜索", False, f"搜索失败: {data.get('detail')}", data
                    )
        except Exception as e:
            self.add_result("文档搜索", False, f"请求失败: {str(e)}")

    async def test_create_note(self):
        """测试创建笔记"""
        if not self.space_id:
            self.add_result("创建笔记", False, "需要先创建空间")
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "title": f"测试笔记 {datetime.now().strftime('%H:%M:%S')}",
                "content": "这是一个测试笔记的内容。\n\n包含多行文本。",
                "space_id": self.space_id,
                "tags": ["测试", "自动化"],
            }

            async with self.session.post(
                f"{API_BASE}/notes/", headers=headers, json=payload
            ) as response:
                data = await response.json()
                if response.status in [200, 201]:
                    self.note_id = data.get("id")
                    self.add_result(
                        "创建笔记",
                        True,
                        f"笔记ID: {self.note_id}",
                        {
                            "id": self.note_id,
                            "title": data.get("title"),
                            "tags": data.get("tags"),
                        },
                    )
                else:
                    self.add_result(
                        "创建笔记", False, f"创建失败: {data.get('detail')}", data
                    )
        except Exception as e:
            self.add_result("创建笔记", False, f"请求失败: {str(e)}")

    async def test_deep_research(self):
        """测试深度研究功能"""
        if not self.access_token:
            self.add_result("深度研究", False, "需要先登录")
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # 首先获取可用的 agent
            async with self.session.get(
                f"{API_BASE}/agents/", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # 修复：正确处理返回的数据结构
                    agents_list = (
                        data.get("agents", []) if isinstance(data, dict) else data
                    )

                    # 查找研究代理
                    research_agent = None
                    for agent in agents_list:
                        if agent.get("agent_type") == "research":
                            research_agent = agent
                            break

                    if not research_agent:
                        self.add_result(
                            "深度研究",
                            False,
                            "未找到研究代理",
                            {"available_agents": agents_list},
                        )
                        return

                    self.agent_id = research_agent["id"]
                else:
                    self.add_result("深度研究", False, "获取代理列表失败")
                    return

            # 执行深度研究
            payload = {
                "prompt": "人工智能在医疗领域的应用",
                "mode": "general",
                "stream": False
            }

            start_time = time.time()
            async with self.session.post(
                f"{API_BASE}/agents/{self.agent_id}/execute",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),  # 2分钟超时
            ) as response:
                elapsed = time.time() - start_time
                data = await response.json()

                if response.status == 200:
                    self.add_result(
                        "深度研究",
                        True,
                        f"研究完成 (耗时: {elapsed:.2f}秒)",
                        {
                            "topic": "人工智能在医疗领域的应用",
                            "space_id": data.get("space_id"),
                            "sources_count": len(data.get("sources", [])),
                            "content_length": len(data.get("content", "")),
                        },
                    )
                else:
                    self.add_result(
                        "深度研究", False, f"研究失败: {data.get('detail')}", data
                    )
        except TimeoutError:
            self.add_result("深度研究", False, "请求超时（超过2分钟）")
        except Exception as e:
            self.add_result("深度研究", False, f"请求失败: {str(e)}")

    async def test_list_conversations(self):
        """测试获取对话列表"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with self.session.get(
                f"{API_BASE}/chat/conversations", headers=headers
            ) as response:
                data = await response.json()
                if response.status == 200:
                    conversations = data.get("items", [])
                    self.add_result(
                        "对话列表",
                        True,
                        f"共有 {len(conversations)} 个对话",
                        {
                            "total": data.get("total"),
                            "has_test_conversation": any(
                                c["id"] == self.conversation_id for c in conversations
                            ),
                        },
                    )
                else:
                    self.add_result(
                        "对话列表", False, f"获取失败: {data.get('detail')}", data
                    )
        except Exception as e:
            self.add_result("对话列表", False, f"请求失败: {str(e)}")

    async def test_get_spaces(self):
        """测试获取空间列表"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with self.session.get(
                f"{API_BASE}/spaces/", headers=headers
            ) as response:
                data = await response.json()
                if response.status == 200:
                    spaces = data.get("items", []) if isinstance(data, dict) else data
                    self.add_result(
                        "空间列表",
                        True,
                        f"共有 {len(spaces)} 个空间",
                        {
                            "count": len(spaces),
                            "has_test_space": any(
                                s.get("id") == self.space_id for s in spaces
                            )
                            if isinstance(spaces, list)
                            else False,
                        },
                    )
                else:
                    self.add_result(
                        "空间列表", False, f"获取失败: {data.get('detail')}", data
                    )
        except Exception as e:
            self.add_result("空间列表", False, f"请求失败: {str(e)}")

    async def test_delete_operations(self):
        """测试删除操作"""
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # 删除笔记
        if self.note_id:
            try:
                async with self.session.delete(
                    f"{API_BASE}/notes/{self.note_id}", headers=headers
                ) as response:
                    if response.status in [200, 204]:
                        self.add_result("删除笔记", True, f"笔记 {self.note_id} 已删除")
                    else:
                        data = await response.json()
                        self.add_result(
                            "删除笔记", False, f"删除失败: {data.get('detail')}"
                        )
            except Exception as e:
                self.add_result("删除笔记", False, f"请求失败: {str(e)}")

        # 删除文档
        if self.document_id:
            try:
                async with self.session.delete(
                    f"{API_BASE}/documents/{self.document_id}", headers=headers
                ) as response:
                    if response.status in [200, 204]:
                        self.add_result(
                            "删除文档", True, f"文档 {self.document_id} 已删除"
                        )
                    else:
                        data = await response.json()
                        self.add_result(
                            "删除文档", False, f"删除失败: {data.get('detail')}"
                        )
            except Exception as e:
                self.add_result("删除文档", False, f"请求失败: {str(e)}")

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 70)
        print("📊 SecondBrain 后端功能测试报告")
        print("=" * 70)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed

        print("\n📈 测试统计:")
        print(f"  总测试数: {total}")
        print(f"  ✅ 通过: {passed}")
        print(f"  ❌ 失败: {failed}")
        print(f"  成功率: {(passed / total * 100):.1f}%")

        print("\n🔍 测试详情:")
        # 按模块分组显示
        modules = {
            "基础功能": ["健康检查"],
            "用户认证": ["用户注册", "新用户登录", "演示账号登录", "获取用户信息"],
            "AI对话": ["创建对话", "发送消息", "流式消息", "对话列表"],
            "知识管理": ["创建空间", "空间列表", "上传文档", "文档搜索", "创建笔记"],
            "高级功能": ["深度研究"],
            "清理操作": ["删除笔记", "删除文档"],
        }

        for module_name, test_names in modules.items():
            module_results = [r for r in self.test_results if r["test"] in test_names]
            if module_results:
                module_passed = sum(1 for r in module_results if r["success"])
                status = "✅" if module_passed == len(module_results) else "⚠️"
                print(
                    f"\n{status} {module_name} ({module_passed}/{len(module_results)}):"
                )
                for result in module_results:
                    status_icon = "✓" if result["success"] else "✗"
                    print(f"    {status_icon} {result['test']}: {result['message']}")

        if failed > 0:
            print("\n❌ 失败的测试详情:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"\n  测试项: {result['test']}")
                    print(f"  错误信息: {result['message']}")
                    if result.get("details"):
                        print(f"  详细信息: {result['details']}")

        print("\n🎯 结论:")
        if passed == total:
            print("  ✅ 所有功能测试通过！后端系统运行完全正常。")
            print("  ✅ 可以放心地进行前端集成和部署。")
        elif passed / total >= 0.8:
            print("  ⚠️ 核心功能正常运行，有少量功能需要检查。")
            print("  ⚠️ 建议优先修复失败的测试项，但不影响基本使用。")
        else:
            print("  ❌ 系统存在较多问题，需要立即修复。")
            print("  ❌ 请检查后端服务配置和依赖。")

        print("\n📝 下一步建议:")
        if passed == total:
            print("  1. 通知前端同学可以开始集成")
            print("  2. 准备部署到云服务")
            print("  3. 创建演示数据")
        else:
            print("  1. 检查并修复失败的测试")
            print("  2. 确保 OpenRouter API 密钥配置正确")
            print("  3. 验证数据库和向量数据库连接")
        print("=" * 70)


async def main():
    """运行所有测试"""
    print("🚀 开始 SecondBrain 后端完整功能测试")
    print("⏰ 测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)

    async with APITester() as tester:
        # 基础测试
        await tester.test_health_check()

        # 用户认证测试
        await tester.test_user_registration()
        await tester.test_user_login()
        await tester.test_get_user_info()

        # 也测试演示账号
        await tester.test_user_login(use_demo=True)

        # AI 对话测试
        await tester.test_create_conversation()
        await tester.test_send_message()
        await tester.test_stream_message()
        await tester.test_list_conversations()

        # 知识管理测试
        await tester.test_create_space()
        await tester.test_get_spaces()
        await tester.test_upload_document()
        await tester.test_search_documents()
        await tester.test_create_note()

        # 高级功能测试
        await tester.test_deep_research()

        # 清理测试
        await tester.test_delete_operations()

        # 打印摘要
        tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
