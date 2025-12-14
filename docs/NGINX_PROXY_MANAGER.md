# Nginx Proxy Manager Configuration Guide
**Personal AI Assistant - Reverse Proxy Setup**

---

## Overview

This guide covers setting up Nginx Proxy Manager (NPM) to provide:
- **HTTPS/SSL** termination for `ai.gruff.icu`
- **Reverse proxy** from public domain to internal Docker container
- **Security headers** and CORS configuration
- **LetsEncrypt** certificate management

---

## Prerequisites

- NPM installed and running on moria
- Access to NPM web interface (typically `http://moria:81`)
- DNS configured: `ai.gruff.icu` → Your public IP
- Port forwarding: 80/443 → moria:80/443 (on your Unifi UDR7)
- Personal AI Assistant deployed and running on port 8000

---

## Step-by-Step Configuration

### Step 1: Access NPM Interface

1. **Navigate to:** `http://moria:81` (or your NPM URL)
2. **Login** with your admin credentials
3. **Verify** NPM is healthy and connected

---

### Step 2: Add SSL Certificate (if not already exists)

**Navigate to:** SSL Certificates > Add SSL Certificate

#### Option A: Wildcard Certificate (Recommended)

**Domain Names:**
```
*.gruff.icu
gruff.icu
```

**Email:** `andy@fennerfam.com`

**Use DNS Challenge:** ✓ (Required for wildcard)
- **DNS Provider:** Select your provider (Cloudflare, Route53, etc.)
- **Credentials:** Enter API token/key

**Agreement:** ✓ I Agree to the Let's Encrypt Terms of Service

**Click:** Save

#### Option B: Single Subdomain Certificate

**Domain Names:**
```
ai.gruff.icu
```

**Email:** `andy@fennerfam.com`

**Use HTTP Challenge:** ✓ (Simpler, but only for specific subdomain)

**Agreement:** ✓ I Agree to the Let's Encrypt Terms of Service

**Click:** Save

**Wait 30-60 seconds** for LetsEncrypt verification.

---

### Step 3: Add Proxy Host for AI Assistant

**Navigate to:** Hosts > Proxy Hosts > Add Proxy Host

#### Details Tab

**Domain Names:**
```
ai.gruff.icu
```

**Scheme:** `http` (internal connection to Docker)

**Forward Hostname / IP:**
```
moria
```
*Or use the Docker bridge IP:*
```
172.17.0.1
```
*Or use the container IP (find with `docker inspect personal-ai-assistant-api`)*

**Forward Port:**
```
8000
```

**Options:**
- ✓ Cache Assets
- ✓ Block Common Exploits
- ✓ Websockets Support

#### SSL Tab

**SSL Certificate:** Select `*.gruff.icu` or `ai.gruff.icu`

**Options:**
- ✓ Force SSL
- ✓ HTTP/2 Support
- ✓ HSTS Enabled
- ✗ HSTS Subdomains (not needed for single subdomain)

#### Advanced Tab

**Custom Nginx Configuration:**

```nginx
# CORS Configuration for Web/Mobile Clients
# Allow requests from any origin (adjust if you want specific origins)
add_header Access-Control-Allow-Origin * always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS, PATCH" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-API-Key, Accept, Origin" always;
add_header Access-Control-Max-Age 86400 always;

# Handle preflight OPTIONS requests
if ($request_method = 'OPTIONS') {
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS, PATCH" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-API-Key, Accept, Origin" always;
    add_header Access-Control-Max-Age 86400 always;
    add_header Content-Length 0;
    add_header Content-Type text/plain;
    return 204;
}

# Security Headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Increase timeouts for long-running Claude API calls
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;
send_timeout 300s;

# Proxy headers
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host $host;
proxy_set_header X-Forwarded-Port $server_port;

# Enable compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
```

**Click:** Save

---

### Step 4: Verify Configuration

#### Test Internal Access (from TrueNAS)

```bash
curl http://localhost:8000/api/v1/health
```

Expected:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "..."
  }
}
```

#### Test HTTPS Access (from your Mac)

```bash
curl https://ai.gruff.icu/api/v1/health
```

Should return the same JSON with valid SSL.

#### Test from Browser

Navigate to:
```
https://ai.gruff.icu/docs
```

You should see the **FastAPI Swagger UI** documentation page.

#### Test API Endpoint

```bash
# With API key
curl -H "X-API-Key: YOUR_API_KEY" https://ai.gruff.icu/api/v1/thoughts
```

Should return `[]` (empty array) if no thoughts exist, or actual data.

---

## Advanced Configuration

### Rate Limiting (Optional)

To protect against abuse, add rate limiting in NPM Advanced tab:

```nginx
# Rate limiting zone (add at top of config)
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Apply to location block
limit_req zone=api_limit burst=20 nodelay;
limit_req_status 429;
```

This limits to 10 requests/second with burst of 20.

### IP Whitelisting (VPN Only Access)

If you want VPN-only access, whitelist your WireGuard subnet:

```nginx
# Allow only WireGuard VPN clients
allow 10.0.0.0/24;  # Replace with your WireGuard subnet
deny all;
```

### Custom Error Pages

```nginx
# Custom error handling
error_page 502 503 504 /50x.html;
location = /50x.html {
    return 503 '{"success": false, "error": {"code": "SERVICE_UNAVAILABLE", "message": "API is temporarily unavailable"}}';
    add_header Content-Type application/json;
}
```

---

## Troubleshooting

### 502 Bad Gateway

**Cause:** NPM can't reach the backend container.

**Solutions:**
1. Verify container is running: `docker-compose ps`
2. Check container health: `docker inspect personal-ai-assistant-api | grep -A 5 Health`
3. Test internal access: `curl http://moria:8000/api/v1/health`
4. Verify Docker network: `docker network inspect ai-assistant-network`
5. Try using container IP instead of hostname in NPM

