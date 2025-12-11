"""
Claude analysis result models for the Personal AI Assistant.

Stores Claude's reasoning, summaries, and suggestions for audit trail
and future context. Enables reviewing what Claude analyzed and when.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field
from sqlalchemy import Column, Float, Integer, JSON, String, Text, ForeignKey

from .base import BaseTimestampModel, BaseDBModel
from .enums import AnalysisType


class ClaudeAnalysisCreate(BaseTimestampModel):
    """
    Model for storing Claude analysis results.
    
    Created automatically when Claude performs analysis on thoughts.
    Includes the full reasoning, themes discovered, and action suggestions.
    
    Example:
        >>> analysis = ClaudeAnalysisCreate(
        ...     thought_id=UUID(...),
        ...     user_id=UUID(...),
        ...     analysis_type=AnalysisType.CONSCIOUSNESS_CHECK,
        ...     summary="User thinking about email improvements",
        ...     themes=["email", "automation"],
        ...     suggested_action="Create consolidated task",
        ...     confidence=0.85,
        ...     tokens_used=234
        ... )
    """

    
    thought_id: Optional[UUID] = Field(
        default=None,
        description="Specific thought analyzed (if applicable)"
    )
    user_id: UUID = Field(..., description="User who owns this analysis")
    analysis_type: AnalysisType = Field(
        ...,
        description="Type of analysis performed"
    )
    summary: str = Field(
        ...,
        max_length=5000,
        description="Claude's high-level summary"
    )
    themes: List[str] = Field(
        default_factory=list,
        description="Themes discovered in thoughts"
    )
    suggested_action: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Recommended next action"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)"
    )
    tokens_used: int = Field(
        ...,
        gt=0,
        description="API tokens consumed"
    )
    raw_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Complete Claude API response for debugging"
    )



# ClaudeAnalysisCreate is complete as-is (extends BaseTimestampModel)
# No separate Response model needed - same fields
ClaudeAnalysisResponse = ClaudeAnalysisCreate


class ClaudeAnalysisDB(BaseDBModel):
    """
    SQLAlchemy ORM model for claude_analysis_results table.
    
    Stores Claude's analysis results for audit trail and context.
    Enables reviewing what Claude analyzed and when for debugging.
    """
    
    __tablename__ = "claude_analysis_results"
    
    thought_id = Column(String(36), ForeignKey("thoughts.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    summary = Column(Text, nullable=False)
    themes = Column(JSON, nullable=False, default=list)
    suggested_action = Column(String(1000), nullable=True)
    confidence = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=False)
    raw_response = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<ClaudeAnalysisDB(id={self.id}, "
            f"type={self.analysis_type}, "
            f"user_id={self.user_id}, "
            f"tokens={self.tokens_used})>"
        )

    
    def to_response(self) -> ClaudeAnalysisResponse:
        """Convert SQLAlchemy model to Pydantic response model."""
        return ClaudeAnalysisResponse(
            id=self.id,
            thought_id=self.thought_id,
            user_id=self.user_id,
            analysis_type=AnalysisType(self.analysis_type),
            summary=self.summary,
            themes=self.themes or [],
            suggested_action=self.suggested_action,
            confidence=self.confidence,
            tokens_used=self.tokens_used,
            raw_response=self.raw_response,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
