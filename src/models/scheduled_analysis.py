"""
Scheduled analysis models for the Personal AI Assistant.

Tracks all scheduled consciousness checks, including their status,
results, and performance metrics. Provides audit trail for debugging.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseTimestampModel, BaseRequestModel, TZDateTime, utc_now, Base
from .enums import ScheduledAnalysisStatus


class ScheduledAnalysisCreate(BaseRequestModel):
    """
    Model for creating a scheduled analysis record.
    
    Typically created by the scheduler when initiating a consciousness check.
    """
    
    user_id: UUID = Field(..., description="User this analysis is for")
    scheduled_at: datetime = Field(..., description="When this was scheduled to run")
    triggered_by: str = Field(
        default="scheduler",
        description="What triggered this analysis: scheduler, manual, api"
    )


class ScheduledAnalysisResponse(BaseTimestampModel):
    """
    Complete scheduled analysis model returned by API.
    
    Includes execution details, results, and performance metrics.
    """
    
    user_id: UUID = Field(..., description="User this analysis belongs to")
    scheduled_at: datetime = Field(..., description="When this was scheduled to run")
    executed_at: Optional[datetime] = Field(None, description="When execution started")
    completed_at: Optional[datetime] = Field(None, description="When execution completed")
    status: ScheduledAnalysisStatus = Field(..., description="Current status")
    
    # Execution details
    skip_reason: Optional[str] = Field(
        None,
        description="Why was this skipped: no_new_thoughts, disabled_by_user"
    )
    thoughts_since_last_check: Optional[int] = Field(
        None,
        description="Number of new thoughts since last completed check"
    )
    thoughts_analyzed_count: Optional[int] = Field(
        None,
        description="Total thoughts analyzed in this check"
    )
    analysis_duration_ms: Optional[int] = Field(
        None,
        description="How long the analysis took in milliseconds"
    )
    
    # Results
    analysis_result_id: Optional[UUID] = Field(
        None,
        description="ID of the ClaudeAnalysisResult record"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if status is FAILED"
    )
    
    triggered_by: str = Field(
        ...,
        description="What triggered this: scheduler, manual, api"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "scheduled_at": "2025-12-26T14:00:00Z",
                "executed_at": "2025-12-26T14:00:01Z",
                "completed_at": "2025-12-26T14:00:15Z",
                "status": "completed",
                "thoughts_since_last_check": 3,
                "thoughts_analyzed_count": 17,
                "analysis_duration_ms": 14250,
                "analysis_result_id": "result-xyz",
                "triggered_by": "scheduler"
            }
        }


class ScheduledAnalysisHistoryResponse(BaseRequestModel):
    """
    Paginated history of scheduled analyses.
    """
    
    analyses: list[ScheduledAnalysisResponse] = Field(
        ...,
        description="List of scheduled analysis records"
    )
    total: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Maximum records per page")
    offset: int = Field(..., description="Current offset")
    has_more: bool = Field(..., description="Whether more records exist")


class ScheduledAnalysisDB(Base):
    """
    SQLAlchemy ORM model for scheduled_analyses table.
    
    Tracks every scheduled consciousness check run for audit trail.
    Note: Does not inherit from BaseDBModel because it has different
    timestamp requirements (created_at only, no updated_at).
    """
    
    __tablename__ = "scheduled_analyses"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    
    # Scheduling metadata
    scheduled_at = Column(TZDateTime, nullable=False)
    executed_at = Column(TZDateTime, nullable=True)
    completed_at = Column(TZDateTime, nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    
    # Execution details
    skip_reason = Column(String(100), nullable=True)
    thoughts_since_last_check = Column(Integer, nullable=True)
    thoughts_analyzed_count = Column(Integer, nullable=True)
    analysis_duration_ms = Column(Integer, nullable=True)
    
    # Results
    analysis_result_id = Column(
        String(36),
        ForeignKey('claude_analysis_results.id', ondelete='SET NULL'),
        nullable=True
    )
    error_message = Column(Text, nullable=True)
    
    # Trigger source
    triggered_by = Column(String(50), nullable=False, default='scheduler')
    
    # Metadata (only created_at, no updated_at since this is append-only)
    created_at = Column(TZDateTime, nullable=False, default=utc_now)
    
    # Relationships
    user = relationship("UserDB", back_populates="scheduled_analyses")
    analysis_result = relationship("ClaudeAnalysisDB")
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<ScheduledAnalysisDB("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"status={self.status}, "
            f"scheduled_at={self.scheduled_at})>"
        )
    
    def to_response(self) -> ScheduledAnalysisResponse:
        """Convert SQLAlchemy model to Pydantic response model."""
        return ScheduledAnalysisResponse(
            id=self.id,
            user_id=self.user_id,
            scheduled_at=self.scheduled_at,
            executed_at=self.executed_at,
            completed_at=self.completed_at,
            status=ScheduledAnalysisStatus(self.status),
            skip_reason=self.skip_reason,
            thoughts_since_last_check=self.thoughts_since_last_check,
            thoughts_analyzed_count=self.thoughts_analyzed_count,
            analysis_duration_ms=self.analysis_duration_ms,
            analysis_result_id=self.analysis_result_id,
            error_message=self.error_message,
            triggered_by=self.triggered_by,
            created_at=self.created_at,
            updated_at=self.created_at  # Use created_at as updated_at for this model
        )
