#!/usr/bin/env python3
"""
SecondBrain 演示数据创建脚本
用于在部署后快速创建演示数据，展示系统的完整功能
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any

import aiohttp

# API配置
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# 演示用户配置
DEMO_USERS = [
    {
        "username": "demo_user",
        "email": "demo@example.com",
        "password": "Demo123456!",
        "full_name": "演示用户",
    },
    {
        "username": "teacher_demo",
        "email": "teacher@example.com",
        "password": "Teacher123456!",
        "full_name": "教师演示账号",
    },
]

# 演示空间配置
DEMO_SPACES = [
    {
        "name": "人工智能研究",
        "description": "收集和整理人工智能相关的研究资料、论文和笔记",
        "is_public": True,
    },
    {
        "name": "项目开发文档",
        "description": "SecondBrain项目的开发文档、API说明和技术架构",
        "is_public": False,
    },
    {
        "name": "学习笔记",
        "description": "个人学习笔记，包括编程、算法和系统设计",
        "is_public": False,
    },
]

# 演示文档内容
DEMO_DOCUMENTS = [
    {
        "filename": "AI_Introduction.md",
        "content": """# 人工智能简介

## 什么是人工智能？

人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

## AI的主要领域

### 1. 机器学习（Machine Learning）
机器学习是AI的核心，是使计算机具有智能的根本途径。

### 2. 深度学习（Deep Learning）
深度学习是机器学习的分支，是一种基于对数据进行表征学习的算法。

### 3. 自然语言处理（NLP）
让计算机理解、解释和生成人类语言。

### 4. 计算机视觉
使机器能够从图像或视频中获取信息。

## 应用场景

- **医疗诊断**：辅助医生进行疾病诊断
- **自动驾驶**：实现车辆的自主导航
- **智能客服**：提供24/7的客户服务
- **金融风控**：识别欺诈交易和风险评估
""",
    },
    {
        "filename": "SecondBrain_Architecture.md",
        "content": """# SecondBrain 系统架构

## 技术栈

### 后端
- **框架**: FastAPI (Python)
- **数据库**: PostgreSQL
- **缓存**: Redis
- **向量数据库**: Qdrant
- **对象存储**: MinIO

### 前端
- **框架**: React
- **状态管理**: Redux
- **UI组件**: Ant Design

## 核心模块

### 1. AI对话模块
- 支持多种AI模型（OpenAI、Claude、Gemini等）
- 流式响应
- 对话历史管理
- 消息分支功能

### 2. 知识管理模块
- 文档上传和解析
- 向量化存储
- 语义搜索
- 笔记管理

### 3. 智能代理模块
- 深度研究功能
- 自定义代理
- 任务自动化

## API设计

采用RESTful设计原则，主要端点包括：
- `/api/v1/auth` - 认证相关
- `/api/v1/chat` - 对话管理
- `/api/v1/spaces` - 空间管理
- `/api/v1/documents` - 文档管理
- `/api/v1/notes` - 笔记管理
- `/api/v1/agents` - 代理管理
""",
    },
    {
        "filename": "Python_Best_Practices.md",
        "content": """# Python 最佳实践

## 代码风格

### 1. 遵循 PEP 8
Python 官方的编码规范，包括：
- 使用 4 个空格缩进
- 行长度不超过 79 字符
- 类名使用驼峰命名法
- 函数名使用小写下划线命名

### 2. 类型注解
```python
def calculate_discount(price: float, discount_rate: float) -> float:
    return price * (1 - discount_rate)
```

### 3. 文档字符串
```python
def process_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    \"\"\"
    处理输入数据并返回汇总结果

    Args:
        data: 包含原始数据的字典列表

    Returns:
        处理后的汇总数据字典
    \"\"\"
    pass
```

## 性能优化

### 1. 使用生成器
处理大量数据时，使用生成器可以节省内存：
```python
def read_large_file(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            yield line.strip()
```

### 2. 异步编程
使用 asyncio 处理 I/O 密集型任务：
```python
async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## 错误处理

### 1. 具体的异常处理
```python
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # 处理或重新抛出
```

### 2. 使用上下文管理器
```python
from contextlib import contextmanager

@contextmanager
def database_connection():
    conn = create_connection()
    try:
        yield conn
    finally:
        conn.close()
