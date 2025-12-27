"""
Enhanced Consciousness Check Service for Personal AI Assistant.

Phase 3B Spec 2: Personal, contextual consciousness checks that make
analysis feel warm and personalized. This is what transforms sterile
AI analysis into a genuine personal assistant experience.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import logging

from sqlalchemy.orm import Session

from src.models import (
    ThoughtDB,
    ClaudeAnalysisDB,
    UserProfileDB,
    AnalysisType,
    SettingsDepthType,
    AnalysisDepthConfig,
)
from src.services.ai_backends.prompts import (
    build_consciousness_check_prompt,
    parse_json_response,
    extract_consciousness_check_result,
    get_time_of_day,
)

logger = logging.getLogger(__name__)


class ConsciousnessCheckResult:
    """
    Structured result from consciousness check.
    
    Contains the personal, contextual analysis.
    """
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize from parsed response."""
        self.summary = data.get("summary", "Analysis completed.")
        self.themes = data.get("themes", [])
        self.connections = data.get("connections", [])
        self.suggested_actions = data.get("suggested_actions", [])
        self.encouragement = data.get("encouragement", "Keep up the great work!")
        self.discovered_patterns = data.get("discovered_patterns", [])


class EnhancedConsciousnessCheckService:
    """
    Enhanced consciousness check with personal, contextual analysis.
    
    This service is THE KEY to making the system feel personal.
    Every check should:
    - Reference ongoing projects
    - Use warm, encouraging language
    - Connect to past patterns
    - Feel like a conversation with a friend
    """
    
    def __init__(
        self,
        db: Session,
        ai_orchestrator,  # AIOrchestrator from backend_selection
        settings_service,  # SettingsService
        user_profile_service,  # UserProfileService
    ):
        """
        Initialize EnhancedConsciousnessCheckService.
        
        Args:
            db: SQLAlchemy database session
            ai_orchestrator: AI backend orchestrator
            settings_service: For getting user settings
            user_profile_service: For user context
        """
        self.db = db
        self.ai_orchestrator = ai_orchestrator
        self.settings_service = settings_service
        self.user_profile_service = user_profile_service
    
    async def run_consciousness_check(
        self,
        user_id: UUID,
        depth_config: Optional[AnalysisDepthConfig] = None,
        triggered_by: str = "manual"
    ) -> ClaudeAnalysisDB:
        """
        Run enhanced consciousness check with personal context.
        
        This is the main entry point for consciousness checks.
        Builds a rich, personalized prompt and returns warm analysis.
        
        Args:
            user_id: UUID of the user
            depth_config: How many/which thoughts to analyze (uses settings if None)
            triggered_by: "scheduler" or "manual"
            
        Returns:
            ClaudeAnalysisDB with personalized analysis
        """
        start_time = datetime.now(timezone.utc)
        
        # Get settings if depth_config not provided
        if depth_config is None:
            depth_config = await self.settings_service.get_analysis_depth_config(user_id)
        
        # Load user profile
        profile = await self.user_profile_service.get_profile(user_id)
        
        # Load thoughts based on depth config
        thoughts = await self._load_thoughts_for_analysis(user_id, depth_config)
        
        if not thoughts:
            logger.info(f"No thoughts to analyze for user {user_id}")
            return await self._create_empty_result(user_id, triggered_by)
        
        # Load previous analyses for pattern context
        previous_analyses = await self._get_recent_analyses(user_id, limit=3)
        
        # Build context
        context = {
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'time_of_day': get_time_of_day(),
            'triggered_by': triggered_by,
            'thoughts_count': len(thoughts),
        }
        
        # Build rich prompt - THIS IS THE KEY
        prompt = build_consciousness_check_prompt(
            user_profile=profile,
            thoughts=thoughts,
            previous_analyses=previous_analyses,
            context=context
        )
        
        # Send to AI backend
        response = await self._call_ai_backend(
            user_id=user_id,
            prompt=prompt,
            request_id=f"consciousness-check-{uuid4()}"
        )
        
        if not response:
            logger.warning(f"No response from AI backend for consciousness check")
            return await self._create_error_result(user_id, triggered_by, "No AI response")
        
        # Parse response
        parsed = parse_json_response(response)
        if not parsed:
            logger.warning(f"Failed to parse consciousness check response")
            # Fall back to raw response as summary
            parsed = {"summary": response[:1000]}
        
        # Extract structured result
        analysis_data = extract_consciousness_check_result(parsed)
        result = ConsciousnessCheckResult(analysis_data)
        
        # Calculate duration
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        # Store in database
        analysis_record = await self._store_analysis_result(
            user_id=user_id,
            result=result,
            thoughts_count=len(thoughts),
            duration_ms=duration_ms,
            triggered_by=triggered_by,
            raw_response=response
        )
        
        # Update user profile with discovered patterns
        if result.discovered_patterns or result.themes:
            await self.user_profile_service.update_patterns(
                user_id=user_id,
                discovered_patterns=result.discovered_patterns,
                themes=result.themes
            )
        
        return analysis_record
    
    async def _load_thoughts_for_analysis(
        self,
        user_id: UUID,
        depth_config: AnalysisDepthConfig
    ) -> List[ThoughtDB]:
        """
        Load thoughts based on depth configuration.
        
        Implements the "smart" mode: max(last N days, min M thoughts)
        """
        query = self.db.query(ThoughtDB).filter(
            ThoughtDB.user_id == str(user_id)
        )
        
        if depth_config.depth_type == SettingsDepthType.ALL_THOUGHTS:
            # All thoughts (expensive!)
            thoughts = query.order_by(ThoughtDB.created_at.desc()).all()
            
        elif depth_config.depth_type == SettingsDepthType.LAST_N_THOUGHTS:
            # Exactly N most recent
            thoughts = query.order_by(
                ThoughtDB.created_at.desc()
            ).limit(depth_config.max_thoughts or 10).all()
            
        elif depth_config.depth_type == SettingsDepthType.LAST_N_DAYS:
            # All from last N days
            if depth_config.since_date:
                query = query.filter(ThoughtDB.created_at >= depth_config.since_date)
            thoughts = query.order_by(ThoughtDB.created_at.desc()).all()
            
        elif depth_config.depth_type == SettingsDepthType.SMART:
            # Smart mode: max(last N days, min M thoughts)
            thoughts_by_date = []
            thoughts_by_count = []
            
            # Get thoughts by date
            if depth_config.since_date:
                thoughts_by_date = query.filter(
                    ThoughtDB.created_at >= depth_config.since_date
                ).order_by(ThoughtDB.created_at.desc()).all()
            
            # Get minimum count
            min_thoughts = depth_config.min_thoughts or 10
            thoughts_by_count = query.order_by(
                ThoughtDB.created_at.desc()
            ).limit(min_thoughts).all()
            
            # Take whichever is larger
            if len(thoughts_by_date) >= len(thoughts_by_count):
                thoughts = thoughts_by_date
            else:
                thoughts = thoughts_by_count
        else:
            # Default to last 10
            thoughts = query.order_by(
                ThoughtDB.created_at.desc()
            ).limit(10).all()
        
        return thoughts
    
    async def _get_recent_analyses(
        self,
        user_id: UUID,
        limit: int = 3
    ) -> List[ClaudeAnalysisDB]:
        """Get recent analyses for pattern context."""
        return self.db.query(ClaudeAnalysisDB).filter(
            ClaudeAnalysisDB.user_id == str(user_id),
            ClaudeAnalysisDB.analysis_type == AnalysisType.CONSCIOUSNESS_CHECK.value
        ).order_by(
            ClaudeAnalysisDB.created_at.desc()
        ).limit(limit).all()
    
    async def _call_ai_backend(
        self,
        user_id: UUID,
        prompt: str,
        request_id: str
    ) -> Optional[str]:
        """
        Call AI backend for consciousness check.
        
        Uses quality model hint since this is a significant analysis.
        """
        try:
            from src.services.ai_backends.models import BackendRequest
            
            request = BackendRequest(
                request_id=request_id,
                thought_content=prompt,
                context={
                    "user_id": str(user_id),
                    "analysis_type": "consciousness_check"
                },
                timeout_seconds=60,  # Longer timeout for thorough analysis
                model_hint="quality"  # Use quality model
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
    
    async def _store_analysis_result(
        self,
        user_id: UUID,
        result: ConsciousnessCheckResult,
        thoughts_count: int,
        duration_ms: int,
        triggered_by: str,
        raw_response: str
    ) -> ClaudeAnalysisDB:
        """Store analysis result in database."""
        now = datetime.now(timezone.utc)
        
        analysis = ClaudeAnalysisDB(
            id=str(uuid4()),
            thought_id=None,  # Consciousness check analyzes multiple
            user_id=str(user_id),
            analysis_type=AnalysisType.CONSCIOUSNESS_CHECK.value,
            summary=result.summary,
            themes=result.themes,
            suggested_action="; ".join(
                a.get("action", "") for a in result.suggested_actions[:3]
            ) if result.suggested_actions else None,
            confidence=0.85,  # Default confidence for consciousness checks
            tokens_used=None,  # Would need to track from backend
            raw_response={
                "summary": result.summary,
                "themes": result.themes,
                "connections": result.connections,
                "suggested_actions": result.suggested_actions,
                "encouragement": result.encouragement,
                "discovered_patterns": result.discovered_patterns,
                "raw": raw_response[:5000] if raw_response else None,  # Limit size
                "metadata": {
                    "thoughts_analyzed": thoughts_count,
                    "duration_ms": duration_ms,
                    "triggered_by": triggered_by
                }
            },
            created_at=now,
        )
        
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        
        return analysis
    
    async def _create_empty_result(
        self,
        user_id: UUID,
        triggered_by: str
    ) -> ClaudeAnalysisDB:
        """Create result when no thoughts to analyze."""
        now = datetime.now(timezone.utc)
        
        analysis = ClaudeAnalysisDB(
            id=str(uuid4()),
            thought_id=None,
            user_id=str(user_id),
            analysis_type=AnalysisType.CONSCIOUSNESS_CHECK.value,
            summary="No new thoughts to analyze since the last check. Take your time - I'll be here when you need me!",
            themes=[],
            suggested_action=None,
            confidence=1.0,
            tokens_used=0,
            raw_response={
                "empty": True,
                "triggered_by": triggered_by
            },
            created_at=now,
        )
        
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        
        return analysis
    
    async def _create_error_result(
        self,
        user_id: UUID,
        triggered_by: str,
        error_message: str
    ) -> ClaudeAnalysisDB:
        """Create result when analysis fails."""
        now = datetime.now(timezone.utc)
        
        analysis = ClaudeAnalysisDB(
            id=str(uuid4()),
            thought_id=None,
            user_id=str(user_id),
            analysis_type=AnalysisType.CONSCIOUSNESS_CHECK.value,
            summary="I had trouble completing the analysis this time. Don't worry - I'll try again at the next scheduled check!",
            themes=[],
            suggested_action=None,
            confidence=0.0,
            tokens_used=0,
            raw_response={
                "error": True,
                "error_message": error_message,
                "triggered_by": triggered_by
            },
            created_at=now,
        )
        
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        
        return analysis
    
    async def get_latest_analysis(
        self,
        user_id: UUID
    ) -> Optional[ClaudeAnalysisDB]:
        """Get the most recent consciousness check for user."""
        return self.db.query(ClaudeAnalysisDB).filter(
            ClaudeAnalysisDB.user_id == str(user_id),
            ClaudeAnalysisDB.analysis_type == AnalysisType.CONSCIOUSNESS_CHECK.value
        ).order_by(
            ClaudeAnalysisDB.created_at.desc()
        ).first()
    
    async def count_thoughts_since_last_check(
        self,
        user_id: UUID
    ) -> int:
        """
        Count thoughts since last consciousness check.
        
        Used by scheduler to decide if a check should be skipped.
        """
        last_analysis = await self.get_latest_analysis(user_id)
        
        if not last_analysis:
            # No previous analysis, count all thoughts
            return self.db.query(ThoughtDB).filter(
                ThoughtDB.user_id == str(user_id)
            ).count()
        
        return self.db.query(ThoughtDB).filter(
            ThoughtDB.user_id == str(user_id),
            ThoughtDB.created_at > last_analysis.created_at
        ).count()
