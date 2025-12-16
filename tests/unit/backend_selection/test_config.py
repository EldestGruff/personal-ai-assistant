"""
Tests for Backend Configuration

Validates configuration loading from environment variables.
"""

import os
import pytest

from src.services.backend_selection.config import BackendConfig


class TestBackendConfigValidation:
    """Test BackendConfig validation"""
    
    def test_valid_minimal_config(self):
        """Valid config with defaults"""
        config = BackendConfig()
        
        assert config.available_backends == ["claude", "ollama"]
        assert config.primary_backend == "claude"
        assert config.secondary_backend == "ollama"
        assert config.selection_strategy == "sequential"
    
    def test_valid_custom_config(self):
        """Valid config with custom values"""
        config = BackendConfig(
            available_backends=["ollama", "mock"],
            primary_backend="ollama",
            secondary_backend="mock",
            selection_strategy="sequential"
        )
        
        assert config.available_backends == ["ollama", "mock"]
        assert config.primary_backend == "ollama"
        assert config.secondary_backend == "mock"
    
    def test_invalid_strategy(self):
        """Invalid selection strategy should fail"""
        with pytest.raises(ValueError) as exc:
            BackendConfig(selection_strategy="invalid")
        
        assert "selection_strategy" in str(exc.value)
    
    def test_valid_strategies(self):
        """All valid strategies should work"""
        for strategy in ["sequential", "primary_only", "parallel"]:
            config = BackendConfig(selection_strategy=strategy)
            assert config.selection_strategy == strategy
    
    def test_empty_primary_backend(self):
        """Empty primary backend should fail"""
        with pytest.raises(ValueError) as exc:
            BackendConfig(primary_backend="")
        
        assert "primary_backend" in str(exc.value)
    
    def test_whitespace_primary_backend(self):
        """Whitespace-only primary backend should fail"""
        with pytest.raises(ValueError) as exc:
            BackendConfig(primary_backend="   ")
        
        assert "primary_backend" in str(exc.value)


class TestBackendConfigFromEnv:
    """Test loading config from environment variables"""
    
    def test_from_env_defaults(self, monkeypatch):
        """Load config with all defaults"""
        # Clear relevant env vars
        for key in ["AVAILABLE_BACKENDS", "PRIMARY_BACKEND", "SECONDARY_BACKEND",
                    "BACKEND_SELECTION_STRATEGY", "ANTHROPIC_API_KEY",
                    "CLAUDE_API_KEY", "OLLAMA_BASE_URL", "OLLAMA_MODEL"]:
            monkeypatch.delenv(key, raising=False)
        
        config = BackendConfig.from_env()
        
        assert config.available_backends == ["claude", "ollama"]
        assert config.primary_backend == "claude"
        assert config.secondary_backend == "ollama"
        assert config.selection_strategy == "sequential"
    
    def test_from_env_custom_backends(self, monkeypatch):
        """Load custom backends from environment"""
        monkeypatch.setenv("AVAILABLE_BACKENDS", "ollama,mock,claude")
        monkeypatch.setenv("PRIMARY_BACKEND", "ollama")
        monkeypatch.setenv("SECONDARY_BACKEND", "claude")
        
        config = BackendConfig.from_env()
        
        assert config.available_backends == ["ollama", "mock", "claude"]
        assert config.primary_backend == "ollama"
        assert config.secondary_backend == "claude"
    
    def test_from_env_whitespace_handling(self, monkeypatch):
        """Handle whitespace in comma-separated list"""
        monkeypatch.setenv("AVAILABLE_BACKENDS", " claude , ollama , mock ")
        
        config = BackendConfig.from_env()
        
        assert config.available_backends == ["claude", "ollama", "mock"]
    
    def test_from_env_strategy(self, monkeypatch):
        """Load custom strategy from environment"""
        monkeypatch.setenv("BACKEND_SELECTION_STRATEGY", "primary_only")
        
        config = BackendConfig.from_env()
        
        assert config.selection_strategy == "primary_only"
    
    def test_from_env_claude_api_key_anthropic(self, monkeypatch):
        """Load Claude API key from ANTHROPIC_API_KEY"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        
        config = BackendConfig.from_env()
        
        assert config.claude_api_key == "sk-ant-test-key"
    
    def test_from_env_claude_api_key_claude(self, monkeypatch):
        """Load Claude API key from CLAUDE_API_KEY"""
        monkeypatch.setenv("CLAUDE_API_KEY", "sk-claude-test-key")
        
        config = BackendConfig.from_env()
        
        assert config.claude_api_key == "sk-claude-test-key"
    
    def test_from_env_claude_api_key_priority(self, monkeypatch):
        """ANTHROPIC_API_KEY takes priority over CLAUDE_API_KEY"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-priority")
        monkeypatch.setenv("CLAUDE_API_KEY", "sk-claude-fallback")
        
        config = BackendConfig.from_env()
        
        assert config.claude_api_key == "sk-ant-priority"
    
    def test_from_env_ollama_settings(self, monkeypatch):
        """Load Ollama settings from environment"""
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_MODEL", "deepseek-r1:70b")
        
        config = BackendConfig.from_env()
        
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.ollama_model == "deepseek-r1:70b"
    
    def test_from_env_no_secondary(self, monkeypatch):
        """Handle missing secondary backend"""
        monkeypatch.setenv("SECONDARY_BACKEND", "")
        
        config = BackendConfig.from_env()
        
        assert config.secondary_backend is None


class TestBackendConfigHelpers:
    """Test config helper methods"""
    
    def test_is_backend_available_true(self):
        """Backend is available"""
        config = BackendConfig(
            available_backends=["claude", "ollama"]
        )
        
        assert config.is_backend_available("claude") is True
        assert config.is_backend_available("ollama") is True
    
    def test_is_backend_available_false(self):
        """Backend is not available"""
        config = BackendConfig(
            available_backends=["claude"]
        )
        
        assert config.is_backend_available("ollama") is False
        assert config.is_backend_available("mock") is False
    
    def test_get_timeout_for_claude(self):
        """Claude timeout is 30s"""
        config = BackendConfig()
        
        assert config.get_timeout_for_backend("claude") == 30
    
    def test_get_timeout_for_ollama(self):
        """Ollama timeout is 60s (large models)"""
        config = BackendConfig()
        
        assert config.get_timeout_for_backend("ollama") == 60
    
    def test_get_timeout_for_mock(self):
        """Mock timeout is 5s (instant)"""
        config = BackendConfig()
        
        assert config.get_timeout_for_backend("mock") == 5
    
    def test_get_timeout_for_unknown(self):
        """Unknown backend defaults to 30s"""
        config = BackendConfig()
        
        assert config.get_timeout_for_backend("unknown") == 30
