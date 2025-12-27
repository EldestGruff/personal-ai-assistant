"""
Tests for DefaultSelector

Validates selection logic and decision-making.
"""

import pytest

from src.services.backend_selection.default_selector import DefaultSelector
from src.services.backend_selection.config import BackendConfig
from src.services.backend_selection.models import BackendSelectionRequest


class TestDefaultSelectorPrimarySelection:
    """Test primary backend selection"""
    
    @pytest.mark.asyncio
    async def test_selects_configured_primary(self):
        """Select primary backend from config"""
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["claude", "ollama"]
        )
        
        response = await selector.select_backends(request)
        
        assert response.decision_type == "SEQUENTIAL"
        assert len(response.backends) == 1
        assert response.backends[0].name == "claude"
        assert response.backends[0].role == "primary"
    
    @pytest.mark.asyncio
    async def test_uses_secondary_as_primary_when_primary_unavailable(self):
        """Use secondary as primary if primary not available"""
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["ollama"]  # Claude not available
        )
        
        response = await selector.select_backends(request)
        
        assert len(response.backends) == 1
        assert response.backends[0].name == "ollama"
        assert response.backends[0].role == "primary"
    
    @pytest.mark.asyncio
    async def test_fails_when_no_backends_available(self):
        """Raise error when no backends available"""
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["mock"]  # Neither primary nor secondary
        )
        
        with pytest.raises(ValueError) as exc:
            await selector.select_backends(request)
        
        assert "No backends available" in str(exc.value)


class TestDefaultSelectorFallbackSelection:
    """Test fallback backend selection"""
    
    @pytest.mark.asyncio
    async def test_selects_secondary_as_fallback(self):
        """Select secondary as fallback when primary available"""
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["claude", "ollama"]
        )
        
        response = await selector.select_backends(request)
        
        assert len(response.fallback_backends) == 1
        assert response.fallback_backends[0].name == "ollama"
        assert response.fallback_backends[0].role == "fallback"
    
    @pytest.mark.asyncio
    async def test_no_fallback_when_secondary_unavailable(self):
        """No fallback when secondary not available"""
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["claude"]  # Ollama not available
        )
        
        response = await selector.select_backends(request)
        
        assert len(response.fallback_backends) == 0
    
    @pytest.mark.asyncio
    async def test_no_fallback_when_secondary_is_primary(self):
        """No fallback when secondary is promoted to primary"""
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["ollama"]  # Only secondary available
        )
        
        response = await selector.select_backends(request)
        
        assert len(response.backends) == 1
        assert response.backends[0].name == "ollama"
        assert len(response.fallback_backends) == 0


class TestDefaultSelectorTimeouts:
    """Test timeout configuration"""
    
    @pytest.mark.asyncio
    async def test_claude_timeout_is_30s(self):
        """Claude gets 30s timeout"""
        config = BackendConfig(
            primary_backend="claude"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["claude"]
        )
        
        response = await selector.select_backends(request)
        
        assert response.backends[0].timeout_seconds == 30
    
    @pytest.mark.asyncio
    async def test_ollama_timeout_is_120s(self):
        """Ollama gets 120s timeout (large models)"""
        config = BackendConfig(
            primary_backend="ollama"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["ollama"]
        )
        
        response = await selector.select_backends(request)
        
        assert response.backends[0].timeout_seconds == 120
    
    @pytest.mark.asyncio
    async def test_mock_timeout_is_5s(self):
        """Mock gets 5s timeout (instant)"""
        config = BackendConfig(
            primary_backend="mock"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["mock"]
        )
        
        response = await selector.select_backends(request)
        
        assert response.backends[0].timeout_seconds == 5


class TestDefaultSelectorReasoning:
    """Test reasoning explanations"""
    
    @pytest.mark.asyncio
    async def test_reasoning_with_fallback(self):
        """Reasoning explains primary + fallback"""
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["claude", "ollama"]
        )
        
        response = await selector.select_backends(request)
        
        assert "SEQUENTIAL strategy" in response.reasoning
        assert "claude" in response.reasoning
        assert "ollama" in response.reasoning
        assert "fallback" in response.reasoning
    
    @pytest.mark.asyncio
    async def test_reasoning_without_fallback(self):
        """Reasoning explains no fallback"""
        config = BackendConfig(
            primary_backend="claude",
            secondary_backend="ollama"
        )
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["claude"]
        )
        
        response = await selector.select_backends(request)
        
        assert "no fallback available" in response.reasoning


class TestDefaultSelectorRequestIdEcho:
    """Test request ID is echoed back"""
    
    @pytest.mark.asyncio
    async def test_echoes_request_id(self):
        """Response echoes request ID"""
        config = BackendConfig()
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-unique-123",
            thought_length=100,
            available_backends=["claude"]
        )
        
        response = await selector.select_backends(request)
        
        assert response.request_id == "req-unique-123"
