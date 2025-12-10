# Personal AI Assistant Framework - Architecture

**Status:** Design Phase  
**Last Updated:** December 10, 2025  
**Project Lead:** Andy

---

## 1. Project Overview

A query-based personal AI assistant framework that serves as a "conscious subconscious"—capturing thoughts, managing tasks, and surfacing relevant information. Initial focus on thought capture and ADHD-friendly task management, with future expansion to home automation and integration with Apple ecosystem.

**Core Problem Solving:**
- Capture transient thoughts and ideas before they're forgotten
- Provide context-aware reminders and task surfacing
- Centralize information across devices (iPhone, iPad, Mac)
- Leverage Claude API for reasoning and organization

---

## 2. Hardware & Infrastructure

| Device | Role | Status | Notes |
|--------|------|--------|-------|
| **TrueNAS SCALE** (25.04.2.6) | Backend service hub | Always-on | Hosts FastAPI service, database, state management |
| **M4 MacBook Air 32GB** | Primary client | Variable (on/off) | Daily driver; CLI tool, web interface access |
| **Windows Workstation** (i7-14700K, 128GB, Arc B580) | Secondary access | On-most-of-time | Can run desktop clients if needed; hobby/work machine |
| **iPad Pro M1** | Mobile web interface | As-needed | Web interface for quick capture away from desk |
| **iPhone 13 Pro Max** | Always-with-me access | Always-on | Web interface + iOS Shortcuts quick-capture |

**Network Infrastructure:**
- Home LAN (internal)
- WireGuard VPN (Unifi Dream Router 7) for remote access
- Self-signed HTTPS for secure remote connections

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────┐
│  TrueNAS SCALE (Always-On Backend)                  │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ Docker Container                             │   │
│  │                                              │   │
│  │  ┌────────────────────────────────────────┐ │   │
│  │  │ FastAPI Service                        │ │   │
│  │  │ • REST API endpoints                   │ │   │
│  │  │ • Thought capture & retrieval          │ │   │
│  │  │ • Context management                  │ │   │
│  │  │ • Claude API orchestration             │ │   │
│  │  │ • Task/reminder coordination           │ │   │
│  │  └────────────────────────────────────────┘ │   │
│  │                                              │   │
│  │  ┌────────────────────────────────────────┐ │   │
│  │  │ SQLite Database                        │ │   │
│  │  │ • Thoughts & metadata                  │ │   │
│  │  │ • User context/state                   │ │   │
│  │  │ • Task/reminder state                  │ │   │
│  │  │ • Interaction history                  │ │   │
│  │  └────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ Separate ZFS Dataset (Data persistence)      │   │
│  │ • Database backups                           │   │
│  │ • State snapshots                            │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
         │                    │
         │ REST API           │ WireGuard VPN
         │ (HTTP/HTTPS)       │ (Remote access)
         │                    │
    ┌────┴─────┬─────────┬───┴────┐
    │           │         │        │
    v           v         v        v
┌─────────┐ ┌──────────┐ ┌─────┐ ┌────────────┐
│ M4 Mac  │ │ iPad     │ │ Win │ │ iPhone     │
│ (CLI +  │ │ (Web UI) │ │     │ │ (Web + SH) │
│  Web UI)│ │          │ │     │ │            │
└─────────┘ └──────────┘ └─────┘ └────────────┘
```

---

## 4. Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Orchestration** | TrueNAS SCALE + Docker | Container isolation, ZFS reliability, GUI management |
| **Backend Service** | Python 3.11+ FastAPI | Async, modern, easy to test; handles REST API |
| **Database** | SQLite + dataset mount | Simple, reliable, journaled with ZFS |
| **API Design** | REST (JSON) | Simple, stateless, easy for clients |
| **External AI** | Claude API (Anthropic) | Reasoning, organization, context understanding |
| **Client Interfaces** | Web (Flask/simple HTML) + CLI | Cross-platform web, native CLI on Mac |
| **Mobile Integration** | iOS Shortcuts + Web UI | No native app needed initially |
| **VPN/Remote** | WireGuard (already configured) | Existing infrastructure, solid security |
| **Version Control** | Git (GitHub?) | Track changes, rollback capability |

---

## 5. Data Model (Sketch)

```
Thoughts
├── id (UUID)
├── timestamp
├── content (text)
├── tags (array)
├── context (location? app? time-of-day?)
├── status (active, archived, completed)
├── related_thoughts (links)
└── metadata (claude_summary, suggested_action)

Context/State
├── current_focus (what Andy is working on)
├── recent_activity (last N days)
├── habits/patterns (discovered by Claude)
├── preferences (remind me how often? format?)
└── apple_ecosystem (linked Reminders, Calendar)

