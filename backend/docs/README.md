# Second Brain 后端文档

Second Brain 是一个 AI 驱动的个人知识管理系统后端，基于 FastAPI 构建。

## 文档索引

- [API 文档](API.md) - 完整的 API 接口说明
- [架构文档](ARCHITECTURE.md) - 系统架构和技术栈

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository>
cd backend

# 复制环境变量配置
cp .env.example .env
```

### 2. 配置 API 密钥

编辑`.env`文件，添加 OpenRouter API 密钥：

```
OPENROUTER_API_KEY=sk-or-xxx
```

### 3. 启动服务

```bash
# 使用Docker Compose启动
docker-compose up -d
```

### 4. 访问服务

- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/api/v1/docs
- 测试账号: `demo_user / Demo123456!`

## 主要功能

- **AI 对话**: 支持 100+AI 模型，包括 GPT-4、Claude、Gemini 等
- **知识管理**: 创建空间组织文档、笔记和对话
- **文档处理**: 支持 PDF、Word、PPT 等格式
- **深度研究**: AI 驱动的自动化研究助手
- **语义搜索**: 基于向量数据库的智能搜索

## 开发说明

### 运行测试

```bash
# 单元测试
docker-compose exec backend pytest tests/unit/ -v

# 集成测试
docker-compose exec backend pytest tests/integration/ -v
```

### 代码检查

```bash
# 格式化
docker-compose exec backend black app/

# 代码检查
docker-compose exec backend ruff check app/
```

### 数据库迁移

```bash
docker-compose exec backend alembic upgrade head
```

## 技术支持

- 查看[API 文档](API.md)了解接口使用
- 查看[架构文档](ARCHITECTURE.md)了解系统设计
- 项目使用`uv`进行 Python 包管理
- 支持 Docker Compose 一键部署
