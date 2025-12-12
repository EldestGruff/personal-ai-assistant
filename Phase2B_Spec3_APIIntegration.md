# Phase 2B Spec 3: API → Service Integration

**Status:** Ready for Code Generation (After 2B-2)  
**Target:** Claude Sonnet  
**Output:** Updated API routes that call services  
**Complexity:** Medium  
**Dependencies:** Phase 2B-1 (Alembic), Phase 2B-2 (services), Phase 2A (models/API skeleton)

---

## Overview

This specification updates the API routes (from Phase 2A) to integrate with the service layer (from Phase 2B-2). Routes transform HTTP requests → service calls → responses.

**Updated Request Flow:**
```
HTTP Request
    ↓
FastAPI Route Handler
    ↓
Parse/Validate with Pydantic
    ↓
Call Service Layer
    ↓
Handle Errors/Exceptions
    ↓
Convert to APIResponse
    ↓
HTTP Response
```

**What's Changing:**
- Routes no longer have `# TODO: Implement` stubs
- Routes now call service methods
- Error handling converts service exceptions to API responses
- All endpoints functional (except Claude-specific ones, which are Phase 3)

---

## Part 1: Thoughts Routes Integration

### Updated POST /api/v1/thoughts

**Before:**
```python
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_thought(
    thought: ThoughtCreate,
    api_key: str = Depends(verify_api_key)
):
    """Capture a new thought."""
    user_id = get_current_user_id()
    
    # TODO: Actually save to database when DB layer is ready
    thought_response = ThoughtResponse(...)
    
    return APIResponse.success(...)
```

