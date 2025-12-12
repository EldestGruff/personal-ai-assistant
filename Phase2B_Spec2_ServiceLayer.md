# Phase 2B Spec 2: Database Service Layer

**Status:** Ready for Code Generation (After 2B-1)  
**Target:** Claude Sonnet  
**Output:** Service classes for database operations  
**Complexity:** High  
**Dependencies:** Phase 2B-1 (Alembic + tests), Phase 2A (models)

---

## Overview

This specification defines the service layer that handles all database operations. Services contain business logic and are used by API routes. This layer exists between the API (routes) and the database (SQLAlchemy models).

**Architecture:**
```
API Route (HTTP request)
    ↓
Service (business logic + DB queries)
    ↓
SQLAlchemy ORM (database access)
    ↓
SQLite Database
```

**Why This Separation:**
- API routes remain thin and testable
- Database logic is centralized and reusable
- Easy to mock services in tests
- Business logic independent of HTTP

---

## Part 1: ThoughtService

### Purpose
All CRUD operations for thoughts: create, read, update, delete, search, list.

### Requirements

**Create Thought**
```python
async def create_thought(
    user_id: UUID,
    content: str,
    tags: List[str] = None,
    context: Dict[str, Any] = None
) -> ThoughtDB:
    """
    Create and persist a new thought.
    
    Returns:
        ThoughtDB object with id, timestamps
        
    Raises:
        ValueError: If content empty or invalid
        DatabaseError: If database write fails
    """
```

**Read Single Thought**
```python
async def get_thought(
    thought_id: UUID,
    user_id: UUID  # Verify ownership
) -> ThoughtDB:
    """
    Retrieve a single thought.
    
    Raises:
        ThoughtNotFoundError: If thought doesn't exist or user doesn't own it
    """
```

**List Thoughts**
```python
async def list_thoughts(
    user_id: UUID,
    status: ThoughtStatus = None,  # Filter by status
    tags: List[str] = None,         # Filter by tags (OR logic)
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[ThoughtDB], int]:
    """
    List user's thoughts with filtering and pagination.
    
    Returns:
        (list_of_thoughts, total_count)
    """
```

**Update Thought**
```python
async def update_thought(
    thought_id: UUID,
    user_id: UUID,
    **kwargs  # content, tags, status, context
) -> ThoughtDB:
    """
    Update an existing thought.
    
    Only update provided fields. Automatically sets updated_at.
    
    Raises:
        ThoughtNotFoundError: If thought doesn't exist
        ValueError: If update values invalid
    """
```

**Delete Thought**
```python
async def delete_thought(
    thought_id: UUID,
    user_id: UUID
) -> bool:
    """
    Delete a thought (hard delete).
    
    Returns:
        True if deleted, False if not found
    """
```

**Search Thoughts**
```python
async def search_thoughts(
    user_id: UUID,
    query: str,
    fields: List[str] = None,  # Default: ["content", "tags"]
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Tuple[ThoughtDB, float]], int]:
    """
    Full-text search on thought content and tags.
    
    Returns:
        ([(thought, relevance_score), ...], total_count)
    """
```

**Get Related Thoughts**
```python
async def get_related_thoughts(
    thought_id: UUID,
    user_id: UUID,
    limit: int = 10
) -> List[ThoughtDB]:
    """
    Get thoughts related to a specific thought.
    
    Uses thought_relationships table.
    Sorted by confidence descending.
    """
```

**Add Thought Relationship** (for Claude to call)
```python
async def add_thought_relationship(
    source_thought_id: UUID,
    related_thought_id: UUID,
    user_id: UUID,
    relationship_type: str = "similar",
    confidence: float = 0.8,
    discovered_by: str = "claude"
) -> bool:
    """Add link between two thoughts (discovered by Claude analysis)."""
```

### Implementation Notes

**Query Patterns:**

```python
# List with filters and pagination
query = db_session.query(ThoughtDB).filter(
    ThoughtDB.user_id == user_id
)

if status:
    query = query.filter(ThoughtDB.status == status.value)

if tags:
    # Tags are JSON array, check if any tag matches
    for tag in tags:
        query = query.filter(
            ThoughtDB.tags.contains([tag])  # SQLAlchemy JSON contains
        )

query = query.order_by(
    getattr(ThoughtDB, sort_by).desc() 
    if sort_order == "desc" 
    else getattr(ThoughtDB, sort_by).asc()
)

total = query.count()
results = query.offset(offset).limit(limit).all()
```

