"""
Task Suggestions endpoints for Personal AI Assistant API.

Phase 3B Spec 2: AI-generated task suggestions with soft delete for
ADHD-friendly restoration. Users can change their mind and restore
deleted suggestions.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...models import TaskSuggestionAccept, TaskSuggestionResponse
from ...services.task_suggestion_service import TaskSuggestionService
from ..auth import verify_api_key, get_current_user_id
from ..responses import APIResponse, APIError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/task-suggestions",
    tags=["task-suggestions"],
    dependencies=[Depends(verify_api_key)]
)


@router.get("/pending")
async def get_pending_suggestions(
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get all pending task suggestions.
    
    Returns suggestions that have not been accepted or rejected yet.
    Sorted by confidence score (highest first).
    
    Args:
        min_confidence: Minimum confidence threshold (0.0-1.0)
        
    Returns:
        List of pending TaskSuggestionResponse objects
    """
    try:
        user_id = get_current_user_id()
        service = TaskSuggestionService(db)
        
        suggestions = await service.get_pending_suggestions(
            user_id=user_id,
            min_confidence=min_confidence
        )
        
        return APIResponse.success(data={
                "suggestions": [s.to_response().model_dump(mode="json") for s in suggestions],
                "count": len(suggestions)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting pending suggestions: {e}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="SUGGESTIONS_ERROR",
            message=f"Failed to get suggestions: {str(e)}"
        )


@router.get("/history")
async def get_suggestion_history(
    include_deleted: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get task suggestion history.
    
    Returns all suggestions (accepted, rejected, expired) for review.
    
    Args:
        include_deleted: Whether to include soft-deleted suggestions
        limit: Maximum number to return (default 50)
        
    Returns:
        List of TaskSuggestionResponse objects
    """
    try:
        user_id = get_current_user_id()
        service = TaskSuggestionService(db)
        
        suggestions = await service.get_suggestion_history(
            user_id=user_id,
            include_deleted=include_deleted,
            limit=limit
        )
        
        return APIResponse.success(data={
                "suggestions": [s.to_response().model_dump(mode="json") for s in suggestions],
                "count": len(suggestions),
                "include_deleted": include_deleted
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting suggestion history: {e}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="HISTORY_ERROR",
            message=f"Failed to get history: {str(e)}"
        )


@router.get("/{suggestion_id}")
async def get_suggestion(
    suggestion_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get a single task suggestion by ID.
    
    Args:
        suggestion_id: UUID of the suggestion
        
    Returns:
        TaskSuggestionResponse
    """
    try:
        service = TaskSuggestionService(db)
        
        suggestion = await service.get_suggestion(suggestion_id)
        
        if not suggestion:
            raise APIError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="SUGGESTION_NOT_FOUND",
                message=f"Suggestion {suggestion_id} not found"
            )
        
        return APIResponse.success(data=suggestion.to_response().model_dump(mode="json")
        )
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestion: {e}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="SUGGESTION_ERROR",
            message=f"Failed to get suggestion: {str(e)}"
        )


@router.post("/{suggestion_id}/accept", status_code=status.HTTP_201_CREATED)
async def accept_suggestion(
    suggestion_id: UUID,
    modifications: Optional[TaskSuggestionAccept] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Accept a task suggestion and create actual task.
    
    Optionally modify the suggested title, description, priority,
    or estimated effort before creating the task.
    
    Args:
        suggestion_id: UUID of the suggestion
        modifications: Optional changes to apply
        
    Returns:
        Created TaskResponse and updated TaskSuggestionResponse
    """
    try:
        service = TaskSuggestionService(db)
        
        suggestion = await service.get_suggestion(suggestion_id)
        if not suggestion:
            raise APIError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="SUGGESTION_NOT_FOUND",
                message=f"Suggestion {suggestion_id} not found"
            )
        
        task = await service.accept_suggestion(suggestion_id, modifications)
        
        # Refresh suggestion to get updated state
        suggestion = await service.get_suggestion(suggestion_id)
        
        return APIResponse.success(data={
                "task": task.to_response().model_dump(mode="json"),
                "suggestion": suggestion.to_response().model_dump(mode="json")
            },
            message="Task created from suggestion"
        )
        
    except APIError:
        raise
    except ValueError as e:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_SUGGESTION",
            message=str(e)
        )
    except Exception as e:
        logger.error(f"Error accepting suggestion: {e}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ACCEPT_ERROR",
            message=f"Failed to accept suggestion: {str(e)}"
        )


@router.post("/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: UUID,
    reason: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Reject a task suggestion.
    
    Marks the suggestion as rejected. Does not delete it.
    
    Args:
        suggestion_id: UUID of the suggestion
        reason: Optional reason for rejection
        
    Returns:
        Updated TaskSuggestionResponse
    """
    try:
        service = TaskSuggestionService(db)
        
        suggestion = await service.get_suggestion(suggestion_id)
        if not suggestion:
            raise APIError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="SUGGESTION_NOT_FOUND",
                message=f"Suggestion {suggestion_id} not found"
            )
        
        suggestion = await service.reject_suggestion(suggestion_id, reason)
        
        return APIResponse.success(data=suggestion.to_response().model_dump(mode="json"),
            message="Suggestion rejected"
        )
        
    except APIError:
        raise
    except ValueError as e:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_SUGGESTION",
            message=str(e)
        )
    except Exception as e:
        logger.error(f"Error rejecting suggestion: {e}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="REJECT_ERROR",
            message=f"Failed to reject suggestion: {str(e)}"
        )


