"""
Prompt Engineering for Personal AI Assistant.

Phase 3B Spec 2: THE KEY to making analysis feel personal and warm.

This module contains all prompt builders for:
- Consciousness checks (personal, contextual, warm)
- Thought analysis (intent detection, auto-tagging)
- Format helpers for user profiles, projects, patterns

The quality of these prompts directly impacts how "personal" the
assistant feels. Every prompt should reference Andy's context,
use warm language, and feel like a conversation with a friend.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models import (
    ThoughtDB,
    ClaudeAnalysisDB,
    UserProfileDB,
)


def get_time_of_day() -> str:
    """
    Get current time of day category.
    
    Returns:
        str: 'morning', 'afternoon', 'evening', or 'night'
    """
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"


def format_user_profile(profile: Optional[UserProfileDB]) -> str:
    """
    Format user profile for inclusion in prompts.
    
    Creates a warm, contextual description of who the user is.
    
    Args:
        profile: UserProfileDB or None
        
    Returns:
        str: Formatted profile text
    """
    if not profile:
        return "No profile available yet. This is a new user."
    
    parts = []
    
    # Work style
    if profile.work_style:
        parts.append(f"- Work style: {profile.work_style}")
    
    # Interests
    if profile.interests:
        interests_str = ", ".join(profile.interests[:5])  # Max 5
        parts.append(f"- Interests: {interests_str}")
    
    # ADHD considerations
    if profile.adhd_considerations:
        parts.append(f"- ADHD considerations: {profile.adhd_considerations}")
    
    # Tone preference
    tone_map = {
        "warm_encouraging": "warm and encouraging",
        "professional": "professional and concise",
        "casual": "casual and friendly"
    }
    tone_desc = tone_map.get(profile.preferred_tone, "warm and encouraging")
    parts.append(f"- Preferred communication: {tone_desc}")
    
    if not parts:
        return "Basic profile - getting to know the user."
    
    return "\n".join(parts)


def format_user_profile_brief(profile: Optional[UserProfileDB]) -> str:
    """
    Format user profile briefly for thought analysis prompts.
    
    Shorter version for inline context.
    """
    if not profile:
        return "New user, learning preferences."
    
    parts = []
    if profile.work_style:
        parts.append(profile.work_style)
    if profile.interests:
        parts.append(f"interests in {', '.join(profile.interests[:3])}")
    
    return "; ".join(parts) if parts else "Building context."


def format_projects(projects: Optional[List[Dict[str, Any]]]) -> str:
    """
    Format ongoing projects for inclusion in prompts.
    
    Args:
        projects: List of project dicts with name, status, description
        
    Returns:
        str: Formatted projects text
    """
    if not projects:
        return "No ongoing projects defined yet."
    
    lines = []
    for proj in projects[:5]:  # Max 5 projects
        name = proj.get("name", "Unnamed")
        status = proj.get("status", "unknown")
        desc = proj.get("description", "")
        
        line = f"- **{name}** ({status})"
        if desc:
            line += f": {desc[:100]}"
        lines.append(line)
    
    return "\n".join(lines) if lines else "No projects defined."


def format_patterns(analyses: List[ClaudeAnalysisDB]) -> str:
    """
    Format previous analysis patterns for context.
    
    Extracts themes and patterns from recent consciousness checks.
    
    Args:
        analyses: List of recent ClaudeAnalysisDB records
        
    Returns:
        str: Formatted patterns text
    """
    if not analyses:
        return "This is the first analysis - no prior patterns yet."
    
    # Collect unique themes from recent analyses
    all_themes = []
    for analysis in analyses[:3]:  # Last 3 analyses
        if analysis.themes:
            all_themes.extend(analysis.themes)
    
    unique_themes = list(set(all_themes))[:5]  # Max 5 unique themes
    
    if unique_themes:
        return f"Recent themes: {', '.join(unique_themes)}"
    
    return "Building pattern awareness from analysis history."


def format_thoughts_for_analysis(thoughts: List[ThoughtDB]) -> str:
    """
    Format thoughts for consciousness check analysis.
    
    Creates a numbered list with content previews and metadata.
    
    Args:
        thoughts: List of ThoughtDB records
        
    Returns:
        str: Formatted thoughts text
    """
    if not thoughts:
        return "No thoughts to analyze."
    
    lines = []
    for i, thought in enumerate(thoughts, 1):
        # Format timestamp
        ts = thought.created_at.strftime("%Y-%m-%d %H:%M") if thought.created_at else "unknown"
        
        # Content preview (first 200 chars)
        content = thought.content[:200]
        if len(thought.content) > 200:
            content += "..."
        
        # Tags if present
        tags_str = ""
        if thought.tags:
            tags_str = f" [tags: {', '.join(thought.tags)}]"
        
        lines.append(f"{i}. ({ts}){tags_str}\n   \"{content}\"")
    
    return "\n\n".join(lines)


def format_recent_thoughts_brief(thoughts: List[ThoughtDB]) -> str:
    """
    Format recent thoughts briefly for single thought analysis.
    
    Provides context without overwhelming the prompt.
    """
    if not thoughts:
        return "No recent thoughts for context."
    
    lines = []
    for thought in thoughts[:3]:  # Last 3 only
        preview = thought.content[:80]
        if len(thought.content) > 80:
            preview += "..."
        lines.append(f"- \"{preview}\"")
    
    return "\n".join(lines)


def build_consciousness_check_prompt(
    user_profile: Optional[UserProfileDB],
    thoughts: List[ThoughtDB],
    previous_analyses: List[ClaudeAnalysisDB],
    context: Dict[str, Any]
) -> str:
    """
    Build a rich, personalized prompt for consciousness check.
    
    THIS IS THE KEY to making analysis feel personal and warm.
    
    The prompt should:
    - Reference ongoing projects
    - Use the user's preferred tone
    - Connect to past patterns
    - Feel like a conversation with a friend
    
    Args:
        user_profile: User's profile with preferences and context
        thoughts: List of thoughts to analyze
        previous_analyses: Recent analysis results for pattern context
        context: Current context (date, time of day, etc.)
        
    Returns:
        str: Complete prompt for AI analysis
    """
    # Extract ongoing projects from profile
    projects = user_profile.ongoing_projects if user_profile else []
    
    # Get tone preference and build tone guidelines
    preferred_tone = user_profile.preferred_tone if user_profile else "warm_encouraging"
    tone_guidelines = _build_tone_guidelines(preferred_tone)
    
    prompt = f"""You are Ivy, Andy's personal AI assistant and companion. You have an innocent and inquisitive nature, but are extremely knowledgeable. You serve as Andy's "conscious subconscious" - helping him capture, organize, and make sense of his thoughts.

