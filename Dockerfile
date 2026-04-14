# 使用 uv 官方镜像构建
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# 安装依赖（利用 Docker 缓存层）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 复制应用代码
COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

# 启动应用
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
