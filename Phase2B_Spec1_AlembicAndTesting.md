# Phase 2B Spec 1: Alembic Migrations & Testing Foundation

**Status:** Ready for Code Generation  
**Target:** Claude Sonnet  
**Output:** Alembic migration infrastructure + test foundation  
**Complexity:** Medium  
**Dependencies:** Phase 2A (models must exist)

---

## Overview

This specification sets up proper database migration management with Alembic and establishes the testing infrastructure (fixtures, conftest, test utilities) needed for Phase 2B-2 and beyond.

**Why This Matters:**
- Migrations create audit trail of schema evolution
- Prevents "drift" between code (SQLAlchemy models) and database
- Enables rollback if something breaks
- Test fixtures ensure consistent, reproducible test data
- conftest.py provides shared utilities across all tests

---

## Part 1: Alembic Migrations Setup

### Requirements

1. **Alembic Configuration**
   - Already installed (`alembic==1.13.1` in requirements.txt)
   - `alembic.ini` exists in project root
   - Need to set up migration environment

2. **Initial Migration**
   - Auto-generate migration from SQLAlchemy models
   - Create `migrations/versions/0001_initial_schema.py`
   - Captures all tables, indexes, constraints from Phase 2A models

3. **Migration Utilities**
   - Helper scripts to apply/rollback migrations
   - Guidance on manual migration creation

4. **Database Initialization Flow**
   ```
   Local Dev:  poetry run alembic upgrade head
   Deployment: Docker startup script runs migrations
   ```

### What Alembic Will Generate

```
migrations/
├── env.py              # IMPORTANT: Configure logging, transaction handling
├── script.py.template  # Template for new migrations
├── versions/
│   └── 0001_initial_schema.py  # Create all tables from Phase 2A models
└── README
```

### Migration File Structure

The `0001_initial_schema.py` will create:

```python
# Migration that creates:
# - users table
# - thoughts table
# - thought_relationships table
# - tasks table
# - contexts table
# - claude_analysis_results table
# - api_keys table
# - audit_log table
# Plus all indexes, foreign keys, constraints
```

### Key Configuration Points

**env.py should:**
1. Load SQLAlchemy models from `src.models`
2. Set `target_metadata = Base.metadata`
3. Configure auto-migration detection
4. Handle both online and offline migrations

**alembic.ini should:**
1. Point to correct sqlalchemy.url (from .env)
2. Set proper logging level
3. Configure file_template for new migrations

---

## Part 2: Testing Infrastructure

### Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                          # Fixtures, shared utilities
├── test_models.py                       # Model validation tests
├── unit/
│   ├── __init__.py
│   ├── test_models_validation.py        # Pydantic validation
│   ├── test_models_enums.py             # Enum behavior
│   └── test_api.py                      # (placeholder for Phase 2B-3)
├── integration/
│   ├── __init__.py
│   ├── test_thought_service.py          # (Phase 2B-2)
│   ├── test_task_service.py             # (Phase 2B-2)
│   └── test_api_endpoints.py            # (Phase 2B-3)
└── fixtures/
    ├── __init__.py
    ├── users.py                         # User fixtures
    ├── thoughts.py                      # Thought fixtures
    ├── tasks.py                         # Task fixtures
    └── contexts.py                      # Context fixtures
```

### conftest.py - Shared Fixtures

```python
# Key fixtures to create:

@pytest.fixture
def db_session() -> Session:
    """Provides a clean test database session for each test."""
    # Creates temp in-memory SQLite database
    # Applies all migrations
    # Yields session
    # Cleans up after test
    
@pytest.fixture
def api_client() -> TestClient:
    """Provides FastAPI TestClient for API testing."""
    # Returns test client pointing to app
    
@pytest.fixture
def sample_user() -> User:
    """Pre-created test user."""
    
@pytest.fixture
def sample_thought(sample_user: User) -> Thought:
    """Pre-created test thought."""
    
@pytest.fixture
def api_headers() -> dict:
    """Returns auth headers with test API key."""
```

### Test Patterns to Establish

**Model Validation Tests:**
```python
def test_thought_create_valid_input(valid_thought_data):
    """Valid input creates model without error."""
    thought = ThoughtCreate(**valid_thought_data)
    assert thought.content == valid_thought_data["content"]

def test_thought_create_empty_content_raises_error():
    """Empty content raises ValueError."""
    with pytest.raises(ValidationError):
        ThoughtCreate(content="")

def test_thought_create_content_too_long_raises_error():
    """Content > 5000 chars raises ValueError."""
    with pytest.raises(ValidationError):
        ThoughtCreate(content="x" * 5001)

