# Phase 2B Spec 1: Backend Abstraction Layer

**Status:** Ready for Code Generation  
**Target:** Claude Sonnet  
**Output:** Backend protocols, three implementations, registry system, request/response models  
**Complexity:** High  
**Est. Lines of Code:** 1500 (code + tests)

---

## Overview

This specification defines the protocol layer that abstracts AI backends away from business logic. After this spec, your system will support:
- Multiple AI backends (Claude primary, Ollama fallback, Mock for testing)
- Runtime backend selection and swapping
- Consistent request/response contracts across all backends
- Comprehensive error handling and validation

**Key Insight**: The consciousness-check endpoint and ThoughtAnalyzer don't change. The abstraction happens transparently underneath via protocols.

---

## Requirements & Constraints

### Must-Have
- AIBackend protocol that all implementations must satisfy
- ClaudeBackend (wraps Anthropic API, uses existing claude_service.py)
- OllamaBackend (calls http://192.168.7.187:11434)
- MockBackend (deterministic for testing, no API calls)
- BackendRegistry (central registry for managing available backends)
- Request/Response validation (all messages validate against schema)
- Timeout enforcement (no request hangs indefinitely)
- Comprehensive error codes for failure scenarios

### Must-Not
- Break existing API endpoints (consciousness-check v1 continues working)
- Require database changes (this is pure service layer)
- Introduce external dependencies beyond what's already in requirements.txt
- Create circular dependencies

### Edge Cases to Handle
- Backend timeout (request takes too long)
- Backend unavailable (network error, service down)
- Malformed response (backend returns invalid JSON or schema)
- Rate limiting (backend rejects request with 429)
- Context overflow (thought content exceeds backend's context window)
- Partial failures (one field missing from response)

---

## Core Protocol: AIBackend

### Responsibility
Accept a thought analysis request. Return analysis results or a well-structured error. Never leave the caller guessing what happened.

### Request Schema

```python
# src/services/ai_backends/models.py

class BackendRequest(BaseModel):
    """Request to analyze a thought"""
    
    request_id: str = Field(
        ...,
        description="Unique request identifier for tracing"
    )
    thought_content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The thought to analyze (1-5000 characters)"
    )
    context: Optional[dict] = Field(
        default=None,
        description="Additional context (user_id, analysis_depth, etc.)"
    )
    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=60,
        description="Max time to wait for analysis (5-60 seconds)"
    )
    model_hint: Optional[str] = Field(
        default=None,
        description="Suggestion for model selection: 'fast', 'quality', or 'cheap'"
    )
    include_confidence: bool = Field(
        default=True,
        description="Include confidence scores in response"
    )
```

**Validation Rules**:
- `request_id`: Non-empty string, should be UUID format (not enforced)
- `thought_content`: Must be 1-5000 characters, non-whitespace
- `timeout_seconds`: Integer between 5 and 60 (inclusive)
- `context`: If provided, must be a valid dict
- `model_hint`: One of ["fast", "quality", "cheap"] if provided
- `include_confidence`: Boolean

**Example Valid Request**:
```json
{
  "request_id": "req-abc123def456",
  "thought_content": "Should optimize email filtering system",
  "context": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "analysis_depth": "deep"
  },
  "timeout_seconds": 20,
  "model_hint": "quality",
  "include_confidence": true
}
```

---

## Backend Implementations

### Implementation 1: ClaudeBackend
- Wraps or refactors existing `src/services/claude_service.py`
- Uses Anthropic SDK (already in requirements.txt)
- Model: claude-3-haiku-20240307 (or latest available)
- Maps Claude exceptions to standard error codes
- Respects timeout_seconds

### Implementation 2: OllamaBackend
- Calls Ollama at http://192.168.7.187:11434
- Uses httpx or aiohttp for async HTTP
- Model: llama2 (configurable)
- Endpoint: POST /api/generate
- Fully async, respects timeout

### Implementation 3: MockBackend
- No API calls, fully deterministic
- Names: "mock-success", "mock-timeout", "mock-unavailable", "mock-rate-limited"
- Returns canned responses
- Used for testing

---

## Response Schema (Success)

```python
class Theme(BaseModel):
    theme: str
    confidence: float = Field(ge=0.0, le=1.0)

class SuggestedAction(BaseModel):
    action: str
    priority: str = Field(description="low, medium, high")
    confidence: float = Field(ge=0.0, le=1.0)

class Analysis(BaseModel):
    request_id: str
    thought_id: Optional[str] = None
    backend_used: str
    summary: str
    themes: list[Theme] = Field(default=[])
    suggested_actions: list[SuggestedAction] = Field(default=[])
    related_thought_ids: list[str] = Field(default=[])

class AnalysisMetadata(BaseModel):
    tokens_used: int
    processing_time_ms: int
    model_version: str
    timestamp: str

class SuccessResponse(BaseModel):
    success: bool = True
    analysis: Analysis
    metadata: AnalysisMetadata
```

---

## Response Schema (Failure)

```python
class ErrorDetails(BaseModel):
    request_id: str
    backend_name: str
    error_code: str  # INVALID_INPUT, TIMEOUT, RATE_LIMITED, UNAVAILABLE, etc.
    error_message: str
    suggestion: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetails
    metadata: Optional[dict] = None
```

**Error Codes**:
| Code | Meaning | Recoverable |
|------|---------|-------------|
| INVALID_INPUT | Content too long, etc. | No |
| TIMEOUT | Exceeded timeout_seconds | Yes |
| RATE_LIMITED | Backend rate-limited | Yes |
| UNAVAILABLE | Service down | Yes |
| CONTEXT_OVERFLOW | Content exceeds context | No |
| INTERNAL_ERROR | Unexpected error | Maybe |
| MALFORMED_RESPONSE | Invalid response | No |

---

## Protocol Guarantees

Every implementation must guarantee:
1. **Idempotent**: Same request_id always returns same result
2. **Atomic**: Either fully succeeds or fully fails
3. **Bounded**: Completes within timeout_seconds
4. **Traceable**: Every response includes request_id
5. **Validated**: Output matches schema

---

## Backend Registry

```python
class AIBackendRegistry:
    """Registry of available AI backends"""
    
    @classmethod
    def register(cls, name: str, backend: AIBackend) -> None:
        """Register a backend"""
    
    @classmethod
    def get(cls, name: str) -> AIBackend:
        """Retrieve backend by name"""
    
    @classmethod
    def list_available(cls) -> list[str]:
        """List all registered backends"""
```

---

## File Organization

```
src/services/ai_backends/
├── __init__.py
├── models.py               # Request/Response schemas
├── base.py                 # AIBackend protocol
├── claude_backend.py       # ClaudeBackend
├── ollama_backend.py       # OllamaBackend
├── mock_backend.py         # MockBackend
├── registry.py             # BackendRegistry
└── exceptions.py           # Custom exceptions

tests/unit/ai_backends/
├── test_protocol_compliance.py
├── test_claude_backend.py
├── test_ollama_backend.py
├── test_mock_backend.py
└── test_registry.py
```

---

## Testing Strategy

### Unit Tests: Protocol Compliance
All backends must pass the same tests:
- Response schema validation
- Input validation (oversized, empty content)
- Timeout enforcement
- Error code mapping
- request_id echoed in response

### Integration Tests: Real Ollama
- Verify Ollama at 192.168.7.187:11434 is reachable
- Test analysis quality
- Test error scenarios

---

## Dependencies

No new packages needed. Uses:
- pydantic (already in requirements.txt)
- anthropic (already in requirements.txt)
- httpx or aiohttp (for async HTTP to Ollama)
- asyncio (standard library)

---

## Success Criteria

✅ All three backends implement AIBackend protocol
✅ Registry can register and retrieve backends
✅ Request/Response validation with Pydantic
✅ Error handling for all error codes
✅ Timeout enforcement works
✅ Unit tests pass (protocol compliance)
✅ Integration tests pass (real Ollama)
✅ Docstrings on all functions
✅ Type hints throughout
✅ No circular dependencies

---

## Notes for Sonnet

1. Keep it simple - backends wrap APIs, validate, return schemas
2. Protocol first - all implementations must satisfy it exactly
3. Error mapping - map backend-specific errors to standard codes
4. Async throughout - all I/O is async
5. Mock is important - heavily used in tests
6. Production quality - ready for immediate use
