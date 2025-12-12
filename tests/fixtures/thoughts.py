"""
Thought fixtures for testing.

Provides factories and fixtures for creating test thoughts with various
content, tags, and context configurations.
"""

from typing import Dict, Any, List, Optional
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.models.base import utc_now
from src.models.enums import ThoughtStatus


class ThoughtFactory:
    """
    Factory for creating test thought objects.
    
    Provides flexible thought creation with sensible defaults that can be
    overridden for specific test scenarios.
    """
    
    @staticmethod
    def create_dict(
        content: str = "This is a test thought",
        tags: Optional[List[str]] = None,
        status: ThoughtStatus = ThoughtStatus.ACTIVE,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Create thought data dictionary for testing.
        
        Args:
            content: Thought text content
            tags: List of tags (defaults to ["test"])
            status: Thought lifecycle status
            context: Situational context dict
            user_id: User ID (auto-generated if None)
            **kwargs: Additional fields to override
            
        Returns:
            dict: Thought data ready for database insertion or API request
            
        Example:
            >>> thought_data = ThoughtFactory.create_dict(
            ...     content="Remember to test edge cases",
            ...     tags=["testing", "development"]
            ... )
            >>> assert "test" in thought_data["content"]
        """
        if tags is None:
            tags = ["test"]
        
        if context is None:
            context = {
                "active_app": "VSCode",
                "time_of_day": "afternoon"
            }
        
        if user_id is None:
            user_id = str(uuid4())
        
        thought_data = {
            "id": str(uuid4()),
            "user_id": user_id,
            "content": content,
            "tags": tags,
            "status": status.value if isinstance(status, ThoughtStatus) else status,
            "context": context,
            "claude_summary": None,
            "claude_analysis": None,
            "created_at": utc_now(),
            "updated_at": utc_now()
        }
        
        # Override with any additional fields
        thought_data.update(kwargs)
        
        return thought_data
    
    @staticmethod
    def create_api_dict(
        content: str = "This is a test thought",
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Create thought data for API requests (no id, timestamps, user_id).
        
        Args:
            content: Thought text content
            tags: List of tags
            context: Situational context dict
            
        Returns:
            dict: Thought data for API POST/PUT requests
            
        Example:
            >>> api_data = ThoughtFactory.create_api_dict(
            ...     content="API test thought"
            ... )
            >>> assert "id" not in api_data
            >>> assert "created_at" not in api_data
        """
        if tags is None:
            tags = ["test"]
        
        return {
            "content": content,
            "tags": tags,
            "context": context
        }
    
    @staticmethod
    def create_batch(
        count: int,
        user_id: Optional[str] = None,
        **kwargs
    ) -> List[dict]:
        """
        Create multiple thought data dictionaries.
        
        Args:
            count: Number of thoughts to create
            user_id: User ID for all thoughts
            **kwargs: Common fields for all thoughts
            
        Returns:
            list[dict]: List of thought data dictionaries
            
        Example:
            >>> thoughts = ThoughtFactory.create_batch(
            ...     5,
            ...     tags=["batch-test"]
            ... )
            >>> assert len(thoughts) == 5
            >>> assert all("batch-test" in t["tags"] for t in thoughts)
        """
        return [
            ThoughtFactory.create_dict(
                content=f"Test thought #{i+1}",
                user_id=user_id,
                **kwargs
            )
            for i in range(count)
        ]
    
    @staticmethod
    def create_with_long_content(
        length: int = 4500,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Create thought with specific content length for testing limits.
        
        Args:
            length: Desired content length in characters
            user_id: User ID
            
        Returns:
            dict: Thought data with specified content length
        """
        content = "a" * length
        return ThoughtFactory.create_dict(
            content=content,
            user_id=user_id
        )
    
    @staticmethod
    def create_with_many_tags(
        tag_count: int = 5,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Create thought with specific number of tags for testing limits.
        
        Args:
            tag_count: Number of tags to create
            user_id: User ID
            
        Returns:
            dict: Thought data with specified tag count
        """
        tags = [f"tag{i}" for i in range(tag_count)]
        return ThoughtFactory.create_dict(
            content="Thought with many tags",
            tags=tags,
            user_id=user_id
        )


@pytest.fixture
def thought_factory() -> ThoughtFactory:
    """
    Provide ThoughtFactory instance for tests.
    
    Returns:
        ThoughtFactory: Factory for creating test thoughts
        
    Example:
        >>> def test_thought_creation(thought_factory):
        ...     thought_data = thought_factory.create_dict(
        ...         content="Custom thought"
        ...     )
        ...     assert thought_data["content"] == "Custom thought"
    """
    return ThoughtFactory()


@pytest.fixture
def sample_thought(db_session: Session, sample_user: dict) -> dict:
    """
    Create a test thought in the database.
    
    Creates a default test thought linked to sample_user that can be
    used across tests.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        dict: Created thought data with database ID
        
    Example:
        >>> def test_with_thought(sample_thought):
        ...     assert sample_thought["content"]
        ...     assert sample_thought["user_id"]
    """
    from src.models.thought import ThoughtDB
    
    thought_data = ThoughtFactory.create_dict(
        user_id=sample_user["id"]
    )
    thought = ThoughtDB(**thought_data)
    
    db_session.add(thought)
    db_session.commit()
    db_session.refresh(thought)
    
    return {
        "id": thought.id,
        "user_id": thought.user_id,
        "content": thought.content,
        "tags": thought.tags,
        "status": thought.status,
        "context": thought.context,
        "created_at": thought.created_at,
        "updated_at": thought.updated_at
    }


@pytest.fixture
def archived_thought(db_session: Session, sample_user: dict) -> dict:
    """
    Create an archived test thought in the database.
    
    Useful for testing status filtering and lifecycle management.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        dict: Created archived thought data
    """
    from src.models.thought import ThoughtDB
    
    thought_data = ThoughtFactory.create_dict(
        content="Archived test thought",
        status=ThoughtStatus.ARCHIVED,
        user_id=sample_user["id"]
    )
    thought = ThoughtDB(**thought_data)
    
    db_session.add(thought)
    db_session.commit()
    db_session.refresh(thought)
    
    return {
        "id": thought.id,
        "user_id": thought.user_id,
        "content": thought.content,
        "status": thought.status
    }


@pytest.fixture
def multiple_thoughts(db_session: Session, sample_user: dict) -> List[dict]:
    """
    Create multiple test thoughts in the database.
    
    Creates 5 test thoughts with varying content and tags for testing
    list/filter operations.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        list[dict]: List of created thought data
    """
    from src.models.thought import ThoughtDB
    
    thoughts_data = ThoughtFactory.create_batch(
        5,
        user_id=sample_user["id"]
    )
    
    created_thoughts = []
    for thought_data in thoughts_data:
        thought = ThoughtDB(**thought_data)
        db_session.add(thought)
        db_session.commit()
        db_session.refresh(thought)
        
        created_thoughts.append({
            "id": thought.id,
            "content": thought.content,
            "tags": thought.tags
        })
    
    return created_thoughts


@pytest.fixture
def thought_with_claude_analysis(
    db_session: Session,
    sample_user: dict
) -> dict:
    """
    Create a thought with Claude analysis data.
    
    Simulates a thought that has been analyzed by Claude with summary
    and theme extraction.
    
    Args:
        db_session: Database session fixture
        sample_user: Sample user fixture
        
    Returns:
        dict: Created thought data with analysis
    """
    from src.models.thought import ThoughtDB
    
    thought_data = ThoughtFactory.create_dict(
        content="This thought has been analyzed by Claude",
        user_id=sample_user["id"],
        claude_summary="A thought about Claude analysis",
        claude_analysis={
            "themes": ["testing", "ai", "analysis"],
            "confidence": 0.85,
            "related_thought_ids": []
        }
    )
    thought = ThoughtDB(**thought_data)
    
    db_session.add(thought)
    db_session.commit()
    db_session.refresh(thought)
    
    return {
        "id": thought.id,
        "content": thought.content,
        "claude_summary": thought.claude_summary,
        "claude_analysis": thought.claude_analysis
    }
