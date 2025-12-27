"""
Scheduled analysis API endpoints for the Personal AI Assistant.

Provides REST endpoints for viewing consciousness check history,
latest results, and manual triggering of checks.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import verify_api_key, get_current_user_id
from ..responses import APIResponse
from ...database.session import get_db
from ...services.scheduled_analysis_service import ScheduledAnalysisService
from ...services.settings_service import SettingsService
from ...services.scheduler_service import run_consciousness_check_job
from ...services.exceptions import NotFoundError
from ...models.enums import ScheduledAnalysisStatus, SettingsDepthType

router = APIRouter(prefix="/consciousness-check", tags=["consciousness-check"])


def get_scheduled_service(db: Session = Depends(get_db)) -> ScheduledAnalysisService:
    """Dependency injection for ScheduledAnalysisService."""
    return ScheduledAnalysisService(db)


def get_settings_service(db: Session = Depends(get_db)) -> SettingsService:
    """Dependency injection for SettingsService."""
    return SettingsService(db)


class DepthOverride(BaseModel):
    """Override depth configuration for manual trigger."""
    type: SettingsDepthType = Field(
        default=SettingsDepthType.LAST_N_THOUGHTS,
        description="Depth type for this check"
    )
    value: int = Field(
        default=20,
        ge=1,
        description="Depth value (thoughts or days)"
    )


class TriggerRequest(BaseModel):
    """Request body for manual consciousness check trigger."""
    depth_override: Optional[DepthOverride] = Field(
        default=None,
        description="Optional depth override (uses settings if not provided)"
    )


@router.get("/history", response_model=None)
async def get_history(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    scheduled_service: ScheduledAnalysisService = Depends(get_scheduled_service)
):
    """
    Get paginated history of scheduled consciousness checks.
    
    Args:
        limit: Maximum records per page (default 50, max 100)
        offset: Pagination offset
        status_filter: Optional filter by status (pending, running, completed, failed, skipped)
        
    Returns:
        ScheduledAnalysisHistoryResponse with pagination info
    """
    # Parse status filter
    status_enum = None
    if status_filter:
        try:
            status_enum = ScheduledAnalysisStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status_filter}. "
                       f"Valid values: {[s.value for s in ScheduledAnalysisStatus]}"
            )
    
    history = scheduled_service.get_analysis_history(
        user_id=user_id,
        limit=limit,
        offset=offset,
        status=status_enum
    )
    
    return APIResponse.success(data={
        "analyses": [a.model_dump() for a in history.analyses],
        "pagination": {
            "total": history.total,
            "limit": history.limit,
            "offset": history.offset,
            "has_more": history.has_more
        }
    })


@router.get("/latest", response_model=None)
async def get_latest(
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    scheduled_service: ScheduledAnalysisService = Depends(get_scheduled_service),
    db: Session = Depends(get_db)
):
    """
    Get the most recent completed consciousness check result.
    
    Returns the scheduled analysis record along with the full
    Claude analysis result if available.
    
    Returns:
        Latest completed analysis with result details
    """
    analysis = scheduled_service.get_last_completed_check(user_id)
    
    if not analysis:
        return APIResponse.success(
            data=None,
            message="No completed consciousness checks found"
        )
    
    # Get the Claude analysis result if available
    analysis_result = None
    if analysis.analysis_result_id:
        from ...services.claude_analysis_service import ClaudeAnalysisService
        claude_service = ClaudeAnalysisService(db)
        try:
            result = claude_service.get_analysis(str(analysis.analysis_result_id))
            if result:
                analysis_result = {
                    "id": str(result.id),
                    "summary": result.summary,
                    "themes": result.themes,
                    "suggested_action": result.suggested_action,
                    "confidence": result.confidence,
                    "tokens_used": result.tokens_used
                }
        except Exception:
            pass  # Analysis result may have been deleted
    
    return APIResponse.success(data={
        "scheduled_analysis": analysis.model_dump(),
        "analysis_result": analysis_result
    })


@router.post("/trigger", response_model=None)
async def trigger_check(
    background_tasks: BackgroundTasks,
    request: TriggerRequest = None,
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id)
):
    """
    Manually trigger a consciousness check (bypasses schedule).
    
    The check runs asynchronously in the background. Check
    /consciousness-check/history for results.
    
    Args:
        request: Optional depth override configuration
        
    Returns:
        Confirmation message with scheduled analysis ID hint
    """
    # Run check in background
    background_tasks.add_task(run_consciousness_check_job, user_id)
    
    return APIResponse.success(
        data={
            "message": "Consciousness check started",
            "hint": "Check GET /consciousness-check/history for results"
        },
        status_code=status.HTTP_202_ACCEPTED
    )


@router.get("/{analysis_id}", response_model=None)
async def get_analysis_by_id(
    analysis_id: str,
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    scheduled_service: ScheduledAnalysisService = Depends(get_scheduled_service)
):
    """
    Get a specific scheduled analysis by ID.
    
    Args:
        analysis_id: UUID of the scheduled analysis
        
    Returns:
        ScheduledAnalysisResponse
    """
    try:
        analysis = scheduled_service.get_by_id(analysis_id)
        
        # Verify ownership
        if str(analysis.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this analysis"
            )
        
        return APIResponse.success(data=analysis.model_dump())
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
