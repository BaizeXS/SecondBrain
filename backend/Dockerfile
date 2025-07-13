FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv包管理器
RUN pip install uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 使用uv安装依赖
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]