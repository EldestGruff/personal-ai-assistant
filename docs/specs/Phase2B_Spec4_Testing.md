# Phase 2B Spec 4: Testing & Quality Assurance

**Status:** Ready for Code Generation  
**Target:** Claude Sonnet  
**Output:** Comprehensive test suite (unit, integration, evaluation)  
**Complexity:** Medium  
**Est. Lines of Code:** 800 (test code)

---

## Overview

This spec defines testing strategy for the pluggable backends system. After this spec:
- Unit tests verify each backend satisfies protocol
- Integration tests validate fallback and orchestration
- Evaluation tests check analysis quality
- VCR-based deterministic replay prevents breaking changes
- Test coverage >80% for all new code

---

## Test Architecture

```
tests/
├── unit/
│   ├── ai_backends/
│   │   ├── test_protocol_compliance.py
│   │   ├── test_claude_backend.py
│   │   ├── test_ollama_backend.py
│   │   ├── test_mock_backend.py
│   │   └── test_registry.py
│   ├── backend_selection/
│   │   ├── test_default_selector.py
│   │   ├── test_orchestrator.py
│   │   └── test_config.py
│   └── thought_analyzer/
│       └── test_refactored_analyzer.py
│
├── integration/
│   ├── test_ollama_real.py
│   ├── test_fallback_scenarios.py
│   ├── test_consciousness_v2_endpoint.py
│   ├── test_backend_health_checks.py
│   └── test_metrics_collection.py
│
├── evaluation/
│   ├── test_analysis_quality.py
│   └── test_theme_consistency.py
│
├── fixtures/
│   ├── backend_fixtures.py
│   ├── request_fixtures.py
│   └── cassettes/
│       ├── claude_consciousness_check.yaml
│       └── ollama_consciousness_check.yaml
│
└── conftest.py
```

---

## Unit Tests: Protocol Compliance

All backends must pass identical protocol compliance tests:

```python
# tests/unit/ai_backends/test_protocol_compliance.py

class TestProtocolCompliance:
    """All AIBackend implementations must satisfy these tests"""
    
    @pytest.fixture(params=["claude", "ollama", "mock"])
    def backend(self, request):
        """Parameterized: run against all backends"""
```

### Test Cases

1. **response_schema_matches_protocol**
   - Result is SuccessResponse or ErrorResponse
   - Has proper structure (analysis/metadata or error/metadata)

2. **request_id_echoed_in_response**
   - Response includes exact request_id from request

3. **respects_timeout_seconds**
   - Request completes within timeout_seconds
   - Doesn't exceed by more than 200ms

4. **rejects_oversized_content**
   - Content > 5000 chars → ErrorResponse with INVALID_INPUT

5. **rejects_empty_content**
   - Empty content → ErrorResponse with INVALID_INPUT

6. **response_contains_summary**
   - Success response has non-empty summary string

7. **response_contains_timestamp**
   - Response includes ISO8601 timestamp

---

## Unit Tests: Backend-Specific

### Claude Backend

```python
# tests/unit/ai_backends/test_claude_backend.py

class TestClaudeBackend:
    async def test_uses_correct_model(self, monkeypatch):
        """Verify uses expected Claude model"""
    
    async def test_maps_rate_limit_error(self, monkeypatch):
        """Claude RateLimitError → RATE_LIMITED"""
    
    async def test_parses_claude_response(self, monkeypatch):
        """Claude free-form text → structured response"""
```

### Ollama Backend

```python
# tests/unit/ai_backends/test_ollama_backend.py

class TestOllamaBackend:
    async def test_correct_endpoint(self, monkeypatch):
        """Calls POST /api/generate at 192.168.7.187:11434"""
    
    async def test_maps_connection_error(self, monkeypatch):
        """HTTP ConnectError → UNAVAILABLE"""
    
    async def test_parses_ollama_response(self, monkeypatch):
        """Ollama response → structured analysis"""
```

### Mock Backend

```python
# tests/unit/ai_backends/test_mock_backend.py

class TestMockBackend:
    async def test_mock_success_always_succeeds(self):
        """MockBackend('mock-success') always SuccessResponse"""
    
    async def test_mock_unavailable_always_fails(self):
        """MockBackend('mock-unavailable') always ErrorResponse"""
    
    async def test_mock_timeout_exceeds_deadline(self):
        """MockBackend('mock-timeout') sleep > timeout"""
```

---

## Integration Tests: Orchestration

