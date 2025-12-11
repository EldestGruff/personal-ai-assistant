"""
API authentication for Personal AI Assistant.

Simple API key authentication for MVP. Uses Bearer token in Authorization header.
Future: Add proper API key management, rotation, and per-key rate limiting.
"""

import os
from typing import Optional

from fastapi import Header

from .responses import UnauthorizedError


# Load API key from environment variable
VALID_API_KEY = os.getenv("API_KEY")

if not VALID_API_KEY:
    raise RuntimeError(
        "API_KEY environment variable not set. "
        "Add API_KEY=your-uuid-here to .env file."
    )


async def verify_api_key(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency for API key validation.
    
    Verifies the Authorization header contains a valid Bearer token.
    
    Args:
        authorization: Authorization header value (format: "Bearer {key}")
        
    Returns:
        str: The validated API key
        
    Raises:
        UnauthorizedError: If API key is missing or invalid
    """
    if not authorization:
        raise UnauthorizedError()
    
    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError()
    
    api_key = parts[1]
    
    # Validate against environment variable
    if api_key != VALID_API_KEY:
        raise UnauthorizedError()
    
    return api_key


def get_current_user_id() -> str:
    """
    Get current user ID.
    
    For MVP: Returns hardcoded user UUID.
    Future: Extract from validated API key in database.
    """
    # TODO: Replace with actual user lookup when multi-user support added
    return "550e8400-e29b-41d4-a716-446655440000"
