"""
Integration tests for ThoughtService.

Tests the service layer with a real in-memory SQLite database to verify
all CRUD operations, filtering, searching, and error handling work correctly.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.services import ThoughtService, NotFoundError, UnauthorizedError
from src.models.thought import ThoughtDB
from src.models.user import UserDB
from src.models.enums import ThoughtStatus


@pytest.mark.integration
class TestThoughtServiceIntegration:
    """Integration tests for ThoughtService using real database."""
    
    def test_create_thought_success(self, db_session, sample_user):
        """Test creating a thought with all fields."""
        service = ThoughtService(db_session)
        
        thought = service.create_thought(
            user_id=sample_user.id,
            content="Test thought content",
            tags=["test", "integration"],
            context={"app": "pytest"}
        )
        
        assert thought.id is not None
        assert thought.user_id == str(sample_user.id)
        assert thought.content == "Test thought content"
        assert thought.tags == ["test", "integration"]
        assert thought.context == {"app": "pytest"}
        assert thought.status == ThoughtStatus.ACTIVE.value
        assert thought.created_at is not None
        assert thought.updated_at is not None
    
    def test_create_thought_minimal(self, db_session, sample_user):
        """Test creating a thought with only required fields."""
        service = ThoughtService(db_session)
        
        thought = service.create_thought(
            user_id=sample_user.id,
            content="Minimal thought"
        )
        
        assert thought.id is not None
        assert thought.content == "Minimal thought"
        assert thought.tags == []
        assert thought.context is None
    
    def test_get_thought_success(self, db_session, sample_user, sample_thought):
        """Test retrieving an existing thought."""
        service = ThoughtService(db_session)
        
        thought = service.get_thought(
            thought_id=sample_thought.id,
            user_id=sample_user.id
        )
        
        assert thought.id == sample_thought.id
        assert thought.content == sample_thought.content
    
    def test_get_thought_not_found(self, db_session, sample_user):
        """Test retrieving a non-existent thought raises NotFoundError."""
        service = ThoughtService(db_session)
        
        with pytest.raises(NotFoundError) as exc_info:
            service.get_thought(
                thought_id=uuid4(),
                user_id=sample_user.id
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_get_thought_wrong_user(self, db_session, sample_user, sample_thought):
        """Test retrieving another user's thought raises NotFoundError."""
        service = ThoughtService(db_session)
        
        other_user_id = uuid4()
        
        with pytest.raises(NotFoundError):
            service.get_thought(
                thought_id=sample_thought.id,
                user_id=other_user_id
            )
    
    def test_list_thoughts_basic(self, db_session, sample_user):
        """Test listing thoughts with pagination."""
        service = ThoughtService(db_session)
        
        # Create multiple thoughts
        for i in range(5):
            service.create_thought(
                user_id=sample_user.id,
                content=f"Thought {i}"
            )
        
        thoughts, total = service.list_thoughts(
            user_id=sample_user.id,
            limit=3,
            offset=0
        )
        
        assert len(thoughts) == 3
        assert total == 5
    
    def test_list_thoughts_filter_by_status(self, db_session, sample_user):
        """Test filtering thoughts by status."""
        service = ThoughtService(db_session)
        
        # Create active and archived thoughts
        active = service.create_thought(
            user_id=sample_user.id,
            content="Active thought"
        )
        
        archived = service.create_thought(
            user_id=sample_user.id,
            content="Archived thought"
        )
        service.update_thought(
            thought_id=archived.id,
            user_id=sample_user.id,
            status=ThoughtStatus.ARCHIVED
        )
        
        # List only active
        thoughts, total = service.list_thoughts(
            user_id=sample_user.id,
            status=ThoughtStatus.ACTIVE
        )
        
        assert total == 1
        assert thoughts[0].id == active.id
    
    def test_list_thoughts_filter_by_tags(self, db_session, sample_user):
        """Test filtering thoughts by tags."""
        service = ThoughtService(db_session)
        
        # Create thoughts with different tags
        service.create_thought(
            user_id=sample_user.id,
            content="Email thought",
            tags=["email", "work"]
        )
        service.create_thought(
            user_id=sample_user.id,
            content="Personal thought",
            tags=["personal"]
        )
        
        # Filter by email tag
        thoughts, total = service.list_thoughts(
            user_id=sample_user.id,
            tags=["email"]
        )
        
        assert total == 1
        assert "email" in thoughts[0].tags
    
    def test_list_thoughts_sorting(self, db_session, sample_user):
        """Test sorting thoughts by different fields."""
        service = ThoughtService(db_session)
        
        # Create thoughts
        first = service.create_thought(
            user_id=sample_user.id,
            content="First thought"
        )
        second = service.create_thought(
            user_id=sample_user.id,
            content="Second thought"
        )
        
        # Sort by created_at descending (newest first)
        thoughts, _ = service.list_thoughts(
            user_id=sample_user.id,
            sort_by="created_at",
            sort_order="desc"
        )
        
        assert thoughts[0].id == second.id
        assert thoughts[1].id == first.id
    
    def test_update_thought_success(self, db_session, sample_user, sample_thought):
        """Test updating a thought's fields."""
        service = ThoughtService(db_session)
        
        # Save original timestamp before update
        original_time = sample_thought.updated_at
        
        updated = service.update_thought(
            thought_id=sample_thought.id,
            user_id=sample_user.id,
            content="Updated content",
            tags=["updated"],
            status=ThoughtStatus.ARCHIVED
        )
        
        assert updated.id == sample_thought.id
        assert updated.user_id == sample_user.id
        assert updated.content == "Updated content"
        assert updated.tags == ["updated"]
        assert updated.status == ThoughtStatus.ARCHIVED.value
        # Timestamp should be >= original (microsecond precision may match)
        assert updated.updated_at >= original_time
    
    def test_update_thought_partial(self, db_session, sample_user, sample_thought):
        """Test partial update only changes specified fields."""
        service = ThoughtService(db_session)
        
        original_tags = sample_thought.tags
        
        updated = service.update_thought(
            thought_id=sample_thought.id,
            user_id=sample_user.id,
            content="New content"
        )
        
        assert updated.content == "New content"
        assert updated.tags == original_tags  # Unchanged
    
    def test_update_thought_not_found(self, db_session, sample_user):
        """Test updating a non-existent thought raises NotFoundError."""
        service = ThoughtService(db_session)
        
        with pytest.raises(NotFoundError):
            service.update_thought(
                thought_id=uuid4(),
                user_id=sample_user.id,
                content="New content"
            )
    
    def test_delete_thought_success(self, db_session, sample_user, sample_thought):
        """Test deleting a thought."""
        service = ThoughtService(db_session)
        
        result = service.delete_thought(
            thought_id=sample_thought.id,
            user_id=sample_user.id
        )
        
        assert result is True
        
        # Verify thought is gone
        with pytest.raises(NotFoundError):
            service.get_thought(
                thought_id=sample_thought.id,
                user_id=sample_user.id
            )
    
    def test_delete_thought_not_found(self, db_session, sample_user):
        """Test deleting a non-existent thought returns False."""
        service = ThoughtService(db_session)
        
        result = service.delete_thought(
            thought_id=uuid4(),
            user_id=sample_user.id
        )
        
        assert result is False
    
    def test_delete_thought_wrong_user(self, db_session, sample_user, sample_thought):
        """Test deleting another user's thought raises UnauthorizedError."""
        service = ThoughtService(db_session)
        
        other_user_id = uuid4()
        
        with pytest.raises(UnauthorizedError):
            service.delete_thought(
                thought_id=sample_thought.id,
                user_id=other_user_id
            )
    
    def test_search_thoughts_content(self, db_session, sample_user):
        """Test searching thoughts by content."""
        service = ThoughtService(db_session)
        
        # Create searchable thoughts
        service.create_thought(
            user_id=sample_user.id,
            content="Email analyzer improvement"
        )
        service.create_thought(
            user_id=sample_user.id,
            content="Guitar practice schedule"
        )
        
        # Search for "email"
        results, total = service.search_thoughts(
            user_id=sample_user.id,
            query="email"
        )
        
        assert total == 1
        assert "email" in results[0][0].content.lower()
        assert results[0][1] > 0  # Has relevance score
    
    def test_search_thoughts_tags(self, db_session, sample_user):
        """Test searching thoughts by tags."""
        service = ThoughtService(db_session)
        
        service.create_thought(
            user_id=sample_user.id,
            content="Work on project",
            tags=["work", "important"]
        )
        
        # Search for tag
        results, total = service.search_thoughts(
            user_id=sample_user.id,
            query="work"
        )
        
        assert total >= 1
        # Should find it either in content or tags
    
    def test_search_thoughts_empty_query(self, db_session, sample_user):
        """Test searching with empty query returns nothing."""
        service = ThoughtService(db_session)
        
        results, total = service.search_thoughts(
            user_id=sample_user.id,
            query=""
        )
        
        assert total == 0
        assert len(results) == 0
    
    def test_search_thoughts_relevance_scoring(self, db_session, sample_user):
        """Test search results are scored by relevance."""
        service = ThoughtService(db_session)
        
        # Create thoughts with varying relevance
        service.create_thought(
            user_id=sample_user.id,
            content="Test at the end",
            tags=[]
        )
        service.create_thought(
            user_id=sample_user.id,
            content="Test at the beginning",
            tags=["test"]  # Tag match scores higher
        )
        
        results, _ = service.search_thoughts(
            user_id=sample_user.id,
            query="test"
        )
        
        # Results should be sorted by score
        if len(results) >= 2:
            assert results[0][1] >= results[1][1]


# Additional fixtures that might be needed
@pytest.fixture
def sample_thought(db_session, sample_user):
    """Create a sample thought for testing."""
    thought = ThoughtDB(
        id=str(uuid4()),
        user_id=str(sample_user.id),
        content="Sample thought for testing",
        tags=["sample", "test"],
        status=ThoughtStatus.ACTIVE.value,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(thought)
    db_session.commit()
    db_session.refresh(thought)
    return thought
