# Phase 2B: Execution Guide

**Status:** âœ… Three detailed specs created and ready for execution  
**Target:** Claude Sonnet  
**Expected Effort:** 3-4 hours (generate + review + test + integrate)  
**Timeline:** 1-2 days  

---

## Phase 2B Overview

Phase 2B transforms Phase 2A's API skeleton into a **fully functional backend with database integration and comprehensive tests**.

**What Phase 2B Accomplishes:**

| Spec | Focus | Output | LOC |
|------|-------|--------|-----|
| **2B-1** | Alembic Migrations + Testing Foundation | Migration files, test fixtures, conftest | ~400 |
| **2B-2** | Database Service Layer | 4 service classes with CRUD operations | ~800 |
| **2B-3** | API → Service Integration | Updated routes, error handling, integration tests | ~600 |

**Total Expected Output:** ~1,800 lines of production code + ~800 lines of tests

---

## Execution Order (Critical!)

### âœ… Step 1: Phase 2B Spec 1 (Alembic & Testing)
**Time:** 30 min generate + 20 min review = 50 min total

This **must** come first because:
- Sets up Alembic migrations infrastructure
- Creates test fixtures and conftest
- Provides foundation for service tests in Spec 2
- Enables in-memory SQLite database for testing

**What You'll Get:**
- Alembic migration: `0001_initial_schema.py`
- Test fixtures: `users.py`, `thoughts.py`, `tasks.py`
- Test configuration: `conftest.py`, `pytest.ini`
- Model validation tests: `test_models.py`

**Run Spec 1 When Ready:**
```bash
# Copy all outputs to project
# Update migrations/ and tests/

# Verify setup works
pytest tests/  # Should pass

# Commit
git add migrations/ tests/
git commit -m "feat(tests): add Alembic migrations and testing infrastructure"
```

---

### âœ… Step 2: Phase 2B Spec 2 (Service Layer)
**Time:** 45 min generate + 30 min review = 75 min total

Depends on Spec 1 (needs test fixtures, conftest).

**What You'll Get:**
- `src/services/thought_service.py` (~300 lines)
- `src/services/task_service.py` (~200 lines)
- `src/services/context_service.py` (~150 lines)
- `src/services/claude_analysis_service.py` (~150 lines)
- `src/services/exceptions.py` (custom exceptions)
- Service integration tests: `tests/integration/test_*_service.py`

**Run Spec 2 When Ready:**
```bash
# Copy all service files
# Copy integration tests

# Verify services work
pytest tests/integration/  # Should pass

# Check coverage
pytest --cov=src/services tests/

# Commit
git add src/services/ tests/integration/
git commit -m "feat(services): add database service layer with CRUD operations

- ThoughtService: full thought CRUD + search
- TaskService: task management
- ContextService: situational context tracking
- ClaudeAnalysisService: audit trail for Claude analysis
- 80%+ test coverage with in-memory SQLite"
```

---

### âœ… Step 3: Phase 2B Spec 3 (API Integration)
**Time:** 45 min generate + 30 min review = 75 min total

Depends on Spec 1 (fixtures) and Spec 2 (services).

**What You'll Get:**
- Updated routes: `src/api/routes/thoughts.py`, `tasks.py`
- Updated middleware: `src/api/middleware.py` (exception handlers)
- API integration tests: `tests/integration/test_api_endpoints.py`

**Run Spec 3 When Ready:**
```bash
# Copy all updated route files
# Copy updated middleware

# Verify endpoints work
pytest tests/integration/test_api_endpoints.py  # Should pass

# Check full coverage
pytest --cov=src tests/

# Test locally
python -m uvicorn src.api.main:app --reload
# Visit http://localhost:8000/docs to see all endpoints
# Try POST /api/v1/thoughts with sample data

# Commit
git add src/api/ tests/integration/test_api_endpoints.py
git commit -m "feat(api): integrate API routes with service layer

- All endpoints now call service layer
- Database operations fully functional
- Comprehensive error handling
- 80%+ test coverage across API"
```

---

## Full Execution Checklist

### Before You Start
- [ ] Phase 2A is complete and working (health check returns 200)
- [ ] Virtual environment activated: `source venv/bin/activate`
- [ ] You've reviewed all three specs
- [ ] You have the Phase2B_Spec*.md files ready to copy-paste

### Phase 2B-1 Execution
- [ ] Open Claude Sonnet
- [ ] Copy Phase2B_Spec1_AlembicAndTesting.md content
- [ ] Paste with execution prompt (see template below)
- [ ] Review generated code for quality
- [ ] Copy files to correct locations
- [ ] Run `pytest tests/` - all pass?
- [ ] Commit to git
- [ ] Verify git history looks clean

### Phase 2B-2 Execution
- [ ] Open Claude Sonnet (new chat)
- [ ] Copy Phase2B_Spec2_ServiceLayer.md content
- [ ] Paste with execution prompt
- [ ] Review generated code
- [ ] Copy service files
- [ ] Run `pytest tests/integration/` - all pass?
- [ ] Check coverage: `pytest --cov=src/services tests/`
- [ ] Commit to git

### Phase 2B-3 Execution
- [ ] Open Claude Sonnet (new chat)
- [ ] Copy Phase2B_Spec3_APIIntegration.md content
- [ ] Paste with execution prompt
- [ ] Review generated code
- [ ] Copy updated routes and middleware
- [ ] Run `pytest tests/integration/test_api_endpoints.py` - all pass?
- [ ] Check full coverage: `pytest --cov=src tests/`
- [ ] Test locally:
  - [ ] Start server: `uvicorn src.api.main:app --reload`
  - [ ] Check health: GET http://localhost:8000/api/v1/health
  - [ ] Create thought: POST http://localhost:8000/api/v1/thoughts
  - [ ] List thoughts: GET http://localhost:8000/api/v1/thoughts
