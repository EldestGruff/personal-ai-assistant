"""
Claude analysis service layer for database operations.

Stores and retrieves records of Claude's analysis for audit trail,
debugging, and providing context for future analyses.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.analysis import ClaudeAnalysisDB
from ..models.enums import AnalysisType
from ..models.base import utc_now
from .exceptions import DatabaseError


logger = logging.getLogger(__name__)


class ClaudeAnalysisService:
    """
    Service for Claude analysis result database operations.
    
    Manages storage and retrieval of Claude's reasoning, summaries,
    and suggestions for audit and context.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize analysis service with database session.
        
        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session
    
    def record_analysis(
        self,
        user_id: UUID,
        analysis_type: AnalysisType,
        summary: str,
        tokens_used: int,
        thought_id: Optional[UUID] = None,
        themes: Optional[List[str]] = None,
        suggested_action: Optional[str] = None,
        confidence: Optional[float] = None,
        raw_response: Optional[Dict[str, Any]] = None
    ) -> ClaudeAnalysisDB:
        """
        Record a Claude analysis result.
        
        Args:
            user_id: UUID of the user
            analysis_type: Type of analysis performed
            summary: Claude's high-level summary
            tokens_used: Number of API tokens consumed
            thought_id: Optional specific thought analyzed
            themes: Optional list of discovered themes
            suggested_action: Optional recommended action
            confidence: Optional confidence score (0.0-1.0)
            raw_response: Optional complete API response
            
        Returns:
            ClaudeAnalysisDB: Created analysis record
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            analysis = ClaudeAnalysisDB(
                id=str(uuid4()),
                thought_id=str(thought_id) if thought_id else None,
                user_id=str(user_id),
                analysis_type=analysis_type.value,
                summary=summary,
                themes=themes or [],
                suggested_action=suggested_action,
                confidence=confidence,
                tokens_used=tokens_used,
                raw_response=raw_response,
                created_at=utc_now(),
                updated_at=utc_now()
            )
            
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            
            logger.info(
                f"Recorded {analysis_type.value} analysis {analysis.id} "
                f"for user {user_id}"
            )
            return analysis
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error recording analysis: {e}")
            raise DatabaseError(
                "Failed to record analysis due to database error",
                original_error=e
            )
    
    def get_analysis_history(
        self,
        user_id: UUID,
        analysis_type: Optional[AnalysisType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ClaudeAnalysisDB], int]:
        """
        Retrieve past analyses with optional filtering.
        
        Args:
            user_id: UUID of the user
            analysis_type: Optional filter by analysis type
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            Tuple of (list of analyses, total count)
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(ClaudeAnalysisDB).filter(
                ClaudeAnalysisDB.user_id == str(user_id)
            )
            
            # Apply type filter if provided
            if analysis_type:
                query = query.filter(
                    ClaudeAnalysisDB.analysis_type == analysis_type.value
                )
            
            # Get total count
            total = query.count()
            
            # Get results sorted by created_at descending
            results = query.order_by(
                ClaudeAnalysisDB.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return results, total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting analysis history: {e}")
            raise DatabaseError(
                "Failed to get analysis history due to database error",
                original_error=e
            )
    
    def get_analyses_for_thought(
        self,
        thought_id: UUID,
        user_id: UUID
    ) -> List[ClaudeAnalysisDB]:
        """
        Get all analyses that touched a specific thought.
        
        Args:
            thought_id: UUID of the thought
            user_id: UUID of the requesting user
            
        Returns:
            List[ClaudeAnalysisDB]: Analyses for the thought
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            analyses = self.db.query(ClaudeAnalysisDB).filter(
                and_(
                    ClaudeAnalysisDB.thought_id == str(thought_id),
                    ClaudeAnalysisDB.user_id == str(user_id)
                )
            ).order_by(ClaudeAnalysisDB.created_at.desc()).all()
            
            return analyses
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting analyses for thought: {e}")
            raise DatabaseError(
                "Failed to get analyses for thought due to database error",
                original_error=e
            )
    
    def get_recent_analyses(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[ClaudeAnalysisDB]:
        """
        Get most recent analyses for quick context.
        
        Useful for providing Claude with recent analysis history
        for continuity.
        
        Args:
            user_id: UUID of the user
            limit: Maximum analyses to return
            
        Returns:
            List[ClaudeAnalysisDB]: Most recent analyses
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            analyses = self.db.query(ClaudeAnalysisDB).filter(
                ClaudeAnalysisDB.user_id == str(user_id)
            ).order_by(
                ClaudeAnalysisDB.created_at.desc()
            ).limit(limit).all()
            
            return analyses
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting recent analyses: {e}")
            raise DatabaseError(
                "Failed to get recent analyses due to database error",
                original_error=e
            )
    
    def get_total_tokens_used(
        self,
        user_id: UUID,
        analysis_type: Optional[AnalysisType] = None
    ) -> int:
        """
        Calculate total API tokens used.
        
        Useful for cost tracking and usage monitoring.
        
        Args:
            user_id: UUID of the user
            analysis_type: Optional filter by analysis type
            
        Returns:
            int: Total tokens used
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(
                ClaudeAnalysisDB
            ).filter(
                ClaudeAnalysisDB.user_id == str(user_id)
            )
            
            if analysis_type:
                query = query.filter(
                    ClaudeAnalysisDB.analysis_type == analysis_type.value
                )
            
            # Sum tokens_used column
            from sqlalchemy import func
            total = query.with_entities(
                func.sum(ClaudeAnalysisDB.tokens_used)
            ).scalar() or 0
            
            return total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error calculating total tokens: {e}")
            raise DatabaseError(
                "Failed to calculate total tokens due to database error",
                original_error=e
            )
