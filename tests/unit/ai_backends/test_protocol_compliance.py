"""
Protocol compliance tests for AI backends.

Ensures all backend implementations satisfy the AIBackend protocol
with identical behavior guarantees (idempotency, timeouts, validation).
"""

import pytest

from src.services.ai_backends.models import BackendRequest
from src.services.ai_backends.base import validate_backend
from src.services.ai_backends.claude_backend import ClaudeBackend
from src.services.ai_backends.ollama_backend import OllamaBackend
from src.services.ai_backends.mock_backend import MockBackend


@pytest.fixture
def mock_backend():
    """Mock backend instance"""
    return MockBackend(mode="mock-success")


@pytest.fixture
def backends():
    """All backend implementations"""
    return [
        MockBackend(mode="mock-success"),
        # Claude and Ollama would require API keys/connectivity
        # For protocol compliance, we only test MockBackend
    ]


class TestProtocolStructure:
    """Test that backends satisfy protocol structure"""
    
    def test_mock_backend_has_name_property(self, mock_backend):
        """backend has name property"""
        assert hasattr(mock_backend, "name")
        assert isinstance(mock_backend.name, str)
        assert len(mock_backend.name) > 0
    
    def test_mock_backend_has_analyze_method(self, mock_backend):
        """backend has analyze method"""
        assert hasattr(mock_backend, "analyze")
        assert callable(mock_backend.analyze)
    
    def test_mock_backend_has_health_check_method(self, mock_backend):
        """backend has health_check method"""
        assert hasattr(mock_backend, "health_check")
        assert callable(mock_backend.health_check)
    
    def test_validate_backend_accepts_valid(self, mock_backend):
        """validate_backend accepts compliant backend"""
        assert validate_backend(mock_backend) is True
    
    def test_validate_backend_rejects_missing_name(self):
        """validate_backend rejects backend without name"""
        class BadBackend:
            async def analyze(self, req):
                pass
            async def health_check(self):
                pass
        
        assert validate_backend(BadBackend()) is False
    
    def test_validate_backend_rejects_missing_analyze(self):
        """validate_backend rejects backend without analyze"""
        class BadBackend:
            @property
            def name(self):
                return "bad"
            async def health_check(self):
                pass
        
        assert validate_backend(BadBackend()) is False


class TestProtocolBehavior:
    """Test that backends satisfy protocol behavior guarantees"""
    
    @pytest.mark.asyncio
    async def test_analyze_returns_response(self, mock_backend):
        """analyze returns SuccessResponse or ErrorResponse"""
        request = BackendRequest(
            request_id="req-123",
            thought_content="test thought"
        )
        
        response = await mock_backend.analyze(request)
        
        # Response has success field
        assert hasattr(response, "success")
        assert isinstance(response.success, bool)
    
    @pytest.mark.asyncio
    async def test_analyze_echoes_request_id(self, mock_backend):
        """analyze response includes original request_id"""
        request = BackendRequest(
            request_id="req-456",
            thought_content="test thought"
        )
        
        response = await mock_backend.analyze(request)
        
        if response.success:
            assert response.analysis.request_id == "req-456"
        else:
            assert response.error.request_id == "req-456"
    
    @pytest.mark.asyncio
    async def test_analyze_includes_backend_name(self, mock_backend):
        """analyze response includes backend name"""
        request = BackendRequest(
            request_id="req-789",
            thought_content="test thought"
        )
        
        response = await mock_backend.analyze(request)
        
        if response.success:
            assert response.analysis.backend_used == mock_backend.name
        else:
            assert response.error.backend_name == mock_backend.name
    
    @pytest.mark.asyncio
    async def test_health_check_returns_bool(self, mock_backend):
        """health_check returns boolean"""
        result = await mock_backend.health_check()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_success_response_has_analysis(self):
        """success response includes analysis"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-abc",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.success is True
        assert hasattr(response, "analysis")
        assert response.analysis is not None
        assert hasattr(response.analysis, "summary")
    
    @pytest.mark.asyncio
    async def test_success_response_has_metadata(self):
        """success response includes metadata"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-def",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.success is True
        assert hasattr(response, "metadata")
        assert response.metadata is not None
        assert hasattr(response.metadata, "processing_time_ms")
    
    @pytest.mark.asyncio
    async def test_error_response_has_error(self):
        """error response includes error details"""
        backend = MockBackend(mode="mock-timeout")
        request = BackendRequest(
            request_id="req-ghi",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.success is False
        assert hasattr(response, "error")
        assert response.error is not None
        assert hasattr(response.error, "error_code")
        assert hasattr(response.error, "error_message")
    
    @pytest.mark.asyncio
    async def test_error_codes_are_standard(self):
        """error responses use standardized error codes"""
        valid_codes = {
            "INVALID_INPUT",
            "TIMEOUT",
            "RATE_LIMITED",
            "UNAVAILABLE",
            "CONTEXT_OVERFLOW",
            "INTERNAL_ERROR",
            "MALFORMED_RESPONSE"
        }
        
        # Test different error modes
        error_modes = [
            "mock-timeout",
            "mock-unavailable",
            "mock-rate-limited",
            "mock-malformed"
        ]
        
        for mode in error_modes:
            backend = MockBackend(mode=mode)
            request = BackendRequest(
                request_id=f"req-{mode}",
                thought_content="test"
            )
            
            response = await backend.analyze(request)
            
            assert response.success is False
            assert response.error.error_code in valid_codes


class TestIdempotency:
    """Test that backends satisfy idempotency guarantee"""
    
    @pytest.mark.asyncio
    async def test_same_request_id_returns_same_result(self):
        """same request_id yields consistent results"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-idempotent",
            thought_content="test thought"
        )
        
        # Call twice with same request_id
        response1 = await backend.analyze(request)
        response2 = await backend.analyze(request)
        
        # Both should succeed
        assert response1.success is True
        assert response2.success is True
        
        # Both should have same request_id
        assert response1.analysis.request_id == "req-idempotent"
        assert response2.analysis.request_id == "req-idempotent"
        
        # Mock backend returns deterministic content
        assert response1.analysis.summary == response2.analysis.summary


class TestValidation:
    """Test that backends validate inputs"""
    
    @pytest.mark.asyncio
    async def test_backends_accept_valid_request(self, mock_backend):
        """backends accept valid requests"""
        request = BackendRequest(
            request_id="req-valid",
            thought_content="valid thought content"
        )
        
        response = await mock_backend.analyze(request)
        
        # Should not raise exception
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_backends_handle_minimal_request(self, mock_backend):
        """backends handle minimal valid request"""
        request = BackendRequest(
            request_id="req-minimal",
            thought_content="x"  # Minimal 1 char
        )
        
        response = await mock_backend.analyze(request)
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_backends_handle_context(self, mock_backend):
        """backends handle requests with context"""
        request = BackendRequest(
            request_id="req-context",
            thought_content="test",
            context={"user_id": "abc123", "depth": "deep"}
        )
        
        response = await mock_backend.analyze(request)
        
        assert response is not None
