FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (git for pulling code, nodejs/npm for frontend builds, docker for container management)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    nodejs \
    npm \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install FastAPI, uvicorn, and alembic (for database migrations)
RUN pip install --no-cache-dir fastapi uvicorn[standard] alembic

# Copy webhook receiver code
COPY webhook/webhook_receiver.py /app/webhook/webhook_receiver.py

# Expose port
EXPOSE 9002

# Run webhook receiver
CMD ["python", "-m", "uvicorn", "webhook.webhook_receiver:app", "--host", "0.0.0.0", "--port", "9002"]