def test_thought_create_invalid_tags_raises_error():
    """More than 5 tags raises ValueError."""
    with pytest.raises(ValidationError):
        ThoughtCreate(tags=["a", "b", "c", "d", "e", "f"])

def test_thought_response_serializes_to_json(sample_thought):
    """Response model serializes properly to JSON."""
    data = sample_thought.model_dump(mode='json')
    assert data["id"]
    assert data["created_at"]
```

**Database Tests (will use db_session fixture):**
```python
def test_create_thought_in_database(db_session: Session, sample_user):
    """Create thought persists to database."""
    # Will implement in Phase 2B-2
    pass

def test_foreign_key_constraint_enforced(db_session: Session):
    """Invalid foreign key raises constraint error."""
    # Will implement in Phase 2B-2
    pass
```

### Test Data Factory Pattern

Create fixture builders for flexible test data:

```python
# tests/fixtures/thoughts.py

class ThoughtFactory:
    """Factory for creating test thought objects."""
    
    @staticmethod
    def create(
        content="Test thought",
        tags=None,
        status=ThoughtStatus.ACTIVE,
        **kwargs
    ) -> ThoughtCreate:
        """Create a ThoughtCreate with defaults."""
        return ThoughtCreate(
            content=content,
            tags=tags or ["test"],
            **kwargs
        )
    
    @staticmethod
    def create_batch(count: int, **kwargs) -> List[ThoughtCreate]:
        """Create multiple thoughts with variation."""
        return [
            ThoughtFactory.create(content=f"Thought {i}", **kwargs)
            for i in range(count)
        ]

# Usage in tests:
def test_list_multiple_thoughts(db_session, sample_user):
    # Create 10 test thoughts
    thoughts = ThoughtFactory.create_batch(10)
    # ... test code
```

### pytest Configuration

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
minversion = 7.0
markers =
    unit: Unit tests (no DB)
    integration: Integration tests (uses DB)
    slow: Slow tests (skip with -m "not slow")
```

**Markers Usage:**
```python
@pytest.mark.unit
def test_thought_validation():
    """Fast, no database."""
    pass

@pytest.mark.integration
def test_thought_creation_in_db(db_session):
    """Uses database, slower."""
    pass

@pytest.mark.slow
def test_claude_api_integration():
    """Very slow, skip in CI."""
    pass
```

---

## Implementation Details

### Step 1: Alembic Setup

**What Sonnet will generate:**

1. **migrations/env.py**
   - Imports Base from `src.models.base`
   - Configures migration environment
   - Sets up both offline and online migration modes
   - Handles transaction context

2. **migrations/versions/0001_initial_schema.py**
   - Auto-generated from SQLAlchemy models
   - Creates all 8 tables
   - Adds all indexes
   - Sets foreign key constraints
   - Includes upgrade() and downgrade() functions

3. **Helper scripts** (optional):
   ```bash
   # scripts/migrate.sh
   alembic upgrade head
   
   # scripts/migrate-down.sh
   alembic downgrade -1
   ```

### Step 2: Test Infrastructure

**What Sonnet will generate:**

1. **tests/conftest.py** (~150 lines)
   - Pytest configuration
   - Database fixtures (in-memory SQLite)
   - API client fixture
   - Cleanup utilities
   - Session management

2. **tests/fixtures/users.py**
   ```python
   @pytest.fixture
   def sample_user(db_session) -> UserDB:
       user = UserDB(
           id=uuid4(),
           name="Test User",
           email="test@example.com",
           created_at=utc_now(),
           updated_at=utc_now()
       )
       db_session.add(user)
       db_session.commit()
       return user
   ```

3. **tests/fixtures/thoughts.py**
   ```python
   class ThoughtFactory:
       @staticmethod
       def create(...) -> ThoughtCreate:
           # Factory for creating test thoughts
   
   @pytest.fixture
   def sample_thought(db_session, sample_user):
       # Pre-created thought in database
   ```

4. **tests/fixtures/tasks.py** (similar)

5. **tests/test_models.py** (~200 lines)
   - Validation tests for all Pydantic models
   - Edge cases (empty strings, max lengths, special chars)
   - Invalid enum values
   - Required vs optional fields

6. **pytest.ini**
   - Configuration for coverage, markers, paths

---

## Database Initialization Workflow

### Local Development
```bash
# Initial setup
alembic upgrade head  # Creates all tables from 0001_initial_schema.py

# During development
python -m uvicorn src.api.main:app --reload

# Rollback (if schema changes)
alembic downgrade -1  # Undo last migration
alembic upgrade head  # Re-apply with new migration
```

### Testing
```bash
# Runs with fixtures that:
# 1. Create temp in-memory SQLite database
# 2. Apply all migrations
# 3. Provide db_session fixture
# 4. Clean up after each test

pytest tests/
pytest tests/unit/  # Only fast unit tests
pytest tests/ -m "not slow"  # Skip slow tests
```

