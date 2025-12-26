# Phase 3B Spec 1: Settings System & Automated Consciousness Checks

**Status:** Ready for Code Generation  
**Target:** Claude Opus (Complex multi-user architecture + scheduler integration)  
**Output:** Database schema, settings service, API endpoints, APScheduler integration  
**Complexity:** High  

---

## Overview

This specification defines a comprehensive settings system with role-based access control (RBAC) and automated consciousness checks. The system is architected for multi-user capability while currently supporting a single user, with configurable automated analysis that runs on a schedule.

**Purpose:** Create the foundation for user-configurable behavior, automated background tasks, and future multi-user expansion with proper access controls.

---

## Requirements Analysis

### What We're Solving
- Need configurable consciousness check intervals (default: 30 minutes)
- Need automated background processing that respects user preferences
- Need proper multi-user architecture even though MVP is single-user
- Need RBAC foundation for future admin-only features
- Need smart scheduling (only run if new thoughts exist)
- Need persistent storage of scheduled analysis results

### Edge Cases to Handle
- Settings updated while scheduler is running
- Multiple concurrent consciousness checks
- Scheduler survival across container restarts
- Default settings for new users
- Settings validation (intervals can't be negative, etc.)
- Timezone handling for scheduled tasks
- Partial failures in scheduled jobs

### Success Criteria
- Consciousness checks run automatically based on user settings
- Scheduler skips runs when no new thoughts exist
- Settings API supports full CRUD with validation
- RBAC architecture in place (even if not fully enforced yet)
- All scheduled runs tracked in database
- System recovers gracefully from failures

---

## Approach Options

### Option 1: APScheduler with SQLAlchemy Job Store (Recommended) ✅
**Pros:**
- In-process with FastAPI (no external dependencies)
- Persistent job store (survives restarts)
- Dynamic scheduling (update intervals on-the-fly)
- Built-in retry and error handling
- Can use PostgreSQL for job persistence

**Cons:**
- Adds dependency to project
- Slightly more complex than simple cron

### Option 2: System Cron
**Pros:**
- Simple, battle-tested
- No code dependencies

**Cons:**
- Requires external configuration
- Hard to update dynamically from settings
- Requires SSH access to modify
- Not ideal for containerized environments

### Option 3: Celery Beat
**Pros:**
- Powerful, distributed task queue
- Great for complex scheduling

**Cons:**
- Massive overkill for this use case
- Requires Redis/RabbitMQ
- Much more infrastructure to manage

**Decision:** Option 1 (APScheduler). Right balance of power, simplicity, and integration with existing stack.

---

## Architecture Design

### Multi-User with RBAC Foundation

**User Roles:**
```python
class UserRole(str, Enum):
    ADMIN = "admin"      # Full system access, can modify any settings
    USER = "user"        # Standard user, can modify own settings
    READONLY = "readonly"  # View-only access (future)
```

**Permission Model:**
```python
class Permission(str, Enum):
    # Settings permissions
    SETTINGS_READ_OWN = "settings:read:own"
    SETTINGS_WRITE_OWN = "settings:write:own"
    SETTINGS_READ_ALL = "settings:read:all"     # Admin only
    SETTINGS_WRITE_ALL = "settings:write:all"   # Admin only
    
    # Consciousness check permissions
    CONSCIOUSNESS_CHECK_TRIGGER = "consciousness:trigger"
    CONSCIOUSNESS_CHECK_VIEW_HISTORY = "consciousness:view:history"
    
    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    SCHEDULER_CONTROL = "scheduler:control"
```

**Role-Permission Mapping:**
```python
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.SETTINGS_READ_OWN,
        Permission.SETTINGS_WRITE_OWN,
        Permission.SETTINGS_READ_ALL,
        Permission.SETTINGS_WRITE_ALL,
        Permission.CONSCIOUSNESS_CHECK_TRIGGER,
        Permission.CONSCIOUSNESS_CHECK_VIEW_HISTORY,
        Permission.ADMIN_ACCESS,
        Permission.SCHEDULER_CONTROL,
    ],
    UserRole.USER: [
        Permission.SETTINGS_READ_OWN,
        Permission.SETTINGS_WRITE_OWN,
        Permission.CONSCIOUSNESS_CHECK_TRIGGER,
        Permission.CONSCIOUSNESS_CHECK_VIEW_HISTORY,
    ],
    UserRole.READONLY: [
        Permission.SETTINGS_READ_OWN,
        Permission.CONSCIOUSNESS_CHECK_VIEW_HISTORY,
    ],
}
```

---

## Database Schema

### 1. Update `users` Table

```sql
-- Add role column to existing users table
ALTER TABLE users 
ADD COLUMN role VARCHAR(20) DEFAULT 'user',
ADD COLUMN is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN last_login_at TIMESTAMP,
ADD CONSTRAINT check_role CHECK (role IN ('admin', 'user', 'readonly'));

-- Set existing user as admin
UPDATE users SET role = 'admin' WHERE email = 'andy@fennerfam.com';

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
```

---

### 2. Create `user_settings` Table

```sql
CREATE TABLE user_settings (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    
    -- Consciousness Check Settings
    consciousness_check_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    consciousness_check_interval_minutes INTEGER DEFAULT 30 NOT NULL,
    consciousness_check_depth_type VARCHAR(20) DEFAULT 'smart' NOT NULL,
    consciousness_check_depth_value INTEGER DEFAULT 7 NOT NULL,
    consciousness_check_min_thoughts INTEGER DEFAULT 10 NOT NULL,
    
    -- Auto-Analysis Settings
    auto_tagging_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    auto_task_creation_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    task_suggestion_mode VARCHAR(20) DEFAULT 'suggest' NOT NULL,
    
    -- Backend Override Settings (optional, overrides env vars)
    primary_backend VARCHAR(50),
    secondary_backend VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT check_interval_positive CHECK (consciousness_check_interval_minutes > 0),
    CONSTRAINT check_depth_type CHECK (consciousness_check_depth_type IN ('smart', 'last_n_thoughts', 'last_n_days', 'all_thoughts')),
    CONSTRAINT check_depth_value_positive CHECK (consciousness_check_depth_value > 0),
    CONSTRAINT check_min_thoughts_positive CHECK (consciousness_check_min_thoughts > 0),
    CONSTRAINT check_task_suggestion_mode CHECK (task_suggestion_mode IN ('suggest', 'auto_create', 'disabled'))
);

CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);

-- Comments for clarity
COMMENT ON COLUMN user_settings.consciousness_check_depth_type IS 
    'smart: max(last 7 days, min 10 thoughts); last_n_thoughts: specific count; last_n_days: specific days; all_thoughts: everything';
COMMENT ON COLUMN user_settings.task_suggestion_mode IS 
    'suggest: show UI prompt; auto_create: create immediately; disabled: no task detection';
```

**Field Details:**

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `consciousness_check_enabled` | Boolean | TRUE | Master on/off switch |
| `consciousness_check_interval_minutes` | Integer | 30 | How often to run (minutes) |
| `consciousness_check_depth_type` | Enum | 'smart' | Analysis strategy |
| `consciousness_check_depth_value` | Integer | 7 | Value for depth (days or count) |
| `consciousness_check_min_thoughts` | Integer | 10 | Minimum thoughts for 'smart' mode |
| `auto_tagging_enabled` | Boolean | TRUE | Auto-suggest tags |
| `auto_task_creation_enabled` | Boolean | TRUE | Detect tasks from thoughts |
| `task_suggestion_mode` | Enum | 'suggest' | How to handle detected tasks |

**Depth Type Behavior:**
- `smart`: Analyze max(last 7 days, min 10 thoughts) - user's preferred default
- `last_n_thoughts`: Analyze exactly N most recent thoughts
- `last_n_days`: Analyze all thoughts from last N days
- `all_thoughts`: Analyze entire thought history

---

### 3. Create `scheduled_analyses` Table

```sql
CREATE TABLE scheduled_analyses (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    
    -- Scheduling metadata
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    
    -- Execution details
    skip_reason VARCHAR(100),
    thoughts_since_last_check INTEGER,
    thoughts_analyzed_count INTEGER,
    analysis_duration_ms INTEGER,
    
    -- Results
    analysis_result_id VARCHAR(36),
    error_message TEXT,
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_result_id) REFERENCES claude_analysis_results(id) ON DELETE SET NULL,
    CONSTRAINT check_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped'))
);

CREATE INDEX idx_scheduled_analyses_user_status ON scheduled_analyses(user_id, status);
CREATE INDEX idx_scheduled_analyses_scheduled_at ON scheduled_analyses(scheduled_at DESC);
CREATE INDEX idx_scheduled_analyses_user_completed ON scheduled_analyses(user_id, completed_at DESC);

-- Comments
COMMENT ON COLUMN scheduled_analyses.skip_reason IS 
    'Reason for skipping: no_new_thoughts, disabled_by_user, system_error';
```

**Status Values:**
- `pending`: Scheduled but not yet started
- `running`: Currently executing
- `completed`: Finished successfully
- `failed`: Encountered error
- `skipped`: Deliberately skipped (no new thoughts, disabled, etc.)

**Example Row:**
```json
{
  "id": "abc-123",
  "user_id": "andy-uuid",
  "scheduled_at": "2025-12-26 14:00:00",
  "executed_at": "2025-12-26 14:00:01",
  "completed_at": "2025-12-26 14:00:15",
  "status": "completed",
  "thoughts_since_last_check": 3,
  "thoughts_analyzed_count": 17,
  "analysis_duration_ms": 14250,
  "analysis_result_id": "result-xyz",
  "skip_reason": null,
  "error_message": null
}
```

---

## Data Models (Pydantic)

### SettingsDepthType Enum
```python
class SettingsDepthType(str, Enum):
    SMART = "smart"                    # max(last N days, min M thoughts)
    LAST_N_THOUGHTS = "last_n_thoughts"  # Exact count
    LAST_N_DAYS = "last_n_days"        # Date range
    ALL_THOUGHTS = "all_thoughts"      # Everything
```

### TaskSuggestionMode Enum
```python
class TaskSuggestionMode(str, Enum):
    SUGGEST = "suggest"        # Show UI prompt for approval
    AUTO_CREATE = "auto_create"  # Create immediately
    DISABLED = "disabled"      # No task detection
```

### UserSettings (Response Model)
```python
class UserSettings(BaseModel):
    id: UUID
    user_id: UUID
    
    # Consciousness Check
    consciousness_check_enabled: bool = True
    consciousness_check_interval_minutes: int = Field(30, ge=1, le=1440)
    consciousness_check_depth_type: SettingsDepthType = SettingsDepthType.SMART
    consciousness_check_depth_value: int = Field(7, ge=1)
    consciousness_check_min_thoughts: int = Field(10, ge=1)
    
    # Auto-Analysis
    auto_tagging_enabled: bool = True
    auto_task_creation_enabled: bool = True
    task_suggestion_mode: TaskSuggestionMode = TaskSuggestionMode.SUGGEST
    
    # Backend Overrides
    primary_backend: Optional[str] = None
    secondary_backend: Optional[str] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "consciousness_check_enabled": True,
                "consciousness_check_interval_minutes": 30,
                "consciousness_check_depth_type": "smart",
                "consciousness_check_depth_value": 7,
                "consciousness_check_min_thoughts": 10,
                "auto_tagging_enabled": True,
                "auto_task_creation_enabled": True,
                "task_suggestion_mode": "suggest"
            }
        }
```

### UserSettingsUpdate (Request Model)
```python
class UserSettingsUpdate(BaseModel):
    consciousness_check_enabled: Optional[bool] = None
    consciousness_check_interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    consciousness_check_depth_type: Optional[SettingsDepthType] = None
    consciousness_check_depth_value: Optional[int] = Field(None, ge=1)
    consciousness_check_min_thoughts: Optional[int] = Field(None, ge=1)
    
    auto_tagging_enabled: Optional[bool] = None
    auto_task_creation_enabled: Optional[bool] = None
    task_suggestion_mode: Optional[TaskSuggestionMode] = None
    
    primary_backend: Optional[str] = None
    secondary_backend: Optional[str] = None
    
    @validator('consciousness_check_interval_minutes')
    def validate_interval(cls, v):
        if v is not None and (v < 1 or v > 1440):
            raise ValueError('Interval must be between 1 and 1440 minutes (24 hours)')
        return v
```

### ScheduledAnalysis (Response Model)
```python
class ScheduledAnalysis(BaseModel):
    id: UUID
    user_id: UUID
    scheduled_at: datetime
    executed_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str  # pending, running, completed, failed, skipped
    skip_reason: Optional[str]
    thoughts_since_last_check: Optional[int]
    thoughts_analyzed_count: Optional[int]
    analysis_duration_ms: Optional[int]
    analysis_result_id: Optional[UUID]
    error_message: Optional[str]
    created_at: datetime
```

---

## Services Layer

### SettingsService

```python
class SettingsService:
    """
    Business logic for user settings management.
    
    Handles CRUD operations, validation, and default initialization.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_settings(self, user_id: UUID) -> UserSettings:
        """
        Get settings for a user. Creates default settings if none exist.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            UserSettings object
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        pass
    
    async def update_user_settings(
        self, 
        user_id: UUID, 
        updates: UserSettingsUpdate
    ) -> UserSettings:
        """
        Update user settings. Validates changes and triggers
        scheduler updates if interval changed.
        
        Args:
            user_id: UUID of the user
            updates: Partial settings updates
            
        Returns:
            Updated UserSettings object
            
        Raises:
            UserNotFoundError: If user doesn't exist
            ValidationError: If updates invalid
        """
        pass
    
    async def reset_to_defaults(self, user_id: UUID) -> UserSettings:
        """
        Reset settings to system defaults.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Reset UserSettings object
        """
        pass
    
    async def get_analysis_depth_config(
        self, 
        user_id: UUID
    ) -> AnalysisDepthConfig:
        """
        Calculate actual analysis parameters based on depth settings.
        
        For 'smart' mode: returns max(last N days, min M thoughts)
        
        Args:
            user_id: UUID of the user
            
        Returns:
            AnalysisDepthConfig with actual query parameters
        """
        pass
    
    async def initialize_default_settings(self, user_id: UUID) -> UserSettings:
        """
        Create default settings for a new user.
        Called during user creation.
        
        Args:
            user_id: UUID of the new user
            
        Returns:
            Newly created UserSettings
        """
        pass
```

### ScheduledAnalysisService

```python
class ScheduledAnalysisService:
    """
    Tracks and manages scheduled consciousness checks.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_scheduled_run(
        self, 
        user_id: UUID,
        scheduled_at: datetime
    ) -> ScheduledAnalysis:
        """Create a pending scheduled analysis entry."""
        pass
    
    async def mark_running(self, analysis_id: UUID) -> ScheduledAnalysis:
        """Mark analysis as currently running."""
        pass
    
    async def mark_completed(
        self, 
        analysis_id: UUID,
        thoughts_analyzed: int,
        duration_ms: int,
        result_id: UUID
    ) -> ScheduledAnalysis:
        """Mark analysis as completed with results."""
        pass
    
    async def mark_skipped(
        self, 
        analysis_id: UUID,
        reason: str,
        thoughts_since_last: int
    ) -> ScheduledAnalysis:
        """Mark analysis as skipped with reason."""
        pass
    
    async def mark_failed(
        self, 
        analysis_id: UUID,
        error_message: str
    ) -> ScheduledAnalysis:
        """Mark analysis as failed with error."""
        pass
    
    async def get_last_completed_check(
        self, 
        user_id: UUID
    ) -> Optional[ScheduledAnalysis]:
        """Get the most recent completed consciousness check."""
        pass
    
    async def get_analysis_history(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ScheduledAnalysis]:
        """Get paginated history of scheduled analyses."""
        pass
    
    async def count_thoughts_since_last_check(
        self, 
        user_id: UUID
    ) -> int:
        """
        Count new thoughts since the last completed consciousness check.
        Returns 0 if no previous check exists (first run).
        """
        pass
```

---

## APScheduler Integration

### SchedulerService

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

class SchedulerService:
    """
    Manages APScheduler lifecycle and job scheduling.
    """
    
    def __init__(
        self, 
        db_url: str,
        consciousness_check_service: ConsciousnessCheckService,
        settings_service: SettingsService,
        scheduled_analysis_service: ScheduledAnalysisService
    ):
        self.db_url = db_url
        self.consciousness_check_service = consciousness_check_service
        self.settings_service = settings_service
        self.scheduled_analysis_service = scheduled_analysis_service
        
        # Configure scheduler
        jobstores = {
            'default': SQLAlchemyJobStore(url=db_url)
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': True,  # Combine missed runs
            'max_instances': 1,  # Prevent concurrent runs
            'misfire_grace_time': 300  # 5 minutes grace for missed runs
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
    
    def start(self):
        """Start the scheduler on application startup."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler started")
    
    def shutdown(self):
        """Gracefully shutdown scheduler on application shutdown."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("APScheduler shut down")
    
    async def schedule_user_consciousness_checks(self, user_id: UUID):
        """
        Schedule consciousness checks for a user based on their settings.
        Updates existing job if already scheduled.
        
        Args:
            user_id: UUID of the user
        """
        settings = await self.settings_service.get_user_settings(user_id)
        
        job_id = f"consciousness_check_{user_id}"
        
        if not settings.consciousness_check_enabled:
            # Remove job if disabled
            self.scheduler.remove_job(job_id, jobstore='default')
            logger.info(f"Removed consciousness check job for user {user_id}")
            return
        
        # Schedule or update job
        self.scheduler.add_job(
            self._run_consciousness_check,
            trigger='interval',
            minutes=settings.consciousness_check_interval_minutes,
            id=job_id,
            args=[user_id],
            replace_existing=True,
            jobstore='default'
        )
        
        logger.info(
            f"Scheduled consciousness check for user {user_id} "
            f"every {settings.consciousness_check_interval_minutes} minutes"
        )
    
    async def _run_consciousness_check(self, user_id: UUID):
        """
        Execute a scheduled consciousness check.
        
        This is the job that APScheduler runs on schedule.
        """
        scheduled_analysis = None
        start_time = datetime.utcnow()
        
        try:
            # Create scheduled analysis record
            scheduled_analysis = await self.scheduled_analysis_service.create_scheduled_run(
                user_id=user_id,
                scheduled_at=start_time
            )
            
            # Mark as running
            await self.scheduled_analysis_service.mark_running(scheduled_analysis.id)
            
            # Check if there are new thoughts since last check
            new_thought_count = await self.scheduled_analysis_service.count_thoughts_since_last_check(user_id)
            
            if new_thought_count == 0:
                # Skip - no new thoughts
                await self.scheduled_analysis_service.mark_skipped(
                    analysis_id=scheduled_analysis.id,
                    reason="no_new_thoughts",
                    thoughts_since_last=0
                )
                logger.info(f"Skipped consciousness check for user {user_id} - no new thoughts")
                return
            
            # Get settings to determine analysis depth
            depth_config = await self.settings_service.get_analysis_depth_config(user_id)
            
            # Run the actual consciousness check
            result = await self.consciousness_check_service.run_consciousness_check(
                user_id=user_id,
                depth_config=depth_config,
                triggered_by="scheduler"
            )
            
            # Calculate duration
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Mark as completed
            await self.scheduled_analysis_service.mark_completed(
                analysis_id=scheduled_analysis.id,
                thoughts_analyzed=result.thoughts_analyzed_count,
                duration_ms=duration_ms,
                result_id=result.id
            )
            
            logger.info(
                f"Completed consciousness check for user {user_id}: "
                f"{result.thoughts_analyzed_count} thoughts in {duration_ms}ms"
            )
            
        except Exception as e:
            logger.error(f"Failed consciousness check for user {user_id}: {str(e)}", exc_info=True)
            
            if scheduled_analysis:
                await self.scheduled_analysis_service.mark_failed(
                    analysis_id=scheduled_analysis.id,
                    error_message=str(e)
                )
```

---

## API Endpoints

### Settings Endpoints

#### GET `/api/v1/settings`

**Purpose:** Retrieve current user settings

**Request:**
```
Headers:
  Authorization: Bearer {API_KEY}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "settings-uuid",
    "user_id": "andy-uuid",
    "consciousness_check_enabled": true,
    "consciousness_check_interval_minutes": 30,
    "consciousness_check_depth_type": "smart",
    "consciousness_check_depth_value": 7,
    "consciousness_check_min_thoughts": 10,
    "auto_tagging_enabled": true,
    "auto_task_creation_enabled": true,
    "task_suggestion_mode": "suggest",
    "primary_backend": null,
    "secondary_backend": null,
    "created_at": "2025-12-26T10:00:00Z",
    "updated_at": "2025-12-26T10:00:00Z"
  }
}
```

---

#### PUT `/api/v1/settings`

**Purpose:** Update user settings (partial updates supported)

**Request:**
```json
{
  "consciousness_check_enabled": true,
  "consciousness_check_interval_minutes": 45,
  "task_suggestion_mode": "auto_create"
}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "settings-uuid",
    "consciousness_check_interval_minutes": 45,
    "task_suggestion_mode": "auto_create",
    "updated_at": "2025-12-26T14:30:00Z"
  },
  "message": "Settings updated. Scheduler updated to run every 45 minutes."
}
```

**Side Effects:**
- If `consciousness_check_interval_minutes` changed: Updates APScheduler job
- If `consciousness_check_enabled` changed to false: Removes APScheduler job

**Error Cases:**
- 400 Bad Request: Invalid values (interval > 1440, negative values)
- 401 Unauthorized: Missing/invalid API key
- 403 Forbidden: User lacks permission (future RBAC)

---

#### POST `/api/v1/settings/reset`

**Purpose:** Reset settings to system defaults

**Request:**
```
Headers:
  Authorization: Bearer {API_KEY}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "consciousness_check_enabled": true,
    "consciousness_check_interval_minutes": 30,
    "consciousness_check_depth_type": "smart",
    "updated_at": "2025-12-26T15:00:00Z"
  },
  "message": "Settings reset to defaults"
}
```

---

### Scheduled Analysis Endpoints

#### GET `/api/v1/consciousness-check/history`

**Purpose:** Get paginated history of scheduled consciousness checks

**Query Parameters:**
```
?limit=50     # Max results (default 50, max 100)
?offset=0     # Pagination offset
?status=completed  # Optional filter by status
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "analyses": [
      {
        "id": "analysis-uuid",
        "scheduled_at": "2025-12-26T14:00:00Z",
        "executed_at": "2025-12-26T14:00:01Z",
        "completed_at": "2025-12-26T14:00:15Z",
        "status": "completed",
        "thoughts_since_last_check": 3,
        "thoughts_analyzed_count": 17,
        "analysis_duration_ms": 14250,
        "analysis_result_id": "result-xyz"
      },
      {
        "id": "analysis-uuid-2",
        "scheduled_at": "2025-12-26T13:30:00Z",
        "executed_at": "2025-12-26T13:30:01Z",
        "status": "skipped",
        "skip_reason": "no_new_thoughts",
        "thoughts_since_last_check": 0
      }
    ],
    "pagination": {
      "total": 237,
      "limit": 50,
      "offset": 0,
      "has_more": true
    }
  }
}
```

---

#### GET `/api/v1/consciousness-check/latest`

**Purpose:** Get the most recent completed consciousness check result

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "scheduled_analysis": {
      "id": "analysis-uuid",
      "executed_at": "2025-12-26T14:00:01Z",
      "completed_at": "2025-12-26T14:00:15Z",
      "thoughts_analyzed_count": 17
    },
    "analysis_result": {
      "id": "result-xyz",
      "summary": "You've been focused on infrastructure work...",
      "themes": ["infrastructure", "automation"],
      "suggested_actions": [...]
    }
  }
}
```

