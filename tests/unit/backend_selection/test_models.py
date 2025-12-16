"""
Tests for Backend Selection Models

Validates Pydantic schemas for backend selection request/response.
"""

import pytest
from pydantic import ValidationError

from src.services.backend_selection.models import (
    BackendSelectionRequest,
    BackendChoice,
    BackendSelectionResponse,
)


class TestBackendSelectionRequest:
    """Test BackendSelectionRequest validation"""
    
    def test_valid_minimal_request(self):
        """Valid request with minimal fields"""
        request = BackendSelectionRequest(
            request_id="req-123",
            thought_length=100,
            available_backends=["claude"]
        )
        
        assert request.request_id == "req-123"
        assert request.thought_length == 100
        assert request.analysis_type == "standard"  # default
        assert request.available_backends == ["claude"]
        assert request.user_preferences is None  # default
    
    def test_valid_full_request(self):
        """Valid request with all fields"""
        request = BackendSelectionRequest(
            request_id="req-456",
            thought_length=500,
            analysis_type="deep",
            available_backends=["claude", "ollama"],
            user_preferences={"prefer_local": True}
        )
        
        assert request.request_id == "req-456"
        assert request.thought_length == 500
        assert request.analysis_type == "deep"
        assert len(request.available_backends) == 2
        assert request.user_preferences["prefer_local"] is True
    
    def test_thought_length_too_short(self):
        """Thought length must be >= 1"""
        with pytest.raises(ValidationError) as exc:
            BackendSelectionRequest(
                request_id="req-123",
                thought_length=0,
                available_backends=["claude"]
            )
        
        assert "thought_length" in str(exc.value)
    
    def test_thought_length_too_long(self):
        """Thought length must be <= 5000"""
        with pytest.raises(ValidationError) as exc:
            BackendSelectionRequest(
                request_id="req-123",
                thought_length=5001,
                available_backends=["claude"]
            )
        
        assert "thought_length" in str(exc.value)
    
    def test_invalid_analysis_type(self):
        """Analysis type must be valid"""
        with pytest.raises(ValidationError) as exc:
            BackendSelectionRequest(
                request_id="req-123",
                thought_length=100,
                analysis_type="invalid",
                available_backends=["claude"]
            )
        
        assert "analysis_type" in str(exc.value)
    
    def test_valid_analysis_types(self):
        """All valid analysis types should work"""
        for analysis_type in ["standard", "deep", "quick"]:
            request = BackendSelectionRequest(
                request_id="req-123",
                thought_length=100,
                analysis_type=analysis_type,
                available_backends=["claude"]
            )
            assert request.analysis_type == analysis_type
    
    def test_empty_backends_list(self):
        """Available backends cannot be empty"""
        with pytest.raises(ValidationError) as exc:
            BackendSelectionRequest(
                request_id="req-123",
                thought_length=100,
                available_backends=[]
            )
        
        assert "available_backends" in str(exc.value)


class TestBackendChoice:
    """Test BackendChoice validation"""
    
    def test_valid_choice(self):
        """Valid backend choice"""
        choice = BackendChoice(
            name="claude",
            role="primary",
            timeout_seconds=30
        )
        
        assert choice.name == "claude"
        assert choice.role == "primary"
        assert choice.timeout_seconds == 30
    
    def test_default_timeout(self):
        """Timeout defaults to 30"""
        choice = BackendChoice(
            name="ollama",
            role="fallback"
        )
        
        assert choice.timeout_seconds == 30
    
    def test_invalid_role(self):
        """Role must be valid"""
        with pytest.raises(ValidationError) as exc:
            BackendChoice(
                name="claude",
                role="invalid"
            )
        
        assert "role" in str(exc.value)
    
    def test_valid_roles(self):
        """All valid roles should work"""
        for role in ["primary", "fallback", "parallel"]:
            choice = BackendChoice(
                name="test",
                role=role
            )
            assert choice.role == role
    
    def test_timeout_too_low(self):
        """Timeout must be >= 5"""
        with pytest.raises(ValidationError) as exc:
            BackendChoice(
                name="claude",
                role="primary",
                timeout_seconds=4
            )
        
        assert "timeout_seconds" in str(exc.value)
    
    def test_timeout_too_high(self):
        """Timeout must be <= 60"""
        with pytest.raises(ValidationError) as exc:
            BackendChoice(
                name="claude",
                role="primary",
                timeout_seconds=61
            )
        
        assert "timeout_seconds" in str(exc.value)


class TestBackendSelectionResponse:
    """Test BackendSelectionResponse validation"""
    
    def test_valid_response(self):
        """Valid selection response"""
        response = BackendSelectionResponse(
            request_id="req-123",
            decision_type="SEQUENTIAL",
            backends=[
                BackendChoice(name="claude", role="primary")
            ],
            fallback_backends=[
                BackendChoice(name="ollama", role="fallback")
            ],
            reasoning="Claude primary, Ollama fallback per config"
        )
        
        assert response.request_id == "req-123"
        assert response.decision_type == "SEQUENTIAL"
        assert len(response.backends) == 1
        assert len(response.fallback_backends) == 1
        assert "Claude primary" in response.reasoning
        assert response.timestamp  # should be auto-generated
    
    def test_response_without_fallback(self):
        """Valid response with no fallback"""
        response = BackendSelectionResponse(
            request_id="req-123",
            decision_type="PRIMARY_ONLY",
            backends=[
                BackendChoice(name="claude", role="primary")
            ],
            reasoning="Only Claude available"
        )
        
        assert len(response.backends) == 1
        assert len(response.fallback_backends) == 0
    
    def test_invalid_decision_type(self):
        """Decision type must be valid"""
        with pytest.raises(ValidationError) as exc:
            BackendSelectionResponse(
                request_id="req-123",
                decision_type="INVALID",
                backends=[
                    BackendChoice(name="claude", role="primary")
                ],
                reasoning="test"
            )
        
        assert "decision_type" in str(exc.value)
    
    def test_valid_decision_types(self):
        """All valid decision types should work"""
        for decision_type in ["PRIMARY_ONLY", "SEQUENTIAL", "PARALLEL", "COST_OPTIMIZED"]:
            response = BackendSelectionResponse(
                request_id="req-123",
                decision_type=decision_type,
                backends=[
                    BackendChoice(name="test", role="primary")
                ],
                reasoning="test reasoning"
            )
            assert response.decision_type == decision_type
    
    def test_empty_backends_list(self):
        """Backends list cannot be empty"""
        with pytest.raises(ValidationError) as exc:
            BackendSelectionResponse(
                request_id="req-123",
                decision_type="SEQUENTIAL",
                backends=[],
                reasoning="test"
            )
        
        assert "backends" in str(exc.value)
    
    def test_reasoning_too_short(self):
        """Reasoning must be at least 10 characters"""
        with pytest.raises(ValidationError) as exc:
            BackendSelectionResponse(
                request_id="req-123",
                decision_type="SEQUENTIAL",
                backends=[
                    BackendChoice(name="claude", role="primary")
                ],
                reasoning="short"
            )
        
        assert "reasoning" in str(exc.value)
