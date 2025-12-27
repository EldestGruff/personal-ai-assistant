"""
Thought CRUD endpoints for Personal AI Assistant API.

Handles thought capture, retrieval, searching, updating, and deletion.
Integrated with ThoughtService for database operations.
"""

import asyncio
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status, Request
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...models import (
    ThoughtCreate,
    ThoughtUpdate,
    ThoughtResponse,
    ThoughtStatus
)
from ...services.thought_service import ThoughtService
from ...services.thought_intelligence_service import ThoughtIntelligenceService
from ...services.exceptions import (
    NotFoundError,
    InvalidDataError,
    DatabaseError,
    UnauthorizedError
)
from ..auth import verify_api_key, get_current_user_id
from ..responses import (
    APIResponse,
    ThoughtNotFoundError,
    InvalidContentError,
    APIError
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/thoughts",
    tags=["thoughts"],
    dependencies=[Depends(verify_api_key)]
)


async def analyze_thought_background(
    thought_id: UUID,
    user_id: UUID,
    orchestrator,
    db_factory
):
    """
    Background task to analyze a thought after capture.
    
    This runs asynchronously so the thought capture returns immediately.
    If analysis fails, we log but don't affect the captured thought.
    """
    try:
        # Get a fresh db session for background task
        from ...database.session import get_db_context
        from ...services.settings_service import SettingsService
        from ...services.user_profile_service import UserProfileService
        from ...services.task_suggestion_service import TaskSuggestionService
        
        with get_db_context() as db:
            # Get the thought from DB
            thought = db.query(ThoughtDB).filter(ThoughtDB.id == str(thought_id)).first()
            if not thought:
                logger.warning(f"Thought {thought_id} not found for analysis")
                return
            
            # Initialize all required services
            settings_service = SettingsService(db)
            profile_service = UserProfileService(db)
            task_suggestion_service = TaskSuggestionService(db)
            
            intelligence_service = ThoughtIntelligenceService(
                db=db,
                ai_orchestrator=orchestrator,
                settings_service=settings_service,
                user_profile_service=profile_service,
                task_suggestion_service=task_suggestion_service
            )
            
            result = await intelligence_service.analyze_thought_on_capture(
                user_id=user_id,
                thought=thought
            )
            
            if result:
                logger.info(
                    f"Analyzed thought {thought_id}: type={result.thought_type}, "
                    f"actionable={result.is_actionable}, confidence={result.actionable_confidence:.2f}"
                )
                if result.should_suggest_task:
                    logger.info(f"Created task suggestion for thought {thought_id}")
            else:
                logger.debug(f"Analysis skipped or disabled for thought {thought_id}")
                
    except Exception as e:
        # Don't let analysis failures affect the captured thought
        logger.error(f"Background analysis failed for thought {thought_id}: {e}", exc_info=True)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_thought(
    thought: ThoughtCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Capture a new thought.
    
    Takes thought content, tags, context and persists to database.
    Triggers background AI analysis if enabled in settings.
    Returns created thought with generated ID and timestamps.
    
    Args:
        thought: Thought data (content, tags, context)
        
    Returns:
        201 Created: ThoughtResponse with id, created_at, updated_at
        400 Bad Request: If content invalid
        401 Unauthorized: If API key invalid
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = ThoughtService(db)
        thought_db = service.create_thought(
            user_id=user_id,
            content=thought.content,
            tags=thought.tags,
            context=thought.context
        )
        
        # Schedule background analysis if orchestrator is available
        if hasattr(request.app.state, 'orchestrator'):
            from ...database.session import SessionLocal
            background_tasks.add_task(
                analyze_thought_background,
                thought_db.id,
                user_id,
                request.app.state.orchestrator,
                SessionLocal
            )
            logger.debug(f"Scheduled background analysis for thought {thought_db.id}")
        
        return APIResponse.success(
            data=thought_db.to_response().model_dump(mode='json'),
            status_code=status.HTTP_201_CREATED
        )
        
    except InvalidDataError as e:
        logger.warning(f"Invalid thought data: {e}")
        raise InvalidContentError(str(e))
    except DatabaseError as e:
        logger.error(f"Database error creating thought: {e}")
        raise APIError(
            code="DATABASE_ERROR",
            message="Failed to save thought to database",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("", status_code=status.HTTP_200_OK)
async def list_thoughts(
    status_filter: Optional[ThoughtStatus] = Query(None, alias="status"),
    tags: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    List user's thoughts with optional filtering and pagination.
    
    Query Parameters:
        status: Filter by thought status (active, archived, completed)
        tags: Comma-separated tags to filter by (OR logic)
        limit: Max results per page (1-100, default 20)
        offset: Pagination offset (default 0)
        sort_by: Field to sort by (created_at, updated_at)
        sort_order: asc or desc (default desc)
        
    Returns:
        thoughts: Array of ThoughtResponse objects
        pagination: total, offset, limit, has_more
    """
    try:
        user_id = UUID(get_current_user_id())
        
        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        service = ThoughtService(db)
        
        # list_thoughts returns (results, total) tuple
        results, total = service.list_thoughts(
            user_id=user_id,
            status=status_filter,
            tags=tag_list,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return APIResponse.success(
            data={
                "thoughts": [t.to_response().model_dump(mode='json') for t in results],
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
    except DatabaseError as e:
        logger.error(f"Database error listing thoughts: {e}")
        raise APIError(
            code="DATABASE_ERROR",
            message="Failed to retrieve thoughts from database",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/search", status_code=status.HTTP_200_OK)
async def search_thoughts(
    q: str = Query(..., min_length=1),
    fields: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Full-text search on thought content and tags.
    
    Query Parameters:
        q: Search term (required, min 1 char)
        fields: Fields to search in (comma-separated: content,tags)
        limit: Max results (default 50, max 100)
        offset: Pagination offset (default 0)
        
    Returns:
        query: Search term used
        results: Array of matching thoughts with relevance_score
        pagination: total, offset, limit, has_more
    """
    try:
        user_id = UUID(get_current_user_id())
        
        # Parse fields if provided
        field_list = None
        if fields:
            field_list = [field.strip() for field in fields.split(",")]
        
        service = ThoughtService(db)
        
        # search_thoughts returns ([(thought, score), ...], total) tuple
        scored_results, total = service.search_thoughts(
            user_id=user_id,
            query=q,
            fields=field_list,
            limit=limit,
            offset=offset
        )
        
        # Convert tuples to dicts with match_score
        result_data = [
            {
                **thought.to_response().model_dump(mode='json'),
                "match_score": score,
                "matched_fields": field_list or ["content", "tags"]
            }
            for thought, score in scored_results
        ]
        
        return APIResponse.success(
            data={
                "query": q,
                "results": result_data,
                "pagination": {
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                    "has_more": (offset + limit) < total
                }
            }
        )
        
    except InvalidDataError as e:
        logger.warning(f"Invalid search query: {e}")
        raise APIError(
            code="INVALID_QUERY",
            message=f"Invalid search query: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except DatabaseError as e:
        logger.error(f"Database error searching thoughts: {e}")
        raise APIError(
            code="DATABASE_ERROR",
            message="Failed to search thoughts in database",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/{thought_id}", status_code=status.HTTP_200_OK)
async def get_thought(
    thought_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Retrieve a single thought by ID.
    
    Args:
        thought_id: UUID of the thought
        
    Returns:
        200 OK: Complete ThoughtResponse
        404 Not Found: If thought doesn't exist or user doesn't own it
        401 Unauthorized: If API key invalid
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = ThoughtService(db)
        thought_db = service.get_thought(
            thought_id=thought_id,
            user_id=user_id
        )
        
        return APIResponse.success(
            data=thought_db.to_response().model_dump(mode='json')
        )
        
    except NotFoundError as e:
        logger.warning(f"Thought not found: {e}")
        raise ThoughtNotFoundError(str(thought_id))
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized access: {e}")
        raise APIError(
            code="UNAUTHORIZED",
            message="You don't have permission to access this thought",
            status_code=status.HTTP_403_FORBIDDEN
        )
    except DatabaseError as e:
        logger.error(f"Database error getting thought: {e}")
        raise APIError(
            code="DATABASE_ERROR",
            message="Failed to retrieve thought from database",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/{thought_id}", status_code=status.HTTP_200_OK)
async def update_thought(
    thought_id: UUID,
    thought_update: ThoughtUpdate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Update an existing thought.
    
    Only provided fields are updated. Unspecified fields retain their values.
    The updated_at timestamp is automatically refreshed.
    
    Args:
        thought_id: UUID of the thought
        thought_update: Fields to update (all optional)
        
    Returns:
        200 OK: Updated ThoughtResponse
        404 Not Found: If thought doesn't exist
        400 Bad Request: If update data invalid
    """
    try:
        user_id = UUID(get_current_user_id())
        
        # Only update provided fields
        update_data = thought_update.model_dump(exclude_unset=True)
        
        service = ThoughtService(db)
        thought_db = service.update_thought(
            thought_id=thought_id,
            user_id=user_id,
            **update_data
        )
        
        return APIResponse.success(
            data=thought_db.to_response().model_dump(mode='json')
        )
        
    except NotFoundError as e:
        logger.warning(f"Thought not found: {e}")
        raise ThoughtNotFoundError(str(thought_id))
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized access: {e}")
        raise APIError(
            code="UNAUTHORIZED",
            message="You don't have permission to update this thought",
            status_code=status.HTTP_403_FORBIDDEN
        )
    except InvalidDataError as e:
        logger.warning(f"Invalid update data: {e}")
        raise InvalidContentError(str(e))
    except DatabaseError as e:
        logger.error(f"Database error updating thought: {e}")
        raise APIError(
            code="DATABASE_ERROR",
            message="Failed to update thought in database",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/{thought_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thought(
    thought_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Delete a thought.
    
    Args:
        thought_id: UUID of the thought
        
    Returns:
        204 No Content: Empty body (successful deletion)
        404 Not Found: If thought doesn't exist
    """
    try:
        user_id = UUID(get_current_user_id())
        
        service = ThoughtService(db)
        deleted = service.delete_thought(
            thought_id=thought_id,
            user_id=user_id
        )
        
        if not deleted:
            logger.warning(f"Thought not found for deletion: {thought_id}")
            raise ThoughtNotFoundError(str(thought_id))
        
        logger.info(f"Deleted thought {thought_id} for user {user_id}")
        return  # 204 No Content with empty body
        
    except NotFoundError as e:
        logger.warning(f"Thought not found: {e}")
        raise ThoughtNotFoundError(str(thought_id))
    except UnauthorizedError as e:
        logger.warning(f"Unauthorized access: {e}")
        raise APIError(
            code="UNAUTHORIZED",
            message="You don't have permission to delete this thought",
            status_code=status.HTTP_403_FORBIDDEN
        )
    except DatabaseError as e:
        logger.error(f"Database error deleting thought: {e}")
        raise APIError(
            code="DATABASE_ERROR",
            message="Failed to delete thought from database",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
