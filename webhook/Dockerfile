FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and Docker CLI via official Docker repository
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    nodejs \
    npm \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Add Docker's official GPG key
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker CLI from official Docker repository
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install FastAPI, uvicorn, and alembic (for database migrations)
RUN pip install --no-cache-dir fastapi uvicorn[standard] alembic

# Copy webhook receiver code
COPY webhook/webhook_receiver.py /app/webhook/webhook_receiver.py

# Expose port
EXPOSE 9002

# Run webhook receiver
CMD ["python", "-m", "uvicorn", "webhook.webhook_receiver:app", "--host", "0.0.0.0", "--port", "9002"]
