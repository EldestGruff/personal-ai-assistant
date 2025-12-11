"""
Standard API response and error formatting for Personal AI Assistant.

Provides consistent response structure across all endpoints with
proper error handling and request tracking.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from ..models.base import utc_now


def generate_request_id() -> str:
    """Generate unique request ID for tracking."""
    return f"req_{str(uuid4())[:8]}"


class APIResponse:
    """
    Standard API response wrapper.
    
    All successful responses follow this format for consistency.
    """
    
    @staticmethod
    def success(
        data: Any,
        status_code: int = status.HTTP_200_OK,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Create a successful API response."""
        if request_id is None:
            request_id = generate_request_id()
            
        return JSONResponse(
            status_code=status_code,
            content={
                "success": True,
                "data": data,
                "error": None,
                "request_id": request_id,
                "timestamp": utc_now().isoformat()
            }
        )
    
    @staticmethod
    def error(
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Create an error API response."""
        if request_id is None:
            request_id = generate_request_id()
            
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or {}
                },
                "request_id": request_id,
                "timestamp": utc_now().isoformat()
            }
        )


class APIError(HTTPException):
    """Custom exception for API errors."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)


class ThoughtNotFoundError(APIError):
    """Thought with given ID doesn't exist."""
    
    def __init__(self, thought_id: str):
        super().__init__(
            code="THOUGHT_NOT_FOUND",
            message=f"Thought with ID '{thought_id}' not found.",
            details={
                "thought_id": thought_id,
                "suggestion": "Use GET /api/v1/thoughts to list all thoughts."
            },
            status_code=status.HTTP_404_NOT_FOUND
        )


class TaskNotFoundError(APIError):
    """Task with given ID doesn't exist."""
    
    def __init__(self, task_id: str):
        super().__init__(
            code="TASK_NOT_FOUND",
            message=f"Task with ID '{task_id}' not found.",
            details={
                "task_id": task_id,
                "suggestion": "Use GET /api/v1/tasks to list all tasks."
            },
            status_code=status.HTTP_404_NOT_FOUND
        )


class InvalidContentError(APIError):
    """Content validation failed."""
    
    def __init__(self, reason: str):
        super().__init__(
            code="INVALID_CONTENT",
            message=f"Content validation failed: {reason}",
            details={"reason": reason},
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidTagsError(APIError):
    """Tags validation failed."""
    
    def __init__(self, reason: str):
        super().__init__(
            code="INVALID_TAGS",
            message=f"Tags validation failed: {reason}",
            details={"reason": reason},
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UnauthorizedError(APIError):
    """Missing or invalid API key."""
    
    def __init__(self):
        super().__init__(
            code="UNAUTHORIZED",
            message="Missing or invalid API key.",
            details={
                "suggestion": "Include 'Authorization: Bearer YOUR_API_KEY' header."
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class RateLimitError(APIError):
    """Too many requests."""
    
    def __init__(self, retry_after: int):
        super().__init__(
            code="RATE_LIMITED",
            message="Too many requests. Please slow down.",
            details={
                "retry_after_seconds": retry_after,
                "suggestion": f"Wait {retry_after} seconds before retrying."
            },
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class ClaudeAPIError(APIError):
    """Claude API unavailable or error."""
    
    def __init__(self, reason: str):
        super().__init__(
            code="CLAUDE_ERROR",
            message=f"Claude API error: {reason}",
            details={"reason": reason},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