Tasks/Reminders
├── id (UUID)
├── description
├── due_date/time
├── priority
├── status (pending, in-progress, done)
├── linked_thought (source)
└── apple_reminder_id (if synced)
```

---

## 6. Core Modules (Phase 1 & Beyond)

### Phase 1: Foundation (MVP)
1. **Thought Capture Engine**
   - Fast ingest via web form, CLI, Shortcuts
   - Timestamp, tag, context capture
   - Simple retrieval/search

2. **Web Interface**
   - Quick-capture form
   - Thought history/search
   - Simple dashboard

3. **iOS Integration**
   - Shortcuts workflow for quick capture
   - Web interface access on Safari

4. **API Layer**
   - REST endpoints for all operations
   - Authentication (basic API key for now)
   - Rate limiting (basic)

### Phase 2: Surfacing & Intelligence
5. **Claude Integration**
   - Periodic "consciousness checks" (e.g., every 30 min when you're active)
   - Summarize recent thoughts
   - Suggest actions or connections
   - Organize into themes

6. **Context Awareness**
   - Track patterns (when/where ideas happen)
   - Remember Andy's habits and preferences
   - Surface relevant past thoughts

7. **Task Management**
   - Convert thoughts → actionable tasks
   - Priority/deadline inference
   - Integration with Reminders.app (eventually)

### Phase 3+: Advanced (Future)
8. **Apple Ecosystem Integration**
   - Sync with Reminders.app
   - Calendar awareness
   - HomeKit integration for automation

9. **Active Monitoring** (when ready)
   - M4 Mac agent watching app focus, time blocks
   - Proactive surfacing vs. query-based

10. **Spamalyzer 2.0 Integration**
    - Email insights as context
    - Thought capture tied to emails

---

## 7. API Endpoints (Initial Design)

### Thought Management
- `POST /api/thoughts` - Capture new thought
- `GET /api/thoughts` - List thoughts (with filters, search)
- `GET /api/thoughts/{id}` - Retrieve single thought
- `PUT /api/thoughts/{id}` - Update thought
- `DELETE /api/thoughts/{id}` - Archive/delete
- `GET /api/thoughts/search?q=term` - Full-text search

### Claude Integration
- `GET /api/consciousness-check` - Trigger consciousness check (summary + suggestions)
- `POST /api/analyze` - Send specific thought to Claude for analysis
- `GET /api/themes` - Get Claude's discovered patterns/themes

### Task/Reminder Management
- `POST /api/tasks` - Create task from thought
- `GET /api/tasks` - List tasks
- `PUT /api/tasks/{id}` - Update task status
- `POST /api/sync/reminders` - Sync with Apple Reminders (future)

### Health/Debug
- `GET /api/health` - Service health check
- `GET /api/stats` - Usage statistics

---

## 8. Implementation Approach

### Docker Setup on TrueNAS SCALE

1. **Create ZFS Dataset**
   - Path: `/mnt/pool/andy-ai` (or similar)
   - Separate snapshots for backup independence

2. **Docker Container**
   - Base image: `python:3.11-slim`
   - Install FastAPI, SQLite, Anthropic SDK
   - Mount ZFS dataset to `/app/data`
   - Expose port (e.g., 8000 internally, 443 via reverse proxy)

3. **Management**
   - Use TrueNAS Apps/Portainer for GUI control
   - Auto-restart on failure
   - Environment variables for API keys (ANTHROPIC_API_KEY, etc.)

4. **Reverse Proxy** (for HTTPS)
   - Can be nginx in Docker or TrueNAS native
   - Self-signed cert for home network
   - Exposes to iPhone/iPad via WireGuard

### Development Workflow
- Git repo for source code (GitHub or self-hosted)
- Local development on M4 (Python venv)
- CI/CD for Docker image builds (GitHub Actions or simple script)
- Test in staging before prod deployment

---

## 9. Security & Privacy Considerations

| Concern | Approach |
|---------|----------|
| **Data on TrueNAS** | Private home network only; encrypted ZFS recommended |
| **API Authentication** | API key (UUID token) for each client; rotate regularly |
| **Claude API** | Rate-limit calls; keep sensitive data minimal |
| **HTTPS** | Self-signed cert on home network; full HTTPS for remote (WireGuard tunnel) |
| **Database Backups** | TrueNAS snapshots of ZFS dataset; separate backup strategy |
| **Access Control** | WireGuard VPN for remote; API key required |

---

## 10. Questions & Open Items

- [ ] Specific ZFS dataset naming/path?
- [ ] Docker image registry (Docker Hub, self-hosted)?
- [ ] Should we version the API (v1/ path)?
- [ ] How often should "consciousness checks" happen? (30 min? hourly? on-demand only?)
- [ ] Should database syncing across devices be needed, or is web interface sufficient?
- [ ] Backup strategy for ZFS dataset (external drive? secondary storage?)
- [ ] Authentication: simple API key, JWT, or OAuth?
- [ ] Rate limiting requirements?

---

## 11. Success Metrics

- [ ] Can capture a thought in <10 seconds from iPhone
- [ ] Web interface loads instantly on home LAN
- [ ] Claude can find/summarize relevant past thoughts when asked
- [ ] ADHD-friendly (thoughts don't disappear, reminders aren't fire-and-forget)
- [ ] Works both on-home and remote (via VPN)
- [ ] No data loss through multiple backups

---

## 12. Timeline & Milestones

| Phase | Target | Deliverables |
|-------|--------|--------------|
| **Phase 1** | 2-3 weeks | Backend service, web UI, iOS Shortcuts, MVP API |
| **Phase 2** | 4-6 weeks | Claude integration, context awareness, task mgmt |
| **Phase 3+** | TBD | Apple ecosystem integration, active monitoring |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-10 | 0.1 | Initial architecture document; hardware inventory; Phase 1-3 scope |
