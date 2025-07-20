# SecondBrain 系统架构文档

## 系统概述

SecondBrain 是一个基于微服务架构的 AI 驱动知识管理系统，采用 FastAPI 构建，支持多种 AI 模型和完整的文档处理能力。

## 技术栈

### 核心框架

- **Web 框架**: FastAPI (异步支持)
- **服务器**: Uvicorn
- **Python 版本**: 3.11+

### 数据存储

- **主数据库**: PostgreSQL + asyncpg
- **ORM**: SQLAlchemy 2.0 (异步模式)
- **迁移工具**: Alembic
- **缓存**: Redis
- **对象存储**: MinIO
- **向量数据库**: Qdrant

### AI/ML 集成

- **统一接口**: OpenRouter (100+模型)
- **本地模型**: Ollama
- **深度研究**: Perplexity API
- **向量嵌入**: Sentence Transformers
- **框架**: LangChain, LangGraph

### 文档处理

- **PDF**: pdfplumber
- **Office**: python-docx, python-pptx, openpyxl
- **Web**: BeautifulSoup4, httpx
- **Markdown**: markdown
- **代码**: 支持多种编程语言

## 系统架构图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React前端     │────▶│   FastAPI       │────▶│   服务层        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                         │
                        ┌──────┴──────┐          ┌──────┴──────┐
                        │  JWT认证    │           │  AI服务     │
                        │  速率限制    │           │ 文档处理    │
                        └─────────────┘          │  向量搜索    │
                                                 └─────────────┘
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ PostgreSQL  │    │    Redis    │    │    MinIO    │    │   Qdrant    │
│  关系数据    │    │  缓存/会话   │    │  文件存储     │    │  向量检索    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 目录结构

```
backend/
├── app/
│   ├── api/v1/          # API端点
│   │   ├── endpoints/   # 各模块端点
│   │   └── api.py       # 路由聚合
│   ├── core/            # 核心功能
│   │   ├── auth.py      # JWT认证
│   │   ├── config.py    # 配置管理
│   │   ├── database.py  # 数据库连接
│   │   └── rate_limiter.py # 速率限制
│   ├── crud/            # 数据库操作
│   ├── models/          # 数据模型
│   ├── schemas/         # Pydantic模式
│   ├── services/        # 业务逻辑
│   └── main.py         # 应用入口
├── alembic/            # 数据库迁移
├── tests/              # 测试套件
├── scripts/            # 工具脚本
└── docker-compose.yml  # 容器编排
```

## 核心模块设计

### 1. 认证与授权

```python
# JWT Token认证流程
1. 用户登录 -> 验证凭据
2. 生成access_token和refresh_token
3. Token存储在Redis中
4. 每次请求验证Token
5. Token过期自动刷新
```

### 2. AI 服务抽象层

```python
class AIProvider(ABC):
    """统一的AI提供商接口"""
    async def chat(...) -> str
    async def stream_chat(...) -> AsyncGenerator[str, None]
    async def get_embedding(...) -> List[float]
```

支持的提供商：

- OpenRouter (默认，聚合 100+模型)
- OpenAI
- Anthropic
- Google
- DeepSeek
- Ollama (本地模型)

### 3. 文档处理流水线

```
上传文档 → 存储到MinIO → 提取文本内容 → 分块处理 → 生成嵌入 → 存储到Qdrant
    ↓           ↓              ↓            ↓          ↓           ↓
  验证      生成唯一ID    支持多种格式   智能分块   向量化    可搜索
```

### 4. 对话系统

特性：

- OpenAI 兼容的 API (`/chat/completions`)
- 流式响应 (SSE)
- 消息分支管理
- 空间上下文关联
- 多模型支持

### 5. 向量搜索架构

```python
# 向量搜索流程
1. 文档分块: chunk_size=1000, overlap=200
2. 生成嵌入: OpenAI/Sentence-transformers
3. 存储: Qdrant with metadata
4. 搜索: 混合搜索(向量+过滤器)
5. 排序: 相似度评分
```

## 数据模型

### 核心实体关系

```
User ──┬── Space ──┬── Document ── Annotation
       │           ├── Note ────── NoteVersion
       │           └── Conversation ── Message
       ├── Agent ────── AgentExecution
       └── APIKey
```

### 关键设计决策

1. **对话与空间的关系**

   - AI Chat 页面的对话独立存在 (space_id = NULL)
   - 只有 Space 内或 Deep Research 创建的对话关联空间
   - 类似搜索引擎的快速查询模式

2. **Agent 系统设计**

   - 支持 Prompt Agent (简单提示词)
   - 预留 LangGraph Agent 接口
   - 用户可创建自定义 Agent

3. **文档版本控制**
   - Note 支持版本历史
   - 文档更新保留原始文件
   - 标注独立于文档版本

## API 设计原则

### RESTful 规范

- 使用 HTTP 动词表示操作
- 资源使用复数名词
- 嵌套资源保持层级简单
- 统一的错误响应格式

### 分页与过滤

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_next": true
}
```

### 流式响应

```
GET /api/v1/chat/completions?stream=true

data: {"content": "Hello"}
data: {"content": " World"}
data: [DONE]
```

## 性能优化策略

### 1. 数据库优化

- 连接池配置
- 适当的索引
- 查询优化 (避免 N+1)
- 异步数据库操作

### 2. 缓存策略

- Redis 缓存热点数据
- 用户会话缓存
- API 响应缓存
- 向量搜索结果缓存

### 3. 异步处理

- 全异步 API 端点
- 后台任务队列
- 并发请求处理
- 非阻塞 I/O

### 4. 文件处理

- 流式上传/下载
- 异步文本提取
- 批量向量生成
- 智能分块策略

## 安全架构

### 1. 认证安全

- JWT with RS256
- Token 刷新机制
- Redis 黑名单
- 会话管理

### 2. 数据安全

- 密码 bcrypt 加密
- API 密钥加密存储
- 文件访问控制
- SQL 注入防护

### 3. 访问控制

- 基于角色的权限
- 空间级别权限
- API 速率限制
- IP 白名单(可选)

## 部署架构

### Docker Compose 部署

```yaml
services:
  backend:
    build: .
    depends_on: [postgres, redis, minio, qdrant]
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
      - REDIS_URL=redis://redis:6379
    ports:
      - "8000:8000"

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
```

### 生产部署建议

1. **基础设施**

   - Kubernetes 编排
   - 负载均衡(Nginx/Traefik)
   - 自动扩缩容
   - 健康检查

2. **监控告警**

   - Prometheus 指标
   - Grafana 仪表板
   - 日志聚合(ELK)
   - 错误追踪(Sentry)

3. **数据备份**
   - 定时数据库备份
   - MinIO 数据同步
   - 向量数据库快照
   - 灾难恢复计划

## 扩展性设计

### 1. 微服务就绪

- 服务间松耦合
- API 网关模式
- 事件驱动架构
- 独立部署能力

### 2. 插件化架构

- AI 提供商插件
- 文档处理器插件
- 导出格式插件
- 认证方式插件

### 3. 水平扩展

- 无状态设计
- 会话外部存储
- 负载均衡就绪
- 数据库读写分离

## 未来规划

1. **功能扩展**

   - GraphQL API 支持
   - WebSocket 实时协作
   - 移动端 API 优化
   - 批量操作 API

2. **性能提升**

   - 向量索引优化
   - 缓存命中率提升
   - 异步任务优化
   - 数据库分片

3. **AI 能力**
   - LangGraph 集成
   - 多模态处理
   - 自定义模型训练
   - 智能推荐系统
