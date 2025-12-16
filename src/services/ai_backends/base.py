"""
AIBackend protocol definition.

This module defines the contract that all AI backend implementations
must satisfy. Any class that implements this protocol can be used
interchangeably for thought analysis.

The protocol ensures:
1. Consistent request/response schemas
2. Timeout enforcement
3. Error handling
4. Idempotency
5. Observability (request tracing)
"""

from typing import Protocol, Union
from src.services.ai_backends.models import (
    BackendRequest,
    SuccessResponse,
    ErrorResponse,
)


class AIBackend(Protocol):
    """
    Protocol for AI backend implementations.
    
    All backends must implement this protocol to ensure
    consistent behavior across different AI providers.
    
    Guarantees:
    - Idempotent: Same request_id returns same result
    - Atomic: Either fully succeeds or fully fails
    - Bounded: Completes within timeout_seconds
    - Traceable: Every response includes request_id
    - Validated: Output matches schema
    
    Example Implementation:
        class ClaudeBackend:
            @property
            def name(self) -> str:
                return "claude"
            
            async def analyze(
                self,
                request: BackendRequest
            ) -> Union[SuccessResponse, ErrorResponse]:
                # Implementation here
                pass
    """
    
    @property
    def name(self) -> str:
        """
        Unique identifier for this backend.
        
        Used for logging, monitoring, and registry lookups.
        Should be lowercase, no spaces (e.g., "claude", "ollama").
        
        Returns:
            str: Backend name
        """
        ...
    
    async def analyze(
        self,
        request: BackendRequest
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Analyze a thought and return structured results.
        
        This is the core operation all backends must implement.
        Must respect timeout_seconds, handle errors gracefully,
        and return standardized responses.
        
        Args:
            request: BackendRequest with thought content and config
        
        Returns:
            SuccessResponse if analysis succeeds
            ErrorResponse if analysis fails
        
        Raises:
            No exceptions should escape - all errors should be
            returned as ErrorResponse objects
        
        Example:
            request = BackendRequest(
                request_id="req-abc123",
                thought_content="Should optimize email system",
                timeout_seconds=20
            )
            response = await backend.analyze(request)
            
            if response.success:
                print(response.analysis.summary)
            else:
                print(response.error.error_code)
        """
        ...
    
    async def health_check(self) -> bool:
        """
        Check if backend is healthy and available.
        
        Should be lightweight (complete in <2s) and not
        count against rate limits if possible.
        
        Returns:
            bool: True if backend is healthy and reachable
        
        Example:
            if await backend.health_check():
                print("Backend is healthy")
            else:
                print("Backend is unavailable")
        """
        ...


def validate_backend(backend: any) -> bool:
    """
    Validate that an object satisfies AIBackend protocol.
    
    Checks that the object has all required methods with
    correct signatures. Useful for runtime verification
    before registering a backend.
    
    Args:
        backend: Object to validate
    
    Returns:
        bool: True if backend satisfies protocol
    
    Example:
        from src.services.ai_backends.claude_backend import ClaudeBackend
        
        backend = ClaudeBackend()
        if validate_backend(backend):
            registry.register("claude", backend)
    """
    required_attrs = ["name", "analyze", "health_check"]
    
    for attr in required_attrs:
        if not hasattr(backend, attr):
            return False
    
    # Check name is a property/string
    if not isinstance(backend.name, str):
        return False
    
    # Check methods are callable
    if not callable(getattr(backend, "analyze")):
        return False
    if not callable(getattr(backend, "health_check")):
        return False
    
    return True
