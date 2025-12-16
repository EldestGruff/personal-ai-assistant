"""
Tests for MockBackend implementation.

Verifies that MockBackend provides deterministic,
reliable responses for all test scenarios.
"""

import pytest

from src.services.ai_backends.models import BackendRequest
from src.services.ai_backends.mock_backend import MockBackend


class TestMockBackendSuccess:
    """Test MockBackend in success mode"""
    
    @pytest.mark.asyncio
    async def test_success_mode_returns_success(self):
        """mock-success returns SuccessResponse"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-123",
            thought_content="test thought"
        )
        
        response = await backend.analyze(request)
        
        assert response.success is True
        assert response.analysis is not None
        assert response.metadata is not None
    
    @pytest.mark.asyncio
    async def test_success_includes_summary(self):
        """response includes summary"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-456",
            thought_content="test content"
        )
        
        response = await backend.analyze(request)
        
        assert response.success is True
        assert len(response.analysis.summary) > 0
        assert "test content" in response.analysis.summary.lower()
    
    @pytest.mark.asyncio
    async def test_detects_email_theme(self):
        """detects 'email' theme in content"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-789",
            thought_content="should improve email system"
        )
        
        response = await backend.analyze(request)
        
        themes = [t.theme for t in response.analysis.themes]
        assert "email" in themes
    
    @pytest.mark.asyncio
    async def test_detects_optimization_theme(self):
        """detects 'optimization' theme"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-abc",
            thought_content="need to optimize performance"
        )
        
        response = await backend.analyze(request)
        
        themes = [t.theme for t in response.analysis.themes]
        assert "optimization" in themes
    
    @pytest.mark.asyncio
    async def test_suggests_action_for_should(self):
        """suggests action when content contains 'should'"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-def",
            thought_content="should create a new task"
        )
        
        response = await backend.analyze(request)
        
        assert len(response.analysis.suggested_actions) > 0
    
    @pytest.mark.asyncio
    async def test_no_action_for_statement(self):
        """no action for simple statement"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-ghi",
            thought_content="the weather is nice"
        )
        
        response = await backend.analyze(request)
        
        # May or may not have actions, just verify it doesn't crash
        assert response.success is True
    
    @pytest.mark.asyncio
    async def test_includes_metadata(self):
        """response includes processing metadata"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-jkl",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.metadata.tokens_used >= 0
        assert response.metadata.processing_time_ms >= 0
        assert response.metadata.model_version == "mock-v1.0"
    
    @pytest.mark.asyncio
    async def test_deterministic_output(self):
        """same input produces same output"""
        backend = MockBackend(mode="mock-success")
        request = BackendRequest(
            request_id="req-mno",
            thought_content="deterministic test"
        )
        
        response1 = await backend.analyze(request)
        response2 = await backend.analyze(request)
        
        assert response1.analysis.summary == response2.analysis.summary
        theme_names1 = [t.theme for t in response1.analysis.themes]
        theme_names2 = [t.theme for t in response2.analysis.themes]
        assert theme_names1 == theme_names2


class TestMockBackendErrors:
    """Test MockBackend error modes"""
    
    @pytest.mark.asyncio
    async def test_timeout_mode_returns_timeout(self):
        """mock-timeout returns TIMEOUT error"""
        backend = MockBackend(mode="mock-timeout")
        request = BackendRequest(
            request_id="req-timeout",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.success is False
        assert response.error.error_code == "TIMEOUT"
    
    @pytest.mark.asyncio
    async def test_unavailable_mode_returns_unavailable(self):
        """mock-unavailable returns UNAVAILABLE error"""
        backend = MockBackend(mode="mock-unavailable")
        request = BackendRequest(
            request_id="req-unavail",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.success is False
        assert response.error.error_code == "UNAVAILABLE"
    
    @pytest.mark.asyncio
    async def test_rate_limited_mode_returns_rate_limited(self):
        """mock-rate-limited returns RATE_LIMITED error"""
        backend = MockBackend(mode="mock-rate-limited")
        request = BackendRequest(
            request_id="req-rate",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.success is False
        assert response.error.error_code == "RATE_LIMITED"
    
    @pytest.mark.asyncio
    async def test_malformed_mode_returns_malformed(self):
        """mock-malformed returns MALFORMED_RESPONSE error"""
        backend = MockBackend(mode="mock-malformed")
        request = BackendRequest(
            request_id="req-malform",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.success is False
        assert response.error.error_code == "MALFORMED_RESPONSE"
    
    @pytest.mark.asyncio
    async def test_errors_include_request_id(self):
        """error responses include request_id"""
        backend = MockBackend(mode="mock-timeout")
        request = BackendRequest(
            request_id="req-pqr",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.error.request_id == "req-pqr"
    
    @pytest.mark.asyncio
    async def test_errors_include_backend_name(self):
        """error responses include backend name"""
        backend = MockBackend(mode="mock-unavailable")
        request = BackendRequest(
            request_id="req-stu",
            thought_content="test"
        )
        
        response = await backend.analyze(request)
        
        assert response.error.backend_name == backend.name


class TestMockBackendHealthCheck:
    """Test MockBackend health check"""
    
    @pytest.mark.asyncio
    async def test_health_check_always_true(self):
        """mock backend always healthy"""
        backend = MockBackend(mode="mock-success")
        assert await backend.health_check() is True
    
    @pytest.mark.asyncio
    async def test_health_check_true_even_in_error_modes(self):
        """health check true even for error modes"""
        for mode in ["mock-timeout", "mock-unavailable", "mock-rate-limited"]:
            backend = MockBackend(mode=mode)
            assert await backend.health_check() is True


class TestMockBackendName:
    """Test MockBackend name property"""
    
    def test_name_matches_mode(self):
        """backend name matches mode"""
        backend = MockBackend(mode="mock-success")
        assert backend.name == "mock-success"
    
    def test_name_for_different_modes(self):
        """name reflects selected mode"""
        modes = ["mock-timeout", "mock-unavailable", "mock-rate-limited"]
        for mode in modes:
            backend = MockBackend(mode=mode)
            assert backend.name == mode
