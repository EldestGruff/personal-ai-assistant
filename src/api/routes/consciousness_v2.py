"""
Consciousness Check Endpoints

v2: Pluggable backends with automatic fallback
v3 (enhanced): Personal, contextual analysis with user profile

Differences from v1:
- Uses BackendOrchestrator (not direct Claude)
- Includes per-backend metrics
- Automatic fallback (primary → secondary)
- Better error handling
- v3: Warm, personalized insights referencing projects/patterns
"""

import logging
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...api.auth import verify_api_key, get_current_user_id
from ...database.session import get_db
from ...services.thought_analyzer import ThoughtAnalyzer
from ...services.metrics import BackendMetrics, BackendStats
from ...models.thought import ThoughtResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class ThoughtRef(BaseModel):
    """Reference to a thought for analysis"""
    
    id: str = Field(..., description="Thought ID")
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Thought content"
    )


class ConsciousnessCheckRequest(BaseModel):
    """Request for consciousness check v2"""
    
    recent_thoughts: list[ThoughtRef] = Field(
        ...,
        description="Thoughts to analyze (usually last 10-20)"
    )
    limit_recent: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max thoughts to analyze"
    )
    include_archived: bool = Field(
        default=False,
        description="Include archived thoughts"
    )


class ConsciousnessCheckResponse(BaseModel):
    """Response from consciousness check v2"""
    
    success: bool = Field(..., description="Whether analysis succeeded")
    request_id: str = Field(..., description="Request ID for tracing")
    summary: str = Field(..., description="Overall summary")
    themes: list[str] = Field(
        default=[],
        description="Extracted themes"
    )
    suggested_actions: list[str] = Field(
        default=[],
        description="Suggested next actions"
    )
    source_analyses: int = Field(
        ...,
        description="Number of thoughts analyzed"
    )
    backend_stats: dict[str, BackendStats] = Field(
        ...,
        description="Per-backend performance metrics"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="When analysis completed"
    )


# Dependency injection placeholders
# These will be set up in main.py startup
_analyzer: Optional[ThoughtAnalyzer] = None
_metrics: Optional[BackendMetrics] = None


def get_thought_analyzer() -> ThoughtAnalyzer:
    """Get ThoughtAnalyzer instance (dependency)"""
    if _analyzer is None:
        raise HTTPException(
            status_code=500,
            detail="ThoughtAnalyzer not initialized"
        )
    return _analyzer


def get_metrics() -> BackendMetrics:
    """Get BackendMetrics instance (dependency)"""
    if _metrics is None:
        raise HTTPException(
            status_code=500,
            detail="BackendMetrics not initialized"
        )
    return _metrics


def set_analyzer(analyzer: ThoughtAnalyzer) -> None:
    """Set analyzer instance (called from main.py)"""
    global _analyzer
    _analyzer = analyzer


def set_metrics(metrics: BackendMetrics) -> None:
    """Set metrics instance (called from main.py)"""
    global _metrics
    _metrics = metrics


