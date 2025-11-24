# Cloud Run ready container built with uv + uvicorn
FROM python:3.12-slim AS base

ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install uv (project manager) first
RUN pip install --no-cache-dir uv

# Sync dependencies using lockfile for reproducibility
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Run MCP server (PORT is provided by Cloud Run; default 8080 for local)
CMD ["uv", "run", "server.py"]
