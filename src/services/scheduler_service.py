"""
Background scheduler for periodic tasks.

Provides APScheduler integration with persistent job store for
scheduled consciousness checks and other periodic operations.
Handles dynamic scheduling based on user settings.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from ..database.session import get_db, DATABASE_URL
from ..models.base import utc_now
from ..models.enums import AnalysisType, ThoughtStatus

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Background scheduler for periodic tasks with persistent job store.
    
    Uses APScheduler with SQLAlchemy job store for job persistence
    across container restarts. Integrates with SettingsService for
    dynamic scheduling based on user preferences.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize scheduler service.
        
        Args:
            db_url: Database URL for job store (uses DATABASE_URL if not provided)
        """
        self.db_url = db_url or DATABASE_URL
        
        # Configure job stores for persistence
        jobstores = {
            'default': SQLAlchemyJobStore(url=self.db_url)
        }
        
        # Job defaults
        job_defaults = {
            'coalesce': True,  # Combine missed runs into one
            'max_instances': 1,  # Prevent concurrent runs of same job
            'misfire_grace_time': 300  # 5 minutes grace for missed runs
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Add event listeners for logging
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )
        
        self._started = False
        logger.info("📅 Scheduler service initialized")

    def start(self):
        """Start the scheduler on application startup."""
        if not self._started and not self.scheduler.running:
            self.scheduler.start()
            self._started = True
            logger.info("📅 Scheduler service started")

    def shutdown(self, wait: bool = True):
        """
        Gracefully shutdown scheduler on application shutdown.
        
        Args:
            wait: Wait for running jobs to complete (default True)
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            self._started = False
            logger.info("📅 Scheduler service stopped")

    def schedule_user_consciousness_checks(
        self, 
        user_id: str,
        interval_minutes: Optional[int] = None,
        enabled: bool = True
    ):
        """
        Schedule consciousness checks for a user based on their settings.
        Updates existing job if already scheduled.
        
        Args:
            user_id: UUID of the user (as string)
            interval_minutes: Override interval (uses settings if None)
            enabled: Whether to enable or disable the job
        """
        job_id = f"consciousness_check_{user_id}"
        
        if not enabled:
            # Remove job if disabled
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"❌ Removed consciousness check job for user {user_id}")
            except Exception:
                pass  # Job may not exist
            return
        
        # Get interval from settings if not provided
        if interval_minutes is None:
            interval_minutes = self._get_user_interval(user_id)
        
        # Schedule or update job
        self.scheduler.add_job(
            func=run_consciousness_check_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            args=[user_id],
            replace_existing=True,
            name=f'Consciousness Check - User {user_id[:8]}'
        )
        
        logger.info(
            f"⏰ Scheduled consciousness check for user {user_id[:8]}... "
            f"every {interval_minutes} minutes"
        )

    def remove_job(self, job_id: str):
        """
        Remove a scheduled job.
        
        Args:
            job_id: ID of the job to remove
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.warning(f"Could not remove job {job_id}: {e}")

    def get_job(self, job_id: str):
        """
        Get a scheduled job by ID.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Job object or None
        """
        return self.scheduler.get_job(job_id)

    def get_all_jobs(self):
        """Get all scheduled jobs."""
        return self.scheduler.get_jobs()

    def _get_user_interval(self, user_id: str) -> int:
        """
        Get consciousness check interval from user settings.
        
        Args:
            user_id: UUID of the user (as string)
            
        Returns:
            Interval in minutes (default 30)
        """
        try:
            db = next(get_db())
            try:
                from .settings_service import SettingsService
                settings_service = SettingsService(db)
                settings = settings_service.get_user_settings(user_id)
                return settings.consciousness_check_interval_minutes
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not get settings for user {user_id}: {e}")
            return 30  # Default

    def _job_executed_listener(self, event):
        """Log successful job execution."""
        logger.debug(f"Job {event.job_id} executed successfully")

    def _job_error_listener(self, event):
        """Log job execution errors."""
        logger.error(
            f"Job {event.job_id} failed: {event.exception}",
            exc_info=True
        )

    def start_consciousness_check_schedule(self):
        """
        Start consciousness check schedules for all active users.
        
        Called during application startup to initialize all jobs.
        """
        try:
            db = next(get_db())
            try:
                from ..models.user import UserDB
                users = db.query(UserDB).filter(UserDB.is_active == True).all()
                
                for user in users:
                    self._schedule_user_if_enabled(db, user.id)
                    
                logger.info(
                    f"⏰ Scheduled consciousness checks for {len(users)} users"
                )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to start consciousness check schedules: {e}")

    def _schedule_user_if_enabled(self, db, user_id: str):
        """
        Schedule consciousness check for user if enabled in settings.
        
        Args:
            db: Database session
            user_id: User ID
        """
        try:
            from .settings_service import SettingsService
            settings_service = SettingsService(db)
            settings = settings_service.get_user_settings(user_id)
            
            if settings.consciousness_check_enabled:
                self.schedule_user_consciousness_checks(
                    user_id=user_id,
                    interval_minutes=settings.consciousness_check_interval_minutes,
                    enabled=True
                )
            else:
                logger.info(
                    f"Consciousness checks disabled for user {user_id[:8]}..."
                )
        except Exception as e:
            logger.error(
                f"Failed to schedule for user {user_id}: {e}"
            )


