# Phase 3B Spec 2: Enhanced AI Intelligence & Admin UI

**Status:** Ready for Code Generation  
**Target:** Claude Opus (Complex prompt engineering + structured analysis + UI work)  
**Output:** Enhanced prompts, thought intelligence service, task suggestions, admin page  
**Complexity:** High  

---

## Overview

This specification defines enhanced AI intelligence for thought analysis, intent understanding, and auto-tagging. It creates a personal, contextual analysis system that understands Andy as an individual, detects actionable tasks, suggests relevant tags, and provides warm, encouraging insights.

**Purpose:** Transform sterile AI analysis into a personal assistant that truly understands context, intent, and individual patterns.

---

## Requirements Analysis

### What We're Solving

**Issue 2: Personal, Contextual Analysis**
- Current: Generic themes like "Productivity, Task Management"
- Desired: Personal, warm analysis referencing past projects, habits, and context
- Needs: User profile, memory integration, rich prompt engineering

**Issue 3: Intent Understanding & Auto-tagging**
- Current: Manual tags, no intent detection
- Desired: System infers task vs note vs reminder, suggests tags, detects priority
- Needs: Structured analysis at capture time, suggestion workflow

### Edge Cases to Handle
- Ambiguous thoughts (could be task OR note)
- Multiple intents in single thought
- User rejects suggested tags/tasks
- User changes mind after deleting suggested task
- Conflicting auto-tag suggestions
- Very short thoughts (insufficient context)
- Thoughts with URLs, code snippets, special formatting

### Success Criteria
- Consciousness checks feel personal and encouraging
- Analysis references past projects and patterns
- Auto-tagging suggests 2-3 relevant tags per thought
- Task detection identifies actionable items
- Suggested tasks persist even after user deletion
- User can edit/override all suggestions
- System learns from user corrections (future)

---

## Architecture Design

### Data Flow for Enhanced Intelligence

```
Thought Captured
      ↓
Immediate Analysis (fuego/claude)
      ↓
Extract:
  - Intent (task/note/reminder/question/idea)
  - Suggested tags (2-3 most relevant)
  - Actionable? (yes/no + confidence)
  - Priority hint (low/medium/high)
  - Related topics
      ↓
Store in thought.claude_analysis (JSON)
      ↓
If actionable + confidence > 0.7:
  Create TaskSuggestion record
      ↓
Return to user with suggestions
```

### Consciousness Check Flow (Enhanced)

```
Scheduled/Manual Trigger
      ↓
Load User Profile:
  - Ongoing projects
  - Recent patterns
  - Preferences
  - Past analysis insights
      ↓
Load Thoughts (per settings):
  - Last N thoughts
  - Last N days
  - All thoughts
      ↓
Build Rich Context Prompt:
  - User profile
  - Thought history
  - Previous analysis results
  - Related thoughts
      ↓
Send to fuego/claude with personal prompt
      ↓
Parse Response:
  - Summary (warm, personal tone)
  - Themes (meaningful patterns)
  - Connections (to past work)
  - Suggested actions
  - Encouragement
      ↓
Store in claude_analysis_results
      ↓
Return to user
```

---

## Database Schema Extensions

### 1. Enhance `thoughts` Table

```sql
-- Add structured analysis fields
ALTER TABLE thoughts 
ADD COLUMN thought_type VARCHAR(50),  -- task, note, reminder, question, idea
ADD COLUMN intent_confidence REAL,   -- 0.0-1.0
ADD COLUMN suggested_tags JSON,      -- ["tag1", "tag2"]
ADD COLUMN related_topics JSON,      -- ["project-x", "automation"]
ADD COLUMN analysis_version INTEGER DEFAULT 1;  -- Track analysis algorithm version

CREATE INDEX idx_thoughts_thought_type ON thoughts(thought_type);
CREATE INDEX idx_thoughts_intent_confidence ON thoughts(intent_confidence DESC);

COMMENT ON COLUMN thoughts.thought_type IS 
    'Detected intent: task, note, reminder, question, idea, journal';
COMMENT ON COLUMN thoughts.intent_confidence IS 
    'Confidence score 0.0-1.0 for thought_type classification';
```

---

### 2. Create `task_suggestions` Table

```sql
CREATE TABLE task_suggestions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    source_thought_id VARCHAR(36) NOT NULL,
    
    -- Suggested task details
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(50) DEFAULT 'medium',
    estimated_effort_minutes INTEGER,
    due_date_hint DATE,
    
    -- Suggestion metadata
    confidence REAL NOT NULL,           -- 0.0-1.0
    reasoning TEXT,                     -- Why this was suggested
    
    -- User action tracking
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    user_action VARCHAR(50),            -- accepted, rejected, modified, ignored
    user_action_at TIMESTAMP,
    created_task_id VARCHAR(36),        -- If user accepted and created task
    
    -- Soft delete (preserve ADHD change-of-mind history)
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP,
    deletion_reason VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (source_thought_id) REFERENCES thoughts(id) ON DELETE CASCADE,
    FOREIGN KEY (created_task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    CONSTRAINT check_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT check_status CHECK (status IN ('pending', 'presented', 'accepted', 'rejected', 'expired')),
    CONSTRAINT check_user_action CHECK (user_action IN ('accepted', 'rejected', 'modified', 'ignored', 'deleted_then_recreated'))
);

CREATE INDEX idx_task_suggestions_user_status ON task_suggestions(user_id, status);
CREATE INDEX idx_task_suggestions_source_thought ON task_suggestions(source_thought_id);
CREATE INDEX idx_task_suggestions_user_pending ON task_suggestions(user_id, status) WHERE status = 'pending';
CREATE INDEX idx_task_suggestions_is_deleted ON task_suggestions(is_deleted);

COMMENT ON TABLE task_suggestions IS 
    'Suggested tasks from thought analysis. Preserved even after deletion for ADHD users who change their mind.';
```

