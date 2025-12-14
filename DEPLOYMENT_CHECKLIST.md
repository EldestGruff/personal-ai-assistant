# Personal AI Assistant - Deployment Checklist
**TrueNAS SCALE Production Deployment**

---

## Pre-Deployment Preparation

### 1. Environment Setup
- [ ] TrueNAS dataset created: `/mnt/data2-pool/andy-ai`
- [ ] Dataset has correct permissions (check with `ls -la`)
- [ ] Postgres subdirectory created: `/mnt/data2-pool/andy-ai/postgres`
- [ ] SSH access to moria verified
- [ ] Git repository is clean (all changes committed)

### 2. Secrets and Keys
- [ ] Generate production API key: `python3 -c "import uuid; print(uuid.uuid4())"`
  - **API Key:** `____________________________________`
- [ ] Anthropic API key obtained from console.anthropic.com
  - **Anthropic Key:** `sk-ant-________________________________`
- [ ] Generate strong database password: `openssl rand -base64 32`
  - **DB Password:** `____________________________________`
- [ ] Store all secrets in secure location (1Password, etc.)

### 3. DNS Configuration
- [ ] DNS record created: `ai.gruff.icu` → Your public IP
- [ ] DNS propagation verified: `nslookup ai.gruff.icu`
- [ ] TTL set appropriately (300-3600 seconds)

### 4. Network Configuration
- [ ] Port forwarding configured on Unifi UDR7:
  - [ ] Port 80 → moria:80 (HTTP)
  - [ ] Port 443 → moria:443 (HTTPS)
- [ ] Firewall rules allow traffic to moria
- [ ] WireGuard VPN tested (if using VPN-only access)

---

## Deployment Steps

### Phase 1: Copy Files to TrueNAS

- [ ] **Option A:** SCP from Mac
  ```bash
  cd /Users/andy/Dev/personal-ai-assistant
  scp -r . andy@moria:/mnt/data2-pool/andy-ai/personal-ai-assistant/
  ```

- [ ] **Option B:** Git clone on TrueNAS
  ```bash
  ssh andy@moria
  cd /mnt/data2-pool/andy-ai
  git clone <repo-url> personal-ai-assistant
  ```

- [ ] Verify files copied correctly:
  ```bash
  ls -la /mnt/data2-pool/andy-ai/personal-ai-assistant/
  ```

### Phase 2: Configure Environment

- [ ] SSH into TrueNAS: `ssh andy@moria`
- [ ] Navigate to docker directory:
  ```bash
  cd /mnt/data2-pool/andy-ai/personal-ai-assistant/docker
  ```
- [ ] Copy production template:
  ```bash
  cp .env.production .env
  ```
- [ ] Edit environment file:
  ```bash
  nano .env
  ```
- [ ] Fill in all required values:
  - [ ] `API_KEY`
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `POSTGRES_PASSWORD`
  - [ ] `DEBUG=false`
  - [ ] `LOG_LEVEL=INFO`
- [ ] Verify `.env` file:
  ```bash
  cat .env | grep -v "^#" | grep -v "^$"
  ```
- [ ] **CRITICAL:** Do NOT commit `.env` to git

### Phase 3: Build and Deploy Containers

- [ ] Build Docker image:
  ```bash
  docker-compose build
  ```
  - [ ] Build completes without errors
  - [ ] Image size is reasonable (~500MB - 1GB)

- [ ] Start services:
  ```bash
  docker-compose up -d
  ```

- [ ] Verify containers started:
  ```bash
  docker-compose ps
  ```
  - [ ] `personal-ai-assistant-db` is `Up (healthy)`
  - [ ] `personal-ai-assistant-api` is `Up (healthy)`

- [ ] Check logs for errors:
  ```bash
  docker-compose logs db
  docker-compose logs api
  ```
  - [ ] Database migrations ran successfully
  - [ ] API server started on port 8000
  - [ ] No critical errors in logs

### Phase 4: Verify Local Access

- [ ] Test health endpoint from TrueNAS:
  ```bash
  curl http://localhost:8000/api/v1/health
  ```
  - [ ] Returns JSON: `{"success": true, "data": {"status": "healthy"}}`

- [ ] Test from Mac (same network):
  ```bash
  curl http://<moria-ip>:8000/api/v1/health
  ```
  - [ ] Same successful response

