"""
Pytest configuration and shared fixtures for Personal AI Assistant tests.

Provides database fixtures, API client, and common test utilities.
All fixtures use isolated test databases to ensure test independence.
"""

import os
from typing import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.database.session import get_db
from src.models.base import Base, utc_now
from src.models.enums import ThoughtStatus, TaskStatus, Priority
from src.models.user import UserDB


# Use in-memory SQLite for tests (isolated, fast)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """
    Create a test database engine with in-memory SQLite.
    
    Creates a fresh database for each test function to ensure isolation.
    Uses StaticPool to maintain the in-memory database across connections.
    
    Yields:
        Engine: SQLAlchemy engine connected to in-memory database
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Keep in-memory DB alive across connections
        echo=False,  # Set to True for SQL debugging
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Disable foreign keys before dropping tables to avoid constraint violations
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.commit()
    
    # Clean up: drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_session_factory(test_engine):
    """
    Create a session factory for test database.
    
    Args:
        test_engine: Test database engine fixture
        
    Returns:
        sessionmaker: Factory for creating test sessions
    """
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )


@pytest.fixture(scope="function")
def db_session(test_session_factory) -> Generator[Session, None, None]:
    """
    Provide a clean database session for each test.
    
    Creates a new session, yields it for the test, then rolls back
    any changes and closes the session. This ensures test isolation.
    
    Args:
        test_session_factory: Session factory fixture
        
    Yields:
        Session: Database session for testing
        
    Example:
        >>> def test_create_thought(db_session):
        ...     thought = ThoughtDB(content="Test thought")
        ...     db_session.add(thought)
        ...     db_session.commit()
        ...     assert db_session.query(ThoughtDB).count() == 1
    """
    session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()  # Rollback any uncommitted changes
        session.close()


@pytest.fixture(scope="function")
def api_client(db_session) -> TestClient:
    """
    Provide a FastAPI TestClient with test database.
    
    Overrides the get_db dependency to use the test database session
    instead of the production database.
    
    Args:
        db_session: Test database session
        
    Returns:
        TestClient: FastAPI test client for making API requests
        
    Example:
        >>> def test_health_endpoint(api_client):
        ...     response = api_client.get("/api/v1/health")
        ...     assert response.status_code == 200
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def test_api_key() -> str:
    """
    Provide a test API key for authenticated requests.
    
    Returns:
        str: Valid test API key (UUID format)
        
    Note: In real tests, this would need to be in the api_keys table.
          For now, it's just a valid UUID format for testing auth middleware.
    """
    return str(uuid4())


@pytest.fixture
def auth_headers(test_api_key) -> dict:
    """
    Provide authorization headers for API requests.
    
    Args:
        test_api_key: Test API key fixture
        
    Returns:
        dict: Headers dictionary with Authorization bearer token
        
    Example:
        >>> def test_create_thought(api_client, auth_headers):
        ...     response = api_client.post(
        ...         "/api/v1/thoughts",
        ...         json={"content": "Test"},
        ...         headers=auth_headers
        ...     )
        ...     assert response.status_code == 201
    """
    return {
        "Authorization": f"Bearer {test_api_key}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_user_data() -> dict:
    """
    Provide sample user data for testing.
    
    Returns:
        dict: Valid user data for creating test users
    """
    return {
        "id": str(uuid4()),
        "name": "Test User",
        "email": "test@example.com",
        "preferences": {
            "timezone": "America/New_York",
            "max_thoughts_goal": 20
        },
        "is_active": True,
        "created_at": utc_now(),
        "updated_at": utc_now()
    }


@pytest.fixture
def sample_user(db_session) -> UserDB:
    """
    Create and persist a sample user in the test database.
    
    Args:
        db_session: Test database session
        
    Returns:
        UserDB: Created user object with ID
        
    Example:
        >>> def test_thought_creation(db_session, sample_user):
        ...     thought = ThoughtDB(user_id=sample_user.id, content="Test")
        ...     db_session.add(thought)
        ...     db_session.commit()
    """
    user = UserDB(
        id=str(uuid4()),
        name="Test User",
        email=f"test_{uuid4()}@example.com",  # Unique email per test
        preferences={
            "timezone": "America/New_York",
            "max_thoughts_goal": 20
        },
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_thought_data() -> dict:
    """
    Provide sample thought data for testing.
    
    Returns:
        dict: Valid thought data for creating test thoughts
    """
    return {
        "content": "This is a test thought about testing",
        "tags": ["test", "development"],
        "context": {
            "active_app": "VSCode",
            "time_of_day": "afternoon"
        }
    }


@pytest.fixture
def sample_task_data() -> dict:
    """
    Provide sample task data for testing.
    
    Returns:
        dict: Valid task data for creating test tasks
    """
    return {
        "title": "Test Task",
        "description": "A test task for testing",
        "priority": Priority.MEDIUM.value,
        "status": TaskStatus.PENDING.value
    }


# Test utility functions

def assert_valid_uuid(value: str) -> None:
    """
    Assert that a string is a valid UUID.
    
    Args:
        value: String to validate
        
    Raises:
        AssertionError: If value is not a valid UUID
    """
    from uuid import UUID
    try:
        UUID(value)
    except (ValueError, AttributeError):
        pytest.fail(f"'{value}' is not a valid UUID")


def assert_valid_timestamp(value: str) -> None:
    """
    Assert that a string is a valid ISO 8601 timestamp.
    
    Args:
        value: String to validate
        
    Raises:
        AssertionError: If value is not a valid ISO timestamp
    """
    from datetime import datetime
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        pytest.fail(f"'{value}' is not a valid ISO 8601 timestamp")


def assert_response_success(response) -> dict:
    """
    Assert that an API response indicates success and return data.
    
    Args:
        response: FastAPI test client response
        
    Returns:
        dict: Response data from successful response
        
    Raises:
        AssertionError: If response indicates failure
    """
    assert response.status_code in [200, 201, 204], \
        f"Expected success status code, got {response.status_code}"
    
    if response.status_code != 204:  # No content
        data = response.json()
        assert data.get("success") is True, \
            f"Expected success=true, got {data.get('success')}"
        return data.get("data")
    
    return {}


def assert_response_error(response, expected_code: int = None) -> dict:
    """
    Assert that an API response indicates an error.
    
    Args:
        response: FastAPI test client response
        expected_code: Expected HTTP status code (optional)
        
    Returns:
        dict: Error information from response
        
    Raises:
        AssertionError: If response indicates success
    """
    if expected_code:
        assert response.status_code == expected_code, \
            f"Expected status {expected_code}, got {response.status_code}"
    
    data = response.json()
    assert data.get("success") is False, \
        f"Expected success=false, got {data.get('success')}"
    assert "error" in data, "Expected error field in response"
    
    return data.get("error")
