#!/usr/bin/env python3
"""前端快速测试脚本 - 验证所有核心功能"""

import asyncio
import json
from datetime import datetime

import aiohttp

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 演示账号
DEMO_USER = "demo_user"
DEMO_PASS = "Demo123456!"


class FrontendQuickTest:
    def __init__(self):
        self.session = None
        self.access_token = None
        self.results = []

    async def setup(self):
        """初始化会话"""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """清理会话"""
        if self.session:
            await self.session.close()

    def print_result(self, test_name: str, success: bool, message: str = ""):
        """打印测试结果"""
        icon = "✅" if success else "❌"
        print(f"{icon} {test_name}: {message}")
        self.results.append({"test": test_name, "success": success, "message": message})

    async def test_health(self):
        """测试健康检查"""
        try:
            async with self.session.get(f"{BASE_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.print_result("健康检查", True, f"服务正常 - {data['service']}")
                else:
                    self.print_result("健康检查", False, f"状态码: {resp.status}")
        except Exception as e:
            self.print_result("健康检查", False, str(e))

    async def test_login(self):
        """测试登录"""
        try:
            # 表单登录
            data = aiohttp.FormData()
            data.add_field("username", DEMO_USER)
            data.add_field("password", DEMO_PASS)

            async with self.session.post(f"{API_BASE}/auth/login", data=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.access_token = result["access_token"]
                    self.print_result(
                        "用户登录", True, f"获得 Token: {self.access_token[:20]}..."
                    )
                else:
                    self.print_result("用户登录", False, f"状态码: {resp.status}")
        except Exception as e:
            self.print_result("用户登录", False, str(e))

    async def test_user_info(self):
        """测试获取用户信息"""
        if not self.access_token:
            self.print_result("用户信息", False, "需要先登录")
            return

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(
                f"{API_BASE}/users/me", headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.print_result(
                        "用户信息",
                        True,
                        f"用户: {data['username']}, 邮箱: {data['email']}",
                    )
                else:
                    self.print_result("用户信息", False, f"状态码: {resp.status}")
        except Exception as e:
            self.print_result("用户信息", False, str(e))

    async def test_chat(self):
        """测试 AI 对话"""
        if not self.access_token:
            self.print_result("AI 对话", False, "需要先登录")
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # 创建对话
            conv_data = {
                "title": f"测试对话 {datetime.now().strftime('%H:%M:%S')}",
                "mode": "chat",
            }
            async with self.session.post(
                f"{API_BASE}/chat/conversations", headers=headers, json=conv_data
            ) as resp:
                if resp.status != 201:
                    self.print_result("创建对话", False, f"状态码: {resp.status}")
                    return

                conv = await resp.json()
                conv_id = conv["id"]
                self.print_result("创建对话", True, f"对话 ID: {conv_id}")

            # 发送消息
            msg_data = {"content": "你好，请介绍一下 SecondBrain 系统", "stream": False}
            async with self.session.post(
                f"{API_BASE}/chat/conversations/{conv_id}/messages",
                headers=headers,
                json=msg_data,
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    ai_response = result["message"]["content"][:100] + "..."
                    self.print_result("发送消息", True, f"AI 回复: {ai_response}")
                else:
                    self.print_result("发送消息", False, f"状态码: {resp.status}")

        except Exception as e:
            self.print_result("AI 对话", False, str(e))

    async def test_spaces(self):
        """测试空间管理"""
        if not self.access_token:
            self.print_result("空间管理", False, "需要先登录")
            return

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            # 获取空间列表
            async with self.session.get(f"{API_BASE}/spaces/", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    space_count = data.get("total", 0)
                    self.print_result("空间列表", True, f"共有 {space_count} 个空间")

                    # 如果有空间，显示第一个
                    if data.get("items"):
                        first_space = data["items"][0]
                        print(
                            f"  └─ 示例: {first_space['name']} ({first_space['icon']})"
                        )
                else:
                    self.print_result("空间列表", False, f"状态码: {resp.status}")

        except Exception as e:
            self.print_result("空间管理", False, str(e))

    async def test_deep_research(self):
        """测试 Deep Research"""
        if not self.access_token:
            self.print_result("Deep Research", False, "需要先登录")
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # 执行 Deep Research
            research_data = {
                "prompt": "什么是量子计算？",
                "mode": "general",
                "stream": False,
            }

            print("⏳ 正在进行深度研究（可能需要 20-30 秒）...")

            async with self.session.post(
                f"{API_BASE}/agents/1/execute",
                headers=headers,
                json=research_data,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.print_result(
                        "Deep Research",
                        True,
                        f"研究完成，空间 ID: {result.get('result', {}).get('space_id')}",
                    )
                else:
                    self.print_result("Deep Research", False, f"状态码: {resp.status}")

        except TimeoutError:
            self.print_result("Deep Research", False, "请求超时")
        except Exception as e:
            self.print_result("Deep Research", False, str(e))

    async def test_websocket(self):
        """测试 WebSocket 连接"""
        if not self.access_token:
            self.print_result("WebSocket", False, "需要先登录")
            return

        try:
            ws_url = f"ws://localhost:8000/ws?token={self.access_token}"

            async with self.session.ws_connect(ws_url) as ws:
                # 发送测试消息
                await ws.send_json(
                    {"type": "ping", "data": {"timestamp": datetime.now().isoformat()}}
                )

                # 等待响应
                msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    self.print_result(
                        "WebSocket",
                        True,
                        f"连接成功，收到: {data.get('type', 'unknown')}",
                    )
                else:
                    self.print_result("WebSocket", False, "未收到有效响应")

                await ws.close()

        except TimeoutError:
            self.print_result("WebSocket", False, "连接超时")
        except Exception as e:
            self.print_result("WebSocket", False, str(e))

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 SecondBrain 前端快速测试")
        print("=" * 60)
        print(f"API 地址: {API_BASE}")
        print(f"测试账号: {DEMO_USER}")
        print("=" * 60)
        print()

        # 基础测试
        print("📋 基础功能测试")
        print("-" * 40)
        await self.test_health()
        await self.test_login()
        await self.test_user_info()
        print()

        # 核心功能测试
        print("🎯 核心功能测试")
        print("-" * 40)
        await self.test_chat()
        await self.test_spaces()
        print()

        # 高级功能测试
        print("🔬 高级功能测试")
        print("-" * 40)
        await self.test_deep_research()
        await self.test_websocket()
        print()

        # 测试总结
        print("=" * 60)
        print("📊 测试总结")
        print("=" * 60)

        success_count = sum(1 for r in self.results if r["success"])
        total_count = len(self.results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        print(f"✅ 通过: {success_count}/{total_count} ({success_rate:.1f}%)")

        if success_count < total_count:
            print("\n❌ 失败的测试:")
            for r in self.results:
                if not r["success"]:
                    print(f"  - {r['test']}: {r['message']}")

        print("\n💡 提示:")
        print("  - 确保后端服务正在运行: docker-compose ps")
        print("  - 查看 API 文档: http://localhost:8000/api/v1/docs")
        print("  - 使用 Web 测试界面: http://localhost:8080")
        print("  - 查看详细日志: docker-compose logs -f backend")


async def main():
    tester = FrontendQuickTest()
    await tester.setup()

    try:
        await tester.run_all_tests()
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