@router.delete("/{suggestion_id}")
async def delete_suggestion(
    suggestion_id: UUID,
    reason: str = "user_deleted",
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Soft delete a task suggestion.
    
    Preserves the suggestion for ADHD users who change their mind.
    Can be restored later with POST /restore endpoint.
    
    Args:
        suggestion_id: UUID of the suggestion
        reason: Reason for deletion (default: "user_deleted")
        
    Returns:
        Confirmation message
    """
    try:
        service = TaskSuggestionService(db)
        
        suggestion = await service.get_suggestion(suggestion_id)
        if not suggestion:
            raise APIError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="SUGGESTION_NOT_FOUND",
                message=f"Suggestion {suggestion_id} not found"
            )
        
        await service.soft_delete_suggestion(suggestion_id, reason)
        
        return APIResponse.success(data={"message": "Suggestion deleted but preserved in history. Use /restore to undo."})
        
    except APIError:
        raise
    except ValueError as e:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="DELETE_ERROR",
            message=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting suggestion: {e}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="DELETE_ERROR",
            message=f"Failed to delete suggestion: {str(e)}"
        )


@router.post("/{suggestion_id}/restore")
async def restore_suggestion(
    suggestion_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Restore a soft-deleted suggestion.
    
    For ADHD users who change their mind - this is a feature!
    Restores the suggestion to its previous state.
    
    Args:
        suggestion_id: UUID of the suggestion
        
    Returns:
        Restored TaskSuggestionResponse
    """
    try:
        service = TaskSuggestionService(db)
        
        suggestion = await service.get_suggestion(suggestion_id)
        if not suggestion:
            raise APIError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="SUGGESTION_NOT_FOUND",
                message=f"Suggestion {suggestion_id} not found"
            )
        
        if not suggestion.is_deleted:
            raise APIError(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="NOT_DELETED",
                message="Suggestion is not deleted"
            )
        
        suggestion = await service.restore_suggestion(suggestion_id)
        
        return APIResponse.success(data=suggestion.to_response().model_dump(mode="json"),
            message="Suggestion restored"
        )
        
    except APIError:
        raise
    except ValueError as e:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="RESTORE_ERROR",
            message=str(e)
        )
    except Exception as e:
        logger.error(f"Error restoring suggestion: {e}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="RESTORE_ERROR",
            message=f"Failed to restore suggestion: {str(e)}"
        )


@router.get("/thought/{thought_id}")
async def get_suggestions_for_thought(
    thought_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get all suggestions generated from a specific thought.
    
    Args:
        thought_id: UUID of the source thought
        
    Returns:
        List of TaskSuggestionResponse objects
    """
    try:
        service = TaskSuggestionService(db)
        
        suggestions = await service.get_suggestions_for_thought(thought_id)
        
        return APIResponse.success(data={
                "thought_id": str(thought_id),
                "suggestions": [s.to_response().model_dump(mode="json") for s in suggestions],
                "count": len(suggestions)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting suggestions for thought: {e}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="SUGGESTIONS_ERROR",
            message=f"Failed to get suggestions: {str(e)}"
        )
