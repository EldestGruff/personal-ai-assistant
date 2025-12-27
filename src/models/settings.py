"""
Settings models for the Personal AI Assistant.

Defines user-configurable settings for consciousness checks, auto-analysis,
and backend preferences. Supports multi-user architecture with RBAC foundation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseTimestampModel, BaseRequestModel, BaseDBModel, TZDateTime, utc_now
from .enums import SettingsDepthType, TaskSuggestionMode


class UserSettingsCreate(BaseRequestModel):
    """
    Model for creating user settings.
    
    Typically created automatically when a user is created.
    All fields have sensible defaults for ADHD-friendly operation.
    """
    
    # Consciousness Check Settings
    consciousness_check_enabled: bool = Field(
        default=True,
        description="Master on/off switch for automated consciousness checks"
    )
    consciousness_check_interval_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="How often to run consciousness checks (1-1440 minutes)"
    )
    consciousness_check_depth_type: SettingsDepthType = Field(
        default=SettingsDepthType.SMART,
        description="Analysis depth strategy"
    )
    consciousness_check_depth_value: int = Field(
        default=7,
        ge=1,
        description="Value for depth (days or thought count depending on type)"
    )
    consciousness_check_min_thoughts: int = Field(
        default=10,
        ge=1,
        description="Minimum thoughts to analyze for 'smart' mode"
    )
    
    # Auto-Analysis Settings
    auto_tagging_enabled: bool = Field(
        default=True,
        description="Auto-suggest tags when capturing thoughts"
    )
    auto_task_creation_enabled: bool = Field(
        default=True,
        description="Detect tasks from thoughts"
    )
    task_suggestion_mode: TaskSuggestionMode = Field(
        default=TaskSuggestionMode.SUGGEST,
        description="How to handle detected tasks"
    )
    
    # Backend Override Settings
    primary_backend: Optional[str] = Field(
        default=None,
        description="Override primary AI backend (optional)"
    )
    secondary_backend: Optional[str] = Field(
        default=None,
        description="Override secondary/fallback AI backend (optional)"
    )


class UserSettingsUpdate(BaseRequestModel):
    """
    Model for updating user settings.
    
    All fields are optional - only provide fields you want to update.
    Partial updates are supported.
    
    Example:
        >>> update = UserSettingsUpdate(
        ...     consciousness_check_interval_minutes=45,
        ...     task_suggestion_mode="auto_create"
        ... )
    """
    
    consciousness_check_enabled: Optional[bool] = None
    consciousness_check_interval_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        le=1440
    )
    consciousness_check_depth_type: Optional[SettingsDepthType] = None
    consciousness_check_depth_value: Optional[int] = Field(default=None, ge=1)
    consciousness_check_min_thoughts: Optional[int] = Field(default=None, ge=1)
    
    auto_tagging_enabled: Optional[bool] = None
    auto_task_creation_enabled: Optional[bool] = None
    task_suggestion_mode: Optional[TaskSuggestionMode] = None
    
    primary_backend: Optional[str] = None
    secondary_backend: Optional[str] = None
    
    @field_validator('consciousness_check_interval_minutes')
    @classmethod
    def validate_interval(cls, v: Optional[int]) -> Optional[int]:
        """Ensure interval is within valid range."""
        if v is not None and (v < 1 or v > 1440):
            raise ValueError('Interval must be between 1 and 1440 minutes (24 hours)')
        return v


class UserSettingsResponse(BaseTimestampModel):
    """
    Complete user settings model returned by API.
    
    Includes all configuration options with current values.
    """
    
    user_id: UUID = Field(..., description="ID of the user these settings belong to")
    
    # Consciousness Check Settings
    consciousness_check_enabled: bool = Field(
        ...,
        description="Master on/off switch for automated consciousness checks"
    )
    consciousness_check_interval_minutes: int = Field(
        ...,
        description="How often to run consciousness checks (minutes)"
    )
    consciousness_check_depth_type: SettingsDepthType = Field(
        ...,
        description="Analysis depth strategy"
    )
    consciousness_check_depth_value: int = Field(
        ...,
        description="Value for depth (days or thought count)"
    )
    consciousness_check_min_thoughts: int = Field(
        ...,
        description="Minimum thoughts to analyze for 'smart' mode"
    )
    
    # Auto-Analysis Settings
    auto_tagging_enabled: bool = Field(
        ...,
        description="Auto-suggest tags when capturing thoughts"
    )
    auto_task_creation_enabled: bool = Field(
        ...,
        description="Detect tasks from thoughts"
    )
    task_suggestion_mode: TaskSuggestionMode = Field(
        ...,
        description="How to handle detected tasks"
    )
    
    # Backend Override Settings
    primary_backend: Optional[str] = Field(
        None,
        description="Override primary AI backend"
    )
    secondary_backend: Optional[str] = Field(
        None,
        description="Override secondary AI backend"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "consciousness_check_enabled": True,
                "consciousness_check_interval_minutes": 30,
                "consciousness_check_depth_type": "smart",
                "consciousness_check_depth_value": 7,
                "consciousness_check_min_thoughts": 10,
                "auto_tagging_enabled": True,
                "auto_task_creation_enabled": True,
                "task_suggestion_mode": "suggest",
                "primary_backend": None,
                "secondary_backend": None,
                "created_at": "2025-12-26T10:00:00Z",
                "updated_at": "2025-12-26T10:00:00Z"
            }
        }


class AnalysisDepthConfig(BaseRequestModel):
    """
    Computed analysis depth configuration.
    
    Returned by SettingsService.get_analysis_depth_config() after
    resolving the depth_type into actual query parameters.
    
    For 'smart' mode: returns max(last N days, min M thoughts)
    """
    
    depth_type: SettingsDepthType = Field(
        ...,
        description="Original depth type from settings"
    )
    since_date: Optional[datetime] = Field(
        None,
        description="Analyze thoughts created after this date"
    )
    max_thoughts: Optional[int] = Field(
        None,
        description="Maximum number of thoughts to analyze"
    )
    min_thoughts: Optional[int] = Field(
        None,
        description="Minimum thoughts to ensure (for smart mode)"
    )


class UserSettingsDB(BaseDBModel):
    """
    SQLAlchemy ORM model for user_settings table.
    
    Stores user-configurable settings. One settings record per user.
    """
    
    __tablename__ = "user_settings"
    
    user_id = Column(
        String(36),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    
    # Consciousness Check Settings
    consciousness_check_enabled = Column(Boolean, nullable=False, default=True)
    consciousness_check_interval_minutes = Column(Integer, nullable=False, default=30)
    consciousness_check_depth_type = Column(String(20), nullable=False, default='smart')
    consciousness_check_depth_value = Column(Integer, nullable=False, default=7)
    consciousness_check_min_thoughts = Column(Integer, nullable=False, default=10)
    
    # Auto-Analysis Settings
    auto_tagging_enabled = Column(Boolean, nullable=False, default=True)
    auto_task_creation_enabled = Column(Boolean, nullable=False, default=True)
    task_suggestion_mode = Column(String(20), nullable=False, default='suggest')
    
    # Backend Override Settings
    primary_backend = Column(String(50), nullable=True)
    secondary_backend = Column(String(50), nullable=True)
    
    # Relationship to user
    user = relationship("UserDB", back_populates="settings")
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<UserSettingsDB("
            f"user_id={self.user_id}, "
            f"interval={self.consciousness_check_interval_minutes}min, "
            f"enabled={self.consciousness_check_enabled})>"
        )
    
    def to_response(self) -> UserSettingsResponse:
        """Convert SQLAlchemy model to Pydantic response model."""
        return UserSettingsResponse(
            id=self.id,
            user_id=self.user_id,
            consciousness_check_enabled=self.consciousness_check_enabled,
            consciousness_check_interval_minutes=self.consciousness_check_interval_minutes,
            consciousness_check_depth_type=SettingsDepthType(self.consciousness_check_depth_type),
            consciousness_check_depth_value=self.consciousness_check_depth_value,
            consciousness_check_min_thoughts=self.consciousness_check_min_thoughts,
            auto_tagging_enabled=self.auto_tagging_enabled,
            auto_task_creation_enabled=self.auto_task_creation_enabled,
            task_suggestion_mode=TaskSuggestionMode(self.task_suggestion_mode),
            primary_backend=self.primary_backend,
            secondary_backend=self.secondary_backend,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
