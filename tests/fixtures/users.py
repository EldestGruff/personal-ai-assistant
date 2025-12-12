"""
User fixtures for testing.

Provides factories and fixtures for creating test users with various
configurations and preferences.
"""

from typing import Dict, Any, Optional
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.models.base import utc_now


class UserFactory:
    """
    Factory for creating test user objects.
    
    Provides flexible user creation with sensible defaults that can be
    overridden for specific test scenarios.
    """
    
    @staticmethod
    def create_dict(
        name: str = "Test User",
        email: str = None,
        preferences: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        **kwargs
    ) -> dict:
        """
        Create user data dictionary for testing.
        
        Args:
            name: User's display name
            email: User's email (auto-generated if None)
            preferences: User preferences dict
            is_active: Whether user account is active
            **kwargs: Additional fields to override
            
        Returns:
            dict: User data ready for database insertion
            
        Example:
            >>> user_data = UserFactory.create_dict(
            ...     name="Andy",
            ...     email="andy@example.com"
            ... )
            >>> assert user_data["name"] == "Andy"
        """
        if email is None:
            # Generate unique email for each user
            email = f"test_{str(uuid4())[:8]}@example.com"
        
        if preferences is None:
            preferences = {
                "timezone": "America/New_York",
                "max_thoughts_goal": 20,
                "reminder_frequency_minutes": 30
            }
        
        user_data = {
            "id": str(uuid4()),
            "name": name,
            "email": email,
            "preferences": preferences,
            "is_active": is_active,
            "created_at": utc_now(),
            "updated_at": utc_now()
        }
        
        # Override with any additional fields
        user_data.update(kwargs)
        
        return user_data
    
    @staticmethod
    def create_batch(
        count: int,
        **kwargs
    ) -> list[dict]:
        """
        Create multiple user data dictionaries.
        
        Args:
            count: Number of users to create
            **kwargs: Common fields for all users
            
        Returns:
            list[dict]: List of user data dictionaries
            
        Example:
            >>> users = UserFactory.create_batch(3, name="Test User")
            >>> assert len(users) == 3
            >>> assert all(u["name"] == "Test User" for u in users)
        """
        return [
            UserFactory.create_dict(**kwargs)
            for _ in range(count)
        ]


@pytest.fixture
def user_factory() -> UserFactory:
    """
    Provide UserFactory instance for tests.
    
    Returns:
        UserFactory: Factory for creating test users
        
    Example:
        >>> def test_user_creation(user_factory):
        ...     user_data = user_factory.create_dict(name="Custom User")
        ...     assert user_data["name"] == "Custom User"
    """
    return UserFactory()


@pytest.fixture
def sample_user(db_session: Session) -> dict:
    """
    Create a test user in the database.
    
    Creates a default test user that can be used across tests.
    The user is committed to the database and available for queries.
    
    Args:
        db_session: Database session fixture
        
    Returns:
        dict: Created user data with database ID
        
    Example:
        >>> def test_with_user(sample_user, db_session):
        ...     from src.models.thought import ThoughtDB
        ...     thought = ThoughtDB(
        ...         user_id=sample_user["id"],
        ...         content="Test thought"
        ...     )
        ...     db_session.add(thought)
        ...     db_session.commit()
    """
    from src.models.user import UserDB  # Import here to avoid circular deps
    
    user_data = UserFactory.create_dict()
    user = UserDB(**user_data)
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "preferences": user.preferences,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


@pytest.fixture
def inactive_user(db_session: Session) -> dict:
    """
    Create an inactive test user in the database.
    
    Useful for testing access control and user state filtering.
    
    Args:
        db_session: Database session fixture
        
    Returns:
        dict: Created inactive user data
    """
    from src.models.user import UserDB
    
    user_data = UserFactory.create_dict(
        name="Inactive User",
        is_active=False
    )
    user = UserDB(**user_data)
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_active": user.is_active
    }


@pytest.fixture
def multiple_users(db_session: Session) -> list[dict]:
    """
    Create multiple test users in the database.
    
    Creates 3 test users with different configurations for testing
    multi-user scenarios.
    
    Args:
        db_session: Database session fixture
        
    Returns:
        list[dict]: List of created user data
    """
    from src.models.user import UserDB
    
    users_data = [
        UserFactory.create_dict(name="User One", email="user1@example.com"),
        UserFactory.create_dict(name="User Two", email="user2@example.com"),
        UserFactory.create_dict(name="User Three", email="user3@example.com"),
    ]
    
    created_users = []
    for user_data in users_data:
        user = UserDB(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        created_users.append({
            "id": user.id,
            "name": user.name,
            "email": user.email
        })
    
    return created_users
