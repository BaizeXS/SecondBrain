# Second Brain 后端架构

## 技术栈

### 核心框架
- **FastAPI** - 高性能异步Web框架
- **Python 3.12** - 编程语言  
- **SQLAlchemy 2.0** - 异步ORM
- **Pydantic 2.0** - 数据验证

### 数据存储
- **PostgreSQL** - 主数据库
- **Redis** - 缓存和会话
- **MinIO** - 文件存储
- **Qdrant** - 向量数据库

### AI集成
- **OpenRouter** - 统一AI网关（支持100+模型）
- **LangChain** - AI应用框架
- **Sentence Transformers** - 文本嵌入

## 项目结构

```
app/
├── api/v1/endpoints/    # API端点（12个模块）
├── core/               # 核心功能（认证、配置、数据库）
├── models/             # 数据模型
├── schemas/            # 请求/响应模式
├── crud/               # 数据库操作
├── services/           # 业务逻辑
└── main.py            # 应用入口
```

## 主要模块

### 1. 认证系统
- JWT令牌认证（访问令牌 + 刷新令牌）
- 基于角色的访问控制
- 密码bcrypt加密

### 2. 知识管理
- **Spaces** - 知识空间组织
- **Documents** - 文档上传和处理
- **Notes** - 笔记（支持版本控制）
- **Annotations** - 文档标注

### 3. AI功能
- **Chat** - AI对话（支持流式响应）
- **Deep Research** - 深度研究代理
- **Ollama** - 本地模型支持

### 4. 数据处理
- 支持PDF、Word、PPT等多种格式
- 文本提取和向量化
- 语义搜索

## 数据库设计

### 核心表
- `users` - 用户信息和配置
- `spaces` - 知识空间
- `documents` - 文档元数据
- `notes` - 笔记内容
- `conversations` - 对话记录
- `messages` - 消息（支持分支）

### 特色功能
- 时间戳自动管理
- 文档父子关系
- 笔记版本历史
- 消息分支管理

## 部署架构

### Docker容器
```yaml
services:
  backend:      # FastAPI应用
  postgres:     # 数据库
  redis:        # 缓存
  minio:        # 文件存储
  qdrant:       # 向量数据库
  frontend:     # Web界面
```

### 环境配置
- 使用`.env`文件管理配置
- 支持多环境部署
- 容器化一键启动

## 开发规范

### 代码质量
- Black代码格式化
- Ruff代码检查
- MyPy类型检查
- Pytest单元测试

### API设计
- RESTful风格
- 统一错误处理
- 请求限流保护
- Swagger文档自动生成

## 性能优化

- 异步数据库操作
- Redis缓存策略
- 连接池管理
- 流式响应支持