# Second Brain 技术文档与架构设计

## 一、系统功能树

```
Second Brain
├── 🏠 主页模块 (Home)
│   ├── 核心界面组件
│   │   ├── 中央输入框
│   │   ├── 快速启动建议
│   │   └── 三栏布局管理
│   ├── 工具栏模块
│   │   ├── Chat模式（纯AI对话）
│   │   ├── Search模式（智能搜索）
│   │   └── Think模式（深度推理）
│   └── 设置区模块
│       ├── 模型选择器
│       ├── 文件上传
│       └── 搜索范围配置
│
├── 🤖 AI代理系统 (AI Agents)
│   ├── 内置代理
│   │   ├── Deep Research Agent
│   │   ├── Wiki Generator Agent
│   │   └── Data Analysis Agent
│   ├── 代理管理
│   │   ├── 自定义代理创建
│   │   ├── 代理市场
│   │   └── 代理编排工作流
│   └── 代理执行引擎
│
├── 📚 知识库管理 (Knowledge Base)
│   ├── Space管理
│   │   ├── Space创建/编辑/删除
│   │   ├── Space元数据管理
│   │   └── Space权限控制
│   ├── 资源管理
│   │   ├── 文档处理
│   │   │   ├── 文档上传/解析
│   │   │   ├── 文档预览
│   │   │   ├── 文档标注
│   │   │   └── 文档翻译
│   │   ├── 网页内容管理
│   │   ├── 多媒体管理
│   │   └── 笔记系统
│   ├── 知识图谱
│   │   ├── 实体识别
│   │   ├── 关系抽取
│   │   └── 图谱可视化
│   └── 对话历史管理
│
├── 👥 协作系统 (Collaboration)
│   ├── 共享管理
│   │   ├── Space共享
│   │   ├── 权限控制
│   │   └── 协作编辑
│   ├── 团队功能
│   │   ├── 团队Space
│   │   ├── 讨论功能
│   │   └── 工作流管理
│   └── 变更追踪
│
├── 👤 用户系统 (User Management)
│   ├── 认证授权
│   │   ├── 用户注册/登录
│   │   ├── OAuth集成
│   │   └── JWT令牌管理
│   ├── 权限管理
│   │   ├── 免费用户限制
│   │   ├── 会员权限
│   │   └── API配额管理
│   └── 用户配置
│       ├── API Key管理
│       ├── 个性化设置
│       └── 使用统计
│
└── ⚙️ 系统设置 (System Settings)
    ├── 模型配置
    │   ├── 模型管理
    │   ├── API配置
    │   └── 成本控制
    ├── 数据管理
    │   ├── 导入导出
    │   ├── 备份恢复
    │   └── 数据安全
    └── 系统监控
        ├── 性能监控
        ├── 日志管理
        └── 错误追踪
```

## 二、技术架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端应用层                              │
│  (React/Vue + TypeScript + TailwindCSS + WebSocket)         │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      API网关层                                │
│              (Nginx + Rate Limiting + CORS)                  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务层                         │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │   认证    │   AI服务  │  知识库   │   协作    │  系统管理 │  │
│  │  服务     │   模块    │   服务    │   服务    │   服务   │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                       数据存储层                              │
│  ┌────────┬────────┬────────┬────────┬────────┬────────┐   │
│  │PostgreSQL│Redis  │MinIO  │Qdrant │Elastic │Kafka   │   │
│  │(主数据库)│(缓存) │(文件) │(向量) │(搜索) │(消息)  │   │
│  └────────┴────────┴────────┴────────┴────────┴────────┘   │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      外部服务集成                             │
│   OpenAI │ Anthropic │ Gemini │ DeepSeek │ Perplexity       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈选择

### 后端技术栈

- **框架**: FastAPI (异步支持、自动文档生成)

- **异步运行时**: Uvicorn + Gunicorn

- **数据库**:
  - PostgreSQL (主数据存储)
  - Redis (缓存、会话、限流)
  - MinIO (文件对象存储)
  - Qdrant (向量数据库)
  - Elasticsearch (全文搜索)
  
