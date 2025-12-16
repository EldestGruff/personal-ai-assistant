"""
Claude backend implementation using Anthropic API.

Wraps existing ClaudeService to implement the standardized
AIBackend protocol. Maps Claude-specific responses and errors
to protocol-compliant formats.
"""

import logging
import asyncio
import time
from typing import Union
from datetime import datetime

from anthropic import (
    APIError as AnthropicAPIError,
    APITimeoutError,
    RateLimitError as AnthropicRateLimitError,
)

from src.services.claude_service import ClaudeService
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
from src.services.ai_backends.exceptions import (
    BackendTimeoutError,
    BackendUnavailableError,
    BackendRateLimitError,
    BackendInvalidInputError,
    BackendMalformedResponseError,
    BackendInternalError,
)


logger = logging.getLogger(__name__)


class ClaudeBackend:
    """
    Claude backend using Anthropic API.
    
    Implements AIBackend protocol by wrapping ClaudeService
    and standardizing all responses.
    
    Example:
        backend = ClaudeBackend()
        request = BackendRequest(
            request_id="req-123",
            thought_content="Should optimize email"
        )
        response = await backend.analyze(request)
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize Claude backend.
        
        Args:
            api_key: Anthropic API key (uses env var if not provided)
        """
        self._claude = ClaudeService(api_key=api_key)
        self._name = "claude"
    
    @property
    def name(self) -> str:
        """Backend identifier"""
        return self._name
    
    async def analyze(
        self,
        request: BackendRequest
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Analyze thought using Claude API.
        
        Args:
            request: Standardized backend request
        
        Returns:
            SuccessResponse if successful
            ErrorResponse if failed
        """
        start_time = time.time()
        
        try:
            # Run analysis with timeout
            result = await asyncio.wait_for(
                self._run_analysis(request),
                timeout=request.timeout_seconds
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return self._build_success_response(
                request=request,
                result=result,
                processing_time_ms=processing_time_ms
            )
            
        except asyncio.TimeoutError:
            return self._build_timeout_error(request)
        
        except AnthropicRateLimitError as e:
            return self._build_rate_limit_error(request, e)
        
        except AnthropicAPIError as e:
            return self._build_api_error(request, e)
        
        except Exception as e:
            return self._build_internal_error(request, e)
    
    async def _run_analysis(
        self,
        request: BackendRequest
    ) -> dict:
        """
        Run Claude analysis in executor.
        
        Claude SDK is synchronous, so we run it in
        a thread pool to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._analyze_sync,
            request
        )
    
    def _analyze_sync(self, request: BackendRequest) -> dict:
        """
        Synchronous analysis call.
        
        Creates a temporary ThoughtDB-like object and calls
        ClaudeService.analyze_thought().
        """
        # Create minimal thought object for ClaudeService
        from src.models.thought import ThoughtDB
        
        thought = ThoughtDB(
            id="temp-id",
            user_id=request.context.get("user_id", "unknown"),
            content=request.thought_content,
            tags=[],
            status="active"
        )
        
        # Call existing ClaudeService
        return self._claude.analyze_thought(
            thought=thought,
            context_thoughts=None
        )
    
    def _build_success_response(
        self,
        request: BackendRequest,
        result: dict,
        processing_time_ms: int
    ) -> SuccessResponse:
        """Build standardized success response"""
        # Extract themes
        themes = [
            Theme(theme=t, confidence=0.8)
            for t in result.get("related_themes", [])
        ]
        
        # Extract suggested actions
        actions = []
        if result.get("is_actionable") and result.get("action_suggestion"):
            actions.append(
                SuggestedAction(
                    action=result["action_suggestion"],
                    priority="medium",
                    confidence=0.7
                )
            )
        
        analysis = Analysis(
            request_id=request.request_id,
            backend_used=self.name,
            summary=result.get("summary", "Analysis completed"),
            themes=themes,
            suggested_actions=actions,
            related_thought_ids=[]
        )
        
        metadata = AnalysisMetadata(
            tokens_used=result.get("tokens_used", 0),
            processing_time_ms=processing_time_ms,
            model_version=self._claude.model,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return SuccessResponse(
            success=True,
            analysis=analysis,
            metadata=metadata
        )
    
    def _build_timeout_error(
        self,
        request: BackendRequest
    ) -> ErrorResponse:
        """Build timeout error response"""
        return ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id=request.request_id,
                backend_name=self.name,
                error_code="TIMEOUT",
                error_message=f"Analysis exceeded {request.timeout_seconds}s",
                suggestion="Retry with longer timeout"
            )
        )
    
    def _build_rate_limit_error(
        self,
        request: BackendRequest,
        exc: AnthropicRateLimitError
    ) -> ErrorResponse:
        """Build rate limit error response"""
        return ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id=request.request_id,
                backend_name=self.name,
                error_code="RATE_LIMITED",
                error_message=str(exc),
                suggestion="Retry after a few seconds or use fallback backend"
            )
        )
    
    def _build_api_error(
        self,
        request: BackendRequest,
        exc: AnthropicAPIError
    ) -> ErrorResponse:
        """Build API error response"""
        return ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id=request.request_id,
                backend_name=self.name,
                error_code="UNAVAILABLE",
                error_message=f"Claude API error: {str(exc)}",
                suggestion="Check API status or use fallback backend"
            )
        )
    
    def _build_internal_error(
        self,
        request: BackendRequest,
        exc: Exception
    ) -> ErrorResponse:
        """Build internal error response"""
        logger.error(f"Internal error in ClaudeBackend: {exc}")
        
        return ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id=request.request_id,
                backend_name=self.name,
                error_code="INTERNAL_ERROR",
                error_message=f"Unexpected error: {str(exc)}",
                suggestion="Check logs for details"
            )
        )
    
    async def health_check(self) -> bool:
        """
        Check if Claude API is reachable.
        
        Returns:
            bool: True if healthy
        """
        try:
            # Quick test: check if client is initialized
            if not self._claude or not self._claude.client:
                return False
            
            # Could optionally make a minimal API call here
            # For now, just check initialization
            return True
            
        except Exception:
            return False