```python
# tests/integration/test_fallback_scenarios.py

class TestFallbackScenarios:
    async def test_primary_succeeds_returns_result(self):
        """Primary succeeds → return its result"""
        # Register mock-success as primary
        # Orchestrator should return immediately
    
    async def test_fallback_used_when_primary_fails(self):
        """Primary fails (RATE_LIMITED) → try fallback"""
        # Primary: mock-unavailable
        # Fallback: mock-success
        # Should succeed with fallback
    
    async def test_non_recoverable_error_does_not_fallback(self):
        """INVALID_INPUT error → don't try fallback"""
        # Primary returns INVALID_INPUT
        # Fallback not called
```

---

## Integration Tests: Real Ollama

```python
# tests/integration/test_ollama_real.py

@pytest.mark.integration
class TestOllamaReal:
    """Test against real Ollama at 192.168.7.187:11434"""
    
    @pytest.mark.skipif(
        not os.getenv("TEST_REAL_OLLAMA"),
        reason="Requires REAL Ollama. Set TEST_REAL_OLLAMA=1"
    )
    async def test_ollama_available(self):
        """Ollama reachable and responds"""
    
    async def test_ollama_produces_analysis(self):
        """Ollama returns reasonable analysis output"""
```

---

## Evaluation Tests: Quality

```python
# tests/evaluation/test_analysis_quality.py

@pytest.mark.evaluation
class TestAnalysisQuality:
    async def test_themes_consistency_across_backends(self, vcr):
        """Both backends identify major themes"""
        # Use VCR cassette for deterministic replay
        # Compare theme extraction between Claude and Ollama
    
    async def test_suggested_actions_are_reasonable(self, vcr):
        """Actions should be actionable and clear"""
```

---

## Testing Fixtures

### conftest.py

```python
# tests/conftest.py

@pytest.fixture
def backend_registry():
    """Fresh registry for each test"""
    registry = AIBackendRegistry()
    registry.register("mock-success", MockBackend("mock-success"))
    registry.register("mock-failure", MockBackend("mock-unavailable"))
    return registry

@pytest.fixture
def backend_selector():
    """Mock selector for orchestrator tests"""
    return Mock(spec=BackendSelector)

@pytest.fixture
def backend_orchestrator(backend_registry, backend_selector):
    """Orchestrator with test backends"""
    return BackendOrchestrator(backend_registry, backend_selector)

@pytest.fixture
def vcr_config():
    """VCR configuration for deterministic replay"""
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "decode_compressed_response": True,
        "cassette_library_dir": "tests/fixtures/cassettes",
    }
```

---

## Test Markers

```
# pytest.ini (updated)

[pytest]
markers =
    unit: Fast unit tests (no I/O)
    integration: Integration tests (may use real services)
    evaluation: Quality evaluation tests (may be slow)
```

---

## Coverage Requirements

Target: >80% coverage for all new code

```bash
pytest tests/ --cov=src/services/ai_backends \
               --cov=src/services/backend_selection \
               --cov-report=html
```

Expected:
- ai_backends/: >85%
- backend_selection/: >80%
- Overall: >80%

---

## VCR for Deterministic Replay

Record real API responses once, replay deterministically:

```python
@pytest.mark.vcr
async def test_consciousness_check(vcr):
    with vcr.use_cassette("consciousness_check.yaml"):
        result = await consciousness_check(...)
        # VCR records response if not exists
        # Replays if cassette exists
```

Benefits:
- No API calls in later test runs
- Prevents breaking changes to analysis
- Validates quality remains consistent
- Enables CI/CD without API keys

---

## Success Criteria

✅ Protocol compliance tests pass for all backends
✅ Fallback tests verify orchestration logic
✅ Integration tests pass (with real Ollama)
✅ Evaluation tests check analysis quality
✅ Coverage >80% for new code
✅ VCR cassettes recorded
✅ Tests run in <5 min (unit), <15 min (integration)

---

## Running Tests

```bash
# Unit tests only
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# All with coverage
pytest tests/ --cov=src -v --cov-report=html

# Real Ollama (opt-in)
TEST_REAL_OLLAMA=1 pytest tests/integration/test_ollama_real.py -v
```

---

## Notes for Sonnet

1. Protocol compliance first - test same scenarios against all backends
2. Parameterized fixtures - run tests against multiple backends efficiently
3. VCR is key - record once, replay forever
4. Mock is essential - use Mock objects for selector, registry, etc.
5. Clear test names - describe what's being tested
6. Comprehensive error scenarios - timeout, rate limit, unavailable, malformed
7. Generate comprehensive, production-quality tests
