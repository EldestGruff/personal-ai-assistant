# Docker Deployment Files

This directory contains everything needed to deploy the Personal AI Assistant using Docker and PostgreSQL.

## 📁 Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build for FastAPI application |
| `docker-compose.yml` | Orchestrates API + PostgreSQL services |
| `.env.example` | Environment variables template |
| `init-db.sql` | PostgreSQL initialization script |
| `deploy.sh` | Automated deployment script |
| `DEPLOYMENT.md` | Comprehensive deployment guide |

## 🚀 Quick Start

### Local Development/Testing

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit with your values
nano .env

# 3. Deploy locally
./deploy.sh local

# 4. Access API
open http://localhost:8000/docs
```

### Production Deployment to TrueNAS (moria)

```bash
# Deploy to moria
./deploy.sh moria

# Verify deployment
ssh andy@moria 'cd /mnt/tank/andy-ai/app/docker && docker-compose ps'
```

## 📖 Documentation

See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Detailed deployment steps
- Configuration reference
- Troubleshooting guide
- Monitoring & maintenance
- Security considerations

## 🐘 PostgreSQL vs SQLite

This deployment uses **PostgreSQL 16** instead of SQLite for:
- ✅ Better concurrency handling
- ✅ Production-grade ACID compliance
- ✅ Full-text search capabilities
- ✅ Connection pooling
- ✅ Better performance at scale

## 🔧 Services

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI application |
| `postgres` | 5432 | PostgreSQL database (internal) |

## 📊 Data Persistence

PostgreSQL data is persisted in Docker volumes:
- **Local:** Docker managed volume
- **moria:** ZFS-backed at `/mnt/tank/andy-ai/postgres-data`

## 🔐 Environment Variables

Required variables in `.env`:

```bash
# Database
POSTGRES_USER=andy
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=personal_ai

# API
API_KEY=<uuid-key>

# AI Backends
ANTHROPIC_API_KEY=<claude-key>
PRIMARY_BACKEND=claude
SECONDARY_BACKEND=ollama

# Ollama
OLLAMA_BASE_URL=http://192.168.7.187:11434
OLLAMA_MODEL=llama3.2:latest
```

## 🏥 Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Backend availability
curl http://localhost:8000/api/v1/health/backends

# PostgreSQL
docker-compose exec postgres pg_isready -U andy
```

## 📝 Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart api

# Access database
docker-compose exec postgres psql -U andy personal_ai

# Run migrations
docker-compose exec api alembic upgrade head

# Rebuild images
docker-compose build --no-cache
```

## 🆘 Troubleshooting

### Services won't start
```bash
docker-compose logs
docker-compose ps
```

### Database connection issues
```bash
docker-compose exec api env | grep DATABASE
docker-compose exec postgres pg_isready -U andy
```

### Port conflicts
```bash
sudo lsof -i :8000
sudo lsof -i :5432
```

## 📚 More Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [TrueNAS SCALE Documentation](https://www.truenas.com/docs/scale/)

---

**Ready to deploy!** Follow DEPLOYMENT.md for step-by-step instructions.
