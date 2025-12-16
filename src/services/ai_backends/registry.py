"""
Central registry for managing AI backends.

Provides a single source of truth for available backends,
enabling runtime backend selection and swapping without
changing business logic.
"""

import logging
from typing import Dict, List, Optional

from src.services.ai_backends.base import AIBackend, validate_backend
from src.services.ai_backends.exceptions import BackendError


logger = logging.getLogger(__name__)


class AIBackendRegistry:
    """
    Registry of available AI backends.
    
    Manages backend registration, retrieval, and lifecycle.
    Acts as a service locator for backend implementations.
    
    Example:
        # Register backends
        AIBackendRegistry.register("claude", ClaudeBackend())
        AIBackendRegistry.register("ollama", OllamaBackend())
        
        # Retrieve backend
        backend = AIBackendRegistry.get("claude")
        response = await backend.analyze(request)
        
        # List available
        backends = AIBackendRegistry.list_available()
    """
    
    _backends: Dict[str, AIBackend] = {}
    _default: Optional[str] = None
    
    @classmethod
    def register(
        cls,
        name: str,
        backend: AIBackend
    ) -> None:
        """
        Register a backend.
        
        Args:
            name: Unique backend identifier
            backend: Backend implementation
        
        Raises:
            ValueError: If name is empty or backend invalid
            
        Example:
            registry.register("claude", ClaudeBackend())
        """
        if not name or not name.strip():
            raise ValueError("Backend name cannot be empty")
        
        if not validate_backend(backend):
            raise ValueError(
                f"Backend '{name}' does not satisfy AIBackend protocol"
            )
        
        cls._backends[name] = backend
        logger.info(f"Registered backend: {name}")
        
        # Set as default if first backend
        if cls._default is None:
            cls._default = name
            logger.info(f"Set default backend: {name}")
    
    @classmethod
    def get(cls, name: str) -> AIBackend:
        """
        Retrieve backend by name.
        
        Args:
            name: Backend identifier
        
        Returns:
            AIBackend: Registered backend
        
        Raises:
            KeyError: If backend not registered
            
        Example:
            backend = registry.get("claude")
        """
        if name not in cls._backends:
            available = ", ".join(cls._backends.keys())
            raise KeyError(
                f"Backend '{name}' not registered. "
                f"Available: {available}"
            )
        
        return cls._backends[name]
    
    @classmethod
    def get_default(cls) -> Optional[AIBackend]:
        """
        Get default backend.
        
        Returns:
            AIBackend: Default backend if set
            None: If no backends registered
            
        Example:
            backend = registry.get_default()
            if backend:
                response = await backend.analyze(request)
        """
        if cls._default and cls._default in cls._backends:
            return cls._backends[cls._default]
        return None
    
    @classmethod
    def set_default(cls, name: str) -> None:
        """
        Set default backend.
        
        Args:
            name: Backend identifier
        
        Raises:
            KeyError: If backend not registered
            
        Example:
            registry.set_default("ollama")
        """
        if name not in cls._backends:
            available = ", ".join(cls._backends.keys())
            raise KeyError(
                f"Cannot set default to '{name}'. "
                f"Available: {available}"
            )
        
        cls._default = name
        logger.info(f"Set default backend: {name}")
    
    @classmethod
    def list_available(cls) -> List[str]:
        """
        List all registered backend names.
        
        Returns:
            list[str]: Backend identifiers
            
        Example:
            backends = registry.list_available()
            print(f"Available backends: {backends}")
        """
        return list(cls._backends.keys())
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Remove a backend from registry.
        
        Args:
            name: Backend identifier
        
        Raises:
            KeyError: If backend not registered
            
        Example:
            registry.unregister("old-backend")
        """
        if name not in cls._backends:
            raise KeyError(f"Backend '{name}' not registered")
        
        del cls._backends[name]
        logger.info(f"Unregistered backend: {name}")
        
        # Clear default if it was removed
        if cls._default == name:
            cls._default = None
            # Set new default if others available
            if cls._backends:
                cls._default = next(iter(cls._backends))
                logger.info(f"New default backend: {cls._default}")
    
    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered backends.
        
        Used primarily for testing to reset state.
        
        Example:
            # In test teardown
            registry.clear()
        """
        cls._backends.clear()
        cls._default = None
        logger.info("Cleared all backends")
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if backend is registered.
        
        Args:
            name: Backend identifier
        
        Returns:
            bool: True if registered
            
        Example:
            if registry.is_registered("claude"):
                backend = registry.get("claude")
        """
        return name in cls._backends
    
    @classmethod
    async def health_check_all(cls) -> Dict[str, bool]:
        """
        Check health of all registered backends.
        
        Returns:
            dict: {backend_name: is_healthy}
            
        Example:
            health = await registry.health_check_all()
            for name, healthy in health.items():
                if healthy:
                    print(f"{name}: OK")
                else:
                    print(f"{name}: UNHEALTHY")
        """
        health = {}
        
        for name, backend in cls._backends.items():
            try:
                health[name] = await backend.health_check()
            except Exception as e:
                logger.warning(
                    f"Health check failed for {name}: {e}"
                )
                health[name] = False
        
        return health
