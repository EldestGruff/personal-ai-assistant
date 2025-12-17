# Personal AI Assistant - TrueNAS SCALE Deployment Guide

**Target Server:** moria (TrueNAS SCALE 25.04.2.6)  
**Deployment Method:** Docker Compose  
**Database:** PostgreSQL 16  
**Last Updated:** December 17, 2024

---

## 📋 Prerequisites

### On TrueNAS SCALE (moria)
- ✅ Docker installed and running
- ✅ SSH access (key-based authentication configured)
- ✅ ZFS dataset for data persistence
- ✅ Network access to Ollama server (if using)

### On Development Machine
- ✅ SSH key configured for moria
- ✅ Git repository cloned
- ✅ `.env` file configured

---

## 🚀 Quick Start (Local Testing First)

Before deploying to moria, test locally:

```bash
cd ~/Dev/personal-ai-assistant/docker

# Copy environment template
cp .env.example .env

# Edit .env with your actual values
nano .env

# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Test API
curl http://localhost:8000/api/v1/health

# Stop services
docker-compose down
```

---

## 📦 Deployment to TrueNAS SCALE (moria)

### Step 1: Prepare TrueNAS Server

SSH into moria:

```bash
ssh andy@moria
```

Create ZFS dataset for persistence:

```bash
# Create dataset for Personal AI data
sudo zfs create tank/andy-ai

# Create subdirectories
sudo mkdir -p /mnt/tank/andy-ai/postgres-data
sudo mkdir -p /mnt/tank/andy-ai/logs
sudo mkdir -p /mnt/tank/andy-ai/app

# Set permissions
sudo chown -R andy:andy /mnt/tank/andy-ai
```

Configure snapshots for backups:

```bash
# Hourly snapshots, keep 24
sudo zfs set com.sun:auto-snapshot=true tank/andy-ai
sudo zfs set com.sun:auto-snapshot:frequent=true tank/andy-ai
sudo zfs set com.sun:auto-snapshot:hourly=true tank/andy-ai
```

### Step 2: Transfer Application Code

From your development machine:

```bash
# Create deployment package (excludes unnecessary files)
cd ~/Dev/personal-ai-assistant
tar --exclude='venv' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='tests' \
    --exclude='htmlcov' \
    --exclude='.pytest_cache' \
    --exclude='*.db' \
    -czf personal-ai-assistant.tar.gz .

# Transfer to moria
scp personal-ai-assistant.tar.gz andy@moria:/mnt/tank/andy-ai/

# SSH into moria and extract
ssh andy@moria
cd /mnt/tank/andy-ai/app
tar -xzf ../personal-ai-assistant.tar.gz
rm ../personal-ai-assistant.tar.gz
```

### Step 3: Configure Environment

On moria, create `.env` file:

```bash
cd /mnt/tank/andy-ai/app/docker
cp .env.example .env
nano .env
```

Configure with production values:

```bash
# Database
POSTGRES_USER=andy
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=personal_ai

# API
API_KEY=<secure-uuid-key>

# AI Backends
ANTHROPIC_API_KEY=<your-claude-api-key>
AVAILABLE_BACKENDS=claude,ollama
PRIMARY_BACKEND=claude
SECONDARY_BACKEND=ollama

# Ollama (moria local or network)
OLLAMA_BASE_URL=http://192.168.7.187:11434
OLLAMA_MODEL=llama3.2:latest

# Application
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Step 4: Update docker-compose for Production

Edit `docker-compose.yml` to use ZFS-backed volumes:

```bash
cd /mnt/tank/andy-ai/app/docker
nano docker-compose.yml
```

Update the volumes section:

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/tank/andy-ai/postgres-data
```

Update API service to mount logs:

```yaml
  api:
    # ... existing config ...
    volumes:
      - /mnt/tank/andy-ai/logs:/app/logs
```

### Step 5: Build and Deploy

```bash
cd /mnt/tank/andy-ai/app/docker

# Build images
docker-compose build --no-cache

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 6: Initialize Database

Run Alembic migrations:

```bash
# Enter API container
docker-compose exec api bash

# Run migrations
alembic upgrade head

# Exit container
exit
```

### Step 7: Verify Deployment

```bash
# Check health
curl http://moria:8000/api/v1/health

# Check backend availability
curl http://moria:8000/api/v1/health/backends

# Test API (from another machine on network)
curl -H "Authorization: Bearer <your-api-key>" \
     http://moria:8000/api/v1/thoughts
```

---

## 🔧 Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_USER` | Yes | andy | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | - | PostgreSQL password |
| `POSTGRES_DB` | Yes | personal_ai | Database name |
| `API_KEY` | Yes | - | API authentication key |
| `ANTHROPIC_API_KEY` | Conditional | - | Required if using Claude |
| `AVAILABLE_BACKENDS` | No | claude,ollama,mock | Comma-separated list |
| `PRIMARY_BACKEND` | No | claude | Primary AI backend |
| `SECONDARY_BACKEND` | No | ollama | Fallback backend |
| `OLLAMA_BASE_URL` | Conditional | - | Required if using Ollama |
| `OLLAMA_MODEL` | No | llama3.2:latest | Ollama model |
| `LOG_LEVEL` | No | INFO | Logging level |
| `ENVIRONMENT` | No | production | Environment name |

