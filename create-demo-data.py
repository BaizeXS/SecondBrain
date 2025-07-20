#!/usr/bin/env python3
"""
创建演示数据脚本
用于毕业设计展示
"""
import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.models import User, Space, Note, Conversation, Message, Agent
from app.core.security import get_password_hash

# 演示数据配置
DEMO_USERS = [
    {
        "username": "demo",
        "email": "demo@example.com",
        "password": "Demo123!",
        "full_name": "演示用户"
    },
    {
        "username": "teacher",
        "email": "teacher@demo.com",
        "password": "Teacher123!",
        "full_name": "指导老师"
    },
    {
        "username": "student",
        "email": "student@demo.com", 
        "password": "Student123!",
        "full_name": "学生助手"
    }
]

DEMO_SPACES = [
    {
        "name": "人工智能研究",
        "description": "收集和整理关于AI最新技术的资料，包括深度学习、NLP、计算机视觉等",
        "tags": ["AI", "深度学习", "研究"],
        "is_public": True
    },
    {
        "name": "毕业论文资料",
        "description": "毕业设计相关的文献、代码和笔记",
        "tags": ["毕设", "论文", "学习"],
        "is_public": False
    },
    {
        "name": "技术博客草稿",
        "description": "准备发布的技术文章和教程",
        "tags": ["博客", "写作", "分享"],
        "is_public": True
    }
]

DEMO_NOTES = [
    {
        "title": "SecondBrain 系统架构设计",
        "content": """# SecondBrain 系统架构设计

## 1. 整体架构
SecondBrain 采用前后端分离的架构设计：
- **前端**：React + TypeScript
- **后端**：FastAPI + Python
- **数据库**：PostgreSQL + Redis
- **向量数据库**：Qdrant
- **对象存储**：MinIO

## 2. 核心功能模块
### 2.1 AI 聊天模块
- 支持多模型切换（OpenAI、Anthropic、Google等）
- 流式响应
- 上下文管理

### 2.2 知识库管理
- 文档上传和解析
- 向量化存储
- 智能检索

### 2.3 深度研究
- 集成 Perplexity API
- 自动生成研究报告
- 来源引用

## 3. 技术亮点
- 异步架构，高并发支持
- 模块化设计，易于扩展
- Docker 容器化部署
""",
        "space_id": 1,
        "tags": ["架构", "设计", "技术"]
    },
    {
        "title": "向量数据库技术调研",
        "content": """# 向量数据库技术调研

## 主流向量数据库对比

### 1. Qdrant
- **优点**：性能优秀，API 友好，支持过滤
- **缺点**：生态相对较小
- **适用场景**：中小规模应用

### 2. Pinecone
- **优点**：完全托管，易于使用
- **缺点**：成本较高
- **适用场景**：企业级应用

### 3. Weaviate
- **优点**：功能丰富，支持多种向量化方法
- **缺点**：资源消耗较大
- **适用场景**：复杂查询需求

## 最终选择
选择 Qdrant 的原因：
1. 开源免费
2. 性能满足需求
3. 部署简单
4. 文档完善
""",
        "space_id": 1,
        "tags": ["向量数据库", "技术选型", "Qdrant"]
    },
    {
        "title": "会议记录：毕设中期检查",
        "content": """# 毕设中期检查会议记录

**时间**：2024年3月15日 14:00-15:30
**地点**：教研室会议室
**参会人员**：指导老师、答辩组老师

## 进展汇报
1. 完成了系统的基础架构搭建
2. 实现了 AI 对话功能
3. 完成了文档管理模块
4. 正在开发深度研究功能

## 老师建议
1. 加强系统的创新点说明
2. 补充更多的测试用例
3. 完善用户体验设计
4. 准备详细的演示视频

## 下一步计划
- [ ] 完成深度研究功能
- [ ] 编写完整的测试用例
- [ ] 优化前端界面
- [ ] 准备答辩PPT
""",
        "space_id": 2,
        "tags": ["会议", "毕设", "进展"]
    }
]