```
""",
    },
]

# 演示笔记
DEMO_NOTES = [
    {
        "title": "项目进度更新 - 2025年1月",
        "content": """## 本月完成的工作

1. **后端开发**
   - ✅ 完成所有核心API开发
   - ✅ 集成多个AI模型提供商
   - ✅ 实现向量搜索功能

2. **前端开发**
   - ✅ 完成基础UI框架
   - ✅ 实现对话界面
   - 🔄 优化响应式设计

3. **测试和部署**
   - ✅ 单元测试覆盖率达到80%
   - ✅ 集成测试通过
   - 🔄 准备生产环境部署

## 下一步计划

- 完成前后端集成测试
- 部署到云服务器
- 准备演示材料
""",
        "tags": ["项目管理", "进度更新"],
    },
    {
        "title": "AI模型对比研究",
        "content": """# 主流AI模型对比

## GPT-4
- **优势**：强大的推理能力，广泛的知识面
- **劣势**：成本较高，有时过于冗长
- **适用场景**：复杂问题解答、创意写作

## Claude 3
- **优势**：安全性高，逻辑清晰，代码能力强
- **劣势**：知识截止日期限制
- **适用场景**：技术文档、代码分析

## Gemini Pro
- **优势**：多模态能力，响应速度快
- **劣势**：中文支持有待提升
- **适用场景**：图像理解、快速查询

## 国产模型
- **通义千问**：中文理解能力强
- **文心一言**：擅长中文创作
- **ChatGLM**：开源可部署

## 选择建议
根据具体应用场景选择：
- 通用对话：GPT-4 或 Claude
- 代码开发：Claude 或 DeepSeek
- 中文场景：通义千问或文心一言
- 成本敏感：开源模型或API套餐
""",
        "tags": ["AI", "研究", "对比分析"],
    },
    {
        "title": "FastAPI 开发技巧",
        "content": """# FastAPI 开发最佳实践

## 1. 项目结构
```
app/
├── api/
│   └── v1/
│       ├── endpoints/
│       └── api.py
├── core/
│   ├── config.py
│   └── security.py
├── models/
├── schemas/
├── services/
└── main.py
```

## 2. 依赖注入
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_user(db, user_id)
```

## 3. 异步处理
```python
@router.post("/process")
async def process_data(
    background_tasks: BackgroundTasks,
    data: DataSchema
):
    background_tasks.add_task(heavy_processing, data)
    return {"message": "Processing started"}
```

## 4. 错误处理
```python
@router.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

## 5. 性能优化
- 使用连接池
- 实现缓存策略
- 异步I/O操作
- 合理使用中间件
""",
        "tags": ["FastAPI", "Python", "后端开发"],
    },
]

# 演示对话
DEMO_CONVERSATIONS = [
    {
        "title": "了解SecondBrain系统",
        "messages": [
            {"role": "user", "content": "请介绍一下SecondBrain系统的主要功能"},
            {
                "role": "assistant",
                "content": "SecondBrain是一个智能知识管理系统，主要包含以下核心功能：\n\n1. **AI对话**：支持多种AI模型，可以进行智能对话和问答\n2. **知识管理**：创建空间来组织文档、笔记等知识内容\n3. **智能搜索**：基于语义的全文搜索功能\n4. **深度研究**：自动收集和整理特定主题的研究资料\n\n您可以将它作为您的第二大脑，帮助您更好地管理和利用知识。",
            },
        ],
    },
    {
        "title": "Python编程问题咨询",
        "messages": [
            {"role": "user", "content": "如何在Python中实现单例模式？"},
            {
                "role": "assistant",
                "content": "在Python中实现单例模式有几种常见方法：\n\n```python\n# 方法1：使用__new__方法\nclass Singleton:\n    _instance = None\n    \n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance\n\n# 方法2：使用装饰器\ndef singleton(cls):\n    instances = {}\n    def get_instance(*args, **kwargs):\n        if cls not in instances:\n            instances[cls] = cls(*args, **kwargs)\n        return instances[cls]\n    return get_instance\n\n@singleton\nclass MyClass:\n    pass\n\n# 方法3：使用元类\nclass SingletonMeta(type):\n    _instances = {}\n    \n    def __call__(cls, *args, **kwargs):\n        if cls not in cls._instances:\n            cls._instances[cls] = super().__call__(*args, **kwargs)\n        return cls._instances[cls]\n```\n\n推荐使用装饰器方法，因为它更Pythonic且易于理解。",
            },
        ],
    },
]


