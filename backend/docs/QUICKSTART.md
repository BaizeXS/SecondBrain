# Second Brain 快速启动指南

## 前置要求

- Docker (版本 20.10+)
- Docker Compose (版本 1.29+)
- Python 3.12+ (可选，用于本地开发)
- OpenRouter API 密钥（用于访问100+AI模型）
- Perplexity API 密钥（用于Deep Research功能）

## 快速启动

### 1. 克隆项目
```bash
git clone <repository-url>
cd backend
```

### 2. 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env` 文件，添加必要的 API 密钥：

```env
# 必需：OpenRouter API密钥（统一AI网关）
OPENROUTER_API_KEY=sk-or-...

# 必需：用于Deep Research功能
PERPLEXITY_API_KEY=pplx-...

# 可选：直接使用特定AI提供商（如果不使用OpenRouter）
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=AIza...
# DEEPSEEK_API_KEY=sk-...

# 系统密钥（建议修改）
SECRET_KEY=your-secret-key-here
```

### 3. 启动服务
```bash
./scripts/start.sh
```

或手动启动：
```bash
docker-compose up -d
```

### 4. 访问应用

- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/api/v1/docs
- Redoc 文档: http://localhost:8000/api/v1/redoc
- MinIO 控制台: http://localhost:9001
  - 用户名: minioadmin
  - 密码: minioadmin
- PostgreSQL: localhost:5432
  - 数据库: secondbrain
  - 用户: secondbrain
  - 密码: secondbrain123
- Redis: localhost:6379
- Qdrant: localhost:6333

## 常用命令

### 查看日志
```bash
# 所有服务
docker-compose logs -f

# 仅后端服务
docker-compose logs -f backend
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart backend
```

### 清理数据（谨慎使用）
```bash
docker-compose down
rm -rf ./data
```

### 重新构建镜像
```bash
docker-compose build --no-cache
```

### 进入容器调试
```bash
docker-compose exec backend bash
```

### 手动运行数据库迁移
```bash
docker-compose exec backend alembic upgrade head
```

## 数据存储

所有数据都存储在 `./data` 目录下：
- `./data/postgres` - PostgreSQL 数据（用户、空间、对话等）
- `./data/redis` - Redis 数据（会话、缓存、速率限制）
- `./data/minio` - MinIO 文件存储（上传的文档）
- `./data/qdrant` - Qdrant 向量数据（文档嵌入、语义搜索）

## 初始演示数据

创建演示数据以快速体验系统功能：
```bash
# 运行演示数据创建脚本
docker-compose exec backend python examples/create_demo_data.py
```

演示账号：
- 用户名: demo_user / 密码: Demo123456!
- 用户名: teacher_demo / 密码: Teacher123456!

## 开发说明

### 使用uv进行包管理
本项目使用 `uv` 而不是 `pip` 进行Python包管理：

```bash
# 安装依赖
docker-compose exec backend uv pip install -r requirements.txt

# 安装新包
docker-compose exec backend uv pip install package_name

# 运行测试
docker-compose exec backend uv run pytest

# 代码格式化
docker-compose exec backend uv run black app/
docker-compose exec backend uv run ruff check app/ --fix
```

后端服务已配置热重载，修改代码后会自动重启。

### 项目结构
```
backend/
├── app/                    # 应用代码
│   ├── api/v1/            # API v1版本
│   │   └── endpoints/     # 端点模块（11个路由器）
│   ├── core/              # 核心配置
│   │   ├── auth.py       # JWT认证
│   │   ├── config.py     # 系统配置
│   │   └── database.py   # 数据库连接
│   ├── crud/              # 数据库CRUD操作
│   ├── models/            # SQLAlchemy数据模型
│   ├── schemas/           # Pydantic数据模式
│   └── services/          # 业务逻辑层
│       ├── ai_service.py  # AI提供商抽象
│       ├── openrouter_service.py # OpenRouter集成
│       └── ...           # 其他服务
├── alembic/               # 数据库迁移
├── tests/                 # 测试套件
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── data/                  # 持久化数据（gitignore）
├── docs/                  # 项目文档
├── examples/              # 示例代码
├── scripts/               # 实用脚本
├── docker-compose.yml     # Docker编排
├── Dockerfile            # Docker镜像
├── pyproject.toml        # Python项目配置
└── requirements.txt      # Python依赖
```

## 故障排除

### 端口被占用
修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "8001:8000"  # 改为其他端口
```

### 数据库连接失败
确保 PostgreSQL 服务已启动：
```bash
docker-compose ps postgres
docker-compose logs postgres
```

### API 密钥未配置
确保 `.env` 文件中配置了必需的 API 密钥：
- `OPENROUTER_API_KEY` - 用于AI对话功能
- `PERPLEXITY_API_KEY` - 用于Deep Research功能

### 密码验证失败
密码必须满足以下要求：
- 至少8个字符
- 包含大写字母
- 包含小写字母
- 包含数字

### AI模型错误
确保使用正确的OpenRouter模型格式：
- `openrouter/auto` - 自动选择最佳模型
- `openrouter/openai/gpt-4` - 指定GPT-4
- `openrouter/anthropic/claude-3-opus` - 指定Claude 3

### 文件上传失败
- 检查MinIO服务是否正常运行
- 确认文件大小不超过限制（默认50MB）
- 支持的格式：PDF, DOCX, PPTX, TXT, MD等

## 测试API

### 快速测试
```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 使用HTTPie测试登录
http --form POST http://localhost:8000/api/v1/auth/login \
  username=demo_user \
  password=Demo123456!
```

### 完整测试
```bash
# 运行完整的API测试
docker-compose exec backend python test_all_apis_100_percent.py
```