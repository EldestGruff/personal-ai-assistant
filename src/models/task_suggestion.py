"""
Task Suggestion models for the Personal AI Assistant.

Phase 3B Spec 2: AI-generated task suggestions from thought analysis.
Includes soft delete for ADHD-friendly restoration - users can change
their mind and restore deleted suggestions.
"""

from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator
from sqlalchemy import Column, String, Text, Boolean, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import relationship

from .base import (
    BaseTimestampModel,
    BaseRequestModel,
    BaseDBModel,
    TZDateTime,
    utc_now,
)
from .enums import Priority, TaskSuggestionStatus, TaskSuggestionUserAction


class SuggestedTag(BaseRequestModel):
    """
    A suggested tag with confidence score.
    
    Used in thought analysis response.
    """
    
    tag: str = Field(..., min_length=1, max_length=50, description="Tag name")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)"
    )
    reason: Optional[str] = Field(default=None, description="Why this tag was suggested")


class TaskSuggestionFromAnalysis(BaseRequestModel):
    """
    Task suggestion extracted from thought analysis.
    
    This is the structure returned by AI analysis, before being
    stored as a TaskSuggestion record.
    """
    
    title: str = Field(..., min_length=1, max_length=200, description="Suggested task title")
    description: Optional[str] = Field(default=None, max_length=5000, description="Task description")
    priority: Priority = Field(default=Priority.MEDIUM, description="Suggested priority")
    estimated_effort_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        description="Estimated effort in minutes"
    )
    due_date_hint: Optional[date] = Field(default=None, description="Suggested due date")
    reasoning: str = Field(..., description="Why this task was suggested")


class TaskSuggestionCreate(BaseRequestModel):
    """
    Model for creating a task suggestion.
    
    Typically created by ThoughtIntelligenceService from analysis.
    """
    
    source_thought_id: UUID = Field(..., description="ID of the thought that spawned this")
    title: str = Field(..., min_length=1, max_length=200, description="Suggested task title")
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: Priority = Field(default=Priority.MEDIUM)
    estimated_effort_minutes: Optional[int] = Field(default=None, ge=1)
    due_date_hint: Optional[date] = Field(default=None)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: Optional[str] = Field(default=None, description="Why this was suggested")


class TaskSuggestionAccept(BaseRequestModel):
    """
    Model for accepting a task suggestion with optional modifications.
    
    Allows user to tweak the suggested task before creation.
    """
    
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: Optional[Priority] = None
    estimated_effort_minutes: Optional[int] = Field(default=None, ge=1)
    due_date: Optional[date] = Field(default=None, description="Actual due date for task")


class TaskSuggestionResponse(BaseTimestampModel):
    """
    Complete task suggestion returned by API.
    
    Includes suggestion details, confidence, reasoning, and user action tracking.
    """
    
    user_id: UUID = Field(..., description="Owner of this suggestion")
    source_thought_id: Optional[UUID] = Field(default=None, description="Thought that spawned this (optional for consciousness check generated suggestions)")
    
    # Suggested task details
    title: str = Field(..., description="Suggested task title")
    description: Optional[str] = Field(default=None)
    priority: Priority = Field(default=Priority.MEDIUM)
    estimated_effort_minutes: Optional[int] = Field(default=None)
    due_date_hint: Optional[date] = Field(default=None)
    
    # Suggestion metadata
    confidence: float = Field(..., description="AI confidence (0.0-1.0)")
    reasoning: Optional[str] = Field(default=None, description="Why this was suggested")
    
    # User action tracking
    status: TaskSuggestionStatus = Field(default=TaskSuggestionStatus.PENDING)
    user_action: Optional[TaskSuggestionUserAction] = Field(default=None)
    user_action_at: Optional[datetime] = Field(default=None)
    created_task_id: Optional[UUID] = Field(default=None, description="Task created if accepted")
    
    # Soft delete
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    deletion_reason: Optional[str] = Field(default=None)
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "source_thought_id": "550e8400-e29b-41d4-a716-446655440002",
                "title": "Improve email spam analyzer",
                "description": "Add regex patterns for unsubscribe URLs",
                "priority": "medium",
                "confidence": 0.85,
                "reasoning": "Contains actionable verb 'improve' and specific technical details",
                "status": "pending",
                "is_deleted": False,
                "created_at": "2025-12-26T14:00:00Z",
                "updated_at": "2025-12-26T14:00:00Z"
            }
        }


class TaskSuggestionDB(BaseDBModel):
    """
    SQLAlchemy ORM model for task_suggestions table.
    
    Stores AI-generated task suggestions with soft delete support
    for ADHD-friendly restoration.
    """
    
    __tablename__ = "task_suggestions"
    
    user_id = Column(
        String(36),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    source_thought_id = Column(
        String(36),
        ForeignKey('thoughts.id', ondelete='CASCADE'),
        nullable=False
    )
    
    # Suggested task details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(50), nullable=False, default=Priority.MEDIUM.value)
    estimated_effort_minutes = Column(Integer, nullable=True)
    due_date_hint = Column(Date, nullable=True)
    
    # Suggestion metadata
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    
    # User action tracking
    status = Column(
        String(50),
        nullable=False,
        default=TaskSuggestionStatus.PENDING.value
    )
    user_action = Column(String(50), nullable=True)
    user_action_at = Column(TZDateTime, nullable=True)
    created_task_id = Column(
        String(36),
        ForeignKey('tasks.id', ondelete='SET NULL'),
        nullable=True
    )
    
    # Soft delete
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(TZDateTime, nullable=True)
    deletion_reason = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("UserDB", back_populates="task_suggestions")
    source_thought = relationship("ThoughtDB", back_populates="task_suggestions")
    created_task = relationship("TaskDB", back_populates="source_suggestion")
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<TaskSuggestionDB("
            f"id={self.id}, "
            f"title='{self.title[:30]}...', "
            f"confidence={self.confidence}, "
            f"status={self.status})>"
        )
    
    def to_response(self) -> TaskSuggestionResponse:
        """Convert SQLAlchemy model to Pydantic response model."""
        return TaskSuggestionResponse(
            id=self.id,
            user_id=self.user_id,
            source_thought_id=self.source_thought_id,
            title=self.title,
            description=self.description,
            priority=Priority(self.priority),
            estimated_effort_minutes=self.estimated_effort_minutes,
            due_date_hint=self.due_date_hint,
            confidence=self.confidence,
            reasoning=self.reasoning,
            status=TaskSuggestionStatus(self.status),
            user_action=TaskSuggestionUserAction(self.user_action) if self.user_action else None,
            user_action_at=self.user_action_at,
            created_task_id=self.created_task_id,
            is_deleted=self.is_deleted,
            deleted_at=self.deleted_at,
            deletion_reason=self.deletion_reason,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
