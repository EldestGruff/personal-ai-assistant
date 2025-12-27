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
        "analyses": [a.model_dump(mode="json") for a in history.analyses],
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
    db: Session = Depends(get_db)
):
    """
    Get the most recent completed consciousness check result.
    
    Returns the analysis in dashboard-compatible format.
    
    Returns:
        Latest analysis with summary, themes, actions, timestamp
    """
    from ...models import ClaudeAnalysisDB, AnalysisType
    
    # Get latest consciousness check from claude_analysis_results
    analysis = db.query(ClaudeAnalysisDB).filter(
        ClaudeAnalysisDB.user_id == user_id,
        ClaudeAnalysisDB.analysis_type == AnalysisType.CONSCIOUSNESS_CHECK.value
    ).order_by(
        ClaudeAnalysisDB.created_at.desc()
    ).first()
    
    if not analysis:
        return APIResponse.success(data={
            "summary": "No consciousness checks have been run yet. The scheduler will run checks automatically, or you can trigger one manually.",
            "themes": [],
            "suggested_actions": [],
            "source_analyses": 0,
            "timestamp": None,
            "backend_stats": {}
        })
    
    # Extract data from raw_response if available
    raw = analysis.raw_response or {}
    
    # Build dashboard-compatible response
    return APIResponse.success(data={
        "summary": analysis.summary or "Analysis completed.",
        "themes": analysis.themes or raw.get("themes", []),
        "suggested_actions": raw.get("suggested_actions", []),
        "source_analyses": raw.get("metadata", {}).get("thoughts_analyzed", 0),
        "timestamp": analysis.created_at.isoformat() if analysis.created_at else None,
        "backend_stats": {
            "stored": {
                "tokens_used": analysis.tokens_used,
                "processing_time_ms": raw.get("metadata", {}).get("duration_ms")
            }
        },
        "encouragement": raw.get("encouragement"),
        "connections": raw.get("connections", [])
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
        
        return APIResponse.success(data=analysis.model_dump(mode="json"))
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
