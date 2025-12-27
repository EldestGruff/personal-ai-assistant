"""
Settings API endpoints for the Personal AI Assistant.

Provides REST endpoints for user settings management including
get, update, and reset operations. Integrates with scheduler
for dynamic job updates.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import verify_api_key, get_current_user_id
from ..responses import APIResponse
from ...database.session import get_db
from ...services.settings_service import SettingsService
from ...services.scheduler_service import get_scheduler
from ...services.exceptions import NotFoundError, ValidationError
from ...models.settings import UserSettingsUpdate, UserSettingsResponse

router = APIRouter(prefix="/settings", tags=["settings"])


def get_settings_service(db: Session = Depends(get_db)) -> SettingsService:
    """Dependency injection for SettingsService."""
    return SettingsService(db)


@router.get("", response_model=None)
async def get_settings(
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Get current user settings.
    
    Creates default settings if none exist for the user.
    
    Returns:
        UserSettingsResponse with all configuration options
    """
    try:
        settings = settings_service.get_user_settings(user_id)
        return APIResponse.success(data=settings.model_dump(mode="json"))
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("", response_model=None)
async def update_settings(
    updates: UserSettingsUpdate,
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Update user settings (partial updates supported).
    
    Only updates fields that are provided in the request body.
    If consciousness check interval or enabled status changes,
    the scheduler job is automatically updated.
    
    Args:
        updates: Partial settings updates
        
    Returns:
        Updated UserSettingsResponse with message
    """
    try:
        # Get current settings to compare
        old_settings = settings_service.get_user_settings(user_id)
        
        # Apply updates
        new_settings = settings_service.update_user_settings(user_id, updates)
        
        # Update scheduler if needed
        message = "Settings updated successfully"
        if settings_service.settings_have_changed(old_settings, new_settings):
            scheduler = get_scheduler()
            scheduler.schedule_user_consciousness_checks(
                user_id=user_id,
                interval_minutes=new_settings.consciousness_check_interval_minutes,
                enabled=new_settings.consciousness_check_enabled
            )
            message = (
                f"Settings updated. Scheduler updated to run every "
                f"{new_settings.consciousness_check_interval_minutes} minutes."
            )
        
        return APIResponse.success(
            data=new_settings.model_dump(mode="json")
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/reset", response_model=None)
async def reset_settings(
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_current_user_id),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Reset settings to system defaults.
    
    Resets all settings to their default values and updates
    the scheduler accordingly.
    
    Returns:
        Reset UserSettingsResponse
    """
    try:
        settings = settings_service.reset_to_defaults(user_id)
        
        # Update scheduler with default settings
        scheduler = get_scheduler()
        scheduler.schedule_user_consciousness_checks(
            user_id=user_id,
            interval_minutes=settings.consciousness_check_interval_minutes,
            enabled=settings.consciousness_check_enabled
        )
        
        return APIResponse.success(
            data=settings.model_dump(mode="json")
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
