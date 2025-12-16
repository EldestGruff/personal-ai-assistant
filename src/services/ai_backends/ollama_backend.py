"""
Ollama backend implementation for local LLM inference.

Connects to Ollama server at http://192.168.7.187:11434
for local, privacy-preserving thought analysis.
"""

import logging
import asyncio
import time
import json
from typing import Union
from datetime import datetime

import httpx

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
    BackendMalformedResponseError,
)


logger = logging.getLogger(__name__)


class OllamaBackend:
    """
    Ollama backend for local LLM inference.
    
    Connects to Ollama server for privacy-preserving
    thought analysis without external API calls.
    
    Example:
        backend = OllamaBackend(
            base_url="http://192.168.7.187:11434"
        )
        response = await backend.analyze(request)
    """
    
    def __init__(
        self,
        base_url: str = "http://192.168.7.187:11434",
        model: str = "gemma3:27b"
    ):
        """
        Initialize Ollama backend.
        
        Args:
            base_url: Ollama server URL
            model: Model to use (e.g., "gemma3:27b", "deepseek-r1:70b")
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._name = "ollama"
        self._chat_url = f"{self._base_url}/api/chat"
    
    @property
    def name(self) -> str:
        """Backend identifier"""
        return self._name
    
    async def analyze(
        self,
        request: BackendRequest
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Analyze thought using Ollama.
        
        Args:
            request: Standardized backend request
        
        Returns:
            SuccessResponse if successful
            ErrorResponse if failed
        """
        start_time = time.time()
        
        try:
            # Build prompt
            prompt = self._build_prompt(request.thought_content)
            
            # Call Ollama with timeout
            result = await asyncio.wait_for(
                self._call_ollama(prompt),
                timeout=request.timeout_seconds
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse response
            analysis_data = self._parse_response(result)
            
            return self._build_success_response(
                request=request,
                analysis_data=analysis_data,
                processing_time_ms=processing_time_ms
            )
            
        except asyncio.TimeoutError:
            return self._build_timeout_error(request)
        
        except httpx.ConnectError as e:
            return self._build_unavailable_error(request, str(e))
        
        except Exception as e:
            return self._build_internal_error(request, e)
    
    async def _call_ollama(self, prompt: str) -> dict:
        """
        Make async HTTP call to Ollama chat API.
        
        Args:
            prompt: Formatted prompt
        
        Returns:
            dict: Ollama response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._chat_url,
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    def _build_prompt(self, thought_content: str) -> str:
        """
        Build analysis prompt.
        
        Args:
            thought_content: Thought to analyze
        
        Returns:
            str: Formatted prompt
        """
        return f"""Analyze this thought and provide structured insights.

Thought: {thought_content}

Provide your analysis in this JSON format:
{{
    "summary": "One-sentence summary of the thought",
    "themes": ["theme1", "theme2"],
    "is_actionable": true/false,
    "action_suggestion": "Optional task if actionable",
    "insights": ["insight1", "insight2"]
}}

Analysis:"""
    
    def _parse_response(self, result: dict) -> dict:
        """
        Parse Ollama chat API response.
        
        Args:
            result: Raw Ollama response
        
        Returns:
            dict: Parsed analysis data
        """
        # Extract message content from chat API response
        message = result.get("message", {})
        text = message.get("content", "")
        
        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
            
            # Fallback if no JSON found
            return {
                "summary": text[:200] if text else "Analysis completed",
                "themes": [],
                "is_actionable": False,
                "insights": []
            }
            
        except json.JSONDecodeError:
            # Return minimal response if parsing fails
            return {
                "summary": text[:200] if text else "Analysis completed",
                "themes": [],
                "is_actionable": False,
                "insights": []
            }
    
    def _build_success_response(
        self,
        request: BackendRequest,
        analysis_data: dict,
        processing_time_ms: int
    ) -> SuccessResponse:
        """Build standardized success response"""
        # Extract themes
        themes = [
            Theme(theme=t, confidence=0.7)
            for t in analysis_data.get("themes", [])
        ]
        
        # Extract suggested actions
        actions = []
        if analysis_data.get("is_actionable"):
            action_text = analysis_data.get(
                "action_suggestion",
                "Create task"
            )
            actions.append(
                SuggestedAction(
                    action=action_text,
                    priority="medium",
                    confidence=0.6
                )
            )
        
        analysis = Analysis(
            request_id=request.request_id,
            backend_used=self.name,
            summary=analysis_data.get("summary", "Analysis completed"),
            themes=themes,
            suggested_actions=actions,
            related_thought_ids=[]
        )
        
        metadata = AnalysisMetadata(
            tokens_used=0,  # Ollama doesn't report tokens
            processing_time_ms=processing_time_ms,
            model_version=self._model,
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
                suggestion="Increase timeout or try faster model"
            )
        )
    
    def _build_unavailable_error(
        self,
        request: BackendRequest,
        details: str
    ) -> ErrorResponse:
        """Build unavailable error response"""
        return ErrorResponse(
            success=False,
            error=ErrorDetails(
                request_id=request.request_id,
                backend_name=self.name,
                error_code="UNAVAILABLE",
                error_message=f"Ollama server unreachable: {details}",
                suggestion="Check if Ollama is running at {self._base_url}"
            )
        )
    
    def _build_internal_error(
        self,
        request: BackendRequest,
        exc: Exception
    ) -> ErrorResponse:
        """Build internal error response"""
        logger.error(f"Internal error in OllamaBackend: {exc}")
        
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
        Check if Ollama server is reachable.
        
        Returns:
            bool: True if healthy
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
                
        except Exception:
            return False