DEMO_CONVERSATIONS = [
    {
        "title": "了解 SecondBrain",
        "messages": [
            {
                "role": "user",
                "content": "请介绍一下 SecondBrain 系统的主要功能"
            },
            {
                "role": "assistant", 
                "content": """SecondBrain 是一个智能知识管理系统，主要功能包括：

1. **AI 对话助手**
   - 支持多种 AI 模型（OpenAI、Anthropic、Google 等）
   - 可以进行智能对话和问答
   - 支持上下文记忆

2. **知识库管理**
   - 创建多个知识空间（Space）
   - 上传和管理文档（PDF、Word、TXT等）
   - 智能搜索和检索

3. **深度研究功能**
   - 基于 Perplexity API
   - 自动搜索和整理资料
   - 生成研究报告

4. **笔记管理**
   - Markdown 格式支持
   - 标签分类
   - 全文搜索

5. **文件分析**
   - 上传文件后可以基于内容问答
   - 支持多种文件格式
   - 智能总结和提取

这个系统的目标是成为你的"第二大脑"，帮助你更好地管理和利用知识！"""
            },
            {
                "role": "user",
                "content": "深度研究功能是如何工作的？"
            },
            {
                "role": "assistant",
                "content": """深度研究功能的工作流程如下：

1. **输入研究主题**
   - 用户在聊天界面选择"深度研究"模式
   - 输入想要研究的主题或问题

2. **自动搜索和分析**
   - 系统调用 Perplexity API
   - 搜索互联网上的相关资料
   - 分析和整理信息

3. **生成研究报告**
   - 自动创建一个新的知识空间
   - 生成结构化的研究报告
   - 包含关键发现、详细分析和来源引用

4. **保存和管理**
   - 研究结果自动保存
   - 可以继续在这个空间内深入探讨
   - 支持导出和分享

**使用场景举例**：
- 技术调研："最新的向量数据库技术对比"
- 市场分析："2024年AI行业发展趋势"
- 学术研究："深度学习在医疗领域的应用"

这个功能特别适合需要快速了解某个领域或收集资料的场景！"""
            }
        ]
    },
    {
        "title": "技术问题讨论",
        "messages": [
            {
                "role": "user",
                "content": "FastAPI 和 Flask 相比有什么优势？"
            },
            {
                "role": "assistant",
                "content": """FastAPI 相比 Flask 有以下主要优势：

## 1. **性能优势**
- FastAPI 基于 Starlette 和 Pydantic，性能接近 NodeJS 和 Go
- 原生支持异步（async/await）
- Flask 需要额外配置才能支持异步

## 2. **自动 API 文档**
- 自动生成交互式 API 文档（Swagger UI）
- 自动生成 ReDoc 文档
- Flask 需要额外安装扩展

## 3. **类型验证**
```python
# FastAPI - 自动验证
@app.post("/items/")
async def create_item(item: Item):
    return item

# Flask - 手动验证
@app.route("/items/", methods=["POST"])
def create_item():
    data = request.get_json()
    # 需要手动验证...
```

## 4. **现代 Python 特性**
- 基于 Python 3.6+ 类型提示
- 更好的 IDE 支持
- 自动补全和错误检查

## 5. **内置功能**
- WebSocket 支持
- 后台任务
- 依赖注入系统

**选择建议**：
- 新项目推荐 FastAPI
- 老项目或简单应用可以继续用 Flask"""
            }
        ]
    }
]