- **消息队列**: Kafka/RabbitMQ (异步任务)

- **任务调度**: Celery + Celery Beat

- **认证**: JWT + OAuth2

- **API文档**: OpenAPI/Swagger

### 依赖库

- **ORM**: SQLAlchemy 2.0 (异步支持)

- **数据验证**: Pydantic V2

- **HTTP客户端**: httpx (异步)

- **文档处理**:
  - PyPDF2/pdfplumber (PDF)
  - python-docx (Word)
  - python-pptx (PowerPoint)
  - markdown2 (Markdown)
  
- **NLP处理**:
- LangChain (AI编排)
  - spaCy (实体识别)
- transformers (嵌入)

## 三、后端API设计

### 3.1 API路由结构

```python
# API路由结构
api/
├── v1/
│   ├── auth/          # 认证相关
│   │   ├── register
│   │   ├── login
│   │   ├── refresh
│   │   └── logout
│   │
│   ├── chat/          # 聊天功能
│   │   ├── conversations
│   │   ├── messages
│   │   └── stream
│   │
│   ├── search/        # 搜索功能
│   │   ├── web
│   │   ├── academic
│   │   └── news
│   │
│   ├── think/         # 推理功能
│   │   ├── analyze
│   │   └── reasoning
│   │
│   ├── agents/        # AI代理
│   │   ├── list
│   │   ├── create
│   │   ├── execute
│   │   └── workflows
│   │
│   ├── spaces/        # 知识空间
│   │   ├── CRUD操作
│   │   ├── resources/
│   │   ├── knowledge-graph/
│   │   └── analytics/
│   │
│   ├── documents/     # 文档管理
│   │   ├── upload
│   │   ├── preview
│   │   ├── annotate
│   │   └── translate
│   │
│   ├── collaboration/ # 协作功能
│   │   ├── share
│   │   ├── permissions
│   │   └── activities
│   │
│   └── settings/      # 系统设置
│       ├── profile
│       ├── api-keys
│       └── preferences
```

### 3.2 核心模块设计

### 3.2.1 认证授权模块

```python
# app/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

class AuthService:
    def __init__(self):
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.SECRET_KEY = settings.SECRET_KEY
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
        user = await get_user(username=token_data.username)
        if user is None:
            raise credentials_exception
        return user
```

### 3.2.2 AI服务模块

```python
# app/services/ai_service.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any
import httpx
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class AIProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        pass

    @abstractmethod
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator:
        pass

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = ChatOpenAI(
            api_key=api_key,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        response = await self.client.achat(messages, **kwargs)
        return response.content

    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator:
        async for chunk in self.client.astream(messages, **kwargs):
            yield chunk.content

class AIService:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider,
            "deepseek": DeepSeekProvider
        }

    async def get_provider(self, provider_name: str, api_key: str) -> AIProvider:
        provider_class = self.providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class(api_key)

    async def route_request(self, request: ChatRequest, user: User) -> ChatResponse:
        # 智能路由逻辑
        if request.mode == "auto":
            provider_name, model = await self.auto_select_model(request)
        else:
            provider_name, model = request.provider, request.model

        provider = await self.get_provider(provider_name, user.get_api_key(provider_name))

        if request.stream:
            return StreamingResponse(
                provider.stream_chat(request.messages, model=model),
                media_type="text/event-stream"
            )
        else:
            response = await provider.chat(request.messages, model=model)
            return ChatResponse(content=response, model=model)
```

### 3.2.3 知识库服务模块