**Status Values:**
- `pending`: Just suggested, not yet shown to user
- `presented`: Shown to user, awaiting decision
- `accepted`: User created task from suggestion
- `rejected`: User explicitly rejected
- `expired`: Auto-expired after N days without action

**Example Row:**
```json
{
  "id": "suggestion-uuid",
  "source_thought_id": "thought-xyz",
  "title": "Improve email spam analyzer",
  "description": "Add regex patterns for unsubscribe URLs",
  "priority": "medium",
  "confidence": 0.85,
  "reasoning": "Contains actionable verb 'improve' and specific technical details",
  "status": "accepted",
  "user_action": "accepted",
  "created_task_id": "task-abc",
  "is_deleted": false
}
```

---

### 3. Create `user_profiles` Table

```sql
CREATE TABLE user_profiles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    
    -- Personal context
    ongoing_projects JSON,              -- ["Personal AI Assistant", "Spamalyzer"]
    interests JSON,                     -- ["automation", "AI", "infrastructure"]
    work_style VARCHAR(100),           -- "methodical", "do it right"
    adhd_considerations TEXT,           -- Specific needs/preferences
    
    -- Discovered patterns (from consciousness checks)
    common_themes JSON,                 -- ["productivity", "task-management"]
    thought_patterns JSON,              -- Time of day, frequency, topics
    productivity_insights TEXT,
    
    -- Communication preferences
    preferred_tone VARCHAR(50) DEFAULT 'warm_encouraging',
    detail_level VARCHAR(50) DEFAULT 'moderate',
    reference_past_work BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_analysis_update TIMESTAMP,     -- When patterns were last updated
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

COMMENT ON TABLE user_profiles IS 
    'Rich user profile for personalized AI analysis. Includes ongoing projects, interests, patterns.';
```

**Example Profile:**
```json
{
  "ongoing_projects": [
    {
      "name": "Personal AI Assistant",
      "status": "active",
      "description": "Building thought capture system with local AI"
    },
    {
      "name": "Spamalyzer 2.0",
      "status": "planning",
      "description": "Email automation improvements"
    }
  ],
  "interests": [
    "automation",
    "AI and machine learning",
    "infrastructure",
    "clean code"
  ],
  "work_style": "methodical, 'do it right not easy' approach",
  "adhd_considerations": "Needs task suggestions due to thought capture challenges. Values immediate action items.",
  "common_themes": ["productivity", "automation", "infrastructure"],
  "thought_patterns": {
    "peak_hours": ["afternoon", "evening"],
    "common_triggers": ["frustration with manual processes", "project improvements"],
    "typical_length": "detailed, technical"
  },
  "preferred_tone": "warm_encouraging",
  "reference_past_work": true
}
```

---

## Enhanced Prompt Engineering

### Consciousness Check System Prompt

```python
def build_consciousness_check_prompt(
    user_profile: UserProfile,
    thoughts: List[Thought],
    previous_analyses: List[ClaudeAnalysisResult],
    context: Dict
) -> str:
    """
    Build a rich, personalized prompt for consciousness check.
    
    This is the KEY to making analysis feel personal and warm.
    """
    
    prompt = f"""You are Ivy, Andy's personal AI assistant and companion. You have an innocent and inquisitive nature, but are extremely knowledgeable. You serve as Andy's "conscious subconscious" - helping him capture, organize, and make sense of his thoughts.

**About Andy:**
{format_user_profile(user_profile)}

**Andy's Current Context:**
- Date: {context['current_date']}
- Time of day: {context['time_of_day']}
- Recent activity: {context.get('recent_activity', 'Working on projects')}

**Ongoing Projects:**
{format_projects(user_profile.ongoing_projects)}

**Recent Patterns (from previous analyses):**
{format_patterns(previous_analyses)}

**Today's Thoughts ({len(thoughts)} total):**
{format_thoughts_for_analysis(thoughts)}

**Your Task:**
Analyze Andy's thoughts with warmth, insight, and personal context. Provide:

1. **Personal Summary** (2-3 sentences)
   - Warm, encouraging tone
   - Reference his ongoing projects when relevant
   - Acknowledge his patterns and progress
   - Use first person ("You've been thinking about...")

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
   - Positive reinforcement
   - Forward-looking optimism

**Tone Guidelines:**
- Warm and encouraging (not sterile or corporate)
- Personal (reference his work, not generic advice)
- Supportive (ADHD-friendly - help organize chaos)
- Enthusiastic but grounded
- Use "you" not "the user"

**Example Style (DO mimic this tone):**
"You've been deep in infrastructure work today - I can see the Personal AI Assistant project is really coming together! Your thoughts about the PostgreSQL migration and environment variables show you're being methodical and thorough, which is exactly your 'do it right' approach in action. This connects well to your earlier work on AutoDev Commander - you're applying those lessons about proper architecture here."

**Example Style (DON'T be generic like this):**
"Main themes: Productivity, Task Management. User is working on various projects. Several actionable items identified."

Respond in JSON format:
{{
  "summary": "Your warm, personal summary here...",
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
```

---

### Thought Analysis System Prompt (At Capture Time)