**Search Implementation:**

SQLite doesn't have native FTS5 by default. Use LIKE for MVP:

```python
# Simple LIKE search (case-insensitive)
query = db_session.query(ThoughtDB).filter(
    or_(
        ThoughtDB.content.ilike(f"%{query_str}%"),
        ThoughtDB.tags.contains([query_str])  # Tag exact match
    )
)
# Score by position: earlier match = higher relevance
# (Can enhance with FTS5 later if needed)
```

---

## Part 2: TaskService

### Purpose
All CRUD operations for tasks. Tasks are created from thoughts but can also be standalone.

### Requirements

**Create Task**
```python
async def create_task(
    user_id: UUID,
    title: str,
    description: str = None,
    source_thought_id: UUID = None,
    priority: Priority = Priority.MEDIUM,
    due_date: date = None,
    estimated_effort_minutes: int = None
) -> TaskDB:
    """Create a new task."""
```

**Read Single Task**
```python
async def get_task(
    task_id: UUID,
    user_id: UUID
) -> TaskDB:
    """Retrieve a task (with ownership check)."""
```

**List Tasks**
```python
async def list_tasks(
    user_id: UUID,
    status: TaskStatus = None,
    priority: Priority = None,
    due_date_from: date = None,
    due_date_to: date = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[TaskDB], int]:
    """List tasks with filtering (active tasks first by default)."""
```

**Update Task**
```python
async def update_task(
    task_id: UUID,
    user_id: UUID,
    **kwargs  # title, description, status, priority, due_date, etc.
) -> TaskDB:
    """Update a task."""
```

**Delete Task**
```python
async def delete_task(
    task_id: UUID,
    user_id: UUID
) -> bool:
    """Delete a task."""
```

**Mark Task Complete**
```python
async def complete_task(
    task_id: UUID,
    user_id: UUID
) -> TaskDB:
    """
    Mark task as done and set completed_at timestamp.
    
    Sets:
    - status = TaskStatus.DONE
    - completed_at = utc_now()
    """
```

**Get Tasks for Thought**
```python
async def get_tasks_for_thought(
    thought_id: UUID,
    user_id: UUID
) -> List[TaskDB]:
    """Get all tasks created from a specific thought."""
```

### Implementation Notes

Similar patterns to ThoughtService:
- Filter queries by user_id (ownership)
- Pagination with limit/offset
- Sorting by specified fields
- Raise NotFoundError if not found or wrong owner

---

## Part 3: ContextService

### Purpose
Track situational context when thoughts are captured.

### Requirements

**Create Context Session**
```python
async def start_context_session(
    user_id: UUID,
    current_activity: str,
    active_app: str = None,
    location: str = None,
    time_of_day: TimeOfDay = None,
    energy_level: EnergyLevel = None,
    focus_state: FocusState = None,
    notes: str = None
) -> str:  # session_id
    """
    Start a new context session.
    
    Returns:
        session_id (string, not UUID)
    """
```

**End Context Session**
```python
async def end_context_session(
    session_id: str,
    user_id: UUID
) -> ContextDB:
    """Mark context session as ended."""
```

**Get Current Context**
```python
async def get_current_context(
    user_id: UUID
) -> Optional[ContextDB]:
    """Get the active (not-ended) context session."""
```

**Get Context History**
```python
async def get_context_history(
    user_id: UUID,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[ContextDB], int]:
    """Retrieve past context sessions."""
```

---

## Part 4: ClaudeAnalysisService

### Purpose
Store records of Claude's analysis for audit trail and future context.

### Requirements

**Record Analysis**
```python
async def record_analysis(
    user_id: UUID,
    analysis_type: AnalysisType,
    thought_id: UUID = None,
    summary: str = None,
    themes: List[str] = None,
    suggested_action: str = None,
    confidence: float = 0.8,
    tokens_used: int = 0,
    raw_response: Dict[str, Any] = None
) -> ClaudeAnalysisResultDB:
    """Record what Claude analyzed and what it found."""
```

**Get Analysis History**
```python
async def get_analysis_history(
    user_id: UUID,
    analysis_type: AnalysisType = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[ClaudeAnalysisResultDB], int]:
    """Retrieve past analyses for audit/context."""
```

**Get Analyses for Thought**
```python
async def get_analyses_for_thought(
    thought_id: UUID,
    user_id: UUID
) -> List[ClaudeAnalysisResultDB]:
    """Get all analyses that touched a specific thought."""
```

