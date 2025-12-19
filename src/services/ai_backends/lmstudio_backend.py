"""
LM Studio backend implementation for local LLM inference.

LM Studio provides an OpenAI-compatible API, making it easy to run
local models with the same interface as OpenAI's API.
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


class LMStudioBackend:
    """
    LM Studio backend for local LLM inference.

    Uses OpenAI-compatible API to connect to LM Studio server
    running on local machine with Arc B580 GPU acceleration.

    Example:
        backend = LMStudioBackend(
            base_url="http://192.168.7.187:1234/v1"
        )
        response = await backend.analyze(request)
    """

    def __init__(
        self,
        base_url: str = "http://192.168.7.187:1234/v1",
        model: str = "local-model"
    ):
        """
        Initialize LM Studio backend.

        Args:
            base_url: LM Studio server URL (OpenAI-compatible endpoint)
            model: Model identifier (use "local-model" or specific model name)
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._name = "lmstudio"
        self._chat_url = f"{self._base_url}/chat/completions"

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
            # Build prompt
            prompt = self._build_prompt(request.thought_content)

            # Call LM Studio with timeout
            result = await asyncio.wait_for(
                self._call_lmstudio(prompt),
                timeout=request.timeout_seconds
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Parse response
            analysis_data = self._parse_response(result)

            return self._build_success_response(
                request=request,
                analysis_data=analysis_data,
                processing_time_ms=processing_time_ms,
                tokens_used=result.get("usage", {}).get("total_tokens", 0)
            )

        except asyncio.TimeoutError:
            return self._build_timeout_error(request)

        except httpx.ConnectError as e:
            return self._build_unavailable_error(request, str(e))

        except Exception as e:
            return self._build_internal_error(request, e)

    async def _call_lmstudio(self, prompt: str) -> dict:
        """
        Make async HTTP call to LM Studio OpenAI-compatible API.

        Args:
            prompt: Formatted prompt

        Returns:
            dict: LM Studio response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._chat_url,
                json={
                    "model": self._model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an AI assistant that analyzes thoughts and provides structured insights."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "stream": False
                },
                headers={
                    "Content-Type": "application/json"
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
        Parse LM Studio OpenAI-compatible response.

        Args:
            result: Raw LM Studio response

        Returns:
            dict: Parsed analysis data
        """
        # Extract message content from OpenAI-compatible response
        choices = result.get("choices", [])
        if not choices:
            return {
                "summary": "Analysis completed",
                "themes": [],
                "is_actionable": False,
                "insights": []
            }

        message = choices[0].get("message", {})
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
        processing_time_ms: int,
        tokens_used: int
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
            tokens_used=tokens_used,
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
                suggestion="Increase timeout or use a faster model"
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
                suggestion=f"Check if LM Studio is running at {self._base_url}"
            )
        )

    def _build_internal_error(
        self,
        request: BackendRequest,
        exc: Exception
    ) -> ErrorResponse:
        """Build internal error response"""
        logger.error(f"Internal error in LMStudioBackend: {exc}")

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
                # Try to get models list (OpenAI-compatible endpoint)
                response = await client.get(
                    f"{self._base_url}/models",
                    timeout=5.0
                )
                return response.status_code == 200

        except Exception:
            return False
