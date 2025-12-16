"""
API route handlers for Personal AI Assistant.

Organizes endpoints by resource type.
"""

from .health import router as health_router
from .thoughts import router as thoughts_router
from .tasks import router as tasks_router
from .claude import router as claude_router
from .consciousness_v2 import router as consciousness_v2_router

__all__ = [
    "health_router",
    "thoughts_router",
    "tasks_router",
    "claude_router",
    "consciousness_v2_router",
]