**Use Case:** Web UI calls this on page load to display most recent check

---

#### POST `/api/v1/consciousness-check/trigger`

**Purpose:** Manually trigger a consciousness check (bypasses schedule)

**Request:**
```json
{
  "depth_override": {
    "type": "last_n_thoughts",
    "value": 20
  }
}
```
(depth_override is optional - uses settings if not provided)

**Response:** 202 Accepted (runs async)
```json
{
  "success": true,
  "data": {
    "scheduled_analysis_id": "manual-trigger-uuid",
    "message": "Consciousness check started. Check /api/v1/consciousness-check/history for results."
  }
}
```

---

## Application Lifecycle Integration

### FastAPI Startup Event

```python
# src/api/main.py

from contextlib import asynccontextmanager
from src.services.scheduler_service import SchedulerService

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - startup and shutdown.
    """
    # Startup
    logger.info("🚀 Starting Personal AI Assistant API")
    
    # Initialize scheduler
    scheduler_service = get_scheduler_service()
    scheduler_service.start()
    
    # Schedule consciousness checks for all active users
    settings_service = get_settings_service()
    users = await get_all_active_users()
    
    for user in users:
        await scheduler_service.schedule_user_consciousness_checks(user.id)
        logger.info(f"Scheduled consciousness checks for user: {user.email}")
    
    logger.info("✅ Scheduler initialized and jobs scheduled")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Personal AI Assistant API")
    scheduler_service.shutdown()
    logger.info("✅ Scheduler shut down gracefully")

app = FastAPI(lifespan=lifespan)
```

