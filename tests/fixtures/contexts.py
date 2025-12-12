"""
Context fixtures for testing.

Provides factories and fixtures for creating test context sessions with
various environmental and mental state configurations.
"""

from typing import Optional
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.models.base import utc_now
from src.models.enums import TimeOfDay, EnergyLevel, FocusState


class ContextFactory:
    """
    Factory for creating test context objects.
    
    Provides flexible context creation with sensible defaults that can be
    overridden for specific test scenarios.
    """
    
    @staticmethod
    def create_dict(
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        current_activity: str = "Testing",
        active_app: str = "VSCode",
        location: Optional[str] = None,
        time_of_day: TimeOfDay = TimeOfDay.AFTERNOON,
        energy_level: EnergyLevel = EnergyLevel.MEDIUM,
        focus_state: FocusState = FocusState.DEEP_WORK,
        thought_count: int = 0,
        notes: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Create context data dictionary for testing.
        
        Args:
            session_id: Unique session identifier (auto-generated if None)
            user_id: User ID (auto-generated if None)
            current_activity: What the user was doing
            active_app: Foreground application
            location: Physical location
            time_of_day: General time of day
            energy_level: User's self-reported energy level
            focus_state: User's mental focus state
            thought_count: Number of thoughts in this session
            notes: Additional situational notes
            **kwargs: Additional fields to override
            
        Returns:
            dict: Context data ready for database insertion
            
        Example:
            >>> context_data = ContextFactory.create_dict(
            ...     current_activity="Email review",
            ...     time_of_day=TimeOfDay.MORNING
            ... )
            >>> assert context_data["current_activity"] == "Email review"
        """
        if session_id is None:
            session_id = f"sess_{str(uuid4())[:8]}"
        
        if user_id is None:
            user_id = str(uuid4())
        
        context_data = {
            "id": session_id,  # session_id is the primary key
            "user_id": user_id,
            "started_at": utc_now(),
            "current_activity": current_activity,
            "active_app": active_app,
            "location": location,
            "time_of_day": time_of_day.value if isinstance(time_of_day, TimeOfDay) else time_of_day,
            "energy_level": energy_level.value if isinstance(energy_level, EnergyLevel) else energy_level,
            "focus_state": focus_state.value if isinstance(focus_state, FocusState) else focus_state,
            "thought_count": thought_count,
            "notes": notes,
            "ended_at": None,
            "created_at": utc_now(),
            "updated_at": utc_now()
        }
        
        # Override with any additional fields
        context_data.update(kwargs)
        
        return context_data
    
    @staticmethod
    def create_api_dict(
        session_id: str = None,
        current_activity: str = "Testing",
        active_app: str = "VSCode",
        location: Optional[str] = None,
        time_of_day: Optional[TimeOfDay] = TimeOfDay.AFTERNOON,
        energy_level: Optional[EnergyLevel] = EnergyLevel.MEDIUM,
        focus_state: Optional[FocusState] = FocusState.DEEP_WORK,
        notes: Optional[str] = None
    ) -> dict:
        """
        Create context data for API requests (no id, timestamps, user_id).
        
        Args:
            session_id: Unique session identifier
            current_activity: What the user was doing
            active_app: Foreground application
            location: Physical location
            time_of_day: General time of day
            energy_level: User's self-reported energy level
            focus_state: User's mental focus state
            notes: Additional situational notes
            
        Returns:
            dict: Context data for API POST requests
        """
        if session_id is None:
            session_id = f"sess_{str(uuid4())[:8]}"
        
        return {
            "session_id": session_id,
            "current_activity": current_activity,
            "active_app": active_app,
            "location": location,
            "time_of_day": time_of_day.value if time_of_day else None,
            "energy_level": energy_level.value if energy_level else None,
            "focus_state": focus_state.value if focus_state else None,
            "notes": notes
        }
    
    @staticmethod
    def create_batch(
        count: int,
        user_id: Optional[str] = None,
        **kwargs
    ) -> list[dict]:
        """
        Create multiple context data dictionaries.
        
        Args:
            count: Number of contexts to create
            user_id: User ID for all contexts
            **kwargs: Common fields for all contexts
            
        Returns:
            list[dict]: List of context data dictionaries
            
        Example:
            >>> contexts = ContextFactory.create_batch(
            ...     3,
            ...     time_of_day=TimeOfDay.EVENING
            ... )
            >>> assert len(contexts) == 3
            >>> assert all(c["time_of_day"] == "evening" for c in contexts)
        """
        return [
            ContextFactory.create_dict(
                session_id=f"sess_{i}_{str(uuid4())[:8]}",
                user_id=user_id,
                **kwargs
            )
            for i in range(count)
        ]


@pytest.fixture
def context_factory() -> ContextFactory:
    """
    Provide ContextFactory instance for tests.
    
    Returns:
        ContextFactory: Factory for creating test contexts
        
    Example:
        >>> def test_context_creation(context_factory):
        ...     context_data = context_factory.create_dict(
        ...         current_activity="Custom activity"
        ...     )
        ...     assert context_data["current_activity"] == "Custom activity"
    """
    return ContextFactory()


@pytest.fixture
def sample_context(db_session: Session, sample_user: dict) -> dict:
    """
    Create a test context in the database.
    
    Creates a default test context linked to sample_user that can be
    used across tests.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        dict: Created context data with database ID
        
    Example:
        >>> def test_with_context(sample_context):
        ...     assert sample_context["session_id"]
        ...     assert sample_context["current_activity"]
    """
    from src.models.context import ContextDB
    
    context_data = ContextFactory.create_dict(
        user_id=sample_user["id"]
    )
    context = ContextDB(**context_data)
    
    db_session.add(context)
    db_session.commit()
    db_session.refresh(context)
    
    return {
        "id": context.id,  # session_id
        "session_id": context.id,
        "user_id": context.user_id,
        "started_at": context.started_at,
        "current_activity": context.current_activity,
        "active_app": context.active_app,
        "time_of_day": context.time_of_day,
        "energy_level": context.energy_level,
        "focus_state": context.focus_state,
        "thought_count": context.thought_count
    }


@pytest.fixture
def morning_context(db_session: Session, sample_user: dict) -> dict:
    """
    Create a morning context session.
    
    Useful for testing time-of-day filtering and pattern analysis.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        dict: Created morning context data
    """
    from src.models.context import ContextDB
    
    context_data = ContextFactory.create_dict(
        user_id=sample_user["id"],
        current_activity="Morning planning",
        time_of_day=TimeOfDay.MORNING,
        energy_level=EnergyLevel.HIGH,
        focus_state=FocusState.DEEP_WORK
    )
    context = ContextDB(**context_data)
    
    db_session.add(context)
    db_session.commit()
    db_session.refresh(context)
    
    return {
        "id": context.id,
        "time_of_day": context.time_of_day,
        "energy_level": context.energy_level
    }


@pytest.fixture
def interrupted_context(db_session: Session, sample_user: dict) -> dict:
    """
    Create a context with interrupted focus state.
    
    Useful for testing focus state analysis and recommendations.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        dict: Created interrupted context data
    """
    from src.models.context import ContextDB
    
    context_data = ContextFactory.create_dict(
        user_id=sample_user["id"],
        current_activity="Email interruptions",
        time_of_day=TimeOfDay.AFTERNOON,
        energy_level=EnergyLevel.LOW,
        focus_state=FocusState.INTERRUPTED,
        notes="Too many context switches"
    )
    context = ContextDB(**context_data)
    
    db_session.add(context)
    db_session.commit()
    db_session.refresh(context)
    
    return {
        "id": context.id,
        "focus_state": context.focus_state,
        "notes": context.notes
    }


@pytest.fixture
def multiple_contexts(db_session: Session, sample_user: dict) -> list[dict]:
    """
    Create multiple test contexts with varying configurations.
    
    Creates 4 contexts representing different times of day and mental states
    for testing pattern analysis.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        list[dict]: List of created context data
    """
    from src.models.context import ContextDB
    
    contexts_data = [
        ContextFactory.create_dict(
            user_id=sample_user["id"],
            time_of_day=TimeOfDay.MORNING,
            energy_level=EnergyLevel.HIGH,
            focus_state=FocusState.DEEP_WORK
        ),
        ContextFactory.create_dict(
            user_id=sample_user["id"],
            time_of_day=TimeOfDay.AFTERNOON,
            energy_level=EnergyLevel.MEDIUM,
            focus_state=FocusState.DEEP_WORK
        ),
        ContextFactory.create_dict(
            user_id=sample_user["id"],
            time_of_day=TimeOfDay.EVENING,
            energy_level=EnergyLevel.MEDIUM,
            focus_state=FocusState.INTERRUPTED
        ),
        ContextFactory.create_dict(
            user_id=sample_user["id"],
            time_of_day=TimeOfDay.NIGHT,
            energy_level=EnergyLevel.LOW,
            focus_state=FocusState.SCATTERED
        ),
    ]
    
    created_contexts = []
    for context_data in contexts_data:
        context = ContextDB(**context_data)
        db_session.add(context)
        db_session.commit()
        db_session.refresh(context)
        
        created_contexts.append({
            "id": context.id,
            "time_of_day": context.time_of_day,
            "energy_level": context.energy_level,
            "focus_state": context.focus_state
        })
    
    return created_contexts
