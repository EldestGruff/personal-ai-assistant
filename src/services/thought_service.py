"""
Thought service layer for database operations.

Handles all CRUD operations for thoughts including creation, retrieval,
searching, updating, and relationship management. Enforces business logic
and ownership validation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import or_, and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.thought import ThoughtDB
from ..models.enums import ThoughtStatus
from ..models.base import utc_now
from .exceptions import (
    NotFoundError,
    InvalidDataError,
    DatabaseError,
    UnauthorizedError
)


logger = logging.getLogger(__name__)


class ThoughtService:
    """
    Service for thought-related database operations.
    
    Provides methods for creating, reading, updating, deleting, and
    searching thoughts. All operations verify user ownership.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize thought service with database session.
        
        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session
    
    def create_thought(
        self,
        user_id: UUID,
        content: str,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ThoughtDB:
        """
        Create and persist a new thought.
        
        Args:
            user_id: UUID of the user creating the thought
            content: The thought text (1-5000 chars, validated by Pydantic)
            tags: Optional list of tags (max 5)
            context: Optional contextual metadata
            
        Returns:
            ThoughtDB: Created thought with id and timestamps
            
        Raises:
            InvalidDataError: If content is invalid
            DatabaseError: If database operation fails
        """
        try:
            thought = ThoughtDB(
                id=str(uuid4()),
                user_id=str(user_id),
                content=content.strip(),
                tags=tags or [],
                status=ThoughtStatus.ACTIVE.value,
                context=context,
                created_at=utc_now(),
                updated_at=utc_now()
            )
            
            self.db.add(thought)
            self.db.commit()
            self.db.refresh(thought)
            
            logger.info(f"Created thought {thought.id} for user {user_id}")
            return thought
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating thought: {e}")
            raise DatabaseError(
                "Failed to create thought due to database error",
                original_error=e
            )
    
    def get_thought(self, thought_id: UUID, user_id: UUID) -> ThoughtDB:
        """
        Retrieve a single thought by ID with ownership verification.
        
        Args:
            thought_id: UUID of the thought to retrieve
            user_id: UUID of the requesting user
            
        Returns:
            ThoughtDB: The requested thought
            
        Raises:
            NotFoundError: If thought doesn't exist or user doesn't own it
        """
        try:
            thought = self.db.query(ThoughtDB).filter(
                and_(
                    ThoughtDB.id == str(thought_id),
                    ThoughtDB.user_id == str(user_id)
                )
            ).first()
            
            if not thought:
                raise NotFoundError("Thought", str(thought_id))
            
            return thought
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving thought: {e}")
            raise DatabaseError(
                "Failed to retrieve thought due to database error",
                original_error=e
            )
    
    def list_thoughts(
        self,
        user_id: UUID,
        status: Optional[ThoughtStatus] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[ThoughtDB], int]:
        """
        List user's thoughts with optional filtering and pagination.
        
        Args:
            user_id: UUID of the user
            status: Optional status filter
            tags: Optional tag filter (OR logic - any tag matches)
            limit: Maximum results to return
            offset: Pagination offset
            sort_by: Column to sort by (created_at, updated_at)
            sort_order: Sort direction (asc, desc)
            
        Returns:
            Tuple of (list of thoughts, total count)
            
        Raises:
            InvalidDataError: If sort_by field is invalid
            DatabaseError: If database operation fails
        """
        try:
            # Build base query with user filter
            query = self.db.query(ThoughtDB).filter(
                ThoughtDB.user_id == str(user_id)
            )
            
            # Apply status filter if provided
            if status:
                query = query.filter(ThoughtDB.status == status.value)
            
            # Apply tag filter if provided (OR logic)
            if tags:
                # Check if any provided tag is in the thought's tags
                # SQLite doesn't have json_contains, so we use json_extract with LIKE
                tag_filters = [
                    func.json_extract(ThoughtDB.tags, '$').like(f'%"{tag}"%')
                    for tag in tags
                ]
                query = query.filter(or_(*tag_filters))
            
            # Get total count before pagination
            total = query.count()
            
            # Apply sorting
            if not hasattr(ThoughtDB, sort_by):
                raise InvalidDataError(
                    f"Invalid sort field: {sort_by}",
                    details={"valid_fields": ["created_at", "updated_at"]}
                )
            
            sort_column = getattr(ThoughtDB, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            
            # Apply pagination
            results = query.offset(offset).limit(limit).all()
            
            return results, total
            
        except InvalidDataError:
            raise  # Re-raise our custom error
        except SQLAlchemyError as e:
            logger.error(f"Database error listing thoughts: {e}")
            raise DatabaseError(
                "Failed to list thoughts due to database error",
                original_error=e
            )
    
    def update_thought(
        self,
        thought_id: UUID,
        user_id: UUID,
        **kwargs
    ) -> ThoughtDB:
        """
        Update an existing thought.
        
        Only updates provided fields. Automatically sets updated_at.
        Validates ownership before updating.
        
        Args:
            thought_id: UUID of the thought to update
            user_id: UUID of the requesting user
            **kwargs: Fields to update (content, tags, status, context, etc.)
            
        Returns:
            ThoughtDB: Updated thought
            
        Raises:
            NotFoundError: If thought doesn't exist or user doesn't own it
            InvalidDataError: If update values are invalid
            DatabaseError: If database operation fails
        """
        try:
            # Get existing thought with ownership check
            thought = self.get_thought(thought_id, user_id)
            
            # Update provided fields
            for key, value in kwargs.items():
                if hasattr(thought, key) and value is not None:
                    # Convert enum to value if needed
                    if key == "status" and isinstance(value, ThoughtStatus):
                        value = value.value
                    setattr(thought, key, value)
            
            # Always update timestamp
            thought.updated_at = utc_now()
            
            self.db.commit()
            self.db.refresh(thought)
            
            logger.info(f"Updated thought {thought_id} for user {user_id}")
            return thought
            
        except NotFoundError:
            raise  # Re-raise not found error
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating thought: {e}")
            raise DatabaseError(
                "Failed to update thought due to database error",
                original_error=e
            )
    
    def delete_thought(self, thought_id: UUID, user_id: UUID) -> bool:
        """
        Delete a thought (hard delete).
        
        Args:
            thought_id: UUID of the thought to delete
            user_id: UUID of the requesting user
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            UnauthorizedError: If user doesn't own the thought
            DatabaseError: If database operation fails
        """
        try:
            thought = self.db.query(ThoughtDB).filter(
                ThoughtDB.id == str(thought_id)
            ).first()
            
            if not thought:
                return False
            
            # Verify ownership
            if thought.user_id != str(user_id):
                raise UnauthorizedError("Thought", str(user_id))
            
            self.db.delete(thought)
            self.db.commit()
            
            logger.info(f"Deleted thought {thought_id} for user {user_id}")
            return True
            
        except UnauthorizedError:
            raise  # Re-raise authorization error
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting thought: {e}")
            raise DatabaseError(
                "Failed to delete thought due to database error",
                original_error=e
            )
    
    def search_thoughts(
        self,
        user_id: UUID,
        query: str,
        fields: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Tuple[ThoughtDB, float]], int]:
        """
        Full-text search on thought content and tags.
        
        Uses simple LIKE search for MVP. Returns results with relevance scores.
        
        Args:
            user_id: UUID of the user
            query: Search term
            fields: Fields to search (default: ["content", "tags"])
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            Tuple of ([(thought, relevance_score), ...], total_count)
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            if not query.strip():
                return [], 0
            
            search_pattern = f"%{query}%"
            fields = fields or ["content", "tags"]
            
            # Build search query
            db_query = self.db.query(ThoughtDB).filter(
                ThoughtDB.user_id == str(user_id)
            )
            
            # Add field filters
            filters = []
            if "content" in fields:
                filters.append(ThoughtDB.content.ilike(search_pattern))
            if "tags" in fields:
                # Search within JSON array
                filters.append(
                    func.json_extract(ThoughtDB.tags, '$').like(search_pattern)
                )
            
            if filters:
                db_query = db_query.filter(or_(*filters))
            
            # Get total count
            total = db_query.count()
            
            # Get results
            results = db_query.offset(offset).limit(limit).all()
            
            # Calculate relevance scores
            scored_results = []
            for thought in results:
                score = self._calculate_relevance_score(thought, query)
                scored_results.append((thought, score))
            
            # Sort by relevance score (highest first)
            scored_results.sort(key=lambda x: x[1], reverse=True)
            
            return scored_results, total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error searching thoughts: {e}")
            raise DatabaseError(
                "Failed to search thoughts due to database error",
                original_error=e
            )
    
    def _calculate_relevance_score(
        self,
        thought: ThoughtDB,
        query: str
    ) -> float:
        """
        Calculate relevance score for search result.
        
        Simple scoring: earlier match = higher score, tag match > content match.
        
        Args:
            thought: Thought to score
            query: Search query
            
        Returns:
            float: Relevance score (0.0-1.0)
        """
        score = 0.0
        query_lower = query.lower()
        
        # Tag exact match: highest score
        if thought.tags and query_lower in [t.lower() for t in thought.tags]:
            score += 0.9
        
        # Content contains query
        if query_lower in thought.content.lower():
            # Earlier in content = higher score
            position = thought.content.lower().find(query_lower)
            position_score = 1.0 - (position / len(thought.content))
            score += 0.5 * position_score
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_related_thoughts(
        self,
        thought_id: UUID,
        user_id: UUID,
        limit: int = 10
    ) -> List[ThoughtDB]:
        """
        Get thoughts related to a specific thought.
        
        NOTE: This requires the thought_relationships table which may not
        be implemented yet. For now, returns empty list.
        
        Args:
            thought_id: UUID of the source thought
            user_id: UUID of the requesting user
            limit: Maximum related thoughts to return
            
        Returns:
            List[ThoughtDB]: Related thoughts sorted by confidence
            
        Raises:
            NotFoundError: If source thought doesn't exist
        """
        # Verify source thought exists and user owns it
        self.get_thought(thought_id, user_id)
        
        # TODO: Implement once thought_relationships table exists
        # For now, return empty list
        logger.warning(
            f"get_related_thoughts called but relationships table not yet implemented"
        )
        return []
    
    def add_thought_relationship(
        self,
        source_thought_id: UUID,
        related_thought_id: UUID,
        user_id: UUID,
        relationship_type: str = "similar",
        confidence: float = 0.8,
        discovered_by: str = "claude"
    ) -> bool:
        """
        Add a relationship between two thoughts.
        
        NOTE: This requires the thought_relationships table which may not
        be implemented yet. For now, returns False.
        
        Args:
            source_thought_id: UUID of the source thought
            related_thought_id: UUID of the related thought
            user_id: UUID of the user (for ownership verification)
            relationship_type: Type of relationship (similar, elaboration, etc.)
            confidence: Confidence score (0.0-1.0)
            discovered_by: Who discovered the relationship (claude, user_manual)
            
        Returns:
            bool: True if relationship added, False otherwise
            
        Raises:
            NotFoundError: If either thought doesn't exist
        """
        # Verify both thoughts exist and user owns them
        self.get_thought(source_thought_id, user_id)
        self.get_thought(related_thought_id, user_id)
        
        # TODO: Implement once thought_relationships table exists
        logger.warning(
            f"add_thought_relationship called but relationships table not yet implemented"
        )
        return False
