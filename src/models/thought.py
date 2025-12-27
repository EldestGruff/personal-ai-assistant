"""
Thought models for the Personal AI Assistant.

Defines Pydantic models for API validation and SQLAlchemy models for database
persistence. Thoughts are the core capture mechanism for transient ideas.

Phase 3B Spec 2: Enhanced with AI intelligence fields for intent classification,
auto-tagging, and actionability detection.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator
from sqlalchemy import Column, JSON, String, Text, Boolean, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import (
    BaseTimestampModel,
    BaseRequestModel,
    BaseDBModel,
    TZDateTime,
    validate_content_length
)
from .enums import ThoughtStatus, ThoughtType, EmotionalTone, Urgency


class ThoughtCreate(BaseRequestModel):
    """
    Model for creating a new thought via API.
    
    This is what the user sends when capturing a thought. Does not include
    id, created_at, or updated_at as those are auto-generated.
    
    Example:
        >>> thought = ThoughtCreate(
        ...     content="Should improve the email spam analyzer",
        ...     tags=["email", "improvement"],
        ...     context={"active_app": "Mail.app"}
        ... )
    """

    
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The thought text content (1-5000 characters)"
    )
    tags: List[str] = Field(
        default_factory=list,
        max_length=5,
        description="Category tags (max 5, each max 50 chars)"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Situational context (app, location, time of day, etc.)"
    )
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty and within length limits."""
        return validate_content_length(v, max_length=5000)
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """
        Validate tags format and constraints.
        
        Rules:
        - Max 5 tags
        - Each tag 1-50 characters
        - Lowercase alphanumeric + hyphens only
        - No duplicates
        """
        if len(v) > 5:
            raise ValueError("Maximum 5 tags allowed")
        
        validated_tags = []
        for tag in v:
            tag = tag.strip().lower()
            if not tag:
                continue  # Skip empty tags
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds 50 character limit")
            if not tag.replace('-', '').replace('_', '').isalnum():
                raise ValueError(
                    f"Tag '{tag}' contains invalid characters. "
                    "Use only lowercase alphanumeric and hyphens."
                )
            validated_tags.append(tag)
        
        # Check for duplicates
        if len(validated_tags) != len(set(validated_tags)):
            raise ValueError("Duplicate tags not allowed")
        
        return validated_tags