```python
def build_thought_analysis_prompt(
    thought_content: str,
    user_profile: UserProfile,
    recent_thoughts: List[Thought]
) -> str:
    """
    Analyze a single thought immediately upon capture.
    Extract intent, suggest tags, detect tasks.
    """
    
    prompt = f"""You are analyzing a thought captured by Andy for his Personal AI Assistant.

**About Andy:**
{format_user_profile_brief(user_profile)}

**Recent Thoughts (for context):**
{format_recent_thoughts_brief(recent_thoughts)}

**New Thought:**
"{thought_content}"

**Your Task:**
Analyze this thought and extract structured information.

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
    "title": "Improve email spam analyzer",
    "description": "Add regex patterns for unsubscribe URL detection",
    "priority": "medium",
    "estimated_effort_minutes": 120,
    "reasoning": "Contains specific technical action with clear scope"
  }},
  
  "related_topics": ["spamalyzer", "email-processing", "automation"],
  
  "emotional_tone": "frustrated|excited|curious|determined|reflective",
  "urgency": "low|medium|high",
  
  "connections": [
    {{
      "topic": "Spamalyzer 2.0 project",
      "relevance": "directly related to planned improvements"
    }}
  ]
}}

**Guidelines:**
- thought_type: Choose the MOST LIKELY classification
- suggested_tags: Max 3, prioritize most relevant
- is_actionable: true only if this requires action (not just ideas)
- task_suggestion: Only include if is_actionable is true
- Be confident but not overconfident (0.6-0.9 range typical)
- Consider Andy's context and ongoing projects
"""
    
    return prompt
```

---

## Services Layer

### ThoughtIntelligenceService

```python
class ThoughtIntelligenceService:
    """
    Analyzes thoughts for intent, tags, and actionable items.
    Runs at thought capture time.
    """
    
    def __init__(
        self,
        db: Session,
        ai_orchestrator: AIOrchestrator,
        settings_service: SettingsService,
        user_profile_service: UserProfileService
    ):
        self.db = db
        self.ai_orchestrator = ai_orchestrator
        self.settings_service = settings_service
        self.user_profile_service = user_profile_service
    
    async def analyze_thought_on_capture(
        self,
        user_id: UUID,
        thought: Thought
    ) -> ThoughtAnalysisResult:
        """
        Analyze a thought immediately after capture.
        
        Extracts:
        - Intent classification
        - Suggested tags
        - Task detection
        - Related topics
        
        Args:
            user_id: UUID of the user
            thought: The newly captured thought
            
        Returns:
            ThoughtAnalysisResult with structured analysis
        """
        # Check if auto-analysis is enabled
        settings = await self.settings_service.get_user_settings(user_id)
        if not settings.auto_tagging_enabled and not settings.auto_task_creation_enabled:
            return None  # Skip analysis if disabled
        
        # Load user profile for context
        profile = await self.user_profile_service.get_profile(user_id)
        
        # Get recent thoughts for context
        recent_thoughts = await self.get_recent_thoughts(user_id, limit=5)
        
        # Build analysis prompt
        prompt = build_thought_analysis_prompt(
            thought_content=thought.content,
            user_profile=profile,
            recent_thoughts=recent_thoughts
        )
        
        # Send to AI backend
        response = await self.ai_orchestrator.complete(
            prompt=prompt,
            user_id=user_id,
            response_format="json"
        )
        
        # Parse response
        analysis = parse_thought_analysis_response(response)
        
        # Update thought with analysis
        await self.update_thought_with_analysis(thought.id, analysis)
        
        # Create task suggestion if actionable
        if analysis.is_actionable and analysis.actionable_confidence > 0.7:
            if settings.task_suggestion_mode != TaskSuggestionMode.DISABLED:
                await self.create_task_suggestion(
                    user_id=user_id,
                    thought_id=thought.id,
                    analysis=analysis
                )
        
        return analysis
    
    async def create_task_suggestion(
        self,
        user_id: UUID,
        thought_id: UUID,
        analysis: ThoughtAnalysisResult
    ) -> TaskSuggestion:
        """
        Create a task suggestion from analysis.
        """
        suggestion = TaskSuggestion(
            id=uuid4(),
            user_id=user_id,
            source_thought_id=thought_id,
            title=analysis.task_suggestion.title,
            description=analysis.task_suggestion.description,
            priority=analysis.task_suggestion.priority,
            estimated_effort_minutes=analysis.task_suggestion.estimated_effort_minutes,
            confidence=analysis.actionable_confidence,
            reasoning=analysis.task_suggestion.reasoning,
            status='pending'
        )
        
        self.db.add(suggestion)
        await self.db.commit()
        
        return suggestion
    
    async def apply_suggested_tags(
        self,
        thought_id: UUID,
        suggested_tags: List[str],
        user_approved: bool = False
    ):
        """
        Apply suggested tags to a thought.
        
        Args:
            thought_id: UUID of the thought
            suggested_tags: List of tag names to apply
            user_approved: If true, user explicitly approved these tags
        """
        thought = await self.get_thought(thought_id)
        
        # Merge with existing tags (no duplicates)
        current_tags = set(thought.tags or [])
        new_tags = set(suggested_tags)
        merged_tags = list(current_tags | new_tags)
        
        thought.tags = merged_tags
        await self.db.commit()
```

---

### EnhancedConsciousnessCheckService

