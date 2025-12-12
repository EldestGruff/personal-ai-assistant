# Personal AI Assistant - Dockerfile
# FastAPI service containerization for TrueNAS SCALE deployment

FROM python:3.12-slim

# Metadata
LABEL maintainer="andy@fennerfam.com"
LABEL description="Personal AI Assistant - FastAPI Backend"
LABEL version="0.1.0"

# Python optimization environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (layer caching optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY docker-entrypoint.sh .

# Make entrypoint executable and create non-root user
RUN chmod +x docker-entrypoint.sh && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start with entrypoint that runs migrations first
ENTRYPOINT ["./docker-entrypoint.sh"]
