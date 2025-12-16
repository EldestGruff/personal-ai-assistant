"""
Backend Orchestrator

Executes backend selection decisions with automatic fallback.

Takes selector decisions and implements the execution logic:
primary → fallback on recoverable errors, fail fast on non-recoverable.
"""

import logging
from typing import Union

from src.services.ai_backends import (
    AIBackendRegistry,
    BackendRequest,
    SuccessResponse,
    ErrorResponse,
)
from src.services.backend_selection.models import (
    BackendSelectionRequest,
    BackendChoice,
)
from src.services.backend_selection.base import BackendSelector


logger = logging.getLogger(__name__)


class BackendOrchestrator:
    """
    Orchestrates backend execution with automatic fallback.
    
    Responsibilities:
    1. Ask selector which backends to use
    2. Execute primary backend
    3. Automatically fallback on recoverable errors
    4. Fail fast on non-recoverable errors
    5. Log all decisions for observability
    
    Error Classification:
    - Recoverable (try fallback): RATE_LIMITED, UNAVAILABLE, TIMEOUT,
      INTERNAL_ERROR, MALFORMED_RESPONSE
    - Non-recoverable (fail fast): INVALID_INPUT, CONTEXT_OVERFLOW
    
    Example:
        registry = AIBackendRegistry()
        registry.register("claude", ClaudeBackend())
        registry.register("ollama", OllamaBackend())
        
        config = BackendConfig.from_env()
        selector = DefaultSelector(config)
        
        orchestrator = BackendOrchestrator(registry, selector)
        
        # Analyze with automatic fallback
        response = await orchestrator.analyze_with_fallback(
            request=backend_request,
            thought_length=150
        )
    """
    
    # Errors that should trigger fallback
    RECOVERABLE_ERRORS = {
        "RATE_LIMITED",
        "UNAVAILABLE",
        "TIMEOUT",
        "INTERNAL_ERROR",
        "MALFORMED_RESPONSE",
    }
    
    # Errors that should fail immediately (don't retry)
    NON_RECOVERABLE_ERRORS = {
        "INVALID_INPUT",
        "CONTEXT_OVERFLOW",
    }
    
    def __init__(
        self,
        registry: AIBackendRegistry,
        selector: BackendSelector
    ):
        """
        Initialize orchestrator.
        
        Args:
            registry: Backend registry with available backends
            selector: Backend selector for decision-making
        """
        self.registry = registry
        self.selector = selector
    
    async def analyze_with_fallback(
        self,
        request: BackendRequest,
        thought_length: int,
        analysis_type: str = "standard"
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Analyze using selector logic with automatic fallback.
        
        This is the main entry point for analysis with intelligent
        backend selection and automatic retry on recoverable failures.
        
        Args:
            request: Backend request with thought to analyze
            thought_length: Length of thought (for selection)
            analysis_type: Type of analysis ("standard", "deep", "quick")
        
        Returns:
            Union[SuccessResponse, ErrorResponse]: Analysis result
        
        Example:
            request = BackendRequest(
                request_id="req-123",
                thought_content="Should optimize email system",
                timeout_seconds=30
            )
            
            response = await orchestrator.analyze_with_fallback(
                request=request,
                thought_length=len(request.thought_content)
            )
            
            if response.success:
                print(response.analysis.summary)
            else:
                print(response.error.error_message)
        """
        # Get selection decision
        available = self.registry.list_available()
        selection = await self._get_selection_decision(
            request.request_id,
            thought_length,
            analysis_type,
            available
        )
        
        logger.info(
            f"[{request.request_id}] Selection decision: "
            f"{selection.decision_type} - {selection.reasoning}"
        )
        
        # Try primary backend(s)
        for choice in selection.backends:
            result = await self._try_backend(choice, request)
            
            if result.success:
                logger.info(
                    f"[{request.request_id}] SUCCESS with primary "
                    f"backend '{choice.name}'"
                )
                return result
            
            # Check if error is recoverable
            if not self._is_recoverable_error(result):
                logger.warning(
                    f"[{request.request_id}] Non-recoverable error "
                    f"from '{choice.name}': {result.error.error_code}. "
                    f"Failing without retry."
                )
                return result
            
            logger.warning(
                f"[{request.request_id}] Recoverable error from "
                f"'{choice.name}': {result.error.error_code}. "
                f"Will try fallback."
            )
        
        # Try fallback backend(s)
        for choice in selection.fallback_backends:
            result = await self._try_backend(choice, request)
            
            if result.success:
                logger.info(
                    f"[{request.request_id}] SUCCESS with fallback "
                    f"backend '{choice.name}'"
                )
                return result
            
            logger.warning(
                f"[{request.request_id}] Fallback backend "
                f"'{choice.name}' failed: {result.error.error_code}"
            )
        
        # All backends failed
        logger.error(
            f"[{request.request_id}] All backends failed. "
            f"Primary: {[c.name for c in selection.backends]}, "
            f"Fallback: {[c.name for c in selection.fallback_backends]}"
        )
        
        # Return last error encountered
        return result
    
    async def _get_selection_decision(
        self,
        request_id: str,
        thought_length: int,
        analysis_type: str,
        available_backends: list[str]
    ):
        """
        Get backend selection decision from selector.
        
        Args:
            request_id: Request identifier
            thought_length: Length of thought
            analysis_type: Type of analysis
            available_backends: Available backend names
        
        Returns:
            BackendSelectionResponse: Selection decision
        """
        selection_request = BackendSelectionRequest(
            request_id=request_id,
            thought_length=thought_length,
            analysis_type=analysis_type,
            available_backends=available_backends
        )
        
        return await self.selector.select_backends(selection_request)
    
    async def _try_backend(
        self,
        choice: BackendChoice,
        request: BackendRequest
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Try executing request on a specific backend.
        
        Args:
            choice: Backend choice with config
            request: Backend request
        
        Returns:
            Union[SuccessResponse, ErrorResponse]: Result
        """
        backend = self.registry.get(choice.name)
        
        # Update timeout from choice
        request.timeout_seconds = choice.timeout_seconds
        
        logger.info(
            f"[{request.request_id}] Trying backend '{choice.name}' "
            f"(role={choice.role}, timeout={choice.timeout_seconds}s)"
        )
        
        return await backend.analyze(request)
    
    def _is_recoverable_error(
        self,
        response: ErrorResponse
    ) -> bool:
        """
        Determine if error is recoverable (should try fallback).
        
        Args:
            response: Error response
        
        Returns:
            bool: True if error is recoverable
        """
        error_code = response.error.error_code
        return error_code in self.RECOVERABLE_ERRORS
