"""
Thought models for the Personal AI Assistant.

Defines Pydantic models for API validation and SQLAlchemy models for database
persistence. Thoughts are the core capture mechanism for transient ideas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator
from sqlalchemy import Column, JSON, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY

from .base import (
    BaseTimestampModel,
    BaseRequestModel,
    BaseDBModel,
    validate_content_length
)
from .enums import ThoughtStatus


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
    
    Example:
        >>> response = ThoughtResponse(
        ...     id=UUID(...),
        ...     user_id=UUID(...),
        ...     content="Should improve the email spam analyzer",
        ...     tags=["email", "improvement"],
        ...     status=ThoughtStatus.ACTIVE,
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


class ThoughtDB(BaseDBModel):
    """
    SQLAlchemy ORM model for thoughts table.
    
    Mirrors ThoughtResponse but optimized for database storage.
    Uses proper column types and foreign key relationships.
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
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<ThoughtDB(id={self.id}, "
            f"user_id={self.user_id}, "
            f"status={self.status}, "
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
            created_at=self.created_at,
            updated_at=self.updated_at
        )
