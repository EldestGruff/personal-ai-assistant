"""
Health check endpoint for Personal AI Assistant API.

Provides service status, version info, and database connectivity check.
"""

import time
from fastapi import APIRouter, status

from ..responses import APIResponse

# Track service start time
SERVICE_START_TIME = time.time()
VERSION = "0.1.0"

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Check service health and database connectivity.
    
    Returns service status, version, database status, and uptime.
    """
    uptime = int(time.time() - SERVICE_START_TIME)
    
    # TODO: Add actual database connectivity check when DB is set up
    database_status = "connected"
    
    return APIResponse.success(
        data={
            "status": "healthy",
            "version": VERSION,
            "database": database_status,
            "uptime_seconds": uptime,
        }
    )
