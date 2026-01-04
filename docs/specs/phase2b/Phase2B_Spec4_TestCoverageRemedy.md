# Phase 2B Spec 4: Test Coverage Remedy

**Status:** Ready for Code Generation  
**Target:** Claude Sonnet  
**Output:** Comprehensive test suite to achieve 80%+ coverage  
**Complexity:** High  
**Priority:** BLOCKING - Must complete before Phase 2C

---

## Problem Statement

Current test coverage is **47%**, far below the required **80%** target.

### Coverage Gaps (from htmlcov report)

| File | Current | Target | Gap |
|------|---------|--------|-----|
| `thought_service.py` | 17% | 80% | -63% |
| `task_service.py` | 16% | 80% | -64% |
| `context_service.py` | 23% | 80% | -57% |
| `claude_analysis_service.py` | 29% | 80% | -51% |
| `thoughts.py` (routes) | 22% | 80% | -58% |
| `tasks.py` (routes) | 27% | 80% | -53% |
| `middleware.py` | 33% | 80% | -47% |
| `auth.py` | 42% | 80% | -38% |

### Root Cause Identified

The `sample_user` fixture creates a user with `uuid4()` (random ID), but `get_current_user_id()` returns a hardcoded UUID. This means:
- Service tests with `sample_user` work (they pass the user_id directly)
- API endpoint tests fail silently because the route uses `get_current_user_id()` which doesn't match `sample_user.id`

---

## Part 1: Fix Test Infrastructure

### 1.1 Update conftest.py - User ID Consistency

**Problem:** Two different user IDs in play
**Solution:** Centralize the test user ID

```python
# tests/conftest.py - Add at top after imports

# Centralized test user ID - matches get_current_user_id() for MVP
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
```

**Update sample_user fixture:**

```python
@pytest.fixture
def sample_user(db_session) -> UserDB:
    """
    Create the test user that matches get_current_user_id().
    
    IMPORTANT: This user ID MUST match the hardcoded ID in auth.py
    so that API endpoint tests work correctly.
    """
    from src.api.auth import get_current_user_id
    
    user = UserDB(
        id=get_current_user_id(),  # Use the same ID as auth module
        name="Test User",
        email="test@example.com",
        preferences={
            "timezone": "America/New_York",
            "max_thoughts_goal": 20
        },
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
```

### 1.2 Add Service Test Fixtures

```python
# tests/conftest.py - Add these fixtures

@pytest.fixture
def thought_service(db_session) -> "ThoughtService":
    """Provide ThoughtService instance with test database."""
    from src.services.thought_service import ThoughtService
    return ThoughtService(db_session)


@pytest.fixture
def task_service(db_session) -> "TaskService":
    """Provide TaskService instance with test database."""
    from src.services.task_service import TaskService
    return TaskService(db_session)


@pytest.fixture
def context_service(db_session) -> "ContextService":
    """Provide ContextService instance with test database."""
    from src.services.context_service import ContextService
    return ContextService(db_session)


@pytest.fixture
def claude_analysis_service(db_session) -> "ClaudeAnalysisService":
    """Provide ClaudeAnalysisService instance with test database."""
    from src.services.claude_analysis_service import ClaudeAnalysisService
    return ClaudeAnalysisService(db_session)
```

### 1.3 Add Thought Factory Fixture

```python
@pytest.fixture
def create_thought(db_session, sample_user):
    """
    Factory fixture for creating test thoughts.
    
    Usage:
        thought = create_thought(content="Test")
        thought = create_thought(content="Test", tags=["a", "b"])
    """
    from src.models.thought import ThoughtDB
    from src.models.enums import ThoughtStatus
    
    def _create_thought(
        content: str = "Test thought",
        tags: list = None,
        status: str = ThoughtStatus.ACTIVE.value,
        context: dict = None
    ) -> ThoughtDB:
        thought = ThoughtDB(
            id=str(uuid4()),
            user_id=sample_user.id,
            content=content,
            tags=tags or [],
            status=status,
            context=context,
            created_at=utc_now(),
            updated_at=utc_now()
        )
        db_session.add(thought)
        db_session.commit()
        db_session.refresh(thought)
        return thought
    
    return _create_thought


@pytest.fixture
def create_task(db_session, sample_user):
    """
    Factory fixture for creating test tasks.
    """
    from src.models.task import TaskDB
    from src.models.enums import TaskStatus, Priority
    
    def _create_task(
        title: str = "Test task",
        description: str = None,
        priority: str = Priority.MEDIUM.value,
        status: str = TaskStatus.PENDING.value,
        source_thought_id: str = None
    ) -> TaskDB:
        task = TaskDB(
            id=str(uuid4()),
            user_id=sample_user.id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            source_thought_id=source_thought_id,
            created_at=utc_now(),
            updated_at=utc_now()
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        return task
    
    return _create_task
```

