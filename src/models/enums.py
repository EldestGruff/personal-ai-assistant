"""
Enumeration types for the Personal AI Assistant.

Defines all constrained string values used throughout the application
for status tracking, priorities, and contextual information.
"""

from enum import Enum


class ThoughtStatus(str, Enum):
    """
    Lifecycle status of a thought.
    
    - ACTIVE: Thought is current and relevant
    - ARCHIVED: Thought has been stored for reference but not active
    - COMPLETED: Thought has been acted upon and is complete
    """
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class TaskStatus(str, Enum):
    """
    Lifecycle status of a task.
    
    - PENDING: Task created but not started
    - IN_PROGRESS: Currently working on task
    - DONE: Task completed successfully
    - CANCELLED: Task no longer relevant or needed
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"



class Priority(str, Enum):
    """
    Task priority levels.
    
    - LOW: Nice to have, no urgency
    - MEDIUM: Should be done soon
    - HIGH: Important, needs attention
    - CRITICAL: Urgent, top priority
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TimeOfDay(str, Enum):
    """
    General time of day categories for context tracking.
    
    Helps identify when thoughts typically occur.
    """
    MORNING = "morning"      # ~6am-12pm
    AFTERNOON = "afternoon"  # ~12pm-6pm
    EVENING = "evening"      # ~6pm-10pm
    NIGHT = "night"          # ~10pm-6am


class EnergyLevel(str, Enum):
    """
    User's self-reported energy level at time of thought capture.
    
    Helps Claude identify patterns between energy and thought quality.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"



class FocusState(str, Enum):
    """
    User's mental focus state at time of thought capture.
    
    Helps identify patterns between focus quality and thought capture.
    - DEEP_WORK: Fully focused, in flow state
    - INTERRUPTED: Broken focus, context switching
    - SCATTERED: Unfocused, distracted
    """
    DEEP_WORK = "deep_work"
    INTERRUPTED = "interrupted"
    SCATTERED = "scattered"


class AnalysisType(str, Enum):
    """
    Type of analysis Claude performed.
    
    Used to categorize different Claude API interactions for audit trail.
    - CONSCIOUSNESS_CHECK: Periodic review of recent thoughts
    - SIMILARITY_CHECK: Finding related thoughts
    - THEME_EXTRACTION: Identifying patterns across thoughts
    - TASK_SUGGESTION: Recommending actionable tasks
    """
    CONSCIOUSNESS_CHECK = "consciousness_check"
    SIMILARITY_CHECK = "similarity_check"
    THEME_EXTRACTION = "theme_extraction"
    TASK_SUGGESTION = "task_suggestion"


# =============================================================================
# RBAC (Role-Based Access Control) Enums - Phase 3B
# =============================================================================

class UserRole(str, Enum):
    """
    User role for RBAC (Role-Based Access Control).
    
    Multi-user architecture foundation, even though MVP is single-user.
    - ADMIN: Full system access, can modify any settings
    - USER: Standard user, can modify own settings
    - READONLY: View-only access (future)
    """
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class Permission(str, Enum):
    """
    Fine-grained permissions for RBAC.
    
    Each permission controls access to a specific action or resource.
    Permissions are assigned to roles via ROLE_PERMISSIONS mapping.
    """
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


# Role to Permission mapping
ROLE_PERMISSIONS: dict[UserRole, list[Permission]] = {
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


# =============================================================================
# Settings Enums - Phase 3B
# =============================================================================

class SettingsDepthType(str, Enum):
    """
    Analysis depth strategy for consciousness checks.
    
    Controls how many thoughts are analyzed during a check.
    - SMART: max(last N days, min M thoughts) - user's preferred default
    - LAST_N_THOUGHTS: Analyze exactly N most recent thoughts
    - LAST_N_DAYS: Analyze all thoughts from last N days
    - ALL_THOUGHTS: Analyze entire thought history (expensive)
    """
    SMART = "smart"
    LAST_N_THOUGHTS = "last_n_thoughts"
    LAST_N_DAYS = "last_n_days"
    ALL_THOUGHTS = "all_thoughts"


class TaskSuggestionMode(str, Enum):
    """
    How to handle detected tasks from thought analysis.
    
    ADHD-friendly design: default is SUGGEST (user decides).
    - SUGGEST: Show UI prompt for approval before creating task
    - AUTO_CREATE: Create task immediately without confirmation
    - DISABLED: No task detection or creation
    """
    SUGGEST = "suggest"
    AUTO_CREATE = "auto_create"
    DISABLED = "disabled"


class ScheduledAnalysisStatus(str, Enum):
    """
    Status of a scheduled consciousness check run.
    
    Tracks the lifecycle of each scheduled analysis.
    - PENDING: Scheduled but not yet started
    - RUNNING: Currently executing
    - COMPLETED: Finished successfully
    - FAILED: Encountered error
    - SKIPPED: Deliberately skipped (no new thoughts, disabled, etc.)
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