- [ ] Test with API key:
  ```bash
  curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/api/v1/thoughts
  ```
  - [ ] Returns `{"success": true, "data": []}`

- [ ] Access FastAPI docs:
  ```
  http://<moria-ip>:8000/docs
  ```
  - [ ] Swagger UI loads correctly
  - [ ] Can see all endpoints

---

## Nginx Proxy Manager Setup

### Phase 5: SSL Certificate

- [ ] Access NPM interface: `http://moria:81`
- [ ] Navigate to: SSL Certificates
- [ ] **Option A:** Use existing `*.gruff.icu` wildcard cert
  - [ ] Verify cert is valid and not expired

- [ ] **Option B:** Create new certificate for `ai.gruff.icu`
  - [ ] Add SSL Certificate
  - [ ] Domain: `ai.gruff.icu`
  - [ ] Email: `andy@fennerfam.com`
  - [ ] Use DNS Challenge (for wildcard) or HTTP Challenge
  - [ ] Agree to Let's Encrypt ToS
  - [ ] Wait for certificate issuance (~60 seconds)
  - [ ] Verify status shows "Valid"

### Phase 6: Proxy Host Configuration

- [ ] Navigate to: Hosts > Proxy Hosts
- [ ] Click: Add Proxy Host
- [ ] **Details Tab:**
  - [ ] Domain Names: `ai.gruff.icu`
  - [ ] Scheme: `http`
  - [ ] Forward Hostname/IP: `moria` (or `172.17.0.1`)
  - [ ] Forward Port: `8000`
  - [ ] Cache Assets: ✓
  - [ ] Block Common Exploits: ✓
  - [ ] Websockets Support: ✓

- [ ] **SSL Tab:**
  - [ ] SSL Certificate: Select certificate
  - [ ] Force SSL: ✓
  - [ ] HTTP/2 Support: ✓
  - [ ] HSTS Enabled: ✓

- [ ] **Advanced Tab:**
  - [ ] Paste CORS configuration (from docs/NGINX_PROXY_MANAGER.md)
  - [ ] Verify timeout settings (300s)
  - [ ] Verify security headers

- [ ] Click: Save

### Phase 7: Verify HTTPS Access

- [ ] Test from Mac (internal network):
  ```bash
  curl https://ai.gruff.icu/api/v1/health
  ```
  - [ ] Returns successful JSON
  - [ ] No SSL errors

- [ ] Test in browser:
  ```
  https://ai.gruff.icu/docs
  ```
  - [ ] Swagger UI loads
  - [ ] SSL certificate is valid (green padlock)

- [ ] Test with API key:
  ```bash
  curl -H "X-API-Key: YOUR_API_KEY" https://ai.gruff.icu/api/v1/thoughts
  ```
  - [ ] Returns successful response

- [ ] Test from iPhone (over LTE, WiFi off):
  - [ ] Open Safari: `https://ai.gruff.icu/docs`
  - [ ] Page loads correctly
  - [ ] No certificate warnings

---

## iOS Shortcuts Setup

### Phase 8: Create Shortcuts

- [ ] Open Shortcuts app on iPhone
- [ ] Create "Quick Capture" shortcut (see docs/IOS_SHORTCUTS.md)
  - [ ] Configure API URL: `https://ai.gruff.icu/api/v1/thoughts`
  - [ ] Add API key header
  - [ ] Test shortcut
  - [ ] Verify thought appears in database

- [ ] Create "Voice Capture" shortcut
  - [ ] Test dictation functionality
  - [ ] Verify thought captured

- [ ] Add shortcut to home screen widget
  - [ ] Test one-tap capture

- [ ] Configure Back Tap (optional):
  - [ ] Settings > Accessibility > Touch > Back Tap
  - [ ] Double Tap → Quick Capture
  - [ ] Test with phone unlocked

- [ ] Test Siri integration:
  - [ ] "Hey Siri, capture thought"
  - [ ] Verify it works

---

## Validation and Testing

### Phase 9: End-to-End Testing

- [ ] **Create Thought (API):**
  ```bash
  curl -X POST https://ai.gruff.icu/api/v1/thoughts \
    -H "X-API-Key: YOUR_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"content": "Test thought from deployment", "tags": ["test"]}'
  ```
  - [ ] Returns 201 Created
  - [ ] Response includes thought ID

