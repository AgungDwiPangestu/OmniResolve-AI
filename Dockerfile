# =============================================================================
# Dockerfile — OmniResolve-AI API Service
# Compatible dengan Docker (SumoPod) dan Podman (local dev)
# =============================================================================

FROM python:3.12-slim AS base

# Metadata
LABEL maintainer="OmniResolve-AI Team"
LABEL description="Autonomous Retail Conflict Resolver — Multi-Agent AI System"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user untuk keamanan
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

WORKDIR /app

# Install Python dependencies (layer terpisah agar cache efisien)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY db/ ./db/

# Ownership
RUN chown -R appuser:appuser /app

USER appuser

# Set PYTHONPATH agar `src.*` bisa di-import dari /app
ENV PYTHONPATH=/app

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