```python
# app/services/knowledge_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Space, Document, Note
from app.core.vector_store import VectorStore

class KnowledgeService:
    def __init__(self, db: AsyncSession, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store

    async def create_space(self, user_id: int, space_data: SpaceCreate) -> Space:
        space = Space(
            user_id=user_id,
            name=space_data.name,
            description=space_data.description,
            metadata=space_data.metadata
        )
        self.db.add(space)
        await self.db.commit()
        await self.db.refresh(space)

        # 初始化向量存储集合
        await self.vector_store.create_collection(f"space_{space.id}")

        return space

    async def add_document_to_space(
        self,
        space_id: int,
        file: UploadFile,
        user_id: int
    ) -> Document:
        # 1. 保存文件到对象存储
        file_url = await self.upload_file_to_storage(file)

        # 2. 解析文档内容
        content = await self.parse_document(file)

        # 3. 生成向量嵌入
        embeddings = await self.generate_embeddings(content)

        # 4. 保存到数据库
        document = Document(
            space_id=space_id,
            user_id=user_id,
            filename=file.filename,
            file_url=file_url,
            content=content,
            metadata={
                "size": file.size,
                "content_type": file.content_type
            }
        )
        self.db.add(document)
        await self.db.commit()

        # 5. 存储向量
        await self.vector_store.add_documents(
            collection_name=f"space_{space_id}",
            documents=[{
                "id": str(document.id),
                "content": content,
                "metadata": document.metadata
            }],
            embeddings=embeddings
        )

        return document

    async def search_in_space(
        self,
        space_id: int,
        query: str,
        limit: int = 10
    ) -> List[SearchResult]:
        # 1. 生成查询向量
        query_embedding = await self.generate_embedding(query)

        # 2. 向量搜索
        results = await self.vector_store.search(
            collection_name=f"space_{space_id}",
            query_vector=query_embedding,
            limit=limit
        )

        # 3. 获取文档详情
        document_ids = [r["id"] for r in results]
        documents = await self.db.query(Document).filter(
            Document.id.in_(document_ids)
        ).all()

        return [
            SearchResult(
                document=doc,
                score=result["score"],
                highlight=self.extract_highlight(doc.content, query)
            )
            for doc, result in zip(documents, results)
        ]
```

### 3.2.4 文档处理模块

```python
# app/services/document_service.py
import asyncio
from typing import Dict, Any
from app.core.parsers import PDFParser, DocxParser, PPTXParser

class DocumentService:
    def __init__(self):
        self.parsers = {
            'application/pdf': PDFParser(),
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': DocxParser(),
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': PPTXParser(),
            'text/markdown': MarkdownParser(),
            'text/plain': TextParser()
        }

    async def parse_document(self, file: UploadFile) -> Dict[str, Any]:
        parser = self.parsers.get(file.content_type)
        if not parser:
            raise ValueError(f"Unsupported file type: {file.content_type}")

        content = await file.read()
        return await parser.parse(content)

    async def generate_preview(self, document_id: int, page: int = 1) -> bytes:
        document = await self.get_document(document_id)

        # 根据文档类型生成预览
        if document.content_type == 'application/pdf':
            return await self.generate_pdf_preview(document, page)
        else:
            # 转换为HTML预览
            return await self.generate_html_preview(document)

    async def translate_document(
        self,
        document_id: int,
        target_language: str,
        translation_service: str = "deepseek"
    ) -> Document:
        document = await self.get_document(document_id)

        # 分段翻译
        segments = self.split_document_into_segments(document.content)
        translated_segments = []

        for segment in segments:
            translated = await self.translate_segment(
                segment,
                target_language,
                translation_service
            )
            translated_segments.append(translated)

        # 保存翻译结果
        translated_document = Document(
            space_id=document.space_id,
            user_id=document.user_id,
            filename=f"{document.filename}_translated_{target_language}",
            content="\\n".join(translated_segments),
            parent_id=document.id,
            metadata={
                "source_language": document.metadata.get("language", "auto"),
                "target_language": target_language,
                "translation_service": translation_service
            }
        )

        self.db.add(translated_document)
        await self.db.commit()

        return translated_document
```

### 3.3 数据库设计

