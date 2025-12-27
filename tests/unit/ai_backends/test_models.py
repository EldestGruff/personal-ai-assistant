"""
Tests for AI backend request/response models.

Verifies Pydantic validation for all schemas,
ensuring data integrity at protocol boundaries.
"""

import pytest
from pydantic import ValidationError

from src.services.ai_backends.models import (
    BackendRequest,
    Theme,
    SuggestedAction,
    Analysis,
    AnalysisMetadata,
    SuccessResponse,
    ErrorDetails,
    ErrorResponse,
)


class TestBackendRequest:
    """Test BackendRequest validation"""
    
    def test_valid_minimal_request(self):
        """minimal valid request succeeds"""
        request = BackendRequest(
            request_id="req-123",
            thought_content="test thought"
        )
        
        assert request.request_id == "req-123"
        assert request.thought_content == "test thought"
        assert request.timeout_seconds == 30
        assert request.include_confidence is True
    
    def test_valid_full_request(self):
        """full valid request succeeds"""
        request = BackendRequest(
            request_id="req-456",
            thought_content="analyze this",
            context={"user_id": "abc123"},
            timeout_seconds=45,
            model_hint="quality",
            include_confidence=False
        )
        
        assert request.context == {"user_id": "abc123"}
        assert request.timeout_seconds == 45
        assert request.model_hint == "quality"
        assert request.include_confidence is False
    
    def test_content_too_short(self):
        """empty content rejected"""
        with pytest.raises(ValidationError):
            BackendRequest(
                request_id="req-789",
                thought_content=""
            )
    
    def test_content_too_long(self):
        """content >5000 chars rejected"""
        long_content = "x" * 5001
        with pytest.raises(ValidationError):
            BackendRequest(
                request_id="req-abc",
                thought_content=long_content
            )
    
    def test_whitespace_only_content(self):
        """whitespace-only content rejected"""
        with pytest.raises(ValidationError):
            BackendRequest(
                request_id="req-def",
                thought_content="   "
            )
    
    def test_content_strips_whitespace(self):
        """content whitespace trimmed"""
        request = BackendRequest(
            request_id="req-ghi",
            thought_content="  test  "
        )
        assert request.thought_content == "test"
    
    def test_timeout_too_low(self):
        """timeout <5 rejected"""
        with pytest.raises(ValidationError):
            BackendRequest(
                request_id="req-jkl",
                thought_content="test",
                timeout_seconds=3
            )
    
    def test_timeout_too_high(self):
        """timeout >300 rejected"""
        with pytest.raises(ValidationError):
            BackendRequest(
                request_id="req-mno",
                thought_content="test",
                timeout_seconds=301
            )
    
    def test_invalid_model_hint(self):
        """invalid model hint rejected"""
        with pytest.raises(ValidationError):
            BackendRequest(
                request_id="req-pqr",
                thought_content="test",
                model_hint="invalid"
            )
    
    def test_valid_model_hints(self):
        """valid model hints accepted"""
        for hint in ["fast", "quality", "cheap"]:
            request = BackendRequest(
                request_id="req-stu",
                thought_content="test",
                model_hint=hint
            )
            assert request.model_hint == hint


class TestTheme:
    """Test Theme validation"""
    
    def test_valid_theme(self):
        """valid theme succeeds"""
        theme = Theme(theme="test theme", confidence=0.85)
        assert theme.theme == "test theme"
        assert theme.confidence == 0.85
    
    def test_confidence_defaults(self):
        """confidence defaults to 1.0"""
        theme = Theme(theme="test")
        assert theme.confidence == 1.0
    
    def test_confidence_too_low(self):
        """confidence <0 rejected"""
        with pytest.raises(ValidationError):
            Theme(theme="test", confidence=-0.1)
    
    def test_confidence_too_high(self):
        """confidence >1 rejected"""
        with pytest.raises(ValidationError):
            Theme(theme="test", confidence=1.1)


class TestSuggestedAction:
    """Test SuggestedAction validation"""
    
    def test_valid_action(self):
        """valid action succeeds"""
        action = SuggestedAction(
            action="create task",
            priority="high",
            confidence=0.9
        )
        assert action.action == "create task"
        assert action.priority == "high"
        assert action.confidence == 0.9
    
    def test_priority_defaults(self):
        """priority defaults to medium"""
        action = SuggestedAction(action="test")
        assert action.priority == "medium"
    
    def test_invalid_priority(self):
        """invalid priority rejected"""
        with pytest.raises(ValidationError):
            SuggestedAction(action="test", priority="urgent")
    
    def test_valid_priorities(self):
        """valid priorities accepted"""
        for priority in ["low", "medium", "high", "critical"]:
            action = SuggestedAction(
                action="test",
                priority=priority
            )
            assert action.priority == priority


class TestAnalysis:
    """Test Analysis validation"""
    
    def test_valid_minimal_analysis(self):
        """minimal valid analysis succeeds"""
        analysis = Analysis(
            request_id="req-123",
            backend_used="mock",
            summary="test summary"
        )
        assert analysis.request_id == "req-123"
        assert analysis.backend_used == "mock"
        assert analysis.summary == "test summary"
        assert analysis.themes == []
        assert analysis.suggested_actions == []
    
    def test_valid_full_analysis(self):
        """full valid analysis succeeds"""
        analysis = Analysis(
            request_id="req-456",
            thought_id="thought-789",
            backend_used="claude",
            summary="full summary",
            themes=[Theme(theme="test")],
            suggested_actions=[SuggestedAction(action="test")],
            related_thought_ids=["id1", "id2"]
        )
        assert len(analysis.themes) == 1
        assert len(analysis.suggested_actions) == 1
        assert len(analysis.related_thought_ids) == 2


class TestSuccessResponse:
    """Test SuccessResponse validation"""
    
    def test_valid_success_response(self):
        """valid success response succeeds"""
        response = SuccessResponse(
            success=True,
            analysis=Analysis(
                request_id="req-123",
                backend_used="mock",
                summary="test"
            ),
            metadata=AnalysisMetadata(
                tokens_used=100,
                processing_time_ms=200,
                model_version="v1"
            )
        )
        assert response.success is True
        assert response.analysis is not None
        assert response.metadata is not None


class TestErrorResponse:
    """Test ErrorResponse validation"""
    
    def test_valid_error_response(self):
        """valid error response succeeds"""
        response = ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id="req-123",
                backend_name="mock",
                error_code="TIMEOUT",
                error_message="test timeout"
            )
        )
        assert response.success is False
        assert response.error.error_code == "TIMEOUT"
    
    def test_error_with_suggestion(self):
        """error with suggestion succeeds"""
        response = ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id="req-456",
                backend_name="mock",
                error_code="UNAVAILABLE",
                error_message="test error",
                suggestion="try again"
            )
        )
        assert response.error.suggestion == "try again"