### Port Mapping

| Port | Service | Description |
|------|---------|-------------|
| 8000 | FastAPI | API endpoints, docs |
| 5432 | PostgreSQL | Database (not exposed externally) |

---

## 📊 Monitoring & Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 api
```

### Check Service Status

```bash
docker-compose ps
docker-compose top
```

### Database Backup

```bash
# Manual backup
docker-compose exec postgres pg_dump -U andy personal_ai > backup_$(date +%Y%m%d).sql

# Automatic via ZFS snapshots
zfs list -t snapshot tank/andy-ai
```

### Database Restore

```bash
# From SQL file
cat backup_20241217.sql | docker-compose exec -T postgres psql -U andy personal_ai

# From ZFS snapshot
zfs rollback tank/andy-ai@auto-2024-12-17-0000
```

### Update Application

```bash
# On development machine - create new package
cd ~/Dev/personal-ai-assistant
tar --exclude='venv' --exclude='.git' -czf personal-ai-assistant.tar.gz .
scp personal-ai-assistant.tar.gz andy@moria:/mnt/tank/andy-ai/

# On moria - update and restart
cd /mnt/tank/andy-ai/app
docker-compose down
cd ..
rm -rf app/*
tar -xzf personal-ai-assistant.tar.gz -C app/
cd app/docker
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔒 Security Considerations

### API Key Security
- Use UUIDs for API keys
- Rotate keys regularly
- Never commit `.env` to git
- Store `.env` in encrypted storage

### Database Security
- Strong PostgreSQL password (20+ chars)
- Database not exposed outside Docker network
- Regular backups via ZFS snapshots

### Network Security
- WireGuard VPN for remote access
- Consider reverse proxy with SSL (Traefik/Nginx)
- Rate limiting enabled in FastAPI

### Container Security
- Runs as non-root user (appuser, UID 1000)
- Minimal base image (python:3.12-slim)
- No unnecessary packages

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check Docker daemon
sudo systemctl status docker

# Check port conflicts
sudo netstat -tulpn | grep 8000
sudo netstat -tulpn | grep 5432

# Check logs
docker-compose logs
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection from API container
docker-compose exec api bash
pg_isready -h postgres -p 5432 -U andy -d personal_ai
```

### API Returns Errors

```bash
# Check environment variables
docker-compose exec api env | grep DATABASE_URL
docker-compose exec api env | grep ANTHROPIC_API_KEY

# Check migrations
docker-compose exec api alembic current
docker-compose exec api alembic upgrade head
```

### Backend Health Issues

```bash
# Check backend availability
curl http://moria:8000/api/v1/health/backends

# Check Claude API key
docker-compose exec api python -c "import os; print('Key set:', bool(os.getenv('ANTHROPIC_API_KEY')))"

# Check Ollama connectivity
docker-compose exec api curl http://192.168.7.187:11434/api/tags
```

---

## 📈 Performance Tuning

### PostgreSQL

Edit `docker-compose.yml` to add performance settings:

```yaml
postgres:
  command:
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "effective_cache_size=1GB"
    - "-c"
    - "max_connections=100"
```

### FastAPI Workers

For production with multiple cores:

```yaml
api:
  command: ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## 🔄 Automatic Startup

Configure Docker Compose to start on boot:

```bash
# Create systemd service
sudo nano /etc/systemd/system/personal-ai.service
```

Service file content:

```ini
[Unit]
Description=Personal AI Assistant
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/mnt/tank/andy-ai/app/docker
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=andy

[Install]
WantedBy=multi-user.target
```

Enable service:

```bash
sudo systemctl enable personal-ai.service
sudo systemctl start personal-ai.service
sudo systemctl status personal-ai.service
```

---

## ✅ Post-Deployment Checklist

- [ ] Services running (`docker-compose ps`)
- [ ] Health check passes (`curl http://moria:8000/api/v1/health`)
- [ ] Database accessible (`docker-compose exec postgres psql -U andy personal_ai`)
- [ ] Migrations applied (`docker-compose exec api alembic current`)
- [ ] API key works (`curl -H "Authorization: Bearer <key>" http://moria:8000/api/v1/thoughts`)
- [ ] Backends available (`curl http://moria:8000/api/v1/health/backends`)
- [ ] Logs directory created (`ls -la /mnt/tank/andy-ai/logs`)
- [ ] ZFS snapshots enabled (`zfs get com.sun:auto-snapshot tank/andy-ai`)
- [ ] Systemd service enabled (optional: `systemctl is-enabled personal-ai`)

---

## 📞 Support & Resources

- **Documentation:** `/docs` endpoint
- **API Docs:** `http://moria:8000/docs`
- **Health Check:** `http://moria:8000/api/v1/health`
- **Backend Status:** `http://moria:8000/api/v1/health/backends`
- **Repository:** `https://github.com/EldestGruff/personal-ai-assistant`

---

**Deployment Complete!** 🎉

Your Personal AI Assistant is now running on moria with PostgreSQL backing.
