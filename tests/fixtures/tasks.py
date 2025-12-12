"""
Task fixtures for testing.

Provides factories and fixtures for creating test tasks with various
priorities, statuses, and configurations.
"""

from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.models.base import utc_now
from src.models.enums import TaskStatus, Priority


class TaskFactory:
    """
    Factory for creating test task objects.
    
    Provides flexible task creation with sensible defaults that can be
    overridden for specific test scenarios.
    """
    
    @staticmethod
    def create_dict(
        title: str = "Test Task",
        description: str = "A test task for testing",
        priority: Priority = Priority.MEDIUM,
        status: TaskStatus = TaskStatus.PENDING,
        user_id: Optional[str] = None,
        source_thought_id: Optional[str] = None,
        due_date: Optional[date] = None,
        estimated_effort_minutes: Optional[int] = None,
        **kwargs
    ) -> dict:
        """
        Create task data dictionary for testing.
        
        Args:
            title: Task title (short description)
            description: Detailed task description
            priority: Task priority level
            status: Task lifecycle status
            user_id: User ID (auto-generated if None)
            source_thought_id: Source thought ID if task derived from thought
            due_date: Optional deadline date
            estimated_effort_minutes: Optional time estimate
            **kwargs: Additional fields to override
            
        Returns:
            dict: Task data ready for database insertion or API request
            
        Example:
            >>> task_data = TaskFactory.create_dict(
            ...     title="Implement feature X",
            ...     priority=Priority.HIGH
            ... )
            >>> assert task_data["priority"] == "high"
        """
        if user_id is None:
            user_id = str(uuid4())
        
        task_data = {
            "id": str(uuid4()),
            "user_id": user_id,
            "source_thought_id": source_thought_id,
            "title": title,
            "description": description,
            "priority": priority.value if isinstance(priority, Priority) else priority,
            "status": status.value if isinstance(status, TaskStatus) else status,
            "due_date": due_date,
            "estimated_effort_minutes": estimated_effort_minutes,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "completed_at": None
        }
        
        # Override with any additional fields
        task_data.update(kwargs)
        
        return task_data
    
    @staticmethod
    def create_api_dict(
        title: str = "Test Task",
        description: str = "A test task for testing",
        priority: Priority = Priority.MEDIUM,
        source_thought_id: Optional[str] = None,
        due_date: Optional[date] = None,
        estimated_effort_minutes: Optional[int] = None
    ) -> dict:
        """
        Create task data for API requests (no id, timestamps, user_id).
        
        Args:
            title: Task title
            description: Task description
            priority: Task priority
            source_thought_id: Source thought ID
            due_date: Optional deadline
            estimated_effort_minutes: Optional time estimate
            
        Returns:
            dict: Task data for API POST/PUT requests
            
        Example:
            >>> api_data = TaskFactory.create_api_dict(
            ...     title="API test task"
            ... )
            >>> assert "id" not in api_data
            >>> assert "created_at" not in api_data
        """
        data = {
            "title": title,
            "description": description,
            "priority": priority.value if isinstance(priority, Priority) else priority
        }
        
        if source_thought_id:
            data["source_thought_id"] = source_thought_id
        if due_date:
            data["due_date"] = due_date.isoformat()
        if estimated_effort_minutes:
            data["estimated_effort_minutes"] = estimated_effort_minutes
        
        return data
    
    @staticmethod
    def create_batch(
        count: int,
        user_id: Optional[str] = None,
        **kwargs
    ) -> List[dict]:
        """
        Create multiple task data dictionaries.
        
        Args:
            count: Number of tasks to create
            user_id: User ID for all tasks
            **kwargs: Common fields for all tasks
            
        Returns:
            list[dict]: List of task data dictionaries
            
        Example:
            >>> tasks = TaskFactory.create_batch(
            ...     3,
            ...     priority=Priority.HIGH
            ... )
            >>> assert len(tasks) == 3
            >>> assert all(t["priority"] == "high" for t in tasks)
        """
        return [
            TaskFactory.create_dict(
                title=f"Test task #{i+1}",
                user_id=user_id,
                **kwargs
            )
            for i in range(count)
        ]
    
    @staticmethod
    def create_with_due_date(
        days_from_now: int,
        user_id: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Create task with due date relative to today.
        
        Args:
            days_from_now: Days to add to current date (negative for past)
            user_id: User ID
            **kwargs: Additional fields
            
        Returns:
            dict: Task data with calculated due date
            
        Example:
            >>> task = TaskFactory.create_with_due_date(7)  # Due in 1 week
            >>> task = TaskFactory.create_with_due_date(-3)  # Overdue by 3 days
        """
        due_date = date.today() + timedelta(days=days_from_now)
        return TaskFactory.create_dict(
            user_id=user_id,
            due_date=due_date,
            **kwargs
        )
    
    @staticmethod
    def create_completed(
        user_id: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Create a completed task with completion timestamp.
        
        Args:
            user_id: User ID
            **kwargs: Additional fields
            
        Returns:
            dict: Task data with status=done and completed_at set
        """
        return TaskFactory.create_dict(
            status=TaskStatus.DONE,
            completed_at=utc_now(),
            user_id=user_id,
            **kwargs
        )


@pytest.fixture
def task_factory() -> TaskFactory:
    """
    Provide TaskFactory instance for tests.
    
    Returns:
        TaskFactory: Factory for creating test tasks
        
    Example:
        >>> def test_task_creation(task_factory):
        ...     task_data = task_factory.create_dict(
        ...         title="Custom task"
        ...     )
        ...     assert task_data["title"] == "Custom task"
    """
    return TaskFactory()


@pytest.fixture
def sample_task(db_session: Session, sample_user: dict) -> dict:
    """
    Create a test task in the database.
    
    Creates a default test task linked to sample_user that can be
    used across tests.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        dict: Created task data with database ID
        
    Example:
        >>> def test_with_task(sample_task):
        ...     assert sample_task["title"]
        ...     assert sample_task["status"] == "pending"
    """
    from src.models.task import TaskDB
    
    task_data = TaskFactory.create_dict(
        user_id=sample_user["id"]
    )
    task = TaskDB(**task_data)
    
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "due_date": task.due_date,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }


