"""
Backend Selection Models

Request/response schemas for backend selection decisions.

These models enable the selector to receive context about
a request and return a decision about which backend(s) to use.
"""

from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class BackendSelectionRequest(BaseModel):
    """
    Request to select appropriate backend(s).
    
    Provides context about the request so selector can make
    intelligent decisions about which backend to use.
    
    Example:
        request = BackendSelectionRequest(
            request_id="req-abc123",
            thought_length=157,
            analysis_type="standard",
            available_backends=["claude", "ollama", "mock"]
        )
    """
    
    request_id: str = Field(
        ...,
        description="Unique request identifier for tracing"
    )
    thought_length: int = Field(
        ...,
        ge=1,
        le=5000,
        description="Length of the thought content (characters)"
    )
    analysis_type: str = Field(
        default="standard",
        description="Type of analysis: 'standard', 'deep', 'quick'"
    )
    available_backends: list[str] = Field(
        ...,
        min_length=1,
        description="Names of available backends (e.g., ['claude', 'ollama'])"
    )
    user_preferences: Optional[dict] = Field(
        default=None,
        description="User preferences (prefer_local, max_latency_ms, etc.)"
    )
    
    @field_validator("analysis_type")
    @classmethod
    def validate_analysis_type(cls, v):
        """Ensure analysis type is valid"""
        valid = ["standard", "deep", "quick"]
        if v not in valid:
            raise ValueError(
                f"analysis_type must be one of: {', '.join(valid)}"
            )
        return v


class BackendChoice(BaseModel):
    """
    Choice of a single backend with role and configuration.
    
    Represents one backend selected for use, along with
    its role (primary/fallback) and timeout settings.
    
    Example:
        choice = BackendChoice(
            name="claude",
            role="primary",
            timeout_seconds=30
        )
    """
    
    name: str = Field(
        ...,
        description="Backend name (e.g., 'claude', 'ollama', 'mock')"
    )
    role: str = Field(
        ...,
        description="Role: 'primary', 'fallback', or 'parallel'"
    )
    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=60,
        description="Timeout for this specific backend (5-60 seconds)"
    )
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Ensure role is valid"""
        valid = ["primary", "fallback", "parallel"]
        if v not in valid:
            raise ValueError(
                f"role must be one of: {', '.join(valid)}"
            )
        return v


class BackendSelectionResponse(BaseModel):
    """
    Decision about which backend(s) to use.
    
    Contains the primary backend(s) to try, optional fallbacks,
    and reasoning explaining why this decision was made.
    
    Example:
        response = BackendSelectionResponse(
            request_id="req-abc123",
            decision_type="SEQUENTIAL",
            backends=[
                BackendChoice(name="claude", role="primary")
            ],
            fallback_backends=[
                BackendChoice(name="ollama", role="fallback")
            ],
            reasoning="Claude primary, Ollama fallback per config",
            timestamp="2025-12-16T10:00:00.000000Z"
        )
    """
    
    request_id: str = Field(
        ...,
        description="Echo of request ID for tracing"
    )
    decision_type: str = Field(
        ...,
        description="Decision strategy: PRIMARY_ONLY, SEQUENTIAL, PARALLEL, COST_OPTIMIZED"
    )
    backends: list[BackendChoice] = Field(
        ...,
        min_length=1,
        description="Primary backend(s) to try first"
    )
    fallback_backends: list[BackendChoice] = Field(
        default=[],
        description="Fallback backend(s) if primary fails"
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        description="Explanation of why this decision was made"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="When decision was made (ISO 8601 UTC)"
    )
    
    @field_validator("decision_type")
    @classmethod
    def validate_decision_type(cls, v):
        """Ensure decision type is valid"""
        valid = ["PRIMARY_ONLY", "SEQUENTIAL", "PARALLEL", "COST_OPTIMIZED"]
        if v not in valid:
            raise ValueError(
                f"decision_type must be one of: {', '.join(valid)}"
            )
        return v
