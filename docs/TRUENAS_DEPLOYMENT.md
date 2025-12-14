# TrueNAS SCALE Deployment Guide
**Personal AI Assistant - Production Deployment on moria**

---

## Prerequisites

- **TrueNAS SCALE**: 25.04.2.6 (installed and running)
- **Dataset Created**: `/mnt/data2-pool/andy-ai`
- **Nginx Proxy Manager**: Running and accessible
- **Domain**: `gruff.icu` with DNS configured
- **SSH Access**: To moria for CLI operations (optional)

---

## Quick Start (TL;DR)

```bash
# 1. Copy project to TrueNAS
scp -r /Users/andy/Dev/personal-ai-assistant andy@moria:/mnt/data2-pool/andy-ai/

# 2. SSH into TrueNAS
ssh andy@moria

# 3. Navigate to docker directory
cd /mnt/data2-pool/andy-ai/personal-ai-assistant/docker

# 4. Configure environment
cp .env.production .env
nano .env  # Fill in actual values

# 5. Deploy
docker-compose up -d

# 6. Check status
docker-compose ps
docker-compose logs -f api
```

---

## Detailed Deployment Steps

### Step 1: Prepare the Dataset

Ensure the dataset exists and has correct permissions:

```bash
# On TrueNAS (via SSH or Shell)
ls -la /mnt/data2-pool/andy-ai

# Should show the dataset
# If not, create it via TrueNAS UI: Storage > Pools > data2-pool > Add Dataset
```

### Step 2: Copy Project Files to TrueNAS

**Option A: Using SCP (from your Mac)**
```bash
cd /Users/andy/Dev/personal-ai-assistant
scp -r . andy@moria:/mnt/data2-pool/andy-ai/personal-ai-assistant/
```

**Option B: Using Git (from TrueNAS)**
```bash
ssh andy@moria
cd /mnt/data2-pool/andy-ai
git clone <your-repo-url> personal-ai-assistant
cd personal-ai-assistant
git checkout main
```

### Step 3: Configure Environment Variables

```bash
# SSH into TrueNAS
ssh andy@moria
cd /mnt/data2-pool/andy-ai/personal-ai-assistant/docker

# Copy production template
cp .env.production .env

# Edit with your values
nano .env
```

**Fill in these critical values:**
```bash
# Generate UUID for API_KEY
python3 -c "import uuid; print(uuid.uuid4())"

# Get Anthropic API key from console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Generate strong database password
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

**Save the file** (Ctrl+O, Enter, Ctrl+X)

### Step 4: Build and Deploy

```bash
cd /mnt/data2-pool/andy-ai/personal-ai-assistant/docker

# Build the image
docker-compose build

# Start services in detached mode
docker-compose up -d

# Watch the logs to confirm startup
docker-compose logs -f
```

**Expected output:**
```
personal-ai-assistant-db  | database system is ready to accept connections
personal-ai-assistant-api | 🔧 Running database migrations...
personal-ai-assistant-api | INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial_schema
personal-ai-assistant-api | 🚀 Starting Personal AI Assistant API...
personal-ai-assistant-api | INFO:     Started server process
personal-ai-assistant-api | INFO:     Uvicorn running on http://0.0.0.0:8000
```

Press `Ctrl+C` to exit logs (containers keep running).

### Step 5: Verify Deployment

**Check container status:**
```bash
docker-compose ps
```

Should show both containers as "Up" with healthy status.

**Test API locally (from TrueNAS):**
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-12-14T..."
  }
}
```

**Test from your Mac (internal network):**
```bash
# Replace <moria-ip> with actual IP
curl http://<moria-ip>:8000/api/v1/health
```

---

## Nginx Proxy Manager Configuration

### Step 1: Access NPM Interface

1. Navigate to your NPM UI (likely `http://moria:81` or similar)
2. Login with your credentials

### Step 2: Add Proxy Host

