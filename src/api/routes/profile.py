"""
User Profile endpoints for Personal AI Assistant API.

Phase 3B Spec 2: Manages user profiles for personalized AI analysis.
Profiles include ongoing projects, interests, work style, and discovered patterns.
"""

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...models import UserProfileUpdate, UserProfileResponse
from ...services.user_profile_service import UserProfileService
from ..auth import verify_api_key, get_current_user_id
from ..responses import APIResponse, APIError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
    dependencies=[Depends(verify_api_key)]
)


# Request models for JSON bodies
class AddProjectRequest(BaseModel):
    """Request to add a new project"""
    name: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="active")
    description: Optional[str] = Field(default=None, max_length=500)


class UpdateProjectStatusRequest(BaseModel):
    """Request to update project status"""
    status: str = Field(..., description="New status: active, planning, paused, completed")


@router.get("", response_model=None)
async def get_profile(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get user profile.
    
    Returns the user's profile including ongoing projects, interests,
    work style, and discovered patterns from consciousness checks.
    
    If no profile exists, a default profile is created automatically.
    
    Returns:
        UserProfileResponse with all profile fields
    """
    try:
        user_id = get_current_user_id()
        service = UserProfileService(db)
        
        profile = await service.get_profile_response(user_id)
        
        return APIResponse.success(data=profile.model_dump(mode="json")
        )
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise APIError(
            code="PROFILE_ERROR",
            message=f"Failed to get profile: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("", response_model=None)
async def update_profile(
    updates: UserProfileUpdate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Update user profile.
    
    Partial updates supported - only provide fields you want to change.
    
    Updatable fields:
    - ongoing_projects: List of project objects
    - interests: List of interest strings  
    - work_style: Description of work approach
    - adhd_considerations: ADHD-specific needs
    - preferred_tone: warm_encouraging, professional, casual
    - detail_level: brief, moderate, comprehensive
    - reference_past_work: Whether to reference past work in analysis
    
    Args:
        updates: Fields to update
        
    Returns:
        Updated UserProfileResponse
    """
    try:
        user_id = get_current_user_id()
        service = UserProfileService(db)
        
        profile = await service.update_profile(user_id, updates)
        
        return APIResponse.success(data=profile.to_response().model_dump(mode="json"))
        
    except ValueError as e:
        raise APIError(
            code="INVALID_PROFILE_DATA",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise APIError(
            code="PROFILE_UPDATE_ERROR",
            message=f"Failed to update profile: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/projects", response_model=None)
async def add_project(
    request: AddProjectRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Add a new ongoing project to profile.
    
    Projects are referenced in consciousness checks for context.
    
    Args:
        request: Project details (name required, status and description optional)
        
    Returns:
        Updated profile
    """
    try:
        user_id = get_current_user_id()
        service = UserProfileService(db)
        
        profile = await service.add_project(
            user_id=user_id,
            name=request.name,
            status=request.status,
            description=request.description
        )
        
        return APIResponse.success(data=profile.to_response().model_dump(mode="json"))
        
    except ValueError as e:
        raise APIError(
            code="INVALID_PROJECT",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error adding project: {e}")
        raise APIError(
            code="PROJECT_ADD_ERROR",
            message=f"Failed to add project: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/projects/{project_name}/status", response_model=None)
async def update_project_status(
    project_name: str,
    request: UpdateProjectStatusRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Update project status.
    
    Args:
        project_name: Name of the project
        request: New status (active, planning, paused, completed)
        
    Returns:
        Updated profile
    """
    try:
        user_id = get_current_user_id()
        service = UserProfileService(db)
        
        profile = await service.update_project_status(
            user_id=user_id,
            project_name=project_name,
            new_status=request.status
        )
        
        return APIResponse.success(data=profile.to_response().model_dump(mode="json"))
        
    except ValueError as e:
        raise APIError(
            code="PROJECT_NOT_FOUND",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error updating project status: {e}")
        raise APIError(
            code="PROJECT_UPDATE_ERROR",
            message=f"Failed to update project: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/projects/{project_name}", response_model=None)
async def remove_project(
    project_name: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Remove a project from profile.
    
    Args:
        project_name: Name of the project to remove
        
    Returns:
        Updated profile
    """
    try:
        user_id = get_current_user_id()
        service = UserProfileService(db)
        
        profile = await service.remove_project(user_id, project_name)
        
        return APIResponse.success(data=profile.to_response().model_dump(mode="json"))
        
    except Exception as e:
        logger.error(f"Error removing project: {e}")
        raise APIError(
            code="PROJECT_REMOVE_ERROR",
            message=f"Failed to remove project: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
