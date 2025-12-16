# Phase 2B Spec 3: Integration & New Endpoint

**Status:** Ready for Code Generation  
**Target:** Claude Sonnet  
**Output:** Refactored ThoughtAnalyzer, new consciousness-check-v2 endpoint, metrics, health checks  
**Complexity:** Medium  
**Est. Lines of Code:** 600 (code + tests)

---

## Overview

This spec integrates the backend abstraction and orchestration into the actual API. After this spec:
- New `/api/v1/consciousness-check-v2` endpoint uses pluggable backends
- Existing `/api/v1/consciousness-check` (v1) continues working (backward compatibility)
- Per-backend metrics collected (success rate, response time, tokens)
- Health checks verify backend availability
- Gradual migration path: validate v2, migrate consumers, retire v1

---

## ThoughtAnalyzer Refactoring

### Current Implementation (Phase 2A - Tightly Coupled)

```python
class ThoughtAnalyzer:
    def __init__(self, claude_service: ClaudeService):
        self.claude_service = claude_service
    
    async def analyze(self, thought: Thought) -> dict:
        """Analyze using Claude directly"""
        result = await self.claude_service.analyze_thought(thought.content)
        return result
```

### New Implementation (Phase 2B - Uses Abstraction)

```python
class ThoughtAnalyzer:
    def __init__(self, orchestrator: BackendOrchestrator):
        """Initialize with backend orchestrator (not specific backend)"""
        self.orchestrator = orchestrator
    
    async def analyze(self, thought: Thought) -> Union[SuccessResponse, ErrorResponse]:
        """Analyze using orchestrator (handles backend selection + fallback)"""
        
        request = BackendRequest(
            request_id=str(uuid4()),
            thought_content=thought.content,
            context={"user_id": thought.user_id},
            timeout_seconds=30
        )
        
        # Orchestrator handles:
        # 1. Backend selection (which backend to use)
        # 2. Fallback (try primary, then fallback if fails)
        # 3. Error handling
        response = await self.orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(thought.content)
        )
        
        return response
```

**Key Changes**:
- Dependency injection: receives orchestrator, not specific backend
- No direct Claude API calls
- Automatic fallback if primary fails
- Metrics collected automatically

---

## New Endpoint: consciousness-check-v2

### Route Definition

```python
# src/api/routes/consciousness_v2.py

@router.post("/consciousness-check-v2")
async def consciousness_check_v2(
    request: ConsciousnessCheckRequest,
    api_key: str = Depends(verify_api_key),
    analyzer: ThoughtAnalyzer = Depends(get_thought_analyzer),
    metrics: BackendMetrics = Depends(get_metrics)
) -> ConsciousnessCheckResponse:
    """
    Consciousness check using pluggable backends
    
    Uses backend selection/orchestration:
    - Primary: Claude (fast, capable)
    - Fallback: Ollama (local, always available)
    """
```

### Request Schema

```python
class ThoughtRef(BaseModel):
    id: str
    content: str

class ConsciousnessCheckRequest(BaseModel):
    recent_thoughts: list[ThoughtRef] = Field(
        ...,
        description="Thoughts to analyze (usually last 10-20)"
    )
    limit_recent: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max results to return"
    )
    include_archived: bool = Field(
        default=False,
        description="Include archived thoughts"
    )
```

### Response Schema

```python
class BackendStats(BaseModel):
    requests_total: int
    requests_success: int
    requests_failed: int
    success_rate: float
    avg_response_time_ms: float
    tokens_used: int = 0

class ConsciousnessCheckResponse(BaseModel):
    success: bool
    request_id: str
    summary: str
    themes: list[str]
    suggested_actions: list[str]
    source_analyses: int
    backend_stats: dict[str, BackendStats]
    timestamp: str
```

---

## Metrics Collection

### BackendMetrics Service

```python
# src/services/metrics.py

class BackendMetrics:
    """Track backend performance metrics"""
    
    def record_success(
        self,
        backend_name: str,
        response_time_ms: int,
        tokens: int = 0
    ) -> None:
        """Record successful request"""
    
    def record_failure(
        self,
        backend_name: str,
        error_code: str
    ) -> None:
        """Record failed request"""
    
    def get_stats(self, backend_name: str) -> BackendStats:
        """Get current stats for a backend"""
```

