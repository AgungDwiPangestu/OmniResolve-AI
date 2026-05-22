# Claude Office Visualizer - Multi-stage Dockerfile
# Stage 1: Build frontend with Node.js
# Stage 2: Run backend with Python/uv

# =============================================================================
# Stage 1: Frontend Build
# =============================================================================
FROM docker.io/oven/bun:1 AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better layer caching
COPY frontend/package.json frontend/bun.lock* ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy frontend source
COPY frontend/ ./

# Build args for Next.js NEXT_PUBLIC_* env vars (embedded at build time)
ARG NEXT_PUBLIC_ARCHIVE_KEY
ARG NEXT_PUBLIC_OMNI_API_URL
ARG NEXT_PUBLIC_WS_URL

ENV NEXT_PUBLIC_ARCHIVE_KEY=$NEXT_PUBLIC_ARCHIVE_KEY
ENV NEXT_PUBLIC_OMNI_API_URL=$NEXT_PUBLIC_OMNI_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

# Build static export
RUN bun run build

# =============================================================================
# Stage 2: Python Runtime
# =============================================================================
FROM docker.io/library/python:3.13-slim AS runtime

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Copy backend dependency files
COPY backend/pyproject.toml backend/uv.lock* backend/README.md* ./

# Install dependencies (without dev dependencies)
RUN uv sync --no-dev --frozen

# Copy backend source and configuration
COPY backend/app ./app
COPY backend/floors.toml ./floors.toml

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/out ./static

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" || exit 1

# Run the application
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