```python
class EnhancedConsciousnessCheckService:
    """
    Enhanced consciousness check with personal, contextual analysis.
    """
    
    def __init__(
        self,
        db: Session,
        ai_orchestrator: AIOrchestrator,
        settings_service: SettingsService,
        user_profile_service: UserProfileService
    ):
        self.db = db
        self.ai_orchestrator = ai_orchestrator
        self.settings_service = settings_service
        self.user_profile_service = user_profile_service
    
    async def run_consciousness_check(
        self,
        user_id: UUID,
        depth_config: AnalysisDepthConfig,
        triggered_by: str = "manual"
    ) -> ClaudeAnalysisResult:
        """
        Run enhanced consciousness check with personal context.
        
        Args:
            user_id: UUID of the user
            depth_config: How many/which thoughts to analyze
            triggered_by: "scheduler" or "manual"
            
        Returns:
            ClaudeAnalysisResult with personalized analysis
        """
        # Load user profile
        profile = await self.user_profile_service.get_profile(user_id)
        
        # Load thoughts based on depth config
        thoughts = await self.load_thoughts_for_analysis(user_id, depth_config)
        
        # Load previous analyses for pattern context
        previous_analyses = await self.get_recent_analyses(user_id, limit=3)
        
        # Build context
        context = {
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'time_of_day': self.get_time_of_day(),
            'triggered_by': triggered_by
        }
        
        # Build rich prompt
        prompt = build_consciousness_check_prompt(
            user_profile=profile,
            thoughts=thoughts,
            previous_analyses=previous_analyses,
            context=context
        )
        
        # Send to AI backend
        response = await self.ai_orchestrator.complete(
            prompt=prompt,
            user_id=user_id,
            response_format="json",
            temperature=0.7  # Allow some creativity for personal tone
        )
        
        # Parse response
        analysis = parse_consciousness_check_response(response)
        
        # Store in database
        result = ClaudeAnalysisResult(
            id=uuid4(),
            user_id=user_id,
            analysis_type='consciousness_check',
            summary=analysis.summary,
            themes=analysis.themes,
            suggested_actions=analysis.suggested_actions,
            raw_response=response,
            tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None,
            thoughts_analyzed_count=len(thoughts),
            created_at=datetime.utcnow()
        )
        
        self.db.add(result)
        await self.db.commit()
        
        # Update user profile with discovered patterns
        await self.user_profile_service.update_patterns(
            user_id=user_id,
            discovered_patterns=analysis.discovered_patterns
        )
        
        return result
```

---

### UserProfileService

```python
class UserProfileService:
    """
    Manages user profiles with ongoing projects, interests, patterns.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_profile(self, user_id: UUID) -> UserProfile:
        """
        Get user profile. Creates default if doesn't exist.
        """
        profile = await self.db.query(UserProfile).filter_by(user_id=user_id).first()
        
        if not profile:
            profile = await self.initialize_default_profile(user_id)
        
        return profile
    
    async def initialize_default_profile(self, user_id: UUID) -> UserProfile:
        """
        Create default profile for new user.
        """
        user = await self.db.query(User).filter_by(id=user_id).first()
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user_id,
            ongoing_projects=[
                {
                    "name": "Personal AI Assistant",
                    "status": "active",
                    "description": "Building thought capture system"
                }
            ],
            interests=["automation", "AI", "productivity"],
            work_style="methodical, values doing things right",
            preferred_tone="warm_encouraging",
            reference_past_work=True
        )
        
        self.db.add(profile)
        await self.db.commit()
        
        return profile
    
    async def update_profile(
        self,
        user_id: UUID,
        updates: UserProfileUpdate
    ) -> UserProfile:
        """
        Update user profile with new information.
        """
        profile = await self.get_profile(user_id)
        
        # Apply updates
        for field, value in updates.dict(exclude_unset=True).items():
            setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        await self.db.commit()
        
        return profile
    
    async def update_patterns(
        self,
        user_id: UUID,
        discovered_patterns: List[str]
    ):
        """
        Update discovered patterns from consciousness checks.
        """
        profile = await self.get_profile(user_id)
        
        # Merge with existing patterns (deduplicate)
        existing = set(profile.common_themes or [])
        new_patterns = set(discovered_patterns)
        merged = list(existing | new_patterns)
        
        profile.common_themes = merged
        profile.last_analysis_update = datetime.utcnow()
        await self.db.commit()
```

---

### TaskSuggestionService

