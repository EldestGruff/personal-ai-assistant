"""
Tests for error handling paths to improve coverage.

These tests target specific error branches in routes and services
that aren't covered by happy-path tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from src.services.exceptions import (
    NotFoundError, DatabaseError, InvalidDataError, ConflictError
)


class TestThoughtRouteErrors:
    """Test error handling in thought routes."""
    
    def test_create_thought_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during creation returns 500."""
        with patch('src.api.routes.thoughts.ThoughtService') as mock:
            mock.return_value.create_thought.side_effect = DatabaseError(
                "Connection failed"
            )
            response = api_client.post(
                "/api/v1/thoughts",
                json={"content": "Test thought", "tags": []},
                headers=auth_headers
            )
            assert response.status_code == 500
            assert "DATABASE_ERROR" in response.text

    def test_create_thought_invalid_data_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """InvalidDataError during creation returns 400."""
        with patch('src.api.routes.thoughts.ThoughtService') as mock:
            mock.return_value.create_thought.side_effect = InvalidDataError(
                "Content too long"
            )
            response = api_client.post(
                "/api/v1/thoughts",
                json={"content": "Test", "tags": []},
                headers=auth_headers
            )
            assert response.status_code == 400

    def test_get_thought_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during get returns 500."""
        thought_id = str(uuid4())
        with patch('src.api.routes.thoughts.ThoughtService') as mock:
            mock.return_value.get_thought.side_effect = DatabaseError(
                "Query failed"
            )
            response = api_client.get(
                f"/api/v1/thoughts/{thought_id}",
                headers=auth_headers
            )
            assert response.status_code == 500

    def test_update_thought_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during update returns 500."""
        thought_id = str(uuid4())
        with patch('src.api.routes.thoughts.ThoughtService') as mock:
            mock.return_value.update_thought.side_effect = DatabaseError(
                "Update failed"
            )
            response = api_client.put(
                f"/api/v1/thoughts/{thought_id}",
                json={"content": "Updated"},
                headers=auth_headers
            )
            assert response.status_code == 500

    def test_delete_thought_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during delete returns 500."""
        thought_id = str(uuid4())
        with patch('src.api.routes.thoughts.ThoughtService') as mock:
            mock.return_value.delete_thought.side_effect = DatabaseError(
                "Delete failed"
            )
            response = api_client.delete(
                f"/api/v1/thoughts/{thought_id}",
                headers=auth_headers
            )
            assert response.status_code == 500

    def test_list_thoughts_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during list returns 500."""
        with patch('src.api.routes.thoughts.ThoughtService') as mock:
            mock.return_value.list_thoughts.side_effect = DatabaseError(
                "List failed"
            )
            response = api_client.get(
                "/api/v1/thoughts",
                headers=auth_headers
            )
            assert response.status_code == 500

    def test_search_thoughts_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during search returns 500."""
        with patch('src.api.routes.thoughts.ThoughtService') as mock:
            mock.return_value.search_thoughts.side_effect = DatabaseError(
                "Search failed"
            )
            response = api_client.get(
                "/api/v1/thoughts/search?q=test",
                headers=auth_headers
            )
            assert response.status_code == 500


class TestTaskRouteErrors:
    """Test error handling in task routes."""
    
    def test_create_task_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during task creation returns 500."""
        with patch('src.api.routes.tasks.TaskService') as mock:
            mock.return_value.create_task.side_effect = DatabaseError(
                "Connection failed"
            )
            response = api_client.post(
                "/api/v1/tasks",
                json={"title": "Test task"},
                headers=auth_headers
            )
            assert response.status_code == 500

    def test_get_task_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during get returns 500."""
        task_id = str(uuid4())
        with patch('src.api.routes.tasks.TaskService') as mock:
            mock.return_value.get_task.side_effect = DatabaseError(
                "Query failed"
            )
            response = api_client.get(
                f"/api/v1/tasks/{task_id}",
                headers=auth_headers
            )
            assert response.status_code == 500

    def test_update_task_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during update returns 500."""
        task_id = str(uuid4())
        with patch('src.api.routes.tasks.TaskService') as mock:
            mock.return_value.update_task.side_effect = DatabaseError(
                "Update failed"
            )
            response = api_client.put(
                f"/api/v1/tasks/{task_id}",
                json={"title": "Updated"},
                headers=auth_headers
            )
            assert response.status_code == 500

    def test_delete_task_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during delete returns 500."""
        task_id = str(uuid4())
        with patch('src.api.routes.tasks.TaskService') as mock:
            mock.return_value.delete_task.side_effect = DatabaseError(
                "Delete failed"
            )
            response = api_client.delete(
                f"/api/v1/tasks/{task_id}",
                headers=auth_headers
            )
            assert response.status_code == 500

    def test_list_tasks_database_error(
        self, api_client: TestClient, auth_headers: dict
    ):
        """DatabaseError during list returns 500."""
        with patch('src.api.routes.tasks.TaskService') as mock:
            mock.return_value.list_tasks.side_effect = DatabaseError(
                "List failed"
            )
            response = api_client.get(
                "/api/v1/tasks",
                headers=auth_headers
            )
            assert response.status_code == 500


class TestServiceExceptions:
    """Test service exception coverage."""
    
    def test_conflict_error_with_field(self):
        """ConflictError stores conflicting field."""
        error = ConflictError("Duplicate entry", conflicting_field="email")
        assert error.conflicting_field == "email"
        assert "Duplicate entry" in str(error)

    def test_conflict_error_without_field(self):
        """ConflictError works without field."""
        error = ConflictError("General conflict")
        assert error.conflicting_field is None
        assert "General conflict" in str(error)

    def test_database_error_with_original(self):
        """DatabaseError stores original exception."""
        original = ValueError("Original error")
        error = DatabaseError("Wrapped error", original_error=original)
        assert error.original_error is original
        assert "Wrapped error" in str(error)

    def test_database_error_without_original(self):
        """DatabaseError works without original exception."""
        error = DatabaseError("Simple error")
        assert error.original_error is None