@pytest.fixture
def task_from_thought(
    db_session: Session,
    sample_user: dict,
    sample_thought: dict
) -> dict:
    """
    Create a task derived from a thought.
    
    Links a test task to a sample thought to test the thought->task flow.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        sample_thought: Sample thought fixture
        
    Returns:
        dict: Created task data linked to thought
    """
    from src.models.task import TaskDB
    
    task_data = TaskFactory.create_dict(
        title="Task from thought",
        description="A task created from a thought",
        user_id=sample_user["id"],
        source_thought_id=sample_thought["id"]
    )
    task = TaskDB(**task_data)
    
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    
    return {
        "id": task.id,
        "source_thought_id": task.source_thought_id,
        "title": task.title
    }


@pytest.fixture
def high_priority_task(db_session: Session, sample_user: dict) -> dict:
    """
    Create a high-priority test task.
    
    Useful for testing priority filtering and sorting.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        dict: Created high-priority task data
    """
    from src.models.task import TaskDB
    
    task_data = TaskFactory.create_dict(
        title="High priority task",
        priority=Priority.HIGH,
        user_id=sample_user["id"]
    )
    task = TaskDB(**task_data)
    
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    
    return {
        "id": task.id,
        "title": task.title,
        "priority": task.priority
    }


@pytest.fixture
def completed_task(db_session: Session, sample_user: dict) -> dict:
    """
    Create a completed test task.
    
    Useful for testing status filtering and task lifecycle.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        dict: Created completed task data
    """
    from src.models.task import TaskDB
    
    task_data = TaskFactory.create_completed(
        title="Completed task",
        user_id=sample_user["id"]
    )
    task = TaskDB(**task_data)
    
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "completed_at": task.completed_at
    }


@pytest.fixture
def multiple_tasks(db_session: Session, sample_user: dict) -> List[dict]:
    """
    Create multiple test tasks with varying priorities.
    
    Creates 4 tasks with different priorities for testing
    list/filter/sort operations.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        list[dict]: List of created task data
    """
    from src.models.task import TaskDB
    
    tasks_data = [
        TaskFactory.create_dict(
            title="Low priority task",
            priority=Priority.LOW,
            user_id=sample_user["id"]
        ),
        TaskFactory.create_dict(
            title="Medium priority task",
            priority=Priority.MEDIUM,
            user_id=sample_user["id"]
        ),
        TaskFactory.create_dict(
            title="High priority task",
            priority=Priority.HIGH,
            user_id=sample_user["id"]
        ),
        TaskFactory.create_dict(
            title="Critical priority task",
            priority=Priority.CRITICAL,
            user_id=sample_user["id"]
        ),
    ]
    
    created_tasks = []
    for task_data in tasks_data:
        task = TaskDB(**task_data)
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        created_tasks.append({
            "id": task.id,
            "title": task.title,
            "priority": task.priority,
            "status": task.status
        })
    
    return created_tasks