async def create_demo_data():
    """创建演示数据"""
    async with SessionLocal() as db:
        print("🚀 开始创建演示数据...")
        
        # 1. 创建用户
        print("\n👤 创建演示用户...")
        users = []
        for user_data in DEMO_USERS:
            # 检查用户是否存在
            result = await db.execute(
                select(User).filter(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(30, 90))
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                users.append(user)
                print(f"  ✅ 创建用户: {user.email}")
            else:
                users.append(existing_user)
                print(f"  ⏭️  用户已存在: {existing_user.email}")
        
        # 2. 创建知识空间
        print("\n📁 创建知识空间...")
        spaces = []
        for i, space_data in enumerate(DEMO_SPACES):
            # 为不同用户创建空间
            user = users[i % len(users)]
            
            space = Space(
                name=space_data["name"],
                description=space_data["description"],
                user_id=user.id,
                is_public=space_data["is_public"],
                tags=space_data["tags"],
                created_at=datetime.utcnow() - timedelta(days=random.randint(20, 60))
            )
            db.add(space)
            await db.commit()
            await db.refresh(space)
            spaces.append(space)
            print(f"  ✅ 创建空间: {space.name}")
        
        # 3. 创建笔记
        print("\n📝 创建笔记...")
        for note_data in DEMO_NOTES:
            # 确保 space_id 有效
            space_id = note_data.get("space_id", 1)
            if space_id <= len(spaces):
                space = spaces[space_id - 1]
                user = users[0]  # 使用第一个用户
                
                note = Note(
                    title=note_data["title"],
                    content=note_data["content"],
                    user_id=user.id,
                    space_id=space.id,
                    tags=note_data.get("tags", []),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(5, 30))
                )
                db.add(note)
                print(f"  ✅ 创建笔记: {note.title}")
        
        await db.commit()
        
        # 4. 创建对话
        print("\n💬 创建演示对话...")
        for conv_data in DEMO_CONVERSATIONS:
            user = users[0]  # 使用演示用户
            
            # 创建对话
            conversation = Conversation(
                user_id=user.id,
                title=conv_data["title"],
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            
            # 创建消息
            for i, msg_data in enumerate(conv_data["messages"]):
                message = Message(
                    conversation_id=conversation.id,
                    role=msg_data["role"],
                    content=msg_data["content"],
                    model="gpt-4" if msg_data["role"] == "assistant" else None,
                    created_at=conversation.created_at + timedelta(minutes=i * 2)
                )
                db.add(message)
            
            print(f"  ✅ 创建对话: {conversation.title}")
        
        await db.commit()
        
        # 5. 确保有默认 Agent
        print("\n🤖 检查 AI Agents...")
        result = await db.execute(select(Agent))
        agents = result.scalars().all()
        
        if not agents:
            default_agents = [
                {
                    "name": "通用助手",
                    "description": "通用 AI 助手，可以回答各种问题",
                    "agent_type": "general",
                    "is_active": True
                },
                {
                    "name": "深度研究",
                    "description": "深度研究助手，帮助你搜索和整理资料",
                    "agent_type": "research",
                    "is_active": True
                },
                {
                    "name": "写作助手",
                    "description": "帮助你进行创意写作和文案创作",
                    "agent_type": "writing",
                    "is_active": True
                },
                {
                    "name": "代码专家",
                    "description": "编程助手，帮助你解决代码问题",
                    "agent_type": "coding",
                    "is_active": True
                }
            ]
            
            for agent_data in default_agents:
                agent = Agent(**agent_data)
                db.add(agent)
                print(f"  ✅ 创建 Agent: {agent.name}")
            
            await db.commit()
        else:
            print(f"  ℹ️  已有 {len(agents)} 个 Agents")
        
        print("\n✅ 演示数据创建完成！")
        print("\n📊 数据统计：")
        print(f"  - 用户数: {len(users)}")
        print(f"  - 空间数: {len(spaces)}")
        print(f"  - 笔记数: {len(DEMO_NOTES)}")
        print(f"  - 对话数: {len(DEMO_CONVERSATIONS)}")
        
        print("\n🔑 测试账号：")
        for user in DEMO_USERS:
            print(f"  - {user['email']} / {user['password']}")

if __name__ == "__main__":
    asyncio.run(create_demo_data())