---

## Implementation Checklist

### Database Layer
- [ ] Alembic migration to add `role` column to `users` table
- [ ] Alembic migration to create `user_settings` table
- [ ] Alembic migration to create `scheduled_analyses` table
- [ ] SQLAlchemy ORM models for new tables
- [ ] Database seed: Set Andy as admin role
- [ ] Database seed: Create default settings for existing users

### Models Layer
- [ ] Pydantic request/response models for settings
- [ ] Pydantic models for scheduled analyses
- [ ] Enums for roles, permissions, depth types, task modes

### Services Layer
- [ ] SettingsService with full CRUD
- [ ] ScheduledAnalysisService for tracking runs
- [ ] SchedulerService with APScheduler integration
- [ ] Update ConsciousnessCheckService to accept depth config

### API Layer
- [ ] GET `/api/v1/settings`
- [ ] PUT `/api/v1/settings`
- [ ] POST `/api/v1/settings/reset`
- [ ] GET `/api/v1/consciousness-check/history`
- [ ] GET `/api/v1/consciousness-check/latest`
- [ ] POST `/api/v1/consciousness-check/trigger`

### Integration
- [ ] Update FastAPI lifespan to start/stop scheduler
- [ ] Settings updates trigger scheduler job updates
- [ ] Scheduler job runs consciousness check with proper depth
- [ ] Scheduler job creates/updates scheduled_analyses records

