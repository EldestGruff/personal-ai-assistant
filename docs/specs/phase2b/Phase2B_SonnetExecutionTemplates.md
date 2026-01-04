# Phase 2B Sonnet Execution Templates

## Overview

These templates are self-contained sections you can copy-paste to a **NEW Sonnet chat** to execute each Phase 2B spec. Each template includes all context, project state, and instructions.

**Key Feature:** Sonnet reads the actual spec file from your filesystem (no manual copy-paste of specs needed).

---

# COPY & PASTE THIS FOR PHASE 2B SPEC 1

```
## CONTEXT: Phase 2B Spec 1 - Alembic & Testing Foundation

You are an expert Python developer assisting Andy with the Personal AI Assistant project.

**Project State:**
- Language: Python 3.12
- Framework: FastAPI with Pydantic and SQLAlchemy
- Database: SQLite (local, with eventual TrueNAS deployment)
- Project location: /Users/andy/Dev/personal-ai-assistant
- Repository: GitHub (EldestGruff/personal-ai-assistant)
- Status: Phase 2A complete (models, API skeleton, no database integration yet)

**Your Access:**
- You can read/write files directly on Andy's Mac filesystem
- All files are in /Users/andy/Dev/personal-ai-assistant/
- Use standard file operations (paths are absolute)
- Git is available for commits

**Your Constraints:**
- Follow strict standards from STANDARDS_INTEGRATION.md (clean code, 80%+ test coverage, comprehensive docstrings)
- Function max 20 lines, max 3 params, single responsibility
- All code must be production-ready
- Generate complete implementations, not stubs

**This Spec:** 2B-1 (Alembic migrations + testing foundation)

---

## SPECIFICATION

Read the complete specification from this file in Andy's project:
/Users/andy/Dev/personal-ai-assistant/Phase2B_Spec1_AlembicAndTesting.md

You have filesystem access - read this file directly to get the full specification.

---

## GENERATION INSTRUCTIONS

Generate complete, production-ready code for Phase 2B Spec 1.

**Files to Generate:**
1. migrations/env.py - Alembic environment configuration
2. migrations/versions/0001_initial_schema.py - Initial schema migration
3. tests/conftest.py - Pytest fixtures and configuration
4. tests/test_models.py - Comprehensive model validation tests
5. tests/fixtures/users.py - User test fixtures
6. tests/fixtures/thoughts.py - Thought test fixtures and factory
7. tests/fixtures/tasks.py - Task test fixtures and factory
8. pytest.ini - Pytest configuration

Deliver production-quality code ready for immediate integration.
```

---

# COPY & PASTE THIS FOR PHASE 2B SPEC 2

```
## CONTEXT: Phase 2B Spec 2 - Database Service Layer

You are an expert Python developer assisting Andy with the Personal AI Assistant project.

**Project State:**
- Language: Python 3.12
- Status: Phase 2B-1 COMPLETE ✅ (Alembic migrations and test infrastructure in place)

**This Spec:** 2B-2 (Database service layer with CRUD operations)

**Your Access:** You have filesystem access to /Users/andy/Dev/personal-ai-assistant/

---

## SPECIFICATION

Read the complete specification from this file in Andy's project:
/Users/andy/Dev/personal-ai-assistant/Phase2B_Spec2_ServiceLayer.md

You have filesystem access - read this file directly to get the full specification.

---

## GENERATION INSTRUCTIONS

Generate complete, production-ready service layer code for Phase 2B Spec 2.

**Files to Generate:**
1. src/services/__init__.py
2. src/services/exceptions.py
3. src/services/thought_service.py
4. src/services/task_service.py
5. src/services/context_service.py
6. src/services/claude_analysis_service.py
7. tests/integration/test_thought_service.py
8. tests/integration/test_task_service.py
9. tests/integration/test_context_service.py

Deliver production-quality service layer ready for API integration.
```

---

# COPY & PASTE THIS FOR PHASE 2B SPEC 3

```
## CONTEXT: Phase 2B Spec 3 - API Integration

You are an expert Python developer assisting Andy with the Personal AI Assistant project.

**Project State:**
- Language: Python 3.12
- Status: Phase 2B-1 & 2B-2 COMPLETE ✅ (migrations, services, tests all working)

**This Spec:** 2B-3 (API routes integrated with service layer)

**Your Access:** You have filesystem access to /Users/andy/Dev/personal-ai-assistant/

---

## SPECIFICATION

Read the complete specification from this file in Andy's project:
/Users/andy/Dev/personal-ai-assistant/Phase2B_Spec3_APIIntegration.md

You have filesystem access - read this file directly to get the full specification.

---

## GENERATION INSTRUCTIONS

Generate complete, production-ready API integration code for Phase 2B Spec 3.

**Files to Update/Generate:**
1. src/api/routes/thoughts.py - REPLACE with service-integrated version
2. src/api/routes/tasks.py - REPLACE with service-integrated version
3. src/api/middleware.py - UPDATE to add service exception handlers
4. tests/integration/test_api_endpoints.py - NEW comprehensive integration tests
5. tests/integration/test_thought_endpoints.py - NEW endpoint-specific tests
6. tests/integration/test_task_endpoints.py - NEW endpoint-specific tests

Deliver production-quality API integration ready for Phase 2C (deployment).
```

---

## How to Use

### For Spec 1 (First):
1. Copy the "COPY & PASTE THIS FOR PHASE 2B SPEC 1" section
2. Open a **NEW chat with Claude Sonnet**
3. Paste the entire section
4. Sonnet will read the spec file automatically from your filesystem
5. Review outputs, integrate, test, commit

### For Spec 2 (Second):
1. Wait for Spec 1 to be complete and tested ✅
2. Copy the "COPY & PASTE THIS FOR PHASE 2B SPEC 2" section
3. Open a **NEW chat with Claude Sonnet**
4. Paste the entire section
5. Follow outputs, integrate, test, commit

### For Spec 3 (Third):
1. Wait for Spec 2 to be complete and tested ✅
2. Copy the "COPY & PASTE THIS FOR PHASE 2B SPEC 3" section
3. Open a **NEW chat with Claude Sonnet**
4. Paste the entire section
5. Follow outputs, integrate, test, commit

---

## Why This Works Better

✅ **No manual spec copy-paste** - Template tells Sonnet the file path, it reads directly
✅ **Self-contained** - Each template has all context needed
✅ **No setup repetition** - No "yes you have filesystem access" in each chat
✅ **File is source of truth** - Sonnet reads the current version
✅ **Clean templates** - Just copy-paste and go

Perfect for sequential execution as time permits. 🚀
