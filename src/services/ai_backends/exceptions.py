"""
Custom exceptions for AI backend operations.

These exceptions map backend-specific errors to standardized
error codes, enabling consistent error handling across all backends.
"""


class BackendError(Exception):
    """Base exception for all backend errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        backend_name: str,
        recoverable: bool = False
    ):
        """
        Initialize backend error
        
        Args:
            message: Human-readable error message
            error_code: Standardized error code
            backend_name: Name of backend that raised error
            recoverable: Whether retry might succeed
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.backend_name = backend_name
        self.recoverable = recoverable


class BackendTimeoutError(BackendError):
    """Request exceeded timeout threshold"""
    
    def __init__(self, backend_name: str, timeout_seconds: int):
        super().__init__(
            message=f"Backend '{backend_name}' timeout after {timeout_seconds}s",
            error_code="TIMEOUT",
            backend_name=backend_name,
            recoverable=True
        )
        self.timeout_seconds = timeout_seconds


class BackendUnavailableError(BackendError):
    """Backend service is unreachable"""
    
    def __init__(self, backend_name: str, details: str = ""):
        super().__init__(
            message=f"Backend '{backend_name}' unavailable: {details}",
            error_code="UNAVAILABLE",
            backend_name=backend_name,
            recoverable=True
        )


class BackendRateLimitError(BackendError):
    """Backend rate limit exceeded"""
    
    def __init__(
        self,
        backend_name: str,
        retry_after: int = None
    ):
        message = f"Backend '{backend_name}' rate limited"
        if retry_after:
            message += f", retry after {retry_after}s"
        
        super().__init__(
            message=message,
            error_code="RATE_LIMITED",
            backend_name=backend_name,
            recoverable=True
        )
        self.retry_after = retry_after


class BackendInvalidInputError(BackendError):
    """Request validation failed"""
    
    def __init__(self, backend_name: str, details: str):
        super().__init__(
            message=f"Invalid input: {details}",
            error_code="INVALID_INPUT",
            backend_name=backend_name,
            recoverable=False
        )


class BackendContextOverflowError(BackendError):
    """Content exceeds backend context window"""
    
    def __init__(
        self,
        backend_name: str,
        content_length: int,
        max_length: int
    ):
        super().__init__(
            message=(
                f"Content length {content_length} exceeds "
                f"backend '{backend_name}' max {max_length}"
            ),
            error_code="CONTEXT_OVERFLOW",
            backend_name=backend_name,
            recoverable=False
        )
        self.content_length = content_length
        self.max_length = max_length


class BackendMalformedResponseError(BackendError):
    """Backend returned invalid response"""
    
    def __init__(self, backend_name: str, details: str):
        super().__init__(
            message=f"Malformed response from '{backend_name}': {details}",
            error_code="MALFORMED_RESPONSE",
            backend_name=backend_name,
            recoverable=False
        )


class BackendInternalError(BackendError):
    """Unexpected internal error"""
    
    def __init__(self, backend_name: str, details: str):
        super().__init__(
            message=f"Internal error in '{backend_name}': {details}",
            error_code="INTERNAL_ERROR",
            backend_name=backend_name,
            recoverable=False
        )