@router.post(
    "/consciousness-check-v2",
    response_model=ConsciousnessCheckResponse,
    summary="Consciousness check v2 (pluggable backends)",
    description=(
        "Analyze recent thoughts using backend orchestration. "
        "Automatically selects backend and falls back if needed. "
        "Includes per-backend performance metrics."
    )
)
async def consciousness_check_v2(
    request: ConsciousnessCheckRequest,
    api_key: str = Depends(verify_api_key),
    analyzer: ThoughtAnalyzer = Depends(get_thought_analyzer),
    metrics: BackendMetrics = Depends(get_metrics)
) -> ConsciousnessCheckResponse:
    """
    Consciousness check using pluggable backends.
    
    Uses backend selection/orchestration:
    - Primary: Claude (fast, capable)
    - Fallback: Ollama (local, always available)
    
    Automatically falls back if primary fails with
    recoverable error (timeout, rate limit, etc.)
    
    Args:
        request: Consciousness check request
        api_key: API key for authentication
        analyzer: ThoughtAnalyzer instance
        metrics: BackendMetrics instance
    
    Returns:
        ConsciousnessCheckResponse with analysis and metrics
    """
    logger.info(
        f"Consciousness check v2: {len(request.recent_thoughts)} thoughts"
    )
    
    # Limit thoughts to analyze
    thoughts_to_analyze = request.recent_thoughts[:request.limit_recent]
    
    # Convert to ThoughtResponse objects
    from uuid import uuid4
    thoughts = [
        ThoughtResponse(
            id=str(uuid4()),  # Generate valid UUID
            content=t.content,
            user_id="550e8400-e29b-41d4-a716-446655440000",  # Valid default UUID
            tags=[],
            status="active",
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat()
        )
        for t in thoughts_to_analyze
    ]
    
    # Analyze thoughts
    logger.debug(f"Analyzing {len(thoughts)} thoughts...")
    
    results = await analyzer.analyze_batch(thoughts)
    
    # Record metrics for each result
    for result in results:
        if result.success:
            metrics.record_success(
                backend_name=result.analysis.backend_used,
                response_time_ms=result.metadata.processing_time_ms,
                tokens=result.metadata.tokens_used
            )
        else:
            metrics.record_failure(
                backend_name="unknown",  # Error response doesn't have backend info
                error_code=result.error.error_code
            )
    
    # Extract successful analyses
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    logger.info(
        f"Analysis complete: {len(successful)} succeeded, "
        f"{len(failed)} failed"
    )
    
    if not successful:
        # All analyses failed
        raise HTTPException(
            status_code=503,
            detail=(
                f"All {len(results)} analyses failed. "
                f"Primary and fallback backends unavailable."
            )
        )
    
    # Synthesize results
    all_themes = []
    all_actions = []
    
    for result in successful:
        all_themes.extend(t.theme for t in result.analysis.themes)
        all_actions.extend(
            a.action for a in result.analysis.suggested_actions
        )
    
    # Deduplicate themes
    unique_themes = list(dict.fromkeys(all_themes))[:10]
    
    # Deduplicate actions
    unique_actions = list(dict.fromkeys(all_actions))[:10]
    
    # Create summary
    summary = _create_summary(
        successful_count=len(successful),
        total_count=len(results),
        themes=unique_themes
    )
    
    # Get backend stats
    backend_stats = metrics.get_all_stats()
    
    return ConsciousnessCheckResponse(
        success=True,
        request_id=successful[0].analysis.request_id,
        summary=summary,
        themes=unique_themes,
        suggested_actions=unique_actions,
        source_analyses=len(successful),
        backend_stats=backend_stats
    )


def _create_summary(
    successful_count: int,
    total_count: int,
    themes: list[str]
) -> str:
    """
    Create consciousness check summary.
    
    Args:
        successful_count: Number of successful analyses
        total_count: Total analyses attempted
        themes: Extracted themes
    
    Returns:
        Summary text
    """
    if successful_count == total_count:
        status = f"Analyzed all {total_count} thoughts"
    else:
        failed = total_count - successful_count
        status = (
            f"Analyzed {successful_count}/{total_count} thoughts "
            f"({failed} failed)"
        )
    
    if themes:
        theme_list = ", ".join(themes[:3])
        if len(themes) > 3:
            theme_list += f", and {len(themes) - 3} more"
        
        return (
            f"{status}. "
            f"Main themes: {theme_list}."
        )
    else:
        return f"{status}. No clear themes identified."


# ============================================================================
# Enhanced Consciousness Check v3 - Personal, Contextual Analysis
# ============================================================================


class EnhancedConsciousnessCheckRequest(BaseModel):
    """Request for enhanced consciousness check"""
    
    depth: str = Field(
        default="smart",
        description="Analysis depth: quick (last 5), standard (last 10), deep (last 20), smart (adaptive)"
    )
    focus_tags: Optional[list[str]] = Field(
        default=None,
        description="Optional tags to focus analysis on"
    )


class SurfacedThoughtRef(BaseModel):
    """Reference to a surfaced thought"""
    
    id: str = Field(..., description="Thought ID")
    content: str = Field(..., description="Thought content")
    relevance_score: float = Field(..., description="Relevance score 0-1")
    reason: str = Field(..., description="Why this thought was surfaced")


class SuggestedAction(BaseModel):
    """Suggested action from analysis"""
    
    action: str = Field(..., description="Action type")
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Action description")
    priority: Optional[str] = Field(None, description="Suggested priority")


class EnhancedConsciousnessCheckResponse(BaseModel):
    """Response from enhanced consciousness check"""
    
    success: bool = Field(..., description="Whether analysis succeeded")
    summary: str = Field(..., description="Personal, contextual summary")
    themes: list[str] = Field(default=[], description="Discovered themes")
    surfaced_thoughts: list[SurfacedThoughtRef] = Field(
        default=[],
        description="Relevant thoughts surfaced"
    )
    suggested_actions: list[SuggestedAction] = Field(
        default=[],
        description="Suggested next actions"
    )
    productivity_insight: Optional[str] = Field(
        None,
        description="Productivity observation"
    )
    encouragement: Optional[str] = Field(
        None,
        description="Encouraging note"
    )
    thoughts_analyzed: int = Field(..., description="Number of thoughts analyzed")
    backend_used: Optional[str] = Field(None, description="AI backend used")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="When analysis completed"
    )