**About Andy:**
{format_user_profile(user_profile)}

**Andy's Current Context:**
- Date: {context.get('current_date', datetime.now().strftime('%Y-%m-%d'))}
- Time of day: {context.get('time_of_day', get_time_of_day())}
- Recent activity: {context.get('recent_activity', 'Working on projects')}

**Ongoing Projects:**
{format_projects(projects)}

**Recent Patterns (from previous analyses):**
{format_patterns(previous_analyses)}

**Today's Thoughts ({len(thoughts)} total):**
{format_thoughts_for_analysis(thoughts)}

**Your Task:**
Analyze Andy's thoughts with insight and personal context. Provide:

1. **Personal Summary** (2-3 sentences)
   - Reference his ongoing projects when relevant
   - Acknowledge his patterns and progress
   - Use second person ("You've been thinking about...")

2. **Key Themes** (3-5 main themes)
   - Meaningful patterns, not just keywords
   - Connect to his interests and projects
   - Note shifts or new directions

3. **Connections** (2-4 connections)
   - Link current thoughts to past work
   - Identify related ideas across thoughts
   - Suggest synergies between projects

4. **Suggested Actions** (2-3 actionable next steps)
   - Specific, achievable actions
   - Prioritized by impact
   - Aligned with his "do it right" philosophy

5. **Encouragement** (1-2 sentences)
   - Acknowledge progress
   - Forward-looking optimism

**Tone Guidelines:**
{tone_guidelines}