**Navigate to:** Hosts > Proxy Hosts > Add Proxy Host

**Details Tab:**
- **Domain Names:** `ai.gruff.icu`
- **Scheme:** `http`
- **Forward Hostname/IP:** `moria` (or `172.17.0.1` for Docker host)
- **Forward Port:** `8000`
- **Cache Assets:** ✓ (enabled)
- **Block Common Exploits:** ✓ (enabled)
- **Websockets Support:** ✓ (enabled, for future)

**SSL Tab:**
- **SSL Certificate:** Select existing `*.gruff.icu` or create new
- **Force SSL:** ✓ (enabled)
- **HTTP/2 Support:** ✓ (enabled)
- **HSTS Enabled:** ✓ (enabled)

**Advanced Tab (optional):**
```nginx
# CORS headers for web/mobile clients
add_header Access-Control-Allow-Origin *;
add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-API-Key";

# Security headers
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
```

**Save** the proxy host.

### Step 3: Test External Access

**From your Mac (over WiFi):**
```bash
curl https://ai.gruff.icu/api/v1/health
```

**From your iPhone (over LTE, disable WiFi):**
```bash
# Use a browser or Shortcuts
# Navigate to: https://ai.gruff.icu/api/v1/health
```

Should return the health check JSON with HTTPS.

---

## TrueNAS Apps UI Deployment (Alternative)

If you prefer the TrueNAS web interface:

### Step 1: Navigate to Apps

**TrueNAS UI:** Apps > Discover Apps > Custom App

### Step 2: Configure Application

**Application Name:** `personal-ai-assistant`

**Image and Policy:**
- **Image Repository:** Build locally first (see CLI steps above)
- Or use Docker Hub if you push the image

**Container Settings:**
- **Environment Variables:** Add all from `.env.production`
- **Port Forwarding:** `8000:8000`
- **Storage:** Mount `/mnt/data2-pool/andy-ai/postgres` to `/var/lib/postgresql/data`

**Network:** Bridge mode

**Save** and deploy.

---

## Management Commands

### View Logs
```bash
cd /mnt/data2-pool/andy-ai/personal-ai-assistant/docker

# All logs
docker-compose logs -f

# Just API
docker-compose logs -f api

# Just database
docker-compose logs -f db

# Last 50 lines
docker-compose logs --tail=50 api
```

### Restart Services
```bash
# Restart everything
docker-compose restart

# Restart just API (after code changes)
docker-compose restart api

# Rebuild and restart (after code changes)
docker-compose up -d --build
```

### Stop Services
```bash
# Stop but keep data
docker-compose stop

# Stop and remove containers (data persists in volume)
docker-compose down

# Nuclear option: remove everything including data
docker-compose down -v  # ⚠️ DANGER: Deletes database!
```

### Database Access
```bash
# Interactive psql shell
docker-compose exec db psql -U aiassistant -d aiassistant

# Backup database
docker-compose exec db pg_dump -U aiassistant aiassistant > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T db psql -U aiassistant aiassistant < backup_20251214.sql
```

### Run Migrations Manually
```bash
# If you need to re-run migrations
docker-compose exec api alembic upgrade head

# Check migration status
docker-compose exec api alembic current

# View migration history
docker-compose exec api alembic history
```

---

## Troubleshooting

### API Container Won't Start

**Check logs:**
```bash
docker-compose logs api
```

**Common issues:**
- Database not ready: Wait 30 seconds and check `docker-compose logs db`
- Migration failure: Check DATABASE_URL format
- Missing environment variables: Verify `.env` file exists and is complete

### Database Connection Errors

**Verify database is healthy:**
```bash
docker-compose ps db
```

Should show "healthy" status.

**Test connection:**
```bash
docker-compose exec db psql -U aiassistant -d aiassistant -c "SELECT 1;"
```

### Can't Access from External Network

**Check firewall:**
```bash
# On TrueNAS
sudo ufw status
```

