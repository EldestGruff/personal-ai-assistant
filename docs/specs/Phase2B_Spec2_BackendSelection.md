# Phase 2B Spec 2: Backend Selection & Orchestration

**Status:** Ready for Code Generation  
**Target:** Claude Sonnet  
**Output:** BackendSelector protocol, orchestrator logic, configuration system  
**Complexity:** High  
**Est. Lines of Code:** 800 (code + tests)

---

## Overview

This spec defines the decision-making layer that determines which backend(s) to use and orchestrates fallback when the primary backend fails.

After this spec, your system will:
- Make intelligent decisions about which backend to use
- Fall back gracefully when primary fails
- Log decision-making for observability
- Configure backend selection via environment variables

---

## Core Protocol: BackendSelector

### Responsibility
Given a request and available backends, decide which backend(s) to use and in what order.

### Request Schema

```python
class BackendSelectionRequest(BaseModel):
    """Request to select appropriate backend(s)"""
    
    request_id: str = Field(..., description="Unique request identifier")
    thought_length: int = Field(
        ..., 
        ge=1,
        le=5000,
        description="Length of the thought content"
    )
    analysis_type: str = Field(
        default="standard",
        description="Type of analysis: 'standard', 'deep', 'quick'"
    )
    available_backends: list[str] = Field(
        ...,
        description="Names of available backends (e.g., ['claude', 'ollama'])"
    )
    user_preferences: Optional[dict] = Field(
        default=None,
        description="User preferences (prefer_local, max_latency_ms, etc.)"
    )
```

---

### Response Schema

```python
class BackendChoice(BaseModel):
    """Choice of a single backend"""
    
    name: str = Field(description="Backend name (e.g., 'claude', 'ollama')")
    role: str = Field(
        description="Role in this decision: 'primary', 'fallback', 'parallel'"
    )
    timeout_seconds: int = Field(
        default=30,
        description="Timeout for this specific backend"
    )

class BackendSelectionResponse(BaseModel):
    """Decision about which backend(s) to use"""
    
    request_id: str
    decision_type: str = Field(
        description="Decision strategy: PRIMARY_ONLY, SEQUENTIAL, PARALLEL, COST_OPTIMIZED"
    )
    backends: list[BackendChoice] = Field(
        description="Primary backend(s) to try first"
    )
    fallback_backends: list[BackendChoice] = Field(
        default=[],
        description="Fallback backend(s) if primary fails"
    )
    reasoning: str = Field(
        description="Explanation of why this decision was made"
    )
    timestamp: str = Field(description="ISO8601 timestamp")
```

---

## Decision Strategies

### SEQUENTIAL (Recommended - use this for MVP)
1. Primary backend: Claude (if available)
2. Fallback backend: Ollama (if available)

Automatically try fallback if primary fails with recoverable error.

---

## BackendOrchestrator: Execution Logic

The orchestrator takes selector decisions and executes them with fallback:

```python
class BackendOrchestrator:
    """Orchestrates backend selection and execution"""
    
    def __init__(
        self,
        registry: AIBackendRegistry,
        selector: BackendSelector
    ):
        self.registry = registry
        self.selector = selector
    
    async def analyze_with_fallback(
        self,
        request: BackendRequest,
        thought_length: int
    ) -> Union[SuccessResponse, ErrorResponse]:
        """Analyze using selector logic with automatic fallback"""
```

**Logic**:
1. Ask selector which backends to use
2. Try primary backend
3. If primary succeeds → return result
4. If primary fails with recoverable error (RATE_LIMITED, UNAVAILABLE, TIMEOUT) → try fallback
5. If primary fails with non-recoverable error (INVALID_INPUT) → return error (don't try fallback)
6. If fallback succeeds → return result
7. If all backends fail → return error

---

## Configuration

Backend selection controlled via environment variables:

```bash
# .env

# Which backends are available
AVAILABLE_BACKENDS=claude,ollama

# Primary backend
PRIMARY_BACKEND=claude
CLAUDE_API_KEY=sk-...

# Secondary backend (Ollama)
SECONDARY_BACKEND=ollama
OLLAMA_BASE_URL=http://192.168.7.187:11434
OLLAMA_MODEL=llama2

# Selection strategy
BACKEND_SELECTION_STRATEGY=sequential
```

```python
class BackendConfig(BaseModel):
    """Configuration for backend selection"""
    
    available_backends: list[str] = Field(
        default=["claude", "ollama"]
    )
    primary_backend: str = Field(default="claude")
    secondary_backend: Optional[str] = Field(default="ollama")
    selection_strategy: str = Field(default="sequential")
    
    @classmethod
    def from_env(cls) -> "BackendConfig":
        """Load from environment variables"""
        return cls(...)
```

---

## DefaultSelector Implementation

```python
class DefaultSelector(BackendSelector):
    """Default backend selector - SEQUENTIAL strategy"""
    
    def __init__(self, config: BackendConfig):
        self.config = config
    
    async def select_backends(
        self,
        request: BackendSelectionRequest
    ) -> BackendSelectionResponse:
        """Select backends using SEQUENTIAL strategy
        
        - Primary: configured primary backend (usually Claude)
        - Fallback: configured secondary backend (usually Ollama)
        """
```

---

## File Organization

```
src/services/backend_selection/
├── __init__.py
├── models.py                    # Request/Response schemas
├── base.py                      # BackendSelector protocol
├── default_selector.py          # DefaultSelector
├── orchestrator.py              # BackendOrchestrator
├── config.py                    # Configuration loading
└── exceptions.py                # Custom exceptions

tests/unit/backend_selection/
├── test_default_selector.py
├── test_orchestrator.py
└── test_config.py
```

---

## Testing Strategy

### Unit Tests: Selector Logic
- Selector chooses correct primary when available
- Selector uses fallback when primary unavailable
- Configuration loads from environment

### Integration Tests: Orchestrator
- When primary succeeds → return its result
- When primary fails with RATE_LIMITED → try fallback
- When primary fails with UNAVAILABLE → try fallback
- When primary fails with INVALID_INPUT → don't fallback
- When all backends fail → return error

---

## Error Handling

The orchestrator maps backend errors to decisions:

| Backend Error | Action |
|---------------|--------|
| RATE_LIMITED | Try fallback |
| UNAVAILABLE | Try fallback |
| TIMEOUT | Try fallback |
| INVALID_INPUT | Return error (don't retry) |
| CONTEXT_OVERFLOW | Return error (don't retry) |
| INTERNAL_ERROR | Try fallback (once) |
| MALFORMED_RESPONSE | Try fallback (once) |

---

## Success Criteria

✅ BackendSelector protocol defined
✅ DefaultSelector implements SEQUENTIAL strategy
✅ BackendOrchestrator handles primary + fallback
✅ Configuration loads from environment variables
✅ Fallback is automatic (primary fails → try fallback)
✅ Logging shows decision rationale
✅ Timeout enforced per backend
✅ Unit tests validate selector logic
✅ Integration tests validate orchestration

---

## Notes for Sonnet

1. Selector makes decisions. Orchestrator executes them.
2. Logging critical - show which backend chosen and why
3. Use asyncio.wait_for() for timeout enforcement
4. Classify errors correctly - recoverable vs non-recoverable
5. Fallback is automatic and transparent to caller
6. Configuration from environment (enables deployment flexibility)
7. Generate production-quality code
