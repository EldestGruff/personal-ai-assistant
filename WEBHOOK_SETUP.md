# GitHub Webhooks Deployment System Setup

**Status:** Ready for implementation  
**Target:** TrueNAS SCALE (moria)  
**Workflow:** Push to main → Auto-deploy  

---

## Overview

When you push code to `main` on GitHub:

1. GitHub sends webhook to `https://ai.gruff.icu/webhook`
2. Nginx Proxy Manager routes it to `moria:9002/webhook`
3. Webhook receiver validates signature and triggers deployment
4. Deployment script pulls code, builds frontend, restarts Docker
5. Everything is logged

**From your perspective:** Push code, wait 2-3 minutes, system is live.

---

## One-Time Setup (on moria)

### Step 1: Verify Git Repository

First, moria needs to be a git repository that can pull from GitHub.

```bash
ssh andy@moria
cd /mnt/data2-pool/andy-ai/app

# Check if git repo exists
git remote -v
# Should show: origin https://github.com/EldestGruff/personal-ai-assistant.git

# If NOT set up as git repo yet:
git init
git remote add origin https://github.com/EldestGruff/personal-ai-assistant.git
git fetch origin
git checkout main
```

**Why:** The deploy script needs to pull code from GitHub. If moria doesn't have `.git/`, deployment will fail.

---

### Step 2: Set Up Webhook Receiver Service

Copy webhook receiver to moria:

```bash
# On your Mac
scp webhook/webhook_receiver.py andy@moria:/mnt/data2-pool/andy-ai/app/webhook/

# SSH into moria
ssh andy@moria
cd /mnt/data2-pool/andy-ai/app

# Create webhook directory if it doesn't exist
mkdir -p webhook
```

---

### Step 3: Create Systemd Service File

Webhook receiver needs to run as a service that auto-starts on reboot.

```bash
ssh andy@moria

# Create systemd service file
sudo tee /etc/systemd/system/personal-ai-webhook.service > /dev/null << 'EOF'
[Unit]
Description=Personal AI Assistant Webhook Receiver
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=andy
WorkingDirectory=/mnt/data2-pool/andy-ai/app
Environment="WEBHOOK_SECRET=thisisasecret"
Environment="DEPLOY_SCRIPT=/mnt/data2-pool/andy-ai/app/scripts/deploy.sh"
Environment="LOG_DIR=/mnt/data2-pool/andy-ai/app/logs/deployments"
ExecStart=/usr/local/bin/python3 -m uvicorn webhook.webhook_receiver:app --host 0.0.0.0 --port 9002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable personal-ai-webhook.service
sudo systemctl start personal-ai-webhook.service

# Verify it started
sudo systemctl status personal-ai-webhook.service
```

**What this does:**
- Creates a service that runs `webhook_receiver.py` on port 9002
- Automatically restarts if it crashes
- Auto-starts on moria reboot
- Sets environment variables (webhook secret, paths)

---

### Step 4: Verify Webhook Receiver is Running

```bash
# Check if service is active
sudo systemctl status personal-ai-webhook.service

# Check if port 9002 is listening
sudo netstat -tlnp | grep 9002
# Should show: tcp 0 0 0.0.0.0:9002 0.0.0.0:* LISTEN

# Test health endpoint (from moria)
curl http://localhost:9002/health
# Should return: {"status":"healthy","service":"webhook-receiver"}
```

---

### Step 5: Make Deploy Script Executable

```bash
ssh andy@moria
cd /mnt/data2-pool/andy-ai/app

chmod +x scripts/deploy.sh

# Verify it's executable
ls -la scripts/deploy.sh
# Should show: -rwxr-xr-x (executable)
```

---

### Step 6: Test Deployment Manually (Optional but Recommended)

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
# - Docker restart
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

### Check Webhook Receiver Status

```bash
ssh andy@moria

# Check if service is running
sudo systemctl status personal-ai-webhook.service

# View service logs
sudo journalctl -u personal-ai-webhook.service -f

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

If you see 404 or 500, something is wrong with the routing.

### Test 2: Trigger Manual Deployment

```bash
# Simulate a GitHub webhook (test locally first)
curl -X POST http://localhost:9002/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=incorrect" \
  -d '{}'

# Should return 401 (bad signature) - that's correct
```

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

### Issue: Webhook receiver not starting

**Check:**
```bash
sudo systemctl status personal-ai-webhook.service
sudo journalctl -u personal-ai-webhook.service -n 50
```

**Common causes:**
- Python/uvicorn not installed
- Port 9002 already in use
- Directory permissions

**Fix:**
```bash
# Install dependencies
pip install fastapi uvicorn

# Check port 9002
lsof -i :9002
# If something is using it, kill it

# Restart service
sudo systemctl restart personal-ai-webhook.service
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
# Ensure npm is available
which npm
npm --version

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
# From moria, test connectivity to NPM
curl -v http://localhost:81/  # NPM admin interface

# From your Mac, test the webhook endpoint
curl -v https://ai.gruff.icu/webhook

# Check NPM proxy configuration
# Go to http://moria:81 → Hosts → Proxy Hosts
# Verify ai.gruff.icu routes to moria:9002
```

---

### Issue: Webhook signature verification fails

**Check the secret matches:**
```bash
# In webhook_receiver.py, secret is read from environment variable
echo $WEBHOOK_SECRET

# In GitHub webhook settings, the secret should match exactly
# Go to GitHub → Settings → Webhooks → Edit
# Compare the "Secret" field with what's in systemd service file
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

## Cleanup Commands

If you need to manually manage things:

```bash
# Stop webhook receiver
sudo systemctl stop personal-ai-webhook.service

# Start webhook receiver
sudo systemctl start personal-ai-webhook.service

# Restart webhook receiver
sudo systemctl restart personal-ai-webhook.service

# View recent logs
sudo journalctl -u personal-ai-webhook.service -n 100

# Disable auto-start (if you want to disable automatic deployments)
sudo systemctl disable personal-ai-webhook.service

# Re-enable auto-start
sudo systemctl enable personal-ai-webhook.service

# Manually trigger deployment
bash /mnt/data2-pool/andy-ai/app/scripts/deploy.sh
```

---

## Success Criteria

You'll know it's working when:

- ✅ Webhook receiver service is running: `sudo systemctl status personal-ai-webhook.service`
- ✅ Port 9002 is listening: `sudo netstat -tlnp | grep 9002`
- ✅ Health check passes: `curl http://localhost:9002/health`
- ✅ You can push code and see deployment logs appear in real-time
- ✅ System is live within 3 minutes of pushing

---

## Next Steps

1. **Run one-time setup** on moria (all the sections above)
2. **Test manual deployment** with `bash scripts/deploy.sh`
3. **Push a test commit** to main
4. **Watch logs** as webhook triggers automatic deployment
5. **Verify system is live** after deployment completes

Once this is working, you never have to manually deploy again. Just push code.

---

**Questions? Check troubleshooting section or review the logs.**
