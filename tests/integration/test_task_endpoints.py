"""
Detailed integration tests for task endpoints.

Focuses on edge cases, validation, and task-specific functionality.
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from datetime import date, timedelta


@pytest.mark.integration
class TestTaskCreation:
    """Test task creation edge cases."""
    
    def test_create_minimal_task(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create task with only required fields."""
        response = api_client.post(
            "/api/v1/tasks",
            json={"title": "Minimal task"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"] == "Minimal task"
        assert data["status"] == "pending"
        assert data["priority"] == "medium"  # Default
    
    def test_create_task_with_all_fields(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create task with all optional fields."""
        today = date.today()
        due_date = (today + timedelta(days=7)).isoformat()
        
        response = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Complete task",
                "description": "Detailed description",
                "priority": "high",
                "due_date": due_date,
                "estimated_effort_minutes": 120
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"] == "Complete task"
        assert data["description"] == "Detailed description"
        assert data["priority"] == "high"
        assert data["due_date"] == due_date
        assert data["estimated_effort_minutes"] == 120
    
    def test_create_task_from_thought(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create task linked to source thought."""
        # Create thought first
        thought_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Need to build feature X"},
            headers=auth_headers
        )
        thought_id = thought_resp.json()["data"]["id"]
        
        # Create task from thought
        task_resp = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Build feature X",
                "source_thought_id": thought_id,
                "priority": "high"
            },
            headers=auth_headers
        )
        
        assert task_resp.status_code == 201
        data = task_resp.json()["data"]
        assert data["source_thought_id"] == thought_id
    
    def test_create_task_with_invalid_thought_id_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Create task with non-existent thought ID fails."""
        fake_thought_id = str(uuid4())
        response = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Task",
                "source_thought_id": fake_thought_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404
        error = response.json()["error"]
        assert "not found" in error["message"].lower()
    
    def test_create_task_with_empty_title_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Empty title is rejected."""
        response = api_client.post(
            "/api/v1/tasks",
            json={"title": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_create_task_with_invalid_priority_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Invalid priority value rejected."""
        response = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Task",
                "priority": "super_ultra_high"  # Invalid
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestTaskRetrieval:
    """Test task retrieval functionality."""
    
    def test_get_task_by_id(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Retrieve task by exact ID."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Findable task"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        get_resp = api_client.get(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == task_id
    
    def test_get_nonexistent_task_returns_404(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Non-existent task ID returns 404."""
        fake_id = str(uuid4())
        response = api_client.get(
            f"/api/v1/tasks/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_list_tasks_default_params(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """List tasks with default parameters."""
        response = api_client.get(
            "/api/v1/tasks",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "tasks" in data
        assert "pagination" in data
    
    def test_list_tasks_filter_by_status(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Filter tasks by status."""
        # Create tasks with different statuses
        api_client.post(
            "/api/v1/tasks",
            json={"title": "Pending task"},
            headers=auth_headers
        )
        
        # Create and complete a task
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "To complete"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        api_client.post(
            f"/api/v1/tasks/{task_id}/complete",
            headers=auth_headers
        )
        
        # Filter by done status
        response = api_client.get(
            "/api/v1/tasks?status=done",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        tasks = response.json()["data"]["tasks"]
        assert all(t["status"] == "done" for t in tasks)
    
    def test_list_tasks_filter_by_priority(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Filter tasks by priority."""
        # Create tasks with different priorities
        api_client.post(
            "/api/v1/tasks",
            json={"title": "Critical task", "priority": "critical"},
            headers=auth_headers
        )
        api_client.post(
            "/api/v1/tasks",
            json={"title": "Low task", "priority": "low"},
            headers=auth_headers
        )
        
        # Filter by critical
        response = api_client.get(
            "/api/v1/tasks?priority=critical",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        tasks = response.json()["data"]["tasks"]
        assert all(t["priority"] == "critical" for t in tasks)
    
    def test_list_tasks_pagination(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """List tasks with pagination."""
        # Create 15 tasks
        for i in range(15):
            api_client.post(
                "/api/v1/tasks",
                json={"title": f"Task {i}"},
                headers=auth_headers
            )
        
        # Get first page
        response = api_client.get(
            "/api/v1/tasks?limit=5&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["tasks"]) <= 5
        assert data["pagination"]["has_more"] is True


@pytest.mark.integration
class TestTaskUpdate:
    """Test task update functionality."""
    
    def test_update_title(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update task title."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Original title"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        update_resp = api_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"title": "Updated title"},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["title"] == "Updated title"
    
    def test_update_priority(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update task priority."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Task", "priority": "low"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        update_resp = api_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"priority": "critical"},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["priority"] == "critical"
    
    def test_update_status(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update task status."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Task"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        update_resp = api_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["status"] == "in_progress"
    
    def test_update_due_date(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update task due date."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Task"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        new_due_date = (date.today() + timedelta(days=14)).isoformat()
        update_resp = api_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"due_date": new_due_date},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["due_date"] == new_due_date
    
    def test_update_partial_fields(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Update only some fields, others unchanged."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Original",
                "priority": "low",
                "description": "Original description"
            },
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        # Update only priority
        update_resp = api_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"priority": "high"},
            headers=auth_headers
        )
        
        data = update_resp.json()["data"]
        assert data["priority"] == "high"
        assert data["title"] == "Original"  # Unchanged
        assert data["description"] == "Original description"  # Unchanged


@pytest.mark.integration
class TestTaskCompletion:
    """Test task completion functionality."""
    
    def test_complete_task(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Complete task sets status to done."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "To complete"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        complete_resp = api_client.post(
            f"/api/v1/tasks/{task_id}/complete",
            headers=auth_headers
        )
        
        assert complete_resp.status_code == 200
        data = complete_resp.json()["data"]
        assert data["status"] == "done"
        assert data["completed_at"] is not None
    
    def test_complete_nonexistent_task_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Complete non-existent task returns 404."""
        fake_id = str(uuid4())
        response = api_client.post(
            f"/api/v1/tasks/{fake_id}/complete",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_complete_already_completed_task(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Completing already completed task succeeds."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Task"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        # Complete once
        api_client.post(
            f"/api/v1/tasks/{task_id}/complete",
            headers=auth_headers
        )
        
        # Complete again
        complete_resp2 = api_client.post(
            f"/api/v1/tasks/{task_id}/complete",
            headers=auth_headers
        )
        
        assert complete_resp2.status_code == 200
        assert complete_resp2.json()["data"]["status"] == "done"


@pytest.mark.integration
class TestTaskDeletion:
    """Test task deletion functionality."""
    
    def test_delete_task(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Delete task returns 204."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "To delete"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        delete_resp = api_client.delete(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        
        assert delete_resp.status_code == 204
    
    def test_delete_nonexistent_task_fails(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Delete non-existent task returns 404."""
        fake_id = str(uuid4())
        response = api_client.delete(
            f"/api/v1/tasks/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_deleted_task_not_in_list(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Deleted task doesn't appear in list."""
        create_resp = api_client.post(
            "/api/v1/tasks",
            json={"title": "Will be deleted"},
            headers=auth_headers
        )
        task_id = create_resp.json()["data"]["id"]
        
        api_client.delete(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        
        # List tasks
        list_resp = api_client.get(
            "/api/v1/tasks",
            headers=auth_headers
        )
        
        tasks = list_resp.json()["data"]["tasks"]
        task_ids = [t["id"] for t in tasks]
        assert task_id not in task_ids


@pytest.mark.integration
class TestTaskThoughtRelationship:
    """Test relationship between tasks and thoughts."""
    
    def test_task_links_to_source_thought(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Task maintains link to source thought."""
        # Create thought
        thought_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Need to do something"},
            headers=auth_headers
        )
        thought_id = thought_resp.json()["data"]["id"]
        
        # Create task from thought
        task_resp = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Do the thing",
                "source_thought_id": thought_id
            },
            headers=auth_headers
        )
        
        # Verify link
        task_data = task_resp.json()["data"]
        assert task_data["source_thought_id"] == thought_id
        
        # Retrieve task and verify link persists
        get_resp = api_client.get(
            f"/api/v1/tasks/{task_data['id']}",
            headers=auth_headers
        )
        assert get_resp.json()["data"]["source_thought_id"] == thought_id
    
    def test_deleting_thought_clears_task_link(
        self, 
        api_client: TestClient, 
        auth_headers: dict
    ):
        """Deleting source thought clears task's source_thought_id."""
        # Create thought
        thought_resp = api_client.post(
            "/api/v1/thoughts",
            json={"content": "Temporary thought"},
            headers=auth_headers
        )
        thought_id = thought_resp.json()["data"]["id"]
        
        # Create task from thought
        task_resp = api_client.post(
            "/api/v1/tasks",
            json={
                "title": "Task from thought",
                "source_thought_id": thought_id
            },
            headers=auth_headers
        )
        task_id = task_resp.json()["data"]["id"]
        
        # Delete thought
        api_client.delete(
            f"/api/v1/thoughts/{thought_id}",
            headers=auth_headers
        )
        
        # Verify task still exists but link is cleared
        get_resp = api_client.get(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["source_thought_id"] is None
