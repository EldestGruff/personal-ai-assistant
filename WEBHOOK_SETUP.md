# GitHub Webhooks Deployment System Setup (Docker-Based)

**Status:** Ready for implementation  
**Target:** TrueNAS SCALE (moria)  
**Approach:** Docker container for webhook receiver  
**Workflow:** Push to main → Auto-deploy  

---

## Overview

When you push code to `main` on GitHub:

1. GitHub sends webhook to `https://ai.gruff.icu/webhook`
2. Nginx Proxy Manager routes it to `moria:9002/webhook`
3. Webhook receiver container validates signature and triggers deployment
4. Deployment script pulls code, builds frontend, restarts Docker
5. Everything is logged

**From your perspective:** Push code, wait 2-3 minutes, system is live.

---

## Components

### Docker-Based Webhook Receiver
- Lightweight Python container running FastAPI + uvicorn
- Runs alongside your existing postgres and api containers
- Auto-restarts if it crashes
- Shares the same Docker network as your other services

### Deployment Script
- Same as before, runs on moria
- Called by webhook receiver when valid GitHub webhook received
- Handles git pull, npm build, migrations, docker rebuild

---

## One-Time Setup (on moria)

### Step 1: Verify Git Repository is Initialized

This should already be done, but verify:

```bash
ssh andy@moria

cd /mnt/data2-pool/andy-ai/app

# Check git status
git status
# Should show: On branch main, Your branch is up to date with 'origin/main'

# Check remotes
git remote -v
# Should show: origin https://github.com/EldestGruff/personal-ai-assistant.git
```

---

### Step 2: Verify Webhook Files Exist

Check that recent pull brought in the webhook files:

```bash
ssh andy@moria

cd /mnt/data2-pool/andy-ai/app

# Should exist:
ls -la webhook/webhook_receiver.py
ls -la webhook/Dockerfile
ls -la scripts/deploy.sh
```

All three should exist from the git pull.

---

### Step 3: Update docker-compose.yml Environment Variables

The webhook-receiver service needs the webhook secret to validate GitHub signatures.

```bash
ssh andy@moria

cd /mnt/data2-pool/andy-ai/app/docker

# Edit .env file
nano .env

# Add or verify this line exists:
# WEBHOOK_SECRET=thisisasecret
```

The `docker-compose.yml` is already configured to use this environment variable.

---

### Step 4: Build and Start the Webhook Receiver

```bash
ssh andy@moria

cd /mnt/data2-pool/andy-ai/app/docker

# Build all images (including webhook-receiver)
docker compose build

# Verify the build succeeded
# Should show: [+] Built personal-ai-webhook (or similar)

# Start all containers
docker compose up -d

# Verify containers are running
docker compose ps
# Should show:
#   personal-ai-db      (Healthy)
#   personal-ai-api     (Healthy)
#   personal-ai-webhook (Healthy)
```

---

### Step 5: Verify Webhook Receiver is Running

```bash
ssh andy@moria

# Check if container is healthy
docker compose ps personal-ai-webhook
# Status should show "Healthy"

# Test health endpoint
curl http://localhost:9002/health
# Should return: {"status":"healthy","service":"webhook-receiver"}

# Check container logs
docker compose logs webhook-receiver
# Should show: "Uvicorn running on 0.0.0.0:9002"
```

---

### Step 6: Make Deploy Script Executable

```bash
ssh andy@moria

cd /mnt/data2-pool/andy-ai/app

chmod +x scripts/deploy.sh

# Verify it's executable
ls -la scripts/deploy.sh
# Should show: -rwxr-xr-x
```

---

### Step 7: Test Deployment Manually (Optional but Recommended)

Before relying on webhooks, test the deploy script works:

```bash
ssh andy@moria

cd /mnt/data2-pool/andy-ai/app

# Run deployment script manually
bash scripts/deploy.sh

# Watch the log
tail -f logs/deployments/latest.log
```

If this succeeds, you know the deployment system works.

---

## How to Use It

### Normal Workflow

```bash
# On your Mac
cd ~/Dev/personal-ai-assistant

# Make changes, test locally
git add .
git commit -m "feat(api): add capture form to web interface"
git push origin main

# Deployment starts automatically on moria
# Wait 2-3 minutes for:
# - Code to pull
# - Frontend to build
# - Database migrations
# - Docker rebuild
# 
# System is live
```

---

## Monitoring Deployment

### View Deployment Logs

```bash
ssh andy@moria

# View latest deployment
tail -f /mnt/data2-pool/andy-ai/app/logs/deployments/latest.log

# View specific deployment by timestamp
tail -f /mnt/data2-pool/andy-ai/app/logs/deployments/20250120_143022.log

# View last 50 lines
tail -50 /mnt/data2-pool/andy-ai/app/logs/deployments/latest.log
```

### Check Webhook Receiver Container Status

```bash
ssh andy@moria

cd /mnt/data2-pool/andy-ai/app/docker

# Check if container is running
docker compose ps webhook-receiver

# View container logs
docker compose logs webhook-receiver

# Follow logs in real-time
docker compose logs -f webhook-receiver

# Check if port 9002 is responsive
curl http://localhost:9002/health
```

---

## Testing the Webhook

### Test 1: Verify GitHub Can Reach Webhook

GitHub should have already sent test webhooks. Check them:

1. Go to GitHub → personal-ai-assistant repo → Settings → Webhooks
2. Click on the webhook configuration
3. Scroll to "Recent Deliveries"
4. You should see POST requests with status 200

If you see 404 or 500, check that NPM is routing correctly:

