"""
Task Suggestion Service for Personal AI Assistant.

Phase 3B Spec 2: Manages AI-generated task suggestions with soft delete
for ADHD-friendly restoration. Users can change their mind and restore
deleted suggestions.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.models import (
    TaskSuggestionDB,
    TaskSuggestionCreate,
    TaskSuggestionAccept,
    TaskSuggestionResponse,
    TaskSuggestionStatus,
    TaskSuggestionUserAction,
    TaskDB,
    TaskStatus,
    Priority,
)


class TaskSuggestionService:
    """
    Manages task suggestions - create, present, accept/reject.
    
    Preserves deleted suggestions for ADHD users who change their mind.
    This is a feature, not a bug - restoration is intentional.
    """
    
    def __init__(self, db: Session):
        """
        Initialize TaskSuggestionService.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    async def create_suggestion(
        self,
        user_id: UUID,
        create_data: TaskSuggestionCreate
    ) -> TaskSuggestionDB:
        """
        Create a new task suggestion from analysis.
        
        Args:
            user_id: UUID of the user
            create_data: TaskSuggestionCreate with suggestion details
            
        Returns:
            Created TaskSuggestionDB
        """
        now = datetime.now(timezone.utc)
        
        suggestion = TaskSuggestionDB(
            id=str(uuid4()),
            user_id=str(user_id),
            source_thought_id=str(create_data.source_thought_id),
            title=create_data.title,
            description=create_data.description,
            priority=create_data.priority.value if hasattr(create_data.priority, 'value') else create_data.priority,
            estimated_effort_minutes=create_data.estimated_effort_minutes,
            due_date_hint=create_data.due_date_hint,
            confidence=create_data.confidence,
            reasoning=create_data.reasoning,
            status=TaskSuggestionStatus.PENDING.value,
            user_action=None,
            user_action_at=None,
            created_task_id=None,
            is_deleted=False,
            deleted_at=None,
            deletion_reason=None,
            created_at=now,
            updated_at=now,
        )
        
        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)
        
        return suggestion
    
    async def get_suggestion(self, suggestion_id: UUID) -> Optional[TaskSuggestionDB]:
        """
        Get a single suggestion by ID.
        
        Args:
            suggestion_id: UUID of the suggestion
            
        Returns:
            TaskSuggestionDB or None
        """
        return self.db.query(TaskSuggestionDB).filter(
            TaskSuggestionDB.id == str(suggestion_id)
        ).first()
    
    async def get_pending_suggestions(
        self,
        user_id: UUID,
        min_confidence: float = 0.0
    ) -> List[TaskSuggestionDB]:
        """
        Get all pending task suggestions for user.
        
        Args:
            user_id: UUID of the user
            min_confidence: Minimum confidence threshold (default 0.0)
            
        Returns:
            List of pending TaskSuggestionDB records
        """
        return self.db.query(TaskSuggestionDB).filter(
            TaskSuggestionDB.user_id == str(user_id),
            TaskSuggestionDB.status.in_([
                TaskSuggestionStatus.PENDING.value,
                TaskSuggestionStatus.PRESENTED.value
            ]),
            TaskSuggestionDB.is_deleted == False,
            TaskSuggestionDB.confidence >= min_confidence
        ).order_by(TaskSuggestionDB.confidence.desc()).all()
    
    async def mark_as_presented(
        self,
        suggestion_id: UUID
    ) -> TaskSuggestionDB:
        """
        Mark a suggestion as presented to user.
        
        Args:
            suggestion_id: UUID of the suggestion
            
        Returns:
            Updated TaskSuggestionDB
            
        Raises:
            ValueError: If suggestion not found
        """
        suggestion = await self.get_suggestion(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion {suggestion_id} not found")
        
        suggestion.status = TaskSuggestionStatus.PRESENTED.value
        suggestion.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(suggestion)
        
        return suggestion
    
    async def accept_suggestion(
        self,
        suggestion_id: UUID,
        user_modifications: Optional[TaskSuggestionAccept] = None
    ) -> TaskDB:
        """
        Accept a task suggestion and create actual task.
        
        Args:
            suggestion_id: UUID of the suggestion
            user_modifications: Optional changes to title, priority, etc.
            
        Returns:
            Created TaskDB object
            
        Raises:
            ValueError: If suggestion not found
        """
        suggestion = await self.get_suggestion(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion {suggestion_id} not found")
        
        now = datetime.now(timezone.utc)
        
        # Build task data with optional modifications
        title = suggestion.title
        description = suggestion.description
        priority = suggestion.priority
        estimated_effort = suggestion.estimated_effort_minutes
        due_date = suggestion.due_date_hint
        
        if user_modifications:
            if user_modifications.title is not None:
                title = user_modifications.title
            if user_modifications.description is not None:
                description = user_modifications.description
            if user_modifications.priority is not None:
                priority = user_modifications.priority.value if hasattr(user_modifications.priority, 'value') else user_modifications.priority
            if user_modifications.estimated_effort_minutes is not None:
                estimated_effort = user_modifications.estimated_effort_minutes
            if user_modifications.due_date is not None:
                due_date = user_modifications.due_date
        
        # Create task
        task = TaskDB(
            id=str(uuid4()),
            user_id=suggestion.user_id,
            source_thought_id=suggestion.source_thought_id,
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING.value,
            due_date=due_date,
            estimated_effort_minutes=estimated_effort,
            completed_at=None,
            linked_reminders=[],
            subtasks=[],
            created_at=now,
            updated_at=now,
        )
        
        self.db.add(task)
        
        # Update suggestion
        user_action = TaskSuggestionUserAction.MODIFIED.value if user_modifications else TaskSuggestionUserAction.ACCEPTED.value
        
        suggestion.status = TaskSuggestionStatus.ACCEPTED.value
        suggestion.user_action = user_action
        suggestion.user_action_at = now
        suggestion.created_task_id = task.id
        suggestion.updated_at = now
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    async def reject_suggestion(
        self,
        suggestion_id: UUID,
        reason: Optional[str] = None
    ) -> TaskSuggestionDB:
        """
        Reject a task suggestion.
        
        Args:
            suggestion_id: UUID of the suggestion
            reason: Optional reason for rejection
            
        Returns:
            Updated TaskSuggestionDB
            
        Raises:
            ValueError: If suggestion not found
        """
        suggestion = await self.get_suggestion(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion {suggestion_id} not found")
        
        now = datetime.now(timezone.utc)
        
        suggestion.status = TaskSuggestionStatus.REJECTED.value
        suggestion.user_action = TaskSuggestionUserAction.REJECTED.value
        suggestion.user_action_at = now
        suggestion.updated_at = now
        
        # Store reason in deletion_reason field (reusing for simplicity)
        if reason:
            suggestion.deletion_reason = reason
        
        self.db.commit()
        self.db.refresh(suggestion)
        
        return suggestion
    
    async def soft_delete_suggestion(
        self,
        suggestion_id: UUID,
        reason: str = "user_deleted"
    ) -> TaskSuggestionDB:
        """
        Soft delete - preserve for ADHD users who change their mind.
        
        This is an intentional feature. Deleted suggestions can be restored.
        
        Args:
            suggestion_id: UUID of the suggestion
            reason: Reason for deletion
            
        Returns:
            Updated TaskSuggestionDB
            
        Raises:
            ValueError: If suggestion not found
        """
        suggestion = await self.get_suggestion(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion {suggestion_id} not found")
        
        now = datetime.now(timezone.utc)
        
        suggestion.is_deleted = True
        suggestion.deleted_at = now
        suggestion.deletion_reason = reason
        suggestion.updated_at = now
        # Don't change status - allows restoration to previous state
        
        self.db.commit()
        self.db.refresh(suggestion)
        
        return suggestion
    
    async def restore_suggestion(
        self,
        suggestion_id: UUID
    ) -> TaskSuggestionDB:
        """
        Restore a soft-deleted suggestion.
        
        For ADHD users who change their mind - this is a feature!
        
        Args:
            suggestion_id: UUID of the suggestion
            
        Returns:
            Restored TaskSuggestionDB
            
        Raises:
            ValueError: If suggestion not found or not deleted
        """
        suggestion = await self.get_suggestion(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion {suggestion_id} not found")
        
        if not suggestion.is_deleted:
            raise ValueError("Suggestion is not deleted")
        
        now = datetime.now(timezone.utc)
        
        suggestion.is_deleted = False
        suggestion.deleted_at = None
        suggestion.deletion_reason = None
        suggestion.user_action = TaskSuggestionUserAction.DELETED_THEN_RECREATED.value
        suggestion.updated_at = now
        
        # Reset to presented status if it was pending before
        if suggestion.status in [TaskSuggestionStatus.PENDING.value, TaskSuggestionStatus.PRESENTED.value]:
            suggestion.status = TaskSuggestionStatus.PRESENTED.value
        
        self.db.commit()
        self.db.refresh(suggestion)
        
        return suggestion
    
    async def get_suggestion_history(
        self,
        user_id: UUID,
        include_deleted: bool = False,
        limit: int = 50
    ) -> List[TaskSuggestionDB]:
        """
        Get suggestion history for user.
        
        Args:
            user_id: UUID of the user
            include_deleted: Whether to include soft-deleted suggestions
            limit: Maximum number to return
            
        Returns:
            List of TaskSuggestionDB records
        """
        query = self.db.query(TaskSuggestionDB).filter(
            TaskSuggestionDB.user_id == str(user_id)
        )
        
        if not include_deleted:
            query = query.filter(TaskSuggestionDB.is_deleted == False)
        
        return query.order_by(
            TaskSuggestionDB.created_at.desc()
        ).limit(limit).all()
    
    async def get_suggestions_for_thought(
        self,
        thought_id: UUID
    ) -> List[TaskSuggestionDB]:
        """
        Get all suggestions generated from a specific thought.
        
        Args:
            thought_id: UUID of the source thought
            
        Returns:
            List of TaskSuggestionDB records
        """
        return self.db.query(TaskSuggestionDB).filter(
            TaskSuggestionDB.source_thought_id == str(thought_id)
        ).order_by(TaskSuggestionDB.created_at.desc()).all()
    
    async def expire_old_suggestions(
        self,
        user_id: UUID,
        days_old: int = 7
    ) -> int:
        """
        Expire suggestions older than N days without action.
        
        Args:
            user_id: UUID of the user
            days_old: How old suggestions must be to expire
            
        Returns:
            Number of suggestions expired
        """
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        result = self.db.query(TaskSuggestionDB).filter(
            TaskSuggestionDB.user_id == str(user_id),
            TaskSuggestionDB.status.in_([
                TaskSuggestionStatus.PENDING.value,
                TaskSuggestionStatus.PRESENTED.value
            ]),
            TaskSuggestionDB.is_deleted == False,
            TaskSuggestionDB.created_at < cutoff
        ).update({
            "status": TaskSuggestionStatus.EXPIRED.value,
            "updated_at": datetime.now(timezone.utc)
        })
        
        self.db.commit()
        
        return result
