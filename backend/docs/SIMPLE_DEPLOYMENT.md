# SecondBrain 简单部署指南

适用于毕业设计项目的最简化部署方案

## 🎯 目标

让项目能在任何服务器上快速运行起来，不需要复杂配置。

## 📋 服务器要求

- **最低配置**：2核4G内存，40G硬盘
- **推荐配置**：4核8G内存，80G硬盘  
- **系统**：Ubuntu 20.04/22.04 或 CentOS 7/8
- **需要开放端口**：80, 443（HTTPS）, 8000（后端API）

## 🚀 方案一：Docker Compose 一键部署（推荐）

这是最简单的方案，所有服务打包在一起。

### 1. 准备服务器

```bash
# 安装 Docker（Ubuntu）
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 创建部署文件

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  # 后端服务
  backend:
    image: secondbrain-backend:latest
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://secondbrain:secondbrain123@postgres:5432/secondbrain
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=your-secret-key-change-this
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - ALLOWED_ORIGINS=http://localhost,http://你的域名
    volumes:
      - ./backend/data:/app/data
    depends_on:
      - postgres
      - redis
      - qdrant
      - minio
    restart: always

  # 前端服务
  frontend:
    image: secondbrain-frontend:latest
    build: ./frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_BASE_URL=http://你的域名:8000/api/v1
    depends_on:
      - backend
    restart: always

  # 数据库
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=secondbrain
      - POSTGRES_USER=secondbrain
      - POSTGRES_PASSWORD=secondbrain123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  # 缓存
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always

  # 向量数据库
  qdrant:
    image: qdrant/qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    restart: always

  # 文件存储
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    restart: always

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  minio_data:
```

### 3. 创建简单的 Dockerfile

**后端 Dockerfile**：
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# 复制文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 启动
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile**：
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### 4. 一键部署脚本

创建 `deploy.sh`：

```bash
#!/bin/bash

echo "🚀 开始部署 SecondBrain..."

# 检查环境变量
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  请设置 OPENROUTER_API_KEY 环境变量"
    echo "export OPENROUTER_API_KEY=your_key_here"
    exit 1
fi

# 构建镜像
echo "📦 构建 Docker 镜像..."
docker-compose build

# 启动服务
echo "🔧 启动所有服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 运行数据库迁移
echo "📊 初始化数据库..."
docker-compose exec backend alembic upgrade head

# 创建演示数据（可选）
echo "📝 创建演示数据..."
docker-compose exec backend python tools/demo_data_creator.py

echo "✅ 部署完成！"
echo ""
echo "访问地址："
echo "  前端: http://你的服务器IP"
echo "  后端API: http://你的服务器IP:8000"
echo "  API文档: http://你的服务器IP:8000/api/v1/docs"
echo ""
echo "默认账号："
echo "  用户名: demo_user"
echo "  密码: Demo123456!"
```

### 5. 执行部署

```bash
# 设置环境变量
export OPENROUTER_API_KEY=your_key_here

# 执行部署
chmod +x deploy.sh
./deploy.sh
```

## 🛠️ 方案二：直接部署（不用 Docker）

如果不想用 Docker，可以直接在服务器上运行。

### 1. 安装依赖

```bash
# Python 3.12
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# PostgreSQL
sudo apt install postgresql postgresql-contrib

# Redis
sudo apt install redis-server

# 其他服务可以用 Docker 单独运行
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
docker run -d --name minio -p 9000:9000 -p 9001:9001 minio/minio server /data
```

### 2. 部署后端

```bash
# 克隆代码
git clone your-repo
cd secondbrain/backend

# 创建虚拟环境
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 部署前端

```bash
cd ../frontend

# 安装依赖
npm install

# 构建
npm run build

# 使用 nginx 托管
sudo apt install nginx
sudo cp -r dist/* /var/www/html/
```

## 📝 最简配置清单

### 必需的环境变量

```bash
# .env 文件
DATABASE_URL=postgresql://user:pass@localhost/secondbrain
SECRET_KEY=any-random-string-change-this
OPENROUTER_API_KEY=your-openrouter-key
```

### Nginx 配置（如需要）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🚨 常见问题

### 1. 端口被占用
```bash
# 查看端口占用
sudo lsof -i :8000
# 修改 docker-compose.yml 中的端口映射
```

### 2. 内存不足
```bash
# 添加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. 权限问题
```bash
# 给 Docker 数据目录权限
sudo chown -R 1000:1000 ./data
```

## ✅ 验证部署

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 测试 API
curl http://localhost:8000/health

# 测试前端
curl http://localhost
```

## 💡 给答辩的建议

1. **架构说明**：
   - 采用微服务架构，各组件独立部署
   - 使用 Docker 容器化，保证环境一致性
   - 前后端分离，便于独立开发和扩展

2. **技术亮点**：
   - 支持多种 AI 模型接入
   - 向量数据库实现智能搜索
   - Deep Research 功能展示 AI 应用能力

3. **部署优势**：
   - 一键部署，降低使用门槛
   - 资源占用优化，适合普通服务器
   - 完整的监控和日志系统

---

**总结**：这个简化方案去掉了所有企业级的复杂配置，专注于让项目快速运行起来。整个部署过程不超过 10 分钟，非常适合毕业设计项目的演示和答辩。