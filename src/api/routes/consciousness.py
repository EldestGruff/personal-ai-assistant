"""
Consciousness check endpoints.

Handles retrieving scheduled consciousness checks and manually triggering them.
"""

import logging
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ...api.auth import verify_api_key, get_current_user_id
from ...database.session import get_db
from ...services.thought_service import ThoughtService
from ...services.claude_service import ClaudeService
from ...services.claude_analysis_service import ClaudeAnalysisService
from ...models.enums import AnalysisType, ThoughtStatus
from ...api.responses import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/consciousness/latest")
async def get_latest_consciousness_check(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get the latest scheduled consciousness check result.

    Returns the most recent consciousness check analysis from the database,
    which is generated automatically every 30 minutes by the background scheduler.
    """
    try:
        user_id = UUID(get_current_user_id())
        analysis_service = ClaudeAnalysisService(db)

        # Get the most recent consciousness check
        latest = analysis_service.get_latest_by_type(
            user_id=user_id,
            analysis_type=AnalysisType.CONSCIOUSNESS_CHECK
        )

        if not latest:
            return APIResponse.success(
                data={
                    "has_check": False,
                    "message": "No consciousness checks found yet. First check will run automatically within 30 minutes."
                }
            )

        return APIResponse.success(
            data={
                "has_check": True,
                "id": str(latest.id),
                "summary": latest.summary,
                "themes": latest.themes,
                "suggested_actions": latest.suggested_action.split("\n") if latest.suggested_action else [],
                "tokens_used": latest.tokens_used,
                "created_at": latest.created_at.isoformat() if latest.created_at else None,
                "raw_response": latest.raw_response
            }
        )

    except Exception as e:
        logger.error(f"Error retrieving latest consciousness check: {e}")
        return APIResponse.error(
            code="RETRIEVAL_ERROR",
            message=f"Failed to retrieve consciousness check: {str(e)}"
        )


@router.post("/consciousness/trigger")
async def trigger_consciousness_check(
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Manually trigger a consciousness check to run immediately.

    This runs the same analysis as the scheduled job but executes immediately
    in the background. The result will be saved to the database and can be
    retrieved via /consciousness/latest.
    """
    try:
        user_id = UUID(get_current_user_id())

        # Run the check in the background
        background_tasks.add_task(
            _run_consciousness_check_for_user,
            db=db,
            user_id=user_id
        )

        return APIResponse.success(
            data={
                "message": "Consciousness check triggered and running in background",
                "status": "processing"
            }
        )

    except Exception as e:
        logger.error(f"Error triggering consciousness check: {e}")
        return APIResponse.error(
            code="TRIGGER_ERROR",
            message=f"Failed to trigger consciousness check: {str(e)}"
        )


async def _run_consciousness_check_for_user(db: Session, user_id: UUID):
    """
    Run consciousness check for a specific user (background task).

    Args:
        db: Database session
        user_id: User UUID
    """
    try:
        logger.info(f"🧠 Running manual consciousness check for user {user_id}...")

        # Get recent thoughts
        thought_service = ThoughtService(db)
        thoughts, total = thought_service.list_thoughts(
            user_id=user_id,
            status=ThoughtStatus.ACTIVE,
            limit=20,
            offset=0,
            sort_by="created_at",
            sort_order="desc"
        )

        if not thoughts:
            logger.info(f"No thoughts found for user {user_id}, skipping check")
            return

        # Call Claude for analysis
        claude = ClaudeService()
        analysis_result = claude.consciousness_check(thoughts, timeframe="recent")

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
            f"✅ Manual consciousness check completed for user {user_id}: "
            f"{len(thoughts)} thoughts, {analysis_result.get('tokens_used', 0)} tokens"
        )

    except Exception as e:
        logger.error(f"Error in manual consciousness check for user {user_id}: {e}")
