# Phase 3B: Execution Guide - Settings, Automation & Enhanced Intelligence

**Status:** âœ… Two comprehensive specs ready for Opus  
**Timeline:** 3-6 hours execution + testing + integration  
**Complexity:** High (both specs are foundational architecture)  

---

## 📋 **Overview**

Phase 3B transforms the Personal AI Assistant from a basic thought capture system into an intelligent, configurable, personal assistant. Two major specifications:

### **Spec 1: Settings System & Automated Consciousness Checks**
- Multi-user architecture with RBAC
- Configurable settings (interval, depth, auto-analysis)
- APScheduler integration for automated checks
- Smart scheduling (only run if new thoughts exist)
- Database tracking of all scheduled runs

### **Spec 2: Enhanced AI Intelligence & Admin UI**
- Personal, contextual consciousness check prompts
- Auto-tagging and intent detection at thought capture
- Task suggestion workflow (ADHD-friendly)
- User profile system
- Admin page for all settings

---

## 🎯 **Model Recommendations**

### **Both Specs: Use OPUS** ⭐

**Why Opus for Spec 1?**
- Complex multi-user architecture with RBAC foundation
- APScheduler integration is critical and tricky
- Scheduler lifecycle management must be perfect
- Multiple database tables with complex relationships
- Dynamic job updating based on settings changes
- This is foundational infrastructure - mistakes are expensive

**Why Opus for Spec 2?**
- **Prompt engineering is THE KEY** to making analysis feel personal
- Sophisticated JSON parsing from AI responses
- Multiple new services with complex business logic
- Soft delete patterns for ADHD users (preserve change-of-mind history)
- Admin UI with JavaScript integration
- Must integrate seamlessly with existing Phase 2A/3A code
- Quality here directly impacts daily user experience

**Cost vs Quality:**
Both specs are architectural foundations. Getting them right the first time saves hours of troubleshooting and refactoring. Opus's superior code quality and attention to detail justify the extra cost here.

---

## 📊 **What Each Spec Produces**

### **Spec 1 Output (Settings & Automation)**

**Database:**
```
migrations/versions/000X_add_user_roles.py
migrations/versions/000Y_create_user_settings.py
migrations/versions/000Z_create_scheduled_analyses.py
```

**Models:**
```
src/models/settings.py              # NEW
src/models/scheduled_analysis.py    # NEW
src/models/enums.py                 # UPDATE (add roles, permissions)
src/database/models.py              # UPDATE (new tables)
```

**Services:**
```
src/services/settings_service.py              # NEW
src/services/scheduled_analysis_service.py    # NEW
src/services/scheduler_service.py             # NEW (APScheduler)
```

**API:**
```
src/api/routes/settings.py                    # NEW
src/api/routes/scheduled_analyses.py          # NEW
src/api/main.py                               # UPDATE (lifespan, scheduler)
requirements.txt                              # UPDATE (add apscheduler)
```

---

### **Spec 2 Output (AI Intelligence & Admin UI)**

**Database:**
```
migrations/versions/000A_enhance_thoughts.py
migrations/versions/000B_create_task_suggestions.py
migrations/versions/000C_create_user_profiles.py
```

**Models:**
```
src/models/task_suggestion.py       # NEW
src/models/user_profile.py          # NEW
src/models/thought.py               # UPDATE (new fields)
```

**Services:**
```
src/services/thought_intelligence_service.py   # NEW
src/services/enhanced_consciousness_check_service.py  # NEW
src/services/user_profile_service.py           # NEW
src/services/task_suggestion_service.py        # NEW
src/services/ai_backends/prompts.py            # NEW (prompt builders)
```

**API:**
```
src/api/routes/thoughts.py                     # UPDATE (add analysis)
src/api/routes/task_suggestions.py             # NEW
src/api/routes/profile.py                      # NEW
```

**UI:**
```
web/admin.html                      # NEW
web/admin.js                        # NEW
web/styles.css                      # UPDATE (admin styling)
```

---

## 🚀 **Execution Order**

### **Step 1: Spec 1 First (Settings & Automation)**

**Why first?**
- Spec 2 depends on user_settings table (for auto-tagging config)
- Spec 2 needs user_profiles table foundation
- Admin UI needs settings API to exist
- Scheduler must be running for automated checks

**Run Spec 1 → Test → Commit → Then run Spec 2**

---

### **Step 2: Execute Spec 1**

