"""
Integration tests for TaskService.

Tests the service layer with a real in-memory SQLite database to verify
all CRUD operations, filtering, completion tracking, and error handling.
"""

import pytest
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4

from src.services import TaskService, NotFoundError, UnauthorizedError
from src.models.task import TaskDB
from src.models.thought import ThoughtDB
from src.models.enums import TaskStatus, Priority, ThoughtStatus


@pytest.mark.integration
class TestTaskServiceIntegration:
    """Integration tests for TaskService using real database."""
    
    def test_create_task_success(self, db_session, sample_user):
        """Test creating a task with all fields."""
        service = TaskService(db_session)
        
        task = service.create_task(
            user_id=sample_user.id,
            title="Test task",
            description="Detailed description",
            priority=Priority.HIGH,
            due_date=date.today() + timedelta(days=7),
            estimated_effort_minutes=120
        )
        
        assert task.id is not None
        assert task.user_id == str(sample_user.id)
        assert task.title == "Test task"
        assert task.description == "Detailed description"
        assert task.priority == Priority.HIGH.value
        assert task.status == TaskStatus.PENDING.value
        assert task.due_date == date.today() + timedelta(days=7)
        assert task.estimated_effort_minutes == 120
        assert task.completed_at is None
    
    def test_create_task_minimal(self, db_session, sample_user):
        """Test creating a task with only required fields."""
        service = TaskService(db_session)
        
        task = service.create_task(
            user_id=sample_user.id,
            title="Minimal task"
        )
        
        assert task.id is not None
        assert task.title == "Minimal task"
        assert task.description is None
        assert task.priority == Priority.MEDIUM.value  # Default
        assert task.status == TaskStatus.PENDING.value
    
    def test_create_task_from_thought(
        self,
        db_session,
        sample_user,
        sample_thought
    ):
        """Test creating a task linked to a thought."""
        service = TaskService(db_session)
        
        task = service.create_task(
            user_id=sample_user.id,
            title="Task from thought",
            source_thought_id=sample_thought.id
        )
        
        assert task.source_thought_id == str(sample_thought.id)
    
    def test_get_task_success(self, db_session, sample_user, sample_task):
        """Test retrieving an existing task."""
        service = TaskService(db_session)
        
        task = service.get_task(
            task_id=sample_task.id,
            user_id=sample_user.id
        )
        
        assert task.id == sample_task.id
        assert task.title == sample_task.title
    
    def test_get_task_not_found(self, db_session, sample_user):
        """Test retrieving a non-existent task raises NotFoundError."""
        service = TaskService(db_session)
        
        with pytest.raises(NotFoundError) as exc_info:
            service.get_task(
                task_id=uuid4(),
                user_id=sample_user.id
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_get_task_wrong_user(self, db_session, sample_user, sample_task):
        """Test retrieving another user's task raises NotFoundError."""
        service = TaskService(db_session)
        
        other_user_id = uuid4()
        
        with pytest.raises(NotFoundError):
            service.get_task(
                task_id=sample_task.id,
                user_id=other_user_id
            )
    
    def test_list_tasks_basic(self, db_session, sample_user):
        """Test listing tasks with pagination."""
        service = TaskService(db_session)
        
        # Create multiple tasks
        for i in range(5):
            service.create_task(
                user_id=sample_user.id,
                title=f"Task {i}"
            )
        
        tasks, total = service.list_tasks(
            user_id=sample_user.id,
            limit=3,
            offset=0
        )
        
        assert len(tasks) == 3
        assert total == 5
    
    def test_list_tasks_filter_by_status(self, db_session, sample_user):
        """Test filtering tasks by status."""
        service = TaskService(db_session)
        
        # Create pending and done tasks
        pending = service.create_task(
            user_id=sample_user.id,
            title="Pending task"
        )
        
        done = service.create_task(
            user_id=sample_user.id,
            title="Done task"
        )
        service.complete_task(
            task_id=done.id,
            user_id=sample_user.id
        )
        
        # List only pending
        tasks, total = service.list_tasks(
            user_id=sample_user.id,
            status=TaskStatus.PENDING
        )
        
        assert total == 1
        assert tasks[0].id == pending.id
    
    def test_list_tasks_filter_by_priority(self, db_session, sample_user):
        """Test filtering tasks by priority."""
        service = TaskService(db_session)
        
        # Create tasks with different priorities
        service.create_task(
            user_id=sample_user.id,
            title="High priority",
            priority=Priority.HIGH
        )
        service.create_task(
            user_id=sample_user.id,
            title="Low priority",
            priority=Priority.LOW
        )
        
        # Filter by high priority
        tasks, total = service.list_tasks(
            user_id=sample_user.id,
            priority=Priority.HIGH
        )
        
        assert total == 1
        assert tasks[0].priority == Priority.HIGH.value
    
    def test_list_tasks_filter_by_due_date(self, db_session, sample_user):
        """Test filtering tasks by due date range."""
        service = TaskService(db_session)
        
        today = date.today()
        
        # Create tasks with different due dates
        service.create_task(
            user_id=sample_user.id,
            title="Due soon",
            due_date=today + timedelta(days=3)
        )
        service.create_task(
            user_id=sample_user.id,
            title="Due later",
            due_date=today + timedelta(days=30)
        )
        
        # Filter by date range (next week)
        tasks, total = service.list_tasks(
            user_id=sample_user.id,
            due_date_from=today,
            due_date_to=today + timedelta(days=7)
        )
        
        assert total == 1
        assert tasks[0].title == "Due soon"
    
    def test_update_task_success(self, db_session, sample_user, sample_task):
        """Test updating a task's fields."""
        service = TaskService(db_session)
        
        # Save original timestamp before update
        original_time = sample_task.updated_at
        
        updated = service.update_task(
            task_id=sample_task.id,
            user_id=sample_user.id,
            title="Updated title",
            priority=Priority.CRITICAL,
            status=TaskStatus.IN_PROGRESS
        )
        
        assert updated.title == "Updated title"
        assert updated.priority == Priority.CRITICAL.value
        assert updated.status == TaskStatus.IN_PROGRESS.value
        # Use >= to handle microsecond precision (update can be very fast)
        assert updated.updated_at >= original_time
        assert updated.id == sample_task.id
        assert updated.user_id == sample_user.id
    
    def test_update_task_partial(self, db_session, sample_user, sample_task):
        """Test partial update only changes specified fields."""
        service = TaskService(db_session)
        
        original_priority = sample_task.priority
        
        updated = service.update_task(
            task_id=sample_task.id,
            user_id=sample_user.id,
            title="New title"
        )
        
        assert updated.title == "New title"
        assert updated.priority == original_priority  # Unchanged
    
    def test_update_task_not_found(self, db_session, sample_user):
        """Test updating a non-existent task raises NotFoundError."""
        service = TaskService(db_session)
        
        with pytest.raises(NotFoundError):
            service.update_task(
                task_id=uuid4(),
                user_id=sample_user.id,
                title="New title"
            )
    
    def test_delete_task_success(self, db_session, sample_user, sample_task):
        """Test deleting a task."""
        service = TaskService(db_session)
        
        result = service.delete_task(
            task_id=sample_task.id,
            user_id=sample_user.id
        )
        
        assert result is True
        
        # Verify task is gone
        with pytest.raises(NotFoundError):
            service.get_task(
                task_id=sample_task.id,
                user_id=sample_user.id
            )
    
    def test_delete_task_not_found(self, db_session, sample_user):
        """Test deleting a non-existent task returns False."""
        service = TaskService(db_session)
        
        result = service.delete_task(
            task_id=uuid4(),
            user_id=sample_user.id
        )
        
        assert result is False
    
    def test_delete_task_wrong_user(self, db_session, sample_user, sample_task):
        """Test deleting another user's task raises UnauthorizedError."""
        service = TaskService(db_session)
        
        other_user_id = uuid4()
        
        with pytest.raises(UnauthorizedError):
            service.delete_task(
                task_id=sample_task.id,
                user_id=other_user_id
            )
    
    def test_complete_task_success(self, db_session, sample_user, sample_task):
        """Test marking a task as complete."""
        service = TaskService(db_session)
        
        # Capture time before completion
        before_completion = datetime.now(timezone.utc)
        
        completed = service.complete_task(
            task_id=sample_task.id,
            user_id=sample_user.id
        )
        
        assert completed.status == TaskStatus.DONE.value
        assert completed.completed_at is not None
        # Ensure completed_at is reasonable (within last few seconds)
        # Handle both naive and aware datetimes
        if completed.completed_at.tzinfo is None:
            # If naive, make it aware for comparison
            completed_at_aware = completed.completed_at.replace(tzinfo=timezone.utc)
        else:
            completed_at_aware = completed.completed_at
        
        assert completed_at_aware <= datetime.now(timezone.utc)
        assert completed_at_aware >= before_completion
    
    def test_complete_task_not_found(self, db_session, sample_user):
        """Test completing a non-existent task raises NotFoundError."""
        service = TaskService(db_session)
        
        with pytest.raises(NotFoundError):
            service.complete_task(
                task_id=uuid4(),
                user_id=sample_user.id
            )
    
    def test_get_tasks_for_thought(
        self,
        db_session,
        sample_user,
        sample_thought
    ):
        """Test retrieving all tasks for a thought."""
        service = TaskService(db_session)
        
        # Create tasks from same thought
        task1 = service.create_task(
            user_id=sample_user.id,
            title="Task 1",
            source_thought_id=sample_thought.id
        )
        task2 = service.create_task(
            user_id=sample_user.id,
            title="Task 2",
            source_thought_id=sample_thought.id
        )
        
        # Create task from different thought
        service.create_task(
            user_id=sample_user.id,
            title="Unrelated task"
        )
        
        tasks = service.get_tasks_for_thought(
            thought_id=sample_thought.id,
            user_id=sample_user.id
        )
        
        assert len(tasks) == 2
        task_ids = [t.id for t in tasks]
        assert task1.id in task_ids
        assert task2.id in task_ids


# Additional fixtures
@pytest.fixture
def sample_task(db_session, sample_user):
    """Create a sample task for testing."""
    task = TaskDB(
        id=str(uuid4()),
        user_id=str(sample_user.id),
        title="Sample task for testing",
        description="Test description",
        priority=Priority.MEDIUM.value,
        status=TaskStatus.PENDING.value,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def sample_thought(db_session, sample_user):
    """Create a sample thought for testing."""
    thought = ThoughtDB(
        id=str(uuid4()),
        user_id=str(sample_user.id),
        content="Sample thought for testing",
        tags=["sample"],
        status=ThoughtStatus.ACTIVE.value,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(thought)
    db_session.commit()
    db_session.refresh(thought)
    return thought