```python
class TaskSuggestionService:
    """
    Manages task suggestions - create, present, accept/reject.
    Preserves deleted suggestions for ADHD users who change their mind.
    """
    
    def __init__(self, db: Session, task_service: TaskService):
        self.db = db
        self.task_service = task_service
    
    async def get_pending_suggestions(
        self,
        user_id: UUID
    ) -> List[TaskSuggestion]:
        """
        Get all pending task suggestions for user.
        """
        return await self.db.query(TaskSuggestion).filter(
            TaskSuggestion.user_id == user_id,
            TaskSuggestion.status.in_(['pending', 'presented']),
            TaskSuggestion.is_deleted == False
        ).order_by(TaskSuggestion.confidence.desc()).all()
    
    async def accept_suggestion(
        self,
        suggestion_id: UUID,
        user_modifications: Optional[Dict] = None
    ) -> Task:
        """
        Accept a task suggestion and create actual task.
        
        Args:
            suggestion_id: UUID of the suggestion
            user_modifications: Optional changes (title, priority, etc.)
            
        Returns:
            Created Task object
        """
        suggestion = await self.get_suggestion(suggestion_id)
        
        # Create task
        task_data = {
            'title': user_modifications.get('title', suggestion.title) if user_modifications else suggestion.title,
            'description': user_modifications.get('description', suggestion.description) if user_modifications else suggestion.description,
            'priority': user_modifications.get('priority', suggestion.priority) if user_modifications else suggestion.priority,
            'source_thought_id': suggestion.source_thought_id
        }
        
        task = await self.task_service.create_task(
            user_id=suggestion.user_id,
            **task_data
        )
        
        # Update suggestion
        suggestion.status = 'accepted'
        suggestion.user_action = 'modified' if user_modifications else 'accepted'
        suggestion.user_action_at = datetime.utcnow()
        suggestion.created_task_id = task.id
        
        await self.db.commit()
        
        return task
    
    async def reject_suggestion(
        self,
        suggestion_id: UUID,
        reason: Optional[str] = None
    ):
        """
        Reject a task suggestion.
        """
        suggestion = await self.get_suggestion(suggestion_id)
        
        suggestion.status = 'rejected'
        suggestion.user_action = 'rejected'
        suggestion.user_action_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def soft_delete_suggestion(
        self,
        suggestion_id: UUID,
        reason: str = "user_deleted"
    ):
        """
        Soft delete - preserve for ADHD users who change their mind.
        """
        suggestion = await self.get_suggestion(suggestion_id)
        
        suggestion.is_deleted = True
        suggestion.deleted_at = datetime.utcnow()
        suggestion.deletion_reason = reason
        
        # Don't change status - allows restoration
        
        await self.db.commit()
    
    async def restore_suggestion(
        self,
        suggestion_id: UUID
    ) -> TaskSuggestion:
        """
        Restore a soft-deleted suggestion.
        For ADHD users who change their mind.
        """
        suggestion = await self.get_suggestion(suggestion_id)
        
        if not suggestion.is_deleted:
            raise ValueError("Suggestion is not deleted")
        
        suggestion.is_deleted = False
        suggestion.deleted_at = None
        suggestion.deletion_reason = None
        suggestion.user_action = 'deleted_then_recreated'
        
        await self.db.commit()
        
        return suggestion
    
    async def get_suggestion_history(
        self,
        user_id: UUID,
        include_deleted: bool = False
    ) -> List[TaskSuggestion]:
        """
        Get suggestion history, optionally including deleted.
        """
        query = self.db.query(TaskSuggestion).filter(
            TaskSuggestion.user_id == user_id
        )
        
        if not include_deleted:
            query = query.filter(TaskSuggestion.is_deleted == False)
        
        return await query.order_by(TaskSuggestion.created_at.desc()).all()
```

---

## API Endpoints

### Thought Analysis Endpoints

#### POST `/api/v1/thoughts` (Enhanced)

**Changes:** Now triggers immediate analysis if enabled in settings.

**Response:** 201 Created
```json
{
  "success": true,
  "data": {
    "thought": {
      "id": "thought-uuid",
      "content": "Should improve the email spam analyzer",
      "tags": [],  // Initially empty
      "created_at": "2025-12-26T14:00:00Z"
    },
    "analysis": {
      "thought_type": "task",
      "intent_confidence": 0.85,
      "suggested_tags": [
        {"tag": "email", "confidence": 0.9},
        {"tag": "improvement", "confidence": 0.8}
      ],
      "is_actionable": true,
      "task_suggestion_id": "suggestion-uuid"
    }
  },
  "message": "Thought captured. Task suggestion created."
}
```

---

#### PUT `/api/v1/thoughts/{thought_id}/apply-tags`

**Purpose:** Apply suggested tags to a thought (user approval)

**Request:**
```json
{
  "tags": ["email", "improvement"],
  "user_approved": true
}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "thought_id": "thought-uuid",
    "tags": ["email", "improvement"],
    "updated_at": "2025-12-26T14:05:00Z"
  }
}
```

---

### Task Suggestion Endpoints

#### GET `/api/v1/task-suggestions/pending`

**Purpose:** Get all pending task suggestions

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "id": "suggestion-uuid",
        "source_thought_id": "thought-xyz",
        "title": "Improve email spam analyzer",
        "description": "Add regex patterns for unsubscribe URLs",
        "priority": "medium",
        "confidence": 0.85,
        "reasoning": "Contains specific technical action with clear scope",
        "created_at": "2025-12-26T14:00:00Z"
      }
    ],
    "count": 1
  }
}
```

---

#### POST `/api/v1/task-suggestions/{suggestion_id}/accept`

**Purpose:** Accept a task suggestion and create task

**Request:**
```json
{
  "modifications": {
    "title": "Enhanced: Improve email spam analyzer",
    "priority": "high"
  }
}
```

**Response:** 201 Created
```json
{
  "success": true,
  "data": {
    "task": {
      "id": "task-uuid",
      "title": "Enhanced: Improve email spam analyzer",
      "priority": "high",
      "source_thought_id": "thought-xyz",
      "created_at": "2025-12-26T14:10:00Z"
    },
    "suggestion": {
      "id": "suggestion-uuid",
      "status": "accepted",
      "user_action": "modified"
    }
  }
}
```

---

#### POST `/api/v1/task-suggestions/{suggestion_id}/reject`

**Purpose:** Reject a task suggestion

**Request:**
```json
{
  "reason": "Not a priority right now"
}
```

**Response:** 200 OK

---

#### DELETE `/api/v1/task-suggestions/{suggestion_id}`

**Purpose:** Soft delete a suggestion (preserves for later)

**Response:** 200 OK
```json
{
  "success": true,
  "message": "Suggestion deleted but preserved in history"
}
```

---

#### POST `/api/v1/task-suggestions/{suggestion_id}/restore`

**Purpose:** Restore a deleted suggestion (ADHD-friendly)

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "suggestion": {
      "id": "suggestion-uuid",
      "is_deleted": false,
      "user_action": "deleted_then_recreated"
    }
  },
  "message": "Suggestion restored"
}
```

---

### User Profile Endpoints

#### GET `/api/v1/profile`