```python
# app/models/models.py
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    spaces = relationship("Space", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

class Space(Base):
    __tablename__ = "spaces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="spaces")
    documents = relationship("Document", back_populates="space")
    notes = relationship("Note", back_populates="space")
    conversations = relationship("Conversation", back_populates="space")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    space_id = Column(Integer, ForeignKey("spaces.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_url = Column(String(1000))
    content = Column(Text)
    content_type = Column(String(100))
    metadata = Column(JSON)
    parent_id = Column(Integer, ForeignKey("documents.id"))  # 用于翻译文档
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    space = relationship("Space", back_populates="documents")
    annotations = relationship("Annotation", back_populates="document")
    children = relationship("Document", backref="parent", remote_side=[id])

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    space_id = Column(Integer, ForeignKey("spaces.id"))
    mode = Column(String(20))  # chat, search, think
    title = Column(String(500))
    metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    user = relationship("User", back_populates="conversations")
    space = relationship("Space", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20))  # user, assistant, system
    content = Column(Text)
    model = Column(String(100))
    metadata = Column(JSON)  # 包含引用、来源等
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    conversation = relationship("Conversation", back_populates="messages")
```

### 3.4 WebSocket实时通信

```python
# app/core/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        self.active_connections[user_id].discard(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

    async def broadcast_to_space(self, message: str, space_id: int, user_ids: List[int]):
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)

# WebSocket路由
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    # 验证token
    user = await auth_service.verify_token(token)
    if not user or user.id != user_id:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理不同类型的消息
            if message["type"] == "chat":
                await handle_chat_message(message, user_id, db)
            elif message["type"] == "collaboration":
                await handle_collaboration_message(message, user_id, db)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

## 四、部署架构

### 4.1 容器化部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 后端服务
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/secondbrain
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      - postgres
      - redis
      - minio

  # 数据库服务
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: secondbrain
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # 缓存服务
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  # 对象存储
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

  # 向量数据库
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  # 消息队列
  kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    depends_on:
      - zookeeper

  # Celery Worker
  celery_worker:
    build: .
    command: celery -A app.core.celery worker --loglevel=info
    depends_on:
      - redis
      - postgres

  # Celery Beat
  celery_beat:
    build: .
    command: celery -A app.core.celery beat --loglevel=info
    depends_on:
      - redis
      - postgres

volumes:
  postgres_data:
  redis_data:
  minio_data:
  qdrant_data:
```

### 4.2 生产环境配置

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 基础配置
    APP_NAME: str = "Second Brain"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # 安全配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 数据库配置
    DATABASE_URL: str
    REDIS_URL: str

    # 对象存储
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False

    # 向量数据库
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # API限流
    RATE_LIMIT_FREE_USER: int = 20  # 每日限制
    RATE_LIMIT_PREMIUM_USER: int = 200  # 每日限制

    # AI提供商配置
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    PERPLEXITY_API_KEY: Optional[str] = None

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"

settings = Settings()
```

## 五、开发计划与里程碑

### Phase 1: 基础架构 (2-3周)

- [ ]  项目初始化和基础配置
- [ ]  数据库模型设计和迁移
- [ ]  认证授权系统
- [ ]  基础API框架搭建
- [ ]  Docker环境配置

### Phase 2: 核心功能 (4-5周)

- [ ]  Chat模式实现
- [ ]  Search模式集成
- [ ]  Think模式开发
- [ ]  文档上传和解析
- [ ]  Space管理功能

### Phase 3: 高级功能 (4-5周)

- [ ]  AI Agent系统
- [ ]  知识图谱构建
- [ ]  文档翻译功能
- [ ]  协作功能
- [ ]  WebSocket实时通信

### Phase 4: 优化与扩展 (3-4周)

- [ ]  性能优化
- [ ]  缓存策略
- [ ]  监控和日志
- [ ]  测试覆盖
- [ ]  部署和运维

## 六、关键技术挑战与解决方案

### 6.1 大文件处理

- **挑战**: 处理大型PDF、视频等文件

- **解决方案**:
- 使用流式上传
  - 分块处理
- 后台异步任务

### 6.2 实时协作

- **挑战**: 多用户同时编辑冲突

- **解决方案**:
- 操作转换(OT)算法
  - CRDT数据结构
- WebSocket实时同步

### 6.3 AI响应延迟

- **挑战**: AI模型响应时间长

- **解决方案**:
- 流式响应
  - 缓存常见查询
- 模型预热

### 6.4 向量搜索性能

- **挑战**: 大规模向量搜索效率

- **解决方案**:
- 向量索引优化
  - 分片策略
- 混合搜索(向量+关键词)