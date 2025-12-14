# Personal AI Assistant - Quick Reference Card

**Keep this handy during deployment and daily use**

---

## 🔑 Essential URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **API (Production)** | https://ai.gruff.icu/api/v1 | Main API endpoint |
| **API Docs (Swagger)** | https://ai.gruff.icu/docs | Interactive API documentation |
| **Health Check** | https://ai.gruff.icu/api/v1/health | Verify API is running |
| **NPM Interface** | http://moria:81 | Nginx Proxy Manager admin |
| **TrueNAS Dashboard** | http://moria | TrueNAS web interface |

---

## 🔐 Credentials Location

**Store in 1Password or secure vault:**
- API Key (UUID)
- Anthropic API Key
- Database Password
- NPM Admin Password

---

## 📡 Key Endpoints

### Thoughts
```bash
# Create thought
POST /api/v1/thoughts
{
  "content": "Your thought here",
  "tags": ["optional", "tags"],
  "context": {}
}

# List thoughts
GET /api/v1/thoughts?limit=10&sort_by=created_at&sort_order=desc

# Search thoughts
GET /api/v1/thoughts/search?q=keyword

# Get specific thought
GET /api/v1/thoughts/{id}

# Update thought
PUT /api/v1/thoughts/{id}

# Delete thought
DELETE /api/v1/thoughts/{id}
```

### Tasks
```bash
# Create task
POST /api/v1/tasks
{
  "title": "Task title",
  "description": "Optional description",
  "priority": "medium",
  "due_date": "2025-12-20"
}

# List tasks
GET /api/v1/tasks?status=pending

# Complete task
POST /api/v1/tasks/{id}/complete

# Update task
PUT /api/v1/tasks/{id}

# Delete task
DELETE /api/v1/tasks/{id}
```

---

## 🐳 Docker Commands

### Status and Logs
```bash
# Check container status
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View API logs only
docker-compose logs -f api

# View last 50 lines
docker-compose logs --tail=50 api

# Check for errors
docker-compose logs api | grep ERROR
```

### Control
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Restart just API
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build

# Stop and remove containers
docker-compose down
```

### Database
```bash
# Access PostgreSQL shell
docker-compose exec db psql -U aiassistant -d aiassistant

# Backup database
docker-compose exec db pg_dump -U aiassistant aiassistant > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T db psql -U aiassistant aiassistant < backup_20251214.sql

# Run migrations
docker-compose exec api alembic upgrade head

# Check migration status
docker-compose exec api alembic current
```

---

## 🧪 Testing Commands

### Local Testing (from TrueNAS)
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Create thought
curl -X POST http://localhost:8000/api/v1/thoughts \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test thought"}'

# List thoughts
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/v1/thoughts
```

### Remote Testing (from Mac)
```bash
# Health check
curl https://ai.gruff.icu/api/v1/health

# Create thought
curl -X POST https://ai.gruff.icu/api/v1/thoughts \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test thought from Mac"}'

# List thoughts
curl -H "X-API-Key: YOUR_API_KEY" \
  https://ai.gruff.icu/api/v1/thoughts
```

---

## 📱 iOS Shortcuts Quick Copy

### Quick Capture URL Configuration
```
URL: https://ai.gruff.icu/api/v1/thoughts
Method: POST
Headers:
  X-API-Key: YOUR_API_KEY_HERE
  Content-Type: application/json
Body (JSON):
{
  "content": [Provided Input]
}
```

### Voice Capture
Same as above, but use `[Dictated Text]` instead of `[Provided Input]`

### Create Task
```
URL: https://ai.gruff.icu/api/v1/tasks
Method: POST
Headers:
  X-API-Key: YOUR_API_KEY_HERE
  Content-Type: application/json
Body (JSON):
{
  "title": [Provided Input],
  "priority": "medium"
}
```

---

## 🚨 Troubleshooting Quick Fixes

### Container won't start
```bash
# Check logs
docker-compose logs api

# Verify environment
cat docker/.env

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Can't access API remotely
```bash
# Test local first
curl http://localhost:8000/api/v1/health

# Test internal network
curl http://moria:8000/api/v1/health

# Check NPM proxy host
# NPM UI > Hosts > Verify ai.gruff.icu is enabled

# Check DNS
nslookup ai.gruff.icu

# Check firewall
sudo ufw status
```

### Database connection error
```bash
# Check DB is healthy
docker-compose ps db

# Test connection
docker-compose exec db psql -U aiassistant -d aiassistant -c "SELECT 1;"

# Check DATABASE_URL
docker-compose exec api env | grep DATABASE_URL

# Restart DB
docker-compose restart db
```

### SSL certificate issues
```bash
# Check NPM certificate status
# NPM UI > SSL Certificates

# Verify DNS
nslookup ai.gruff.icu

# Re-issue certificate
# NPM UI > SSL Certificates > Edit > Force Renew

# Check LetsEncrypt rate limits
# 50 certs per week per domain
```

---

## 📂 Important File Locations

### On TrueNAS (moria)
```
/mnt/data2-pool/andy-ai/
├── personal-ai-assistant/       # Application code
│   ├── docker/
│   │   ├── docker-compose.yml   # Container orchestration
│   │   └── .env                 # SECRETS (don't commit!)
│   ├── src/                     # API source code
│   ├── alembic/                 # Database migrations
│   └── docs/                    # Documentation
└── postgres/                    # Database data (persistent)
    └── pgdata/
