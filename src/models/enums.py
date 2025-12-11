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
