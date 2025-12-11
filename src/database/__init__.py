"""
Database package for Personal AI Assistant.

Provides SQLAlchemy session management, connection pooling,
and database utilities for SQLite persistence.
"""

from .session import (
    engine,
    SessionLocal,
    get_db,
    init_db
)

# Re-export models from models package for convenience
from ..models.base import Base
from ..models.thought import ThoughtDB
from ..models.task import TaskDB
from ..models.context import ContextDB
from ..models.analysis import ClaudeAnalysisDB

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "Base",
    "ThoughtDB",
    "TaskDB",
    "ContextDB",
    "ClaudeAnalysisDB",
]
