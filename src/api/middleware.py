"""
Middleware for Personal AI Assistant API.

Provides rate limiting to prevent abuse and manage Claude API costs.
Also handles service exception conversion to API responses.
Uses in-memory storage (good enough for single-user MVP).
"""

import logging
import time
from collections import defaultdict
from typing import Callable, Dict

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..services.exceptions import (
    ServiceError,
    NotFoundError,
    UnauthorizedError,
    InvalidDataError,
    DatabaseError
)
from .responses import RateLimitError, APIResponse


logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter with sliding window.
    
    Tracks requests per API key and enforces limits.
    """
    
    def __init__(self):
        # Structure: {api_key: [(timestamp, endpoint), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        
        # Rate limits (requests per minute)
        self.limits = {
            "default": 1000,  # General CRUD operations (relaxed for single user)
            "claude": 60,     # Claude API calls (relaxed)
        }
    
    def _clean_old_requests(self, api_key: str, window_seconds: int = 60):
        """Remove requests older than window."""
        cutoff = time.time() - window_seconds
        self.requests[api_key] = [
            (ts, endpoint) for ts, endpoint in self.requests[api_key]
            if ts > cutoff
        ]
    
    def check_rate_limit(self, api_key: str, endpoint: str) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Returns:
            tuple: (allowed, limit, remaining)
        """
        # Determine which limit applies
        if "/consciousness-check" in endpoint or "/claude" in endpoint:
            limit = self.limits["claude"]
        else:
            limit = self.limits["default"]
        
        # Clean old requests
        self._clean_old_requests(api_key)
        
        # Count recent requests
        current_count = len(self.requests[api_key])
        remaining = max(0, limit - current_count)
        allowed = current_count < limit
        
        # Record this request if allowed
        if allowed:
            self.requests[api_key].append((time.time(), endpoint))
        
        return allowed, limit, remaining


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Rate limiting disabled for single-user instance
        # Extract API key from Authorization header
        # auth_header = request.headers.get("authorization", "")
        # api_key = "unknown"
        # if auth_header.startswith("Bearer "):
        #     api_key = auth_header[7:]
        
        # Check rate limit
        # endpoint = request.url.path
        # allowed, limit, remaining = rate_limiter.check_rate_limit(api_key, endpoint)
        
        # If rate limited, return error
        # if not allowed:
        #     raise RateLimitError(retry_after=60)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers (dummy values)
        # response.headers["RateLimit-Limit"] = str(limit)
        # response.headers["RateLimit-Remaining"] = str(remaining)
        # response.headers["RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response


async def service_exception_handler(request: Request, exc: ServiceError) -> Response:
    """
    Convert service layer exceptions to API responses.
    
    Provides consistent error formatting and appropriate HTTP status codes
    for all service-layer exceptions.
    
    Args:
        request: FastAPI request object
        exc: Service exception to convert
        
    Returns:
        JSONResponse with appropriate status code and error details
    """
    if isinstance(exc, NotFoundError):
        logger.warning(f"NotFoundError: {exc}")
        return APIResponse.error(
            code=f"{exc.resource_type.upper()}_NOT_FOUND",
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    elif isinstance(exc, UnauthorizedError):
        logger.warning(f"UnauthorizedError: {exc}")
        return APIResponse.error(
            code="FORBIDDEN",
            message=str(exc),
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    elif isinstance(exc, InvalidDataError):
        logger.warning(f"InvalidDataError: {exc}")
        return APIResponse.error(
            code="INVALID_DATA",
            message=str(exc),
            details=exc.details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    elif isinstance(exc, DatabaseError):
        logger.error(f"DatabaseError: {exc}")
        # Don't expose internal database details to client
        return APIResponse.error(
            code="DATABASE_ERROR",
            message="Internal server error (database operation failed)",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    else:
        # Catch-all for other ServiceError subclasses
        logger.error(f"ServiceError: {exc}")
        return APIResponse.error(
            code="SERVICE_ERROR",
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
