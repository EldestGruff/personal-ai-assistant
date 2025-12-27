"""
User Profile models for the Personal AI Assistant.

Phase 3B Spec 2: Rich user profile for personalized AI analysis.
Includes ongoing projects, interests, work style, and discovered patterns
that inform consciousness checks and thought analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator
from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from .base import (
    BaseTimestampModel,
    BaseRequestModel,
    BaseDBModel,
    TZDateTime,
    utc_now,
)
from .enums import PreferredTone, DetailLevel


class OngoingProject(BaseRequestModel):
    """
    An ongoing project in the user's profile.
    
    Helps AI understand context and make relevant connections.
    
    Example:
        >>> project = OngoingProject(
        ...     name="Personal AI Assistant",
        ...     status="active",
        ...     description="Building thought capture system with local AI"
        ... )
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Project name"
    )
    status: str = Field(
        default="active",
        description="Project status: active, planning, paused, completed"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Brief project description"
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of allowed values."""
        valid = ['active', 'planning', 'paused', 'completed']
        if v.lower() not in valid:
            raise ValueError(f"Status must be one of: {', '.join(valid)}")
        return v.lower()


class ThoughtPattern(BaseRequestModel):
    """
    Discovered patterns in user's thought capture behavior.
    
    Used by AI to understand when/how user thinks best.
    """
    
    peak_hours: List[str] = Field(
        default_factory=list,
        description="Time periods when most thoughts are captured"
    )
    common_triggers: List[str] = Field(
        default_factory=list,
        description="What typically triggers thought capture"
    )
    typical_length: Optional[str] = Field(
        default=None,
        description="Typical thought length: brief, moderate, detailed"
    )


class UserProfileCreate(BaseRequestModel):
    """
    Model for creating a user profile.
    
    Typically created automatically when user is created, with defaults.
    """
    
    ongoing_projects: List[OngoingProject] = Field(
        default_factory=list,
        description="User's current projects"
    )
    interests: List[str] = Field(
        default_factory=list,
        description="User's interests and focus areas"
    )
    work_style: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Description of user's work approach"
    )
    adhd_considerations: Optional[str] = Field(
        default=None,
        description="Specific ADHD-related needs or preferences"
    )
    preferred_tone: PreferredTone = Field(
        default=PreferredTone.WARM_ENCOURAGING,
        description="Preferred communication tone for AI responses"
    )
    detail_level: DetailLevel = Field(
        default=DetailLevel.MODERATE,
        description="Preferred detail level for AI responses"
    )
    reference_past_work: bool = Field(
        default=True,
        description="Whether AI should reference past projects in analysis"
    )
    
    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v: List[str]) -> List[str]:
        """Validate and normalize interests."""
        # Deduplicate and lowercase
        return list(set(i.strip().lower() for i in v if i.strip()))


class UserProfileUpdate(BaseRequestModel):
    """
    Model for updating a user profile.
    
    All fields optional - partial updates supported.
    """
    
    ongoing_projects: Optional[List[OngoingProject]] = None
    interests: Optional[List[str]] = None
    work_style: Optional[str] = Field(default=None, max_length=255)
    adhd_considerations: Optional[str] = None
    common_themes: Optional[List[str]] = None
    thought_patterns: Optional[ThoughtPattern] = None
    productivity_insights: Optional[str] = None
    preferred_tone: Optional[PreferredTone] = None
    detail_level: Optional[DetailLevel] = None
    reference_past_work: Optional[bool] = None
    
    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate interests if provided."""
        if v is None:
            return v
        return list(set(i.strip().lower() for i in v if i.strip()))


class UserProfileResponse(BaseTimestampModel):
    """
    Complete user profile returned by API.
    
    Includes all profile fields plus discovered patterns.
    """
    
    user_id: str = Field(..., description="ID of the user this profile belongs to")
    
    # Personal context
    ongoing_projects: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="User's ongoing projects"
    )
    interests: List[str] = Field(
        default_factory=list,
        description="User's interests"
    )
    work_style: Optional[str] = Field(
        default=None,
        description="User's work approach description"
    )
    adhd_considerations: Optional[str] = Field(
        default=None,
        description="ADHD-specific considerations"
    )
    
    # Discovered patterns
    common_themes: List[str] = Field(
        default_factory=list,
        description="Themes discovered from consciousness checks"
    )
    thought_patterns: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Discovered thought capture patterns"
    )
    productivity_insights: Optional[str] = Field(
        default=None,
        description="AI-discovered productivity insights"
    )
    
    # Communication preferences
    preferred_tone: PreferredTone = Field(
        default=PreferredTone.WARM_ENCOURAGING,
        description="Preferred AI communication tone"
    )
    detail_level: DetailLevel = Field(
        default=DetailLevel.MODERATE,
        description="Preferred detail level"
    )
    reference_past_work: bool = Field(
        default=True,
        description="Whether to reference past work in analysis"
    )
    
    # Last update timestamp
    last_analysis_update: Optional[datetime] = Field(
        default=None,
        description="When patterns were last updated from analysis"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "ongoing_projects": [
                    {
                        "name": "Personal AI Assistant",
                        "status": "active",
                        "description": "Building thought capture system"
                    }
                ],
                "interests": ["automation", "AI", "infrastructure"],
                "work_style": "methodical, do it right",
                "common_themes": ["productivity", "automation"],
                "preferred_tone": "warm_encouraging",
                "detail_level": "moderate",
                "reference_past_work": True,
                "created_at": "2025-12-26T10:00:00Z",
                "updated_at": "2025-12-26T10:00:00Z"
            }
        }


