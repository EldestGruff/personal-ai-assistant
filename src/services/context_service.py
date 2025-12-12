"""
Context service layer for database operations.

Handles context session management including starting, ending, and
retrieving contextual information about when and where thoughts occurred.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.context import ContextDB
from ..models.enums import TimeOfDay, EnergyLevel, FocusState
from ..models.base import utc_now
from .exceptions import (
    NotFoundError,
    InvalidDataError,
    DatabaseError
)


logger = logging.getLogger(__name__)


class ContextService:
    """
    Service for context-related database operations.
    
    Manages context sessions that track user's situational state
    during thought capture.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize context service with database session.
        
        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session
    
    def start_context_session(
        self,
        user_id: UUID,
        session_id: str,
        current_activity: Optional[str] = None,
        active_app: Optional[str] = None,
        location: Optional[str] = None,
        time_of_day: Optional[TimeOfDay] = None,
        energy_level: Optional[EnergyLevel] = None,
        focus_state: Optional[FocusState] = None,
        notes: Optional[str] = None
    ) -> ContextDB:
        """
        Create a new context session.
        
        Args:
            user_id: UUID of the user
            session_id: Unique identifier for this context session
            current_activity: What the user is doing
            active_app: Foreground application
            location: Physical location
            time_of_day: General time of day
            energy_level: User's energy level
            focus_state: User's focus state
            notes: Additional notes
            
        Returns:
            ContextDB: Created context session
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            context = ContextDB(
                id=session_id,  # session_id is the primary key
                user_id=str(user_id),
                started_at=utc_now(),
                current_activity=current_activity,
                active_app=active_app,
                location=location,
                time_of_day=time_of_day.value if time_of_day else None,
                energy_level=energy_level.value if energy_level else None,
                focus_state=focus_state.value if focus_state else None,
                thought_count=0,
                notes=notes,
                ended_at=None
            )
            
            self.db.add(context)
            self.db.commit()
            self.db.refresh(context)
            
            logger.info(f"Started context session {session_id} for user {user_id}")
            return context
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error starting context session: {e}")
            raise DatabaseError(
                "Failed to start context session due to database error",
                original_error=e
            )
    
    def end_context_session(
        self,
        session_id: str,
        user_id: UUID
    ) -> ContextDB:
        """
        Mark a context session as ended.
        
        Args:
            session_id: ID of the context session to end
            user_id: UUID of the requesting user
            
        Returns:
            ContextDB: Ended context session
            
        Raises:
            NotFoundError: If session doesn't exist or user doesn't own it
            DatabaseError: If database operation fails
        """
        try:
            context = self.db.query(ContextDB).filter(
                and_(
                    ContextDB.id == session_id,
                    ContextDB.user_id == str(user_id)
                )
            ).first()
            
            if not context:
                raise NotFoundError("Context session", session_id)
            
            # Set end time if not already set
            if not context.ended_at:
                context.ended_at = utc_now()
            
            self.db.commit()
            self.db.refresh(context)
            
            logger.info(f"Ended context session {session_id} for user {user_id}")
            return context
            
        except NotFoundError:
            raise  # Re-raise not found error
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error ending context session: {e}")
            raise DatabaseError(
                "Failed to end context session due to database error",
                original_error=e
            )
    
    def get_current_context(self, user_id: UUID) -> Optional[ContextDB]:
        """
        Get the active (not-ended) context session for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Optional[ContextDB]: Active context session or None
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            context = self.db.query(ContextDB).filter(
                and_(
                    ContextDB.user_id == str(user_id),
                    ContextDB.ended_at == None
                )
            ).order_by(ContextDB.started_at.desc()).first()
            
            return context
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting current context: {e}")
            raise DatabaseError(
                "Failed to get current context due to database error",
                original_error=e
            )
    
    def get_context_history(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ContextDB], int]:
        """
        Retrieve past context sessions.
        
        Args:
            user_id: UUID of the user
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            Tuple of (list of contexts, total count)
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(ContextDB).filter(
                ContextDB.user_id == str(user_id)
            )
            
            # Get total count
            total = query.count()
            
            # Get results sorted by started_at descending
            results = query.order_by(
                ContextDB.started_at.desc()
            ).offset(offset).limit(limit).all()
            
            return results, total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting context history: {e}")
            raise DatabaseError(
                "Failed to get context history due to database error",
                original_error=e
            )
    
    def increment_thought_count(
        self,
        session_id: str,
        user_id: UUID
    ) -> ContextDB:
        """
        Increment the thought count for a context session.
        
        Called when a thought is captured within a context session.
        
        Args:
            session_id: ID of the context session
            user_id: UUID of the user
            
        Returns:
            ContextDB: Updated context session
            
        Raises:
            NotFoundError: If session doesn't exist or user doesn't own it
            DatabaseError: If database operation fails
        """
        try:
            context = self.db.query(ContextDB).filter(
                and_(
                    ContextDB.id == session_id,
                    ContextDB.user_id == str(user_id)
                )
            ).first()
            
            if not context:
                raise NotFoundError("Context session", session_id)
            
            context.thought_count += 1
            
            self.db.commit()
            self.db.refresh(context)
            
            logger.debug(
                f"Incremented thought count for session {session_id} "
                f"to {context.thought_count}"
            )
            return context
            
        except NotFoundError:
            raise  # Re-raise not found error
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error incrementing thought count: {e}")
            raise DatabaseError(
                "Failed to increment thought count due to database error",
                original_error=e
            )
    
    def get_context(
        self,
        session_id: str,
        user_id: UUID
    ) -> ContextDB:
        """
        Get a specific context session by ID.
        
        Args:
            session_id: ID of the context session
            user_id: UUID of the requesting user
            
        Returns:
            ContextDB: The requested context session
            
        Raises:
            NotFoundError: If session doesn't exist or user doesn't own it
            DatabaseError: If database operation fails
        """
        try:
            context = self.db.query(ContextDB).filter(
                and_(
                    ContextDB.id == session_id,
                    ContextDB.user_id == str(user_id)
                )
            ).first()
            
            if not context:
                raise NotFoundError("Context session", session_id)
            
            return context
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting context: {e}")
            raise DatabaseError(
                "Failed to get context due to database error",
                original_error=e
            )
