# Backend Data Flow

**Personal AI Assistant - Request Flows & Sequence Diagrams**

**Last Updated:** January 4, 2026  
**Version:** 0.1.0  
**Status:** Phase 3B Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
3. [Thought Capture Flow](#thought-capture-flow)
4. [AI Analysis Flow](#ai-analysis-flow)
5. [Task Suggestion Flow](#task-suggestion-flow)
6. [Consciousness Check Flow](#consciousness-check-flow)
7. [Task Management Flow](#task-management-flow)
8. [Settings Management Flow](#settings-management-flow)
9. [Error Handling Flow](#error-handling-flow)
10. [Background Job Flow](#background-job-flow)

---

## Overview

This document maps the complete data flow through the Personal AI Assistant backend, showing how requests travel from the client through the API layer, service layer, AI orchestration, and database.

### **Request Flow Layers**

```mermaid
graph LR
    A[Client] -->|HTTP Request| B[FastAPI]
    B --> C[Auth Middleware]
    C --> D[Route Handler]
    D --> E[Service Layer]
    E --> F{AI Backend?}
    F -->|Yes| G[AI Orchestrator]
    F -->|No| H[Database]
    G --> I[Claude/Ollama]
    I --> H
    E --> H
    H -->|Data| E
    E -->|Response| D
    D -->|JSON| B
    B -->|HTTP Response| A
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#fff4e1
    style D fill:#e8f5e9
    style E fill:#e8f5e9
    style G fill:#ffe0b2
    style I fill:#ffebee
    style H fill:#f3e5f5
```

### **Typical Response Times**

| Flow Type | Layers Involved | Target Time | Notes |
|-----------|----------------|-------------|-------|
| Simple CRUD | Client → API → Service → DB | < 100ms | Direct database operations |
| AI Analysis | Client → API → Service → AI → DB | 3-5s | External AI API call |
| Consciousness Check | Background → Service → AI → DB | 5-10s | Multiple AI calls, pattern analysis |
| Task Accept | Client → API → Service → DB | < 300ms | Multiple database writes |

---

## Authentication Flow

Every API request requires authentication via Bearer token.

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as Auth Middleware
    participant DB as Database
    participant R as Route Handler
    
    C->>MW: HTTP Request<br/>Authorization: Bearer {token}
    
    Note over MW: Extract token from header
    MW->>MW: Hash token (SHA256)
    MW->>DB: SELECT * FROM api_keys<br/>WHERE key_hash = ?
    
    alt Valid Token
        DB-->>MW: API key record found
        MW->>MW: Attach user_id to request.state
        MW->>R: Forward request
        R-->>MW: Response
        MW-->>C: HTTP 200 + JSON
    else Invalid Token
        DB-->>MW: No record found
        MW-->>C: HTTP 401 Unauthorized<br/>{"error": "Invalid API key"}
    else Missing Token
        MW-->>C: HTTP 401 Unauthorized<br/>{"error": "Missing Authorization header"}
    end
```

### **Authentication Implementation**

```python
# src/api/dependencies.py

async def verify_api_key(
    authorization: str = Header(None)
) -> str:
    """
    Dependency for API key authentication.
    
    Returns user_id if valid, raises 401 if invalid.
    """
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    
    # Hash token
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Query database
    db = next(get_db())
    api_key = db.query(APIKeyDB).filter(
        APIKeyDB.key_hash == token_hash,
        APIKeyDB.is_active == True
    ).first()
    
    if not api_key:
        raise HTTPException(401, "Invalid API key")
    
    # Update last_used_at
    api_key.last_used_at = datetime.utcnow()
    db.commit()
    
    return api_key.user_id
```

---

## Thought Capture Flow

The most common operation: capturing a new thought from the user.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Route<br/>(thoughts.py)
    participant TS as ThoughtService
    participant INT as ThoughtIntelligence<br/>Service
    participant DB as Database
    participant BG as Background Task
    participant ORCH as AI Orchestrator
    participant CLAUDE as Claude API
    
    C->>API: POST /api/v1/thoughts<br/>{"content": "...", "tags": [...]}
    API->>API: Validate request (Pydantic)
    API->>TS: create_thought(user_id, data)
    
    TS->>DB: INSERT INTO thoughts
    DB-->>TS: Thought created (with ID)
    TS-->>API: ThoughtDB object
    
    Note over API: Thought saved!<br/>Return immediately
    API-->>C: HTTP 201 Created<br/>ThoughtResponse
    
    par Background Analysis
        API->>BG: Schedule analyze_thought_background()
        BG->>INT: analyze_thought_on_capture(thought)
        INT->>INT: Check if auto-analysis enabled
        
        alt Auto-analysis enabled
            INT->>ORCH: analyze(request)
            ORCH->>CLAUDE: API call with prompt
            CLAUDE-->>ORCH: Analysis result
            ORCH-->>INT: Parsed analysis
            
            INT->>DB: UPDATE thoughts SET<br/>suggested_tags, thought_type,<br/>is_actionable, etc.
            
            alt Task detected (confidence > 0.7)
                INT->>DB: INSERT INTO task_suggestions
            end
        end
    end
```

### **Key Points**

1. **Immediate Response:** Thought saved to database first, API returns immediately (< 100ms)
2. **Background Analysis:** AI analysis happens asynchronously via background task
3. **Conditional AI:** Only analyzes if `auto_tagging_enabled` or `auto_task_creation_enabled` is true
4. **Task Detection:** If AI determines thought is actionable with high confidence, creates task suggestion

### **Thought Capture Implementation**

```python
# src/api/routes/thoughts.py

@router.post("/thoughts", response_model=ThoughtResponse, status_code=201)
async def create_thought(
    thought_create: ThoughtCreate,
    user_id: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create new thought.
    
    1. Validate input (Pydantic)
    2. Save to database (immediate)
    3. Return response (< 100ms)
    4. Trigger background AI analysis (async)
    """
    # Create thought via service
    thought = thought_service.create_thought(
        db=db,
        user_id=UUID(user_id),
        thought_create=thought_create
    )
    
    # Schedule background analysis (doesn't block response)
    background_tasks.add_task(
        analyze_thought_background,
        thought_id=UUID(thought.id),
        user_id=UUID(user_id),
        orchestrator=ai_orchestrator,
        db_factory=get_db_context
    )
    
    return thought.to_response()
```

---

## AI Analysis Flow

How AI analysis is orchestrated with fallback backends.

```mermaid
sequenceDiagram
    participant INT as ThoughtIntelligence<br/>Service
    participant ORCH as AI Orchestrator
    participant CLAUDE as Claude Backend
    participant OLLAMA as Ollama Backend
    participant MOCK as Mock Backend
    participant DB as Database
    
    INT->>ORCH: analyze(request)<br/>with prompt & context
    
    Note over ORCH: Try primary backend (Claude)
    ORCH->>CLAUDE: analyze(request)
    
    alt Claude Success
        CLAUDE->>CLAUDE: Call Anthropic API
        CLAUDE-->>ORCH: SuccessResponse
        ORCH-->>INT: Analysis result
    else Claude Timeout
        CLAUDE-->>ORCH: ErrorResponse (TIMEOUT)
        Note over ORCH: Fallback to Ollama
        ORCH->>OLLAMA: analyze(request)
        
        alt Ollama Success
            OLLAMA->>OLLAMA: Call local AI
            OLLAMA-->>ORCH: SuccessResponse
            ORCH-->>INT: Analysis result
        else Ollama Failure
            OLLAMA-->>ORCH: ErrorResponse
            Note over ORCH: Fallback to Mock
            ORCH->>MOCK: analyze(request)
            MOCK-->>ORCH: Mock response
            ORCH-->>INT: Mock analysis
        end
    else Claude Rate Limited
        CLAUDE-->>ORCH: ErrorResponse (RATE_LIMITED)
        Note over ORCH: Wait and retry (3 attempts)
        ORCH->>CLAUDE: analyze(request) [retry 1]
        CLAUDE-->>ORCH: ErrorResponse
        ORCH->>CLAUDE: analyze(request) [retry 2]
        CLAUDE-->>ORCH: SuccessResponse
        ORCH-->>INT: Analysis result
    end
    
    INT->>DB: UPDATE thoughts with analysis
    DB-->>INT: Success
```

### **Backend Selection Logic**

```python
# src/services/ai_backends/orchestrator.py

async def analyze(self, request: BackendRequest) -> SuccessResponse:
    """
    Orchestrate backend selection with fallback.
    
    Order:
    1. Primary backend (Claude)
    2. Secondary backend (Ollama, if configured)
    3. Mock backend (testing/fallback)
    
    Retry logic:
    - Timeout: Try next backend
    - Rate limited: Wait and retry (3 attempts)
    - Unavailable: Try next backend
    """
    backends_to_try = [
        self.primary_backend,
        self.secondary_backend,
        self.mock_backend
    ]
    
    for backend in backends_to_try:
        if not backend:
            continue
        
        try:
            result = await backend.analyze(request)
            
            if isinstance(result, SuccessResponse):
                return result
            
            # Handle retryable errors
            if result.error.error_code == "RATE_LIMITED":
                await asyncio.sleep(5)  # Wait before retry
                result = await backend.analyze(request)
                if isinstance(result, SuccessResponse):
                    return result
        
        except Exception as e:
            logger.warning(f"Backend {backend.name} failed: {e}")
            continue
    
    # All backends failed
    raise AllBackendsFailedError()
```

---

## Task Suggestion Flow

AI detects actionable thought and creates task suggestion.

```mermaid
sequenceDiagram
    participant INT as ThoughtIntelligence<br/>Service
    participant ORCH as AI Orchestrator
    participant CLAUDE as Claude API
    participant TSS as TaskSuggestion<br/>Service
    participant DB as Database
    participant CLIENT as Client<br/>(Dashboard)
    
    Note over INT: Thought analysis complete
    INT->>INT: Check if is_actionable == true<br/>AND confidence > 0.7
    
    alt Actionable & High Confidence
        INT->>TSS: create_suggestion(data)
        TSS->>DB: INSERT INTO task_suggestions
        DB-->>TSS: Suggestion created
        TSS-->>INT: TaskSuggestionDB
        
        Note over INT: Check task_suggestion_mode
        
        alt Mode: "auto_create"
            INT->>TSS: accept_suggestion(suggestion_id)
            TSS->>DB: INSERT INTO tasks
            TSS->>DB: UPDATE task_suggestions<br/>SET status='accepted'
            DB-->>TSS: Task created
        else Mode: "suggest" (default)
            Note over TSS: Suggestion remains pending<br/>User must accept/reject
        end
    end
    
    Note over CLIENT: User opens dashboard
    CLIENT->>API: GET /api/v1/task-suggestions
    API->>TSS: get_pending_suggestions(user_id)
    TSS->>DB: SELECT * FROM task_suggestions<br/>WHERE status='pending'
    DB-->>TSS: Pending suggestions
    TSS-->>API: List[TaskSuggestionDB]
    API-->>CLIENT: HTTP 200 + suggestions
    
    CLIENT->>CLIENT: User clicks "Accept"
    CLIENT->>API: POST /api/v1/task-suggestions/{id}/accept
    API->>TSS: accept_suggestion(id, modifications)
    TSS->>DB: BEGIN TRANSACTION
    TSS->>DB: INSERT INTO tasks
    TSS->>DB: UPDATE task_suggestions<br/>SET status='accepted',<br/>user_action='accepted'
    TSS->>DB: COMMIT
    DB-->>TSS: Success
    TSS-->>API: TaskResponse + SuggestionResponse
    API-->>CLIENT: HTTP 200 + created task
```

### **Task Suggestion Modes**

| Mode | Behavior | User Experience |
|------|----------|-----------------|
| **disabled** | No suggestions created | AI analysis doesn't create suggestions |
| **suggest** (default) | Suggestions created, pending user approval | User sees suggestions, must accept/reject |
| **auto_create** | Suggestions auto-accepted, task created immediately | Task appears instantly after thought capture |

---

## Consciousness Check Flow

Periodic analysis of recent thoughts to surface patterns and insights.

```mermaid
sequenceDiagram
    participant SCHED as APScheduler
    participant CS as Consciousness<br/>Service
    participant TS as ThoughtService
    participant PROF as ProfileService
    participant ORCH as AI Orchestrator
    participant CLAUDE as Claude API
    participant TSS as TaskSuggestion<br/>Service
    participant DB as Database
    
    Note over SCHED: Every 30-60 minutes
    SCHED->>CS: run_consciousness_check(user_id)
    
    CS->>TS: get_recent_thoughts(user_id, limit=20)
    TS->>DB: SELECT * FROM thoughts<br/>WHERE user_id=? ORDER BY created_at DESC
    DB-->>TS: Recent thoughts
    TS-->>CS: List[ThoughtDB]
    
    CS->>PROF: get_profile(user_id)
    PROF->>DB: SELECT * FROM user_profiles
    DB-->>PROF: UserProfileDB
    PROF-->>CS: Profile data
    
    CS->>CS: Build consciousness check prompt<br/>with thoughts + profile context
    
    CS->>ORCH: analyze(request)<br/>Prompt: "Analyze these thoughts..."
    ORCH->>CLAUDE: API call
    CLAUDE-->>ORCH: Analysis result
    ORCH-->>CS: Parsed result
    
    Note over CS: Process analysis result
    CS->>CS: Extract patterns, themes, insights
    
    loop For each suggested action
        CS->>TSS: create_suggestion(action)
        TSS->>DB: INSERT INTO task_suggestions
    end
    
    CS->>DB: INSERT INTO claude_analysis_results<br/>WITH summary, themes, insights
    DB-->>CS: Success
    
    CS->>DB: UPDATE user_profiles<br/>SET patterns = updated_patterns
    DB-->>CS: Success
    
    CS-->>SCHED: Check complete
```

### **Consciousness Check Prompt Template**

```python
# src/services/ai_backends/prompts.py

def build_consciousness_check_prompt(
    recent_thoughts: List[ThoughtDB],
    user_profile: UserProfileDB,
    time_window: str
) -> str:
    """
    Build comprehensive consciousness check prompt.
    
    Includes:
    - Recent thoughts (last 24 hours typically)
    - User profile context (projects, patterns)
    - Previous insights (for continuity)
    """
    return f"""
    You are Andy's Personal AI Assistant performing a consciousness check.
    
    **About Andy:**
    {format_user_profile(user_profile)}
    
    **Recent Thoughts ({time_window}):**
    {format_thoughts_for_analysis(recent_thoughts)}
    
    **Previous Patterns:**
    {user_profile.work_patterns}
    
    **Your Task:**
    Analyze these thoughts and provide:
    1. **Themes:** What patterns do you see?
    2. **Insights:** What can Andy learn from this?
    3. **Suggested Actions:** What should Andy do next?
    4. **Concerns:** Anything Andy should be aware of?
    
    Be warm, encouraging, and helpful. Andy has ADHD, so actionable
    insights are more valuable than abstract observations.
    
    Respond in JSON format: {{
      "summary": "Brief overview...",
      "themes": ["theme1", "theme2"],
      "insights": ["insight1", "insight2"],
      "suggested_actions": [
        {{"action": "...", "priority": "high/medium/low"}},
      ],
      "concerns": ["concern1"] // Optional
    }}
    """
```

---

## Task Management Flow

Creating, updating, and completing tasks.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Route<br/>(tasks.py)
    participant TASKS as TaskService
    participant DB as Database
    
    Note over C: User creates task manually
    C->>API: POST /api/v1/tasks<br/>{"title": "...", "priority": "high"}
    API->>TASKS: create_task(user_id, data)
    TASKS->>DB: INSERT INTO tasks
    DB-->>TASKS: Task created
    TASKS-->>API: TaskDB
    API-->>C: HTTP 201 + TaskResponse
    
    Note over C: Later... user completes task
    C->>API: PUT /api/v1/tasks/{id}<br/>{"status": "done"}
    API->>TASKS: update_task(task_id, updates)
    TASKS->>DB: UPDATE tasks SET<br/>status='done',<br/>completed_at=NOW()
    DB-->>TASKS: Task updated
    TASKS-->>API: Updated TaskDB
    API-->>C: HTTP 200 + TaskResponse
    
    Note over C: User deletes task
    C->>API: DELETE /api/v1/tasks/{id}
    API->>TASKS: delete_task(task_id)
    TASKS->>DB: DELETE FROM tasks WHERE id=?
    DB-->>TASKS: Deleted
    TASKS-->>API: Success
    API-->>C: HTTP 204 No Content
```

### **Task Status Lifecycle**

```mermaid
stateDiagram-v2
    [*] --> pending: Task created
    pending --> in_progress: User starts task
    in_progress --> done: User completes
    pending --> done: Quick complete
    done --> pending: Reopen task
    pending --> [*]: Delete
    in_progress --> [*]: Delete
    done --> [*]: Delete
```

---

## Settings Management Flow

User updates their AI analysis preferences.

```mermaid
sequenceDiagram
    participant C as Client<br/>(Admin UI)
    participant API as API Route<br/>(settings.py)
    participant SET as SettingsService
    participant DB as Database
    
    Note over C: User opens admin page
    C->>API: GET /api/v1/settings
    API->>SET: get_user_settings(user_id)
    SET->>DB: SELECT * FROM user_settings<br/>WHERE user_id=?
    DB-->>SET: UserSettingsDB
    SET-->>API: UserSettingsResponse
    API-->>C: HTTP 200 + settings
    
    Note over C: User toggles auto-tagging
    C->>API: PUT /api/v1/settings<br/>{"auto_tagging_enabled": true}
    API->>SET: update_settings(user_id, updates)
    SET->>DB: UPDATE user_settings SET<br/>auto_tagging_enabled=true
    DB-->>SET: Settings updated
    SET-->>API: Updated settings
    API-->>C: HTTP 200 + new settings
    
    Note over C,DB: Future thoughts will now<br/>trigger auto-tagging
```

### **Settings Impact on Data Flow**

```mermaid
graph TD
    A[Thought Captured] --> B{Auto-tagging<br/>enabled?}
    B -->|Yes| C[Trigger AI Analysis]
    B -->|No| D[Skip AI Analysis]
    
    C --> E{Auto-task<br/>enabled?}
    E -->|Yes| F[Detect Tasks]
    E -->|No| G[Skip Task Detection]
    
    F --> H{Task<br/>suggestion mode?}
    H -->|disabled| D
    H -->|suggest| I[Create Pending Suggestion]
    H -->|auto_create| J[Create Task Immediately]
    
    style B fill:#fff4e1
    style E fill:#fff4e1
    style H fill:#fff4e1
```

---

## Error Handling Flow

How errors are caught and returned to the client.

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as Error Middleware
    participant API as Route Handler
    participant SVC as Service Layer
    participant DB as Database
    
    C->>MW: HTTP Request
    MW->>API: Forward request
    
    alt Validation Error (Pydantic)
        API->>API: Pydantic validation fails
        API-->>MW: ValidationError
        MW->>MW: Format as 422 response
        MW-->>C: HTTP 422 Unprocessable Entity<br/>{"detail": [...]}
    
    else Service Error (Business Logic)
        API->>SVC: Service method call
        SVC->>SVC: Business logic error
        SVC-->>API: raise ValueError("...")
        API->>API: Catch exception
        API-->>MW: HTTPException(400, ...)
        MW-->>C: HTTP 400 Bad Request<br/>{"detail": "..."}
    
    else Database Error
        SVC->>DB: Database operation
        DB-->>SVC: IntegrityError
        SVC->>SVC: Catch database error
        SVC-->>API: raise DatabaseError("...")
        API->>API: Catch exception
        API-->>MW: HTTPException(500, ...)
        MW-->>C: HTTP 500 Internal Server Error<br/>{"detail": "Database error"}
    
    else Not Found
        SVC->>DB: SELECT ... WHERE id=?
        DB-->>SVC: No rows found
        SVC-->>API: Return None
        API->>API: Check if None
        API-->>MW: HTTPException(404, "Not found")
        MW-->>C: HTTP 404 Not Found<br/>{"detail": "Thought not found"}
    
    else Success
        API->>SVC: Service method call
        SVC->>DB: Database operation
        DB-->>SVC: Success
        SVC-->>API: Return data
        API-->>MW: Response model
        MW-->>C: HTTP 200/201 + JSON
    end
```

### **Error Response Format**

All errors follow FastAPI's standard format:

```json
{
  "detail": "Error message here"
}

// Or for validation errors:
{
  "detail": [
    {
      "loc": ["body", "content"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### **Custom Exception Handling**

```python
# src/api/main.py

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle business logic errors"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors"""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred"}
    )
```

---

## Background Job Flow

How scheduled jobs (consciousness checks) are executed.

```mermaid
sequenceDiagram
    participant MAIN as main.py<br/>(Startup)
    participant SCHED as APScheduler
    participant JOB as Job Function
    participant SVC as Service Layer
    participant DB as Database
    
    Note over MAIN: Application startup
    MAIN->>SCHED: Initialize scheduler
    MAIN->>SCHED: add_job(<br/>  func=run_consciousness_checks,<br/>  trigger="interval",<br/>  minutes=30<br/>)
    SCHED->>SCHED: Start scheduler thread
    SCHED-->>MAIN: Scheduler running
    
    Note over SCHED: Wait 30 minutes...
    SCHED->>JOB: run_consciousness_checks()
    
    JOB->>DB: SELECT * FROM users<br/>WHERE is_active=true
    DB-->>JOB: List of active users
    
    loop For each user
        JOB->>SVC: run_consciousness_check(user_id)
        
        Note over SVC: Check if user wants checks now
        SVC->>DB: SELECT * FROM user_settings
        DB-->>SVC: Settings
        
        alt Consciousness checks enabled
            SVC->>SVC: Perform analysis<br/>(see Consciousness Check Flow)
            SVC->>DB: Store results
        else Disabled
            SVC->>SVC: Skip user
        end
    end
    
    JOB-->>SCHED: Job complete
    
    Note over SCHED: Wait 30 minutes...<br/>Repeat forever
```

### **Scheduler Configuration**

```python
# src/api/main.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    """Start background scheduler on app startup"""
    
    # Add consciousness check job
    scheduler.add_job(
        func=run_all_consciousness_checks,
        trigger="interval",
        minutes=30,  # Configurable via settings
        id="consciousness_checks",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("⏰ Background scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on app shutdown"""
    scheduler.shutdown()
    logger.info("⏰ Scheduler stopped")
```

---

## Data Flow Optimization

### **Caching Strategy** (Future)

```mermaid
graph TB
    A[Request] --> B{Cache Hit?}
    B -->|Yes| C[Return Cached]
    B -->|No| D[Query Database]
    D --> E[Store in Cache]
    E --> F[Return Fresh Data]
    
    style B fill:#fff4e1
```

**Potential Cache Targets:**
- User settings (high read, low write)
- User profiles (high read, low write)
- Recent thoughts (read-heavy on dashboard load)

**Not Cached:**
- Thought creation (write operation)
- Task updates (need immediate consistency)
- AI analysis results (unique per request)

### **Database Query Optimization**

```sql
-- Indexed queries (fast)
SELECT * FROM thoughts 
WHERE user_id = ? 
ORDER BY created_at DESC 
LIMIT 20;
-- Uses: idx_thoughts_user_id, idx_thoughts_created_at

-- Full-text search (slower but acceptable)
SELECT * FROM thoughts 
WHERE user_id = ?
  AND (
    content LIKE '%keyword%' 
    OR tags::text LIKE '%keyword%'
  )
LIMIT 50;
-- Sequential scan on content (no FTS yet)
```

---

## Related Documentation

- [System Architecture](BACKEND_SYSTEM_ARCHITECTURE.md) - Component overview
- [File Organization](BACKEND_FILE_ORGANIZATION.md) - File inventory
- [Component Details](BACKEND_COMPONENT_DETAILS.md) - API/service details
- [API Documentation](http://localhost:8000/docs) - Interactive OpenAPI docs

---

**Document Version:** 1.0  
**Last Updated:** January 4, 2026  
**Maintained By:** Andy (@EldestGruff)