---

## Part 2: ThoughtService Tests (17% → 80%)

**File:** `tests/integration/test_thought_service.py`

### Tests to Add

```python
"""
Comprehensive tests for ThoughtService.

Covers all CRUD operations, filtering, searching, pagination,
error handling, and edge cases.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from src.services.thought_service import ThoughtService
from src.services.exceptions import NotFoundError, UnauthorizedError, DatabaseError
from src.models.enums import ThoughtStatus


@pytest.mark.integration
class TestThoughtServiceCreate:
    """Test thought creation scenarios."""
    
    def test_create_thought_minimal(self, thought_service, sample_user):
        """Create thought with only required fields."""
        thought = thought_service.create_thought(
            user_id=sample_user.id,
            content="Minimal thought"
        )
        
        assert thought.id is not None
        assert thought.content == "Minimal thought"
        assert thought.tags == []
        assert thought.context is None
        assert thought.status == ThoughtStatus.ACTIVE.value
    
    def test_create_thought_full(self, thought_service, sample_user):
        """Create thought with all optional fields."""
        thought = thought_service.create_thought(
            user_id=sample_user.id,
            content="Full thought",
            tags=["test", "complete"],
            context={"app": "VSCode", "mood": "productive"}
        )
        
        assert thought.tags == ["test", "complete"]
        assert thought.context["app"] == "VSCode"
    
    def test_create_thought_strips_whitespace(self, thought_service, sample_user):
        """Content whitespace is trimmed."""
        thought = thought_service.create_thought(
            user_id=sample_user.id,
            content="  padded content  "
        )
        
        assert thought.content == "padded content"
    
    def test_create_thought_with_unicode(self, thought_service, sample_user):
        """Unicode content is preserved."""
        thought = thought_service.create_thought(
            user_id=sample_user.id,
            content="日本語テスト 🎉 émojis"
        )
        
        assert "日本語" in thought.content
        assert "🎉" in thought.content
    
    def test_create_thought_sets_timestamps(self, thought_service, sample_user):
        """Timestamps are automatically set."""
        before = datetime.now(timezone.utc)
        thought = thought_service.create_thought(
            user_id=sample_user.id,
            content="Timestamped"
        )
        after = datetime.now(timezone.utc)
        
        assert before <= thought.created_at <= after
        assert thought.created_at == thought.updated_at


@pytest.mark.integration
class TestThoughtServiceGet:
    """Test thought retrieval scenarios."""
    
    def test_get_thought_success(self, thought_service, sample_user, create_thought):
        """Retrieve existing thought by ID."""
        created = create_thought(content="Findable")
        
        found = thought_service.get_thought(
            thought_id=created.id,
            user_id=sample_user.id
        )
        
        assert found.id == created.id
        assert found.content == "Findable"
    
    def test_get_thought_not_found(self, thought_service, sample_user):
        """Non-existent ID raises NotFoundError."""
        fake_id = uuid4()
        
        with pytest.raises(NotFoundError) as exc_info:
            thought_service.get_thought(
                thought_id=fake_id,
                user_id=sample_user.id
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_get_thought_wrong_user(self, thought_service, sample_user, create_thought):
        """Cannot retrieve another user's thought."""
        created = create_thought(content="Private")
        other_user_id = uuid4()
        
        with pytest.raises(NotFoundError):
            thought_service.get_thought(
                thought_id=created.id,
                user_id=other_user_id
            )


@pytest.mark.integration
class TestThoughtServiceList:
    """Test thought listing with filters and pagination."""
    
    def test_list_thoughts_empty(self, thought_service, sample_user):
        """Empty database returns empty list."""
        thoughts, total = thought_service.list_thoughts(user_id=sample_user.id)
        
        assert thoughts == []
        assert total == 0
    
    def test_list_thoughts_basic(self, thought_service, sample_user, create_thought):
        """List returns all user's thoughts."""
        create_thought(content="One")
        create_thought(content="Two")
        create_thought(content="Three")
        
        thoughts, total = thought_service.list_thoughts(user_id=sample_user.id)
        
        assert len(thoughts) == 3
        assert total == 3
    
    def test_list_thoughts_pagination_limit(self, thought_service, sample_user, create_thought):
        """Limit parameter restricts results."""
        for i in range(10):
            create_thought(content=f"Thought {i}")
        
        thoughts, total = thought_service.list_thoughts(
            user_id=sample_user.id,
            limit=5
        )
        
        assert len(thoughts) == 5
        assert total == 10
    
    def test_list_thoughts_pagination_offset(self, thought_service, sample_user, create_thought):
        """Offset parameter skips results."""
        for i in range(10):
            create_thought(content=f"Thought {i}")
        
        thoughts, total = thought_service.list_thoughts(
            user_id=sample_user.id,
            limit=5,
            offset=5
        )
        
        assert len(thoughts) == 5
        assert total == 10
    
    def test_list_thoughts_filter_by_status(self, thought_service, sample_user, create_thought):
        """Status filter returns only matching thoughts."""
        create_thought(content="Active", status=ThoughtStatus.ACTIVE.value)
        create_thought(content="Archived", status=ThoughtStatus.ARCHIVED.value)
        
        thoughts, total = thought_service.list_thoughts(
            user_id=sample_user.id,
            status=ThoughtStatus.ACTIVE
        )
        
        assert total == 1
        assert thoughts[0].content == "Active"
    
    def test_list_thoughts_filter_by_tags(self, thought_service, sample_user, create_thought):
        """Tag filter returns thoughts with matching tags."""
        create_thought(content="Work stuff", tags=["work", "urgent"])
        create_thought(content="Personal", tags=["personal"])
        
        thoughts, total = thought_service.list_thoughts(
            user_id=sample_user.id,
            tags=["work"]
        )
        
        assert total == 1
        assert "work" in thoughts[0].tags
    
    def test_list_thoughts_sort_desc(self, thought_service, sample_user, create_thought):
        """Sort descending returns newest first."""
        first = create_thought(content="First")
        second = create_thought(content="Second")
        
        thoughts, _ = thought_service.list_thoughts(
            user_id=sample_user.id,
            sort_by="created_at",
            sort_order="desc"
        )
        
        assert thoughts[0].id == second.id
    
    def test_list_thoughts_sort_asc(self, thought_service, sample_user, create_thought):
        """Sort ascending returns oldest first."""
        first = create_thought(content="First")
        second = create_thought(content="Second")
        
        thoughts, _ = thought_service.list_thoughts(
            user_id=sample_user.id,
            sort_by="created_at",
            sort_order="asc"
        )
        
        assert thoughts[0].id == first.id
    
    def test_list_thoughts_invalid_sort_field(self, thought_service, sample_user):
        """Invalid sort field raises InvalidDataError."""
        from src.services.exceptions import InvalidDataError
        
        with pytest.raises(InvalidDataError):
            thought_service.list_thoughts(
                user_id=sample_user.id,
                sort_by="nonexistent_field"
            )


@pytest.mark.integration
class TestThoughtServiceUpdate:
    """Test thought update scenarios."""
    
    def test_update_thought_content(self, thought_service, sample_user, create_thought):
        """Update content field."""
        thought = create_thought(content="Original")
        
        updated = thought_service.update_thought(
            thought_id=thought.id,
            user_id=sample_user.id,
            content="Updated"
        )
        
        assert updated.content == "Updated"
    
    def test_update_thought_tags(self, thought_service, sample_user, create_thought):
        """Update tags field."""
        thought = create_thought(content="Test", tags=["old"])
        
        updated = thought_service.update_thought(
            thought_id=thought.id,
            user_id=sample_user.id,
            tags=["new", "updated"]
        )
        
        assert updated.tags == ["new", "updated"]
    
    def test_update_thought_status(self, thought_service, sample_user, create_thought):
        """Update status field."""
        thought = create_thought(content="Test")
        
        updated = thought_service.update_thought(
            thought_id=thought.id,
            user_id=sample_user.id,
            status=ThoughtStatus.ARCHIVED
        )
        
        assert updated.status == ThoughtStatus.ARCHIVED.value
    
    def test_update_thought_partial(self, thought_service, sample_user, create_thought):
        """Partial update preserves unchanged fields."""
        thought = create_thought(content="Original", tags=["keep"])
        
        updated = thought_service.update_thought(
            thought_id=thought.id,
            user_id=sample_user.id,
            content="Changed"
        )
        
        assert updated.content == "Changed"
        assert updated.tags == ["keep"]  # Preserved
    
    def test_update_thought_refreshes_timestamp(self, thought_service, sample_user, create_thought):
        """Update changes updated_at timestamp."""
        thought = create_thought(content="Test")
        original_updated = thought.updated_at
        
        import time
        time.sleep(0.01)  # Ensure time difference
        
        updated = thought_service.update_thought(
            thought_id=thought.id,
            user_id=sample_user.id,
            content="Changed"
        )
        
        assert updated.updated_at > original_updated
    
    def test_update_thought_not_found(self, thought_service, sample_user):
        """Update non-existent thought raises NotFoundError."""
        with pytest.raises(NotFoundError):
            thought_service.update_thought(
                thought_id=uuid4(),
                user_id=sample_user.id,
                content="Nope"
            )


@pytest.mark.integration
class TestThoughtServiceDelete:
    """Test thought deletion scenarios."""
    
    def test_delete_thought_success(self, thought_service, sample_user, create_thought):
        """Delete existing thought returns True."""
        thought = create_thought(content="Delete me")
        
        result = thought_service.delete_thought(
            thought_id=thought.id,
            user_id=sample_user.id
        )
        
        assert result is True
        
        # Verify deleted
        with pytest.raises(NotFoundError):
            thought_service.get_thought(thought.id, sample_user.id)
    
    def test_delete_thought_not_found(self, thought_service, sample_user):
        """Delete non-existent thought returns False."""
        result = thought_service.delete_thought(
            thought_id=uuid4(),
            user_id=sample_user.id
        )
        
        assert result is False
    
    def test_delete_thought_wrong_user(self, thought_service, sample_user, create_thought):
        """Delete another user's thought raises UnauthorizedError."""
        thought = create_thought(content="Private")
        
        with pytest.raises(UnauthorizedError):
            thought_service.delete_thought(
                thought_id=thought.id,
                user_id=uuid4()
            )


@pytest.mark.integration
class TestThoughtServiceSearch:
    """Test thought search functionality."""
    
    def test_search_thoughts_by_content(self, thought_service, sample_user, create_thought):
        """Search finds thoughts by content."""
        create_thought(content="Email analyzer needs work")
        create_thought(content="Guitar practice tomorrow")
        
        results, total = thought_service.search_thoughts(
            user_id=sample_user.id,
            query="email"
        )
        
        assert total == 1
        assert "email" in results[0][0].content.lower()
    
    def test_search_thoughts_by_tag(self, thought_service, sample_user, create_thought):
        """Search finds thoughts by tag."""
        create_thought(content="Something", tags=["important"])
        create_thought(content="Other", tags=["trivial"])
        
        results, total = thought_service.search_thoughts(
            user_id=sample_user.id,
            query="important"
        )
        
        assert total >= 1
    
    def test_search_thoughts_case_insensitive(self, thought_service, sample_user, create_thought):
        """Search is case insensitive."""
        create_thought(content="EMAIL analyzer")
        
        results, total = thought_service.search_thoughts(
            user_id=sample_user.id,
            query="email"
        )
        
        assert total == 1
    
    def test_search_thoughts_empty_query(self, thought_service, sample_user, create_thought):
        """Empty query returns no results."""
        create_thought(content="Something")
        
        results, total = thought_service.search_thoughts(
            user_id=sample_user.id,
            query=""
        )
        
        assert total == 0
        assert results == []
    
    def test_search_thoughts_no_matches(self, thought_service, sample_user, create_thought):
        """No matches returns empty list."""
        create_thought(content="Something")
        
        results, total = thought_service.search_thoughts(
            user_id=sample_user.id,
            query="xyznonexistent123"
        )
        
        assert total == 0
    
    def test_search_thoughts_with_relevance_score(self, thought_service, sample_user, create_thought):
        """Search results include relevance scores."""
        create_thought(content="Test search relevance")
        
        results, total = thought_service.search_thoughts(
            user_id=sample_user.id,
            query="test"
        )
        
        assert len(results) == 1
        thought, score = results[0]
        assert score > 0
    
    def test_search_thoughts_pagination(self, thought_service, sample_user, create_thought):
        """Search supports pagination."""
        for i in range(10):
            create_thought(content=f"Test thought {i}")
        
        results, total = thought_service.search_thoughts(
            user_id=sample_user.id,
            query="test",
            limit=5,
            offset=0
        )
        
        assert len(results) == 5
        assert total == 10
```