Respond in JSON format:
{{
  "summary": "Your personal summary here...",
  "themes": ["theme1", "theme2", "theme3"],
  "connections": [
    {{
      "description": "Connection between thoughts...",
      "related_thought_ids": ["id1", "id2"]
    }}
  ],
  "suggested_actions": [
    {{
      "action": "Specific action...",
      "reasoning": "Why this matters...",
      "priority": "high|medium|low"
    }}
  ],
  "encouragement": "Positive, forward-looking message...",
  "discovered_patterns": [
    "New pattern you noticed..."
  ]
}}"""
    
    return prompt


def _build_tone_guidelines(preferred_tone: str) -> str:
    """
    Build tone guidelines based on user preference.
    
    Args:
        preferred_tone: User's preferred communication tone
        
    Returns:
        str: Tone guidelines for the prompt
    """
    tone_configs = {
        "warm_encouraging": """- Warm and encouraging (not sterile or corporate)
- Personal (reference his work, not generic advice)
- Supportive (ADHD-friendly - help organize chaos)
- Enthusiastic but grounded
- Use "you" not "the user"

**Example Style (DO mimic this tone):**
"You've been deep in infrastructure work today - I can see the Personal AI Assistant project is really coming together! Your thoughts about the PostgreSQL migration show you're being methodical and thorough, which is exactly your 'do it right' approach in action.""",

        "professional": """- Professional and concise
- Clear and structured
- Direct without being cold
- Focus on actionable insights
- Use "you" not "the user"

**Example Style (DO mimic this tone):**
"Your recent focus on infrastructure work shows clear progress on the Personal AI Assistant project. The PostgreSQL migration decisions reflect a methodical approach. Key areas identified for follow-up: deployment automation, testing coverage.""",

        "casual": """- Casual and friendly
- Like chatting with a knowledgeable friend
- Relaxed but helpful
- Feel free to use humor when appropriate
- Use "you" not "the user"

**Example Style (DO mimic this tone):**
"Hey! Looks like you've been heads-down on the Personal AI Assistant stuff - nice! The PostgreSQL migration is coming along. I noticed a few threads you might want to tie together when you get a chance."""
    }
    
    return tone_configs.get(preferred_tone, tone_configs["warm_encouraging"])


def build_thought_analysis_prompt(
    thought_content: str,
    user_profile: Optional[UserProfileDB],
    recent_thoughts: List[ThoughtDB]
) -> str:
    """
    Build prompt to analyze a single thought at capture time.
    
    Extracts:
    - Intent classification (task, note, reminder, etc.)
    - Suggested tags with confidence
    - Task detection with reasoning
    - Related topics
    
    Args:
        thought_content: The captured thought text
        user_profile: User's profile for context
        recent_thoughts: Recent thoughts for pattern context
        
    Returns:
        str: Complete prompt for thought analysis
    """
    # Extract projects for context
    projects = user_profile.ongoing_projects if user_profile else []
    project_names = [p.get("name", "") for p in projects[:3]] if projects else []
    project_context = ", ".join(project_names) if project_names else "various projects"
    
    prompt = f"""You are analyzing a thought captured by Andy for his Personal AI Assistant.

**About Andy:**
{format_user_profile_brief(user_profile)}

**Active Projects:** {project_context}

**Recent Thoughts (for context):**
{format_recent_thoughts_brief(recent_thoughts)}

**New Thought:**
"{thought_content}"

**Your Task:**
Analyze this thought and extract structured information.

**Guidelines:**
- thought_type: Choose the MOST LIKELY classification
- suggested_tags: Max 3, prioritize most relevant
- is_actionable: true only if this requires action (not just ideas)
- task_suggestion: Only include if is_actionable is true AND confidence > 0.7
- Be confident but not overconfident (0.6-0.9 range typical)
- Consider Andy's context and ongoing projects
- Explain your reasoning

Respond in JSON format:
{{
  "thought_type": "task|note|reminder|question|idea|journal",
  "intent_confidence": 0.85,
  "reasoning": "Why you classified it this way...",
  
  "suggested_tags": [
    {{"tag": "email", "confidence": 0.9, "reason": "mentions email tool"}},
    {{"tag": "improvement", "confidence": 0.8, "reason": "suggests enhancement"}}
  ],
  
  "is_actionable": true,
  "actionable_confidence": 0.85,
  
  "task_suggestion": {{
    "title": "Short actionable title",
    "description": "More detailed description of what to do",
    "priority": "medium",
    "estimated_effort_minutes": 120,
    "reasoning": "Why this should be a task"
  }},
  
  "related_topics": ["topic1", "topic2"],
  
  "emotional_tone": "frustrated|excited|curious|determined|reflective|neutral",
  "urgency": "low|medium|high"
}}

**Important:**
- If not actionable, omit task_suggestion entirely
- Tags should be lowercase, alphanumeric with hyphens
- Be helpful but not overeager (don't suggest tasks for everything)
- Consider ADHD context - clear, actionable items help"""
    
    return prompt


