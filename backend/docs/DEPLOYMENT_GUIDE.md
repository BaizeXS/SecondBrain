# 🚀 SecondBrain 部署指南

## 概述

本指南将帮助您将 SecondBrain 后端服务部署到云平台。

## 📋 部署前准备

### 1. 环境要求

- Docker 和 Docker Compose
- 云服务商账号（阿里云、腾讯云、AWS 等）
- 域名（可选）
- SSL 证书（可选）

### 2. 检查清单

- [x] 后端 API 测试通过（100%成功率，104个端点）
- [x] Deep Research 功能已修复
- [x] 演示数据脚本准备就绪（examples/create_demo_data.py）
- [x] 环境变量配置文件准备
- [ ] 云服务器准备
- [ ] 数据库备份策略

## 🏗️ 部署架构

### 推荐配置

```
负载均衡器 (Nginx/ALB)
    ↓
FastAPI 后端 (8000端口)
    ↓
├── PostgreSQL (数据库)
├── Redis (缓存/会话)
├── MinIO (对象存储)
└── Qdrant (向量数据库)
```

### 服务器配置建议

- **最小配置**: 2 核 4G 内存
- **推荐配置**: 4 核 8G 内存
- **存储空间**: 50GB+（根据文档量调整）

## 📦 部署步骤

### 1. 准备服务器

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo systemctl enable docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 克隆代码

```bash
git clone https://github.com/yourusername/SecondBrain.git
cd SecondBrain/backend
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env.production

# 编辑生产环境配置
vim .env.production
```

**重要配置项**:

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://secondbrain:your_secure_password@postgres:5432/secondbrain

# 安全密钥（使用强密码）
SECRET_KEY=your-very-secure-secret-key-here

# AI服务配置（必需）
OPENROUTER_API_KEY=sk-or-v1-your-api-key
PERPLEXITY_API_KEY=pplx-your-api-key

# 可选：直接AI提供商（如果不使用OpenRouter）
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# 对象存储（MinIO）
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_secure_minio_password

# Redis配置
REDIS_URL=redis://redis:6379/0

# 其他配置
ENVIRONMENT=production
DEBUG=false
```

### 4. 创建生产环境 Docker Compose

```bash
# 创建 docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
      - minio
      - qdrant
    volumes:
      - ./app:/app/app
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: secondbrain
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: secondbrain
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: always

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    restart: always

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
  redis_data:
  minio_data:
  qdrant_data:
EOF
```

### 5. 配置 Nginx

```bash
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # 强制跳转 HTTPS（如果有证书）
        # return 301 https://$server_name$request_uri;

        location / {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # SSE 支持
            proxy_buffering off;
            proxy_cache off;
            proxy_read_timeout 86400;
        }
    }

    # HTTPS 配置（如果有证书）
    # server {
    #     listen 443 ssl http2;
    #     server_name your-domain.com;
    #
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #
    #     location / {
    #         proxy_pass http://backend;
    #         # ... 其他配置同上
    #     }
    # }
}
EOF
```

### 6. 启动服务

```bash
# 构建和启动所有服务
docker-compose -f docker-compose.prod.yml up -d --build

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 创建演示数据（可选）
docker-compose -f docker-compose.prod.yml exec backend python examples/create_demo_data.py
```

## 🔒 安全配置

### 1. 防火墙设置

```bash
# 只开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. 环境变量安全

- 使用强密码
- 不要将 .env 文件提交到代码仓库
- 定期轮换 API 密钥

### 3. 数据备份

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份数据库
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U secondbrain secondbrain > $BACKUP_DIR/postgres.sql

# 备份 MinIO 数据
docker run --rm -v secondbrain_minio_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/minio.tar.gz /data

# 备份 Qdrant 数据
docker run --rm -v secondbrain_qdrant_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/qdrant.tar.gz /data

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x backup.sh

# 设置定时备份
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backup.sh") | crontab -
```

## 📊 监控和维护

### 1. 健康检查

```bash
# 检查所有服务状态
docker-compose -f docker-compose.prod.yml ps

# 检查 API 健康状态
curl http://localhost:8000/health

# 查看资源使用
docker stats
```

### 2. 日志管理

```bash
# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 设置日志轮转
cat > /etc/logrotate.d/docker << EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
EOF
```

### 3. 性能优化

- 使用 Redis 缓存热点数据
- 配置 PostgreSQL 连接池
- 使用 CDN 加速静态资源
- 启用 Gzip 压缩

## 🚨 故障排查

### 常见问题

1. **数据库连接失败**

   ```bash
   # 检查数据库状态
   docker-compose -f docker-compose.prod.yml exec postgres psql -U secondbrain -c "SELECT 1"
   ```

2. **MinIO 无法访问**

   ```bash
   # 检查 MinIO 状态
   docker-compose -f docker-compose.prod.yml logs minio
   ```

3. **API 响应慢**
   - 检查数据库索引
   - 增加 worker 数量
   - 优化查询语句
   - 确认 OpenRouter API 密钥有效

4. **Deep Research 失败**
   - 确认 PERPLEXITY_API_KEY 已配置
   - 检查请求使用 `prompt` 字段而非 `query`

5. **登录失败**
   - 密码必须：8+ 字符，包含大小写字母和数字
   - 登录支持 FormData 和 JSON 两种格式

## 📱 快速部署脚本

创建一键部署脚本 `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 开始部署 SecondBrain..."

# 拉取最新代码
git pull origin main

# 使用生产环境变量
cp .env.production .env

# 停止旧容器
docker-compose -f docker-compose.prod.yml down

# 构建并启动新容器
docker-compose -f docker-compose.prod.yml up -d --build

# 等待服务启动
sleep 10

# 运行迁移
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 健康检查
if curl -f http://localhost:8000/api/v1/health; then
    echo "✅ 部署成功！"
    
    # 显示访问信息
    echo "🌐 访问地址："
    echo "   - API: http://your-server-ip:8000"
    echo "   - API文档: http://your-server-ip:8000/api/v1/docs"
    echo "   - MinIO控制台: http://your-server-ip:9001"
else
    echo "❌ 部署失败，请检查日志"
    docker-compose -f docker-compose.prod.yml logs
fi
```

## 🎯 部署检查清单

- [ ] 服务器准备完成
- [ ] Docker 环境安装
- [ ] 代码部署成功
- [ ] 环境变量配置
- [ ] 数据库迁移完成
- [ ] 所有服务健康运行
- [ ] API 测试通过
- [ ] 备份策略配置
- [ ] 监控告警设置
- [ ] 域名解析（可选）
- [ ] SSL 证书（可选）

## 📞 支持信息

如遇到问题，请检查：

1. Docker 日志：`docker-compose -f docker-compose.prod.yml logs`
2. API 健康状态：`http://your-domain.com/api/v1/health`
3. 系统资源：`df -h` 和 `free -m`
4. API 文档：`http://your-domain.com/api/v1/docs`

### 关键配置提醒

1. **OpenRouter 配置**
   - 必须配置 `OPENROUTER_API_KEY`
   - 模型格式：`openrouter/auto`、`openrouter/openai/gpt-4` 等

2. **密码要求**
   - 最少 8 个字符
   - 包含大写字母、小写字母和数字

3. **文件大小限制**
   - 默认 50MB，可在 `app/core/config.py` 中调整

4. **支持的文件格式**
   - 文档：PDF, DOCX, PPTX, XLSX, TXT, MD
   - 图片：JPG, PNG, GIF, BMP, WEBP
   - 代码：多种编程语言

---