- [ ] **Retrieve Thought:**
  ```bash
  curl -H "X-API-Key: YOUR_API_KEY" https://ai.gruff.icu/api/v1/thoughts
  ```
  - [ ] Returns array with test thought
  - [ ] Data is correct

- [ ] **Create Task (iOS Shortcut):**
  - [ ] Use "Quick Task" shortcut
  - [ ] Create test task
  - [ ] Verify notification appears

- [ ] **Retrieve Task (API):**
  ```bash
  curl -H "X-API-Key: YOUR_API_KEY" https://ai.gruff.icu/api/v1/tasks
  ```
  - [ ] Returns task created from shortcut

- [ ] **Delete Test Data:**
  - [ ] Use Swagger UI or API to delete test thoughts/tasks

### Phase 10: Performance Testing

- [ ] Capture 10 thoughts rapidly via iOS Shortcut
  - [ ] All 10 captured successfully
  - [ ] No timeouts or errors
  - [ ] Average capture time: _____ seconds

- [ ] Check API response time:
  ```bash
  time curl -H "X-API-Key: YOUR_API_KEY" https://ai.gruff.icu/api/v1/thoughts
  ```
  - [ ] Response time < 500ms

- [ ] Check Docker container resources:
  ```bash
  docker stats --no-stream
  ```
  - [ ] API container CPU: < 10%
  - [ ] API container RAM: < 500MB
  - [ ] DB container RAM: < 200MB

### Phase 11: Error Handling

- [ ] Test invalid API key:
  ```bash
  curl -H "X-API-Key: invalid" https://ai.gruff.icu/api/v1/thoughts
  ```
  - [ ] Returns 403 Forbidden
  - [ ] Error message is clear

- [ ] Test missing API key:
  ```bash
  curl https://ai.gruff.icu/api/v1/thoughts
  ```
  - [ ] Returns 403 Forbidden

- [ ] Test invalid endpoint:
  ```bash
  curl -H "X-API-Key: YOUR_API_KEY" https://ai.gruff.icu/api/v1/nonexistent
  ```
  - [ ] Returns 404 Not Found

- [ ] Test malformed JSON:
  ```bash
  curl -X POST https://ai.gruff.icu/api/v1/thoughts \
    -H "X-API-Key: YOUR_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{invalid json}'
  ```
  - [ ] Returns 400 Bad Request
  - [ ] Error is descriptive

---

## Monitoring and Maintenance Setup

### Phase 12: Logging and Monitoring

- [ ] Verify Docker logs are accessible:
  ```bash
  docker-compose logs -f api
  ```

- [ ] Set up log rotation (if needed):
  - [ ] Check Docker log driver settings
  - [ ] Configure max-size and max-file

- [ ] Bookmark key URLs:
  - [ ] API Docs: `https://ai.gruff.icu/docs`
  - [ ] Health Check: `https://ai.gruff.icu/api/v1/health`
  - [ ] NPM Interface: `http://moria:81`

- [ ] Document credentials in secure location (1Password):
  - [ ] API Key
  - [ ] Anthropic API Key
  - [ ] Database Password
  - [ ] NPM Admin Password

### Phase 13: Backup Configuration

- [ ] Create database backup script:
  ```bash
  nano /mnt/data2-pool/andy-ai/backup.sh
  # Paste backup script from docs/TRUENAS_DEPLOYMENT.md
  chmod +x /mnt/data2-pool/andy-ai/backup.sh
  ```

- [ ] Test backup manually:
  ```bash
  /mnt/data2-pool/andy-ai/backup.sh
  ```
  - [ ] Backup file created
  - [ ] File size is reasonable

- [ ] Schedule automated backups (cron):
  ```bash
  crontab -e
  # Add: 0 2 * * * /mnt/data2-pool/andy-ai/backup.sh
  ```

- [ ] Configure ZFS snapshots (TrueNAS UI):
  - [ ] Storage > Pools > data2-pool > andy-ai
  - [ ] Enable periodic snapshots
  - [ ] Hourly: Keep 24
  - [ ] Daily: Keep 7
  - [ ] Weekly: Keep 4

### Phase 14: Security Hardening