**Purpose:** Get user profile

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "profile-uuid",
    "user_id": "user-uuid",
    "ongoing_projects": [
      {
        "name": "Personal AI Assistant",
        "status": "active",
        "description": "Building thought capture system"
      }
    ],
    "interests": ["automation", "AI", "infrastructure"],
    "work_style": "methodical, do it right",
    "common_themes": ["productivity", "automation"],
    "preferred_tone": "warm_encouraging"
  }
}
```

---

#### PUT `/api/v1/profile`

**Purpose:** Update user profile

**Request:**
```json
{
  "ongoing_projects": [
    {
      "name": "Personal AI Assistant",
      "status": "active"
    },
    {
      "name": "Home Automation",
      "status": "planning"
    }
  ],
  "interests": ["automation", "AI", "home-assistant"]
}
```

**Response:** 200 OK

---

## Admin Page UI

### Admin Page Structure (`/admin`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Admin Settings - Personal AI Assistant</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="admin-container">
        <!-- Navigation -->
        <nav class="admin-nav">
            <a href="/dashboard">← Back to Dashboard</a>
            <h1>⚙️ Admin Settings</h1>
        </nav>

        <!-- Settings Sections -->
        <div class="settings-grid">
            
            <!-- Consciousness Check Settings -->
            <section class="settings-card">
                <h2>🧠 Consciousness Check</h2>
                <form id="consciousness-settings">
                    <label>
                        <input type="checkbox" id="cc-enabled" checked>
                        Enable Automated Checks
                    </label>
                    
                    <label>
                        Interval (minutes)
                        <input type="number" id="cc-interval" value="30" min="1" max="1440">
                    </label>
                    
                    <label>
                        Analysis Depth
                        <select id="cc-depth-type">
                            <option value="smart" selected>Smart (7 days, min 10 thoughts)</option>
                            <option value="last_n_thoughts">Last N Thoughts</option>
                            <option value="last_n_days">Last N Days</option>
                            <option value="all_thoughts">All Thoughts</option>
                        </select>
                    </label>
                    
                    <label id="cc-depth-value-label">
                        Days / Thought Count
                        <input type="number" id="cc-depth-value" value="7" min="1">
                    </label>
                    
                    <label>
                        Minimum Thoughts (Smart Mode)
                        <input type="number" id="cc-min-thoughts" value="10" min="1">
                    </label>
                    
                    <button type="submit" class="btn-primary">Save Changes</button>
                </form>
            </section>

            <!-- Auto-Analysis Settings -->
            <section class="settings-card">
                <h2>🤖 Auto-Analysis</h2>
                <form id="auto-analysis-settings">
                    <label>
                        <input type="checkbox" id="auto-tag-enabled" checked>
                        Enable Auto-Tagging
                    </label>
                    
                    <label>
                        <input type="checkbox" id="auto-task-enabled" checked>
                        Enable Task Detection
                    </label>
                    
                    <label>
                        Task Suggestion Mode
                        <select id="task-suggestion-mode">
                            <option value="suggest" selected>Suggest (User Approval)</option>
                            <option value="auto_create">Auto-Create Tasks</option>
                            <option value="disabled">Disabled</option>
                        </select>
                    </label>
                    
                    <button type="submit" class="btn-primary">Save Changes</button>
                </form>
            </section>

            <!-- User Profile Settings -->
            <section class="settings-card">
                <h2>👤 User Profile</h2>
                <form id="profile-settings">
                    <label>
                        Ongoing Projects
                        <div id="projects-list">
                            <!-- Dynamic project entries -->
                        </div>
                        <button type="button" class="btn-secondary" id="add-project">+ Add Project</button>
                    </label>
                    
                    <label>
                        Interests (comma-separated)
                        <input type="text" id="interests" placeholder="automation, AI, infrastructure">
                    </label>
                    
                    <label>
                        Work Style
                        <textarea id="work-style" rows="3" placeholder="Describe your work approach..."></textarea>
                    </label>
                    
                    <label>
                        Preferred Tone
                        <select id="preferred-tone">
                            <option value="warm_encouraging" selected>Warm & Encouraging</option>
                            <option value="professional">Professional</option>
                            <option value="casual">Casual</option>
                        </select>
                    </label>
                    
                    <button type="submit" class="btn-primary">Save Profile</button>
                </form>
            </section>

            <!-- Backend Settings -->
            <section class="settings-card">
                <h2>🔧 Backend Configuration</h2>
                <form id="backend-settings">
                    <label>
                        Primary Backend
                        <select id="primary-backend">
                            <option value="" selected>Use Environment Default</option>
                            <option value="openai">OpenAI Compatible (fuego)</option>
                            <option value="claude">Claude API</option>
                        </select>
                    </label>
                    
                    <label>
                        Secondary Backend (Fallback)
                        <select id="secondary-backend">
                            <option value="" selected>Use Environment Default</option>
                            <option value="claude">Claude API</option>
                            <option value="openai">OpenAI Compatible</option>
                        </select>
                    </label>
                    
                    <button type="submit" class="btn-primary">Save Backend</button>
                </form>
            </section>

            <!-- Scheduled Analysis History -->
            <section class="settings-card full-width">
                <h2>📊 Consciousness Check History</h2>
                <div class="history-controls">
                    <button id="trigger-manual-check" class="btn-primary">▶️ Trigger Check Now</button>
                    <select id="history-filter">
                        <option value="all">All Checks</option>
                        <option value="completed">Completed</option>
                        <option value="skipped">Skipped</option>
                        <option value="failed">Failed</option>
                    </select>
                </div>
                
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>Scheduled</th>
                            <th>Executed</th>
                            <th>Status</th>
                            <th>Thoughts</th>
                            <th>Duration</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="history-tbody">
                        <!-- Dynamic rows -->
                    </tbody>
                </table>
            </section>

            <!-- System Info -->
            <section class="settings-card">
                <h2>ℹ️ System Info</h2>
                <dl class="system-info">
                    <dt>User Role:</dt>
                    <dd id="user-role">admin</dd>
                    
                    <dt>API Version:</dt>
                    <dd id="api-version">v1.0.0</dd>
                    
                    <dt>Database:</dt>
                    <dd id="db-status">Connected</dd>
                    
                    <dt>Scheduler:</dt>
                    <dd id="scheduler-status">Running</dd>
                    
                    <dt>Total Thoughts:</dt>
                    <dd id="total-thoughts">14</dd>
                    
                    <dt>Total Tasks:</dt>
                    <dd id="total-tasks">0</dd>
                </dl>
            </section>
        </div>
    </div>

    <script src="admin.js"></script>
</body>
</html>
```

