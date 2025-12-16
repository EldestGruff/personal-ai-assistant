# Personal AI Assistant - Pluggable Backends Living Spec

**Version:** 1.0  
**Status:** Foundation Design (Ready for Integration into Phase 2B)  
**Last Updated:** December 15, 2025  
**Audience:** Architecture review, implementation planning, Sonnet/Opus code generation  
**Scope:** AI backend abstraction, primary/secondary failover, statistical comparison, graceful degradation

---

## Table of Contents

1. [Introduction: The Problem](#introduction-the-problem)
2. [Why Pluggable Backends Matter for PAI](#why-pluggable-backends-matter-for-pai)
3. [Identifying Boundaries](#identifying-boundaries)
4. [Core Protocols](#core-protocols)
5. [Implementation Patterns](#implementation-patterns)
6. [Decision Making Framework](#decision-making-framework)
7. [Testing Strategy](#testing-strategy)
8. [Phase Integration (2A/2B/2C)](#phase-integration)
9. [Monitoring & Observability](#monitoring--observability)
10. [Version Roadmap](#version-roadmap)
11. [Implementation Checklist](#implementation-checklist)

---

## Introduction: The Problem

**Current State** (from Phase 2A specs):
- Consciousness check endpoint calls Claude directly
- If Claude API is down → no analysis works
- If rate-limited → users wait
- If costs spike → no cost optimization available
- If you want to test locally → you must modify the core logic

**What We Want**:
- Claude as primary (fast, capable, cloud-based)
- Local model as secondary (free, private, always available)
- Option to run both simultaneously and compare results
- Seamless swapping based on config, not code changes
- Core logic that doesn't know (or care) which backend it's using

**The Arcade Cartridge Metaphor** 🎮:

Think of 1980s arcade cabinets. Each cabinet is a standardized interface:
- Joystick input (same for all games)
- Screen output (same for all games)
- Sound system (same for all games)

You swap ROM cartridges—some have Pac-Man, some have Donkey Kong, some have Street Fighter. The cabinet doesn't change. The games don't know about the cabinet's internals. But swapping cartridges lets you completely change what the cabinet does.

**That's what we're building for PAI.**

The "cabinet" is your thought processing system. The "cartridges" are AI backends (Claude, Ollama, Gemini). Swap them at configuration time. Everything else stays the same.

---

## Why Pluggable Backends Matter for PAI

### Practical Reasons

1. **Resilience**: Claude unavailable? Degrade to local model.
2. **Cost Optimization**: Cheap thoughts → local model. Complex analysis → Claude.
3. **Privacy**: No network required → local model always available on TrueNAS.
4. **Testing**: Mock backend for unit tests. No API calls, deterministic results.
5. **Comparison**: Run Claude and Ollama simultaneously, compare quality.
6. **Evolution**: Add Gemini next year without touching core logic.

### Strategic Reasons

1. **Control**: You own your infrastructure. Less dependence on external services.
2. **Learning**: Understand how different models handle the same problems.
3. **Future-Proofing**: New models emerge constantly. Protocol-based design adapts.
4. **Team Growth**: When you hire devs, they can add new backends without understanding core logic.

### Business Reasons (Even for Personal Projects)

1. **Cost**: Local models are free after initial setup.
2. **Latency**: Local models respond instantly (useful for fast consciousness checks).
3. **Benchmarking**: "Does Claude's analysis justify its cost vs. free local model?"

---

## Identifying Boundaries

Where do we put protocol boundaries in PAI? Look for places where you might want to:
- Swap implementations
- Add new implementations
- Test in isolation
- Make decisions at runtime

### Boundary 1: AI Backend (Primary)

**What**: The interface to any LLM provider.

**Current assumption**: Claude only.

**Future state**: Claude, Ollama, Gemini, custom fine-tuned models, etc.

**Responsibility**: "Accept a request for analysis. Return results structured according to protocol."

**Why boundary here**: You'll definitely want to swap this. Probably soon (local fallback).

---

### Boundary 2: Thought Analyzer (Secondary)

**What**: The service that coordinates analysis of thoughts.

**Current architecture**: Could call Claude directly, making tight coupling.

**Better architecture**: Call through AIBackend protocol.

**Responsibility**: "Take a thought. Delegate to appropriate backend. Return analysis results."

**Why boundary here**: Separates orchestration (which backend? when?) from execution (actually analyzing).

---

### Boundary 3: Backend Selector (Decision Logic)

**What**: The logic that decides which backend(s) to use.

**Examples of logic**:
```
- Simple thoughts (< 100 chars) → use local model (fast, free)
- Complex thoughts (> 100 chars) → use Claude (better quality)
- Consciousness check (analyzing 20 thoughts) → use primary backend
- Running comparison → use both Claude and local, compare results
- Claude rate-limited → fallback to local
- Network down → local only
```

**Why boundary here**: Decision rules change. You'll iterate on this.

---

### Boundary 4: Analysis Results Comparator

**What**: When running multiple backends simultaneously, compare results.

**Examples of comparison**:
- Do both models identify the same themes?
- Do they agree on suggested actions?
- What's the confidence score for each?
- Which analysis is more actionable?

**Why boundary here**: Comparison logic is complex enough to test separately.

---

## Core Protocols

Protocols are contracts. They say: "I will provide this request. I promise to handle it like this. Here's what you'll get back. Here are error cases we've identified."

### Protocol 1: AIBackend (The Main One)

**Responsibility**: Accept a thought analysis request. Return analysis results.

**Request**:
```json
{
  "request_id": "req_abc123def456",
  "thought_content": "Should optimize the email spam filter",
  "context": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "recent_thoughts_count": 5,
    "analysis_depth": "deep"
  },
  "timeout_seconds": 30,
  "model_hint": null,
  "include_confidence": true
}
```

**Field Details**:
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `request_id` | UUID | Yes | Trace requests end-to-end |
| `thought_content` | string | Yes | 1-5000 chars |
| `context` | object | No | Background info for analysis |
| `timeout_seconds` | int | No | Max time to wait (default: 30, max: 60) |
| `model_hint` | string | No | Suggestion ("fast", "quality", "cheap") |
| `include_confidence` | bool | No | Return confidence scores (default: true) |

---

**Response (Success)**:
```json
{
  "success": true,
  "analysis": {
    "request_id": "req_abc123def456",
    "thought_id": "a8f4c2b1-9d7e-4e3f-8b6c-1a2d3e4f5g6h",
    "backend_used": "claude-sonnet-4-5",
    "summary": "User is thinking about improving email automation. Related to earlier thoughts about system optimization.",
    "themes": [
      {
        "theme": "email automation",
        "confidence": 0.95
      },
      {
        "theme": "system optimization",
        "confidence": 0.87
      }
    ],
    "suggested_actions": [
      {
        "action": "Create task for email filter improvements",
        "priority": "medium",
        "confidence": 0.82
      }
    ],
    "related_thought_ids": [
      "related-id-1",
      "related-id-2"
    ]
  },
  "metadata": {
    "tokens_used": 234,
    "processing_time_ms": 1250,
    "model_version": "claude-sonnet-4-5-20250929",
    "timestamp": "2025-12-15T14:30:00.123456Z"
  }
}
```

---

**Response (Failure)**:
```json
{
  "success": false,
  "error": {
    "code": "TIMEOUT",
    "message": "Analysis did not complete within 30 seconds",
    "details": {
      "request_id": "req_abc123def456",
      "timeout_seconds": 30,
      "backend": "claude-sonnet-4-5",
      "suggestion": "Try increasing timeout or using a faster backend"
    }
  },
  "metadata": {
    "timestamp": "2025-12-15T14:30:00.123456Z"
  }
}
```

---

**Guaranteed Behaviors**:
- **Idempotent**: Same request_id always returns same result (or error)
- **Atomic**: Either fully succeeds or fully fails (no partial analysis)
- **Bounded**: Completes within timeout_seconds or returns TIMEOUT error
- **Traceable**: Every response includes request_id for end-to-end tracing
- **Validated**: Output always matches protocol schema

**Error Codes**:
| Code | Meaning | Recoverable | Suggestion |
|------|---------|-------------|-----------|
| `TIMEOUT` | Exceeded timeout_seconds | Yes | Retry with longer timeout or different backend |
| `INVALID_INPUT` | Content > 5000 chars or malformed | No | Fix request before retrying |
| `RATE_LIMITED` | Backend rate-limited | Yes | Wait and retry, or use different backend |
| `UNAVAILABLE` | Backend service down | Yes | Failover to secondary backend |
| `INTERNAL_ERROR` | Unexpected backend error | Maybe | Escalate to logs, retry later |
| `CONTEXT_OVERFLOW` | Backend context window exceeded | No | Summarize context and retry |

---

### Protocol 2: BackendSelector

**Responsibility**: Decide which backend(s) to use and in what order.

**Request**:
```json
{
  "request_id": "req_abc123def456",
  "thought_length": 45,
  "analysis_type": "consciousness_check",
  "available_backends": ["claude", "ollama"],
  "user_preferences": {
    "prefer_local": false,
    "enable_comparison": false,
    "max_cost_cents": 5
  }
}
```

**Response**:
```json
{
  "decision": "SEQUENTIAL",
  "backends": [
    {
      "name": "claude",
      "role": "primary",
      "timeout_seconds": 20,
      "model_hint": "quality"
    }
  ],
  "fallback_backends": [
    {
      "name": "ollama",
      "role": "secondary",
      "timeout_seconds": 10,
      "model_hint": "fast"
    }
  ],
  "reasoning": "Primary backend available. Use Claude for quality. Fallback to local if Claude fails."
}
```

**Decision Types**:
- `PRIMARY_ONLY`: Use primary backend, don't fallback
- `SEQUENTIAL`: Try primary, if fails try secondary
- `PARALLEL`: Run both simultaneously, combine results
- `COST_OPTIMIZED`: Use cheapest option that meets quality threshold

---

### Protocol 3: AnalysisComparator

**Responsibility**: When running multiple backends, compare results.

**Request**:
```json
{
  "request_id": "req_abc123def456",
  "primary_analysis": { /* AIBackend response */ },
  "secondary_analysis": { /* AIBackend response */ },
  "comparison_depth": "themes"  // "quick", "themes", "detailed"
}
```

**Response**:
```json
{
  "agreement_score": 0.85,
  "theme_agreement": [
    {
      "theme": "email automation",
      "primary_confidence": 0.95,
      "secondary_confidence": 0.78,
      "agreement": true
    }
  ],
  "divergences": [
    {
      "type": "missing_theme",
      "primary_has": "system optimization",
      "secondary_has": false,
      "significance": "medium"
    }
  ],
  "recommendation": "Results highly aligned. Primary analysis (Claude) is reliable here.",
  "which_to_use": "primary"
}
```

---

### Protocol 4: FallbackOrchestrator

**Responsibility**: Handle failures gracefully.

**Request**:
```json
{
  "request_id": "req_abc123def456",
  "primary_attempt": {
    "backend": "claude",
    "error": "RATE_LIMITED"
  },
  "fallback_options": ["ollama", "mock"]
}
```

**Response**:
```json
{
  "action": "RETRY_WITH_FALLBACK",
  "next_backend": "ollama",
  "retry_count": 1,
  "max_retries": 3,
  "timeout_seconds": 10
}
```

**Actions**:
- `RETRY_WITH_FALLBACK`: Try secondary backend
- `CIRCUIT_BREAK`: Backend is bad, don't retry soon
- `ESCALATE`: Give up, return partial result to user
- `DEGRADE`: Return cached result from earlier analysis

---

## Implementation Patterns

How do you actually build this? Here are proven patterns.

### Pattern 1: Backend Registry

Keep a registry of available backends. Backends register themselves on startup.

```python
# src/services/ai_backends/registry.py

class AIBackendRegistry:
    """Registry of available AI backends"""
    
    _backends: dict[str, AIBackend] = {}
    
    @classmethod
    def register(cls, name: str, backend: AIBackend):
        """Register a backend"""
        cls._backends[name] = backend
    
    @classmethod
    def get(cls, name: str) -> AIBackend:
        """Retrieve a backend by name"""
        if name not in cls._backends:
            raise BackendNotFoundError(f"Backend '{name}' not registered")
        return cls._backends[name]
    
    @classmethod
    def list_available(cls) -> list[str]:
        """List all registered backends"""
        return list(cls._backends.keys())
```

**Usage**:
```python
# On startup, register available backends

from src.services.ai_backends import (
    ClaudeBackend,
    OllamaBackend,
    MockBackend
)

registry = AIBackendRegistry()
registry.register("claude", ClaudeBackend(api_key=os.getenv("ANTHROPIC_API_KEY")))
registry.register("ollama", OllamaBackend(base_url="http://localhost:11434"))
registry.register("mock", MockBackend())
```

---

### Pattern 2: Primary/Secondary with Fallback

Try primary. If it fails with a recoverable error, try secondary.

```python
# src/services/thought_analyzer.py

class ThoughtAnalyzer:
    def __init__(self, registry: AIBackendRegistry, selector: BackendSelector):
        self.registry = registry
        self.selector = selector
    
    async def analyze(self, thought: Thought) -> AnalysisResult:
        """Analyze a thought with fallback logic"""
        
        request = AnalysisRequest(
            request_id=uuid4(),
            thought_content=thought.content,
            context={"user_id": thought.user_id}
        )
        
        # Decide which backends to use
        decision = self.selector.select_backends(request)
        
        # Try primary backend
        primary_backend = self.registry.get(decision.backends[0].name)
        try:
            result = await primary_backend.analyze(request)
            logger.info(f"Analysis succeeded with {decision.backends[0].name}")
            return result
        except RecoverableError as e:
            logger.warning(f"Primary backend failed: {e}. Trying fallback.")
        
        # Try fallback backends
        for fallback in decision.fallback_backends:
            fallback_backend = self.registry.get(fallback.name)
            try:
                result = await fallback_backend.analyze(request)
                logger.info(f"Analysis succeeded with fallback {fallback.name}")
                return result
            except Exception as e:
                logger.warning(f"Fallback {fallback.name} also failed: {e}")
                continue
        
        # All backends failed
        logger.error(f"All backends failed for request {request.request_id}")
        raise AnalysisFailedError("No available backend could analyze the thought")
```

---

### Pattern 3: Parallel Comparison

Run multiple backends simultaneously, compare results.

```python
# src/services/backend_comparator.py

class BackendComparator:
    async def compare(
        self,
        request: AnalysisRequest,
        backends: list[str]
    ) -> ComparisonResult:
        """Run multiple backends in parallel, compare results"""
        
        registry = AIBackendRegistry()
        
        # Run all backends in parallel
        results = await asyncio.gather(
            *[
                self._run_with_timeout(registry.get(name), request, name)
                for name in backends
            ],
            return_exceptions=True
        )
        
        # Separate successes and failures
        successful = []
        for name, result in zip(backends, results):
            if isinstance(result, Exception):
                logger.warning(f"Backend {name} failed: {result}")
            else:
                successful.append((name, result))
        
        if not successful:
            raise AnalysisFailedError("All backends failed in comparison")
        
        # Compare results
        if len(successful) == 1:
            return ComparisonResult(
                agreement_score=1.0,
                which_to_use=successful[0][0],
                note="Only one backend succeeded"
            )
        
        # Calculate agreement between results
        primary_result = successful[0][1]
        secondary_result = successful[1][1]
        
        agreement = self._calculate_agreement(primary_result, secondary_result)
        
        return ComparisonResult(
            agreement_score=agreement.score,
            theme_agreement=agreement.themes,
            divergences=agreement.divergences,
            which_to_use=agreement.recommended_backend
        )
```

---

### Pattern 4: Cost-Optimized Selection

Route to cheapest backend that meets quality threshold.

```python
# src/services/backend_selector.py

class CostOptimizedSelector(BackendSelector):
    def select_backends(self, request: AnalysisRequest) -> BackendDecision:
        """Select backend based on cost and quality constraints"""
        
        # Simple heuristics based on thought size
        thought_length = len(request.thought_content)
        
        if thought_length < 100:
            # Short thoughts: use fast, cheap backend
            return BackendDecision(
                decision="PRIMARY_ONLY",
                backends=[BackendChoice(name="ollama", role="primary")],
                reasoning="Short thought, use fast local model to save costs"
            )
        elif thought_length < 500:
            # Medium thoughts: prefer local, fallback to Claude
            return BackendDecision(
                decision="SEQUENTIAL",
                backends=[BackendChoice(name="ollama", role="primary")],
                fallback_backends=[BackendChoice(name="claude", role="secondary")],
                reasoning="Medium thought, try local first. Escalate to Claude if needed"
            )
        else:
            # Long thoughts: use Claude for quality, fallback to local
            return BackendDecision(
                decision="SEQUENTIAL",
                backends=[BackendChoice(name="claude", role="primary")],
                fallback_backends=[BackendChoice(name="ollama", role="secondary")],
                reasoning="Long thought needs quality. Use Claude. Fallback if rate-limited"
            )
```

---

## Decision Making Framework

When should you use each pattern?

### Flowchart: Which Backend Pattern?

```
START: New analysis request arrives

Decision 1: Do we need high confidence?
  → YES: Use PRIMARY_ONLY (Claude)
  → NO: Continue

Decision 2: Do we have budget constraints?
  → YES: Use COST_OPTIMIZED (routes to cheapest)
  → NO: Continue

Decision 3: Is this a risky decision (e.g., suggest deletion)?
  → YES: Use PARALLEL + COMPARATOR (verify with multiple models)
  → NO: Continue

Decision 4: Is the primary backend unavailable?
  → YES: Use SEQUENTIAL + FALLBACK (try primary, fallback if fails)
  → NO: Use PRIMARY_ONLY

FALLTHROUGH: Use SEQUENTIAL (try primary, fallback available)
```

---

### Decision Matrix

| Scenario | Pattern | Reasoning |
|----------|---------|-----------|
| Consciousness check (summary) | SEQUENTIAL | Quick analysis, fallback if slow |
| Creating a task (might be wrong) | PARALLEL + COMPARE | Verify before committing |
| Simple thought (< 50 chars) | COST_OPTIMIZED | Cheap is fine here |
| Complex thought (> 1000 chars) | PRIMARY_ONLY (Claude) | Needs Claude quality |
| Claude likely rate-limited | FALLBACK_ONLY | Skip Claude, use Ollama |
| Testing | MOCK_BACKEND | No API calls needed |
| A/B testing backends | PARALLEL + COMPARE | Compare results systematically |

---

## Testing Strategy

How do you test this without breaking things?

### Layer 1: Unit Tests (Protocol Compliance)

Test each backend implementation against the protocol.

```python
# tests/unit/test_claude_backend.py

class TestClaudeBackendProtocol:
    """Verify Claude backend conforms to AIBackend protocol"""
    
    async def test_returns_valid_response_structure(self):
        """Response matches protocol schema"""
        backend = ClaudeBackend(api_key="test-key")
        
        request = AnalysisRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        result = await backend.analyze(request)
        
        # Verify response structure
        assert result.success == True
        assert result.analysis.request_id == request.request_id
        assert isinstance(result.analysis.summary, str)
        assert isinstance(result.analysis.themes, list)
    
    async def test_rejects_oversized_content(self):
        """Validates max content length"""
        backend = ClaudeBackend(api_key="test-key")
        
        oversized_content = "x" * 6000  # Exceeds 5000 char limit
        request = AnalysisRequest(
            request_id="req-123",
            thought_content=oversized_content
        )
        
        result = await backend.analyze(request)
        
        assert result.success == False
        assert result.error.code == "INVALID_INPUT"
    
    async def test_respects_timeout(self):
        """Honors timeout_seconds parameter"""
        backend = ClaudeBackend(api_key="test-key")
        
        request = AnalysisRequest(
            request_id="req-123",
            thought_content="Test",
            timeout_seconds=1
        )
        
        # If this doesn't timeout, backend violates protocol
        start = time.time()
        result = await backend.analyze(request)
        elapsed = time.time() - start
        
        assert elapsed < 1.1  # Small buffer for cleanup
```

---

### Layer 2: Integration Tests (Interaction)

Test how backends work together.

```python
# tests/integration/test_fallback_logic.py

class TestFallbackLogic:
    """Test PRIMARY + FALLBACK pattern"""
    
    async def test_falls_back_when_primary_fails(self):
        """If primary fails, secondary is tried"""
        registry = AIBackendRegistry()
        registry.register("failing", FailingBackend())  # Always fails
        registry.register("working", WorkingBackend())  # Works
        
        analyzer = ThoughtAnalyzer(registry, SelectorSpy())
        
        result = await analyzer.analyze(Thought(
            content="Test",
            user_id="user-123"
        ))
        
        assert result.success == True
        assert "working" in str(result)  # Came from fallback
    
    async def test_uses_primary_when_available(self):
        """Primary is preferred when working"""
        registry = AIBackendRegistry()
        registry.register("primary", MockBackend(name="primary"))
        registry.register("fallback", MockBackend(name="fallback"))
        
        analyzer = ThoughtAnalyzer(registry, AlwaysPrimary())
        
        result = await analyzer.analyze(Thought(content="Test", user_id="user-123"))
        
        assert "primary" in str(result)
```

---

### Layer 3: Evaluation Tests (Quality)

Test the quality of analysis with real models.

```python
# tests/evaluation/test_analysis_quality.py

class TestAnalysisQuality:
    """Evaluate quality of analysis across backends"""
    
    async def test_identifies_themes_consistently(self):
        """Both backends should identify major themes"""
        
        # Reference: a thought with clear themes
        reference_thought = Thought(
            content="Struggling with email productivity. Getting too many spam emails. "
                   "Need better filtering and organization system.",
            user_id="user-123"
        )
        
        backends = ["claude", "ollama"]
        results = {}
        
        for backend_name in backends:
            registry = AIBackendRegistry()
            backend = registry.get(backend_name)
            
            result = await backend.analyze(AnalysisRequest(
                request_id=str(uuid4()),
                thought_content=reference_thought.content
            ))
            results[backend_name] = result
        
        # Both should identify "email" as a theme
        claude_themes = {t.theme for t in results["claude"].analysis.themes}
        ollama_themes = {t.theme for t in results["ollama"].analysis.themes}
        
        # Using a strong evaluator to check consistency
        evaluator = StrongLLMEvaluator()  # Use a real, strong model to judge
        assert evaluator.check_theme_consistency(claude_themes, ollama_themes) > 0.8
```

---

### Layer 4: Regression Tests (Deterministic Replay)

Cache backend responses so tests remain deterministic.

```python
# tests/conftest.py

@pytest.fixture
def vcr_config():
    return {
        "filter_headers": ["authorization"],  # Don't cache API keys
        "decode_compressed_response": True,
        "cassette_library_dir": "tests/cassettes",
    }

# Usage in tests:
@pytest.mark.vcr
async def test_consciousness_check_quality(vcr):
    """VCR records real Claude response, replays deterministically"""
    
    with vcr.use_cassette("consciousness_check.yaml"):
        result = await consciousness_check(
            recent_thoughts=[...],
            backend="claude"
        )
        
        assert result.success
        assert len(result.analysis.themes) > 0
        assert len(result.analysis.suggested_actions) > 0
```

On first run, VCR records the actual Claude response. On subsequent runs, it replays the exact same response, making the test deterministic while verifying Claude quality.

---

## Phase Integration (2A/2B/2C)

How does this protocol layer integrate with your phases?

### Phase 2A: Foundation (Data Models, API, Database)

**No changes needed to Phase 2A specs.** The protocols sit *on top* of these.

**What we do**:
- Phase 2A generates data models, API endpoints, database schema
- We overlay backend protocols on top
- The API endpoints (consciousness-check, analyze) use these protocols internally

**Mapping**:
```
Current (Phase 2A):
  POST /api/v1/consciousness-check
    → calls Claude directly
    → returns analysis

Future (with protocols):
  POST /api/v1/consciousness-check
    → calls BackendSelector
    → calls AIBackend (which could be Claude, Ollama, etc.)
    → returns analysis

Phase 2A code doesn't change. We wrap it with protocols.
```

---

### Phase 2B: Claude Integration + Service Layer

**This is where pluggable backends shine.**

**What Phase 2B will include** (expanded):
- `src/services/ai_backends/base.py` - AIBackend protocol/interface
- `src/services/ai_backends/claude_backend.py` - Claude implementation
- `src/services/ai_backends/ollama_backend.py` - Local model implementation
- `src/services/ai_backends/mock_backend.py` - For testing
- `src/services/ai_backends/registry.py` - Backend registry
- `src/services/backend_selector.py` - Decision logic (which backend to use)
- `src/services/backend_comparator.py` - Compare multiple backends
- `src/services/thought_analyzer.py` - Updated to use protocols

**How this works**:
```
Existing API endpoint (consciousness-check)
  ↓
ThoughtAnalyzer service (NEW)
  ↓
BackendSelector (NEW) - "Which backend should I use?"
  ↓
AIBackend (interface) - "Analyze this"
  ↓
Concrete implementation (Claude, Ollama, Mock)
```

The API endpoint doesn't change. The backend swapping happens transparently below.

---

### Phase 2C: Docker & TrueNAS Deployment

**Configuration-based backend selection** (environment variables).

```dockerfile
# docker-compose.yml

services:
  personal-ai:
    image: personal-ai:latest
    environment:
      # Which backends are available?
      AVAILABLE_BACKENDS: "claude,ollama"
      
      # Primary backend
      PRIMARY_BACKEND: "claude"
      CLAUDE_API_KEY: ${ANTHROPIC_API_KEY}
      
      # Fallback backend
      SECONDARY_BACKEND: "ollama"
      OLLAMA_BASE_URL: "http://ollama:11434"
      
      # Selection strategy
      BACKEND_SELECTION_STRATEGY: "cost_optimized"
```

**Deployment scenarios**:

**Scenario 1: Cloud-First (Default)**
```
PRIMARY: Claude (powerful, cloud)
FALLBACK: Local Ollama (always available)
STRATEGY: Use Claude, fallback if issues
```

**Scenario 2: Local-First (Privacy)**
```
PRIMARY: Ollama (private, free)
FALLBACK: Claude (fallback for hard problems)
STRATEGY: Use Ollama first, escalate if needed
```

**Scenario 3: Cost-Optimized**
```
PRIMARY: Ollama (free)
FALLBACK: Claude (expensive)
STRATEGY: Route by cost - use Ollama unless quality needed
```

**Scenario 4: A/B Testing**
```
PRIMARY: Claude
FALLBACK: Ollama
STRATEGY: Run both, compare, log metrics
```

All of this changes by editing `.env`. No code changes needed.

---

## Monitoring & Observability

How do you know which backend is being used? What's failing?

### Metrics to Track

**Per Backend**:
- Request count (how often is this backend used?)
- Success rate (what % of requests succeed?)
- Response time (how fast is this backend?)
- Error rate (how often does it fail?)
- Tokens used (for Claude, track API cost)

**Cross-Backend**:
- Which backend succeeded when?
- Fallback usage frequency (how often does primary fail?)
- Comparison agreement (when running both, how often do they agree?)

### Implementation: Metrics Service

```python
# src/services/metrics.py

class BackendMetrics:
    """Track backend performance metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "response_time_ms": [],
            "tokens_used": 0,
        })
    
    def record_success(self, backend_name: str, response_time_ms: int, tokens: int = 0):
        """Record successful request"""
        metrics = self.metrics[backend_name]
        metrics["requests_total"] += 1
        metrics["requests_success"] += 1
        metrics["response_time_ms"].append(response_time_ms)
        metrics["tokens_used"] += tokens
    
    def get_success_rate(self, backend_name: str) -> float:
        """Success rate for a backend"""
        metrics = self.metrics[backend_name]
        if metrics["requests_total"] == 0:
            return 0.0
        return metrics["requests_success"] / metrics["requests_total"]
    
    def get_avg_response_time(self, backend_name: str) -> float:
        """Average response time"""
        response_times = self.metrics[backend_name]["response_time_ms"]
        if not response_times:
            return 0.0
        return sum(response_times) / len(response_times)
```

### Logging: Structured Events

Every backend call should log structured information.

```python
# When calling a backend
logger.info("backend_request", extra={
    "request_id": request.request_id,
    "backend": "claude",
    "thought_length": len(thought.content),
    "timeout_seconds": request.timeout_seconds,
})

# When backend responds
logger.info("backend_response", extra={
    "request_id": request.request_id,
    "backend": "claude",
    "success": True,
    "response_time_ms": 1250,
    "tokens_used": 234,
})

# When backend fails
logger.warning("backend_failure", extra={
    "request_id": request.request_id,
    "backend": "claude",
    "error_code": "RATE_LIMITED",
    "error_message": "Rate limit exceeded",
    "will_retry_with": "ollama",
})
```

These structured logs let you build dashboards, alerts, and queries like:
- "What's the success rate of Claude vs. Ollama?"
- "How much does Claude analysis cost per thought?"
- "When does Ollama fail?"
- "How often do we fall back to secondary?"

---

## Version Roadmap

Protocols evolve. Plan for it.

### Version 1.0 (Foundation)

**Current State**:
- AIBackend protocol with request/response schema
- Primary/Secondary fallback
- Basic error codes
- Claude and Ollama implementations

**Compatibility**: 🟢 No existing implementations, this is v1.0

---

### Version 1.1 (Q1 2026)

**Additions** (backward compatible):
- `comparison_strategy` field in BackendSelector (how to combine results)
- `cost_estimate` field in responses (show API cost)
- Optional `prefer_local` hint in requests

**New Implementations**:
- Gemini backend (Google)
- Custom fine-tuned Claude (if available)

**Deprecations**: None yet

---

### Version 2.0 (Q2 2026)

**Major Changes** (breaks v1.0):
- Streaming responses (for long analysis)
- Async callbacks (for analysis that takes time)
- Multi-thought batching (analyze 10 thoughts in one call)

**Migration Path**: v1.0 clients must update. Estimated 2-hour migration.

---

### Version 3.0 (Q4 2026)

**Speculative** (requires further analysis):
- Multi-model ensemble (combine results from 5 models)
- Active learning (user feedback improves model selection)
- Custom evaluation metrics
- Integration with a model training pipeline

---

## Implementation Checklist

Ready to build this? Here's the order.

### Phase 2B: Backend Abstraction (Week 1-2)

- [ ] Define AIBackend protocol (interface/base class)
- [ ] Implement ClaudeBackend (calls Anthropic API)
- [ ] Implement OllamaBackend (calls local Ollama)
- [ ] Implement MockBackend (deterministic for testing)
- [ ] Create BackendRegistry (register/retrieve backends)
- [ ] Write unit tests (protocol compliance)
- [ ] Document backend implementations

**Output**: Backend abstraction layer, testable in isolation.

---

### Phase 2B: Backend Selection (Week 2-3)

- [ ] Define BackendSelector protocol
- [ ] Implement SimpleSelector (always use primary)
- [ ] Implement SequentialSelector (try primary, fallback)
- [ ] Implement CostOptimizedSelector (smart routing)
- [ ] Write tests (selection logic)
- [ ] Document selection strategies

**Output**: Smart backend selection, configured at runtime.

---

### Phase 2B: Integration (Week 3)

- [ ] Update ThoughtAnalyzer to use backends
- [ ] Update consciousness-check endpoint to use protocols
- [ ] Integrate BackendSelector into request flow
- [ ] Write integration tests (fallback scenarios)
- [ ] Add logging/metrics

**Output**: Full protocol layer, backward compatible with API.

---

### Phase 2C: Deployment Config (Week 4)

- [ ] Add environment variables for backend selection
- [ ] Create docker-compose with multiple backend options
- [ ] Document deployment scenarios (cloud-first, local-first, cost-optimized)
- [ ] Add health checks (verify backends are available)
- [ ] Write deployment tests

**Output**: Configuration-driven deployment.

---

### Phase 2C+: Optional Enhancements

- [ ] Backend comparison (run both, compare results)
- [ ] A/B testing framework
- [ ] Cost tracking (Anthropic API usage)
- [ ] Performance dashboard
- [ ] Automated backend selection (learn which backend works best)

---

## Summary: Why This Matters

Without protocols, your PAI system is tightly coupled to Claude. 

```
❌ Without Protocols:
consciousness_check() → Claude API → response
  Problem: Claude down? → System down
  Problem: Rate limited? → Users wait
  Problem: Costs spike? → No mitigation
  Problem: Test? → Must mock Claude directly
```

With protocols, you decouple business logic from backend implementation.

```
✅ With Protocols:
consciousness_check() 
  → BackendSelector → "Which backend?"
  → AIBackend → "Analyze this"
  → ClaudeBackend OR OllamaBackend OR MockBackend
  
  Benefit: Claude down? Try Ollama
  Benefit: Rate limited? Route to local model
  Benefit: Testing? Use mock, no API calls
  Benefit: Add new backend? Just implement protocol
```

This is architecture that scales—not just in features, but in flexibility, resilience, and your ability to understand and maintain it.

---

## Next Steps

1. **Review this spec** - Does it align with your vision?
2. **Validate the protocols** - Do these contracts make sense?
3. **Plan Phase 2B** - Integration with existing specs?
4. **Begin implementation** - Start with backend abstraction?

This is a *living* spec. As you implement, gaps will emerge. Update it. Document what you learn. Share it with future developers (or future you).

---

**Document Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 15, 2025 | Initial foundation design |

**Status**: Ready for Phase 2B implementation planning.