"""
Backend Selection & Orchestration

Decision-making layer that determines which backend(s) to use
and orchestrates execution with automatic fallback.

Components:
- BackendSelector: Protocol for decision-making
- DefaultSelector: SEQUENTIAL strategy implementation
- BackendOrchestrator: Execution with automatic fallback
- BackendConfig: Environment-based configuration

Example:
    # Initialize
    config = BackendConfig.from_env()
    selector = DefaultSelector(config)
    orchestrator = BackendOrchestrator(registry, selector)
    
    # Analyze with automatic fallback
    response = await orchestrator.analyze_with_fallback(
        request=backend_request,
        thought_length=len(thought.content)
    )
"""

from src.services.backend_selection.models import (
    BackendSelectionRequest,
    BackendChoice,
    BackendSelectionResponse,
)
from src.services.backend_selection.config import BackendConfig
from src.services.backend_selection.base import BackendSelector
from src.services.backend_selection.default_selector import DefaultSelector
from src.services.backend_selection.orchestrator import BackendOrchestrator

__all__ = [
    "BackendSelectionRequest",
    "BackendChoice",
    "BackendSelectionResponse",
    "BackendConfig",
    "BackendSelector",
    "DefaultSelector",
    "BackendOrchestrator",
]
