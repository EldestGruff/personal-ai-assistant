"""
Schedule management API endpoints for the Personal AI Assistant.

Provides REST endpoints for managing the consciousness check scheduler,
including start/stop control and schedule configuration.
"""

from typing import Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import verify_api_key, get_current_user_id
from ..responses import APIResponse
from ...database.session import get_db
from ...services.scheduler_service import get_scheduler
from ...services.settings_service import SettingsService
from ...services.scheduled_analysis_service import ScheduledAnalysisService

router = APIRouter(prefix="/scheduled-analyses", tags=["schedule-management"])


def get_settings_service(db: Session = Depends(get_db)) -> SettingsService:
    """Dependency injection for SettingsService."""
    return SettingsService(db)


def get_scheduled_service(db: Session = Depends(get_db)) -> ScheduledAnalysisService:
    """Dependency injection for ScheduledAnalysisService."""
    return ScheduledAnalysisService(db)


class ScheduleUpdate(BaseModel):
    """Schedule configuration update."""
    interval_minutes: Optional[int] = Field(
        default=None,
        ge=5,
        le=1440,
        description="Check interval in minutes (5-1440)"
    )
    active_hours: Optional[dict] = Field(
        default=None,
        description="Active hours config: {start: 'HH:MM', end: 'HH:MM'}"
    )
    weekend_enabled: Optional[bool] = Field(
        default=None,
        description="Whether to run on weekends"
    )


@router.get("", response_model=None)
async def get_schedule_status(
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    settings_service: SettingsService = Depends(get_settings_service),
    scheduled_service: ScheduledAnalysisService = Depends(get_scheduled_service)
):
    """
    Get current schedule status and configuration.
    
    Returns schedule state, settings, and recent analysis results.
    """
    scheduler = get_scheduler()
    job_id = f"consciousness_check_{user_id}"
    job = scheduler.get_job(job_id)
    
    # Get settings
    settings = settings_service.get_user_settings(user_id)
    
    # Get recent analyses
    history = scheduled_service.get_analysis_history(
        user_id=user_id,
        limit=5,
        offset=0
    )
    
    return APIResponse.success(data={
        "is_running": job is not None and settings.consciousness_check_enabled,
        "interval_minutes": settings.consciousness_check_interval_minutes,
        "active_hours": {
            "start": "09:00",
            "end": "18:00"
        },
        "weekend_enabled": False,
        "recent_analyses": [
            {
                "id": str(a.id),
                "timestamp": a.started_at.isoformat() if a.started_at else None,
                "status": a.status.value if a.status else None,
                "thoughts_analyzed": a.thoughts_analyzed or 0,
                "themes": a.themes_discovered or []
            }
            for a in history.analyses
        ]
    })


@router.post("/start", response_model=None)
async def start_schedule(
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Start the consciousness check scheduler for this user.
    
    Uses the interval from user settings.
    """
    # Get current settings
    settings = settings_service.get_user_settings(user_id)
    
    # Enable in settings
    from ...models.settings import UserSettingsUpdate
    settings_service.update_user_settings(
        user_id,
        UserSettingsUpdate(consciousness_check_enabled=True)
    )
    
    # Schedule the job
    scheduler = get_scheduler()
    scheduler.schedule_user_consciousness_checks(
        user_id=user_id,
        interval_minutes=settings.consciousness_check_interval_minutes,
        enabled=True
    )
    
    return APIResponse.success(data={
        "message": "Schedule started",
        "interval_minutes": settings.consciousness_check_interval_minutes
    })


@router.post("/stop", response_model=None)
async def stop_schedule(
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Stop the consciousness check scheduler for this user.
    """
    # Disable in settings
    from ...models.settings import UserSettingsUpdate
    settings_service.update_user_settings(
        user_id,
        UserSettingsUpdate(consciousness_check_enabled=False)
    )
    
    # Remove the job
    scheduler = get_scheduler()
    scheduler.schedule_user_consciousness_checks(
        user_id=user_id,
        enabled=False
    )
    
    return APIResponse.success(data={
        "message": "Schedule stopped"
    })


@router.put("", response_model=None)
async def update_schedule(
    updates: ScheduleUpdate,
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Update schedule configuration.
    
    Updates the interval and reschedules the job if running.
    """
    from ...models.settings import UserSettingsUpdate
    
    # Build settings update
    settings_update = UserSettingsUpdate()
    if updates.interval_minutes is not None:
        settings_update.consciousness_check_interval_minutes = updates.interval_minutes
    
    # Apply settings update
    new_settings = settings_service.update_user_settings(user_id, settings_update)
    
    # Reschedule if enabled
    if new_settings.consciousness_check_enabled:
        scheduler = get_scheduler()
        scheduler.schedule_user_consciousness_checks(
            user_id=user_id,
            interval_minutes=new_settings.consciousness_check_interval_minutes,
            enabled=True
        )
    
    return APIResponse.success(data={
        "message": "Schedule updated",
        "interval_minutes": new_settings.consciousness_check_interval_minutes
    })