---

## Part 3: TaskService Tests (16% → 80%)

**File:** `tests/integration/test_task_service.py`

### Tests to Add

```python
"""
Comprehensive tests for TaskService.

Covers all CRUD operations, completion tracking, filtering,
and relationship to source thoughts.
"""

import pytest
from uuid import uuid4
from datetime import date, timedelta

from src.services.task_service import TaskService
from src.services.exceptions import NotFoundError, UnauthorizedError, InvalidDataError
from src.models.enums import TaskStatus, Priority


@pytest.mark.integration
class TestTaskServiceCreate:
    """Test task creation scenarios."""
    
    def test_create_task_minimal(self, task_service, sample_user):
        """Create task with only title."""
        task = task_service.create_task(
            user_id=sample_user.id,
            title="Minimal task"
        )
        
        assert task.id is not None
        assert task.title == "Minimal task"
        assert task.status == TaskStatus.PENDING.value
        assert task.priority == Priority.MEDIUM.value
    
    def test_create_task_full(self, task_service, sample_user):
        """Create task with all fields."""
        due = date.today() + timedelta(days=7)
        
        task = task_service.create_task(
            user_id=sample_user.id,
            title="Full task",
            description="Detailed description",
            priority=Priority.HIGH,
            due_date=due,
            estimated_effort_minutes=120
        )
        
        assert task.description == "Detailed description"
        assert task.priority == Priority.HIGH.value
        assert task.due_date == due
        assert task.estimated_effort_minutes == 120
    
    def test_create_task_from_thought(self, task_service, sample_user, create_thought):
        """Create task linked to source thought."""
        thought = create_thought(content="Spawns task")
        
        task = task_service.create_task(
            user_id=sample_user.id,
            title="From thought",
            source_thought_id=thought.id
        )
        
        assert task.source_thought_id == thought.id
    
    def test_create_task_invalid_thought_id(self, task_service, sample_user):
        """Invalid source_thought_id raises error."""
        # This may raise NotFoundError or DatabaseError depending on FK constraint
        with pytest.raises((NotFoundError, Exception)):
            task_service.create_task(
                user_id=sample_user.id,
                title="Bad reference",
                source_thought_id=uuid4()
            )


@pytest.mark.integration
class TestTaskServiceGet:
    """Test task retrieval scenarios."""
    
    def test_get_task_success(self, task_service, sample_user, create_task):
        """Retrieve existing task."""
        created = create_task(title="Findable")
        
        found = task_service.get_task(
            task_id=created.id,
            user_id=sample_user.id
        )
        
        assert found.id == created.id
    
    def test_get_task_not_found(self, task_service, sample_user):
        """Non-existent task raises NotFoundError."""
        with pytest.raises(NotFoundError):
            task_service.get_task(
                task_id=uuid4(),
                user_id=sample_user.id
            )
    
    def test_get_task_wrong_user(self, task_service, sample_user, create_task):
        """Cannot get another user's task."""
        task = create_task(title="Private")
        
        with pytest.raises(NotFoundError):
            task_service.get_task(
                task_id=task.id,
                user_id=uuid4()
            )


@pytest.mark.integration
class TestTaskServiceList:
    """Test task listing with filters."""
    
    def test_list_tasks_empty(self, task_service, sample_user):
        """Empty database returns empty list."""
        tasks, total = task_service.list_tasks(user_id=sample_user.id)
        
        assert tasks == []
        assert total == 0
    
    def test_list_tasks_basic(self, task_service, sample_user, create_task):
        """List returns all user's tasks."""
        create_task(title="One")
        create_task(title="Two")
        
        tasks, total = task_service.list_tasks(user_id=sample_user.id)
        
        assert len(tasks) == 2
        assert total == 2
    
    def test_list_tasks_filter_by_status(self, task_service, sample_user, create_task):
        """Filter by status."""
        create_task(title="Pending", status=TaskStatus.PENDING.value)
        create_task(title="Done", status=TaskStatus.DONE.value)
        
        tasks, total = task_service.list_tasks(
            user_id=sample_user.id,
            status=TaskStatus.PENDING
        )
        
        assert total == 1
        assert tasks[0].title == "Pending"
    
    def test_list_tasks_filter_by_priority(self, task_service, sample_user, create_task):
        """Filter by priority."""
        create_task(title="High", priority=Priority.HIGH.value)
        create_task(title="Low", priority=Priority.LOW.value)
        
        tasks, total = task_service.list_tasks(
            user_id=sample_user.id,
            priority=Priority.HIGH
        )
        
        assert total == 1
        assert tasks[0].title == "High"
    
    def test_list_tasks_filter_by_due_date_range(self, task_service, sample_user, create_task):
        """Filter by due date range."""
        today = date.today()
        
        # Task due today
        from src.models.task import TaskDB
        task = TaskDB(
            id=str(uuid4()),
            user_id=sample_user.id,
            title="Due today",
            priority=Priority.MEDIUM.value,
            status=TaskStatus.PENDING.value,
            due_date=today,
            created_at=task_service.db.execute("SELECT datetime('now')").fetchone()[0],
            updated_at=task_service.db.execute("SELECT datetime('now')").fetchone()[0]
        )
        # Note: This is a bit awkward - better to use the service method
        
        # Using service method instead
        task = task_service.create_task(
            user_id=sample_user.id,
            title="Due soon",
            due_date=today + timedelta(days=3)
        )
        task2 = task_service.create_task(
            user_id=sample_user.id,
            title="Due later",
            due_date=today + timedelta(days=30)
        )
        
        tasks, total = task_service.list_tasks(
            user_id=sample_user.id,
            due_date_from=today,
            due_date_to=today + timedelta(days=7)
        )
        
        assert total == 1
        assert tasks[0].title == "Due soon"
    
    def test_list_tasks_pagination(self, task_service, sample_user, create_task):
        """Pagination works correctly."""
        for i in range(10):
            create_task(title=f"Task {i}")
        
        tasks, total = task_service.list_tasks(
            user_id=sample_user.id,
            limit=5,
            offset=0
        )
        
        assert len(tasks) == 5
        assert total == 10


@pytest.mark.integration
class TestTaskServiceUpdate:
    """Test task update scenarios."""
    
    def test_update_task_title(self, task_service, sample_user, create_task):
        """Update title field."""
        task = create_task(title="Original")
        
        updated = task_service.update_task(
            task_id=task.id,
            user_id=sample_user.id,
            title="Updated"
        )
        
        assert updated.title == "Updated"
    
    def test_update_task_priority(self, task_service, sample_user, create_task):
        """Update priority field."""
        task = create_task(title="Test", priority=Priority.LOW.value)
        
        updated = task_service.update_task(
            task_id=task.id,
            user_id=sample_user.id,
            priority=Priority.CRITICAL
        )
        
        assert updated.priority == Priority.CRITICAL.value
    
    def test_update_task_partial(self, task_service, sample_user, create_task):
        """Partial update preserves other fields."""
        task = create_task(title="Keep", description="Also keep")
        
        updated = task_service.update_task(
            task_id=task.id,
            user_id=sample_user.id,
            title="Changed"
        )
        
        assert updated.title == "Changed"
        assert updated.description == "Also keep"


@pytest.mark.integration
class TestTaskServiceComplete:
    """Test task completion functionality."""
    
    def test_complete_task_success(self, task_service, sample_user, create_task):
        """Complete task sets status and timestamp."""
        task = create_task(title="To complete")
        
        completed = task_service.complete_task(
            task_id=task.id,
            user_id=sample_user.id
        )
        
        assert completed.status == TaskStatus.DONE.value
        assert completed.completed_at is not None
    
    def test_complete_task_not_found(self, task_service, sample_user):
        """Complete non-existent task raises NotFoundError."""
        with pytest.raises(NotFoundError):
            task_service.complete_task(
                task_id=uuid4(),
                user_id=sample_user.id
            )


@pytest.mark.integration
class TestTaskServiceDelete:
    """Test task deletion scenarios."""
    
    def test_delete_task_success(self, task_service, sample_user, create_task):
        """Delete existing task."""
        task = create_task(title="Delete me")
        
        result = task_service.delete_task(
            task_id=task.id,
            user_id=sample_user.id
        )
        
        assert result is True
    
    def test_delete_task_not_found(self, task_service, sample_user):
        """Delete non-existent task returns False."""
        result = task_service.delete_task(
            task_id=uuid4(),
            user_id=sample_user.id
        )
        
        assert result is False
    
    def test_delete_task_wrong_user(self, task_service, sample_user, create_task):
        """Delete another user's task raises UnauthorizedError."""
        task = create_task(title="Private")
        
        with pytest.raises(UnauthorizedError):
            task_service.delete_task(
                task_id=task.id,
                user_id=uuid4()
            )


@pytest.mark.integration
class TestTaskServiceGetForThought:
    """Test getting tasks linked to a thought."""
    
    def test_get_tasks_for_thought(self, task_service, sample_user, create_thought):
        """Get all tasks created from a thought."""
        thought = create_thought(content="Source")
        
        task_service.create_task(
            user_id=sample_user.id,
            title="Task 1",
            source_thought_id=thought.id
        )
        task_service.create_task(
            user_id=sample_user.id,
            title="Task 2",
            source_thought_id=thought.id
        )
        
        tasks = task_service.get_tasks_for_thought(
            thought_id=thought.id,
            user_id=sample_user.id
        )
        
        assert len(tasks) == 2
    
    def test_get_tasks_for_thought_none(self, task_service, sample_user, create_thought):
        """No tasks for thought returns empty list."""
        thought = create_thought(content="No tasks")
        
        tasks = task_service.get_tasks_for_thought(
            thought_id=thought.id,
            user_id=sample_user.id
        )
        
        assert tasks == []
```