```bash
ssh andy@moria

# Verify webhook receiver is listening on 9002
docker compose ps webhook-receiver
# Should show: Up (healthy)

# Check NPM proxy configuration
# Go to http://moria:81 → Hosts → Proxy Hosts → ai.gruff.icu
# Verify it forwards to moria:9002 (not 8000)
```

---

### Test 2: Trigger Manual Deployment

```bash
# Simulate a GitHub webhook (test locally first)
curl -X POST http://localhost:9002/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=incorrect" \
  -d '{}'

# Should return 401 (bad signature) - that's correct
```

---

### Test 3: Real Push to Main

```bash
cd ~/Dev/personal-ai-assistant

# Make a simple change
echo "# test" >> README.md

git add README.md
git commit -m "test: trigger webhook deployment"
git push origin main

# Watch the deployment happen
ssh andy@moria
tail -f /mnt/data2-pool/andy-ai/app/logs/deployments/latest.log
```

---

## Troubleshooting

### Issue: Webhook receiver container won't start

**Check:**
```bash
ssh andy@moria
cd /mnt/data2-pool/andy-ai/app/docker

docker compose ps webhook-receiver
# Check status

docker compose logs webhook-receiver
# Check error messages
```

**Common causes:**
- Dockerfile not found (webhook/Dockerfile doesn't exist)
- Python dependencies not installed (FastAPI/uvicorn missing)
- Port 9002 already in use
- webhook_receiver.py file not found in container

**Fix:**
```bash
# Verify files exist
ls -la webhook/webhook_receiver.py
ls -la webhook/Dockerfile

# Rebuild container (fresh build)
docker compose build --no-cache webhook-receiver

# Restart
docker compose up -d webhook-receiver

# Check logs
docker compose logs webhook-receiver
```

---

### Issue: Deployment script fails

**Check logs:**
```bash
tail -100 /mnt/data2-pool/andy-ai/app/logs/deployments/latest.log
```

**Common causes:**
- `npm install` fails (missing node/npm)
- `git pull` fails (SSH key issues)
- Docker build fails
- Alembic migration fails

**Quick fixes:**
```bash
# Ensure npm is available in your frontend container/image
# Test git pull manually
cd /mnt/data2-pool/andy-ai/app
git pull origin main

# Check Docker is working
docker --version
docker compose --version
```

---

### Issue: GitHub webhook not reaching moria

**Check:**
```bash
# From moria, test connectivity to webhook receiver
curl -v http://localhost:9002/health

# From your Mac, test the webhook endpoint
curl -v https://ai.gruff.icu/webhook
# Should return 400 (missing signature) - that's expected, means it reached

# Check NPM proxy configuration
# Go to http://moria:81 → Hosts → Proxy Hosts
# Verify ai.gruff.icu routes to moria:9002
```

---

### Issue: Webhook signature verification fails

**Check the secret matches:**
```bash
# In docker .env, secret should be:
grep WEBHOOK_SECRET /mnt/data2-pool/andy-ai/app/docker/.env

# In GitHub webhook settings:
# Go to GitHub → Settings → Webhooks → Edit
# Compare the "Secret" field with what's in .env
# They must match exactly
```

---

## What to Know

### Automatic Deployments

- **When:** Every push to `main` branch triggers deployment
- **Not when:** Pushes to other branches don't deploy
- **Duration:** 2-3 minutes (building frontend takes time)
- **Logs:** Saved to `/mnt/data2-pool/andy-ai/app/logs/deployments/`

### Deployment Order

1. Git pull (30 seconds)
2. npm install (1-2 minutes, if dependencies change)
3. npm build (1-2 minutes)
4. Copy to web/ (5 seconds)
5. Alembic upgrade (10 seconds)
6. Docker build (1-2 minutes)
7. Docker restart (15 seconds)
8. Health check (5 seconds)

**Total:** 2-3 minutes typical

### If Deployment Fails

1. Check logs: `tail -f /mnt/data2-pool/andy-ai/app/logs/deployments/latest.log`
2. Fix the issue locally
3. Push again
4. Webhook will trigger again automatically

**You can't accidentally break production by pushing bad code** - if it fails, the previous version is still running in Docker until the new deployment succeeds.

---

## Cleanup/Management Commands

```bash
ssh andy@moria
cd /mnt/data2-pool/andy-ai/app/docker

# Stop webhook receiver
docker compose stop webhook-receiver

# Start webhook receiver
docker compose start webhook-receiver

# Restart webhook receiver
docker compose restart webhook-receiver

# View logs
docker compose logs webhook-receiver

# Follow logs
docker compose logs -f webhook-receiver

# Remove and recreate (fresh start)
docker compose rm webhook-receiver
docker compose up -d webhook-receiver

# Manually trigger deployment
bash /mnt/data2-pool/andy-ai/app/scripts/deploy.sh
```

---

## Success Criteria

You'll know it's working when:

- ✅ Webhook receiver container is running: `docker compose ps webhook-receiver`
- ✅ Container status shows "Healthy": `docker compose ps webhook-receiver`
- ✅ Health check passes: `curl http://localhost:9002/health`
- ✅ You can push code and see deployment logs appear in real-time
- ✅ System is live within 3 minutes of pushing

---

## Next Steps

1. **Verify files exist** on moria from git pull
2. **Set WEBHOOK_SECRET** in docker/.env
3. **Build and start containers** with `docker compose build` and `docker compose up -d`
4. **Test manual deployment** with `bash scripts/deploy.sh`
5. **Push a test commit** to main
6. **Watch logs** as webhook triggers automatic deployment
7. **Verify system is live** after deployment completes

Once this is working, you never have to manually deploy again. Just push code.

---

**Questions? Check troubleshooting section or review the logs.**