class ThoughtUpdate(BaseRequestModel):
    """
    Model for updating an existing thought.
    
    All fields are optional - only provide fields you want to update.
    The updated_at timestamp is automatically set on update.
    """
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    tags: Optional[List[str]] = Field(None, max_length=5)
    status: Optional[ThoughtStatus] = None
    context: Optional[Dict[str, Any]] = None

    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        """Validate content if provided."""
        if v is not None:
            return validate_content_length(v, max_length=5000)
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags if provided (same rules as ThoughtCreate)."""
        if v is None:
            return v
        # Reuse validation from ThoughtCreate
        return ThoughtCreate.validate_tags(v)


class ThoughtResponse(BaseTimestampModel):
    """
    Complete thought model returned by API.
    
    Includes all fields including auto-generated id and timestamps.
    This is what users receive when querying thoughts.
    
    Phase 3B Spec 2: Enhanced with AI intelligence fields.
    
    Example:
        >>> response = ThoughtResponse(
        ...     id=UUID(...),
        ...     user_id=UUID(...),
        ...     content="Should improve the email spam analyzer",
        ...     tags=["email", "improvement"],
        ...     status=ThoughtStatus.ACTIVE,
        ...     thought_type=ThoughtType.TASK,
        ...     intent_confidence=0.85,
        ...     created_at=datetime.now(timezone.utc)
        ... )
    """

    
    user_id: UUID = Field(..., description="Owner of this thought")
    content: str = Field(..., description="The thought text content")
    tags: List[str] = Field(default_factory=list, description="Category tags")
    status: ThoughtStatus = Field(
        default=ThoughtStatus.ACTIVE,
        description="Current lifecycle status"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Situational context when captured"
    )
    claude_summary: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Auto-generated summary by Claude"
    )
    claude_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Claude's reasoning about this thought"
    )
    related_thought_ids: List[UUID] = Field(
        default_factory=list,
        description="IDs of related thoughts"
    )
    task_id: Optional[UUID] = Field(
        default=None,
        description="Task created from this thought, if any"
    )
    
    # Phase 3B Spec 2: AI Intelligence Fields
    thought_type: Optional[ThoughtType] = Field(
        default=None,
        description="AI-detected intent type (task, note, reminder, etc.)"
    )
    intent_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for thought_type classification"
    )
    suggested_tags: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="AI-suggested tags with confidence scores"
    )
    related_topics: Optional[List[str]] = Field(
        default=None,
        description="AI-discovered related topics"
    )
    emotional_tone: Optional[EmotionalTone] = Field(
        default=None,
        description="Detected emotional tone of the thought"
    )
    urgency: Optional[Urgency] = Field(
        default=None,
        description="Detected urgency level"
    )
    is_actionable: Optional[bool] = Field(
        default=None,
        description="Whether thought requires action"
    )
    actionable_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence for actionability detection"
    )
    analysis_version: Optional[int] = Field(
        default=None,
        description="Version of analysis algorithm used"
    )
    analyzed_at: Optional[datetime] = Field(
        default=None,
        description="When AI analysis was performed"
    )


class ThoughtDB(BaseDBModel):
    """
    SQLAlchemy ORM model for thoughts table.
    
    Mirrors ThoughtResponse but optimized for database storage.
    Uses proper column types and foreign key relationships.
    
    Phase 3B Spec 2: Enhanced with AI intelligence columns.
    """

    
    __tablename__ = "thoughts"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)  # 1-5000 chars validated at app level
    tags = Column(JSON, nullable=False, default=list)  # Array of strings
    status = Column(
        String(50),
        nullable=False,
        default=ThoughtStatus.ACTIVE.value
    )
    context = Column(JSON, nullable=True)  # Situational metadata
    claude_summary = Column(String(500), nullable=True)
    claude_analysis = Column(JSON, nullable=True)
    related_thought_ids = Column(JSON, nullable=False, default=list)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    
    # Phase 3B Spec 2: AI Intelligence Columns
    thought_type = Column(String(50), nullable=True)
    intent_confidence = Column(Float, nullable=True)
    suggested_tags = Column(JSON, nullable=True)
    related_topics = Column(JSON, nullable=True)
    emotional_tone = Column(String(50), nullable=True)
    urgency = Column(String(20), nullable=True)
    is_actionable = Column(Boolean, nullable=True)
    actionable_confidence = Column(Float, nullable=True)
    analysis_version = Column(Integer, nullable=True, default=1)
    analyzed_at = Column(TZDateTime, nullable=True)
    
    # Relationships
    user = relationship("UserDB", back_populates="thoughts")
    # Note: This is a separate relationship from TaskDB.source_thought
    # task_id links thought TO a task, source_thought_id links task FROM a thought
    task = relationship("TaskDB", foreign_keys=[task_id], uselist=False)
    task_suggestions = relationship("TaskSuggestionDB", back_populates="source_thought")
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<ThoughtDB(id={self.id}, "
            f"user_id={self.user_id}, "
            f"status={self.status}, "
            f"thought_type={self.thought_type}, "
            f"content_preview='{self.content[:50]}...')>"
        )
    
    def to_response(self) -> ThoughtResponse:
        """Convert SQLAlchemy model to Pydantic response model."""
        return ThoughtResponse(
            id=self.id,
            user_id=self.user_id,
            content=self.content,
            tags=self.tags or [],
            status=ThoughtStatus(self.status),
            context=self.context,
            claude_summary=self.claude_summary,
            claude_analysis=self.claude_analysis,
            related_thought_ids=self.related_thought_ids or [],
            task_id=self.task_id,
            thought_type=ThoughtType(self.thought_type) if self.thought_type else None,
            intent_confidence=self.intent_confidence,
            suggested_tags=self.suggested_tags,
            related_topics=self.related_topics,
            emotional_tone=EmotionalTone(self.emotional_tone) if self.emotional_tone else None,
            urgency=Urgency(self.urgency) if self.urgency else None,
            is_actionable=self.is_actionable,
            actionable_confidence=self.actionable_confidence,
            analysis_version=self.analysis_version,
            analyzed_at=self.analyzed_at,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
