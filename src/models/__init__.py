"""
Personal AI Assistant - Data Models

This module provides all data models for the Personal AI Assistant including:
- Base classes for common functionality
- Enums for type constraints
- Pydantic models for API validation
- SQLAlchemy ORM models for database persistence

Models represent thoughts, tasks, contexts, and Claude analysis results.
"""

# Base classes
from .base import (
    Base,
    BaseTimestampModel,
    BaseRequestModel,
    BaseDBModel,
    utc_now,
    validate_content_length
)

# Enums
from .enums import (
    ThoughtStatus,
    TaskStatus,
    Priority,
    TimeOfDay,
    EnergyLevel,
    FocusState,
    AnalysisType,
    # Phase 3B RBAC enums
    UserRole,
    Permission,
    ROLE_PERMISSIONS,
    # Phase 3B Settings enums
    SettingsDepthType,
    TaskSuggestionMode,
    ScheduledAnalysisStatus,
)


# User models
from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserDB
)

# Thought models
from .thought import (
    ThoughtCreate,
    ThoughtUpdate,
    ThoughtResponse,
    ThoughtDB
)

# Task models
from .task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskDB
)

# Context models
from .context import (
    ContextCreate,
    ContextResponse,
    ContextDB
)

# Claude analysis models
from .analysis import (
    ClaudeAnalysisCreate,
    ClaudeAnalysisResponse,
    ClaudeAnalysisDB
)

# Phase 3B: Settings models
from .settings import (
    UserSettingsCreate,
    UserSettingsUpdate,
    UserSettingsResponse,
    AnalysisDepthConfig,
    UserSettingsDB,
)

# Phase 3B: Scheduled analysis models
from .scheduled_analysis import (
    ScheduledAnalysisCreate,
    ScheduledAnalysisResponse,
    ScheduledAnalysisHistoryResponse,
    ScheduledAnalysisDB,
)


# Export all models for clean imports
__all__ = [
    # Base classes
    "Base",
    "BaseTimestampModel",
    "BaseRequestModel",
    "BaseDBModel",
    "utc_now",
    "validate_content_length",
    # Enums
    "ThoughtStatus",
    "TaskStatus",
    "Priority",
    "TimeOfDay",
    "EnergyLevel",
    "FocusState",
    "AnalysisType",
    # Phase 3B RBAC enums
    "UserRole",
    "Permission",
    "ROLE_PERMISSIONS",
    # Phase 3B Settings enums
    "SettingsDepthType",
    "TaskSuggestionMode",
    "ScheduledAnalysisStatus",
    # User models
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserDB",
    # Thought models
    "ThoughtCreate",
    "ThoughtUpdate",
    "ThoughtResponse",
    "ThoughtDB",
    # Task models
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskDB",
    # Context models
    "ContextCreate",
    "ContextResponse",
    "ContextDB",
    # Analysis models
    "ClaudeAnalysisCreate",
    "ClaudeAnalysisResponse",
    "ClaudeAnalysisDB",
    # Phase 3B: Settings models
    "UserSettingsCreate",
    "UserSettingsUpdate",
    "UserSettingsResponse",
    "AnalysisDepthConfig",
    "UserSettingsDB",
    # Phase 3B: Scheduled analysis models
    "ScheduledAnalysisCreate",
    "ScheduledAnalysisResponse",
    "ScheduledAnalysisHistoryResponse",
    "ScheduledAnalysisDB",
]