Port 8000 should be open (or proxied via NPM).

**Check NPM proxy:**
- Verify proxy host is enabled
- Check SSL certificate is valid
- Test internal access first: `curl http://moria:8000/api/v1/health`

### Permission Denied on Dataset

```bash
# Fix ownership
sudo chown -R 999:999 /mnt/data2-pool/andy-ai/postgres

# 999 is the postgres user ID in the alpine container
```

---

## Updating the Application

### Update Code
```bash
# On TrueNAS
cd /mnt/data2-pool/andy-ai/personal-ai-assistant
git pull origin main

# Or copy files from Mac
scp -r /Users/andy/Dev/personal-ai-assistant andy@moria:/mnt/data2-pool/andy-ai/
```

### Rebuild and Deploy
```bash
cd docker
docker-compose build
docker-compose up -d

# Watch for migration messages
docker-compose logs -f api
```

---

## Monitoring and Maintenance

### Health Checks

**Automated Docker health checks** run every 30 seconds:
```bash
docker-compose ps
```

Look for "(healthy)" status.

### ZFS Snapshots

Your dataset is on ZFS, so configure snapshots:

**TrueNAS UI:** Storage > Pools > data2-pool > andy-ai > Edit > Snapshots

**Recommended schedule:**
- Hourly: Keep 24
- Daily: Keep 7
- Weekly: Keep 4

### Backup Strategy

**Database backups:**
```bash
# Create backup script
cat > /mnt/data2-pool/andy-ai/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/mnt/data2-pool/andy-ai/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
docker-compose exec -T db pg_dump -U aiassistant aiassistant > $BACKUP_DIR/backup_$DATE.sql
# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
EOF

chmod +x /mnt/data2-pool/andy-ai/backup.sh

# Add to cron (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /mnt/data2-pool/andy-ai/backup.sh
```

### Log Rotation

Docker handles log rotation automatically, but verify:

```bash
# Check log size
docker-compose logs api | wc -l

# Clear logs if needed
docker-compose down
rm -rf /var/lib/docker/containers/*/.*-json.log
docker-compose up -d
```

---

## Security Considerations

### API Key Rotation

To rotate your API key:

```bash
# Generate new UUID
python3 -c "import uuid; print(uuid.uuid4())"

# Update .env file
nano /mnt/data2-pool/andy-ai/personal-ai-assistant/docker/.env

# Restart API
docker-compose restart api

# Update all clients (iOS Shortcuts, etc.)
```

### Database Password Rotation

```bash
# Generate new password
NEW_PASS=$(openssl rand -base64 32)

# Update in database
docker-compose exec db psql -U aiassistant -d aiassistant -c "ALTER USER aiassistant PASSWORD '$NEW_PASS';"

# Update .env
nano .env
# Change POSTGRES_PASSWORD=<new_password>

# Restart
docker-compose restart
```

### SSL Certificate Renewal

NPM handles LetsEncrypt renewals automatically. Verify:
- **NPM UI:** SSL Certificates > Check expiration dates
- Auto-renewal happens 30 days before expiry

---

## Next Steps

Once deployed and verified:

1. **Test API from iPhone** (see iOS Shortcuts setup)
2. **Add test data** via API
3. **Configure Claude integration** (Phase 3)
4. **Build iOS Shortcuts** for quick capture
5. **Monitor usage** and adjust resources if needed

---

## Support and Resources

- **FastAPI Docs:** https://ai.gruff.icu/docs (auto-generated)
- **Project Repo:** `/mnt/data2-pool/andy-ai/personal-ai-assistant`
- **Logs:** `docker-compose logs -f`
- **Database Shell:** `docker-compose exec db psql -U aiassistant`

---

**Deployment Date:** _____________
**Deployed By:** Andy Fenner
**API Endpoint:** https://ai.gruff.icu
**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Deployed | ⬜ Verified
