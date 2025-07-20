# 前端 Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 设置后端 API 地址
ENV REACT_APP_API_URL=http://localhost:8000/api/v1

# 构建项目
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建结果（React 构建输出在 build 目录）
COPY --from=builder /app/build /usr/share/nginx/html

# 创建 nginx 配置以支持 SPA 路由
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]