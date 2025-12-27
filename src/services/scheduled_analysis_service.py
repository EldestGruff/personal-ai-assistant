"""
Scheduled analysis service for the Personal AI Assistant.

Tracks and manages scheduled consciousness checks, including status
transitions, skip logic, and performance metrics.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..models.base import utc_now
from ..models.enums import ScheduledAnalysisStatus, ThoughtStatus
from ..models.scheduled_analysis import (
    ScheduledAnalysisCreate,
    ScheduledAnalysisResponse,
    ScheduledAnalysisHistoryResponse,
    ScheduledAnalysisDB,
)
from ..models.thought import ThoughtDB
from .exceptions import NotFoundError

logger = logging.getLogger(__name__)


class ScheduledAnalysisService:
    """
    Tracks and manages scheduled consciousness checks.
    
    Provides methods for creating, updating, and querying scheduled
    analysis records. Includes skip logic based on new thought count.
    """
    
    def __init__(self, db: Session):
        """
        Initialize scheduled analysis service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_scheduled_run(
        self, 
        user_id: str,
        scheduled_at: datetime,
        triggered_by: str = "scheduler"
    ) -> ScheduledAnalysisResponse:
        """
        Create a pending scheduled analysis entry.
        
        Args:
            user_id: UUID of the user (as string)
            scheduled_at: When this was scheduled to run
            triggered_by: What triggered this: scheduler, manual, api
            
        Returns:
            Created ScheduledAnalysisResponse
        """
        analysis = ScheduledAnalysisDB(
            id=str(uuid4()),
            user_id=user_id,
            scheduled_at=scheduled_at,
            status=ScheduledAnalysisStatus.PENDING.value,
            triggered_by=triggered_by,
            created_at=utc_now()
        )
        
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        
        logger.debug(
            f"Created scheduled analysis {analysis.id} for user {user_id}"
        )
        
        return analysis.to_response()
    
    def mark_running(self, analysis_id: str) -> ScheduledAnalysisResponse:
        """
        Mark analysis as currently running.
        
        Args:
            analysis_id: UUID of the analysis (as string)
            
        Returns:
            Updated ScheduledAnalysisResponse
            
        Raises:
            NotFoundError: If analysis doesn't exist
        """
        analysis = self._get_analysis(analysis_id)
        
        analysis.status = ScheduledAnalysisStatus.RUNNING.value
        analysis.executed_at = utc_now()
        
        self.db.commit()
        self.db.refresh(analysis)
        
        logger.debug(f"Marked analysis {analysis_id} as running")
        
        return analysis.to_response()
    
    def mark_completed(
        self, 
        analysis_id: str,
        thoughts_analyzed: int,
        duration_ms: int,
        result_id: str
    ) -> ScheduledAnalysisResponse:
        """
        Mark analysis as completed with results.
        
        Args:
            analysis_id: UUID of the analysis (as string)
            thoughts_analyzed: Number of thoughts that were analyzed
            duration_ms: How long the analysis took in milliseconds
            result_id: UUID of the ClaudeAnalysisResult record
            
        Returns:
            Updated ScheduledAnalysisResponse
            
        Raises:
            NotFoundError: If analysis doesn't exist
        """
        analysis = self._get_analysis(analysis_id)
        
        analysis.status = ScheduledAnalysisStatus.COMPLETED.value
        analysis.completed_at = utc_now()
        analysis.thoughts_analyzed_count = thoughts_analyzed
        analysis.analysis_duration_ms = duration_ms
        analysis.analysis_result_id = result_id
        
        self.db.commit()
        self.db.refresh(analysis)
        
        logger.info(
            f"Completed analysis {analysis_id}: "
            f"{thoughts_analyzed} thoughts in {duration_ms}ms"
        )
        
        return analysis.to_response()
    
    def mark_skipped(
        self, 
        analysis_id: str,
        reason: str,
        thoughts_since_last: int
    ) -> ScheduledAnalysisResponse:
        """
        Mark analysis as skipped with reason.
        
        Args:
            analysis_id: UUID of the analysis (as string)
            reason: Why it was skipped (no_new_thoughts, disabled_by_user)
            thoughts_since_last: Number of thoughts since last check
            
        Returns:
            Updated ScheduledAnalysisResponse
            
        Raises:
            NotFoundError: If analysis doesn't exist
        """
        analysis = self._get_analysis(analysis_id)
        
        analysis.status = ScheduledAnalysisStatus.SKIPPED.value
        analysis.completed_at = utc_now()
        analysis.skip_reason = reason
        analysis.thoughts_since_last_check = thoughts_since_last
        
        self.db.commit()
        self.db.refresh(analysis)
        
        logger.info(
            f"Skipped analysis {analysis_id}: {reason} "
            f"({thoughts_since_last} thoughts since last)"
        )
        
        return analysis.to_response()
    
    def mark_failed(
        self, 
        analysis_id: str,
        error_message: str
    ) -> ScheduledAnalysisResponse:
        """
        Mark analysis as failed with error.
        
        Args:
            analysis_id: UUID of the analysis (as string)
            error_message: Description of what went wrong
            
        Returns:
            Updated ScheduledAnalysisResponse
            
        Raises:
            NotFoundError: If analysis doesn't exist
        """
        analysis = self._get_analysis(analysis_id)
        
        analysis.status = ScheduledAnalysisStatus.FAILED.value
        analysis.completed_at = utc_now()
        analysis.error_message = error_message
        
        self.db.commit()
        self.db.refresh(analysis)
        
        logger.error(f"Failed analysis {analysis_id}: {error_message}")
        
        return analysis.to_response()
    
    def get_last_completed_check(
        self, 
        user_id: str
    ) -> Optional[ScheduledAnalysisResponse]:
        """
        Get the most recent completed consciousness check.
        
        Args:
            user_id: UUID of the user (as string)
            
        Returns:
            ScheduledAnalysisResponse or None if no completed checks
        """
        analysis = self.db.query(ScheduledAnalysisDB).filter(
            ScheduledAnalysisDB.user_id == user_id,
            ScheduledAnalysisDB.status == ScheduledAnalysisStatus.COMPLETED.value
        ).order_by(
            desc(ScheduledAnalysisDB.completed_at)
        ).first()
        
        if not analysis:
            return None
        
        return analysis.to_response()
    
    def get_analysis_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[ScheduledAnalysisStatus] = None
    ) -> ScheduledAnalysisHistoryResponse:
        """
        Get paginated history of scheduled analyses.
        
        Args:
            user_id: UUID of the user (as string)
            limit: Maximum records per page (default 50, max 100)
            offset: Pagination offset
            status: Optional filter by status
            
        Returns:
            ScheduledAnalysisHistoryResponse with pagination info
        """
        limit = min(limit, 100)  # Cap at 100
        
        # Build query
        query = self.db.query(ScheduledAnalysisDB).filter(
            ScheduledAnalysisDB.user_id == user_id
        )
        
        if status:
            query = query.filter(
                ScheduledAnalysisDB.status == status.value
            )
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        analyses = query.order_by(
            desc(ScheduledAnalysisDB.scheduled_at)
        ).offset(offset).limit(limit).all()
        
        return ScheduledAnalysisHistoryResponse(
            analyses=[a.to_response() for a in analyses],
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(analyses)) < total
        )
    
    def count_thoughts_since_last_check(self, user_id: str) -> int:
        """
        Count new thoughts since the last completed consciousness check.
        
        Returns 0 if no previous check exists (will still run on first time).
        
        Args:
            user_id: UUID of the user (as string)
            
        Returns:
            Number of thoughts created since last completed check
        """
        last_check = self.get_last_completed_check(user_id)
        
        if not last_check:
            # First run - count all active thoughts
            count = self.db.query(func.count(ThoughtDB.id)).filter(
                ThoughtDB.user_id == user_id,
                ThoughtDB.status == ThoughtStatus.ACTIVE.value
            ).scalar()
            
            logger.debug(
                f"No previous check for user {user_id}, "
                f"found {count} active thoughts"
            )
            return count or 0
        
        # Count thoughts created after last completed check
        count = self.db.query(func.count(ThoughtDB.id)).filter(
            ThoughtDB.user_id == user_id,
            ThoughtDB.status == ThoughtStatus.ACTIVE.value,
            ThoughtDB.created_at > last_check.completed_at
        ).scalar()
        
        logger.debug(
            f"Found {count} thoughts since last check at "
            f"{last_check.completed_at} for user {user_id}"
        )
        
        return count or 0
    
    def get_by_id(self, analysis_id: str) -> ScheduledAnalysisResponse:
        """
        Get a scheduled analysis by ID.
        
        Args:
            analysis_id: UUID of the analysis (as string)
            
        Returns:
            ScheduledAnalysisResponse
            
        Raises:
            NotFoundError: If analysis doesn't exist
        """
        analysis = self._get_analysis(analysis_id)
        return analysis.to_response()
    
    def _get_analysis(self, analysis_id: str) -> ScheduledAnalysisDB:
        """
        Get analysis by ID or raise NotFoundError.
        
        Args:
            analysis_id: UUID of the analysis (as string)
            
        Returns:
            ScheduledAnalysisDB object
            
        Raises:
            NotFoundError: If analysis doesn't exist
        """
        analysis = self.db.query(ScheduledAnalysisDB).filter(
            ScheduledAnalysisDB.id == analysis_id
        ).first()
        
        if not analysis:
            raise NotFoundError(
                f"Scheduled analysis with ID '{analysis_id}' not found"
            )
        
        return analysis
