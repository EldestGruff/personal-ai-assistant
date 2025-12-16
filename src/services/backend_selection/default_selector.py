"""
Default Backend Selector

Implements SEQUENTIAL strategy: try primary first, fallback to secondary.

This is the recommended strategy for production: it provides reliability
through fallback while preferring the higher-quality primary backend.
"""

from src.services.backend_selection.models import (
    BackendSelectionRequest,
    BackendSelectionResponse,
    BackendChoice,
)
from src.services.backend_selection.config import BackendConfig


class DefaultSelector:
    """
    Default backend selector using SEQUENTIAL strategy.
    
    Decision Logic:
    1. Primary backend (from config) is first choice
    2. Secondary backend (from config) is fallback
    3. If primary unavailable, secondary becomes primary
    4. If both unavailable, error
    
    The selector provides clear reasoning for every decision
    to enable observability and debugging.
    
    Example:
        config = BackendConfig.from_env()
        selector = DefaultSelector(config)
        
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=150,
            analysis_type="standard",
            available_backends=["claude", "ollama"]
        )
        
        response = await selector.select_backends(request)
        # Primary: claude
        # Fallback: ollama
    """
    
    def __init__(self, config: BackendConfig):
        """
        Initialize selector with configuration.
        
        Args:
            config: Backend configuration
        """
        self.config = config
    
    async def select_backends(
        self,
        request: BackendSelectionRequest
    ) -> BackendSelectionResponse:
        """
        Select backends using SEQUENTIAL strategy.
        
        Tries primary backend first, falls back to secondary
        if primary fails. Decision based on config + availability.
        
        Args:
            request: Selection request with context
        
        Returns:
            BackendSelectionResponse: Decision with reasoning
        
        Raises:
            ValueError: If no backends available
        """
        available_set = set(request.available_backends)
        
        # Build primary/fallback lists
        primary = self._select_primary(available_set)
        fallback = self._select_fallback(available_set, primary)
        reasoning = self._build_reasoning(primary, fallback)
        
        # Validate we have at least primary
        if not primary:
            raise ValueError(
                f"No backends available. Configured primary "
                f"'{self.config.primary_backend}' and secondary "
                f"'{self.config.secondary_backend}' are not in "
                f"available list: {request.available_backends}"
            )
        
        return BackendSelectionResponse(
            request_id=request.request_id,
            decision_type="SEQUENTIAL",
            backends=primary,
            fallback_backends=fallback,
            reasoning=reasoning
        )
    
    def _select_primary(
        self,
        available: set[str]
    ) -> list[BackendChoice]:
        """
        Select primary backend.
        
        Args:
            available: Set of available backend names
        
        Returns:
            list[BackendChoice]: Primary backend (if available)
        """
        primary_name = self.config.primary_backend
        
        if primary_name in available:
            timeout = self.config.get_timeout_for_backend(primary_name)
            return [
                BackendChoice(
                    name=primary_name,
                    role="primary",
                    timeout_seconds=timeout
                )
            ]
        
        # Primary not available, try secondary as primary
        secondary_name = self.config.secondary_backend
        if secondary_name and secondary_name in available:
            timeout = self.config.get_timeout_for_backend(secondary_name)
            return [
                BackendChoice(
                    name=secondary_name,
                    role="primary",
                    timeout_seconds=timeout
                )
            ]
        
        # Neither available
        return []
    
    def _select_fallback(
        self,
        available: set[str],
        primary: list[BackendChoice]
    ) -> list[BackendChoice]:
        """
        Select fallback backend.
        
        Args:
            available: Set of available backend names
            primary: Already-selected primary
        
        Returns:
            list[BackendChoice]: Fallback backend (if available)
        """
        if not primary:
            return []
        
        primary_name = primary[0].name
        secondary_name = self.config.secondary_backend
        
        # If primary is actually primary, secondary is fallback
        if (
            primary_name == self.config.primary_backend
            and secondary_name
            and secondary_name in available
        ):
            timeout = self.config.get_timeout_for_backend(secondary_name)
            return [
                BackendChoice(
                    name=secondary_name,
                    role="fallback",
                    timeout_seconds=timeout
                )
            ]
        
        # No fallback available
        return []
    
    def _build_reasoning(
        self,
        primary: list[BackendChoice],
        fallback: list[BackendChoice]
    ) -> str:
        """
        Build human-readable reasoning for decision.
        
        Args:
            primary: Primary backend choice(s)
            fallback: Fallback backend choice(s)
        
        Returns:
            str: Reasoning explanation
        """
        if not primary:
            return (
                f"No backends available from config "
                f"(primary={self.config.primary_backend}, "
                f"secondary={self.config.secondary_backend})"
            )
        
        primary_name = primary[0].name
        
        if fallback:
            fallback_name = fallback[0].name
            return (
                f"SEQUENTIAL strategy: {primary_name} primary "
                f"(configured), {fallback_name} fallback (configured). "
                f"Will try {primary_name} first, fall back to "
                f"{fallback_name} on recoverable errors."
            )
        else:
            return (
                f"SEQUENTIAL strategy: {primary_name} primary "
                f"(configured), no fallback available. "
                f"Will fail if {primary_name} encounters errors."
            )