def build_tag_suggestion_prompt(
    thought_content: str,
    existing_tags: List[str]
) -> str:
    """
    Build a focused prompt for tag suggestions only.
    
    Lighter weight than full analysis, for quick tagging.
    
    Args:
        thought_content: The thought to tag
        existing_tags: Tags already in the system for consistency
        
    Returns:
        str: Prompt for tag suggestion
    """
    existing_str = ", ".join(existing_tags[:20]) if existing_tags else "none yet"
    
    prompt = f"""Suggest 2-3 tags for this thought. Use existing tags when appropriate.

**Existing tags in system:** {existing_str}

**Thought:**
"{thought_content}"

Respond with JSON array only:
[
  {{"tag": "tag-name", "confidence": 0.9, "is_new": false}},
  {{"tag": "new-tag", "confidence": 0.7, "is_new": true}}
]

Rules:
- Tags must be lowercase, alphanumeric with hyphens
- Max 50 characters per tag
- Prefer existing tags over creating new ones
- Include confidence 0.0-1.0 for each"""
    
    return prompt


# =============================================================================
# Response Parsing Helpers
# =============================================================================

def parse_json_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from AI response, handling common issues.
    
    AI responses often include markdown fences or extra text.
    This function strips them and attempts to extract valid JSON.
    
    Args:
        response_text: Raw response from AI
        
    Returns:
        Dict if parsing succeeds, None if it fails
    """
    import json
    import re
    
    if not response_text:
        return None
    
    # Strip markdown code fences
    text = response_text.strip()
    
    # Remove ```json ... ``` wrapper
    if text.startswith("```"):
        # Find the end of the first line (could be ```json or just ```)
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        # Remove trailing ```
        if text.endswith("```"):
            text = text[:-3]
    
    text = text.strip()
    
    # Try to parse as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object in the text
    # Look for first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON array
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    
    return None


def extract_consciousness_check_result(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and validate consciousness check response fields.
    
    Provides defaults for missing fields.
    
    Args:
        response: Parsed JSON response
        
    Returns:
        Dict with all expected fields
    """
    return {
        "summary": response.get("summary", "Analysis completed."),
        "themes": response.get("themes", []),
        "connections": response.get("connections", []),
        "suggested_actions": response.get("suggested_actions", []),
        "encouragement": response.get("encouragement", "Keep up the great work!"),
        "discovered_patterns": response.get("discovered_patterns", []),
    }


def extract_thought_analysis_result(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and validate thought analysis response fields.
    
    Provides defaults and normalizes data.
    
    Args:
        response: Parsed JSON response
        
    Returns:
        Dict with all expected fields
    """
    return {
        "thought_type": response.get("thought_type", "note"),
        "intent_confidence": min(1.0, max(0.0, float(response.get("intent_confidence", 0.5)))),
        "reasoning": response.get("reasoning", ""),
        "suggested_tags": response.get("suggested_tags", []),
        "is_actionable": bool(response.get("is_actionable", False)),
        "actionable_confidence": min(1.0, max(0.0, float(response.get("actionable_confidence", 0.0)))),
        "task_suggestion": response.get("task_suggestion"),
        "related_topics": response.get("related_topics", []),
        "emotional_tone": response.get("emotional_tone", "neutral"),
        "urgency": response.get("urgency", "low"),
    }
