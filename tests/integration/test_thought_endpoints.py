"""
Detailed integration tests for thought endpoints.

Focuses on edge cases, validation, and thought-specific functionality.
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestThoughtCreation:
    """Test thought creation edge cases."""
    
    def test_create_minimal_thought(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create thought with only required fields."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Minimal thought"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["content"] == "Minimal thought"
        assert data["tags"] == []
        assert data["context"] is None
    
    def test_create_thought_with_all_fields(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create thought with all optional fields."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={
                "content": "Complete thought",
                "tags": ["tag1", "tag2", "tag3"],
                "context": {
                    "app": "Mail.app",
                    "time_of_day": "morning",
                    "energy_level": "high"
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["content"] == "Complete thought"
        assert len(data["tags"]) == 3
        assert data["context"]["app"] == "Mail.app"
    
    def test_create_thought_with_unicode(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create thought with unicode characters."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={
                "content": "Unicode test: ★ 🎉 こんにちは",
                "tags": ["unicode"]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert "★" in data["content"]
        assert "🎉" in data["content"]
    
    def test_create_thought_with_long_content(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create thought with maximum allowed content length."""
        long_content = "A" * 4999  # Just under 5000 char limit
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": long_content},
            headers=auth_headers
        )
        
        assert response.status_code == 201
    
    def test_create_thought_with_empty_content_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Empty content is rejected."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_create_thought_with_whitespace_only_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Whitespace-only content is rejected."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": "   "},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_create_thought_with_too_many_tags_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """More than 5 tags rejected."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={
                "content": "Test",
                "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422


@pytest.mark.integration
class TestThoughtRetrieval:
    """Test thought retrieval functionality."""
    
    def test_get_thought_by_id(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Retrieve thought by exact ID."""
        # Create
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Findable thought"},
            headers=auth_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        # Retrieve
        get_resp = api_client.get(
            f"/api/v1/thoughts/{thought_id}",
            headers=auth_headers
        )
        
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == thought_id
    
    def test_get_nonexistent_thought_returns_404(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Non-existent thought ID returns 404."""
        fake_id = str(uuid4())
        response = api_client.get(
            f"/api/v1/thoughts/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        error = response.json()["error"]
        assert "not found" in error["message"].lower()
    
    def test_list_thoughts_default_params(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """List thoughts with default parameters."""
        response = api_client.get(
            "/api/v1/thoughts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "thoughts" in data
        assert "pagination" in data
        assert data["pagination"]["limit"] == 20  # Default
    
    def test_list_thoughts_custom_limit(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """List thoughts with custom limit."""
        # Create several thoughts
        for i in range(15):
            api_client.post(
                "/api/v1/thoughts",
                json={"content": f"Thought {i}"},
                headers=auth_headers
            )
        
        response = api_client.get(
            "/api/v1/thoughts?limit=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["thoughts"]) <= 5
    
    def test_list_thoughts_sort_by_created_desc(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """List thoughts sorted by created_at descending (newest first)."""
        # Create thoughts with time gap
        resp1 = api_client.post(
            "/api/v1/thoughts",
            json={"content": "First"},
            headers=auth_headers
        )
        resp2 = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Second"},
            headers=auth_headers
        )
        
        # List with desc order (default)
        response = api_client.get(
            "/api/v1/thoughts?sort_order=desc",
            headers=auth_headers
        )
        
        thoughts = response.json()["data"]["thoughts"]
        # Second should come before First (newest first)
        second_index = next(
            i for i, t in enumerate(thoughts) 
            if t["content"] == "Second"
        )
        first_index = next(
            i for i, t in enumerate(thoughts) 
            if t["content"] == "First"
        )
        assert second_index < first_index


@pytest.mark.integration
class TestThoughtSearch:
    """Test thought search functionality."""
    
    def test_search_by_content(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Search finds thoughts by content."""
        # Create thoughts with distinct content
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "The email system needs improvement"},
            headers=auth_headers
        )
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Weather is nice today"},
            headers=auth_headers
        )
        
        # Search for email
        response = api_client.get(
            "/api/v1/thoughts/search?q=email",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        results = response.json()["data"]["results"]
        assert len(results) >= 1
        assert any("email" in r["content"].lower() for r in results)
    
    def test_search_by_tag(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Search finds thoughts by tags."""
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Something", "tags": ["important"]},
            headers=auth_headers
        )
        
        response = api_client.get(
            "/api/v1/thoughts/search?q=important",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        results = response.json()["data"]["results"]
        assert len(results) >= 1
    
    def test_search_returns_relevance_scores(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Search results include match scores."""
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Machine learning project"},
            headers=auth_headers
        )
        
        response = api_client.get(
            "/api/v1/thoughts/search?q=machine",
            headers=auth_headers
        )
        
        results = response.json()["data"]["results"]
        assert all("match_score" in r for r in results)
        assert all(r["match_score"] > 0 for r in results)
    
    def test_search_with_no_matches(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Search with no matches returns empty results."""
        response = api_client.get(
            "/api/v1/thoughts/search?q=nonexistentquery12345",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["results"] == []
        assert data["pagination"]["total"] == 0
    
    def test_search_requires_query_param(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Search without query parameter fails."""
        response = api_client.get(
            "/api/v1/thoughts/search",
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestThoughtUpdate:
    """Test thought update functionality."""
    
    def test_update_content(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update thought content."""
        # Create
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Original"},
            headers=auth_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        # Update
        update_resp = api_client.put(
            f"/api/v1/thoughts/{thought_id}",
            json={"content": "Updated"},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["content"] == "Updated"
    
    def test_update_tags(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update thought tags."""
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Test", "tags": ["old"]},
            headers=auth_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        update_resp = api_client.put(
            f"/api/v1/thoughts/{thought_id}",
            json={"tags": ["new", "updated"]},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["tags"] == ["new", "updated"]
    
    def test_update_status(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update thought status."""
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Test"},
            headers=auth_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        update_resp = api_client.put(
            f"/api/v1/thoughts/{thought_id}",
            json={"status": "archived"},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["status"] == "archived"
    
    def test_update_refreshes_updated_at(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update changes updated_at timestamp."""
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Test"},
            headers=auth_headers
        )
        original_updated_at = create_resp.json()["data"]["updated_at"]
        thought_id = create_resp.json()["data"]["id"]
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        update_resp = api_client.put(
            f"/api/v1/thoughts/{thought_id}",
            json={"content": "Updated"},
            headers=auth_headers
        )
        
        new_updated_at = update_resp.json()["data"]["updated_at"]
        assert new_updated_at != original_updated_at


@pytest.mark.integration
class TestThoughtDeletion:
    """Test thought deletion functionality."""
    
    def test_delete_thought(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Delete thought returns 204."""
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "To delete"},
            headers=auth_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        delete_resp = api_client.delete(
            f"/api/v1/thoughts/{thought_id}",
            headers=auth_headers
        )
        
        assert delete_resp.status_code == 204
    
    def test_delete_nonexistent_thought_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Delete non-existent thought returns 404."""
        fake_id = str(uuid4())
        response = api_client.delete(
            f"/api/v1/thoughts/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_deleted_thought_not_in_list(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Deleted thought doesn't appear in list."""
        # Create and delete
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Will be deleted"},
            headers=auth_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        api_client.delete(
            f"/api/v1/thoughts/{thought_id}",
            headers=auth_headers
        )
        
        # List thoughts
        list_resp = api_client.get(
            "/api/v1/thoughts",
            headers=auth_headers
        )
        
        thoughts = list_resp.json()["data"]["thoughts"]
        thought_ids = [t["id"] for t in thoughts]
        assert thought_id not in thought_ids