**After:**
```python
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_thought(
    thought: ThoughtCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Capture a new thought.
    
    Takes thought content, tags, context and persists to database.
    Returns created thought with generated ID and timestamps.
    
    Args:
        thought: Thought data (content, tags, context)
        
    Returns:
        201 Created: ThoughtResponse with id, created_at, updated_at
        400 Bad Request: If content invalid
        401 Unauthorized: If API key invalid
    """
    try:
        user_id = get_current_user_id()
        
        service = ThoughtService(db)
        thought_db = await service.create_thought(
            user_id=UUID(user_id),
            content=thought.content,
            tags=thought.tags,
            context=thought.context
        )
        
        return APIResponse.success(
            data=thought_db.to_response().model_dump(mode='json'),
            status_code=status.HTTP_201_CREATED
        )
        
    except InvalidDataError as e:
        raise InvalidContentError(str(e))
    except DatabaseError as e:
        logger.error(f"Database error creating thought: {e}")
        raise APIError(
            code="DATABASE_ERROR",
            message="Failed to save thought to database",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### Updated GET /api/v1/thoughts (List)

**After:**
```python
@router.get("", status_code=status.HTTP_200_OK)
async def list_thoughts(
    status_filter: Optional[ThoughtStatus] = Query(None, alias="status"),
    tags: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    List user's thoughts with optional filtering and pagination.
    
    Query Parameters:
        status: Filter by thought status (active, archived, completed)
        tags: Comma-separated tags to filter by (OR logic)
        limit: Max results per page (1-100, default 20)
        offset: Pagination offset (default 0)
        sort_by: Field to sort by (created_at, updated_at)
        sort_order: asc or desc (default desc)
        
    Returns:
        thoughts: Array of ThoughtResponse objects
        pagination: total, offset, limit, has_more
    """
    try:
        user_id = UUID(get_current_user_id())
        
        # Parse tags if provided
        parsed_tags = None
        if tags:
            parsed_tags = [t.strip().lower() for t in tags.split(",")]
        
        service = ThoughtService(db)
        results, total = await service.list_thoughts(
            user_id=user_id,
            status=status_filter,
            tags=parsed_tags,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        thought_responses = [r.to_response().model_dump(mode='json') for r in results]
        
        return APIResponse.success(
            data={
                "thoughts": thought_responses,
                "pagination": {
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                    "has_more": (offset + limit) < total
                }
            }
        )
        
    except InvalidDataError as e:
        raise APIError(
            code="INVALID_FILTER",
            message=f"Invalid filter parameters: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
```

### Updated GET /api/v1/thoughts/{thought_id}

**After:**
```python
@router.get("/{thought_id}", status_code=status.HTTP_200_OK)
async def get_thought(
    thought_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Retrieve a single thought by ID.
    
    Args:
        thought_id: UUID of the thought
        
    Returns:
        200 OK: Complete ThoughtResponse
        404 Not Found: If thought doesn't exist or user doesn't own it
        401 Unauthorized: If API key invalid
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = ThoughtService(db)
        thought_db = await service.get_thought(
            thought_id=thought_id,
            user_id=user_id
        )
        
        return APIResponse.success(
            data=thought_db.to_response().model_dump(mode='json')
        )
        
    except NotFoundError as e:
        raise ThoughtNotFoundError(str(thought_id))
    except UnauthorizedError as e:
        raise APIError(
            code="UNAUTHORIZED",
            message="You do not have permission to access this thought",
            status_code=status.HTTP_403_FORBIDDEN
        )
```

### Updated PUT /api/v1/thoughts/{thought_id}

**After:**
```python
@router.put("/{thought_id}", status_code=status.HTTP_200_OK)
async def update_thought(
    thought_id: UUID,
    thought_update: ThoughtUpdate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Update an existing thought.
    
    Only provided fields are updated. Unspecified fields retain their values.
    The updated_at timestamp is automatically refreshed.
    
    Args:
        thought_id: UUID of the thought
        thought_update: Fields to update (all optional)
        
    Returns:
        200 OK: Updated ThoughtResponse
        404 Not Found: If thought doesn't exist
        400 Bad Request: If update data invalid
    """
    try:
        user_id = UUID(get_current_user_id())
        
        # Only update provided fields
        update_data = thought_update.model_dump(exclude_unset=True)
        
        service = ThoughtService(db)
        thought_db = await service.update_thought(
            thought_id=thought_id,
            user_id=user_id,
            **update_data
        )
        
        return APIResponse.success(
            data=thought_db.to_response().model_dump(mode='json')
        )
        
    except NotFoundError as e:
        raise ThoughtNotFoundError(str(thought_id))
    except InvalidDataError as e:
        raise InvalidContentError(str(e))
```

### Updated DELETE /api/v1/thoughts/{thought_id}

**After:**
```python
@router.delete("/{thought_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thought(
    thought_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Delete a thought.
    
    Args:
        thought_id: UUID of the thought
        
    Returns:
        204 No Content: Empty body (successful deletion)
        404 Not Found: If thought doesn't exist
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = ThoughtService(db)
        deleted = await service.delete_thought(
            thought_id=thought_id,
            user_id=user_id
        )
        
        if not deleted:
            raise ThoughtNotFoundError(str(thought_id))
        
        return  # 204 No Content with empty body
        
    except NotFoundError as e:
        raise ThoughtNotFoundError(str(thought_id))
```

### Updated GET /api/v1/thoughts/search

**After:**
```python
@router.get("/search", status_code=status.HTTP_200_OK)
async def search_thoughts(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Full-text search on thought content and tags.
    
    Query Parameters:
        q: Search term (required, min 1 char)
        limit: Max results (default 50, max 100)
        offset: Pagination offset (default 0)
        
    Returns:
        results: Array of matching thoughts with relevance_score
        pagination: total, offset, limit, has_more
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = ThoughtService(db)
        results, total = await service.search_thoughts(
            user_id=user_id,
            query=q,
            limit=limit,
            offset=offset
        )
        
        result_data = [
            {
                **r[0].to_response().model_dump(mode='json'),
                "match_score": r[1]
            }
            for r in results
        ]
        
        return APIResponse.success(
            data={
                "query": q,
                "results": result_data,
                "pagination": {
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                    "has_more": (offset + limit) < total
                }
            }
        )
        
    except InvalidDataError as e:
        raise APIError(
            code="INVALID_QUERY",
            message=f"Invalid search query: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
```

---

## Part 2: Tasks Routes Integration

**Similar pattern to thoughts:**

### POST /api/v1/tasks (Create)

```python
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Create a task from thought or standalone."""
    try:
        user_id = UUID(get_current_user_id())
        
        service = TaskService(db)
        task_db = await service.create_task(
            user_id=user_id,
            title=task.title,
            description=task.description,
            source_thought_id=task.source_thought_id,
            priority=task.priority,
            due_date=task.due_date,
            estimated_effort_minutes=task.estimated_effort_minutes
        )
        
        return APIResponse.success(
            data=task_db.to_response().model_dump(mode='json'),
            status_code=status.HTTP_201_CREATED
        )
    except NotFoundError as e:
        raise APIError(
            code="SOURCE_THOUGHT_NOT_FOUND",
            message=f"Source thought not found: {str(e)}",
            status_code=status.HTTP_404_NOT_FOUND
        )
    except InvalidDataError as e:
        raise APIError(
            code="INVALID_TASK",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
```

### GET /api/v1/tasks (List)

Similar to thoughts list, with status/priority/due_date filters.

### GET /api/v1/tasks/{task_id}

Retrieve single task by ID.

### PUT /api/v1/tasks/{task_id}

Update task fields.

### DELETE /api/v1/tasks/{task_id}

Delete task.

### POST /api/v1/tasks/{task_id}/complete

Special endpoint to mark task as done:

```python
@router.post("/{task_id}/complete", status_code=status.HTTP_200_OK)
async def complete_task(
    task_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Mark a task as completed."""
    try:
        user_id = UUID(get_current_user_id())
        
        service = TaskService(db)
        task_db = await service.complete_task(
            task_id=task_id,
            user_id=user_id
        )
        
        return APIResponse.success(
            data=task_db.to_response().model_dump(mode='json')
        )
    except NotFoundError:
        raise APIError(
            code="TASK_NOT_FOUND",
            message=f"Task with ID '{task_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
```

---

## Part 3: Error Handling Middleware

### Exception-to-Response Conversion

Update `src/api/middleware.py` to handle service exceptions:

```python
from src.services.exceptions import (
    ServiceError,
    NotFoundError,
    UnauthorizedError,
    InvalidDataError,
    DatabaseError
)

async def service_exception_handler(request: Request, exc: ServiceError):
    """Convert service exceptions to API responses."""
    
    if isinstance(exc, NotFoundError):
        return APIResponse.error(
            code=f"{exc.resource_type.upper()}_NOT_FOUND",
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    elif isinstance(exc, UnauthorizedError):
        return APIResponse.error(
            code="FORBIDDEN",
            message=str(exc),
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    elif isinstance(exc, InvalidDataError):
        return APIResponse.error(
            code="INVALID_DATA",
            message=str(exc),
            details=exc.details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    elif isinstance(exc, DatabaseError):
        logger.error(f"Database error: {exc}")
        return APIResponse.error(
            code="DATABASE_ERROR",
            message="Internal server error (database operation failed)",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    else:
        logger.error(f"Service error: {exc}")
        return APIResponse.error(
            code="SERVICE_ERROR",
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Register in main.py:
@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return await service_exception_handler(request, exc)
```

---

## Part 4: Integration Testing Strategy

### API Integration Tests

**File:** `tests/integration/test_api_endpoints.py`

```python
@pytest.mark.integration
class TestThoughtEndpoints:
    """Test API endpoints with real database and service layer."""
    
    def test_create_thought_full_flow(
        self, 
        api_client: TestClient, 
        api_headers: dict,
        db_session: Session
    ):
        """
        Full flow: POST /thoughts
        
        Verify:
        - 201 Created response
        - Thought in database
        - All fields returned
        - ID and timestamps generated
        """
        response = api_client.post(
            "/api/v1/thoughts",
            json={
                "content": "Test thought",
                "tags": ["test"],
                "context": {"app": "test"}
            },
            headers=api_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"]  # ID generated
        assert data["data"]["created_at"]  # Timestamp set
        
        # Verify in database
        thought = db_session.query(ThoughtDB).filter_by(
            id=data["data"]["id"]
        ).first()
        assert thought is not None
        assert thought.content == "Test thought"
    
    def test_get_thought_after_create(self, api_client, api_headers, db_session):
        """Create then retrieve thought."""
        # Create
        create_response = api_client.post(...)
        thought_id = create_response.json()["data"]["id"]
        
        # Retrieve
        get_response = api_client.get(
            f"/api/v1/thoughts/{thought_id}",
            headers=api_headers
        )
        
        assert get_response.status_code == 200
        assert get_response.json()["data"]["id"] == thought_id
    
    def test_list_thoughts_with_pagination(self, api_client, api_headers, db_session):
        """List with limit and offset."""
        # Create 25 thoughts
        for i in range(25):
            api_client.post(
                "/api/v1/thoughts",
                json={"content": f"Thought {i}", "tags": []},
                headers=api_headers
            )
        
        # Get first page (limit 10)
        response = api_client.get(
            "/api/v1/thoughts?limit=10&offset=0",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["thoughts"]) == 10
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["has_more"] is True
    
    def test_search_thoughts_returns_matches(self, api_client, api_headers, db_session):
        """Search returns matching thoughts."""
        # Create thoughts with searchable content
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Email is important", "tags": []},
            headers=api_headers
        )
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Just a random thought", "tags": []},
            headers=api_headers
        )
        
        # Search for "email"
        response = api_client.get(
            "/api/v1/thoughts/search?q=email",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["results"]) >= 1
        assert "Email" in data["results"][0]["content"]
    
    def test_update_thought_partial(self, api_client, api_headers, db_session):
        """Update only specified fields."""
        # Create
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Original", "tags": ["old"]},
            headers=api_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        # Update only content
        update_resp = api_client.put(
            f"/api/v1/thoughts/{thought_id}",
            json={"content": "Updated content"},
            headers=api_headers
        )
        
        assert update_resp.status_code == 200
        data = update_resp.json()["data"]
        assert data["content"] == "Updated content"
        assert data["tags"] == ["old"]  # Unchanged
    
    def test_delete_thought_removes_from_database(self, api_client, api_headers, db_session):
        """Delete removes thought from database."""
        # Create
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "To delete", "tags": []},
            headers=api_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        # Delete
        delete_resp = api_client.delete(
            f"/api/v1/thoughts/{thought_id}",
            headers=api_headers
        )
        assert delete_resp.status_code == 204
        
        # Verify gone from database
        thought = db_session.query(ThoughtDB).filter_by(id=thought_id).first()
        assert thought is None
    
    def test_create_thought_without_auth_fails(self, api_client):
        """Request without API key returns 401."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Test", "tags": []}
            # No headers
        )
        assert response.status_code == 401
    
    def test_create_invalid_thought_fails(self, api_client, api_headers):
        """Invalid content rejected."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": "", "tags": []},  # Empty content
            headers=api_headers
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_CONTENT"
```

---

## Success Criteria

- [ ] All thought endpoints functional and tested
- [ ] All task endpoints functional and tested
- [ ] Service layer called from each route
- [ ] Database operations working end-to-end
- [ ] Error handling converts exceptions to API responses
- [ ] Ownership checks prevent cross-user access
- [ ] Pagination works correctly
- [ ] Search returns results with relevance scores
- [ ] Integration tests achieve 80%+ coverage
- [ ] All endpoints respond with consistent APIResponse format
- [ ] Rate limiting middleware active
- [ ] Health check endpoint returns 200
- [ ] API documentation (/docs) shows all endpoints

---

## Code Organization

Sonnet will update:

```
src/api/routes/
├── thoughts.py              # UPDATED: Calls ThoughtService
├── tasks.py                 # UPDATED: Calls TaskService
├── claude.py                # Stubbed (Phase 3)
└── health.py                # No changes needed

src/api/
├── middleware.py            # UPDATED: Service exception handlers
└── (other files unchanged)

tests/integration/
├── test_api_endpoints.py    # NEW: Full API integration tests
├── test_thought_service.py  # Existing from Phase 2B-1
└── test_task_service.py     # Existing from Phase 2B-1
```

---

## Notes for Sonnet

When updating API routes:

1. **Service Injection:**
   - Import service classes
   - Create service instance with db_session: `service = ThoughtService(db)`
   - Call async methods with await

2. **Error Conversion:**
   - Catch service exceptions
   - Convert to API-appropriate exceptions (404, 400, 500)
   - Log unexpected errors
   - Return consistent APIResponse format

3. **Response Formatting:**
   - Use `model.to_response().model_dump(mode='json')` for serialization
   - Include pagination for list endpoints
   - Use correct HTTP status codes

4. **Testing:**
   - Write comprehensive integration tests
   - Test valid and invalid inputs
   - Test ownership/authorization
   - Test pagination and filtering
   - Mock API client for requests

5. **Documentation:**
   - Docstrings explain what endpoint does
   - List all query parameters
   - Document return values
   - Document error codes

Generate production-ready endpoints that are fully tested and integrated with service layer.