#### **Prepare the Prompt**

Open Claude Opus and use this template:

```
[Paste entire contents of Phase3B_Spec1_SettingsSystem.md]

---

CRITICAL INSTRUCTIONS:

You are generating code for Andy's Personal AI Assistant project (Phase 3B.1).

This is FOUNDATIONAL INFRASTRUCTURE that must be bulletproof:
- Multi-user architecture with RBAC (even though single-user now)
- APScheduler integration with persistent job store
- Dynamic scheduler updates based on settings changes
- Smart scheduling (skip if no new thoughts)
- Database migrations that handle existing data gracefully

STANDARDS TO FOLLOW:
- Functions: <20 lines, max 3 parameters, single responsibility
- Testing: 80%+ coverage, comprehensive edge cases
- Naming: snake_case functions, DescriptiveNoun classes
- Error Handling: Fail fast with clear messages
- Documentation: Docstrings on every function
- Code Quality: Readable > clever

CRITICAL REQUIREMENTS:
1. APScheduler MUST use SQLAlchemy job store for persistence
2. Scheduler MUST start on app startup (FastAPI lifespan)
3. Scheduler MUST shutdown gracefully on app shutdown
4. Settings updates MUST dynamically update scheduled jobs
5. "Smart" depth mode: max(last N days, min M thoughts)
6. Skip logic: If count_thoughts_since_last_check() == 0, skip
7. All database migrations MUST be idempotent
8. RBAC permissions defined even if not enforced yet

GENERATE:
- Complete, production-ready implementations
- Comprehensive tests (unit + integration)
- Alembic migrations for all schema changes
- Docstrings with examples
- Type hints throughout

OUTPUT FORMAT:
Provide code in markdown blocks with file paths:

```python
# migrations/versions/000X_add_user_roles.py
[complete file content]
```

```python
# src/services/scheduler_service.py
[complete file content]
```

DELIVER code ready for immediate integration.
```

#### **Review Opus Output**

Opus will generate ~15-20 files. Check:
- âœ… Alembic migrations are present and complete
- âœ… APScheduler configuration looks correct
- âœ… FastAPI lifespan events handle startup/shutdown
- âœ… Tests cover critical paths (settings CRUD, skip logic, job updates)
- âœ… Docstrings present on all services

#### **Integrate & Test**

```bash
cd ~/Dev/personal-ai-assistant

# Copy all generated files to correct locations
# (Opus will provide exact paths)

# Install new dependency
pip install apscheduler

# Update requirements.txt
pip freeze > requirements.txt

# Run migrations
alembic upgrade head

# Run tests
pytest tests/ -v

# Start API locally to verify scheduler
python -m uvicorn src.api.main:app --reload

# Verify scheduler started (check logs)
# Verify settings API works:
curl http://localhost:8000/api/v1/settings \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### **Commit Spec 1**

```bash
git add .
git commit -m "feat(settings): Phase 3B.1 - Settings system and automated consciousness checks

- Multi-user architecture with RBAC foundation
- User settings table with configurable intervals and depth
- APScheduler integration with persistent job store
- Scheduled analyses tracking table
- Smart scheduling (skip if no new thoughts)
- Settings API endpoints (GET/PUT/reset)
- Scheduler service with lifecycle management
- Dynamic job updates when settings change

Generated from Phase 3B Spec 1 by Claude Opus.
Tests: 80%+ coverage on critical paths."

git push origin main
```

---

### **Step 3: Execute Spec 2**

#### **Prepare the Prompt**

Open Claude Opus and use this template:

```
[Paste entire contents of Phase3B_Spec2_AIIntelligence.md]

---

CRITICAL INSTRUCTIONS:

You are generating code for Andy's Personal AI Assistant project (Phase 3B.2).

This is THE KEY to making the system feel personal and intelligent:
- Warm, contextual consciousness check prompts
- Structured thought analysis at capture time
- Auto-tagging with confidence scores
- Task suggestions that preserve ADHD change-of-mind history
- User profile that informs all analysis
- Admin UI for configuration

STANDARDS TO FOLLOW:
- Functions: <20 lines, max 3 parameters, single responsibility
- Testing: 80%+ coverage on prompt building, JSON parsing
- Naming: snake_case functions, DescriptiveNoun classes
- Error Handling: Graceful JSON parsing failures
- Documentation: Docstrings with prompt examples
- Code Quality: Readable > clever

