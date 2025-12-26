"""
OpenAI-compatible backend implementation.

Connects to any OpenAI-compatible server (LM Studio, llama.cpp, vLLM, etc.)
for local, privacy-preserving thought analysis.
"""

import logging
import asyncio
import time
import json
from typing import Union
from datetime import datetime, UTC

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


class OpenAICompatibleBackend:
    """
    OpenAI-compatible backend for local LLM inference.
    
    Connects to any OpenAI-compatible server (LM Studio, llama.cpp, 
    vLLM, Text Generation WebUI, etc.) using the standard OpenAI API.
    
    Example:
        backend = OpenAICompatibleBackend(
            base_url="http://fuego:8080/v1"
        )
        response = await backend.analyze(request)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        model: str = "local-model"
    ):
        """
        Initialize OpenAI-compatible backend.
        
        Args:
            base_url: Server URL (e.g. http://host:8080/v1)
            model: Model identifier (may be ignored by some servers)
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._name = "openai"
        self._chat_url = f"{self._base_url}/chat/completions"
        self._models_url = f"{self._base_url}/models"
        # Enforce serial processing to prevent GPU crashes on the host
        self._semaphore = asyncio.Semaphore(1)
    
    @property
    def name(self) -> str:
        """Backend identifier"""
        return self._name
    
    async def analyze(
        self,
        request: BackendRequest
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Analyze thought using LM Studio.
        
        Args:
            request: Standardized backend request
        
        Returns:
            SuccessResponse if successful
            ErrorResponse if failed
        """
        start_time = time.time()
        
        try:
            # Acquire semaphore to ensure only one request runs at a time
            async with self._semaphore:
                # Build prompt
                prompt = self._build_prompt(request.thought_content)
                
                # Call LLM with timeout
                result = await asyncio.wait_for(
                    self._call_llm(prompt),
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
            logger.error(
                f"[{request.request_id}] httpx.ConnectError connecting to {self._chat_url}: "
                f"Type={type(e).__name__}, Message={str(e)}, Args={e.args}"
            )
            return self._build_unavailable_error(request, str(e))
        
        except Exception as e:
            return self._build_internal_error(request, e)
    
    async def _call_llm(self, prompt: str) -> dict:
        """
        Make async HTTP call to the OpenAI-compatible API.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._chat_url,
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "stream": False
                },
                timeout=60.0
            )
            if response.status_code == 400:
                logger.error(f"OpenAI-compatible API 400 Error: {response.text}")
            response.raise_for_status()
            return response.json()
    
    def _build_prompt(self, thought_content: str) -> str:
        """
        Build analysis prompt.
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
        Parse OpenAI-compatible API response.
        """
        try:
            choices = result.get('choices', [])
            if not choices:
                text = ""
            else:
                text = choices[0].get('message', {}).get('content', "")
        except (KeyError, IndexError):
            text = ""
        
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
            tokens_used=0,  # Usage data might be available in result['usage']
            processing_time_ms=processing_time_ms,
            model_version=self._model,
            timestamp=datetime.now(UTC).isoformat()
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
                error_message=f"LM Studio server unreachable: {details}",
                suggestion=f"Check if server is running at {self._base_url}"
            )
        )
    
    def _build_internal_error(
        self,
        request: BackendRequest,
        exc: Exception
    ) -> ErrorResponse:
        """Build internal error response"""
        logger.error(f"Internal error in OpenAICompatibleBackend: {exc}")
        
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
        Check if LM Studio server is reachable.
        
        Returns:
            bool: True if healthy
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._models_url,
                    timeout=5.0
                )
                if response.status_code == 200:
                    logger.info(f"OpenAI health check: SUCCESS (HTTP {response.status_code})")
                    return True
                else:
                    logger.warning(f"OpenAI health check: FAILED - HTTP {response.status_code}")
                    return False
                
        except Exception as e:
            logger.error(
                f"OpenAI health check: EXCEPTION - {type(e).__name__}: {str(e)} "
                f"(URL: {self._models_url})"
            )
            return False
