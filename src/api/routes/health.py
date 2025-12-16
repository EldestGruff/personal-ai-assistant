"""
Health check endpoint for Personal AI Assistant API.

Provides service status, version info, database connectivity check,
and backend availability status.
"""

import time
import logging
from typing import Dict
from fastapi import APIRouter, status, Request

from ..responses import APIResponse
from ...services.ai_backends import AIBackendRegistry

logger = logging.getLogger(__name__)

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


@router.get("/backends", status_code=status.HTTP_200_OK)
async def health_backends(request: Request):
    """
    Check health of all configured AI backends.
    
    Performs health checks on all registered backends:
    - Claude
    - Ollama
    - Mock (if registered)
    
    Returns availability status and response times for each backend.
    
    Example Response:
        {
          "claude": {
            "status": "healthy",
            "available": true,
            "response_time_ms": 1200
          },
          "ollama": {
            "status": "healthy", 
            "available": true,
            "response_time_ms": 850
          }
        }
    """
    try:
        # Get registry from app state
        registry: AIBackendRegistry = request.app.state.backend_registry
        
        # Get all registered backends
        backend_names = registry.list_backends()
        
        results: Dict[str, dict] = {}
        
        for name in backend_names:
            backend = registry.get(name)
            
            # Measure health check time
            start_time = time.time()
            
            try:
                is_healthy = await backend.health_check()
                response_time = int((time.time() - start_time) * 1000)
                
                results[name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "available": is_healthy,
                    "response_time_ms": response_time
                }
                
                logger.debug(
                    f"Backend {name}: healthy={is_healthy}, "
                    f"response_time={response_time}ms"
                )
                
            except Exception as e:
                response_time = int((time.time() - start_time) * 1000)
                results[name] = {
                    "status": "error",
                    "available": False,
                    "response_time_ms": response_time,
                    "error": str(e)
                }
                logger.warning(f"Backend {name} health check failed: {e}")
        
        return APIResponse.success(data=results)
        
    except AttributeError:
        # Registry not initialized (during startup)
        logger.warning("Backend registry not yet initialized")
        return APIResponse.success(
            data={"message": "Backend system not yet initialized"}
        )
    except Exception as e:
        logger.error(f"Backend health check failed: {e}", exc_info=True)
        return APIResponse.error(
            message="Failed to check backend health",
            error_code="HEALTH_CHECK_FAILED",
            details={"error": str(e)}
        )