CRITICAL REQUIREMENTS:
1. Prompt engineering is EVERYTHING - make it warm and personal
2. Include user profile context in ALL consciousness checks
3. Reference ongoing projects and past patterns
4. Task suggestions use soft delete (preserve for restoration)
5. Auto-tagging suggests 2-3 max, with confidence scores
6. JSON parsing must handle malformed AI responses gracefully
7. Admin UI must be functional (not just pretty)
8. Integration with existing Phase 2A/3A services

PROMPT QUALITY:
- DO: "You've been deep in infrastructure work today..."
- DON'T: "Main themes: Productivity, Task Management"
- ALWAYS reference Andy's context and projects
- ALWAYS use warm, encouraging tone
- ALWAYS explain reasoning for suggestions

GENERATE:
- Complete, production-ready implementations
- Comprehensive tests (especially prompt building)
- Alembic migrations for schema changes
- Admin page HTML/CSS/JS
- Docstrings with prompt examples

OUTPUT FORMAT:
Provide code in markdown blocks with file paths:

```python
# src/services/ai_backends/prompts.py
[complete file content]
```

```html
<!-- web/admin.html -->
[complete file content]
```

DELIVER code that makes Andy feel like he has a true personal assistant.
```

#### **Review Opus Output**

Opus will generate ~20-25 files. Check:
- âœ… Prompt templates are warm and personal (not sterile)
- âœ… JSON parsing handles errors gracefully
- âœ… Soft delete logic preserves task suggestions
- âœ… Admin UI is functional (forms work, history displays)
- âœ… Tests cover prompt building and response parsing
- âœ… Integration points with existing services are correct

#### **Integrate & Test**

```bash
# Copy all generated files

# Run migrations
alembic upgrade head

# Run tests
pytest tests/ -v

# Test thought capture with analysis
curl -X POST http://localhost:8000/api/v1/thoughts \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content": "Should improve the email spam analyzer"}'

# Verify analysis returned (thought_type, suggested_tags, etc.)

# Test admin page
open http://localhost:8000/admin

# Verify settings load and save work
```

#### **Commit Spec 2**

```bash
git add .
git commit -m "feat(intelligence): Phase 3B.2 - Enhanced AI intelligence and admin UI

- Personal, contextual consciousness check prompts
- User profile system (projects, interests, patterns)
- Thought intelligence service (auto-tagging, intent detection)
- Task suggestion workflow with soft delete
- Enhanced prompt engineering for warm, personal tone
- Admin page for settings, profile, and scheduler history
- Structured analysis at thought capture time
- JSON parsing with graceful error handling

Generated from Phase 3B Spec 2 by Claude Opus.
Tests: 80%+ coverage on prompt building and parsing."

git push origin main
```

---

## 🐳 **Deployment to TrueNAS**

After both specs are tested locally:

```bash
# On your Mac, push to GitHub
git push origin main

# SSH to moria
ssh andy@moria

# Navigate to app directory
cd /mnt/data2-pool/andy-ai/app

# Pull latest code
git pull origin main

# Rebuild Docker containers
cd docker
docker compose down
docker compose build
docker compose up -d

# Verify migrations ran
docker exec personal-ai-api alembic current

# Check scheduler started
docker logs personal-ai-api | grep -i scheduler

# Test API
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/settings