- [ ] Commit to git

### Final Verification
- [ ] All tests pass: `pytest tests/`
- [ ] Coverage >80%: `pytest --cov=src tests/`
- [ ] Lint check (optional): `flake8 src/`
- [ ] Type check (optional): `mypy src/`
- [ ] API docs visible: http://localhost:8000/docs
- [ ] Git log shows clean commit history

---

## Sonnet Execution Template

Use this prompt structure when running each spec through Sonnet:

```
[Paste entire Spec content here]

---

EXECUTION INSTRUCTIONS FOR SONNET:

You are generating code for Andy's Personal AI Assistant project.

CRITICAL STANDARDS (from STANDARDS_INTEGRATION.md):
- Functions: <20 lines, max 3 parameters, single responsibility
- Testing: Comprehensive tests (80%+ coverage expected)
- Naming: Strict conventions (snake_case, DescriptiveNoun, UPPERCASE)
- Error Handling: Fail fast with clear messages
- Documentation: Docstrings on every function, explain WHY
- Quality: Readable > clever, tested > assumed

GENERATE:
- Complete, production-ready implementations (not stubs)
- Comprehensive tests (unit and integration)
- Full docstrings with examples
- Type hints throughout
- Proper error handling

OUTPUT FORMAT:
Provide files in markdown code blocks with paths:

```python
# src/services/thought_service.py
[complete file]
```

```python
# src/services/task_service.py
[complete file]
```

(etc. for all files)

Focus on:
1. Code quality that passes review
2. Tests that achieve 80%+ coverage
3. Clear, maintainable implementations
4. Proper error handling and validation

Deliver ready-to-integrate code.
```

---

## Common Issues & Solutions

### Issue: Tests failing with "module not found"
**Solution:** 
```bash
cd /Users/andy/Dev/personal-ai-assistant
pip install -e .  # Install package in editable mode
pytest tests/
```

### Issue: Alembic can't find models
**Solution:** Verify `migrations/env.py` has:
```python
from src.models.base import Base
target_metadata = Base.metadata
```

### Issue: Database locked during tests
**Solution:** Pytest is using in-memory SQLite correctly. May just need to wait or restart Python.

### Issue: Tests pass locally but seem fragile
**Solution:** Likely fixture isolation issue. Verify `conftest.py` has proper cleanup:
```python
@pytest.fixture
def db_session():
    # Create clean session
    # Yield to test
    # Cleanup/rollback after test
```

### Issue: Service tests fail with "no attribute"
**Solution:** Verify ORM models match Pydantic models. Check if fields are missing in SQLAlchemy model.

---

## Success Looks Like This

After completing all three specs:

```
$ pytest tests/ --cov=src
========================= test session starts =========================
collected 145 items

tests/unit/test_models_validation.py ...................... [ 15%]
tests/unit/test_models_enums.py ........................... [  8%]
tests/integration/test_thought_service.py ................ [ 25%]
tests/integration/test_task_service.py .................. [ 20%]
tests/integration/test_api_endpoints.py ................. [ 32%]

========================= 145 passed in 2.34s =========================

---------- coverage: platform darwin -- Python 3.12.0 -----------
src/models/          95%
src/services/        87%
src/api/             82%
------- TOTAL ...................... 88% ----------

✅ All tests passing
✅ 88% coverage (>80% target)
✅ Code ready for Phase 2C (Docker & TrueNAS)
```

And your API fully functional:

```
$ uvicorn src.api.main:app --reload

INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     API Documentation: http://localhost:8000/docs

# Can now:
# - Create thoughts via POST /api/v1/thoughts
# - List/search/update/delete thoughts
# - Create tasks from thoughts
# - Get context and analysis history
# - Full CRUD with database persistence
# - 80%+ test coverage
```

---

## What Comes After Phase 2B

**Phase 2C: Docker & TrueNAS Deployment**
- Dockerfile and docker-compose.yml
- Deployment script for TrueNAS
- ZFS backup strategy
- Environment configuration

**Phase 3: Claude Integration & iOS Shortcuts**
- Full consciousness checks (periodic reviews)
- Thought analysis and relationship discovery
- iOS Shortcuts for quick capture
- Bidirectional sync with Apple Reminders

---

## Git Workflow During Phase 2B

Each time you integrate a spec:

```bash
# 1. Copy all Sonnet-generated files to correct locations

# 2. Verify tests pass
pytest tests/

# 3. Check coverage
pytest --cov=src tests/

# 4. Stage changes
git add src/ tests/ migrations/  # (as applicable)

# 5. Commit with clear message
git commit -m "feat(spec-name): description

- What was generated
- What now works
- Coverage info"

# 6. Verify history
git log --oneline | head -10
```

---

## You're Ready!

You have three comprehensive specs written to production standards. Each one:
- Defines clear requirements
- Shows example implementations
- Includes testing strategy
- Provides success criteria
- Explains error handling

This is high-quality specification work. Running these through Sonnet should produce solid, usable code.

Next step: Start with Spec 2B-1 whenever you're ready. Open Sonnet, follow the template above, and generate the Alembic migrations + testing infrastructure.

Feel free to reach out if any spec is unclear or needs adjustment before running through Sonnet.