Tracks:
- requests_total, requests_success, requests_failed
- success_rate
- average response time
- tokens used
- error codes

---

## Health Checks

### Backend Health Endpoint

```python
# src/api/routes/health.py (UPDATED)

@router.get("/health/backends")
async def health_backends(
    registry: AIBackendRegistry = Depends(get_backend_registry)
) -> dict:
    """Check health of all configured backends"""
```

Returns:
```json
{
  "claude": {
    "status": "healthy",
    "available": true,
    "response_time_ms": 1200
  },
  "ollama": {
    "status": "healthy",
    "available": true,
    "response_time_ms": 850
  }
}
```

---

## Dependency Injection Setup

```python
# src/api/main.py

@app.on_event("startup")
async def startup_backend_system():
    """Initialize backends and orchestrator"""
    
    # Load configuration
    config = BackendConfig.from_env()
    
    # Create registry and register backends
    registry = AIBackendRegistry()
    
    if "claude" in config.available_backends:
        registry.register(
            "claude",
            ClaudeBackend(api_key=os.getenv("ANTHROPIC_API_KEY"))
        )
    
    if "ollama" in config.available_backends:
        registry.register(
            "ollama",
            OllamaBackend(base_url=os.getenv(
                "OLLAMA_BASE_URL",
                "http://192.168.7.187:11434"
            ))
        )
    
    # Create selector and orchestrator
    selector = DefaultSelector(config)
    orchestrator = BackendOrchestrator(registry, selector)
    
    # Create analyzer
    analyzer = ThoughtAnalyzer(orchestrator)
    
    # Store in app state
    app.state.orchestrator = orchestrator
    app.state.analyzer = analyzer
    app.state.metrics = BackendMetrics()
```

---

## Migration Path: v1 → v2

### Phase 1: Both Running
- v1: `/api/v1/consciousness-check` (current, uses direct Claude)
- v2: `/api/v1/consciousness-check-v2` (new, uses orchestrator)

Run in parallel, compare outputs.

### Phase 2: Migrate Consumers
- Update iOS Shortcuts → call v2
- Update internal tools → call v2
- Monitor metrics

### Phase 3: Retire v1
- Remove v1 endpoint
- Remove old ClaudeAnalysisService
- Consolidate to v2

---

## File Organization

```
src/api/
├── routes/
│   ├── consciousness.py     # v1 (deprecated)
│   ├── consciousness_v2.py  # v2 (new)
│   └── health.py            # Updated

src/services/
├── thought_analyzer.py      # REFACTORED
└── metrics.py               # NEW
```

---

## Testing Strategy

### Integration Tests: v2 Endpoint

```python
async def test_returns_valid_response(self, client, test_api_key):
    """v2 endpoint returns valid response"""
    response = client.post(
        "/api/v1/consciousness-check-v2",
        json={
            "recent_thoughts": [
                {"id": "1", "content": "Test thought"}
            ]
        },
        headers={"Authorization": f"Bearer {test_api_key}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "summary" in data
    assert "backend_stats" in data

async def test_includes_backend_metrics(self, client, test_api_key):
    """Response includes per-backend metrics"""
    # Verify backend_stats populated
```

---

## Success Criteria

✅ ThoughtAnalyzer uses orchestrator (not direct Claude)
✅ New `/api/v1/consciousness-check-v2` endpoint works
✅ Metrics collected per backend
✅ Health checks verify backend availability
✅ Fallback works (primary fails → secondary)
✅ Logging shows backend selection/execution
✅ Integration tests pass
✅ Backward compatibility (v1 still works)

---

## Notes for Sonnet

1. Dependency injection - Analyzer gets orchestrator, not specific backend
2. Metrics optional but useful - nice to have for observability
3. Both endpoints coexist - v1 and v2 during migration
4. Health checks lightweight - just poke backends to verify available
5. Error handling graceful - v2 handles backend failures automatically
6. Generate production-quality code
