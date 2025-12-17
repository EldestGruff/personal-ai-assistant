"""
Personal AI Assistant - FastAPI Application

Main application entry point with routes, middleware, and error handling.
"""

# Load environment variables FIRST, before any imports that need them
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import os
from pathlib import Path

from .middleware import RateLimitMiddleware, service_exception_handler
from .responses import APIResponse, APIError
from .routes import (
    health_router,
    thoughts_router,
    tasks_router,
    claude_router,
    consciousness_v2_router
)
from ..services.exceptions import ServiceError

# Create FastAPI app
app = FastAPI(
    title="Personal AI Assistant API",
    description="Query-based personal AI assistant for thought capture and task management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
# Allow all origins for iOS Shortcuts and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Global exception handler for ServiceError
@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    """Handle service layer exceptions with standard format."""
    return await service_exception_handler(request, exc)

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

# Global exception handler for Pydantic validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic validation errors to standard API format."""
    # Extract first error for cleaner message
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        field = ' -> '.join(str(loc) for loc in first_error['loc'])
        message = f"Invalid {field}: {first_error['msg']}"
    else:
        message = "Validation error"
    
    # Ensure errors are JSON serializable by converting to dict with only serializable values
    serializable_errors = []
    for error in errors:
        serializable_errors.append({
            "loc": [str(loc) for loc in error.get("loc", [])],
            "msg": str(error.get("msg", "")),
            "type": str(error.get("type", ""))
        })
    
    return APIResponse.error(
        code="INVALID_CONTENT",
        message=message,
        details={"validation_errors": serializable_errors},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
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
app.include_router(consciousness_v2_router, prefix="/api/v1")

# Mount static files for web dashboard
# Look for web directory relative to this file
web_dir = Path(__file__).parent.parent.parent / "web"
if web_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(web_dir), html=True), name="dashboard")
    print(f"📱 Dashboard mounted at /dashboard from {web_dir}")

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
            "health_check": "/api/v1/health",
            "dashboard": "/dashboard"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup."""
    print("🚀 Personal AI Assistant API starting up...")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/api/v1/health")

    # Initialize backend system (Phase 2B)
    await initialize_backend_system()

    # Start the background scheduler
    from ..services.scheduler_service import get_scheduler
    scheduler = get_scheduler()
    scheduler.start_consciousness_check_schedule()
    print("⏰ Background scheduler started")


async def initialize_backend_system():
    """
    Initialize AI backends, orchestration, and metrics.
    
    Sets up:
    - Backend registry with available backends
    - Backend selector for choosing backends
    - Backend orchestrator for execution with fallback
    - Thought analyzer for high-level analysis
    - Metrics collector for performance tracking
    """
    from ..services.ai_backends import AIBackendRegistry
    from ..services.ai_backends.claude_backend import ClaudeBackend
    from ..services.ai_backends.ollama_backend import OllamaBackend
    from ..services.ai_backends.mock_backend import MockBackend
    from ..services.backend_selection.config import BackendConfig
    from ..services.backend_selection.default_selector import DefaultSelector
    from ..services.backend_selection.orchestrator import BackendOrchestrator
    from ..services.thought_analyzer import ThoughtAnalyzer
    from ..services.metrics import BackendMetrics
    
    print("🔧 Initializing backend system...")
    
    # Load configuration from environment
    config = BackendConfig.from_env()
    print(f"   Primary backend: {config.primary_backend}")
    print(f"   Secondary backend: {config.secondary_backend}")
    print(f"   Strategy: {config.selection_strategy}")
    
    # Create registry
    registry = AIBackendRegistry()
    
    # Register Claude if available
    if config.is_backend_available("claude"):
        if config.claude_api_key:
            try:
                claude = ClaudeBackend(api_key=config.claude_api_key)
                registry.register("claude", claude)
                print("   ✅ Claude backend registered")
            except Exception as e:
                print(f"   ⚠️  Claude backend failed to initialize: {e}")
        else:
            print("   ⚠️  Claude backend enabled but no API key found")
    
    # Register Ollama if available
    if config.is_backend_available("ollama"):
        try:
            ollama = OllamaBackend(
                base_url=config.ollama_base_url,
                model=config.ollama_model
            )
            registry.register("ollama", ollama)
            print(f"   ✅ Ollama backend registered ({config.ollama_model})")
        except Exception as e:
            print(f"   ⚠️  Ollama backend failed to initialize: {e}")
    
    # Register Mock backend if available
    if config.is_backend_available("mock"):
        try:
            mock = MockBackend(mode="mock-success")
            registry.register("mock", mock)
            print("   ✅ Mock backend registered")
        except Exception as e:
            print(f"   ⚠️  Mock backend failed to initialize: {e}")
    
    # Verify at least one backend is available
    available = registry.list_available()
    if not available:
        print("   ❌ ERROR: No backends available!")
        print("   Set ANTHROPIC_API_KEY or configure Ollama to enable backends")
        # Continue anyway for graceful degradation
    else:
        print(f"   Total available backends: {len(available)}")
    
    # Create selector and orchestrator
    selector = DefaultSelector(config)
    orchestrator = BackendOrchestrator(registry, selector)
    print("   ✅ Orchestrator configured")
    
    # Create analyzer
    analyzer = ThoughtAnalyzer(orchestrator)
    print("   ✅ ThoughtAnalyzer ready")
    
    # Create metrics
    metrics = BackendMetrics()
    print("   ✅ Metrics collector initialized")
    
    # Store in app state for dependency injection
    app.state.backend_registry = registry
    app.state.orchestrator = orchestrator
    app.state.analyzer = analyzer
    app.state.metrics = metrics
    
    # Wire up consciousness_v2 endpoint dependencies
    from .routes import consciousness_v2
    consciousness_v2.set_analyzer(analyzer)
    consciousness_v2.set_metrics(metrics)
    print("   ✅ Consciousness v2 endpoint wired up")
    
    print("✅ Backend system initialized successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    print("👋 Personal AI Assistant API shutting down...")

    # Shutdown the scheduler
    from ..services.scheduler_service import get_scheduler
    try:
        scheduler = get_scheduler()
        scheduler.shutdown()
        print("⏰ Scheduler stopped")
    except Exception as e:
        print(f"Error stopping scheduler: {e}")
