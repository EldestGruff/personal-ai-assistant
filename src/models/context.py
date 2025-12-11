"""
Context models for the Personal AI Assistant.

Captures situational context when thoughts are recorded - what the user
was doing, their mental state, and environmental factors. Helps Claude
identify patterns and optimize suggestions.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime

from .base import BaseRequestModel, BaseDBModel
from .enums import TimeOfDay, EnergyLevel, FocusState


class ContextCreate(BaseRequestModel):
    """
    Model for creating a new context session.
    
    Captures the situation and mental state when a thought is recorded.
    This helps Claude understand patterns in when and how ideas occur.
    
    Example:
        >>> context = ContextCreate(
        ...     current_activity="Email review",
        ...     active_app="Mail.app",
        ...     time_of_day=TimeOfDay.AFTERNOON,
        ...     energy_level=EnergyLevel.MEDIUM,
        ...     focus_state=FocusState.INTERRUPTED
        ... )
    """

    
    session_id: str = Field(
        ...,
        max_length=255,
        description="Unique identifier for this context session"
    )
    current_activity: Optional[str] = Field(
        default=None,
        max_length=255,
        description="What the user was doing"
    )
    active_app: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Foreground application (future: auto-detect)"
    )
    location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Physical location (future: GPS)"
    )
    time_of_day: Optional[TimeOfDay] = Field(
        default=None,
        description="General time of day"
    )
    energy_level: Optional[EnergyLevel] = Field(
        default=None,
        description="User's self-reported energy level"
    )
    focus_state: Optional[FocusState] = Field(
        default=None,
        description="User's mental focus state"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional situational notes"
    )



class ContextResponse(ContextCreate):
    """
    Complete context model returned by API.
    
    Extends ContextCreate with additional tracked fields like
    user_id, timestamps, and thought count for the session.
    """
    
    user_id: UUID = Field(..., description="Owner of this context")
    started_at: datetime = Field(..., description="When context began")
    thought_count: int = Field(
        default=0,
        description="Number of thoughts captured in this session"
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        description="When context session ended"
    )


class ContextDB(BaseDBModel):
    """
    SQLAlchemy ORM model for contexts table.
    
    Tracks user's situational context during thought capture sessions.
    Helps identify patterns in when and how thoughts occur.
    """
    
    __tablename__ = "contexts"
    
    # Override base id to use session_id as primary key
    id = Column(String(255), primary_key=True)  # session_id
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    current_activity = Column(String(255), nullable=True)
    active_app = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    time_of_day = Column(String(50), nullable=True)
    energy_level = Column(String(50), nullable=True)
    focus_state = Column(String(50), nullable=True)
    thought_count = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<ContextDB(session_id={self.id}, "
            f"user_id={self.user_id}, "
            f"activity='{self.current_activity}', "
            f"thought_count={self.thought_count})>"
        )
    
    def to_response(self) -> ContextResponse:
        """Convert SQLAlchemy model to Pydantic response model."""
        return ContextResponse(
            session_id=self.id,
            user_id=self.user_id,
            started_at=self.started_at,
            current_activity=self.current_activity,
            active_app=self.active_app,
            location=self.location,
            time_of_day=TimeOfDay(self.time_of_day) if self.time_of_day else None,
            energy_level=EnergyLevel(self.energy_level) if self.energy_level else None,
            focus_state=FocusState(self.focus_state) if self.focus_state else None,
            thought_count=self.thought_count,
            notes=self.notes,
            ended_at=self.ended_at
        )
