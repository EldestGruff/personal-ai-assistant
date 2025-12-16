"""
Backend Selector Protocol

Protocol defining the contract for backend selection logic.

Any backend selector must implement this protocol to enable
pluggable selection strategies.
"""

from typing import Protocol, runtime_checkable

from src.services.backend_selection.models import (
    BackendSelectionRequest,
    BackendSelectionResponse,
)


@runtime_checkable
class BackendSelector(Protocol):
    """
    Protocol for backend selection strategies.
    
    Implementations must provide logic to:
    1. Analyze the request context
    2. Decide which backend(s) to use
    3. Provide reasoning for the decision
    
    Different selectors can implement different strategies:
    - SEQUENTIAL: Try primary, fallback to secondary
    - PRIMARY_ONLY: Only use primary, fail if unavailable
    - PARALLEL: Try multiple backends simultaneously
    - COST_OPTIMIZED: Choose cheapest available option
    
    Example:
        class MyCustomSelector:
            async def select_backends(
                self, request: BackendSelectionRequest
            ) -> BackendSelectionResponse:
                # Custom decision logic
                return response
        
        # Verify it satisfies protocol
        assert isinstance(MyCustomSelector(), BackendSelector)
    """
    
    async def select_backends(
        self,
        request: BackendSelectionRequest
    ) -> BackendSelectionResponse:
        """
        Select which backend(s) to use for a request.
        
        Analyzes request context (thought length, analysis type,
        available backends, user preferences) and returns a
        decision about which backend(s) to try.
        
        Args:
            request: Selection request with context
        
        Returns:
            BackendSelectionResponse: Decision with reasoning
        
        Example:
            selector = DefaultSelector(config)
            
            request = BackendSelectionRequest(
                request_id="req-123",
                thought_length=150,
                analysis_type="standard",
                available_backends=["claude", "ollama"]
            )
            
            response = await selector.select_backends(request)
            print(response.backends[0].name)  # "claude"
            print(response.reasoning)  # "Claude primary per config"
        """
        ...


def validate_selector(selector: object) -> bool:
    """
    Validate that an object implements BackendSelector protocol.
    
    Args:
        selector: Object to validate
    
    Returns:
        bool: True if selector implements protocol
    
    Raises:
        TypeError: If selector doesn't implement protocol
    
    Example:
        selector = DefaultSelector(config)
        
        # Validate
        assert validate_selector(selector)
        
        # Invalid object
        invalid = object()
        try:
            validate_selector(invalid)
        except TypeError:
            print("Invalid selector")
    """
    if not isinstance(selector, BackendSelector):
        raise TypeError(
            f"Object {type(selector).__name__} does not implement "
            f"BackendSelector protocol. Must have 'select_backends' method."
        )
    
    # Verify method signature
    if not hasattr(selector, "select_backends"):
        raise TypeError(
            f"{type(selector).__name__} missing 'select_backends' method"
        )
    
    if not callable(selector.select_backends):
        raise TypeError(
            f"{type(selector).__name__}.select_backends must be callable"
        )
    
    return True
