"""
Task CRUD endpoints for Personal AI Assistant API.

Handles task creation, retrieval, updating, completion, and deletion.
Integrated with TaskService for database operations.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...models import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatus,
    Priority
)
from ...services.task_service import TaskService
from ...services.exceptions import (
    NotFoundError,
    InvalidDataError,
    DatabaseError,
    UnauthorizedError
)
from ..auth import verify_api_key, get_current_user_id
from ..responses import (
    APIResponse,
    TaskNotFoundError,
    APIError
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(verify_api_key)]
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Create a new task from a thought or standalone.
    
    Tasks can be created independently or linked to a source thought.
    If source_thought_id is provided, it must belong to the current user.
    
    Args:
        task: Task creation data
        
    Returns:
        201 Created: TaskResponse with generated ID and timestamps
        400 Bad Request: If task data invalid
        404 Not Found: If source_thought_id doesn't exist
        401 Unauthorized: If API key invalid
        
    Example:
        POST /api/v1/tasks
        {
            "title": "Improve email analyzer",
            "description": "Add regex patterns for unsubscribe URLs",
            "source_thought_id": "a8f4c2b1-9d7e-4e3f-8b6c-1a2d3e4f5g6h",
            "priority": "medium",
            "due_date": "2025-12-17",
            "estimated_effort_minutes": 120
        }
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = TaskService(db)
        task_db = service.create_task(
            user_id=user_id,
            title=task.title,
            description=task.description,
            source_thought_id=task.source_thought_id,
            priority=task.priority,
            due_date=task.due_date,
            estimated_effort_minutes=task.estimated_effort_minutes
        )
        
        return APIResponse.success(
            data=task_db.to_response().model_dump(mode='json'),
            status_code=status.HTTP_201_CREATED
        )
        
    except NotFoundError as e:
        logger.warning(f"Source thought not found: {e}")
        raise APIError(
            code="SOURCE_THOUGHT_NOT_FOUND",
            message=f"Source thought not found: {str(e)}",
            status_code=status.HTTP_404_NOT_FOUND
        )
    except InvalidDataError as e:
        logger.warning(f"Invalid task data: {e}")
        raise APIError(
            code="INVALID_TASK",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except DatabaseError as e:
        logger.error(f"Database error creating task: {e}")
        raise APIError(
            code="DATABASE_ERROR",
            message="Failed to save task to database",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("", status_code=status.HTTP_200_OK)
async def list_tasks(
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority: Optional[Priority] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    List user's tasks with optional filtering and pagination.
    
    Query Parameters:
        status: Filter by task status (pending, in_progress, done, cancelled)
        priority: Filter by priority (low, medium, high, critical)
        limit: Max results per page (1-100, default 20)
        offset: Pagination offset (default 0)
        sort_by: Field to sort by (created_at, updated_at, due_date, priority)
        sort_order: asc or desc (default desc)
        
    Returns:
        200 OK: Array of tasks with pagination metadata
        400 Bad Request: If filter parameters invalid
        401 Unauthorized: If API key invalid
        
    Example:
        GET /api/v1/tasks?status=pending&priority=high&limit=10
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = TaskService(db)
        results, total = service.list_tasks(
            user_id=user_id,
            status=status_filter,
            priority=priority,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        task_responses = [r.to_response().model_dump(mode='json') for r in results]
        
        return APIResponse.success(
            data={
                "tasks": task_responses,
                "pagination": {
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                    "has_more": (offset + limit) < total
                }
            }
        )
        
    except InvalidDataError as e:
        logger.warning(f"Invalid filter parameters: {e}")
        raise APIError(
            code="INVALID_FILTER",
            message=f"Invalid filter parameters: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


@router.get("/{task_id}", status_code=status.HTTP_200_OK)
async def get_task(
    task_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Retrieve a single task by ID.
    
    Args:
        task_id: UUID of the task
        
    Returns:
        200 OK: Complete TaskResponse with all fields
        404 Not Found: If task doesn't exist or user doesn't own it
        401 Unauthorized: If API key invalid
        
    Example:
        GET /api/v1/tasks/b7e3d4c2-8f6e-5a2d-9c7b-2e3f4g5h6i7j
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = TaskService(db)
        task_db = service.get_task(
            task_id=task_id,
            user_id=user_id
        )
        
        return APIResponse.success(
            data=task_db.to_response().model_dump(mode='json')
        )
        
    except NotFoundError as e:
        logger.warning(f"Task not found: {e}")
        raise TaskNotFoundError(str(task_id))
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized access attempt: {e}")
        raise APIError(
            code="UNAUTHORIZED",
            message="You do not have permission to access this task",
            status_code=status.HTTP_403_FORBIDDEN
        )


@router.put("/{task_id}", status_code=status.HTTP_200_OK)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Update an existing task.
    
    Only provided fields are updated. Unspecified fields retain their values.
    The updated_at timestamp is automatically refreshed.
    
    Args:
        task_id: UUID of the task
        task_update: Fields to update (all optional)
        
    Returns:
        200 OK: Updated TaskResponse
        404 Not Found: If task doesn't exist
        400 Bad Request: If update data invalid
        401 Unauthorized: If API key invalid
        
    Example:
        PUT /api/v1/tasks/b7e3d4c2-8f6e-5a2d-9c7b-2e3f4g5h6i7j
        {
            "title": "Updated task title",
            "priority": "high",
            "status": "in_progress"
        }
    """
    try:
        user_id = UUID(get_current_user_id())
        
        # Only update provided fields
        update_data = task_update.model_dump(exclude_unset=True)
        
        service = TaskService(db)
        task_db = service.update_task(
            task_id=task_id,
            user_id=user_id,
            **update_data
        )
        
        return APIResponse.success(
            data=task_db.to_response().model_dump(mode='json')
        )
        
    except NotFoundError as e:
        logger.warning(f"Task not found for update: {e}")
        raise TaskNotFoundError(str(task_id))
    except InvalidDataError as e:
        logger.warning(f"Invalid update data: {e}")
        raise APIError(
            code="INVALID_TASK",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Delete a task.
    
    Permanently removes the task from the database.
    
    Args:
        task_id: UUID of the task
        
    Returns:
        204 No Content: Empty body (successful deletion)
        404 Not Found: If task doesn't exist
        401 Unauthorized: If API key invalid
        
    Example:
        DELETE /api/v1/tasks/b7e3d4c2-8f6e-5a2d-9c7b-2e3f4g5h6i7j
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = TaskService(db)
        deleted = service.delete_task(
            task_id=task_id,
            user_id=user_id
        )
        
        if not deleted:
            logger.warning(f"Task not found for deletion: {task_id}")
            raise TaskNotFoundError(str(task_id))
        
        logger.info(f"Deleted task {task_id} for user {user_id}")
        return  # 204 No Content with empty body
        
    except NotFoundError as e:
        logger.warning(f"Task not found for deletion: {e}")
        raise TaskNotFoundError(str(task_id))


@router.post("/{task_id}/complete", status_code=status.HTTP_200_OK)
async def complete_task(
    task_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Mark a task as completed.
    
    Sets task status to 'done' and records completion timestamp.
    This is a convenience endpoint for the common completion action.
    
    Args:
        task_id: UUID of the task
        
    Returns:
        200 OK: Updated TaskResponse with status=done and completed_at set
        404 Not Found: If task doesn't exist
        401 Unauthorized: If API key invalid
        
    Example:
        POST /api/v1/tasks/b7e3d4c2-8f6e-5a2d-9c7b-2e3f4g5h6i7j/complete
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = TaskService(db)
        task_db = service.complete_task(
            task_id=task_id,
            user_id=user_id
        )
        
        logger.info(f"Completed task {task_id} for user {user_id}")
        
        return APIResponse.success(
            data=task_db.to_response().model_dump(mode='json')
        )
        
    except NotFoundError as e:
        logger.warning(f"Task not found for completion: {e}")
        raise TaskNotFoundError(str(task_id))
