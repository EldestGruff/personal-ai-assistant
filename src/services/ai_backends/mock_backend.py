"""
Mock backend for deterministic testing.

Provides canned responses without making any external API calls.
Different backend names return different types of responses,
enabling comprehensive error scenario testing.
"""

import time
from typing import Union
from datetime import datetime, UTC

from src.services.ai_backends.models import (
    BackendRequest,
    SuccessResponse,
    ErrorResponse,
    Analysis,
    AnalysisMetadata,
    ErrorDetails,
    Theme,
    SuggestedAction,
)


class MockBackend:
    """
    Mock backend for testing.
    
    Returns canned responses based on backend name.
    No external API calls, fully deterministic.
    
    Available modes (set via name):
    - "mock-success": Returns successful analysis
    - "mock-timeout": Returns timeout error
    - "mock-unavailable": Returns unavailable error
    - "mock-rate-limited": Returns rate limit error
    - "mock-malformed": Returns malformed response error
    
    Example:
        backend = MockBackend(mode="mock-success")
        response = await backend.analyze(request)
        assert response.success == True
    """
    
    def __init__(self, mode: str = "mock-success"):
        """
        Initialize mock backend.
        
        Args:
            mode: Response mode (see class docstring)
        """
        self._mode = mode
        self._name = mode
    
    @property
    def name(self) -> str:
        """Backend identifier"""
        return self._name
    
    async def analyze(
        self,
        request: BackendRequest
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Return canned response based on mode.
        
        Args:
            request: Standardized backend request
        
        Returns:
            SuccessResponse or ErrorResponse based on mode
        """
        # Simulate some processing time
        start_time = time.time()
        
        if self._mode == "mock-success":
            return self._mock_success(request, start_time)
        
        elif self._mode == "mock-timeout":
            return self._mock_timeout(request)
        
        elif self._mode == "mock-unavailable":
            return self._mock_unavailable(request)
        
        elif self._mode == "mock-rate-limited":
            return self._mock_rate_limited(request)
        
        elif self._mode == "mock-malformed":
            return self._mock_malformed(request)
        
        else:
            # Default to success
            return self._mock_success(request, start_time)
    
    def _mock_success(
        self,
        request: BackendRequest,
        start_time: float
    ) -> SuccessResponse:
        """Return successful analysis"""
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Generate deterministic response based on content
        content_lower = request.thought_content.lower()
        
        # Extract themes based on keywords
        themes = []
        if "email" in content_lower:
            themes.append(Theme(theme="email", confidence=0.95))
        if "optimize" in content_lower or "improve" in content_lower:
            themes.append(Theme(theme="optimization", confidence=0.90))
        if "task" in content_lower:
            themes.append(Theme(theme="task management", confidence=0.85))
        
        # Default theme if none detected
        if not themes:
            themes.append(Theme(theme="general", confidence=0.70))
        
        # Generate suggested actions
        actions = []
        if "should" in content_lower or "need to" in content_lower:
            actions.append(
                SuggestedAction(
                    action="Create task for this thought",
                    priority="medium",
                    confidence=0.80
                )
            )
        
        analysis = Analysis(
            request_id=request.request_id,
            backend_used=self.name,
            summary=f"Mock analysis: {request.thought_content[:50]}...",
            themes=themes,
            suggested_actions=actions,
            related_thought_ids=[]
        )
        
        metadata = AnalysisMetadata(
            tokens_used=100,
            processing_time_ms=processing_time_ms,
            model_version="mock-v1.0",
            timestamp=datetime.now(UTC).isoformat()
        )
        
        return SuccessResponse(
            success=True,
            analysis=analysis,
            metadata=metadata
        )
    
    def _mock_timeout(self, request: BackendRequest) -> ErrorResponse:
        """Return timeout error"""
        return ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id=request.request_id,
                backend_name=self.name,
                error_code="TIMEOUT",
                error_message=f"Mock timeout after {request.timeout_seconds}s",
                suggestion="This is a mock timeout for testing"
            )
        )
    
    def _mock_unavailable(
        self,
        request: BackendRequest
    ) -> ErrorResponse:
        """Return unavailable error"""
        return ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id=request.request_id,
                backend_name=self.name,
                error_code="UNAVAILABLE",
                error_message="Mock backend unavailable",
                suggestion="This is a mock unavailability for testing"
            )
        )
    
    def _mock_rate_limited(
        self,
        request: BackendRequest
    ) -> ErrorResponse:
        """Return rate limit error"""
        return ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id=request.request_id,
                backend_name=self.name,
                error_code="RATE_LIMITED",
                error_message="Mock rate limit exceeded",
                suggestion="Retry after 60s (mock)"
            )
        )
    
    def _mock_malformed(
        self,
        request: BackendRequest
    ) -> ErrorResponse:
        """Return malformed response error"""
        return ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id=request.request_id,
                backend_name=self.name,
                error_code="MALFORMED_RESPONSE",
                error_message="Mock malformed response",
                suggestion="This is a mock malformed response for testing"
            )
        )
    
    async def health_check(self) -> bool:
        """
        Always returns True for mock backend.
        
        Returns:
            bool: Always True
        """
        return True
