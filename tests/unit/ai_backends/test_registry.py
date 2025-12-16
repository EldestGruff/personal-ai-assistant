"""
Tests for AIBackendRegistry.

Verifies backend registration, retrieval, and lifecycle
management through the central registry.
"""

import pytest

from src.services.ai_backends.registry import AIBackendRegistry
from src.services.ai_backends.mock_backend import MockBackend


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear registry before each test"""
    AIBackendRegistry.clear()
    yield
    AIBackendRegistry.clear()


class TestRegistration:
    """Test backend registration"""
    
    def test_register_backend(self):
        """register adds backend to registry"""
        backend = MockBackend(mode="mock-success")
        AIBackendRegistry.register("mock", backend)
        
        assert AIBackendRegistry.is_registered("mock")
    
    def test_register_sets_first_as_default(self):
        """first registered backend becomes default"""
        backend = MockBackend(mode="mock-success")
        AIBackendRegistry.register("mock", backend)
        
        default = AIBackendRegistry.get_default()
        assert default is not None
        assert default.name == "mock-success"
    
    def test_register_multiple_backends(self):
        """register multiple backends"""
        backend1 = MockBackend(mode="mock-success")
        backend2 = MockBackend(mode="mock-timeout")
        
        AIBackendRegistry.register("mock1", backend1)
        AIBackendRegistry.register("mock2", backend2)
        
        assert AIBackendRegistry.is_registered("mock1")
        assert AIBackendRegistry.is_registered("mock2")
    
    def test_register_empty_name_raises(self):
        """empty name raises ValueError"""
        backend = MockBackend(mode="mock-success")
        
        with pytest.raises(ValueError):
            AIBackendRegistry.register("", backend)
    
    def test_register_invalid_backend_raises(self):
        """invalid backend raises ValueError"""
        class BadBackend:
            pass
        
        with pytest.raises(ValueError):
            AIBackendRegistry.register("bad", BadBackend())


class TestRetrieval:
    """Test backend retrieval"""
    
    def test_get_registered_backend(self):
        """get retrieves registered backend"""
        backend = MockBackend(mode="mock-success")
        AIBackendRegistry.register("mock", backend)
        
        retrieved = AIBackendRegistry.get("mock")
        assert retrieved is backend
    
    def test_get_unregistered_raises(self):
        """get unregistered backend raises KeyError"""
        with pytest.raises(KeyError):
            AIBackendRegistry.get("nonexistent")
    
    def test_get_default_returns_first(self):
        """get_default returns first registered"""
        backend1 = MockBackend(mode="mock-success")
        backend2 = MockBackend(mode="mock-timeout")
        
        AIBackendRegistry.register("mock1", backend1)
        AIBackendRegistry.register("mock2", backend2)
        
        default = AIBackendRegistry.get_default()
        assert default is backend1
    
    def test_get_default_empty_registry(self):
        """get_default returns None when empty"""
        default = AIBackendRegistry.get_default()
        assert default is None


class TestDefaultBackend:
    """Test default backend management"""
    
    def test_set_default(self):
        """set_default changes default backend"""
        backend1 = MockBackend(mode="mock-success")
        backend2 = MockBackend(mode="mock-timeout")
        
        AIBackendRegistry.register("mock1", backend1)
        AIBackendRegistry.register("mock2", backend2)
        
        AIBackendRegistry.set_default("mock2")
        
        default = AIBackendRegistry.get_default()
        assert default is backend2
    
    def test_set_default_unregistered_raises(self):
        """set_default unregistered backend raises KeyError"""
        with pytest.raises(KeyError):
            AIBackendRegistry.set_default("nonexistent")


class TestListing:
    """Test backend listing"""
    
    def test_list_available_empty(self):
        """list_available returns empty list when empty"""
        backends = AIBackendRegistry.list_available()
        assert backends == []
    
    def test_list_available_single(self):
        """list_available returns single backend"""
        backend = MockBackend(mode="mock-success")
        AIBackendRegistry.register("mock", backend)
        
        backends = AIBackendRegistry.list_available()
        assert backends == ["mock"]
    
    def test_list_available_multiple(self):
        """list_available returns all backends"""
        backend1 = MockBackend(mode="mock-success")
        backend2 = MockBackend(mode="mock-timeout")
        
        AIBackendRegistry.register("mock1", backend1)
        AIBackendRegistry.register("mock2", backend2)
        
        backends = AIBackendRegistry.list_available()
        assert "mock1" in backends
        assert "mock2" in backends
        assert len(backends) == 2


class TestUnregistration:
    """Test backend unregistration"""
    
    def test_unregister_backend(self):
        """unregister removes backend"""
        backend = MockBackend(mode="mock-success")
        AIBackendRegistry.register("mock", backend)
        
        AIBackendRegistry.unregister("mock")
        
        assert not AIBackendRegistry.is_registered("mock")
    
    def test_unregister_unregistered_raises(self):
        """unregister unregistered backend raises KeyError"""
        with pytest.raises(KeyError):
            AIBackendRegistry.unregister("nonexistent")
    
    def test_unregister_default_selects_new(self):
        """unregister default selects new default"""
        backend1 = MockBackend(mode="mock-success")
        backend2 = MockBackend(mode="mock-timeout")
        
        AIBackendRegistry.register("mock1", backend1)
        AIBackendRegistry.register("mock2", backend2)
        
        # mock1 is default
        assert AIBackendRegistry.get_default() is backend1
        
        AIBackendRegistry.unregister("mock1")
        
        # mock2 should become default
        default = AIBackendRegistry.get_default()
        assert default is backend2
    
    def test_unregister_last_clears_default(self):
        """unregister last backend clears default"""
        backend = MockBackend(mode="mock-success")
        AIBackendRegistry.register("mock", backend)
        
        AIBackendRegistry.unregister("mock")
        
        assert AIBackendRegistry.get_default() is None


class TestClear:
    """Test registry clearing"""
    
    def test_clear_removes_all(self):
        """clear removes all backends"""
        backend1 = MockBackend(mode="mock-success")
        backend2 = MockBackend(mode="mock-timeout")
        
        AIBackendRegistry.register("mock1", backend1)
        AIBackendRegistry.register("mock2", backend2)
        
        AIBackendRegistry.clear()
        
        assert AIBackendRegistry.list_available() == []
        assert AIBackendRegistry.get_default() is None


class TestIsRegistered:
    """Test registration checking"""
    
    def test_is_registered_true(self):
        """is_registered returns True for registered"""
        backend = MockBackend(mode="mock-success")
        AIBackendRegistry.register("mock", backend)
        
        assert AIBackendRegistry.is_registered("mock")
    
    def test_is_registered_false(self):
        """is_registered returns False for unregistered"""
        assert not AIBackendRegistry.is_registered("nonexistent")


class TestHealthCheckAll:
    """Test health checking all backends"""
    
    @pytest.mark.asyncio
    async def test_health_check_all_empty(self):
        """health_check_all returns empty dict when empty"""
        health = await AIBackendRegistry.health_check_all()
        assert health == {}
    
    @pytest.mark.asyncio
    async def test_health_check_all_single(self):
        """health_check_all returns health status"""
        backend = MockBackend(mode="mock-success")
        AIBackendRegistry.register("mock", backend)
        
        health = await AIBackendRegistry.health_check_all()
        
        assert "mock" in health
        assert health["mock"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_all_multiple(self):
        """health_check_all returns all statuses"""
        backend1 = MockBackend(mode="mock-success")
        backend2 = MockBackend(mode="mock-timeout")
        
        AIBackendRegistry.register("mock1", backend1)
        AIBackendRegistry.register("mock2", backend2)
        
        health = await AIBackendRegistry.health_check_all()
        
        assert "mock1" in health
        assert "mock2" in health
        assert health["mock1"] is True
        assert health["mock2"] is True
