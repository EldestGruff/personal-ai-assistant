# Personal AI Assistant

**A query-based personal AI assistant that serves as your "conscious subconscious" - capturing thoughts, managing tasks, and surfacing relevant information through AI analysis.**

Version: 0.1.0  
Status: Active Development (Phase 3B Complete)  
Architecture: FastAPI Backend + Vanilla JS Frontend + PostgreSQL Database

---

## 🎯 **What It Does**

The Personal AI Assistant helps you:
- **Capture transient thoughts** before they're forgotten (ADHD-friendly)
- **Auto-analyze thoughts** with AI to extract intent, suggest tags, and detect actionable items
- **Surface relevant past thoughts** through Claude-powered consciousness checks
- **Manage tasks** with confidence-based AI suggestions
- **Track patterns** in your thinking and work habits
- **Access everything** from iPhone, iPad, Mac, or any web browser

**Core Philosophy:** Never lose a thought. Always have context when you need it.

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (or use Docker)
- Claude API key (optional: Ollama for local AI)

### **Local Development**

```bash
# 1. Clone repository
git clone https://github.com/EldestGruff/personal-ai-assistant.git
cd personal-ai-assistant

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY and database credentials

# 4. Run database migrations
alembic upgrade head

# 5. Start the API server
uvicorn src.api.main:app --reload --port 8000

# 6. Access the web dashboard
open http://localhost:8000/dashboard
```

### **Production Deployment (TrueNAS/Docker)**

```bash
# See docs/deployment/TRUENAS_DEPLOYMENT.md for complete guide

cd docker
docker compose up -d

# API: http://your-server:8000
# Dashboard: http://your-server:8000/dashboard
```

---

## 📊 **Architecture Overview**

```
┌─────────────────────────────────────────────────────────┐
│  Web Dashboard (Vanilla JS)                             │
│  - Thought capture                                      │
│  - Task management                                      │
│  - AI suggestions                                       │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API
                  ↓
┌─────────────────────────────────────────────────────────┐
│  FastAPI Backend (Python)                               │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ API Routes  │→ │  Services    │→ │   Database    │  │
│  │ (10 files)  │  │  (Thoughts,  │  │  (PostgreSQL) │  │
│  │             │  │   Tasks,     │  │               │  │
│  │             │  │   Claude AI) │  │               │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                  │
                  ↓
          ┌───────────────┐
          │  Claude API   │
          │  (External)   │
          └───────────────┘
```

**For detailed architecture, see:** [docs/BACKEND_SYSTEM_ARCHITECTURE.md](docs/BACKEND_SYSTEM_ARCHITECTURE.md)

---

## 📁 **Project Structure**

```
personal-ai-assistant/
├── src/                    # Backend source code
│   ├── api/               # FastAPI routes & middleware
│   ├── database/          # SQLAlchemy models & session
│   ├── models/            # Pydantic models (10 types)
│   └── services/          # Business logic layer
├── web/                   # Vanilla JS frontend (ACTIVE)
├── alembic/               # Database migrations (7 versions)
├── tests/                 # Test suite (unit + integration)
├── docs/                  # 📚 All documentation (organized!)
│   ├── development/      # ORCHESTRATION_STRATEGY, STANDARDS
│   ├── deployment/       # TrueNAS, webhook, checklists
│   ├── setup/            # Initial setup instructions
│   └── specs/            # Phase specifications (2A, 2B, 3B)
├── docker/                # Docker configuration
└── archive/               # Historical/unused code
```

---

## 🧠 **Core Features**

### **Phase 2A: Foundation** ✅
- FastAPI backend with 10 REST endpoints
- SQLAlchemy ORM with PostgreSQL
- Thought & task CRUD operations
- Database migrations with Alembic

### **Phase 2B: Services & Testing** ✅
- Service layer (Thoughts, Tasks, Context, Claude)
- 187 tests with 81.79% coverage
- Error handling & validation
- Async background tasks

### **Phase 3A: Web Interface** ✅
- Vanilla JS dashboard (mobile-first)
- Real-time thought capture
- Task management
- Search & filtering

### **Phase 3B: AI Intelligence** ✅
- Auto-tagging with confidence scores
- Task detection & suggestions
- User profiles & preferences
- Scheduled consciousness checks
- Admin settings UI

---

## 🔧 **Technology Stack**

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.12 + FastAPI | REST API server |
| **Database** | PostgreSQL 15 | Primary data store |
| **ORM** | SQLAlchemy 2.0 | Database abstraction |
| **Migrations** | Alembic | Schema versioning |
| **AI** | Claude API (Anthropic) | Thought analysis & intelligence |
| **Frontend** | Vanilla JavaScript | Web dashboard |
| **Deployment** | Docker + TrueNAS SCALE | Container orchestration |
| **Testing** | Pytest | Unit & integration tests |
| **VPN** | WireGuard | Secure remote access |