### TrueNAS Deployment (Phase 2C)
```bash
# Docker startup script:
alembic upgrade head  # Apply migrations
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

---

## Testing Strategy

### Phase 2B-1 Test Coverage (This Spec)

**Target: 80%+ coverage of models and validation**

1. **Unit Tests (tests/test_models.py)**
   - [ ] ThoughtCreate validation: empty, too long, invalid tags
   - [ ] ThoughtUpdate validation: optional fields, partial updates
   - [ ] ThoughtResponse serialization: model_dump(), JSON round-trip
   - [ ] TaskCreate/Update/Response validation
   - [ ] Enum validation: invalid values rejected
   - [ ] Context model: JSON serialization
   - [ ] All edge cases from spec

2. **Test Data (tests/fixtures/)**
   - [ ] UserFactory with variations
   - [ ] ThoughtFactory with variations
   - [ ] TaskFactory with variations
   - [ ] Helper functions for common test setups

3. **Fixture Tests**
   - [ ] db_session isolation: changes in one test don't affect another
   - [ ] api_client works with test app
   - [ ] Cleanup runs properly (no leftover data)

### Future Test Coverage (Phases 2B-2, 2B-3)

```
Phase 2B-1 (This): 80% coverage of models
Phase 2B-2: 80% coverage of services (thought_service, task_service)
Phase 2B-3: 80% coverage of API routes
Overall Target: 80%+ coverage across entire codebase
```

---

## Success Criteria

- [ ] Alembic migrations folder initialized and configured
- [ ] `0001_initial_schema.py` migration created and reversible
- [ ] `alembic upgrade head` creates schema successfully
- [ ] `alembic downgrade -1` removes schema cleanly
- [ ] `pytest.ini` configured with coverage requirements
- [ ] All model validation tests pass
- [ ] Test fixtures create consistent test data
- [ ] `pytest` runs full test suite with >80% coverage
- [ ] `pytest tests/unit/` runs fast (< 5 seconds)
- [ ] `pytest tests/integration/` uses fixtures properly

---

## Code Organization

Sonnet will generate/configure:

```
migrations/
├── env.py                              # NEW: Alembic environment
├── versions/
│   └── 0001_initial_schema.py          # NEW: Initial schema migration
├── alembic.ini                         # UPDATE: Configure for project
└── README

tests/
├── conftest.py                         # NEW: Fixtures and setup
├── test_models.py                      # NEW: Model validation tests
├── pytest.ini                          # NEW: Pytest configuration
├── fixtures/
│   ├── __init__.py
│   ├── users.py                        # NEW: User fixtures
│   ├── thoughts.py                     # NEW: Thought fixtures
│   └── tasks.py                        # NEW: Task fixtures
├── unit/
│   ├── test_models_validation.py       # NEW: Detailed validation tests
│   └── test_models_enums.py            # NEW: Enum behavior tests
└── integration/
    └── __init__.py                     # NEW: Placeholder for 2B-2, 2B-3

scripts/
├── migrate.sh                          # NEW: Helper scripts
└── migrate-down.sh
```

---

## Notes for Sonnet

When generating Alembic migrations and test infrastructure:

1. **Alembic env.py:**
   - Import Base from `src.models.base`
   - Set `target_metadata = Base.metadata`
   - Use `run_migrations_online()` for normal operation
   - Include proper transaction handling

2. **Initial Migration:**
   - Should be auto-generated from models
   - Include all 8 tables, indexes, foreign keys
   - Reversible (downgrade() must work)
   - Should NOT include seed data (that's later)

3. **Test Infrastructure:**
   - Use pytest, not unittest
   - In-memory SQLite for tests (`:memory:`)
   - db_session fixture uses SessionLocal from session.py
   - Teardown cleans up all tables between tests
   - Markers for unit vs integration tests

4. **Fixtures:**
   - Create factories, not hardcoded test data
   - Fixtures should be composable (task fixture depends on thought fixture)
   - Use default values from specs (5000 char limit, 5 tag max, etc.)

5. **Test Patterns:**
   - Separate files for validation vs. edge cases vs. integration
   - Clear test naming: `test_functionName_scenario_expectedBehavior`
   - Include both positive (valid) and negative (invalid) cases
   - Use pytest.raises() for exception testing

6. **Coverage Requirements:**
   - pytest --cov=src should show >=80% coverage
   - Coverage report should identify untested branches
   - Don't worry about services/routes yet (Phase 2B-2, 2B-3)

Generate production-quality migration code and test infrastructure. This will be the foundation for all future tests.
