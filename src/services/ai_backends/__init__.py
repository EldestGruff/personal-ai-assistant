"""
AI Backend Abstraction Layer

This package provides a protocol-based abstraction for AI backends,
enabling pluggable implementations (Claude, Ollama, Mock) without
changing business logic.

Core Components:
- AIBackend: Protocol that all backends must implement
- BackendRequest/Response: Standardized request/response schemas
- ClaudeBackend: Primary backend using Anthropic API
- OllamaBackend: Fallback backend using local Ollama
- MockBackend: Deterministic backend for testing
- AIBackendRegistry: Central registry for managing backends

Usage:
    from src.services.ai_backends import AIBackendRegistry, BackendRequest
    
    # Get a backend
    backend = AIBackendRegistry.get("claude")
    
    # Analyze a thought
    request = BackendRequest(
        request_id="req-123",
        thought_content="Should optimize email system"
    )
    response = await backend.analyze(request)
"""

from src.services.ai_backends.base import AIBackend
from src.services.ai_backends.models import (
    BackendRequest,
    SuccessResponse,
    ErrorResponse,
    Analysis,
    Theme,
    SuggestedAction,
)
from src.services.ai_backends.registry import AIBackendRegistry
from src.services.ai_backends.exceptions import (
    BackendError,
    BackendTimeoutError,
    BackendUnavailableError,
    BackendRateLimitError,
)

__all__ = [
    "AIBackend",
    "BackendRequest",
    "SuccessResponse",
    "ErrorResponse",
    "Analysis",
    "Theme",
    "SuggestedAction",
    "AIBackendRegistry",
    "BackendError",
    "BackendTimeoutError",
    "BackendUnavailableError",
    "BackendRateLimitError",
]