class DemoDataCreator:
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.users_tokens = {}
        self.created_data = {
            "users": [],
            "spaces": [],
            "documents": [],
            "notes": [],
            "conversations": [],
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log(self, message: str, level: str = "INFO"):
        """打印日志信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        symbol = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "ℹ️"
        print(f"[{timestamp}] {symbol} {message}")

    async def create_user(self, user_data: dict[str, Any]) -> bool:
        """创建用户账号"""
        if not self.session:
            self.log("Session未初始化", "ERROR")
            return False

        try:
            # 先尝试登录，如果失败则注册
            form_data = aiohttp.FormData()
            form_data.add_field("username", user_data["username"])
            form_data.add_field("password", user_data["password"])

            # 尝试登录
            async with self.session.post(
                f"{API_BASE}/auth/login", data=form_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.users_tokens[user_data["username"]] = data.get("access_token")
                    self.log(
                        f"用户 {user_data['username']} 已存在，登录成功", "SUCCESS"
                    )
                    return True

            # 如果登录失败，尝试注册
            async with self.session.post(
                f"{API_BASE}/auth/register", json=user_data
            ) as response:
                if response.status in [200, 201]:
                    self.log(f"创建用户 {user_data['username']} 成功", "SUCCESS")

                    # 注册后登录
                    async with self.session.post(
                        f"{API_BASE}/auth/login", data=form_data
                    ) as login_response:
                        if login_response.status == 200:
                            data = await login_response.json()
                            self.users_tokens[user_data["username"]] = data.get(
                                "access_token"
                            )
                            return True
                        else:
                            self.log("注册后登录失败", "ERROR")
                            return False
                else:
                    error_data = await response.json()
                    self.log(f"创建用户失败: {error_data.get('detail')}", "ERROR")
                    return False

        except Exception as e:
            self.log(f"创建用户异常: {str(e)}", "ERROR")
            return False

    async def create_space(
        self, username: str, space_data: dict[str, Any]
    ) -> int | None:
        """创建空间"""
        token = self.users_tokens.get(username)
        if not token:
            self.log(f"用户 {username} 未登录", "ERROR")
            return None

        if not self.session:
            self.log("Session未初始化", "ERROR")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                f"{API_BASE}/spaces/", headers=headers, json=space_data
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    space_id = data.get("id")
                    self.created_data["spaces"].append(
                        {"id": space_id, "name": space_data["name"], "owner": username}
                    )
                    self.log(
                        f"创建空间 '{space_data['name']}' 成功 (ID: {space_id})",
                        "SUCCESS",
                    )
                    return space_id
                else:
                    error_data = await response.json()
                    self.log(f"创建空间失败: {error_data.get('detail')}", "ERROR")
                    return None

        except Exception as e:
            self.log(f"创建空间异常: {str(e)}", "ERROR")
            return None

    async def upload_document(
        self, username: str, space_id: int, doc_data: dict[str, Any]
    ) -> int | None:
        """上传文档"""
        token = self.users_tokens.get(username)
        if not token:
            self.log(f"用户 {username} 未登录", "ERROR")
            return None

        if not self.session:
            self.log("Session未初始化", "ERROR")
            return None

        try:
            form = aiohttp.FormData()
            form.add_field(
                "file",
                doc_data["content"].encode("utf-8"),
                filename=doc_data["filename"],
                content_type="text/markdown",
            )
            form.add_field("space_id", str(space_id))

            headers = {"Authorization": f"Bearer {token}"}

            async with self.session.post(
                f"{API_BASE}/documents/upload", headers=headers, data=form
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    doc_id = data.get("id")
                    self.created_data["documents"].append(
                        {
                            "id": doc_id,
                            "filename": doc_data["filename"],
                            "space_id": space_id,
                        }
                    )
                    self.log(
                        f"上传文档 '{doc_data['filename']}' 成功 (ID: {doc_id})",
                        "SUCCESS",
                    )
                    return doc_id
                else:
                    error_data = await response.json()
                    self.log(f"上传文档失败: {error_data.get('detail')}", "ERROR")
                    return None

        except Exception as e:
            self.log(f"上传文档异常: {str(e)}", "ERROR")
            return None

    async def create_note(
        self, username: str, space_id: int, note_data: dict[str, Any]
    ) -> int | None:
        """创建笔记"""
        token = self.users_tokens.get(username)
        if not token:
            self.log(f"用户 {username} 未登录", "ERROR")
            return None

        if not self.session:
            self.log("Session未初始化", "ERROR")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            payload = {
                "title": note_data["title"],
                "content": note_data["content"],
                "space_id": space_id,
                "tags": note_data.get("tags", []),
            }

            async with self.session.post(
                f"{API_BASE}/notes/", headers=headers, json=payload
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    note_id = data.get("id")
                    self.created_data["notes"].append(
                        {
                            "id": note_id,
                            "title": note_data["title"],
                            "space_id": space_id,
                        }
                    )
                    self.log(
                        f"创建笔记 '{note_data['title']}' 成功 (ID: {note_id})",
                        "SUCCESS",
                    )
                    return note_id
                else:
                    error_data = await response.json()
                    self.log(f"创建笔记失败: {error_data.get('detail')}", "ERROR")
                    return None

        except Exception as e:
            self.log(f"创建笔记异常: {str(e)}", "ERROR")
            return None

    async def create_conversation(
        self, username: str, conv_data: dict[str, Any]
    ) -> int | None:
        """创建对话并发送消息"""
        token = self.users_tokens.get(username)
        if not token:
            self.log(f"用户 {username} 未登录", "ERROR")
            return None

        if not self.session:
            self.log("Session未初始化", "ERROR")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            # 创建对话
            conv_payload = {
                "title": conv_data["title"],
                "mode": "chat",
                "model": "openrouter/auto",
            }

            async with self.session.post(
                f"{API_BASE}/chat/conversations", headers=headers, json=conv_payload
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    conv_id = data.get("id")

                    # 发送消息
                    for i in range(0, len(conv_data["messages"]), 2):
                        user_msg = conv_data["messages"][i]

                        # 发送用户消息
                        msg_payload = {
                            "conversation_id": conv_id,
                            "messages": [
                                {"role": "user", "content": user_msg["content"]}
                            ],
                            "model": "openrouter/auto",
                            "stream": False,
                        }

                        async with self.session.post(
                            f"{API_BASE}/chat/completions",
                            headers=headers,
                            json=msg_payload,
                        ) as msg_response:
                            if msg_response.status != 200:
                                self.log("发送消息失败", "ERROR")

                    self.created_data["conversations"].append(
                        {"id": conv_id, "title": conv_data["title"], "owner": username}
                    )
                    self.log(
                        f"创建对话 '{conv_data['title']}' 成功 (ID: {conv_id})",
                        "SUCCESS",
                    )
                    return conv_id
                else:
                    error_data = await response.json()
                    self.log(f"创建对话失败: {error_data.get('detail')}", "ERROR")
                    return None

        except Exception as e:
            self.log(f"创建对话异常: {str(e)}", "ERROR")
            return None

    async def create_all_demo_data(self):
        """创建所有演示数据"""
        self.log("开始创建演示数据...", "INFO")

        # 1. 创建用户
        self.log("========== 创建用户 ==========", "INFO")
        for user in DEMO_USERS:
            await self.create_user(user)

        # 2. 为每个用户创建数据
        for username in self.users_tokens.keys():
            self.log(f"\n========== 为用户 {username} 创建数据 ==========", "INFO")

            # 创建空间
            space_ids = []
            for space in DEMO_SPACES:
                space_id = await self.create_space(username, space)
                if space_id:
                    space_ids.append(space_id)

                    # 在第一个空间上传文档
                    if len(space_ids) == 1:
                        for doc in DEMO_DOCUMENTS:
                            await self.upload_document(username, space_id, doc)

                    # 在每个空间创建笔记
                    for note in DEMO_NOTES[:1]:  # 每个空间创建一个笔记
                        await self.create_note(username, space_id, note)

            # 创建对话
            for conv in DEMO_CONVERSATIONS:
                await self.create_conversation(username, conv)

        # 等待一下让数据处理完成
        await asyncio.sleep(2)

        # 打印总结
        self.print_summary()

    def print_summary(self):
        """打印创建总结"""
        print("\n" + "=" * 70)
        print("📊 演示数据创建总结")
        print("=" * 70)

        print("\n✅ 创建的数据统计：")
        print(f"  - 用户账号: {len(self.users_tokens)} 个")
        print(f"  - 知识空间: {len(self.created_data['spaces'])} 个")
        print(f"  - 文档资料: {len(self.created_data['documents'])} 个")
        print(f"  - 笔记内容: {len(self.created_data['notes'])} 个")
        print(f"  - AI对话: {len(self.created_data['conversations'])} 个")

        print("\n📝 演示账号信息：")
        for user in DEMO_USERS:
            print(f"  - 用户名: {user['username']}")
            print(f"    密码: {user['password']}")
            print(f"    说明: {user['full_name']}")
            print()

        print("💡 使用说明：")
        print("  1. 使用上述账号登录系统")
        print("  2. 查看预创建的空间、文档和笔记")
        print("  3. 体验AI对话功能")
        print("  4. 测试文档搜索和笔记管理")

        # 保存到文件
        self.save_summary_to_file()

    def save_summary_to_file(self):
        """保存总结到文件"""
        summary = {
            "created_at": datetime.now().isoformat(),
            "api_base": API_BASE,
            "demo_accounts": DEMO_USERS,
            "created_data": self.created_data,
            "statistics": {
                "users": len(self.users_tokens),
                "spaces": len(self.created_data["spaces"]),
                "documents": len(self.created_data["documents"]),
                "notes": len(self.created_data["notes"]),
                "conversations": len(self.created_data["conversations"]),
            },
        }

        with open("demo_data_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        self.log("演示数据总结已保存到 demo_data_summary.json", "SUCCESS")


async def main():
    """主函数"""
    print("🚀 SecondBrain 演示数据创建工具")
    print("⏰ 开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🔗 API地址:", API_BASE)
    print("=" * 70)

    async with DemoDataCreator() as creator:
        await creator.create_all_demo_data()

    print("\n✅ 演示数据创建完成！")


if __name__ == "__main__":
    # 支持通过环境变量设置API地址
    if len(sys.argv) > 1:
        API_BASE = sys.argv[1] + "/api/v1"

    asyncio.run(main())
