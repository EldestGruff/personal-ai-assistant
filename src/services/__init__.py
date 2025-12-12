"""
Service layer for the Personal AI Assistant.

Provides business logic and database operations for thoughts, tasks,
contexts, and Claude analysis results. All services enforce ownership
validation and proper error handling.

Usage:
    from src.services import ThoughtService, TaskService
    
    # In a route handler
    thought_service = ThoughtService(db_session)
    thought = thought_service.create_thought(
        user_id=user.id,
        content="My thought",
        tags=["tag1"]
    )
"""

from .exceptions import (
    ServiceError,
    NotFoundError,
    UnauthorizedError,
    InvalidDataError,
    DatabaseError,
    ConflictError
)

from .thought_service import ThoughtService
from .task_service import TaskService
from .context_service import ContextService
from .claude_analysis_service import ClaudeAnalysisService


__all__ = [
    # Exceptions
    "ServiceError",
    "NotFoundError",
    "UnauthorizedError",
    "InvalidDataError",
    "DatabaseError",
    "ConflictError",
    # Services
    "ThoughtService",
    "TaskService",
    "ContextService",
    "ClaudeAnalysisService",
]
