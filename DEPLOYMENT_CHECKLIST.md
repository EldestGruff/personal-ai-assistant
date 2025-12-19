# Deployment Checklist - LM Studio + Auto-Tagging Update

## 🎯 What's New

- ✅ **Consciousness Check Fixed** - Web dashboard now works
- ✅ **Auto-Tagging Implemented** - AI suggests tags on thought creation
- ✅ **LM Studio Backend Added** - GPU-accelerated local inference
- ✅ **Multi-Backend Fallback** - LM Studio → Ollama → Claude

---

## 📋 Pre-Deployment Checklist

### 1. Verify Local AI Servers Running

**On 192.168.7.187:**

Check LM Studio:
```bash
curl http://192.168.7.187:1234/v1/models
```

Check Ollama:
```bash
curl http://192.168.7.187:11434/api/tags
```

---

### 2. Deploy to TrueNAS

```bash
cd docker
./deploy.sh moria
```

---

### 3. Verify Deployment

Check logs for:
```
✅ LM Studio backend registered (local-model)
✅ Ollama backend registered (gemma3:27b)
```

---

### 4. Test Features

- Open http://moria:8000/dashboard
- Click "Refresh Insights"
- Create thought without tags to test auto-tagging

---

**Status:** ☐ Success | ☐ Partial | ☐ Failed
