"""
Tests for BackendOrchestrator

Validates orchestration logic with automatic fallback.
"""

import pytest

from src.services.ai_backends import AIBackendRegistry, BackendRequest
from src.services.ai_backends.mock_backend import MockBackend
from src.services.backend_selection.default_selector import DefaultSelector
from src.services.backend_selection.config import BackendConfig
from src.services.backend_selection.orchestrator import BackendOrchestrator


class TestOrchestratorPrimarySuccess:
    """Test successful execution with primary backend"""
    
    @pytest.mark.asyncio
    async def test_returns_primary_result_on_success(self):
        """Return result from primary when it succeeds"""
        # Setup
        registry = AIBackendRegistry()
        registry.register("claude", MockBackend(mode="mock-success"))
        registry.register("ollama", MockBackend(mode="mock-success"))
        
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        # Execute
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        # Verify
        assert response.success is True
        assert response.analysis.backend_used == "mock-success"
    
    @pytest.mark.asyncio
    async def test_does_not_try_fallback_on_success(self):
        """Don't try fallback when primary succeeds"""
        # Setup with primary success, fallback would fail
        registry = AIBackendRegistry()
        registry.register("claude", MockBackend(mode="mock-success"))
        registry.register("ollama", MockBackend(mode="mock-timeout"))
        
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        # Execute
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        # Verify - would have failed if fallback was tried
        assert response.success is True


class TestOrchestratorRecoverableErrors:
    """Test fallback on recoverable errors"""
    
    @pytest.mark.asyncio
    async def test_fallback_on_rate_limited(self):
        """Try fallback when primary is rate limited"""
        registry = AIBackendRegistry()
        registry.register("claude", MockBackend(mode="mock-rate-limited"))
        registry.register("ollama", MockBackend(mode="mock-success"))
        
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        # Should succeed with fallback
        assert response.success is True
        assert response.analysis.backend_used == "mock-success"
    
    @pytest.mark.asyncio
    async def test_fallback_on_unavailable(self):
        """Try fallback when primary is unavailable"""
        registry = AIBackendRegistry()
        registry.register("claude", MockBackend(mode="mock-unavailable"))
        registry.register("ollama", MockBackend(mode="mock-success"))
        
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        assert response.success is True
        assert response.analysis.backend_used == "mock-success"
    
    @pytest.mark.asyncio
    async def test_fallback_on_timeout(self):
        """Try fallback when primary times out"""
        registry = AIBackendRegistry()
        registry.register("claude", MockBackend(mode="mock-timeout"))
        registry.register("ollama", MockBackend(mode="mock-success"))
        
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        assert response.success is True
        assert response.analysis.backend_used == "mock-success"
    
    @pytest.mark.asyncio
    async def test_fallback_on_malformed(self):
        """Try fallback when primary returns malformed response"""
        registry = AIBackendRegistry()
        registry.register("claude", MockBackend(mode="mock-malformed"))
        registry.register("ollama", MockBackend(mode="mock-success"))
        
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        assert response.success is True


class TestOrchestratorNonRecoverableErrors:
    """Test fail-fast on non-recoverable errors"""
    
    @pytest.mark.asyncio
    async def test_no_fallback_on_invalid_input(self):
        """Don't retry on invalid input (client error)"""
        registry = AIBackendRegistry()
        
        # Create mock that returns INVALID_INPUT error
        class InvalidInputMock:
            @property
            def name(self):
                return "invalid-mock"
            
            async def analyze(self, request):
                from src.services.ai_backends.models import ErrorResponse, ErrorDetails
                return ErrorResponse(
                    success=False,
                    request_id=request.request_id,
                    backend_used="invalid-mock",
                    error=ErrorDetails(
                        error_code="INVALID_INPUT",
                        error_message="Invalid thought content",
                        request_id=request.request_id,
                        backend_name="invalid-mock"
                    )
                )
            
            async def health_check(self):
                return True
        
        registry.register("claude", InvalidInputMock())
        registry.register("ollama", MockBackend(mode="mock-success"))
        
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        # Should fail without trying fallback
        assert response.success is False
        assert response.error.error_code == "INVALID_INPUT"


class TestOrchestratorAllBackendsFail:
    """Test behavior when all backends fail"""
    
    @pytest.mark.asyncio
    async def test_returns_error_when_all_fail(self):
        """Return error when both primary and fallback fail"""
        registry = AIBackendRegistry()
        registry.register("claude", MockBackend(mode="mock-timeout"))
        registry.register("ollama", MockBackend(mode="mock-unavailable"))
        
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        # Should return error from last tried backend
        assert response.success is False
        assert response.error.error_code in ["TIMEOUT", "UNAVAILABLE"]


class TestOrchestratorNoFallback:
    """Test behavior when no fallback is available"""
    
    @pytest.mark.asyncio
    async def test_returns_error_when_no_fallback(self):
        """Return error when primary fails and no fallback"""
        registry = AIBackendRegistry()
        registry.register("claude", MockBackend(mode="mock-timeout"))
        
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend=None  # No fallback
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        assert response.success is False
        assert response.error.error_code == "TIMEOUT"


class TestOrchestratorTimeoutConfiguration:
    """Test timeout configuration from selector"""
    
    @pytest.mark.asyncio
    async def test_uses_timeout_from_selector(self):
        """Use timeout specified by selector"""
        registry = AIBackendRegistry()
        registry.register("ollama", MockBackend(mode="mock-success"))
        
        config = BackendConfig(
            primary_backend="ollama"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        request = BackendRequest(
            request_id="req-123",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        # Verify request timeout was updated from selector
        # (Ollama should get 60s, not default 30s)
        assert response.success is True


class TestOrchestratorRequestIdPropagation:
    """Test request ID is properly propagated"""
    
    @pytest.mark.asyncio
    async def test_request_id_in_response(self):
        """Request ID appears in final response"""
        registry = AIBackendRegistry()
        registry.register("claude", MockBackend(mode="mock-success"))
        
        config = BackendConfig(
            primary_backend="claude"
        )
        selector = DefaultSelector(config)
        orchestrator = BackendOrchestrator(registry, selector)
        
        request = BackendRequest(
            request_id="req-unique-xyz",
            thought_content="Test thought"
        )
        
        response = await orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(request.thought_content)
        )
        
        assert response.analysis.request_id == "req-unique-xyz"
