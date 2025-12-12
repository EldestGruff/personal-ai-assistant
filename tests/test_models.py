"""
Comprehensive model validation tests for Personal AI Assistant.

Tests Pydantic model validation, edge cases, serialization, and
enum behavior. Ensures all data constraints are properly enforced.
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID

from pydantic import ValidationError

from src.models.thought import ThoughtCreate, ThoughtUpdate, ThoughtResponse
from src.models.task import TaskCreate, TaskUpdate, TaskResponse
from src.models.enums import (
    ThoughtStatus,
    TaskStatus,
    Priority,
    TimeOfDay,
    EnergyLevel,
    FocusState
)


# ============================================================================
# Thought Model Tests
# ============================================================================

class TestThoughtCreate:
    """Test ThoughtCreate model validation."""
    
    def test_create_with_valid_minimal_input(self):
        """Valid minimal input creates model without error."""
        thought = ThoughtCreate(content="Test thought")
        assert thought.content == "Test thought"
        assert thought.tags == []  # Default to empty list
        assert thought.context is None  # Default to None
    
    def test_create_with_valid_full_input(self):
        """Valid complete input creates model with all fields."""
        thought = ThoughtCreate(
            content="Complete test thought",
            tags=["test", "complete"],
            context={"active_app": "VSCode", "time_of_day": "afternoon"}
        )
        assert thought.content == "Complete test thought"
        assert thought.tags == ["test", "complete"]
        assert thought.context["active_app"] == "VSCode"
    
    def test_create_empty_content_raises_error(self):
        """Empty content raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ThoughtCreate(content="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_create_whitespace_only_content_raises_error(self):
        """Whitespace-only content raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ThoughtCreate(content="   \n  \t  ")
        assert "Content cannot be empty" in str(exc_info.value)
    
    def test_create_content_too_long_raises_error(self):
        """Content exceeding 5000 chars raises ValidationError."""
        long_content = "a" * 5001
        with pytest.raises(ValidationError) as exc_info:
            ThoughtCreate(content=long_content)
        assert "5000 characters" in str(exc_info.value)
    
    def test_create_content_exactly_5000_chars_succeeds(self):
        """Content with exactly 5000 chars is valid."""
        content = "a" * 5000
        thought = ThoughtCreate(content=content)
        assert len(thought.content) == 5000
    
    def test_create_too_many_tags_raises_error(self):
        """More than 5 tags raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ThoughtCreate(
                content="Test",
                tags=["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"]
            )
        assert "at most 5 items" in str(exc_info.value)
    
    def test_create_exactly_5_tags_succeeds(self):
        """Exactly 5 tags is valid."""
        thought = ThoughtCreate(
            content="Test",
            tags=["tag1", "tag2", "tag3", "tag4", "tag5"]
        )
        assert len(thought.tags) == 5
    
    def test_create_tag_too_long_raises_error(self):
        """Tag exceeding 50 chars raises ValidationError."""
        long_tag = "a" * 51
        with pytest.raises(ValidationError) as exc_info:
            ThoughtCreate(content="Test", tags=[long_tag])
        assert "50 character limit" in str(exc_info.value)
    
    def test_create_tag_invalid_characters_raises_error(self):
        """Tag with invalid characters raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ThoughtCreate(content="Test", tags=["invalid@tag"])
        assert "invalid characters" in str(exc_info.value)
    
    def test_create_tags_normalized_to_lowercase(self):
        """Tags are automatically converted to lowercase."""
        thought = ThoughtCreate(content="Test", tags=["Test", "TAG"])
        assert thought.tags == ["test", "tag"]
    
    def test_create_duplicate_tags_raises_error(self):
        """Duplicate tags raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ThoughtCreate(content="Test", tags=["test", "test"])
        assert "Duplicate tags" in str(exc_info.value)
    
    def test_create_empty_tags_removed(self):
        """Empty tags are filtered out."""
        thought = ThoughtCreate(content="Test", tags=["valid", "", "  "])
        assert thought.tags == ["valid"]
    
    def test_create_with_unicode_content(self):
        """Unicode content is handled correctly."""
        thought = ThoughtCreate(content="Test émojis 🎉 and 日本語")
        assert "émojis" in thought.content
        assert "🎉" in thought.content
        assert "日本語" in thought.content


class TestThoughtUpdate:
    """Test ThoughtUpdate model validation."""
    
    def test_update_with_all_fields_optional(self):
        """All fields are optional for updates."""
        update = ThoughtUpdate()
        assert update.content is None
        assert update.tags is None
        assert update.status is None
    
    def test_update_partial_fields(self):
        """Can update subset of fields."""
        update = ThoughtUpdate(content="Updated content")
        assert update.content == "Updated content"
        assert update.tags is None
    
    def test_update_content_validation_same_as_create(self):
        """Content validation rules same as create."""
        with pytest.raises(ValidationError):
            ThoughtUpdate(content="")
        
        with pytest.raises(ValidationError):
            ThoughtUpdate(content="a" * 5001)
    
    def test_update_tags_validation_same_as_create(self):
        """Tag validation rules same as create."""
        with pytest.raises(ValidationError):
            ThoughtUpdate(tags=["a", "b", "c", "d", "e", "f"])  # Too many
    
    def test_update_invalid_status_raises_error(self):
        """Invalid status value raises ValidationError."""
        with pytest.raises(ValidationError):
            ThoughtUpdate(status="invalid_status")


class TestThoughtResponse:
    """Test ThoughtResponse model serialization."""
    
    def test_response_has_all_required_fields(self, sample_thought_data):
        """Response includes all required fields."""
        from uuid import uuid4
        from src.models.base import utc_now
        
        response = ThoughtResponse(
            id=uuid4(),
            user_id=uuid4(),
            content="Test thought",
            tags=["test"],
            status=ThoughtStatus.ACTIVE,
            context={},
            created_at=utc_now(),
            updated_at=utc_now(),
            claude_summary=None,
            claude_analysis=None
        )
        
        assert response.id
        assert response.user_id
        assert response.content
        assert response.created_at
        assert response.updated_at
    
    def test_response_serializes_to_json(self):
        """Response model serializes to JSON."""
        from uuid import uuid4
        from src.models.base import utc_now
        
        response = ThoughtResponse(
            id=uuid4(),
            user_id=uuid4(),
            content="Test",
            tags=[],
            status=ThoughtStatus.ACTIVE,
            context=None,
            created_at=utc_now(),
            updated_at=utc_now(),
            claude_summary=None,
            claude_analysis=None
        )
        
        data = response.model_dump(mode='json')
        assert isinstance(data["id"], str)
        assert isinstance(data["created_at"], str)  # ISO format


# ============================================================================
# Task Model Tests
# ============================================================================

class TestTaskCreate:
    """Test TaskCreate model validation."""
    
    def test_create_with_valid_minimal_input(self):
        """Valid minimal input creates model."""
        task = TaskCreate(
            title="Test task",
            description="Test description"
        )
        assert task.title == "Test task"
        assert task.priority == Priority.MEDIUM  # Default
    
    def test_create_with_valid_full_input(self):
        """Valid complete input creates model with all fields."""
        from datetime import date
        
        task = TaskCreate(
            title="Complete task",
            description="Full description",
            priority=Priority.HIGH,
            source_thought_id="123e4567-e89b-12d3-a456-426614174000",
            due_date=date.today(),
            estimated_effort_minutes=120
        )
        assert task.title == "Complete task"
        assert task.priority == Priority.HIGH
        assert task.estimated_effort_minutes == 120
    
    def test_create_empty_title_raises_error(self):
        """Empty title raises ValidationError."""
        with pytest.raises(ValidationError):
            TaskCreate(title="", description="Test")
    
    def test_create_title_too_long_raises_error(self):
        """Title exceeding 200 chars raises ValidationError."""
        long_title = "a" * 201
        with pytest.raises(ValidationError):
            TaskCreate(title=long_title, description="Test")
    
    def test_create_description_too_long_raises_error(self):
        """Description exceeding 5000 chars raises ValidationError."""
        long_desc = "a" * 5001
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", description=long_desc)
    
    def test_create_invalid_priority_raises_error(self):
        """Invalid priority value raises ValidationError."""
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", description="Test", priority="invalid")
    
    def test_create_negative_effort_raises_error(self):
        """Negative effort estimate raises ValidationError."""
        with pytest.raises(ValidationError):
            TaskCreate(
                title="Test",
                description="Test",
                estimated_effort_minutes=-10
            )
    
    def test_create_zero_effort_raises_error(self):
        """Zero effort estimate raises ValidationError."""
        with pytest.raises(ValidationError):
            TaskCreate(
                title="Test",
                description="Test",
                estimated_effort_minutes=0
            )


class TestTaskUpdate:
    """Test TaskUpdate model validation."""
    
    def test_update_all_fields_optional(self):
        """All fields are optional for updates."""
        update = TaskUpdate()
        assert update.title is None
        assert update.description is None
        assert update.priority is None
        assert update.status is None
    
    def test_update_partial_fields(self):
        """Can update subset of fields."""
        update = TaskUpdate(title="Updated title", priority=Priority.HIGH)
        assert update.title == "Updated title"
        assert update.priority == Priority.HIGH
        assert update.description is None
    
    def test_update_validation_same_as_create(self):
        """Validation rules same as create."""
        with pytest.raises(ValidationError):
            TaskUpdate(title="a" * 201)  # Too long


# ============================================================================
# Enum Tests
# ============================================================================

class TestEnums:
    """Test enum value validation and behavior."""
    
    def test_thought_status_valid_values(self):
        """ThoughtStatus has correct values."""
        assert ThoughtStatus.ACTIVE.value == "active"
        assert ThoughtStatus.ARCHIVED.value == "archived"
        assert ThoughtStatus.COMPLETED.value == "completed"
    
    def test_task_status_valid_values(self):
        """TaskStatus has correct values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.CANCELLED.value == "cancelled"
    
    def test_priority_valid_values(self):
        """Priority has correct values."""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.CRITICAL.value == "critical"
    
    def test_time_of_day_valid_values(self):
        """TimeOfDay has correct values."""
        assert TimeOfDay.MORNING.value == "morning"
        assert TimeOfDay.AFTERNOON.value == "afternoon"
        assert TimeOfDay.EVENING.value == "evening"
        assert TimeOfDay.NIGHT.value == "night"
    
    def test_energy_level_valid_values(self):
        """EnergyLevel has correct values."""
        assert EnergyLevel.LOW.value == "low"
        assert EnergyLevel.MEDIUM.value == "medium"
        assert EnergyLevel.HIGH.value == "high"
    
    def test_focus_state_valid_values(self):
        """FocusState has correct values."""
        assert FocusState.DEEP_WORK.value == "deep_work"
        assert FocusState.INTERRUPTED.value == "interrupted"
        assert FocusState.SCATTERED.value == "scattered"
    
    def test_enum_comparison(self):
        """Enums can be compared."""
        assert ThoughtStatus.ACTIVE == ThoughtStatus.ACTIVE
        assert ThoughtStatus.ACTIVE != ThoughtStatus.ARCHIVED
    
    def test_enum_string_conversion(self):
        """Enums convert to strings correctly."""
        assert str(Priority.HIGH.value) == "high"


# ============================================================================
# Timestamp and UUID Tests
# ============================================================================

class TestTimestamps:
    """Test timestamp handling and validation."""
    
    def test_utc_now_returns_aware_datetime(self):
        """utc_now() returns timezone-aware datetime."""
        from src.models.base import utc_now
        
        now = utc_now()
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc
    
    def test_naive_timestamp_raises_error(self):
        """Naive timestamp raises ValidationError."""
        from uuid import uuid4
        
        with pytest.raises(ValidationError) as exc_info:
            ThoughtResponse(
                id=uuid4(),
                user_id=uuid4(),
                content="Test",
                tags=[],
                status=ThoughtStatus.ACTIVE,
                context=None,
                created_at=datetime(2025, 1, 1),  # Naive datetime
                updated_at=datetime(2025, 1, 1),
                claude_summary=None,
                claude_analysis=None
            )
        assert "timezone-aware" in str(exc_info.value)


class TestUUIDs:
    """Test UUID generation and validation."""
    
    def test_uuid_field_accepts_uuid(self):
        """UUID fields accept UUID objects."""
        from uuid import uuid4
        from src.models.base import utc_now
        
        thought_id = uuid4()
        user_id = uuid4()
        
        response = ThoughtResponse(
            id=thought_id,
            user_id=user_id,
            content="Test",
            tags=[],
            status=ThoughtStatus.ACTIVE,
            context=None,
            created_at=utc_now(),
            updated_at=utc_now(),
            claude_summary=None,
            claude_analysis=None
        )
        
        assert response.id == thought_id
        assert response.user_id == user_id
    
    def test_uuid_field_accepts_string(self):
        """UUID fields accept valid UUID strings."""
        from uuid import uuid4
        from src.models.base import utc_now
        
        thought_id_str = str(uuid4())
        user_id_str = str(uuid4())
        
        response = ThoughtResponse(
            id=thought_id_str,
            user_id=user_id_str,
            content="Test",
            tags=[],
            status=ThoughtStatus.ACTIVE,
            context=None,
            created_at=utc_now(),
            updated_at=utc_now(),
            claude_summary=None,
            claude_analysis=None
        )
        
        assert str(response.id) == thought_id_str
    
    def test_uuid_field_rejects_invalid_string(self):
        """UUID fields reject invalid UUID strings."""
        from src.models.base import utc_now
        
        with pytest.raises(ValidationError):
            ThoughtResponse(
                id="not-a-uuid",
                user_id="also-not-a-uuid",
                content="Test",
                tags=[],
                status=ThoughtStatus.ACTIVE,
                context=None,
                created_at=utc_now(),
                updated_at=utc_now(),
                claude_summary=None,
                claude_analysis=None
            )


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_thought_with_special_characters_in_content(self):
        """Special characters in content are preserved."""
        special = "Test with @#$%^&*() and <html> and 'quotes' and \"double\""
        thought = ThoughtCreate(content=special)
        assert thought.content == special
    
    def test_thought_with_newlines_in_content(self):
        """Newlines in content are preserved."""
        content = "Line 1\nLine 2\n\nLine 4"
        thought = ThoughtCreate(content=content)
        assert thought.content == content
    
    def test_task_with_past_due_date(self):
        """Task can have past due date (for tracking overdue)."""
        from datetime import date, timedelta
        
        past_date = date.today() - timedelta(days=7)
        task = TaskCreate(
            title="Overdue task",
            description="Test",
            due_date=past_date
        )
        assert task.due_date == past_date
    
    def test_json_context_with_nested_structure(self):
        """Context can contain nested JSON structures."""
        complex_context = {
            "user": {
                "location": "home",
                "energy": "high"
            },
            "environment": {
                "apps": ["VSCode", "Chrome"],
                "tasks": 5
            }
        }
        
        thought = ThoughtCreate(
            content="Test",
            context=complex_context
        )
        assert thought.context["user"]["energy"] == "high"
        assert len(thought.context["environment"]["apps"]) == 2
