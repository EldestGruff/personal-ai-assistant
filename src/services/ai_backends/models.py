"""
Request and response models for AI backend operations.

All backends must accept BackendRequest and return either
SuccessResponse or ErrorResponse. This ensures consistent
contracts across all implementations.
"""

from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BackendRequest(BaseModel):
    """
    Request to analyze a thought.
    
    All backends accept this standardized request format,
    enabling transparent backend swapping without changing
    business logic.
    
    Example:
        request = BackendRequest(
            request_id="req-abc123",
            thought_content="Should optimize email system",
            context={"user_id": "550e...", "depth": "deep"},
            timeout_seconds=20
        )
    """
    
    model_config = ConfigDict(protected_namespaces=())
    
    request_id: str = Field(
        ...,
        description="Unique request identifier for tracing"
    )
    thought_content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The thought to analyze (1-5000 characters)"
    )
    context: Optional[dict] = Field(
        default=None,
        description="Additional context (user_id, analysis_depth, etc.)"
    )
    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=60,
        description="Max time to wait for analysis (5-60 seconds)"
    )
    model_hint: Optional[str] = Field(
        default=None,
        description="Suggestion for model selection: 'fast', 'quality', or 'cheap'"
    )
    include_confidence: bool = Field(
        default=True,
        description="Include confidence scores in response"
    )
    
    @field_validator("thought_content")
    @classmethod
    def validate_content_not_empty(cls, v):
        """Ensure content is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("thought_content cannot be empty or whitespace")
        return v.strip()
    
    @field_validator("model_hint")
    @classmethod
    def validate_model_hint(cls, v):
        """Ensure model hint is valid if provided"""
        if v is not None and v not in ["fast", "quality", "cheap"]:
            raise ValueError(
                "model_hint must be one of: 'fast', 'quality', 'cheap'"
            )
        return v


class Theme(BaseModel):
    """
    A theme extracted from thought content.
    
    Example:
        Theme(theme="email management", confidence=0.85)
    """
    
    theme: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Theme name"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)"
    )


class SuggestedAction(BaseModel):
    """
    An action suggested based on analysis.
    
    Example:
        SuggestedAction(
            action="Create optimization task",
            priority="high",
            confidence=0.9
        )
    """
    
    action: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Suggested action"
    )
    priority: str = Field(
        default="medium",
        description="Priority: low, medium, high, critical"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)"
    )
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """Ensure priority is valid"""
        valid = ["low", "medium", "high", "critical"]
        if v not in valid:
            raise ValueError(f"priority must be one of: {', '.join(valid)}")
        return v


class Analysis(BaseModel):
    """
    Analysis results from a backend.
    
    Contains the substantive analysis: summary, themes,
    suggested actions, and related thoughts.
    """
    
    request_id: str = Field(
        ...,
        description="Request ID from original request"
    )
    thought_id: Optional[str] = Field(
        default=None,
        description="ID of thought if stored in database"
    )
    backend_used: str = Field(
        ...,
        description="Name of backend that performed analysis"
    )
    summary: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Concise summary of thought"
    )
    themes: list[Theme] = Field(
        default=[],
        description="Extracted themes"
    )
    suggested_actions: list[SuggestedAction] = Field(
        default=[],
        description="Recommended actions"
    )
    related_thought_ids: list[str] = Field(
        default=[],
        description="IDs of related thoughts"
    )


class AnalysisMetadata(BaseModel):
    """
    Metadata about the analysis operation.
    
    Tracks performance, resource usage, and timing.
    Useful for monitoring and optimization.
    """
    
    model_config = ConfigDict(protected_namespaces=())
    
    tokens_used: int = Field(
        default=0,
        ge=0,
        description="Number of tokens consumed"
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Time taken to process request (milliseconds)"
    )
    model_version: str = Field(
        ...,
        description="Model used for analysis"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="When analysis completed (ISO 8601 UTC)"
    )


class SuccessResponse(BaseModel):
    """
    Successful analysis response.
    
    Contains both the analysis results and metadata
    about the operation.
    
    Example:
        SuccessResponse(
            success=True,
            analysis=Analysis(...),
            metadata=AnalysisMetadata(...)
        )
    """
    
    success: bool = Field(
        default=True,
        description="Always True for success responses"
    )
    analysis: Analysis = Field(
        ...,
        description="Analysis results"
    )
    metadata: AnalysisMetadata = Field(
        ...,
        description="Operation metadata"
    )


class ErrorDetails(BaseModel):
    """
    Details about an error that occurred.
    
    Provides enough context for debugging and recovery
    decisions. All backends use standardized error codes
    for consistent handling.
    """
    
    request_id: str = Field(
        ...,
        description="Request ID from original request"
    )
    backend_name: str = Field(
        ...,
        description="Name of backend that encountered error"
    )
    error_code: str = Field(
        ...,
        description=(
            "Standardized error code: INVALID_INPUT, TIMEOUT, "
            "RATE_LIMITED, UNAVAILABLE, CONTEXT_OVERFLOW, "
            "INTERNAL_ERROR, MALFORMED_RESPONSE"
        )
    )
    error_message: str = Field(
        ...,
        description="Human-readable error description"
    )
    suggestion: Optional[str] = Field(
        default=None,
        description="Suggestion for recovery"
    )


class ErrorResponse(BaseModel):
    """
    Error response from analysis.
    
    Returned when analysis fails for any reason.
    Contains enough detail for caller to decide
    whether to retry, escalate, or fail.
    
    Example:
        ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id="req-abc123",
                backend_name="claude",
                error_code="TIMEOUT",
                error_message="Analysis exceeded 30s timeout"
            )
        )
    """
    
    success: bool = Field(
        default=False,
        description="Always False for error responses"
    )
    error: ErrorDetails = Field(
        ...,
        description="Error details"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata about the error"
    )
