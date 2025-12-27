"""
User models for the Personal AI Assistant.

Defines user accounts, preferences, and authentication. Supports
multi-user architecture with RBAC foundation (Phase 3B).
"""

from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
from uuid import UUID

from pydantic import Field, field_validator
from sqlalchemy import Column, String, JSON, Boolean
from sqlalchemy.orm import relationship

from .base import BaseTimestampModel, BaseRequestModel, BaseDBModel, TZDateTime
from .enums import UserRole


class UserCreate(BaseRequestModel):
    """
    Model for creating a new user account.
    
    Example:
        >>> user = UserCreate(
        ...     name="Andy",
        ...     email="andy@fennerfam.com",
        ...     preferences={
        ...         "timezone": "America/New_York",
        ...         "max_thoughts_goal": 20
        ...     }
        ... )
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User's display name"
    )
    email: str = Field(
        ...,
        description="User's email address"
    )
    preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="User preferences (timezone, goals, settings)"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty or whitespace-only."""
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or whitespace-only")
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        v = v.strip().lower()
        if not v:
            raise ValueError("Email cannot be empty")
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError("Invalid email format")
        return v


class UserUpdate(BaseRequestModel):
    """
    Model for updating user information.
    
    All fields are optional - only provide fields you want to update.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be empty or whitespace-only")
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email if provided."""
        if v is not None:
            v = v.strip().lower()
            if not v:
                raise ValueError("Email cannot be empty")
            if '@' not in v or '.' not in v.split('@')[1]:
                raise ValueError("Invalid email format")
        return v


class UserResponse(BaseTimestampModel):
    """
    Complete user model returned by API.
    
    Includes all fields including auto-generated id and timestamps.
    """
    
    name: str = Field(..., description="User's display name")
    email: str = Field(..., description="User's email address")
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User preferences"
    )
    is_active: bool = Field(
        default=True,
        description="Whether user account is active"
    )
    role: UserRole = Field(
        default=UserRole.USER,
        description="User's role for RBAC"
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        description="Last login timestamp"
    )


class UserDB(BaseDBModel):
    """
    SQLAlchemy ORM model for users table.
    
    Stores user accounts and preferences. Multi-user architecture
    with RBAC foundation (Phase 3B).
    """
    
    __tablename__ = "users"
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    preferences = Column(JSON, nullable=True, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # RBAC fields (Phase 3B)
    role = Column(String(20), nullable=False, default='user')
    last_login_at = Column(TZDateTime, nullable=True)
    
    # Relationships
    settings = relationship(
        "UserSettingsDB",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    scheduled_analyses = relationship(
        "ScheduledAnalysisDB",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<UserDB(id={self.id}, "
            f"name='{self.name}', "
            f"email='{self.email}', "
            f"role='{self.role}', "
            f"is_active={self.is_active})>"
        )
    
    def to_response(self) -> UserResponse:
        """Convert SQLAlchemy model to Pydantic response model."""
        return UserResponse(
            id=self.id,
            name=self.name,
            email=self.email,
            preferences=self.preferences or {},
            is_active=self.is_active,
            role=UserRole(self.role),
            last_login_at=self.last_login_at,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
