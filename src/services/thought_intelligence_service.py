"""
Thought Intelligence Service for Personal AI Assistant.

Phase 3B Spec 2: Analyzes thoughts for intent, tags, and actionable items.
Runs at thought capture time to provide immediate intelligence.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import logging

from sqlalchemy.orm import Session

from src.models import (
    ThoughtDB,
    TaskSuggestionCreate,
    ThoughtType,
    EmotionalTone,
    Urgency,
    Priority,
    TaskSuggestionMode,
)
from src.services.ai_backends.prompts import (
    build_thought_analysis_prompt,
    parse_json_response,
    extract_thought_analysis_result,
)

logger = logging.getLogger(__name__)


class ThoughtAnalysisResult:
    """
    Structured result from thought analysis.
    
    Contains all extracted intelligence from AI analysis.
    """
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize from parsed response."""
        self.thought_type = data.get("thought_type", "note")
        self.intent_confidence = data.get("intent_confidence", 0.5)
        self.reasoning = data.get("reasoning", "")
        self.suggested_tags = data.get("suggested_tags", [])
        self.is_actionable = data.get("is_actionable", False)
        self.actionable_confidence = data.get("actionable_confidence", 0.0)
        self.task_suggestion = data.get("task_suggestion")
        self.related_topics = data.get("related_topics", [])
        self.emotional_tone = data.get("emotional_tone", "neutral")
        self.urgency = data.get("urgency", "low")
    
    @property
    def should_suggest_task(self) -> bool:
        """Whether this analysis warrants a task suggestion."""
        return self.is_actionable and self.actionable_confidence >= 0.7


