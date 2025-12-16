"""
ThoughtAnalyzer - High-level thought analysis using pluggable backends.

Uses BackendOrchestrator to analyze thoughts with automatic fallback
between backends (Claude → Ollama → Mock).

This is the main entry point for thought analysis, abstracting away
backend selection and error handling details.
"""

import logging
from typing import Union
from uuid import uuid4

from ..services.backend_selection.orchestrator import BackendOrchestrator
from ..services.ai_backends.models import BackendRequest, SuccessResponse, ErrorResponse
from ..models.thought import ThoughtResponse

logger = logging.getLogger(__name__)


class ThoughtAnalyzer:
    """
    High-level thought analysis service using pluggable backends.
    
    Analyzes thoughts using BackendOrchestrator which handles:
    - Backend selection (which backend to use)
    - Automatic fallback (primary fails → try secondary)
    - Error handling and retry logic
    - Metrics collection
    
    Example:
        orchestrator = BackendOrchestrator(registry, selector)
        analyzer = ThoughtAnalyzer(orchestrator)
        
        response = await analyzer.analyze(thought)
        if response.success:
            print(response.analysis.summary)
        else:
            print(response.error.error_message)
    """
    
    def __init__(self, orchestrator: BackendOrchestrator):
        """
        Initialize analyzer with backend orchestrator.
        
        Args:
            orchestrator: BackendOrchestrator that handles backend
                         selection and fallback
        """
        self.orchestrator = orchestrator
        logger.info("ThoughtAnalyzer initialized with orchestrator")
    
    async def analyze(
        self,
        thought: ThoughtResponse
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Analyze a thought using orchestrator with automatic fallback.
        
        The orchestrator will:
        1. Select primary backend based on configuration
        2. Try to analyze using primary
        3. If primary fails with recoverable error, try fallback
        4. Return result or final error
        
        Args:
            thought: Thought to analyze
        
        Returns:
            SuccessResponse if analysis succeeded (from any backend)
            ErrorResponse if all backends failed
        
        Example:
            thought = ThoughtResponse(
                id="123",
                content="Should improve email system",
                user_id="user-456"
            )
            
            response = await analyzer.analyze(thought)
            
            if response.success:
                print(f"Summary: {response.analysis.summary}")
                print(f"Backend: {response.analysis.backend_used}")
            else:
                print(f"Error: {response.error.error_message}")
        """
        # Create backend request
        request = BackendRequest(
            request_id=str(uuid4()),
            thought_content=thought.content,
            context={
                "user_id": str(thought.user_id),
                "thought_id": str(thought.id),
                "tags": thought.tags
            },
            timeout_seconds=30
        )
        
        logger.info(
            f"Analyzing thought {thought.id} "
            f"(length: {len(thought.content)} chars)"
        )
        
        # Orchestrator handles backend selection + fallback
        response = await self.orchestrator.analyze_with_fallback(
            request=request,
            thought_length=len(thought.content)
        )
        
        if response.success:
            logger.info(
                f"Analysis succeeded: thought={thought.id}, "
                f"backend={response.analysis.backend_used}"
            )
        else:
            logger.warning(
                f"Analysis failed: thought={thought.id}, "
                f"error={response.error.error_code}"
            )
        
        return response
    
    async def analyze_batch(
        self,
        thoughts: list[ThoughtResponse]
    ) -> list[Union[SuccessResponse, ErrorResponse]]:
        """
        Analyze multiple thoughts in sequence.
        
        Each thought is analyzed independently. If one fails,
        others still proceed.
        
        Args:
            thoughts: List of thoughts to analyze
        
        Returns:
            List of responses (SuccessResponse or ErrorResponse)
        
        Note:
            This is currently sequential. For parallel processing,
            use asyncio.gather() at the caller level.
        """
        logger.info(f"Starting batch analysis of {len(thoughts)} thoughts")
        
        results = []
        for thought in thoughts:
            result = await self.analyze(thought)
            results.append(result)
        
        successes = sum(1 for r in results if r.success)
        failures = len(results) - successes
        
        logger.info(
            f"Batch analysis complete: "
            f"{successes} succeeded, {failures} failed"
        )
        
        return results
