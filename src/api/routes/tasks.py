"""
Task CRUD endpoints for Personal AI Assistant API.

Handles task creation, retrieval, updating, and deletion.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ...models import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatus,
    Priority
)
from ..auth import verify_api_key, get_current_user_id
from ..responses import (
    APIResponse,
    TaskNotFoundError
)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(verify_api_key)]
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new task from a thought or standalone."""
    user_id = get_current_user_id()
    
    # TODO: Actually save to database
    task_response = TaskResponse(
        user_id=UUID(user_id),
        source_thought_id=task.source_thought_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=TaskStatus.PENDING,
        due_date=task.due_date,
        estimated_effort_minutes=task.estimated_effort_minutes,
        completed_at=None,
        linked_reminders=[],
        subtasks=[]
    )
    
    return APIResponse.success(
        data=task_response.model_dump(mode='json'),
        status_code=status.HTTP_201_CREATED
    )


@router.get("", status_code=status.HTTP_200_OK)
async def list_tasks(
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority: Optional[Priority] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    api_key: str = Depends(verify_api_key)
):
    """List all tasks with optional filtering and pagination."""
    user_id = get_current_user_id()
    
    # TODO: Implement actual database query
    return APIResponse.success(
        data={
            "tasks": [],
            "pagination": {
                "total": 0,
                "offset": offset,
                "limit": limit,
                "has_more": False
            }
        }
    )


@router.get("/{task_id}", status_code=status.HTTP_200_OK)
async def get_task(
    task_id: UUID,
    api_key: str = Depends(verify_api_key)
):
    """Retrieve a single task by ID."""
    user_id = get_current_user_id()
    
    # TODO: Implement actual database query
    raise TaskNotFoundError(str(task_id))


@router.put("/{task_id}", status_code=status.HTTP_200_OK)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update an existing task."""
    user_id = get_current_user_id()
    
    # TODO: Implement actual database update
    raise TaskNotFoundError(str(task_id))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    api_key: str = Depends(verify_api_key)
):
    """Delete a task."""
    user_id = get_current_user_id()
    
    # TODO: Implement actual database deletion
    raise TaskNotFoundError(str(task_id))
