"""
Task service layer for database operations.

Handles all CRUD operations for tasks including creation, retrieval,
updating, completion tracking, and relationship with source thoughts.
"""

import logging
from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from ..models.task import TaskDB
from ..models.enums import TaskStatus, Priority
from ..models.base import utc_now
from .exceptions import (
    NotFoundError,
    InvalidDataError,
    DatabaseError,
    UnauthorizedError
)


logger = logging.getLogger(__name__)


class TaskService:
    """
    Service for task-related database operations.
    
    Provides methods for creating, reading, updating, deleting, and
    completing tasks. All operations verify user ownership.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize task service with database session.
        
        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session
    
    def create_task(
        self,
        user_id: UUID,
        title: str,
        description: Optional[str] = None,
        source_thought_id: Optional[UUID] = None,
        priority: Priority = Priority.MEDIUM,
        due_date: Optional[date] = None,
        estimated_effort_minutes: Optional[int] = None
    ) -> TaskDB:
        """
        Create a new task.
        
        Args:
            user_id: UUID of the user creating the task
            title: Short task description
            description: Detailed task description
            source_thought_id: Optional thought that spawned this task
            priority: Task urgency level
            due_date: Optional deadline
            estimated_effort_minutes: Optional time estimate
            
        Returns:
            TaskDB: Created task with id and timestamps
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            task = TaskDB(
                id=str(uuid4()),
                user_id=str(user_id),
                source_thought_id=str(source_thought_id) if source_thought_id else None,
                title=title.strip(),
                description=description.strip() if description else None,
                priority=priority.value,
                status=TaskStatus.PENDING.value,
                due_date=due_date,
                estimated_effort_minutes=estimated_effort_minutes,
                created_at=utc_now(),
                updated_at=utc_now()
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"Created task {task.id} for user {user_id}")
            return task
            
        except IntegrityError as e:
            self.db.rollback()
            # Foreign key constraint failed - likely invalid source_thought_id
            if "FOREIGN KEY constraint failed" in str(e):
                logger.warning(f"Invalid source_thought_id for task: {e}")
                raise NotFoundError("Thought", str(source_thought_id))
            # Re-raise as DatabaseError for other integrity issues
            logger.error(f"Integrity error creating task: {e}")
            raise DatabaseError(
                "Failed to create task due to database constraint violation",
                original_error=e
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating task: {e}")
            raise DatabaseError(
                "Failed to create task due to database error",
                original_error=e
            )
    
    def get_task(self, task_id: UUID, user_id: UUID) -> TaskDB:
        """
        Retrieve a single task by ID with ownership verification.
        
        Args:
            task_id: UUID of the task to retrieve
            user_id: UUID of the requesting user
            
        Returns:
            TaskDB: The requested task
            
        Raises:
            NotFoundError: If task doesn't exist or user doesn't own it
        """
        try:
            task = self.db.query(TaskDB).filter(
                and_(
                    TaskDB.id == str(task_id),
                    TaskDB.user_id == str(user_id)
                )
            ).first()
            
            if not task:
                raise NotFoundError("Task", str(task_id))
            
            return task
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving task: {e}")
            raise DatabaseError(
                "Failed to retrieve task due to database error",
                original_error=e
            )
    
    def list_tasks(
        self,
        user_id: UUID,
        status: Optional[TaskStatus] = None,
        priority: Optional[Priority] = None,
        due_date_from: Optional[date] = None,
        due_date_to: Optional[date] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[TaskDB], int]:
        """
        List user's tasks with optional filtering and pagination.
        
        Args:
            user_id: UUID of the user
            status: Optional status filter
            priority: Optional priority filter
            due_date_from: Optional start date filter
            due_date_to: Optional end date filter
            limit: Maximum results to return
            offset: Pagination offset
            sort_by: Column to sort by
            sort_order: Sort direction (asc, desc)
            
        Returns:
            Tuple of (list of tasks, total count)
            
        Raises:
            InvalidDataError: If sort_by field is invalid
            DatabaseError: If database operation fails
        """
        try:
            # Build base query with user filter
            query = self.db.query(TaskDB).filter(
                TaskDB.user_id == str(user_id)
            )
            
            # Apply filters
            if status:
                query = query.filter(TaskDB.status == status.value)
            
            if priority:
                query = query.filter(TaskDB.priority == priority.value)
            
            if due_date_from:
                query = query.filter(TaskDB.due_date >= due_date_from)
            
            if due_date_to:
                query = query.filter(TaskDB.due_date <= due_date_to)
            
            # Get total count before pagination
            total = query.count()
            
            # Apply sorting
            if not hasattr(TaskDB, sort_by):
                raise InvalidDataError(
                    f"Invalid sort field: {sort_by}",
                    details={
                        "valid_fields": [
                            "created_at", "updated_at", "due_date", "priority"
                        ]
                    }
                )
            
            sort_column = getattr(TaskDB, sort_by)
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
            logger.error(f"Database error listing tasks: {e}")
            raise DatabaseError(
                "Failed to list tasks due to database error",
                original_error=e
            )
    
    def update_task(
        self,
        task_id: UUID,
        user_id: UUID,
        **kwargs
    ) -> TaskDB:
        """
        Update an existing task.
        
        Only updates provided fields. Automatically sets updated_at.
        Validates ownership before updating.
        
        Args:
            task_id: UUID of the task to update
            user_id: UUID of the requesting user
            **kwargs: Fields to update
            
        Returns:
            TaskDB: Updated task
            
        Raises:
            NotFoundError: If task doesn't exist or user doesn't own it
            InvalidDataError: If update values are invalid
            DatabaseError: If database operation fails
        """
        try:
            # Get existing task with ownership check
            task = self.get_task(task_id, user_id)
            
            # Update provided fields
            for key, value in kwargs.items():
                if hasattr(task, key) and value is not None:
                    # Convert enums to values if needed
                    if key == "status" and isinstance(value, TaskStatus):
                        value = value.value
                    elif key == "priority" and isinstance(value, Priority):
                        value = value.value
                    setattr(task, key, value)
            
            # Always update timestamp
            task.updated_at = utc_now()
            
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"Updated task {task_id} for user {user_id}")
            return task
            
        except NotFoundError:
            raise  # Re-raise not found error
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating task: {e}")
            raise DatabaseError(
                "Failed to update task due to database error",
                original_error=e
            )
    
    def delete_task(self, task_id: UUID, user_id: UUID) -> bool:
        """
        Delete a task (hard delete).
        
        Args:
            task_id: UUID of the task to delete
            user_id: UUID of the requesting user
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            UnauthorizedError: If user doesn't own the task
            DatabaseError: If database operation fails
        """
        try:
            task = self.db.query(TaskDB).filter(
                TaskDB.id == str(task_id)
            ).first()
            
            if not task:
                return False
            
            # Verify ownership
            if task.user_id != str(user_id):
                raise UnauthorizedError("Task", str(user_id))
            
            self.db.delete(task)
            self.db.commit()
            
            logger.info(f"Deleted task {task_id} for user {user_id}")
            return True
            
        except UnauthorizedError:
            raise  # Re-raise authorization error
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting task: {e}")
            raise DatabaseError(
                "Failed to delete task due to database error",
                original_error=e
            )
    
    def complete_task(self, task_id: UUID, user_id: UUID) -> TaskDB:
        """
        Mark a task as complete.
        
        Sets status to DONE and records completion timestamp.
        
        Args:
            task_id: UUID of the task to complete
            user_id: UUID of the requesting user
            
        Returns:
            TaskDB: Completed task
            
        Raises:
            NotFoundError: If task doesn't exist or user doesn't own it
            DatabaseError: If database operation fails
        """
        try:
            task = self.get_task(task_id, user_id)
            
            # Update status and completion time
            task.status = TaskStatus.DONE.value
            task.completed_at = utc_now()
            task.updated_at = utc_now()
            
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"Completed task {task_id} for user {user_id}")
            return task
            
        except NotFoundError:
            raise  # Re-raise not found error
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error completing task: {e}")
            raise DatabaseError(
                "Failed to complete task due to database error",
                original_error=e
            )
    
    def get_tasks_for_thought(
        self,
        thought_id: UUID,
        user_id: UUID
    ) -> List[TaskDB]:
        """
        Get all tasks created from a specific thought.
        
        Args:
            thought_id: UUID of the source thought
            user_id: UUID of the requesting user
            
        Returns:
            List[TaskDB]: Tasks created from the thought
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            tasks = self.db.query(TaskDB).filter(
                and_(
                    TaskDB.source_thought_id == str(thought_id),
                    TaskDB.user_id == str(user_id)
                )
            ).all()
            
            return tasks
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting tasks for thought: {e}")
            raise DatabaseError(
                "Failed to get tasks for thought due to database error",
                original_error=e
            )