- [ ] Verify `.env` file is not world-readable:
  ```bash
  ls -la /mnt/data2-pool/andy-ai/personal-ai-assistant/docker/.env
  ```
  - [ ] Permissions should be 600 or 640

- [ ] Change NPM admin password (if default):
  - [ ] NPM UI > Users > Edit Admin
  - [ ] Use strong password (20+ chars)

- [ ] Verify firewall rules:
  ```bash
  sudo ufw status
  ```
  - [ ] Only 80/443 exposed publicly
  - [ ] 8000, 5432 internal only

- [ ] Enable fail2ban (optional, for NPM):
  - [ ] Monitors NPM access logs
  - [ ] Bans IPs after repeated failed requests

---

## Go-Live Checklist

### Phase 15: Final Verification

- [ ] All containers running and healthy:
  ```bash
  docker-compose ps
  ```

- [ ] Health check passing:
  ```bash
  curl https://ai.gruff.icu/api/v1/health
  ```

- [ ] iOS Shortcuts working from cellular (WiFi off)

- [ ] Database has test data (at least 1 thought, 1 task)

- [ ] Logs show no critical errors:
  ```bash
  docker-compose logs --tail=100 | grep ERROR
  ```

- [ ] Documentation complete:
  - [ ] All secrets stored securely
  - [ ] Deployment date recorded
  - [ ] Known issues documented (if any)

### Phase 16: Handoff to Production

- [ ] Set `DEBUG=false` in `.env` (verify)
- [ ] Set `LOG_LEVEL=INFO` in `.env` (verify)
- [ ] Restart containers with production config:
  ```bash
  docker-compose restart
  ```

- [ ] Configure container auto-restart:
  ```bash
  # Verify restart policy in docker-compose.yml
  # Should be: restart: unless-stopped
  ```

- [ ] Test failover (stop and restart):
  ```bash
  docker-compose stop
  docker-compose up -d
  ```
  - [ ] Containers start automatically
  - [ ] No data loss
  - [ ] Health check passes

---

## Post-Deployment

### Week 1 Monitoring

- [ ] **Day 1:** Capture 5+ thoughts via iOS
- [ ] **Day 1:** Review logs for errors
- [ ] **Day 3:** Test from external network (not home WiFi)
- [ ] **Day 7:** Review API usage (thoughts/tasks created)
- [ ] **Day 7:** Check database size and performance
- [ ] **Day 7:** Verify backups ran successfully

### Week 2 Optimization

- [ ] Identify friction points in capture workflow
- [ ] Optimize iOS Shortcuts based on usage
- [ ] Adjust NPM cache settings if needed
- [ ] Review Docker resource usage, adjust if needed

---

## Rollback Plan

If deployment fails or critical issues arise:

### Emergency Rollback

1. **Stop containers:**
   ```bash
   docker-compose down
   ```

2. **Preserve data:**
   ```bash
   sudo cp -r /mnt/data2-pool/andy-ai/postgres /mnt/data2-pool/andy-ai/postgres.backup
   ```

3. **Check ZFS snapshots:**
   ```bash
   zfs list -t snapshot | grep andy-ai
   ```

4. **Restore from snapshot (if needed):**
   ```bash
   zfs rollback data2-pool/andy-ai@snapshot-name
   ```

5. **Document issues:**
   - Error logs
   - What went wrong
   - Steps to reproduce

6. **Revert DNS (if necessary):**
   - Remove `ai.gruff.icu` DNS record
   - Wait for propagation

---

## Success Criteria

Deployment is successful when:

- ✅ API accessible via `https://ai.gruff.icu`
- ✅ iOS Shortcuts capture thoughts in < 10 seconds
- ✅ Health check returns healthy status
- ✅ No errors in logs after 24 hours
- ✅ Database persists across container restarts
- ✅ SSL certificate is valid
- ✅ External access works (over LTE)

---

## Sign-Off

- [ ] **Deployed By:** _________________________ **Date:** __________
- [ ] **Verified By:** _________________________ **Date:** __________
- [ ] **Production Ready:** ☐ Yes | ☐ No (explain): _______________

---

**Notes:**

```
[Space for deployment notes, issues encountered, etc.]








```

---

**Next Phase:** iOS Shortcuts optimization and daily usage validation
**Future Work:** Claude integration (consciousness checks, analysis)
