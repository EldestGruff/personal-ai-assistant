"""
Claude API service for AI-powered thought analysis.

Handles communication with Anthropic's Claude API for:
- Consciousness checks (periodic thought summaries)
- Thought analysis (single thought insights)
- Tag suggestions (auto-categorization)
- Task extraction (action item identification)
- Pattern detection (recurring themes)
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from anthropic import Anthropic, APIError as AnthropicAPIError

from ..models.thought import ThoughtDB
from ..models.task import TaskDB
from ..models.enums import Priority


logger = logging.getLogger(__name__)


class ClaudeService:
    """
    Service for Claude API interactions.

    Provides high-level methods for thought analysis using Claude.
    Handles prompt construction, API calls, and response parsing.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude service with API credentials.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or provided")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Latest Sonnet model
        self.max_tokens = 2048

    def _call_claude(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        Make API call to Claude with error handling.

        Args:
            system_prompt: System-level instructions for Claude
            user_message: User's message/query
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Dict with 'content', 'tokens_input', 'tokens_output'

        Raises:
            Exception: If API call fails
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract text content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text

            result = {
                "content": content,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "model": response.model,
                "stop_reason": response.stop_reason
            }

            logger.info(
                f"Claude API call successful: {result['tokens_input']} in, "
                f"{result['tokens_output']} out"
            )

            return result

        except AnthropicAPIError as e:
            logger.error(f"Claude API error: {e}")
            raise Exception(f"Claude API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Claude: {e}")
            raise

    def consciousness_check(
        self,
        thoughts: List[ThoughtDB],
        timeframe: str = "recent"
    ) -> Dict[str, Any]:
        """
        Perform a consciousness check: analyze recent thoughts for patterns and insights.

        This is the core "what am I thinking about?" feature.

        Args:
            thoughts: List of recent thoughts to analyze
            timeframe: Description of timeframe (e.g., "today", "this week")

        Returns:
            Dict with:
                - summary: High-level summary of thought patterns
                - themes: List of discovered themes
                - suggested_actions: List of recommended actions
                - concerns: List of recurring concerns or anxieties
                - positives: List of positive patterns
                - tokens_used: Total tokens consumed
        """
        if not thoughts:
            return {
                "summary": "No thoughts to analyze.",
                "themes": [],
                "suggested_actions": [],
                "concerns": [],
                "positives": [],
                "tokens_used": 0
            }

        # Build thought list for Claude
        thought_list = []
        for i, thought in enumerate(thoughts, 1):
            timestamp = thought.created_at.strftime("%Y-%m-%d %H:%M")
            tags = ", ".join(thought.tags) if thought.tags else "none"
            thought_list.append(
                f"{i}. [{timestamp}] {thought.content}\n   Tags: {tags}"
            )

        thoughts_text = "\n\n".join(thought_list)

        system_prompt = """You are an insightful AI assistant analyzing a person's captured thoughts to provide consciousness checks.

Your role is to:
1. Identify recurring themes and patterns
2. Spot concerns or anxieties that keep appearing
3. Notice positive patterns and wins
4. Suggest actionable next steps
5. Be supportive but honest

Format your response as JSON with these fields:
{
    "summary": "2-3 sentence overview of what they're thinking about",
    "themes": ["theme1", "theme2", ...],
    "suggested_actions": ["action1", "action2", ...],
    "concerns": ["concern1", "concern2", ...],
    "positives": ["positive1", "positive2", ...]
}

Keep it concise and actionable. Focus on patterns, not individual thoughts."""

        user_message = f"""Here are my {timeframe} thoughts ({len(thoughts)} total):

{thoughts_text}

Analyze these thoughts and provide insights in JSON format."""

        response = self._call_claude(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.7
        )

        # Parse JSON response
        import json
        try:
            result = json.loads(response["content"])
            result["tokens_used"] = response["tokens_input"] + response["tokens_output"]
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            logger.warning("Failed to parse JSON response, returning raw content")
            return {
                "summary": response["content"],
                "themes": [],
                "suggested_actions": [],
                "concerns": [],
                "positives": [],
                "tokens_used": response["tokens_input"] + response["tokens_output"]
            }

    def suggest_tags(
        self,
        thought_content: str,
        existing_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Suggest relevant tags for a thought.

        Args:
            thought_content: The thought text
            existing_tags: Tags already used by the user (for consistency)

        Returns:
            Dict with:
                - suggested_tags: List of 1-3 suggested tags
                - reasoning: Brief explanation
                - tokens_used: Total tokens consumed
        """
        existing_context = ""
        if existing_tags:
            existing_context = f"\nExisting tags you've used: {', '.join(existing_tags[:20])}"

        system_prompt = f"""You are a helpful AI that suggests tags for thoughts.

Guidelines:
- Suggest 1-3 tags maximum
- Use lowercase, hyphenated words (e.g., "work-project", "idea", "personal")
- Prefer existing tags when appropriate for consistency
- Be specific but not overly granular{existing_context}

Format response as JSON:
{{
    "suggested_tags": ["tag1", "tag2"],
    "reasoning": "Brief explanation of why these tags fit"
}}"""

        user_message = f"Thought: {thought_content}\n\nSuggest appropriate tags."

        response = self._call_claude(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.5
        )

        import json
        try:
            result = json.loads(response["content"])
            result["tokens_used"] = response["tokens_input"] + response["tokens_output"]
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse tag suggestions")
            return {
                "suggested_tags": [],
                "reasoning": "Failed to generate suggestions",
                "tokens_used": response["tokens_input"] + response["tokens_output"]
            }

    def extract_tasks(
        self,
        thoughts: List[ThoughtDB]
    ) -> Dict[str, Any]:
        """
        Extract actionable tasks from thoughts.

        Args:
            thoughts: List of thoughts to analyze for tasks

        Returns:
            Dict with:
                - tasks: List of extracted tasks with title, description, priority
                - reasoning: Explanation of task extraction
                - tokens_used: Total tokens consumed
        """
        if not thoughts:
            return {
                "tasks": [],
                "reasoning": "No thoughts to analyze",
                "tokens_used": 0
            }

        # Build thought list
        thought_list = []
        for i, thought in enumerate(thoughts, 1):
            timestamp = thought.created_at.strftime("%Y-%m-%d %H:%M")
            thought_list.append(f"{i}. [{timestamp}] {thought.content}")

        thoughts_text = "\n".join(thought_list)

        system_prompt = """You are an AI assistant that identifies actionable tasks from captured thoughts.

Look for:
- Explicit mentions of things to do ("need to", "should", "must")
- Implied actions (problems that need solving, ideas that need executing)
- Follow-ups and reminders

For each task, determine:
- A clear, actionable title
- A brief description
- Priority: low, medium, high, or critical

Format as JSON:
{
    "tasks": [
        {
            "title": "Clear, actionable task title",
            "description": "Brief context or details",
            "priority": "medium",
            "source_thought_index": 1
        }
    ],
    "reasoning": "Brief explanation of task extraction logic"
}

Only extract genuine tasks. Don't force tasks where none exist."""

        user_message = f"""Analyze these thoughts for actionable tasks:

{thoughts_text}

Extract tasks in JSON format."""

        response = self._call_claude(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.5
        )

        import json
        try:
            result = json.loads(response["content"])
            result["tokens_used"] = response["tokens_input"] + response["tokens_output"]
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse task extraction")
            return {
                "tasks": [],
                "reasoning": "Failed to extract tasks",
                "tokens_used": response["tokens_input"] + response["tokens_output"]
            }

    def analyze_thought(
        self,
        thought: ThoughtDB,
        context_thoughts: Optional[List[ThoughtDB]] = None
    ) -> Dict[str, Any]:
        """
        Deep analysis of a single thought.

        Args:
            thought: The thought to analyze
            context_thoughts: Recent related thoughts for context

        Returns:
            Dict with:
                - summary: One-sentence summary
                - insights: List of insights or observations
                - related_themes: Themes this thought relates to
                - suggested_tags: Tag suggestions
                - is_actionable: Whether this should become a task
                - tokens_used: Total tokens consumed
        """
        context_text = ""
        if context_thoughts:
            context_list = [f"- {t.content[:100]}..." for t in context_thoughts[:5]]
            context_text = f"\nRecent related thoughts:\n" + "\n".join(context_list)

        system_prompt = """You are an insightful AI analyzing a single thought.

Provide:
1. A concise summary
2. Key insights or observations
3. Related themes
4. Suggested tags (1-3)
5. Whether this is actionable (should become a task)

Format as JSON:
{
    "summary": "One sentence summary",
    "insights": ["insight1", "insight2"],
    "related_themes": ["theme1", "theme2"],
    "suggested_tags": ["tag1", "tag2"],
    "is_actionable": true/false,
    "action_suggestion": "Optional task title if actionable"
}"""

        timestamp = thought.created_at.strftime("%Y-%m-%d %H:%M")
        existing_tags = ", ".join(thought.tags) if thought.tags else "none"

        user_message = f"""Analyze this thought:

Timestamp: {timestamp}
Existing tags: {existing_tags}
Content: {thought.content}{context_text}

Provide analysis in JSON format."""

        response = self._call_claude(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.7
        )

        import json
        try:
            result = json.loads(response["content"])
            result["tokens_used"] = response["tokens_input"] + response["tokens_output"]
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse thought analysis")
            return {
                "summary": thought.content[:100],
                "insights": [],
                "related_themes": [],
                "suggested_tags": [],
                "is_actionable": False,
                "tokens_used": response["tokens_input"] + response["tokens_output"]
            }
