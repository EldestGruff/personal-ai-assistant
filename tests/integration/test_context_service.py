"""
Integration tests for ContextService.

Tests the service layer with a real in-memory SQLite database to verify
context session management, thought counting, and retrieval operations.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.services import ContextService, NotFoundError
from src.models.context import ContextDB
from src.models.enums import TimeOfDay, EnergyLevel, FocusState


@pytest.mark.integration
class TestContextServiceIntegration:
    """Integration tests for ContextService using real database."""
    
    def test_start_context_session_full(self, db_session, sample_user):
        """Test starting a context session with all fields."""
        service = ContextService(db_session)
        
        session_id = f"session_{uuid4()}"
        context = service.start_context_session(
            user_id=sample_user.id,
            session_id=session_id,
            current_activity="Email review",
            active_app="Mail.app",
            location="Home office",
            time_of_day=TimeOfDay.AFTERNOON,
            energy_level=EnergyLevel.MEDIUM,
            focus_state=FocusState.INTERRUPTED,
            notes="Trying to clean inbox"
        )
        
        assert context.id == session_id
        assert context.user_id == str(sample_user.id)
        assert context.current_activity == "Email review"
        assert context.active_app == "Mail.app"
        assert context.location == "Home office"
        assert context.time_of_day == TimeOfDay.AFTERNOON.value
        assert context.energy_level == EnergyLevel.MEDIUM.value
        assert context.focus_state == FocusState.INTERRUPTED.value
        assert context.notes == "Trying to clean inbox"
        assert context.thought_count == 0
        assert context.started_at is not None
        assert context.ended_at is None
    
    def test_start_context_session_minimal(self, db_session, sample_user):
        """Test starting a context session with minimal fields."""
        service = ContextService(db_session)
        
        session_id = f"session_{uuid4()}"
        context = service.start_context_session(
            user_id=sample_user.id,
            session_id=session_id
        )
        
        assert context.id == session_id
        assert context.current_activity is None
        assert context.thought_count == 0
        assert context.ended_at is None
    
    def test_end_context_session_success(
        self,
        db_session,
        sample_user,
        sample_context
    ):
        """Test ending a context session."""
        service = ContextService(db_session)
        
        ended = service.end_context_session(
            session_id=sample_context.id,
            user_id=sample_user.id
        )
        
        assert ended.ended_at is not None
        assert ended.ended_at >= sample_context.started_at
    
    def test_end_context_session_not_found(self, db_session, sample_user):
        """Test ending a non-existent session raises NotFoundError."""
        service = ContextService(db_session)
        
        with pytest.raises(NotFoundError):
            service.end_context_session(
                session_id="nonexistent",
                user_id=sample_user.id
            )
    
    def test_end_context_session_idempotent(
        self,
        db_session,
        sample_user,
        sample_context
    ):
        """Test ending a session twice doesn't change end time."""
        service = ContextService(db_session)
        
        # End once
        first_end = service.end_context_session(
            session_id=sample_context.id,
            user_id=sample_user.id
        )
        first_end_time = first_end.ended_at
        
        # End again
        second_end = service.end_context_session(
            session_id=sample_context.id,
            user_id=sample_user.id
        )
        
        # End time should be the same
        assert second_end.ended_at == first_end_time
    
    def test_get_current_context_exists(self, db_session, sample_user):
        """Test getting active context when one exists."""
        service = ContextService(db_session)
        
        # Start a session
        session_id = f"session_{uuid4()}"
        started = service.start_context_session(
            user_id=sample_user.id,
            session_id=session_id,
            current_activity="Coding"
        )
        
        # Get current
        current = service.get_current_context(user_id=sample_user.id)
        
        assert current is not None
        assert current.id == started.id
        assert current.ended_at is None
    
    def test_get_current_context_none(self, db_session, sample_user):
        """Test getting current context when none active."""
        service = ContextService(db_session)
        
        current = service.get_current_context(user_id=sample_user.id)
        
        assert current is None
    
    def test_get_current_context_ignores_ended(
        self,
        db_session,
        sample_user,
        sample_context
    ):
        """Test that ended contexts are not returned as current."""
        service = ContextService(db_session)
        
        # End the context
        service.end_context_session(
            session_id=sample_context.id,
            user_id=sample_user.id
        )
        
        # Should return None now
        current = service.get_current_context(user_id=sample_user.id)
        
        assert current is None
    
    def test_get_context_history(self, db_session, sample_user):
        """Test retrieving context history with pagination."""
        service = ContextService(db_session)
        
        # Create multiple sessions
        for i in range(5):
            session_id = f"session_{i}"
            service.start_context_session(
                user_id=sample_user.id,
                session_id=session_id,
                current_activity=f"Activity {i}"
            )
        
        contexts, total = service.get_context_history(
            user_id=sample_user.id,
            limit=3,
            offset=0
        )
        
        assert len(contexts) == 3
        assert total == 5
    
    def test_get_context_history_sorted(self, db_session, sample_user):
        """Test context history is sorted by started_at descending."""
        service = ContextService(db_session)
        
        # Create sessions
        first_id = f"first_{uuid4()}"
        second_id = f"second_{uuid4()}"
        
        service.start_context_session(
            user_id=sample_user.id,
            session_id=first_id
        )
        service.start_context_session(
            user_id=sample_user.id,
            session_id=second_id
        )
        
        contexts, _ = service.get_context_history(
            user_id=sample_user.id,
            limit=10
        )
        
        # Newest should be first
        assert contexts[0].id == second_id
        assert contexts[1].id == first_id
    
    def test_increment_thought_count(
        self,
        db_session,
        sample_user,
        sample_context
    ):
        """Test incrementing thought count for a session."""
        service = ContextService(db_session)
        
        initial_count = sample_context.thought_count
        
        updated = service.increment_thought_count(
            session_id=sample_context.id,
            user_id=sample_user.id
        )
        
        assert updated.thought_count == initial_count + 1
        
        # Increment again
        updated2 = service.increment_thought_count(
            session_id=sample_context.id,
            user_id=sample_user.id
        )
        
        assert updated2.thought_count == initial_count + 2
    
    def test_increment_thought_count_not_found(self, db_session, sample_user):
        """Test incrementing count for non-existent session raises error."""
        service = ContextService(db_session)
        
        with pytest.raises(NotFoundError):
            service.increment_thought_count(
                session_id="nonexistent",
                user_id=sample_user.id
            )
    
    def test_get_context_success(
        self,
        db_session,
        sample_user,
        sample_context
    ):
        """Test getting a specific context by ID."""
        service = ContextService(db_session)
        
        context = service.get_context(
            session_id=sample_context.id,
            user_id=sample_user.id
        )
        
        assert context.id == sample_context.id
        assert context.current_activity == sample_context.current_activity
    
    def test_get_context_not_found(self, db_session, sample_user):
        """Test getting a non-existent context raises NotFoundError."""
        service = ContextService(db_session)
        
        with pytest.raises(NotFoundError):
            service.get_context(
                session_id="nonexistent",
                user_id=sample_user.id
            )
    
    def test_get_context_wrong_user(
        self,
        db_session,
        sample_user,
        sample_context
    ):
        """Test getting another user's context raises NotFoundError."""
        service = ContextService(db_session)
        
        other_user_id = uuid4()
        
        with pytest.raises(NotFoundError):
            service.get_context(
                session_id=sample_context.id,
                user_id=other_user_id
            )
    
    def test_multiple_active_contexts_returns_latest(
        self,
        db_session,
        sample_user
    ):
        """Test that get_current_context returns most recent when multiple active."""
        service = ContextService(db_session)
        
        # This shouldn't normally happen but test the behavior
        first_id = f"first_{uuid4()}"
        second_id = f"second_{uuid4()}"
        
        service.start_context_session(
            user_id=sample_user.id,
            session_id=first_id
        )
        service.start_context_session(
            user_id=sample_user.id,
            session_id=second_id
        )
        
        current = service.get_current_context(user_id=sample_user.id)
        
        # Should return the most recent (second)
        assert current.id == second_id


# Additional fixtures
@pytest.fixture
def sample_context(db_session, sample_user):
    """Create a sample context session for testing."""
    context = ContextDB(
        id=f"session_{uuid4()}",
        user_id=str(sample_user.id),
        started_at=datetime.now(timezone.utc),
        current_activity="Testing",
        thought_count=0,
        ended_at=None
    )
    db_session.add(context)
    db_session.commit()
    db_session.refresh(context)
    return context
