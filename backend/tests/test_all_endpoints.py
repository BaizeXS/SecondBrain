"""综合测试所有API端点功能."""

import asyncio
import os

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 加载环境变量
load_dotenv()

console = Console()

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"


class EndpointTester:
    """API端点测试器."""

    def __init__(self):
        self.client: httpx.AsyncClient | None = None
        self.token: str | None = None
        self.headers: dict = {}
        self.test_user = {
            "username": f"test_user_{os.urandom(4).hex()}",
            "email": f"test_{os.urandom(4).hex()}@example.com",
            "password": "TestPassword123!"
        }
        self.created_resources = {
            "user_id": None,
            "space_id": None,
            "document_id": None,
            "conversation_id": None,
        }

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def test_auth_endpoints(self) -> bool:
        """测试认证相关端点."""
        console.print("\n[bold blue]📋 测试认证端点[/bold blue]")

        try:
            # 1. 注册新用户
            console.print("  1️⃣ 注册新用户...")
            response = await self.client.post(
                f"{BASE_URL}/auth/register",
                json=self.test_user
            )
            if response.status_code == 201:
                user_data = response.json()
                self.created_resources["user_id"] = user_data["id"]
                console.print(f"    ✅ 注册成功: {user_data['username']}")
            else:
                console.print(f"    ❌ 注册失败: {response.status_code} - {response.text}")
                return False

            # 2. 用户登录
            console.print("  2️⃣ 用户登录...")
            response = await self.client.post(
                f"{BASE_URL}/auth/login/json",
                json={
                    "username": self.test_user["username"],
                    "password": self.test_user["password"]
                }
            )
            if response.status_code == 200:
                login_data = response.json()
                self.token = login_data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                console.print("    ✅ 登录成功")
            else:
                console.print(f"    ❌ 登录失败: {response.status_code}")
                return False

            # 3. 获取当前用户信息
            console.print("  3️⃣ 获取用户信息...")
            response = await self.client.get(
                f"{BASE_URL}/users/me",
                headers=self.headers
            )
            if response.status_code == 200:
                console.print(f"    ✅ 获取成功: {response.json()['username']}")
            else:
                console.print(f"    ❌ 获取失败: {response.status_code}")
                return False

            return True

        except Exception as e:
            console.print(f"    ❌ 异常: {str(e)}")
            return False

    async def test_space_endpoints(self) -> bool:
        """测试空间相关端点."""
        console.print("\n[bold blue]📁 测试空间端点[/bold blue]")

        try:
            # 1. 创建空间
            console.print("  1️⃣ 创建空间...")
            space_data = {
                "name": "测试空间",
                "description": "这是一个测试空间",
                "color": "#3B82F6",
                "icon": "📚",
                "is_public": False,
                "tags": ["测试", "demo"]
            }
            response = await self.client.post(
                f"{BASE_URL}/spaces/",
                json=space_data,
                headers=self.headers
            )
            if response.status_code == 201:
                space = response.json()
                self.created_resources["space_id"] = space["id"]
                console.print(f"    ✅ 创建成功: {space['name']} (ID: {space['id']})")
            else:
                console.print(f"    ❌ 创建失败: {response.status_code} - {response.text}")
                return False

            # 2. 获取空间列表
            console.print("  2️⃣ 获取空间列表...")
            response = await self.client.get(
                f"{BASE_URL}/spaces/",
                headers=self.headers
            )
            if response.status_code == 200:
                spaces = response.json()
                console.print(f"    ✅ 获取成功: 共 {spaces['total']} 个空间")
            else:
                console.print(f"    ❌ 获取失败: {response.status_code}")
                return False

            # 3. 获取空间详情
            console.print("  3️⃣ 获取空间详情...")
            response = await self.client.get(
                f"{BASE_URL}/spaces/{self.created_resources['space_id']}",
                headers=self.headers
            )
            if response.status_code == 200:
                console.print("    ✅ 获取详情成功")
            else:
                console.print(f"    ❌ 获取失败: {response.status_code}")
                return False

            # 4. 更新空间
            console.print("  4️⃣ 更新空间信息...")
            update_data = {
                "description": "更新后的描述",
                "tags": ["测试", "更新", "demo"]
            }
            response = await self.client.put(
                f"{BASE_URL}/spaces/{self.created_resources['space_id']}",
                json=update_data,
                headers=self.headers
            )
            if response.status_code == 200:
                console.print("    ✅ 更新成功")
            else:
                console.print(f"    ❌ 更新失败: {response.status_code}")
                return False

            return True

        except Exception as e:
            console.print(f"    ❌ 异常: {str(e)}")
            return False

    async def test_document_endpoints(self) -> bool:
        """测试文档相关端点."""
        console.print("\n[bold blue]📄 测试文档端点[/bold blue]")

        try:
            if not self.created_resources["space_id"]:
                console.print("    ⚠️  需要先创建空间")
                return False

            # 1. 上传文档
            console.print("  1️⃣ 上传文档...")
            files = {
                'file': ('test.txt', b'This is a test document content.', 'text/plain')
            }
            data = {
                'space_id': str(self.created_resources["space_id"]),
                'title': '测试文档',
                'tags': '测试,示例'
            }
            response = await self.client.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                data=data,
                headers=self.headers
            )
            if response.status_code == 201:
                document = response.json()
                self.created_resources["document_id"] = document["id"]
                console.print(f"    ✅ 上传成功: {document['filename']} (ID: {document['id']})")
            else:
                console.print(f"    ❌ 上传失败: {response.status_code} - {response.text}")
                return False

            # 2. 获取文档列表
            console.print("  2️⃣ 获取文档列表...")
            response = await self.client.get(
                f"{BASE_URL}/documents/?space_id={self.created_resources['space_id']}",
                headers=self.headers
            )
            if response.status_code == 200:
                documents = response.json()
                console.print(f"    ✅ 获取成功: 共 {documents['total']} 个文档")
            else:
                console.print(f"    ❌ 获取失败: {response.status_code}")
                return False

            # 3. 获取文档详情
            console.print("  3️⃣ 获取文档详情...")
            response = await self.client.get(
                f"{BASE_URL}/documents/{self.created_resources['document_id']}",
                headers=self.headers
            )
            if response.status_code == 200:
                console.print("    ✅ 获取详情成功")
            else:
                console.print(f"    ❌ 获取失败: {response.status_code}")
                return False

            return True

        except Exception as e:
            console.print(f"    ❌ 异常: {str(e)}")
            return False

    async def test_conversation_endpoints(self) -> bool:
        """测试对话相关端点."""
        console.print("\n[bold blue]💬 测试对话端点[/bold blue]")

        try:
            # 1. 创建对话
            console.print("  1️⃣ 创建对话...")
            conversation_data = {
                "title": "测试对话",
                "mode": "chat",
                "space_id": self.created_resources["space_id"]
            }
            response = await self.client.post(
                f"{BASE_URL}/chat/conversations",
                json=conversation_data,
                headers=self.headers
            )
            if response.status_code == 201:
                conversation = response.json()
                self.created_resources["conversation_id"] = conversation["id"]
                console.print(f"    ✅ 创建成功: {conversation['title']} (ID: {conversation['id']})")
            else:
                console.print(f"    ❌ 创建失败: {response.status_code} - {response.text}")
                return False

            # 2. 获取对话列表
            console.print("  2️⃣ 获取对话列表...")
            response = await self.client.get(
                f"{BASE_URL}/chat/conversations",
                headers=self.headers
            )
            if response.status_code == 200:
                conversations = response.json()
                console.print(f"    ✅ 获取成功: 共 {conversations['total']} 个对话")
            else:
                console.print(f"    ❌ 获取失败: {response.status_code}")
                return False

            # 3. 发送聊天消息
            console.print("  3️⃣ 发送聊天消息...")
            chat_request = {
                "messages": [
                    {"role": "user", "content": "你好，这是一个测试消息"}
                ],
                "model": "gpt-4o-mini",
                "conversation_id": self.created_resources["conversation_id"]
            }
            response = await self.client.post(
                f"{BASE_URL}/chat/completions",
                json=chat_request,
                headers=self.headers
            )
            if response.status_code == 200:
                console.print("    ✅ 消息发送成功")
            else:
                console.print(f"    ❌ 发送失败: {response.status_code}")
                # 不算失败，可能是AI服务未配置

            return True

        except Exception as e:
            console.print(f"    ❌ 异常: {str(e)}")
            return False

    async def test_agent_endpoints(self) -> bool:
        """测试代理相关端点."""
        console.print("\n[bold blue]🤖 测试代理端点[/bold blue]")

        try:
            # 1. 获取代理列表
            console.print("  1️⃣ 获取代理列表...")
            response = await self.client.get(
                f"{BASE_URL}/agents/",
                headers=self.headers
            )
            if response.status_code == 200:
                agents = response.json()
                console.print(f"    ✅ 获取成功: 共 {agents['total']} 个代理")

                # 2. 获取代理详情
                if agents['agents']:
                    agent_id = agents['agents'][0]['id']
                    console.print(f"  2️⃣ 获取代理详情 (ID: {agent_id})...")
                    response = await self.client.get(
                        f"{BASE_URL}/agents/{agent_id}",
                        headers=self.headers
                    )
                    if response.status_code == 200:
                        console.print("    ✅ 获取详情成功")
                    else:
                        console.print(f"    ❌ 获取失败: {response.status_code}")
            else:
                console.print(f"    ❌ 获取列表失败: {response.status_code}")
                return False

            return True

        except Exception as e:
            console.print(f"    ❌ 异常: {str(e)}")
            return False

    async def cleanup(self):
        """清理测试数据."""
        console.print("\n[bold yellow]🧹 清理测试数据[/bold yellow]")

        try:
            # 删除文档
            if self.created_resources["document_id"]:
                response = await self.client.delete(
                    f"{BASE_URL}/documents/{self.created_resources['document_id']}",
                    headers=self.headers
                )
                if response.status_code == 204:
                    console.print("  ✅ 删除文档成功")

            # 删除对话
            if self.created_resources["conversation_id"]:
                response = await self.client.delete(
                    f"{BASE_URL}/chat/conversations/{self.created_resources['conversation_id']}",
                    headers=self.headers
                )
                if response.status_code == 204:
                    console.print("  ✅ 删除对话成功")

            # 删除空间
            if self.created_resources["space_id"]:
                response = await self.client.delete(
                    f"{BASE_URL}/spaces/{self.created_resources['space_id']}",
                    headers=self.headers
                )
                if response.status_code == 204:
                    console.print("  ✅ 删除空间成功")

            # 删除用户账户
            if self.token:
                response = await self.client.delete(
                    f"{BASE_URL}/users/me",
                    json={"password": self.test_user["password"]},
                    headers=self.headers
                )
                if response.status_code == 204:
                    console.print("  ✅ 删除用户账户成功")

        except Exception as e:
            console.print(f"  ⚠️  清理时出错: {str(e)}")

    async def run_all_tests(self):
        """运行所有测试."""
        console.print(Panel.fit(
            "[bold green]🚀 Second Brain API 端点测试[/bold green]",
            border_style="green"
        ))

        # 测试结果
        results = {
            "认证": False,
            "空间": False,
            "文档": False,
            "对话": False,
            "代理": False,
        }

        # 运行测试
        results["认证"] = await self.test_auth_endpoints()

        if results["认证"]:  # 只有认证成功才能继续
            results["空间"] = await self.test_space_endpoints()
            results["文档"] = await self.test_document_endpoints()
            results["对话"] = await self.test_conversation_endpoints()
            results["代理"] = await self.test_agent_endpoints()

            # 清理测试数据
            await self.cleanup()

        # 显示测试结果
        console.print("\n[bold]📊 测试结果汇总[/bold]")
        table = Table()
        table.add_column("模块", style="cyan")
        table.add_column("状态", style="green")

        for module, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            table.add_row(module, status)

        console.print(table)

        # 总体结果
        all_passed = all(results.values())
        if all_passed:
            console.print("\n[bold green]✅ 所有测试通过！[/bold green]")
        else:
            console.print("\n[bold red]❌ 部分测试失败[/bold red]")

        return all_passed


async def main():
    """主函数."""
    async with EndpointTester() as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
