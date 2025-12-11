"""
Personal AI Assistant - FastAPI Application

Main application entry point with routes, middleware, and error handling.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .middleware import RateLimitMiddleware
from .responses import APIResponse, APIError
from .routes import (
    health_router,
    thoughts_router,
    tasks_router,
    claude_router
)

# Create FastAPI app
app = FastAPI(
    title="Personal AI Assistant API",
    description="Query-based personal AI assistant for thought capture and task management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Global exception handler for APIError
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle custom API errors with standard format."""
    return APIResponse.error(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        status_code=exc.status_code
    )

# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions gracefully."""
    return APIResponse.error(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
        details={"error": str(exc)},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

# Include all route handlers
app.include_router(health_router, prefix="/api/v1")
app.include_router(thoughts_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(claude_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint."""
    return APIResponse.success(
        data={
            "name": "Personal AI Assistant API",
            "version": "0.1.0",
            "status": "operational",
            "documentation": "/docs",
            "health_check": "/api/v1/health"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup."""
    print("🚀 Personal AI Assistant API starting up...")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/api/v1/health")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    print("👋 Personal AI Assistant API shutting down...")
