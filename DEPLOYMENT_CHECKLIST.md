# Deployment Checklist - LM Studio + Auto-Tagging Update

## 🎯 What's New

- ✅ **Consciousness Check Fixed** - Web dashboard now uses v2 endpoint
- ✅ **Auto-Tagging Implemented** - AI suggests tags on thought creation
- ✅ **LM Studio Backend Added** - GPU-accelerated local inference with Arc B580
- ✅ **Multi-Backend Fallback** - LM Studio → Ollama → Claude
- ✅ **Web Permissions Fixed** - Dashboard loading issue resolved
- ✅ **Deployment Path Fixed** - Correct TrueNAS path (/mnt/data2-pool/andy-ai/app)

---

## 📋 Pre-Deployment Checklist

### 1. Verify Local AI Servers Running

**On 192.168.7.187:**

Check LM Studio (GPU-accelerated):
```bash
curl http://192.168.7.187:1234/v1/models
```

Check Ollama (CPU fallback):
```bash
curl http://192.168.7.187:11434/api/tags
```

Expected: Both should return 200 OK with model lists

---

### 2. Deploy to TrueNAS

```bash
cd docker
./deploy.sh moria
```

The deployment script now:
- Uses correct path: `/mnt/data2-pool/andy-ai/app`
- Automatically fixes web directory permissions post-deployment
- Uses `--no-cache` build for clean image builds

---

### 3. Verify Deployment

Check logs for backend registration:
```bash
ssh andy@moria 'cd /mnt/data2-pool/andy-ai/app/docker && docker compose logs api | grep backend'
```

Expected output:
```
✅ LM Studio backend registered (local-model)
✅ Ollama backend registered (gemma3:27b)
✅ Claude backend registered
```

---

### 4. Test Features

**Consciousness Check:**
1. Open http://moria:8000/dashboard
2. Click "Refresh Insights"
3. Should see analysis from LM Studio (primary) or Ollama (fallback)
4. Check footer for backend used: "🤖 lmstudio" or "🤖 ollama"

**Auto-Tagging:**
1. Create a thought without tags via API or dashboard
2. AI should suggest relevant tags based on content
3. Check logs: `docker compose logs api | grep "Auto-tagged"`

**Backend Fallback:**
1. Stop LM Studio on 192.168.7.187
2. Create thought or refresh insights
3. Should automatically fall back to Ollama
4. Restart LM Studio, should return to primary

---

### 5. Verify Dashboard Access

```bash
curl -I http://moria:8000/dashboard/
```

Expected: `HTTP/1.1 200 OK` (no more Permission Denied errors)

---

## 🐛 Troubleshooting

**Web Permission Errors:**
If you see `PermissionError: [Errno 13] Permission denied: '/app/web/index.html'`:
```bash
ssh andy@moria
docker exec -u root personal-ai-api chmod -R 755 /app/web
```

**Backend Not Registering:**
Check if service is reachable:
```bash
docker exec personal-ai-api curl http://192.168.7.187:1234/v1/models
docker exec personal-ai-api curl http://192.168.7.187:11434/api/tags
```

**Auto-Tagging Not Working:**
Check if `auto_tag=true` parameter is passed:
```bash
ssh andy@moria 'cd /mnt/data2-pool/andy-ai/app/docker && docker compose logs api | grep -i tag'
```

---

**Deployment Status:** ☐ Ready to Deploy | ☐ Success | ☐ Partial | ☐ Failed