---

## 📖 **Documentation**

### **Getting Started**
- [Setup Instructions](docs/setup/SETUP_INSTRUCTIONS.md) - Initial environment setup
- [Quick Reference](docs/QUICK_REFERENCE.md) - Common commands & workflows

### **Architecture & Design**
- [System Architecture](docs/BACKEND_SYSTEM_ARCHITECTURE.md) - Component diagrams & overview
- [File Organization](docs/BACKEND_FILE_ORGANIZATION.md) - Complete file inventory
- [Data Flow](docs/BACKEND_DATA_FLOW.md) - Request flows & sequence diagrams
- [Component Details](docs/BACKEND_COMPONENT_DETAILS.md) - Models, services, routes

### **Development**
- [Orchestration Strategy](docs/development/ORCHESTRATION_STRATEGY.md) - Development philosophy
- [Standards Integration](docs/development/STANDARDS_INTEGRATION.md) - Coding standards & quality

### **Deployment**
- [TrueNAS Deployment](docs/deployment/TRUENAS_DEPLOYMENT.md) - Production setup
- [Webhook Setup](docs/deployment/WEBHOOK_SETUP.md) - Automated deployments
- [Deployment Checklist](docs/deployment/DEPLOYMENT_CHECKLIST.md) - Pre-deployment verification

### **Specifications**
- [Phase 2A Specs](docs/specs/phase2a/) - Data models, API, database schema
- [Phase 2B Specs](docs/specs/phase2b/) - Services, testing, coverage
- [Phase 3B Specs](docs/specs/phase3b/) - Settings system, AI intelligence

---

## 🧪 **Testing**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_thoughts.py

# Current coverage: 81.79% (187 tests)
```

---

## 🚢 **Deployment**

### **Production Environment**
- **Server:** TrueNAS SCALE (moria)
- **URL:** https://ai.gruff.edu
- **Database:** PostgreSQL in Docker container
- **API:** Docker container (personal-ai-api)
- **Reverse Proxy:** Nginx Proxy Manager
- **SSL:** Let's Encrypt via Nginx

### **Automated Deployment**
GitHub webhook triggers deployment on push to main:
```bash
# Webhook receives push event
→ Git pull on moria
→ Docker compose restart api
→ New code live in ~10 seconds
```

See [docs/deployment/WEBHOOK_SETUP.md](docs/deployment/WEBHOOK_SETUP.md) for configuration.

---

## 🎨 **Design Philosophy**

### **ADHD-Friendly**
- **Fast capture:** < 10 seconds from iPhone to database
- **No friction:** Minimal fields required (just thought content)
- **Forgiving:** Tasks survive source thought deletion
- **Encouraging:** AI provides warm, supportive analysis

### **Privacy-First**
- **Self-hosted:** All data on your infrastructure
- **No tracking:** No analytics, no telemetry
- **Open source:** Audit the code yourself

### **Production-Quality**
- **80%+ test coverage**
- **Comprehensive error handling**
- **Proper logging & monitoring**
- **Database migrations tracked**

---

## 🔑 **API Authentication**

All API requests require authentication:

```bash
# Via header
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://ai.gruff.edu/api/v1/thoughts

# API key stored in .env
API_KEY=550e8400-e29b-41d4-a716-446655440000
```

---

## 📱 **iOS Integration**

Quick-capture via iOS Shortcuts:

1. Create new Shortcut
2. Add "Get Contents of URL" action
3. URL: `https://ai.gruff.edu/api/v1/thoughts`
4. Method: POST
5. Headers: `Authorization: Bearer YOUR_API_KEY`
6. JSON Body: `{"content": "Shortcut Input"}`
7. Add to Share Sheet for instant capture

---

## 🐛 **Known Issues**

See [GitHub Issues](https://github.com/EldestGruff/personal-ai-assistant/issues) for current bugs and feature requests.

---

## 📜 **License**

Private project - not open source (yet).

---

## 🙏 **Acknowledgments**

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
- [Claude](https://www.anthropic.com/claude) - AI analysis & intelligence
- [Bootstrap](https://getbootstrap.com/) - Frontend styling

---

## 📧 **Contact**

**Andy** - Project Lead  
GitHub: [@EldestGruff](https://github.com/EldestGruff)

---

## 🗺️ **Roadmap**

### **Phase 4: Advanced Features** (Planned)
- [ ] Apple Reminders integration
- [ ] Calendar awareness
- [ ] Multi-user support
- [ ] Mobile app (iOS/Android)
- [ ] Ollama local AI support
- [ ] Voice capture

### **Phase 5: Intelligence** (Future)
- [ ] Pattern recognition & insights
- [ ] Proactive suggestions
- [ ] Context-aware reminders
- [ ] Email integration (Spamalyzer 2.0)

---

**Version:** 0.1.0  
**Last Updated:** January 4, 2026  
**Status:** Active Development
