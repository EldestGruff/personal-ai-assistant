"""
Middleware for Personal AI Assistant API.

Provides rate limiting to prevent abuse and manage Claude API costs.
Uses in-memory storage (good enough for single-user MVP).
"""

import time
from collections import defaultdict
from typing import Callable, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .responses import RateLimitError


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
            "default": 100,  # General CRUD operations
            "claude": 10,    # Claude API calls (expensive)
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
        # Extract API key from Authorization header
        auth_header = request.headers.get("authorization", "")
        api_key = "unknown"
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
        
        # Check rate limit
        endpoint = request.url.path
        allowed, limit, remaining = rate_limiter.check_rate_limit(api_key, endpoint)
        
        # If rate limited, return error
        if not allowed:
            raise RateLimitError(retry_after=60)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["RateLimit-Limit"] = str(limit)
        response.headers["RateLimit-Remaining"] = str(remaining)
        response.headers["RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