---

## Part 4: API Endpoint Tests

**File:** `tests/integration/test_api_endpoints.py`

Enhance existing tests to ensure all code paths are covered:

```python
"""
Comprehensive API endpoint integration tests.

Tests the full request/response cycle for all endpoints.
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_returns_200(self, api_client):
        """Health endpoint returns 200 OK."""
        response = api_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"


@pytest.mark.integration  
class TestThoughtEndpointsErrors:
    """Test error handling for thought endpoints."""
    
    def test_create_thought_empty_content_422(self, api_client, auth_headers):
        """Empty content returns 422."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_create_thought_too_long_422(self, api_client, auth_headers):
        """Content over 5000 chars returns 422."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": "x" * 5001},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_create_thought_too_many_tags_422(self, api_client, auth_headers):
        """More than 5 tags returns 422."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={
                "content": "Test",
                "tags": ["a", "b", "c", "d", "e", "f"]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_get_thought_invalid_uuid_422(self, api_client, auth_headers):
        """Invalid UUID format returns 422."""
        response = api_client.get(
            "/api/v1/thoughts/not-a-uuid",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_list_thoughts_invalid_limit_422(self, api_client, auth_headers):
        """Limit > 100 returns 422."""
        response = api_client.get(
            "/api/v1/thoughts?limit=500",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_search_missing_query_422(self, api_client, auth_headers):
        """Search without q parameter returns 422."""
        response = api_client.get(
            "/api/v1/thoughts/search",
            headers=auth_headers
        )
        
        assert response.status_code == 422


@pytest.mark.integration
class TestTaskEndpoints:
    """Test task endpoint functionality."""
    
    def test_create_task_success(self, api_client, auth_headers):
        """Create task returns 201."""
        response = api_client.post(
            "/api/v1/tasks",
            json={"title": "Test task"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"] == "Test task"
        assert data["id"] is not None
    
    def test_create_task_with_priority(self, api_client, auth_headers):
        """Create task with priority."""
        response = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Important",
                "priority": "high"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["priority"] == "high"
    
    def test_list_tasks(self, api_client, auth_headers):
        """List tasks returns array."""
        # Create a task first
        api_client.post(
            "/api/v1/tasks",
            json={"title": "Listed"},
            headers=auth_headers
        )
        
        response = api_client.get(
            "/api/v1/tasks",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "tasks" in data
        assert "pagination" in data
    
    def test_get_task(self, api_client, auth_headers):
        """Get single task by ID."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Findable"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        response = api_client.get(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["id"] == task_id
    
    def test_update_task(self, api_client, auth_headers):
        """Update task."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Original"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        response = api_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"title": "Updated"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "Updated"
    
    def test_complete_task(self, api_client, auth_headers):
        """Complete task endpoint."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "To complete"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        response = api_client.post(
            f"/api/v1/tasks/{task_id}/complete",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "done"
        assert data["completed_at"] is not None
    
    def test_delete_task(self, api_client, auth_headers):
        """Delete task returns 204."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Delete me"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        response = api_client.delete(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    def test_get_task_not_found(self, api_client, auth_headers):
        """Get non-existent task returns 404."""
        response = api_client.get(
            f"/api/v1/tasks/{uuid4()}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.integration
class TestAuthenticationRequired:
    """Test that authentication is required."""
    
    def test_thoughts_no_auth_401(self, api_client):
        """Thoughts endpoint without auth returns 401."""
        # Note: api_client fixture overrides auth, so we need raw client
        from fastapi.testclient import TestClient
        from src.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/thoughts")
            assert response.status_code == 401
    
    def test_tasks_no_auth_401(self, api_client):
        """Tasks endpoint without auth returns 401."""
        from fastapi.testclient import TestClient
        from src.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/tasks")
            assert response.status_code == 401
```