def run_consciousness_check_job(user_id: str):
    """
    Execute a scheduled consciousness check.
    
    This is the job function that APScheduler runs on schedule.
    It's defined at module level to be picklable.
    
    Args:
        user_id: UUID of the user (as string)
    """
    logger.info(f"🧠 Running scheduled consciousness check for user {user_id[:8]}...")
    
    start_time = utc_now()
    scheduled_analysis = None
    
    try:
        # Get database session
        db = next(get_db())
        
        try:
            from .scheduled_analysis_service import ScheduledAnalysisService
            from .settings_service import SettingsService
            from .thought_service import ThoughtService
            from .claude_service import ClaudeService
            from .claude_analysis_service import ClaudeAnalysisService
            
            scheduled_service = ScheduledAnalysisService(db)
            settings_service = SettingsService(db)
            thought_service = ThoughtService(db)
            
            # Create scheduled analysis record
            scheduled_analysis = scheduled_service.create_scheduled_run(
                user_id=user_id,
                scheduled_at=start_time,
                triggered_by="scheduler"
            )
            
            # Mark as running
            scheduled_service.mark_running(scheduled_analysis.id)
            
            # Check if there are new thoughts since last check
            new_thought_count = scheduled_service.count_thoughts_since_last_check(
                user_id
            )
            
            if new_thought_count == 0:
                # Skip - no new thoughts
                scheduled_service.mark_skipped(
                    analysis_id=scheduled_analysis.id,
                    reason="no_new_thoughts",
                    thoughts_since_last=0
                )
                logger.info(
                    f"⏭️  Skipped consciousness check for user {user_id[:8]}... "
                    f"- no new thoughts"
                )
                return
            
            # Get settings for depth configuration
            depth_config = settings_service.get_analysis_depth_config(user_id)
            
            # Get thoughts to analyze based on depth config
            thoughts, total = thought_service.list_thoughts(
                user_id=user_id,
                status=ThoughtStatus.ACTIVE,
                limit=depth_config.max_thoughts or 50,
                offset=0,
                sort_by="created_at",
                sort_order="desc"
            )
            
            if not thoughts:
                scheduled_service.mark_skipped(
                    analysis_id=scheduled_analysis.id,
                    reason="no_thoughts_found",
                    thoughts_since_last=new_thought_count
                )
                logger.info(
                    f"⏭️  Skipped consciousness check for user {user_id[:8]}... "
                    f"- no active thoughts found"
                )
                return
            
            # Call Claude for analysis
            claude = ClaudeService()
            analysis_result = claude.consciousness_check(
                thoughts, 
                timeframe=f"last {len(thoughts)}"
            )
            
            # Record the analysis result
            analysis_service = ClaudeAnalysisService(db)
            analysis_record = analysis_service.record_analysis(
                user_id=user_id,
                analysis_type=AnalysisType.CONSCIOUSNESS_CHECK,
                summary=analysis_result.get("summary", ""),
                tokens_used=analysis_result.get("tokens_used", 0),
                themes=analysis_result.get("themes", []),
                suggested_action="\n".join(
                    analysis_result.get("suggested_actions", [])
                ),
                raw_response=analysis_result
            )
            
            # Calculate duration
            duration_ms = int(
                (utc_now() - start_time).total_seconds() * 1000
            )
            
            # Mark as completed
            scheduled_service.mark_completed(
                analysis_id=scheduled_analysis.id,
                thoughts_analyzed=len(thoughts),
                duration_ms=duration_ms,
                result_id=analysis_record.id
            )
            
            logger.info(
                f"✅ Completed consciousness check for user {user_id[:8]}...: "
                f"{len(thoughts)} thoughts in {duration_ms}ms"
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(
            f"❌ Failed consciousness check for user {user_id[:8]}...: {e}",
            exc_info=True
        )
        
        if scheduled_analysis:
            try:
                db = next(get_db())
                try:
                    from .scheduled_analysis_service import ScheduledAnalysisService
                    scheduled_service = ScheduledAnalysisService(db)
                    scheduled_service.mark_failed(
                        analysis_id=scheduled_analysis.id,
                        error_message=str(e)
                    )
                finally:
                    db.close()
            except Exception as mark_error:
                logger.error(f"Could not mark analysis as failed: {mark_error}")


# Global scheduler instance
_scheduler: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerService()
    return _scheduler


def reset_scheduler():
    """Reset the global scheduler (useful for testing)."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
