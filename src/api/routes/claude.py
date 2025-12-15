"""
Claude integration endpoints for Personal AI Assistant API.

Handles consciousness checks and Claude-powered analysis.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.claude_service import ClaudeService
from ...services.thought_service import ThoughtService
from ...services.task_service import TaskService
from ...services.claude_analysis_service import ClaudeAnalysisService
from ...services.exceptions import DatabaseError
from ...models.enums import AnalysisType, ThoughtStatus
from ..auth import verify_api_key, get_current_user_id
from ..responses import APIResponse, APIError

logger = logging.getLogger(__name__)

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
    request: ConsciousnessCheckRequest = ConsciousnessCheckRequest(),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Trigger Claude to analyze recent thoughts.

    Claude reviews recent thoughts, identifies patterns and themes,
    and suggests actionable next steps.

    Note: This endpoint takes 2-5 seconds as it calls Claude API.

    Query Parameters:
        limit_recent: Number of recent thoughts to analyze (default 10, max 50)
        include_archived: Include archived thoughts (default false)
        focus_tags: Optional list of tags to focus analysis on

    Returns:
        analysis_id: UUID of the analysis record
        timestamp: When the analysis was performed
        summary: High-level summary of thought patterns
        themes: List of discovered themes
        suggested_actions: List of recommended actions
        concerns: List of recurring concerns
        positives: List of positive patterns
        tokens_used: Total API tokens consumed
    """
    try:
        user_id = UUID(get_current_user_id())

        # Get recent thoughts
        thought_service = ThoughtService(db)

        # Build status filter
        status_filter = None if request.include_archived else ThoughtStatus.ACTIVE

        # Get thoughts with optional tag filter
        thoughts, total = thought_service.list_thoughts(
            user_id=user_id,
            status=status_filter,
            tags=request.focus_tags,
            limit=request.limit_recent,
            offset=0,
            sort_by="created_at",
            sort_order="desc"
        )

        if not thoughts:
            return APIResponse.success(
                data={
                    "analysis_id": None,
                    "timestamp": None,
                    "summary": "No thoughts found. Start capturing thoughts to enable consciousness checks.",
                    "themes": [],
                    "suggested_actions": [],
                    "concerns": [],
                    "positives": [],
                    "tokens_used": 0
                }
            )

        # Call Claude for analysis
        claude = ClaudeService()
        timeframe = "recent" if request.limit_recent <= 10 else f"last {request.limit_recent}"
        analysis_result = claude.consciousness_check(thoughts, timeframe=timeframe)

        # Record the analysis
        analysis_service = ClaudeAnalysisService(db)
        analysis_record = analysis_service.record_analysis(
            user_id=user_id,
            analysis_type=AnalysisType.CONSCIOUSNESS_CHECK,
            summary=analysis_result.get("summary", ""),
            tokens_used=analysis_result.get("tokens_used", 0),
            themes=analysis_result.get("themes", []),
            suggested_action="\n".join(analysis_result.get("suggested_actions", [])),
            raw_response=analysis_result
        )

        logger.info(
            f"Consciousness check completed for user {user_id}: "
            f"{len(thoughts)} thoughts analyzed, "
            f"{analysis_result.get('tokens_used', 0)} tokens used"
        )

        return APIResponse.success(
            data={
                "analysis_id": analysis_record.id,
                "timestamp": analysis_record.created_at.isoformat(),
                "summary": analysis_result.get("summary", ""),
                "themes": analysis_result.get("themes", []),
                "suggested_actions": analysis_result.get("suggested_actions", []),
                "concerns": analysis_result.get("concerns", []),
                "positives": analysis_result.get("positives", []),
                "tokens_used": analysis_result.get("tokens_used", 0),
                "thoughts_analyzed": len(thoughts)
            }
        )

    except ValueError as e:
        logger.error(f"Claude service configuration error: {e}")
        raise APIError(
            code="CLAUDE_CONFIG_ERROR",
            message="Claude API is not configured. Check ANTHROPIC_API_KEY environment variable.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error during consciousness check: {e}")
        raise APIError(
            code="CONSCIOUSNESS_CHECK_FAILED",
            message=f"Failed to perform consciousness check: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TagSuggestionRequest(BaseModel):
    """Request model for tag suggestions."""

    thought_id: UUID = Field(
        description="UUID of the thought to suggest tags for"
    )


@router.post("/suggest-tags", status_code=status.HTTP_200_OK)
async def suggest_tags(
    request: TagSuggestionRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered tag suggestions for a thought.

    Args:
        thought_id: UUID of the thought

    Returns:
        suggested_tags: List of 1-3 suggested tags
        reasoning: Brief explanation
        tokens_used: API tokens consumed
    """
    try:
        user_id = UUID(get_current_user_id())

        # Get the thought
        thought_service = ThoughtService(db)
        thought = thought_service.get_thought(request.thought_id, user_id)

        # Get all existing tags for context
        all_thoughts, _ = thought_service.list_thoughts(
            user_id=user_id,
            limit=100,
            offset=0
        )

        existing_tags = set()
        for t in all_thoughts:
            if t.tags:
                existing_tags.update(t.tags)

        # Call Claude for tag suggestions
        claude = ClaudeService()
        result = claude.suggest_tags(
            thought_content=thought.content,
            existing_tags=list(existing_tags) if existing_tags else None
        )

        logger.info(
            f"Tag suggestions for thought {request.thought_id}: "
            f"{result.get('suggested_tags', [])}"
        )

        return APIResponse.success(
            data={
                "thought_id": str(request.thought_id),
                "suggested_tags": result.get("suggested_tags", []),
                "reasoning": result.get("reasoning", ""),
                "tokens_used": result.get("tokens_used", 0)
            }
        )

    except Exception as e:
        logger.error(f"Error suggesting tags: {e}")
        raise APIError(
            code="TAG_SUGGESTION_FAILED",
            message=f"Failed to suggest tags: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TaskExtractionRequest(BaseModel):
    """Request model for task extraction."""

    limit_recent: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of recent thoughts to analyze for tasks"
    )


@router.post("/extract-tasks", status_code=status.HTTP_200_OK)
async def extract_tasks(
    request: TaskExtractionRequest = TaskExtractionRequest(),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Extract actionable tasks from recent thoughts.

    Analyzes recent thoughts and identifies action items that should
    become tasks. Can optionally auto-create the suggested tasks.

    Query Parameters:
        limit_recent: Number of recent thoughts to analyze (default 20, max 100)

    Returns:
        tasks: List of extracted tasks with title, description, priority
        reasoning: Explanation of task extraction logic
        tokens_used: API tokens consumed
    """
    try:
        user_id = UUID(get_current_user_id())

        # Get recent thoughts
        thought_service = ThoughtService(db)
        thoughts, total = thought_service.list_thoughts(
            user_id=user_id,
            status=ThoughtStatus.ACTIVE,
            limit=request.limit_recent,
            offset=0,
            sort_by="created_at",
            sort_order="desc"
        )

        if not thoughts:
            return APIResponse.success(
                data={
                    "tasks": [],
                    "reasoning": "No thoughts found to analyze",
                    "tokens_used": 0
                }
            )

        # Call Claude for task extraction
        claude = ClaudeService()
        result = claude.extract_tasks(thoughts)

        logger.info(
            f"Task extraction for user {user_id}: "
            f"{len(result.get('tasks', []))} tasks found from "
            f"{len(thoughts)} thoughts"
        )

        return APIResponse.success(
            data={
                "tasks": result.get("tasks", []),
                "reasoning": result.get("reasoning", ""),
                "tokens_used": result.get("tokens_used", 0),
                "thoughts_analyzed": len(thoughts)
            }
        )

    except Exception as e:
        logger.error(f"Error extracting tasks: {e}")
        raise APIError(
            code="TASK_EXTRACTION_FAILED",
            message=f"Failed to extract tasks: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ThoughtAnalysisRequest(BaseModel):
    """Request model for single thought analysis."""

    thought_id: UUID = Field(
        description="UUID of the thought to analyze"
    )
    include_context: bool = Field(
        default=True,
        description="Include recent related thoughts for context"
    )


@router.post("/analyze-thought", status_code=status.HTTP_200_OK)
async def analyze_thought(
    request: ThoughtAnalysisRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Deep analysis of a single thought.

    Provides insights, theme connections, tag suggestions, and determines
    if the thought is actionable.

    Args:
        thought_id: UUID of the thought to analyze
        include_context: Include recent thoughts for context (default true)

    Returns:
        summary: One-sentence summary
        insights: List of insights or observations
        related_themes: Themes this thought relates to
        suggested_tags: Tag suggestions
        is_actionable: Whether this should become a task
        action_suggestion: Optional task title if actionable
        tokens_used: API tokens consumed
    """
    try:
        user_id = UUID(get_current_user_id())

        # Get the thought
        thought_service = ThoughtService(db)
        thought = thought_service.get_thought(request.thought_id, user_id)

        # Get context thoughts if requested
        context_thoughts = None
        if request.include_context:
            recent_thoughts, _ = thought_service.list_thoughts(
                user_id=user_id,
                limit=10,
                offset=0,
                sort_by="created_at",
                sort_order="desc"
            )
            # Exclude the thought being analyzed
            context_thoughts = [t for t in recent_thoughts if t.id != str(request.thought_id)][:5]

        # Call Claude for analysis
        claude = ClaudeService()
        result = claude.analyze_thought(thought, context_thoughts=context_thoughts)

        # Record the analysis
        analysis_service = ClaudeAnalysisService(db)
        analysis_record = analysis_service.record_analysis(
            user_id=user_id,
            analysis_type=AnalysisType.SIMILARITY_CHECK,
            thought_id=request.thought_id,
            summary=result.get("summary", ""),
            tokens_used=result.get("tokens_used", 0),
            themes=result.get("related_themes", []),
            suggested_action=result.get("action_suggestion"),
            confidence=1.0 if result.get("is_actionable") else 0.0,
            raw_response=result
        )

        logger.info(
            f"Thought analysis for {request.thought_id}: "
            f"actionable={result.get('is_actionable')}"
        )

        return APIResponse.success(
            data={
                "analysis_id": analysis_record.id,
                "thought_id": str(request.thought_id),
                "summary": result.get("summary", ""),
                "insights": result.get("insights", []),
                "related_themes": result.get("related_themes", []),
                "suggested_tags": result.get("suggested_tags", []),
                "is_actionable": result.get("is_actionable", False),
                "action_suggestion": result.get("action_suggestion"),
                "tokens_used": result.get("tokens_used", 0)
            }
        )

    except Exception as e:
        logger.error(f"Error analyzing thought: {e}")
        raise APIError(
            code="THOUGHT_ANALYSIS_FAILED",
            message=f"Failed to analyze thought: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