**Find container IP:**
```bash
docker inspect personal-ai-assistant-api | grep IPAddress
```

### SSL Certificate Errors

**Cause:** Certificate not issued or expired.

**Solutions:**
1. Check certificate status in NPM: SSL Certificates
2. Verify DNS is correct: `nslookup ai.gruff.icu`
3. Check port forwarding: 80/443 must reach NPM
4. Re-request certificate
5. Check LetsEncrypt rate limits (50/week per domain)

### CORS Errors in Browser/Mobile

**Symptoms:**
- Console error: "CORS policy: No 'Access-Control-Allow-Origin' header"
- iOS Shortcut fails with network error

**Solutions:**
1. Verify Advanced config includes CORS headers (see Step 3)
2. Check browser network tab for actual headers returned
3. Ensure `OPTIONS` preflight handler is in place
4. Test with curl to verify headers:

```bash
curl -H "Origin: https://example.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-API-Key" \
     -X OPTIONS \
     -v \
     https://ai.gruff.icu/api/v1/thoughts
```

### Performance Issues

**Symptoms:** Slow responses, timeouts

**Solutions:**
1. Increase timeouts in Advanced config (see Step 3)
2. Check Docker container resources: `docker stats personal-ai-assistant-api`
3. Check Postgres performance: `docker stats personal-ai-assistant-db`
4. Enable gzip compression (included in config above)
5. Add caching for static assets (already enabled via "Cache Assets")

---

## Monitoring NPM

### Access Logs

**NPM Container:**
```bash
docker logs -f nginx-proxy-manager
```

**Check for errors:**
```bash
docker logs nginx-proxy-manager 2>&1 | grep ERROR
```

### View Live Connections

**NPM UI:** Dashboard shows:
- Active proxy hosts
- Certificate status
- Recent access logs

### Test from Multiple Locations

1. **Internal Network:** `curl http://moria:8000/api/v1/health`
2. **Via Proxy (internal):** `curl https://ai.gruff.icu/api/v1/health`
3. **External (over VPN):** Same as #2 from remote device
4. **iPhone (LTE):** Use browser or Shortcuts to test

---

## Port Forwarding Reference (Unifi UDR7)

Ensure these ports are forwarded to moria:

| External Port | Internal Port | Protocol | Destination | Service |
|---------------|---------------|----------|-------------|---------|
| 80            | 80            | TCP      | moria       | HTTP (LetsEncrypt) |
| 443           | 443           | TCP      | moria       | HTTPS (NPM) |

**Unifi Setup:**
1. Network > Settings > Routing & Firewall
2. Port Forward Rules
3. Add rules for 80 and 443 → moria IP

---

## Security Best Practices

### 1. Keep NPM Updated
```bash
docker pull jc21/nginx-proxy-manager:latest
docker-compose up -d nginx-proxy-manager
```

### 2. Strong Admin Password
Change default NPM admin password:
- **NPM UI:** Users > Edit Admin > Change Password

### 3. Enable 2FA (if available)
Check NPM settings for two-factor authentication.

### 4. Monitor Access Logs
Regularly review NPM access logs for suspicious activity.

### 5. Certificate Expiry Alerts
NPM sends email alerts for expiring certificates (verify email settings).

### 6. Firewall Rules
Only expose 80/443 publicly. Keep all other services (8000, 5432, etc.) internal.

---

## Integration with iOS Shortcuts

Your iOS Shortcuts will use:

**Base URL:** `https://ai.gruff.icu/api/v1`

**Headers:**
```
X-API-Key: YOUR_API_KEY
Content-Type: application/json
```

**Example Endpoints:**
- Create thought: `POST https://ai.gruff.icu/api/v1/thoughts`
- List thoughts: `GET https://ai.gruff.icu/api/v1/thoughts`
- Create task: `POST https://ai.gruff.icu/api/v1/tasks`

NPM handles SSL, CORS, and routing transparently.

---

## Backup NPM Configuration

NPM stores config in SQLite database. Back it up:

```bash
# Find NPM data volume
docker volume inspect nginx-proxy-manager_data

# Backup
docker run --rm -v nginx-proxy-manager_data:/data -v $(pwd):/backup alpine tar czf /backup/npm-backup.tar.gz /data

# Restore (if needed)
docker run --rm -v nginx-proxy-manager_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/npm-backup.tar.gz --strip 1"
```

---

## Next Steps

Once NPM is configured and tested:

1. ✅ Verify HTTPS access from multiple devices
2. ✅ Test CORS with iOS Shortcuts (next section)
3. ✅ Monitor access logs for first week
4. ✅ Set up certificate renewal reminders (NPM auto-renews)
5. ✅ Document API key in secure location (1Password, etc.)

---

**Configuration Date:** _____________
**Domain:** ai.gruff.icu
**Certificate Type:** ⬜ Wildcard | ⬜ Single Domain
**Status:** ⬜ Not Started | ⬜ Configured | ⬜ Tested | ⬜ Production
