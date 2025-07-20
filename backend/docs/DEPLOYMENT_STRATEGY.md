# SecondBrain 部署策略指南

## 🚀 推荐方案：Docker 容器化部署

### 为什么选择 Docker？

**优点：**
- ✅ 环境一致性：开发、测试、生产环境完全一致
- ✅ 快速部署：一键启动所有服务
- ✅ 易于扩展：可以轻松水平扩展
- ✅ 版本管理：镜像版本化，便于回滚
- ✅ 资源隔离：各服务独立运行
- ✅ 跨平台：支持各种云服务商

**适合场景：**
- 中小型团队
- 快速迭代
- 多环境部署
- 云原生架构

## 📦 Docker 部署方案

### 方案一：Docker Compose 部署（推荐）

最简单直接，适合单机部署。

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # 前端服务
  frontend:
    build: ./frontend
    image: secondbrain-frontend:latest
    ports:
      - "80:80"
    environment:
      - API_URL=http://backend:8000
    depends_on:
      - backend
    restart: always

  # 后端服务
  backend:
    build: ./backend
    image: secondbrain-backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    depends_on:
      - postgres
      - redis
      - qdrant
      - minio
    restart: always

  # 数据库服务
  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=your_secure_password
    restart: always

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always

  qdrant:
    image: qdrant/qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    restart: always

  minio:
    image: minio/minio
    volumes:
      - minio_data:/data
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=your_secure_password
    command: server /data
    restart: always

  # Nginx 反向代理（可选）
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: always

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  minio_data:
```

### 方案二：Kubernetes 部署（大规模）

适合需要高可用、自动扩展的场景。

```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secondbrain-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: secondbrain-backend
  template:
    metadata:
      labels:
        app: secondbrain-backend
    spec:
      containers:
      - name: backend
        image: your-registry/secondbrain-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

### 方案三：云服务商托管（最简单）

使用 PaaS 服务，如：
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- 阿里云容器服务

## 🛠️ 实施步骤

### 1. 准备 Dockerfile

**后端 Dockerfile：**
```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 运行应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile：**
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# 生产环境
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 2. 环境配置

创建 `.env.production`：
```bash
# API Keys
OPENROUTER_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/secondbrain

# Security
SECRET_KEY=your_secure_secret_key

# Services
REDIS_URL=redis://redis:6379
MINIO_ENDPOINT=minio:9000
QDRANT_HOST=qdrant
```

### 3. 构建和推送镜像

```bash
# 构建镜像
docker build -t secondbrain-backend:latest ./backend
docker build -t secondbrain-frontend:latest ./frontend

# 推送到镜像仓库（可选）
docker tag secondbrain-backend:latest your-registry/secondbrain-backend:latest
docker push your-registry/secondbrain-backend:latest
```

### 4. 部署到服务器

```bash
# 在服务器上
# 1. 拉取代码或镜像
git clone your-repo
cd secondbrain

# 2. 创建环境文件
cp .env.example .env.production
# 编辑 .env.production 填入实际配置

# 3. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 4. 检查状态
docker-compose ps
docker-compose logs -f
```

## 🌟 最佳实践

### 1. 使用多阶段构建
减小镜像体积：
```dockerfile
# 构建阶段
FROM python:3.12 AS builder
# 构建步骤...

# 运行阶段
FROM python:3.12-slim
COPY --from=builder /app /app
```

### 2. 健康检查
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 3. 资源限制
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

### 4. 数据持久化
- 使用命名卷而非绑定挂载
- 定期备份重要数据
- 考虑使用云存储服务

### 5. 安全加固
- 不要在镜像中包含敏感信息
- 使用 secrets 管理敏感配置
- 定期更新基础镜像
- 扫描镜像漏洞

## 📊 方案对比

| 方案 | 复杂度 | 成本 | 扩展性 | 适用场景 |
|------|--------|------|---------|----------|
| Docker Compose | 低 | 低 | 中 | 小型项目、单机部署 |
| Kubernetes | 高 | 中 | 高 | 大型项目、需要自动扩展 |
| 云托管服务 | 低 | 高 | 高 | 快速上线、不想管理基础设施 |
| 传统部署 | 中 | 低 | 低 | 特殊环境限制 |

## 🚨 注意事项

1. **数据安全**
   - 定期备份数据库
   - 使用 SSL/TLS 加密
   - 限制数据库访问

2. **性能优化**
   - 使用 CDN 加速前端资源
   - 配置 Nginx 缓存
   - 数据库连接池优化

3. **监控告警**
   - 配置日志收集（ELK/Loki）
   - 设置性能监控（Prometheus/Grafana）
   - 配置告警通知

4. **高可用方案**
   - 数据库主从复制
   - Redis 哨兵模式
   - 负载均衡器

## 🎯 推荐部署流程

1. **开发环境**：Docker Compose（已有）
2. **测试环境**：Docker Compose + CI/CD
3. **生产环境**：
   - 初期：Docker Compose on 云服务器
   - 中期：Docker Swarm 或轻量 K8s
   - 后期：完整 Kubernetes 集群

## 💡 快速开始

最简单的部署方式：
```bash
# 1. 准备服务器（推荐配置）
# - 4核 8G 内存
# - Ubuntu 22.04
# - 安装 Docker 和 Docker Compose

# 2. 部署命令
ssh your-server
git clone your-repo
cd secondbrain
docker-compose -f docker-compose.prod.yml up -d

# 3. 配置域名和 HTTPS
# 使用 Nginx + Let's Encrypt
```

---

**结论**：Docker 容器化部署是目前最佳选择，既保证了环境一致性，又便于管理和扩展。建议从 Docker Compose 开始，随着业务增长逐步迁移到更复杂的编排系统。