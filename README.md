# SecondBrain - AI 驱动的知识管理系统

一个基于 AI 的智能知识管理系统，帮助用户高效管理和检索个人知识。

## 功能特性

- 🤖 **AI 对话**：支持多模型对话（OpenAI、Claude、DeepSeek 等）
- 🔍 **深度研究**：使用 Perplexity API 进行深度研究
- 📚 **知识库管理**：文档上传、管理和智能检索
- 📝 **笔记系统**：支持 Markdown 笔记编辑和版本管理
- 🎯 **向量搜索**：基于语义的智能搜索
- 📤 **导出功能**：支持导出为 JSON、Markdown 等格式

## 快速开始

### 环境要求

- Docker 和 Docker Compose
- Python 3.12+（仅开发需要）

### 配置

1. 复制环境变量文件：

```bash
cp backend/.env.example backend/.env
```

2. 编辑 `backend/.env`，添加至少一个 AI API Key：

```env
# 至少配置一个
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
DEEPSEEK_API_KEY=sk-xxx
```

### 启动项目

```bash
# 添加执行权限
chmod +x start.sh test.sh

# 启动所有服务
./start.sh
```

服务启动后访问：

- 前端：http://localhost
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/api/v1/docs
- MinIO 控制台：http://localhost:9001（用户名/密码：minioadmin/minioadmin）

### 运行测试

```bash
./test.sh
```

### 常用命令

```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 清理所有数据（慎用）
docker-compose down -v

# 进入后端容器
docker-compose exec backend bash

# 运行数据库迁移
docker-compose exec backend alembic upgrade head
```

## 技术栈

- **前端**：Vue 3 + TypeScript + Vite
- **后端**：FastAPI + SQLAlchemy + Pydantic
- **数据库**：PostgreSQL（关系数据）+ Qdrant（向量数据）
- **缓存**：Redis
- **存储**：MinIO
- **AI**：支持多种 AI 模型提供商

## 项目结构

```
SecondBrain/
├── frontend/          # 前端代码
├── backend/           # 后端代码
│   ├── app/          # 应用代码
│   ├── tests/        # 测试代码
│   └── alembic/      # 数据库迁移
├── docker-compose.yml # Docker 配置
├── start.sh          # 启动脚本
└── test.sh           # 测试脚本
```

## 开发指南

### 后端开发

```bash
cd backend
# 安装依赖（使用 uv）
uv pip install -r requirements.txt

# 运行开发服务器
uv run uvicorn app.main:app --reload

# 创建新的数据库迁移
docker-compose exec backend alembic revision --autogenerate -m "描述"

# 运行测试
uv run pytest
```

### 前端开发

```bash
cd frontend
# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 部署

本项目使用 Docker Compose 进行部署，非常简单：

1. 将整个项目复制到服务器
2. 配置 `.env` 文件
3. 运行 `./start.sh`

对于生产环境，建议：

- 修改数据库密码
- 配置 HTTPS
- 设置备份策略
- 监控服务状态

## License

MIT License