class ThoughtIntelligenceService:
    """
    Analyzes thoughts for intent, tags, and actionable items.
    
    Runs at thought capture time to provide immediate intelligence.
    Uses AI backends for analysis and integrates with settings.
    """
    
    def __init__(
        self,
        db: Session,
        ai_orchestrator,  # AIOrchestrator from backend_selection
        settings_service,  # SettingsService
        user_profile_service,  # UserProfileService
        task_suggestion_service,  # TaskSuggestionService
    ):
        """
        Initialize ThoughtIntelligenceService.
        
        Args:
            db: SQLAlchemy database session
            ai_orchestrator: AI backend orchestrator
            settings_service: For checking user settings
            user_profile_service: For user context
            task_suggestion_service: For creating suggestions
        """
        self.db = db
        self.ai_orchestrator = ai_orchestrator
        self.settings_service = settings_service
        self.user_profile_service = user_profile_service
        self.task_suggestion_service = task_suggestion_service
    
    async def analyze_thought_on_capture(
        self,
        user_id: UUID,
        thought: ThoughtDB
    ) -> Optional[ThoughtAnalysisResult]:
        """
        Analyze a thought immediately after capture.
        
        Extracts:
        - Intent classification (task, note, reminder, etc.)
        - Suggested tags with confidence
        - Task detection with reasoning
        - Related topics
        
        Args:
            user_id: UUID of the user
            thought: The newly captured thought
            
        Returns:
            ThoughtAnalysisResult with structured analysis, or None if disabled
        """
        # Check if auto-analysis is enabled
        user_id_str = str(user_id)
        settings = self.settings_service.get_user_settings(user_id_str)
        
        if not settings.auto_tagging_enabled and not settings.auto_task_creation_enabled:
            logger.debug(f"Auto-analysis disabled for user {user_id}")
            return None
        
        try:
            # Load user profile for context
            profile = self.user_profile_service.get_profile(user_id_str)
            
            # Get recent thoughts for context
            recent_thoughts = await self._get_recent_thoughts(user_id, limit=5)
            
            # Build analysis prompt
            prompt = build_thought_analysis_prompt(
                thought_content=thought.content,
                user_profile=profile,
                recent_thoughts=recent_thoughts
            )
            
            # Send to AI backend
            response = await self._call_ai_backend(
                user_id=user_id,
                prompt=prompt,
                request_id=f"thought-analysis-{thought.id}"
            )
            
            if not response:
                logger.warning(f"No response from AI backend for thought {thought.id}")
                return None
            
            # Parse response
            parsed = parse_json_response(response)
            if not parsed:
                logger.warning(f"Failed to parse AI response for thought {thought.id}")
                return None
            
            # Extract structured result
            analysis_data = extract_thought_analysis_result(parsed)
            analysis = ThoughtAnalysisResult(analysis_data)
            
            # Update thought with analysis
            await self._update_thought_with_analysis(thought, analysis)
            
            # Create task suggestion if actionable
            if analysis.should_suggest_task and settings.task_suggestion_mode != TaskSuggestionMode.DISABLED:
                await self._create_task_suggestion(user_id, thought, analysis, settings)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing thought {thought.id}: {e}")
            return None
    
    async def _get_recent_thoughts(
        self,
        user_id: UUID,
        limit: int = 5
    ) -> List[ThoughtDB]:
        """Get recent thoughts for context."""
        return self.db.query(ThoughtDB).filter(
            ThoughtDB.user_id == str(user_id)
        ).order_by(
            ThoughtDB.created_at.desc()
        ).limit(limit).all()
    
    async def _call_ai_backend(
        self,
        user_id: UUID,
        prompt: str,
        request_id: str
    ) -> Optional[str]:
        """
        Call AI backend for analysis.
        
        Uses the orchestrator which handles backend selection and fallback.
        """
        try:
            # Import here to avoid circular imports
            from src.services.ai_backends.models import BackendRequest
            
            request = BackendRequest(
                request_id=request_id,
                thought_content=prompt,  # Using prompt as content
                context={
                    "user_id": str(user_id),
                    "analysis_type": "thought_capture"
                },
                timeout_seconds=30,
                model_hint="fast"  # Use fast model for capture-time analysis
            )
            
            response = await self.ai_orchestrator.analyze(request)
            
            if response.success:
                return response.analysis.summary
            else:
                logger.warning(f"AI backend error: {response.error.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling AI backend: {e}")
            return None
    
    async def _update_thought_with_analysis(
        self,
        thought: ThoughtDB,
        analysis: ThoughtAnalysisResult
    ) -> None:
        """Update thought with analysis results."""
        now = datetime.now(timezone.utc)
        
        # Map string to enum value
        thought_type = analysis.thought_type
        if thought_type and not hasattr(thought_type, 'value'):
            try:
                thought_type = ThoughtType(thought_type).value
            except ValueError:
                thought_type = ThoughtType.NOTE.value
        elif thought_type:
            thought_type = thought_type.value if hasattr(thought_type, 'value') else thought_type
        
        emotional_tone = analysis.emotional_tone
        if emotional_tone and not hasattr(emotional_tone, 'value'):
            try:
                emotional_tone = EmotionalTone(emotional_tone).value
            except ValueError:
                emotional_tone = EmotionalTone.NEUTRAL.value
        elif emotional_tone:
            emotional_tone = emotional_tone.value if hasattr(emotional_tone, 'value') else emotional_tone
        
        urgency = analysis.urgency
        if urgency and not hasattr(urgency, 'value'):
            try:
                urgency = Urgency(urgency).value
            except ValueError:
                urgency = Urgency.LOW.value
        elif urgency:
            urgency = urgency.value if hasattr(urgency, 'value') else urgency
        
        thought.thought_type = thought_type
        thought.intent_confidence = analysis.intent_confidence
        thought.suggested_tags = analysis.suggested_tags
        thought.related_topics = analysis.related_topics
        thought.emotional_tone = emotional_tone
        thought.urgency = urgency
        thought.is_actionable = analysis.is_actionable
        thought.actionable_confidence = analysis.actionable_confidence
        thought.analysis_version = 1
        thought.analyzed_at = now
        thought.updated_at = now
        
        self.db.commit()
    
    async def _create_task_suggestion(
        self,
        user_id: UUID,
        thought: ThoughtDB,
        analysis: ThoughtAnalysisResult,
        settings
    ) -> None:
        """Create task suggestion from analysis."""
        if not analysis.task_suggestion:
            return
        
        ts = analysis.task_suggestion
        
        # Map priority string to enum
        priority_str = ts.get("priority", "medium")
        try:
            priority = Priority(priority_str)
        except ValueError:
            priority = Priority.MEDIUM
        
        create_data = TaskSuggestionCreate(
            source_thought_id=UUID(thought.id),
            title=ts.get("title", thought.content[:100]),
            description=ts.get("description"),
            priority=priority,
            estimated_effort_minutes=ts.get("estimated_effort_minutes"),
            due_date_hint=None,  # Could parse from ts if present
            confidence=analysis.actionable_confidence,
            reasoning=ts.get("reasoning", analysis.reasoning)
        )
        
        await self.task_suggestion_service.create_suggestion(user_id, create_data)
        
        # If auto-create mode, immediately accept the suggestion
        if settings.task_suggestion_mode == TaskSuggestionMode.AUTO_CREATE:
            suggestions = await self.task_suggestion_service.get_suggestions_for_thought(
                UUID(thought.id)
            )
            if suggestions:
                await self.task_suggestion_service.accept_suggestion(
                    UUID(suggestions[0].id)
                )
    
    async def apply_suggested_tags(
        self,
        thought_id: UUID,
        suggested_tags: List[str],
        user_approved: bool = False
    ) -> ThoughtDB:
        """
        Apply suggested tags to a thought.
        
        Merges with existing tags, no duplicates.
        
        Args:
            thought_id: UUID of the thought
            suggested_tags: List of tag names to apply
            user_approved: If true, user explicitly approved
            
        Returns:
            Updated ThoughtDB
        """
        thought = self.db.query(ThoughtDB).filter(
            ThoughtDB.id == str(thought_id)
        ).first()
        
        if not thought:
            raise ValueError(f"Thought {thought_id} not found")
        
        # Merge with existing tags (no duplicates)
        current_tags = set(thought.tags or [])
        new_tags = set(t.lower().strip() for t in suggested_tags if t.strip())
        merged_tags = list(current_tags | new_tags)[:5]  # Max 5 tags
        
        thought.tags = merged_tags
        thought.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(thought)
        
        return thought
    
    async def get_existing_tags(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> List[str]:
        """
        Get all existing tags for a user.
        
        Useful for tag suggestion consistency.
        
        Args:
            user_id: UUID of the user
            limit: Maximum tags to return
            
        Returns:
            List of unique tag strings
        """
        thoughts = self.db.query(ThoughtDB.tags).filter(
            ThoughtDB.user_id == str(user_id),
            ThoughtDB.tags.isnot(None)
        ).all()
        
        all_tags = set()
        for (tags,) in thoughts:
            if tags:
                all_tags.update(tags)
        
        return sorted(list(all_tags))[:limit]
