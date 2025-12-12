"""
Comprehensive API endpoint integration tests.

Tests complete request/response cycles with real database and service layer.
Verifies all CRUD operations work end-to-end.
"""

import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.thought import ThoughtDB
from src.models.task import TaskDB
from src.models.enums import ThoughtStatus, TaskStatus, Priority


@pytest.mark.integration
class TestThoughtEndpointsIntegration:
    """Integration tests for thought endpoints with database."""
    
    def test_create_thought_full_flow(
        self, 
        api_client: TestClient, 
        auth_headers: dict,
        db_session: Session
    ):
        """
        Full flow: POST /thoughts → database → response.
        
        Verify:
        - 201 Created response
        - Thought stored in database
        - All fields returned correctly
        - ID and timestamps generated
        """
        response = api_client.post(
            "/api/v1/thoughts",
            json={
                "content": "Integration test thought",
                "tags": ["test", "integration"],
                "context": {"app": "pytest", "environment": "test"}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"]  # ID generated
        assert data["data"]["created_at"]  # Timestamp set
        assert data["data"]["content"] == "Integration test thought"
        assert data["data"]["tags"] == ["test", "integration"]
        assert data["data"]["status"] == "active"
        
        # Verify in database
        thought = db_session.query(ThoughtDB).filter_by(
            id=data["data"]["id"]
        ).first()
        assert thought is not None
        assert thought.content == "Integration test thought"
        assert thought.tags == ["test", "integration"]
    
    def test_get_thought_after_create(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create thought then retrieve it."""
        # Create
        create_response = api_client.post(
            "/api/v1/thoughts",
            json={
                "content": "Test retrieval",
                "tags": ["retrieve"]
            },
            headers=auth_headers
        )
        thought_id = create_response.json()["data"]["id"]
        
        # Retrieve
        get_response = api_client.get(
            f"/api/v1/thoughts/{thought_id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        data = get_response.json()["data"]
        assert data["id"] == thought_id
        assert data["content"] == "Test retrieval"
    
    def test_list_thoughts_with_pagination(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """List thoughts with limit and offset."""
        # Create 25 thoughts
        for i in range(25):
            api_client.post(
                "/api/v1/thoughts",
                json={"content": f"Thought {i}", "tags": []},
                headers=auth_headers
            )
        
        # Get first page (limit 10)
        response = api_client.get(
            "/api/v1/thoughts?limit=10&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["thoughts"]) == 10
        assert data["pagination"]["total"] >= 25
        assert data["pagination"]["has_more"] is True
        
        # Get second page
        response2 = api_client.get(
            "/api/v1/thoughts?limit=10&offset=10",
            headers=auth_headers
        )
        assert response2.status_code == 200
        data2 = response2.json()["data"]
        assert len(data2["thoughts"]) == 10
    
    def test_list_thoughts_filter_by_status(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Filter thoughts by status."""
        # Create thoughts with different statuses
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Active thought", "tags": []},
            headers=auth_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        # Archive it
        api_client.put(
            f"/api/v1/thoughts/{thought_id}",
            json={"status": "archived"},
            headers=auth_headers
        )
        
        # Create another active one
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Still active", "tags": []},
            headers=auth_headers
        )
        
        # Filter by archived
        response = api_client.get(
            "/api/v1/thoughts?status=archived",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        thoughts = response.json()["data"]["thoughts"]
        assert all(t["status"] == "archived" for t in thoughts)
    
    def test_list_thoughts_filter_by_tags(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Filter thoughts by tags."""
        # Create thoughts with different tags
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Email thought", "tags": ["email"]},
            headers=auth_headers
        )
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Code thought", "tags": ["code"]},
            headers=auth_headers
        )
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Both", "tags": ["email", "code"]},
            headers=auth_headers
        )
        
        # Filter by email tag
        response = api_client.get(
            "/api/v1/thoughts?tags=email",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        thoughts = response.json()["data"]["thoughts"]
        assert all("email" in t["tags"] for t in thoughts)
        assert len(thoughts) >= 2
    
    def test_search_thoughts_returns_matches(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Search returns matching thoughts with relevance scores."""
        # Create thoughts with searchable content
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Email is very important", "tags": []},
            headers=auth_headers
        )
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Just a random thought", "tags": []},
            headers=auth_headers
        )
        api_client.post(
            "/api/v1/thoughts",
            json={"content": "Another email-related idea", "tags": ["email"]},
            headers=auth_headers
        )
        
        # Search for "email"
        response = api_client.get(
            "/api/v1/thoughts/search?q=email",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["query"] == "email"
        assert len(data["results"]) >= 2
        # Verify match scores are present
        assert all("match_score" in r for r in data["results"])
        assert all(r["match_score"] > 0 for r in data["results"])
    
    def test_update_thought_partial(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update only specified fields, others unchanged."""
        # Create
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={
                "content": "Original content",
                "tags": ["old"],
                "status": "active"
            },
            headers=auth_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        # Update only content
        update_resp = api_client.put(
            f"/api/v1/thoughts/{thought_id}",
            json={"content": "Updated content"},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        data = update_resp.json()["data"]
        assert data["content"] == "Updated content"
        assert data["tags"] == ["old"]  # Unchanged
        assert data["status"] == "active"  # Unchanged
    
    def test_delete_thought_removes_from_database(
        self, 
        api_client: TestClient, 
        auth_headers: dict,
        db_session: Session
    ):
        """Delete removes thought from database."""
        # Create
        create_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "To delete", "tags": []},
            headers=auth_headers
        )
        thought_id = create_resp.json()["data"]["id"]
        
        # Delete
        delete_resp = api_client.delete(
            f"/api/v1/thoughts/{thought_id}",
            headers=auth_headers
        )
        assert delete_resp.status_code == 204
        
        # Verify gone from database
        thought = db_session.query(ThoughtDB).filter_by(id=thought_id).first()
        assert thought is None
    
    def test_create_thought_without_auth_fails(
        self, 
        api_client_real_auth: TestClient
    ):
        """Request without API key returns 401."""
        response = api_client_real_auth.post(
            "/api/v1/thoughts",
            json={"content": "Test", "tags": []}
            # No headers = no auth
        )
        assert response.status_code == 401
    
    def test_create_invalid_thought_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Invalid content rejected with 400."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": "", "tags": []},  # Empty content
            headers=auth_headers
        )
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "INVALID_CONTENT"
    
    def test_get_nonexistent_thought_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Get non-existent thought returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(
            f"/api/v1/thoughts/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
        error = response.json()["error"]
        assert error["code"] == "THOUGHT_NOT_FOUND"


@pytest.mark.integration
class TestTaskEndpointsIntegration:
    """Integration tests for task endpoints with database."""
    
    def test_create_task_full_flow(
        self, 
        api_client: TestClient, 
        auth_headers: dict,
        db_session: Session
    ):
        """
        Full flow: POST /tasks → database → response.
        """
        response = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Integration test task",
                "description": "Test task description",
                "priority": "high",
                "due_date": "2025-12-20",
                "estimated_effort_minutes": 60
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["id"]
        assert data["title"] == "Integration test task"
        assert data["priority"] == "high"
        assert data["status"] == "pending"
        
        # Verify in database
        task = db_session.query(TaskDB).filter_by(id=data["id"]).first()
        assert task is not None
        assert task.title == "Integration test task"
    
    def test_create_task_from_thought(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create task linked to source thought."""
        # First create a thought
        thought_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Need to do something", "tags": []},
            headers=auth_headers
        )
        thought_id = thought_resp.json()["data"]["id"]
        
        # Create task from thought
        task_resp = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Task from thought",
                "source_thought_id": thought_id,
                "priority": "medium"
            },
            headers=auth_headers
        )
        
        assert task_resp.status_code == 201
        task_data = task_resp.json()["data"]
        assert task_data["source_thought_id"] == thought_id
    
    def test_list_tasks_with_filters(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """List tasks filtered by status and priority."""
        # Create tasks with different properties
        api_client.post(
            "/api/v1/tasks",
            json={"title": "High priority", "priority": "high"},
            headers=auth_headers
        )
        api_client.post(
            "/api/v1/tasks",
            json={"title": "Low priority", "priority": "low"},
            headers=auth_headers
        )
        
        # Filter by high priority
        response = api_client.get(
            "/api/v1/tasks?priority=high",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        tasks = response.json()["data"]["tasks"]
        assert all(t["priority"] == "high" for t in tasks)
    
    def test_complete_task_updates_status(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Completing task sets status to done and adds completion time."""
        # Create task
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "To complete", "priority": "medium"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        # Complete it
        complete_resp = api_client.post(
            f"/api/v1/tasks/{task_id}/complete",
            headers=auth_headers
        )
        
        assert complete_resp.status_code == 200
        data = complete_resp.json()["data"]
        assert data["status"] == "done"
        assert data["completed_at"] is not None
    
    def test_update_task_partial(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update only specified task fields."""
        # Create
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Original title",
                "priority": "low"
            },
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        # Update only priority
        update_resp = api_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"priority": "critical"},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        data = update_resp.json()["data"]
        assert data["priority"] == "critical"
        assert data["title"] == "Original title"  # Unchanged
    
    def test_delete_task_removes_from_database(
        self, 
        api_client: TestClient, 
        auth_headers: dict,
        db_session: Session
    ):
        """Delete removes task from database."""
        # Create
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "To delete", "priority": "low"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        # Delete
        delete_resp = api_client.delete(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        assert delete_resp.status_code == 204
        
        # Verify gone
        task = db_session.query(TaskDB).filter_by(id=task_id).first()
        assert task is None


@pytest.mark.integration
class TestAPIResponseFormat:
    """Test consistent API response formatting."""
    
    def test_success_response_format(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """All successful responses follow standard format."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Test", "tags": []},
            headers=auth_headers
        )
        
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "error" in data
        assert "request_id" in data
        assert "timestamp" in data
        assert data["success"] is True
        assert data["error"] is None
    
    def test_error_response_format(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """All error responses follow standard format."""
        response = api_client.post(
            "/api/v1/thoughts",
            json={"content": "", "tags": []},  # Invalid
            headers=auth_headers
        )
        
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "error" in data
        assert "request_id" in data
        assert "timestamp" in data
        assert data["success"] is False
        assert data["data"] is None
        assert "code" in data["error"]
        assert "message" in data["error"]