# Verify admin page accessible
open https://ai.gruff.edu/admin
```

---

## 🧪 **Testing Checklist**

### **Spec 1: Settings & Automation**

- [ ] Settings API GET/PUT/reset works
- [ ] Settings validation rejects invalid values (negative intervals)
- [ ] Scheduler starts on app startup
- [ ] Scheduler shuts down gracefully on app shutdown
- [ ] Consciousness check runs on schedule (verify logs)
- [ ] Check skips when no new thoughts exist
- [ ] Settings update dynamically updates scheduler job
- [ ] Scheduled analyses tracked in database
- [ ] History endpoint returns past runs
- [ ] Manual trigger works (POST /consciousness-check/trigger)

### **Spec 2: AI Intelligence & Admin UI**

- [ ] Thought capture triggers analysis (if enabled)
- [ ] Analysis extracts thought_type, suggested_tags
- [ ] Task suggestions created for actionable thoughts
- [ ] Consciousness check uses enhanced personal prompts
- [ ] Analysis references user profile (projects, patterns)
- [ ] User profile GET/PUT works
- [ ] Admin page loads and displays current settings
- [ ] Admin page forms save changes correctly
- [ ] Task suggestions can be accepted/rejected
- [ ] Soft-deleted suggestions can be restored
- [ ] Scheduler history displays in admin page

---

## 🎯 **Success Criteria**

### **After Spec 1:**
- âœ… Consciousness checks run every 30 minutes (configurable)
- âœ… Checks skip when no new thoughts exist
- âœ… Settings API fully functional
- âœ… Scheduler survives container restarts
- âœ… Multi-user architecture in place (even for single user)
- âœ… RBAC permissions defined

### **After Spec 2:**
- âœ… Consciousness checks feel warm and personal
- âœ… Analysis references Andy's projects and patterns
- âœ… Auto-tagging suggests 2-3 relevant tags
- âœ… Task detection creates suggestions with reasoning
- âœ… Admin page allows full configuration
- âœ… Deleted suggestions can be restored (ADHD-friendly)
- âœ… User profile editable and used in prompts

---

## ⏱️ **Timeline Estimate**

| Activity | Time |
|----------|------|
| **Spec 1 Execution** | |
| Run through Opus | 5-10 min |
| Review output | 10-15 min |
| Integration & file placement | 15-20 min |
| Testing locally | 20-30 min |
| Fixes/adjustments | 15-30 min |
| **Spec 1 Subtotal** | **1.5-2 hours** |
| | |
| **Spec 2 Execution** | |
| Run through Opus | 5-10 min |
| Review output | 15-20 min |
| Integration & file placement | 20-30 min |
| Testing locally | 30-45 min |
| Admin UI testing | 15-20 min |
| Fixes/adjustments | 20-40 min |
| **Spec 2 Subtotal** | **2-2.5 hours** |
| | |
| **Deployment** | |
| Deploy to TrueNAS | 15-20 min |
| Verify production | 10-15 min |
| **Deployment Subtotal** | **30-45 min** |
| | |
| **TOTAL** | **4-5.5 hours** |

---

## 🚨 **Troubleshooting**

### **If Spec 1 Issues:**

**Scheduler doesn't start:**
- Check FastAPI lifespan events are registered
- Verify APScheduler configuration
- Check database connection for job store
- Look for errors in docker logs

**Consciousness checks don't run:**
- Verify user settings.consciousness_check_enabled = True
- Check scheduler_service.schedule_user_consciousness_checks() was called
- Verify interval is set correctly
- Check scheduled_analyses table for records

**Settings updates don't take effect:**
- Verify API endpoint calls scheduler_service.schedule_user_consciousness_checks()
- Check if job is being replaced (replace_existing=True)
- Restart container to force re-read

### **If Spec 2 Issues:**

**Prompts feel sterile:**
- Check user profile has content (ongoing_projects, interests)
- Verify build_consciousness_check_prompt() includes profile
- Test prompt output directly (print it before sending to AI)

**JSON parsing fails:**
- AI responses may include markdown fences (```json)
- Strip these before parsing
- Use try/except with fallback to raw text

**Auto-tagging not working:**
- Check settings.auto_tagging_enabled = True
- Verify ThoughtIntelligenceService.analyze_thought_on_capture() is called
- Check AI backend is responding (not hitting rate limits)

**Admin page won't load:**
- Verify static file serving is configured
- Check file paths are correct (web/admin.html)
- Look for JavaScript errors in browser console

---

## 🤔 **If You Get Stuck**

1. **Branch the conversation** - Keep main conversation clean
2. **Check Phase 2A code** - These specs build on that foundation
3. **Read Opus output carefully** - It will explain its decisions
4. **Test incrementally** - Don't integrate everything at once
5. **Ask me (Ivy) for help** - I can debug with you

---

## 📝 **Next Steps After Phase 3B**

Once both specs are complete:

1. **Monitor automated consciousness checks** - Verify they run on schedule
2. **Adjust prompts if needed** - Fine-tune tone based on results
3. **Collect feedback** - How does the personal analysis feel?
4. **Consider Phase 4** - Home automation, Apple ecosystem integration?

---

## 🎉 **You're Ready!**

Both specs are comprehensive and ready for Opus. Take your time with integration and testing - this is foundational work that will support everything else.

**Remember:**
- Opus quality > Sonnet speed for foundational work
- Test incrementally, don't batch everything
- Keep main conversation clean by branching for troubleshooting
- The goal is a system that feels genuinely personal and helpful

Let's build something amazing! 🚀✨