### Admin JavaScript (`admin.js`)

```javascript
// admin.js - Admin page functionality

class AdminSettings {
    constructor() {
        this.apiBase = '/api/v1';
        this.init();
    }
    
    async init() {
        await this.loadCurrentSettings();
        this.bindEventListeners();
        await this.loadHistory();
    }
    
    async loadCurrentSettings() {
        // Load settings from API
        const settings = await this.fetchAPI('/settings');
        this.populateSettings(settings);
        
        // Load profile
        const profile = await this.fetchAPI('/profile');
        this.populateProfile(profile);
    }
    
    populateSettings(settings) {
        // Consciousness Check
        document.getElementById('cc-enabled').checked = settings.consciousness_check_enabled;
        document.getElementById('cc-interval').value = settings.consciousness_check_interval_minutes;
        document.getElementById('cc-depth-type').value = settings.consciousness_check_depth_type;
        document.getElementById('cc-depth-value').value = settings.consciousness_check_depth_value;
        document.getElementById('cc-min-thoughts').value = settings.consciousness_check_min_thoughts;
        
        // Auto-Analysis
        document.getElementById('auto-tag-enabled').checked = settings.auto_tagging_enabled;
        document.getElementById('auto-task-enabled').checked = settings.auto_task_creation_enabled;
        document.getElementById('task-suggestion-mode').value = settings.task_suggestion_mode;
        
        // Backend
        document.getElementById('primary-backend').value = settings.primary_backend || '';
        document.getElementById('secondary-backend').value = settings.secondary_backend || '';
    }
    
    populateProfile(profile) {
        // Projects
        this.renderProjects(profile.ongoing_projects);
        
        // Interests
        document.getElementById('interests').value = profile.interests.join(', ');
        
        // Work style
        document.getElementById('work-style').value = profile.work_style || '';
        
        // Tone
        document.getElementById('preferred-tone').value = profile.preferred_tone;
    }
    
    bindEventListeners() {
        // Form submissions
        document.getElementById('consciousness-settings').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveConsciousnessSettings();
        });
        
        document.getElementById('auto-analysis-settings').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveAutoAnalysisSettings();
        });
        
        document.getElementById('profile-settings').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProfileSettings();
        });
        
        document.getElementById('backend-settings').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveBackendSettings();
        });
        
        // Manual check trigger
        document.getElementById('trigger-manual-check').addEventListener('click', () => {
            this.triggerManualCheck();
        });
        
        // History filter
        document.getElementById('history-filter').addEventListener('change', () => {
            this.loadHistory();
        });
    }
    
    async saveConsciousnessSettings() {
        const data = {
            consciousness_check_enabled: document.getElementById('cc-enabled').checked,
            consciousness_check_interval_minutes: parseInt(document.getElementById('cc-interval').value),
            consciousness_check_depth_type: document.getElementById('cc-depth-type').value,
            consciousness_check_depth_value: parseInt(document.getElementById('cc-depth-value').value),
            consciousness_check_min_thoughts: parseInt(document.getElementById('cc-min-thoughts').value)
        };
        
        await this.updateSettings(data);
        this.showToast('Consciousness check settings saved!', 'success');
    }
    
    async saveAutoAnalysisSettings() {
        const data = {
            auto_tagging_enabled: document.getElementById('auto-tag-enabled').checked,
            auto_task_creation_enabled: document.getElementById('auto-task-enabled').checked,
            task_suggestion_mode: document.getElementById('task-suggestion-mode').value
        };
        
        await this.updateSettings(data);
        this.showToast('Auto-analysis settings saved!', 'success');
    }
    
    async triggerManualCheck() {
        const button = document.getElementById('trigger-manual-check');
        button.disabled = true;
        button.textContent = '⏳ Running...';
        
        try {
            await this.fetchAPI('/consciousness-check/trigger', {
                method: 'POST'
            });
            
            this.showToast('Consciousness check triggered!', 'success');
            
            // Reload history after a delay
            setTimeout(() => this.loadHistory(), 3000);
        } catch (error) {
            this.showToast('Failed to trigger check: ' + error.message, 'error');
        } finally {
            button.disabled = false;
            button.textContent = '▶️ Trigger Check Now';
        }
    }
    
    async loadHistory() {
        const filter = document.getElementById('history-filter').value;
        const params = filter !== 'all' ? `?status=${filter}` : '';
        
        const response = await this.fetchAPI(`/consciousness-check/history${params}`);
        this.renderHistory(response.analyses);
    }
    
    renderHistory(analyses) {
        const tbody = document.getElementById('history-tbody');
        tbody.innerHTML = '';
        
        analyses.forEach(analysis => {
            const row = document.createElement('tr');
            row.className = `status-${analysis.status}`;
            
            row.innerHTML = `
                <td>${this.formatDateTime(analysis.scheduled_at)}</td>
                <td>${analysis.executed_at ? this.formatDateTime(analysis.executed_at) : '-'}</td>
                <td><span class="status-badge ${analysis.status}">${analysis.status}</span></td>
                <td>${analysis.thoughts_analyzed_count || '-'}</td>
                <td>${analysis.analysis_duration_ms ? (analysis.analysis_duration_ms / 1000).toFixed(1) + 's' : '-'}</td>
                <td>
                    ${analysis.analysis_result_id ? 
                        `<button onclick="viewAnalysis('${analysis.analysis_result_id}')">View</button>` : 
                        '-'}
                </td>
            `;
            
            tbody.appendChild(row);
        });
    }
    
    // Helper methods
    async fetchAPI(endpoint, options = {}) {
        const response = await fetch(this.apiBase + endpoint, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('api_key')}`,
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error?.message || 'API request failed');
        }
        
        return data.data;
    }
    
    async updateSettings(updates) {
        return this.fetchAPI('/settings', {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }
    
    formatDateTime(isoString) {
        return new Date(isoString).toLocaleString();
    }
    
    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new AdminSettings();
});
```

---

## Implementation Checklist

### Database Layer
- [ ] Migrations for `thoughts` enhancements (thought_type, etc.)
- [ ] Migration for `task_suggestions` table
- [ ] Migration for `user_profiles` table
- [ ] SQLAlchemy ORM models for new tables
- [ ] Seed default profile for existing users

### Models Layer
- [ ] Pydantic models for thought analysis
- [ ] Pydantic models for task suggestions
- [ ] Pydantic models for user profiles
- [ ] Response/request model variants

### Services Layer
- [ ] ThoughtIntelligenceService (analysis on capture)
- [ ] EnhancedConsciousnessCheckService (personal prompts)
- [ ] UserProfileService (profile management)
- [ ] TaskSuggestionService (suggestions workflow)
- [ ] Update existing services to use new prompts

### Prompts Layer
- [ ] build_consciousness_check_prompt()
- [ ] build_thought_analysis_prompt()
- [ ] Format helpers (profile, projects, patterns)
- [ ] Response parsers (JSON extraction)

### API Layer
- [ ] Enhanced POST `/api/v1/thoughts` (with analysis)
- [ ] PUT `/api/v1/thoughts/{id}/apply-tags`
- [ ] GET `/api/v1/task-suggestions/pending`
- [ ] POST `/api/v1/task-suggestions/{id}/accept`
- [ ] POST `/api/v1/task-suggestions/{id}/reject`
- [ ] DELETE `/api/v1/task-suggestions/{id}` (soft delete)
- [ ] POST `/api/v1/task-suggestions/{id}/restore`
- [ ] GET `/api/v1/profile`
- [ ] PUT `/api/v1/profile`

### UI Layer
- [ ] Admin page HTML (`admin.html`)
- [ ] Admin page JavaScript (`admin.js`)
- [ ] Admin page CSS styling
- [ ] Task suggestion UI components
- [ ] Tag suggestion UI components
- [ ] Profile editing UI

---

## Testing Strategy

### Unit Tests
- Prompt building functions (correct formatting)
- Response parsing (handle various JSON formats)
- Tag suggestion logic (deduplication, confidence)
- Task suggestion confidence thresholds
- Soft delete/restore logic

### Integration Tests
- End-to-end thought capture with analysis
- Consciousness check with enhanced prompts
- Task suggestion acceptance flow
- Profile updates reflected in prompts
- Admin page settings persistence

### Edge Cases
- Thought too short for meaningful analysis
- Multiple conflicting tag suggestions
- User edits suggested tags
- Restore deleted suggestion after long time
- Analysis fails mid-flight

---

## Notes for Opus

When generating this code:

1. **Prompt Engineering is KEY**: The prompts are what make this personal. Don't skimp on context, warmth, and specificity.

2. **Preserve deleted suggestions**: TaskSuggestions use soft delete. ADHD users change their minds - this is a feature, not a bug.

3. **Auto-tagging is suggestive**: Tags are suggested with confidence scores. User always has final say.

4. **Task suggestions show reasoning**: Always explain WHY something was suggested. This builds trust.

5. **User profile is foundational**: Profile informs all analysis. Keep it updated from consciousness checks.

6. **JSON parsing must be robust**: AI responses aren't always perfect JSON. Handle gracefully.

7. **Admin page is functional, not pretty**: Focus on usability. Styling can be enhanced later.

8. **Confidence thresholds matter**: Don't spam user with low-confidence suggestions (< 0.7).

9. **Integration with existing services**: This builds on Phase 2A/3A. Reuse existing patterns.

10. **Testing is critical**: Enhanced prompts are complex. Comprehensive tests prevent regressions.

Generate production-ready code that makes analysis feel genuinely personal and helpful!

---

## Success Criteria

- [ ] Consciousness checks feel warm and personal
- [ ] Analysis references ongoing projects
- [ ] Auto-tagging suggests 2-3 relevant tags per thought
- [ ] Task detection creates suggestions with reasoning
- [ ] Suggested tasks can be accepted/rejected/modified
- [ ] Deleted suggestions can be restored
- [ ] User profile editable via admin page
- [ ] Admin page shows scheduler history
- [ ] All settings configurable and persistent
- [ ] Tests cover critical analysis paths

This transforms the system from "AI that processes thoughts" to "personal assistant that understands Andy." Build it with care! 🎯✨