class UserProfileDB(BaseDBModel):
    """
    SQLAlchemy ORM model for user_profiles table.
    
    Stores rich user context for personalized AI analysis.
    One profile per user.
    """
    
    __tablename__ = "user_profiles"
    
    user_id = Column(
        String(36),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    
    # Personal context
    ongoing_projects = Column(JSON, nullable=True, default=list)
    interests = Column(JSON, nullable=True, default=list)
    work_style = Column(String(255), nullable=True)
    adhd_considerations = Column(Text, nullable=True)
    
    # Discovered patterns
    common_themes = Column(JSON, nullable=True, default=list)
    thought_patterns = Column(JSON, nullable=True)
    productivity_insights = Column(Text, nullable=True)
    
    # Communication preferences
    preferred_tone = Column(
        String(50),
        nullable=False,
        default=PreferredTone.WARM_ENCOURAGING.value
    )
    detail_level = Column(
        String(50),
        nullable=False,
        default=DetailLevel.MODERATE.value
    )
    reference_past_work = Column(Boolean, nullable=False, default=True)
    
    # Last analysis update
    last_analysis_update = Column(TZDateTime, nullable=True)
    
    # Relationship to user
    user = relationship("UserDB", back_populates="profile")
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<UserProfileDB("
            f"user_id={self.user_id}, "
            f"projects={len(self.ongoing_projects or [])} active, "
            f"tone={self.preferred_tone})>"
        )
    
    def to_response(self) -> UserProfileResponse:
        """Convert SQLAlchemy model to Pydantic response model."""
        return UserProfileResponse(
            id=self.id,
            user_id=self.user_id,
            ongoing_projects=self.ongoing_projects or [],
            interests=self.interests or [],
            work_style=self.work_style,
            adhd_considerations=self.adhd_considerations,
            common_themes=self.common_themes or [],
            thought_patterns=self.thought_patterns,
            productivity_insights=self.productivity_insights,
            preferred_tone=PreferredTone(self.preferred_tone),
            detail_level=DetailLevel(self.detail_level),
            reference_past_work=self.reference_past_work,
            last_analysis_update=self.last_analysis_update,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
