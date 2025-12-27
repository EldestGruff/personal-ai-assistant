"""
Task models for the Personal AI Assistant.

Defines Pydantic models for API validation and SQLAlchemy models for database
persistence. Tasks are actionable items derived from thoughts.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator
from sqlalchemy import Column, Date, Integer, JSON, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from .base import (
    BaseTimestampModel,
    BaseRequestModel,
    BaseDBModel,
    TZDateTime,
    validate_content_length
)
from .enums import TaskStatus, Priority


class TaskCreate(BaseRequestModel):
    """
    Model for creating a new task via API.
    
    Tasks can be created from thoughts or standalone. Does not include
    id, created_at, or updated_at as those are auto-generated.
    
    Example:
        >>> task = TaskCreate(
        ...     title="Improve email spam analyzer",
        ...     description="Add regex patterns for unsubscribe URLs",
        ...     source_thought_id=UUID(...),
        ...     priority=Priority.MEDIUM,
        ...     due_date=date(2025, 12, 17)
        ... )
    """

    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short task description"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Detailed task description"
    )
    source_thought_id: Optional[UUID] = Field(
        default=None,
        description="Thought that spawned this task"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Task urgency level"
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Optional deadline"
    )
    estimated_effort_minutes: Optional[int] = Field(
        default=None,
        gt=0,
        description="Estimated time to complete (minutes)"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty and within length limits."""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty or whitespace-only")
        if len(v) > 200:
            raise ValueError(f"Title exceeds 200 characters (got {len(v)})")
        return v

    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None:
            return validate_content_length(v, max_length=5000)
        return v


class TaskUpdate(BaseRequestModel):
    """
    Model for updating an existing task.
    
    All fields are optional - only provide fields you want to update.
    The updated_at timestamp is automatically set on update.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[date] = None
    estimated_effort_minutes: Optional[int] = Field(None, gt=0)

    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty or whitespace-only")
            if len(v) > 200:
                raise ValueError(f"Title exceeds 200 characters (got {len(v)})")
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None:
            return validate_content_length(v, max_length=5000)
        return v


class TaskResponse(BaseTimestampModel):
    """
    Complete task model returned by API.
    
    Includes all fields including auto-generated id and timestamps.
    This is what users receive when querying tasks.
    
    Example:
        >>> response = TaskResponse(
        ...     id=UUID(...),
        ...     user_id=UUID(...),
        ...     title="Improve email spam analyzer",
        ...     priority=Priority.MEDIUM,
        ...     status=TaskStatus.PENDING,
        ...     created_at=datetime.now(timezone.utc)
        ... )
    """

    
    user_id: UUID = Field(..., description="Owner of this task")
    source_thought_id: Optional[UUID] = Field(
        default=None,
        description="Thought that spawned this task"
    )
    title: str = Field(..., description="Short task description")
    description: Optional[str] = Field(
        default=None,
        description="Detailed task description"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Task urgency level"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current task status"
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Optional deadline"
    )
    estimated_effort_minutes: Optional[int] = Field(
        default=None,
        description="Estimated time to complete (minutes)"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When task was marked as done"
    )
    linked_reminders: List[str] = Field(
        default_factory=list,
        description="Apple Reminders IDs linked to this task"
    )
    subtasks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Subtask breakdown"
    )



class TaskDB(BaseDBModel):
    """
    SQLAlchemy ORM model for tasks table.
    
    Mirrors TaskResponse but optimized for database storage.
    Uses proper column types and foreign key relationships.
    
    Phase 3B Spec 2: Added relationships for source_thought and source_suggestion.
    """
    
    __tablename__ = "tasks"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    source_thought_id = Column(
        String(36),
        ForeignKey("thoughts.id", ondelete="SET NULL"),
        nullable=True
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(
        String(50),
        nullable=False,
        default=Priority.MEDIUM.value
    )
    status = Column(
        String(50),
        nullable=False,
        default=TaskStatus.PENDING.value
    )
    due_date = Column(Date, nullable=True)
    estimated_effort_minutes = Column(Integer, nullable=True)
    completed_at = Column(TZDateTime, nullable=True)
    linked_reminders = Column(JSON, nullable=False, default=list)
    subtasks = Column(JSON, nullable=False, default=list)
    
    # Relationships
    # Note: This links Task to the Thought it was created FROM
    # Different from ThoughtDB.task which links Thought TO a task
    source_thought = relationship(
        "ThoughtDB",
        foreign_keys=[source_thought_id],
        uselist=False
    )
    source_suggestion = relationship(
        "TaskSuggestionDB",
        back_populates="created_task",
        uselist=False
    )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<TaskDB(id={self.id}, "
            f"user_id={self.user_id}, "
            f"status={self.status}, "
            f"priority={self.priority}, "
            f"title='{self.title}')>"
        )
    
    def to_response(self) -> TaskResponse:
        """Convert SQLAlchemy model to Pydantic response model."""
        return TaskResponse(
            id=self.id,
            user_id=self.user_id,
            source_thought_id=self.source_thought_id,
            title=self.title,
            description=self.description,
            priority=Priority(self.priority),
            status=TaskStatus(self.status),
            due_date=self.due_date,
            estimated_effort_minutes=self.estimated_effort_minutes,
            completed_at=self.completed_at,
            linked_reminders=self.linked_reminders or [],
            subtasks=self.subtasks or [],
            created_at=self.created_at,
            updated_at=self.updated_at
        )