---

## Part 5: Service Error Handling

### Custom Exceptions

Create in `src/services/exceptions.py`:

```python
class ServiceError(Exception):
    """Base exception for service layer."""
    pass

class NotFoundError(ServiceError):
    """Resource not found."""
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(
            f"{resource_type} with ID '{resource_id}' not found."
        )

class UnauthorizedError(ServiceError):
    """User doesn't own resource."""
    def __init__(self, resource_type: str, user_id: str):
        super().__init__(
            f"User '{user_id}' not authorized to access this {resource_type}."
        )

class InvalidDataError(ServiceError):
    """Data validation failed."""
    def __init__(self, message: str, details: Dict = None):
        self.details = details or {}
        super().__init__(message)

class DatabaseError(ServiceError):
    """Database operation failed."""
    pass
```

### Error Handling Pattern

```python
@handle_service_errors
async def create_thought(user_id: UUID, **kwargs) -> ThoughtDB:
    """Decorated with error handler."""
    # If any exception occurs, handler catches and logs
    # Converts to appropriate response for API layer
    
def handle_service_errors(func):
    """Decorator that wraps service methods with error handling."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            raise DatabaseError(str(e))
        except ValueError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            raise InvalidDataError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise ServiceError(f"Unexpected error: {str(e)}")
    return wrapper
```

---

## Database Operations Examples

### Example 1: Create Thought with Tags

```python
async def create_thought(
    user_id: UUID,
    content: str,
    tags: List[str] = None,
    context: Dict[str, Any] = None
) -> ThoughtDB:
    """
    Create thought.
    
    1. Validate input (handled by Pydantic in API)
    2. Create ThoughtDB object
    3. Add to session
    4. Commit
    5. Return
    """
    thought = ThoughtDB(
        id=str(uuid4()),
        user_id=str(user_id),
        content=content,
        tags=tags or [],
        status=ThoughtStatus.ACTIVE.value,
        context=context,
        created_at=utc_now(),
        updated_at=utc_now()
    )
    
    db_session.add(thought)
    db_session.commit()
    db_session.refresh(thought)  # Get auto-generated fields
    
    return thought
```

### Example 2: List with Filters

```python
async def list_thoughts(
    user_id: UUID,
    status: ThoughtStatus = None,
    tags: List[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[ThoughtDB], int]:
    """
    List thoughts with optional filters.
    
    Returns (list, total_count) for pagination.
    """
    query = db_session.query(ThoughtDB).filter(
        ThoughtDB.user_id == str(user_id)
    )
    
    # Filter by status if provided
    if status:
        query = query.filter(
            ThoughtDB.status == status.value
        )
    
    # Filter by tags if provided (any tag matches)
    if tags:
        for tag in tags:
            query = query.filter(
                ThoughtDB.tags.contains([tag])
            )
    
    # Get total before pagination
    total = query.count()
    
    # Sort
    sort_column = getattr(ThoughtDB, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Paginate
    results = query.offset(offset).limit(limit).all()
    
    return results, total
```

### Example 3: Search with Relevance

```python
async def search_thoughts(
    user_id: UUID,
    query: str,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Tuple[ThoughtDB, float]], int]:
    """
    Search thoughts by content and tags.
    
    Returns ([(thought, relevance_score), ...], total)
    """
    # Simple LIKE search
    search_pattern = f"%{query}%"
    
    db_query = db_session.query(ThoughtDB).filter(
        and_(
            ThoughtDB.user_id == str(user_id),
            or_(
                ThoughtDB.content.ilike(search_pattern),
                ThoughtDB.tags.contains([query])
            )
        )
    )
    
    total = db_query.count()
    results = db_query.offset(offset).limit(limit).all()
    
    # Score relevance (simple: content match > tag match)
    scored_results = []
    for thought in results:
        score = 1.0
        if query.lower() in thought.content.lower():
            score += 0.5  # Content match scores higher
        scored_results.append((thought, score))
    
    # Sort by score
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    return scored_results, total
```

---

## Testing Strategy

**Phase 2B-2 Test Coverage: 80%+ of service layer**

### Unit Tests (Mocked Database)

