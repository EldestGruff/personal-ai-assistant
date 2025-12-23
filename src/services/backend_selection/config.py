"""
Backend Configuration

Environment-based configuration for backend selection.

Configuration loads from environment variables with sensible
defaults for local development. Enables deployment flexibility
without code changes.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class BackendConfig(BaseModel):
    """
    Configuration for backend selection.
    
    Controls which backends are available, which is primary,
    and what selection strategy to use. Loads from environment
    variables for deployment flexibility.
    
    Environment Variables:
        AVAILABLE_BACKENDS: Comma-separated list (default: "claude,ollama")
        PRIMARY_BACKEND: Primary backend name (default: "claude")
        SECONDARY_BACKEND: Fallback backend (default: "ollama")
        BACKEND_SELECTION_STRATEGY: Strategy to use (default: "sequential")
        CLAUDE_API_KEY: Anthropic API key (required for Claude)
        OLLAMA_BASE_URL: Ollama server URL (default: "http://192.168.7.187:11434")
        OLLAMA_MODEL: Ollama model name (default: "gemma3:27b")
    
    Example:
        # Load from environment
        config = BackendConfig.from_env()
        
        # Or create manually
        config = BackendConfig(
            available_backends=["claude", "ollama"],
            primary_backend="claude",
            secondary_backend="ollama"
        )
    """
    
    available_backends: list[str] = Field(
        default=["claude", "ollama"],
        description="List of backend names to make available"
    )
    primary_backend: str = Field(
        default="claude",
        description="Primary backend to try first"
    )
    secondary_backend: Optional[str] = Field(
        default="ollama",
        description="Secondary backend for fallback"
    )
    selection_strategy: str = Field(
        default="sequential",
        description="Selection strategy: 'sequential', 'primary_only', 'parallel'"
    )
    
    # Backend-specific configuration
    claude_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key (required for Claude backend)"
    )
    ollama_base_url: str = Field(
        default="http://192.168.7.187:11434",
        description="Ollama server URL"
    )
    ollama_model: str = Field(
        default="gemma3:27b",
        description="Ollama model to use"
    )
    
    @field_validator("selection_strategy")
    @classmethod
    def validate_strategy(cls, v):
        """Ensure selection strategy is valid"""
        valid = ["sequential", "primary_only", "parallel"]
        if v not in valid:
            raise ValueError(
                f"selection_strategy must be one of: {', '.join(valid)}"
            )
        return v
    
    @field_validator("primary_backend")
    @classmethod
    def validate_primary_backend(cls, v):
        """Ensure primary backend name is not empty"""
        if not v or not v.strip():
            raise ValueError("primary_backend cannot be empty")
        return v.strip()
    
    @classmethod
    def from_env(cls) -> "BackendConfig":
        """
        Load configuration from environment variables.
        
        Falls back to defaults for any missing variables.
        This enables flexible deployment without code changes.
        
        Returns:
            BackendConfig: Configuration loaded from environment
        
        Example:
            # Set environment variables
            os.environ["PRIMARY_BACKEND"] = "ollama"
            os.environ["CLAUDE_API_KEY"] = "sk-..."
            
            # Load config
            config = BackendConfig.from_env()
            assert config.primary_backend == "ollama"
        """
        # Parse available backends from comma-separated string
        available_str = os.getenv("AVAILABLE_BACKENDS", "claude,ollama")
        available = [b.strip() for b in available_str.split(",") if b.strip()]
        
        # Load other settings
        primary = os.getenv("PRIMARY_BACKEND", "claude")
        secondary = os.getenv("SECONDARY_BACKEND", "ollama")
        strategy = os.getenv("BACKEND_SELECTION_STRATEGY", "sequential")
        
        # Backend-specific settings
        claude_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://192.168.7.187:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:27b")
        
        return cls(
            available_backends=available,
            primary_backend=primary,
            secondary_backend=secondary if secondary else None,
            selection_strategy=strategy,
            claude_api_key=claude_key,
            ollama_base_url=ollama_url,
            ollama_model=ollama_model,
        )
    
    def is_backend_available(self, backend_name: str) -> bool:
        """
        Check if a backend is configured as available.
        
        Args:
            backend_name: Name of backend to check
        
        Returns:
            bool: True if backend is in available_backends list
        
        Example:
            config = BackendConfig.from_env()
            if config.is_backend_available("claude"):
                # Claude is available
                pass
        """
        return backend_name in self.available_backends
    
    def get_timeout_for_backend(self, backend_name: str) -> int:
        """
        Get appropriate timeout for a backend.
        
        Different backends have different performance characteristics.
        Ollama with large models needs more time.
        
        Args:
            backend_name: Name of backend
        
        Returns:
            int: Timeout in seconds
        """
        timeouts = {
            "claude": 30,      # Claude API is fast
            "ollama": 120,     # Large local models need time (increased for 30b)
            "lmstudio": 60,    # Local LLM via OpenAI API needs time
            "mock": 5,         # Mock is instant
        }
        return timeouts.get(backend_name, 30)
