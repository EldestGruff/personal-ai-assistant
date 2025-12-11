"""
Claude integration endpoints for Personal AI Assistant API.

Handles consciousness checks and Claude-powered analysis.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from ..auth import verify_api_key, get_current_user_id
from ..responses import APIResponse, ClaudeAPIError

router = APIRouter(
    prefix="/claude",
    tags=["claude"],
    dependencies=[Depends(verify_api_key)]
)


class ConsciousnessCheckRequest(BaseModel):
    """Request model for consciousness check."""
    
    limit_recent: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of recent thoughts to analyze"
    )
    include_archived: bool = Field(
        default=False,
        description="Include archived thoughts in analysis"
    )
    focus_tags: Optional[List[str]] = Field(
        default=None,
        description="Focus analysis on specific tags"
    )


@router.post("/consciousness-check", status_code=status.HTTP_200_OK)
async def consciousness_check(
    request: ConsciousnessCheckRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Trigger Claude to analyze recent thoughts.
    
    Claude reviews recent thoughts, identifies patterns and themes,
    surfaces relevant past thoughts, and suggests actionable next steps.
    
    Note: This endpoint takes 2-5 seconds as it calls Claude API.
    """
    user_id = get_current_user_id()
    
    # TODO: Implement actual Claude API integration
    return APIResponse.success(
        data={
            "analysis_id": "mock-analysis-id",
            "timestamp": "2025-12-10T15:00:00.123456Z",
            "summary": "Mock analysis: No thoughts found yet. Start capturing thoughts to enable consciousness checks.",
            "themes": [],
            "surfaced_thoughts": [],
            "suggested_actions": [],
            "tokens_used": 0
        }
    )