### Dependencies
- [ ] Add `apscheduler` to requirements.txt

---

## Testing Strategy

### Unit Tests
- Settings validation (intervals, depth types)
- Depth config calculation for 'smart' mode
- Scheduled analysis status transitions
- Permission checking (even if not enforced yet)

### Integration Tests
- Settings CRUD via API
- Scheduler job creation/update/removal
- Consciousness check skip logic (no new thoughts)
- Scheduled analysis history retrieval

### Edge Cases
- Settings update while job is running
- Multiple rapid settings updates
- Scheduler restart recovery
- Failed consciousness check handling

---

## Notes for Opus

When generating this code:

1. **Multi-user architecture**: Build this properly even though it's single-user now. Don't take shortcuts.

2. **RBAC foundation**: Implement the permission system fully. We'll use it soon.

3. **APScheduler persistence**: Use SQLAlchemy job store so jobs survive container restarts.

4. **Error handling**: Scheduled jobs must handle failures gracefully and log clearly.

5. **Timezone awareness**: All datetimes in UTC. User timezone handling is future work.

6. **Settings validation**: Strict validation on intervals, depth values. No negative numbers, no absurd intervals.

7. **Scheduler lifecycle**: Must start on app startup, shutdown gracefully on app shutdown.

8. **Smart depth mode**: Default is `max(last 7 days, min 10 thoughts)`. Implement this calculation.

9. **Skip logic**: If `count_thoughts_since_last_check()` returns 0, skip and mark as skipped with reason.

10. **Migration safety**: Migrations should be idempotent and handle existing data gracefully.

Generate production-ready code that follows all standards from STANDARDS_INTEGRATION.md.

---

## Success Criteria

- [ ] Settings API fully functional with validation
- [ ] APScheduler starts on app startup
- [ ] Consciousness checks run every 30 minutes (or configured interval)
- [ ] Checks skip when no new thoughts exist
- [ ] All scheduled runs tracked in database
- [ ] Settings updates dynamically update scheduler jobs
- [ ] Multi-user architecture in place (even for single user)
- [ ] RBAC permissions defined (even if not enforced yet)
- [ ] Tests cover critical paths
- [ ] Documentation complete

This is the foundation for a truly intelligent, configurable system. Build it right! 🎯