```python
# tests/unit/test_thought_service.py

@pytest.mark.unit
class TestThoughtService:
    """Test service layer with mocked DB."""
    
    def test_create_thought_returns_valid_object(self):
        """Create returns ThoughtDB with ID and timestamps."""
        # Mock db_session
        # Call service.create_thought()
        # Assert returned object has id, created_at, updated_at
        pass
    
    def test_create_thought_with_empty_content_raises_error(self):
        """Empty content rejected."""
        pass
    
    def test_list_thoughts_filters_by_status(self):
        """Status filter applied correctly."""
        pass
    
    def test_list_thoughts_paginates_correctly(self):
        """Offset/limit work as expected."""
        pass
    
    def test_update_thought_only_updates_provided_fields(self):
        """Partial updates don't null out other fields."""
        pass
    
    def test_search_thoughts_returns_relevance_score(self):
        """Search results include relevance."""
        pass
```

### Integration Tests (Real Database)

```python
# tests/integration/test_thought_service.py

@pytest.mark.integration
class TestThoughtServiceIntegration:
    """Test with real in-memory database."""
    
    def test_create_and_retrieve_thought(self, db_session, sample_user):
        """Round-trip: create, retrieve, verify."""
        # Create via service
        # Retrieve via service
        # Assert data matches
        pass
    
    def test_foreign_key_constraint_enforced(self, db_session):
        """Invalid user_id raises constraint error."""
        pass
    
    def test_thought_relationships_cascade_delete(self, db_session):
        """Deleting thought also deletes relationships."""
        pass
```

---

## Service Dependency Injection

### How API Routes Will Use Services

```python
# In API route (Phase 2B-3):
from src.services.thought_service import ThoughtService
from src.database.session import get_db

@router.post("/thoughts", status_code=201)
async def create_thought(
    thought: ThoughtCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Create thought by calling service."""
    user_id = get_current_user_id()
    
    service = ThoughtService(db)
    result = await service.create_thought(
        user_id=user_id,
        content=thought.content,
        tags=thought.tags,
        context=thought.context
    )
    
    return APIResponse.success(
        data=result.to_response().model_dump(mode='json'),
        status_code=status.HTTP_201_CREATED
    )
```

**Service initialization:**
```python
# src/services/thought_service.py

class ThoughtService:
    """Service for thought operations."""
    
    def __init__(self, db_session: Session):
        """Inject database session."""
        self.db = db_session
    
    async def create_thought(self, ...) -> ThoughtDB:
        """Create a thought."""
        # Use self.db for all database operations
```

---

## Success Criteria

- [ ] All service methods implement requested functionality
- [ ] Database queries return correct results
- [ ] Filtering and pagination work correctly
- [ ] Search returns relevance scores
- [ ] Foreign key constraints enforced
- [ ] Ownership checks prevent unauthorized access (user_id verification)
- [ ] Error handling is comprehensive
- [ ] Service tests achieve 80%+ coverage
- [ ] Tests pass with in-memory SQLite database
- [ ] Services ready for API layer integration (Phase 2B-3)

---

## Code Organization

Sonnet will generate:

```
src/services/
├── __init__.py
├── exceptions.py                # Custom exceptions
├── thought_service.py           # ThoughtService class (~300 lines)
├── task_service.py              # TaskService class (~200 lines)
├── context_service.py           # ContextService class (~150 lines)
└── claude_analysis_service.py   # ClaudeAnalysisService (~150 lines)

tests/integration/
├── test_thought_service.py      # Service integration tests
├── test_task_service.py
├── test_context_service.py
└── conftest.py                  # Shared fixtures (if needed)
```

---

## Notes for Sonnet

When generating service layer:

1. **Database Access:**
   - Use SQLAlchemy query API (not raw SQL)
   - Handle None/optional values carefully
   - Use `.value` for enum conversion to string for DB

2. **Async/Await:**
   - Mark all methods as `async def`
   - Use `await` even though SQLAlchemy is synchronous (prepare for async later)
   - Or just use sync methods (db_session.add, db_session.commit)
   - Decide on async vs sync and be consistent

3. **Error Handling:**
   - Catch SQLAlchemyError and convert to ServiceError
   - Verify user_id matches resource owner (no cross-user access)
   - Clear error messages

4. **Testing:**
   - Unit tests mock the db_session
   - Integration tests use fixture with real in-memory SQLite
   - Test both happy path and error cases
   - Include boundary tests (max/min values)

5. **Documentation:**
   - Docstring for every method
   - Include example usage
   - Document all exceptions that can be raised
   - Explain complex queries

Generate production-ready service layer. This is the business logic heart of the application.