---

## Part 5: Run Tests and Verify Coverage

After implementing all tests, run:

```bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Check coverage meets threshold
pytest tests/ --cov=src --cov-fail-under=80
```

---

## Success Criteria

- [ ] All existing tests still pass
- [ ] Overall coverage >= 80%
- [ ] `thought_service.py` coverage >= 80%
- [ ] `task_service.py` coverage >= 80%
- [ ] `thoughts.py` (routes) coverage >= 80%
- [ ] `tasks.py` (routes) coverage >= 80%
- [ ] No fixture user ID mismatches
- [ ] All edge cases covered (validation, errors, authorization)

---

## Notes for Sonnet

When generating these tests:

1. **Fix conftest.py FIRST** - The user ID mismatch will cause silent test failures
2. **Use factory fixtures** - `create_thought()` and `create_task()` for flexibility
3. **Test error paths** - NotFoundError, UnauthorizedError, ValidationError
4. **Test edge cases** - Empty strings, max lengths, unicode, boundaries
5. **Test authorization** - Wrong user cannot access/modify resources
6. **Use pytest.raises()** - For expected exceptions
7. **Keep tests independent** - Each test should work in isolation
8. **Clear test names** - `test_action_scenario_expected_result`

Generate production-quality tests that will catch regressions and verify all code paths.