```

### On Mac (Development)
```
/Users/andy/Dev/personal-ai-assistant/
├── All the same files as above
├── DEPLOYMENT_CHECKLIST.md
├── DEPLOYMENT_READY.md
└── QUICK_REFERENCE.md (this file)
```

---

## 🔄 Common Workflows

### Deploy New Code Changes
```bash
# On Mac: Commit changes
git add .
git commit -m "Description of changes"
git push

# On TrueNAS: Pull and redeploy
ssh andy@moria
cd /mnt/data2-pool/andy-ai/personal-ai-assistant
git pull
cd docker
docker-compose build
docker-compose up -d
docker-compose logs -f api  # Watch for successful startup
```

### Backup Database
```bash
# SSH to TrueNAS
ssh andy@moria

# Run backup
cd /mnt/data2-pool/andy-ai/personal-ai-assistant/docker
docker-compose exec db pg_dump -U aiassistant aiassistant > ../backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh ../backups/
```

### Rotate API Key
```bash
# Generate new key
python3 -c "import uuid; print(uuid.uuid4())"

# Update .env on TrueNAS
ssh andy@moria
nano /mnt/data2-pool/andy-ai/personal-ai-assistant/docker/.env
# Change API_KEY=<new-uuid>

# Restart API
cd /mnt/data2-pool/andy-ai/personal-ai-assistant/docker
docker-compose restart api

# Update iOS Shortcuts with new key
```

### View Recent Thoughts (CLI)
```bash
# Quick query
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://ai.gruff.icu/api/v1/thoughts?limit=5&sort_order=desc" | \
  jq '.data[] | {created: .created_at, content: .content}'
```

### Check System Health
```bash
# Full health check script
ssh andy@moria << 'EOF'
echo "=== Container Status ==="
docker-compose -f /mnt/data2-pool/andy-ai/personal-ai-assistant/docker/docker-compose.yml ps

echo -e "\n=== API Health ==="
curl -s http://localhost:8000/api/v1/health | jq

echo -e "\n=== Recent Logs (last 20 lines) ==="
docker-compose -f /mnt/data2-pool/andy-ai/personal-ai-assistant/docker/docker-compose.yml logs --tail=20 api

echo -e "\n=== Resource Usage ==="
docker stats --no-stream personal-ai-assistant-api personal-ai-assistant-db
EOF
```

---

## 📊 Performance Benchmarks

### Expected Response Times
| Endpoint | Expected | Alert If |
|----------|----------|----------|
| `/health` | < 100ms | > 500ms |
| `POST /thoughts` | < 300ms | > 1000ms |
| `GET /thoughts` | < 200ms | > 800ms |
| `GET /thoughts/search` | < 400ms | > 1500ms |

### Resource Limits
| Container | RAM | CPU | Alert If |
|-----------|-----|-----|----------|
| API | ~200MB | <5% | >500MB or >20% |
| DB | ~150MB | <2% | >400MB or >10% |

---

## 🎯 iOS Capture Time Goals

| Method | Target | Acceptable | Too Slow |
|--------|--------|------------|----------|
| Widget Tap | 5 sec | 7 sec | >10 sec |
| Back Tap | 3 sec | 5 sec | >8 sec |
| Voice | 6 sec | 10 sec | >15 sec |
| Share Sheet | 4 sec | 6 sec | >10 sec |

---

## 📞 Emergency Contacts

### Documentation
- Deployment Guide: `docs/TRUENAS_DEPLOYMENT.md`
- NPM Guide: `docs/NGINX_PROXY_MANAGER.md`
- iOS Guide: `docs/IOS_SHORTCUTS.md`
- Full Checklist: `DEPLOYMENT_CHECKLIST.md`

### External Resources
- FastAPI Docs: https://fastapi.tiangolo.com/
- PostgreSQL Docs: https://www.postgresql.org/docs/
- Docker Compose Docs: https://docs.docker.com/compose/
- iOS Shortcuts Gallery: https://support.apple.com/guide/shortcuts/

---

## 🎨 Quick Environment Setup

### Generate All Secrets (One Command)
```bash
echo "API_KEY=$(python3 -c 'import uuid; print(uuid.uuid4())')"
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "ANTHROPIC_API_KEY=<get from console.anthropic.com>"
```

### Minimal .env File
```bash
# Required
API_KEY=<your-uuid>
ANTHROPIC_API_KEY=<your-anthropic-key>
POSTGRES_PASSWORD=<your-password>

# Recommended
DEBUG=false
LOG_LEVEL=INFO

# Optional (has defaults)
POSTGRES_USER=aiassistant
POSTGRES_DB=aiassistant
```

---

## ✅ Daily Health Check (30 seconds)

```bash
# One-liner health check
curl -s https://ai.gruff.icu/api/v1/health && \
ssh andy@moria "docker-compose -f /mnt/data2-pool/andy-ai/personal-ai-assistant/docker/docker-compose.yml ps | grep -q 'healthy' && echo 'All systems healthy ✅' || echo 'Issues detected ⚠️'"
```

---

**Print this page and keep it near your desk!** 📋

**Last Updated:** 2025-12-14
**Version:** 0.1.0