@router.post(
    "/consciousness-check-v3",
    response_model=EnhancedConsciousnessCheckResponse,
    summary="Enhanced consciousness check (personal, contextual)",
    description=(
        "Analyze recent thoughts with personal context. "
        "References your projects, patterns, and work style. "
        "Produces warm, encouraging insights rather than sterile analysis."
    )
)
async def enhanced_consciousness_check(
    request_body: EnhancedConsciousnessCheckRequest,
    request: Request,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
) -> EnhancedConsciousnessCheckResponse:
    """
    Enhanced consciousness check with personal context.
    
    This version:
    - Loads your user profile (projects, interests, patterns)
    - References your ongoing work in the analysis
    - Uses warm, encouraging language
    - Provides actionable, contextual suggestions
    
    Args:
        request_body: Analysis parameters
        request: FastAPI request (for app state access)
        api_key: API key for authentication
        db: Database session
    
    Returns:
        EnhancedConsciousnessCheckResponse with personal insights
    """
    logger.info(f"Enhanced consciousness check: depth={request_body.depth}")
    
    # Get user ID
    user_id = UUID(get_current_user_id())
    
    # Get orchestrator from app state
    if not hasattr(request.app.state, 'orchestrator'):
        raise HTTPException(
            status_code=503,
            detail="AI backends not initialized"
        )
    
    orchestrator = request.app.state.orchestrator
    
    # Import and use the enhanced service
    from ...services.enhanced_consciousness_check_service import (
        EnhancedConsciousnessCheckService,
        AnalysisDepthConfig
    )
    
    from ...models.settings import SettingsDepthType
    
    # Map depth string to config
    # Use SMART mode with different thresholds for all variants
    depth_configs = {
        "quick": AnalysisDepthConfig(
            depth_type=SettingsDepthType.SMART,
            max_thoughts=5,
            min_thoughts=3
        ),
        "standard": AnalysisDepthConfig(
            depth_type=SettingsDepthType.SMART,
            max_thoughts=10,
            min_thoughts=5
        ),
        "deep": AnalysisDepthConfig(
            depth_type=SettingsDepthType.SMART,
            max_thoughts=20,
            min_thoughts=10
        ),
        "smart": AnalysisDepthConfig(
            depth_type=SettingsDepthType.SMART,
            max_thoughts=15,
            min_thoughts=5
        ),
    }
    depth_config = depth_configs.get(request_body.depth, depth_configs["smart"])
    
    # Run enhanced analysis
    from ...services.settings_service import SettingsService
    from ...services.user_profile_service import UserProfileService
    
    settings_service = SettingsService(db)
    profile_service = UserProfileService(db)
    
    service = EnhancedConsciousnessCheckService(
        db=db,
        ai_orchestrator=orchestrator,
        settings_service=settings_service,
        user_profile_service=profile_service
    )
    result = await service.run_consciousness_check(
        user_id=user_id,
        depth_config=depth_config,
        focus_tags=request_body.focus_tags
    )
    
    if not result:
        return EnhancedConsciousnessCheckResponse(
            success=False,
            summary="I couldn't complete the analysis right now. This might be a temporary issue - try again in a moment.",
            thoughts_analyzed=0,
            timestamp=datetime.now(UTC).isoformat()
        )
    
    return EnhancedConsciousnessCheckResponse(
        success=True,
        summary=result.summary,
        themes=result.themes,
        surfaced_thoughts=[
            SurfacedThoughtRef(
                id=str(t["id"]),
                content=t["content"][:200] + "..." if len(t.get("content", "")) > 200 else t.get("content", ""),
                relevance_score=t.get("relevance_score", 0.8),
                reason=t.get("reason", "Related to current focus")
            )
            for t in result.surfaced_thoughts[:5]
        ],
        suggested_actions=[
            SuggestedAction(
                action=a.get("action", "task"),
                title=a.get("title", "Follow up"),
                description=a.get("description", ""),
                priority=a.get("priority")
            )
            for a in result.suggested_actions[:3]
        ],
        productivity_insight=result.productivity_insight,
        encouragement=result.encouragement,
        thoughts_analyzed=result.thoughts_analyzed,
        backend_used=result.backend_used,
        timestamp=result.timestamp.isoformat() if result.timestamp else datetime.now(UTC).isoformat()
    )
