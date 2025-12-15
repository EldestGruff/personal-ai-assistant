"""
Background scheduler for periodic tasks.

Handles scheduled consciousness checks and other periodic operations.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .claude_service import ClaudeService
from .thought_service import ThoughtService
from .claude_analysis_service import ClaudeAnalysisService
from ..database.session import get_db
from ..models.enums import AnalysisType, ThoughtStatus
from uuid import UUID

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Background scheduler for periodic tasks.

    Runs consciousness checks and other scheduled operations.
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("📅 Scheduler service started")

    def start_consciousness_check_schedule(self):
        """
        Start the 30-minute consciousness check schedule.

        Runs consciousness checks every 30 minutes for the default user.
        """
        # Schedule consciousness check every 30 minutes
        self.scheduler.add_job(
            func=self._run_consciousness_check,
            trigger=IntervalTrigger(minutes=30),
            id='consciousness_check',
            name='Scheduled Consciousness Check',
            replace_existing=True
        )
        logger.info("⏰ Scheduled consciousness check: every 30 minutes")

    def _run_consciousness_check(self):
        """
        Execute a consciousness check for the default user.

        This runs in the background every 30 minutes.
        """
        try:
            logger.info("🧠 Running scheduled consciousness check...")

            # Get database session
            db = next(get_db())

            try:
                # Default user ID (you'll need to set this to your actual user ID)
                # For now, we'll query all users and run checks for each
                from ..models.user import UserDB
                users = db.query(UserDB).all()

                for user in users:
                    self._check_user_consciousness(db, user.id)

            finally:
                db.close()

            logger.info("✅ Scheduled consciousness check completed")

        except Exception as e:
            logger.error(f"❌ Error during scheduled consciousness check: {e}")

    def _check_user_consciousness(self, db, user_id: UUID):
        """
        Run consciousness check for a specific user.

        Args:
            db: Database session
            user_id: User UUID
        """
        try:
            # Get recent thoughts
            thought_service = ThoughtService(db)
            thoughts, total = thought_service.list_thoughts(
                user_id=user_id,
                status=ThoughtStatus.ACTIVE,
                limit=20,
                offset=0,
                sort_by="created_at",
                sort_order="desc"
            )

            if not thoughts:
                logger.info(f"No thoughts found for user {user_id}, skipping check")
                return

            # Call Claude for analysis
            claude = ClaudeService()
            analysis_result = claude.consciousness_check(thoughts, timeframe="last 20")

            # Record the analysis
            analysis_service = ClaudeAnalysisService(db)
            analysis_record = analysis_service.record_analysis(
                user_id=user_id,
                analysis_type=AnalysisType.CONSCIOUSNESS_CHECK,
                summary=analysis_result.get("summary", ""),
                tokens_used=analysis_result.get("tokens_used", 0),
                themes=analysis_result.get("themes", []),
                suggested_action="\n".join(analysis_result.get("suggested_actions", [])),
                raw_response=analysis_result
            )

            logger.info(
                f"✅ Consciousness check for user {user_id}: "
                f"{len(thoughts)} thoughts, {analysis_result.get('tokens_used', 0)} tokens"
            )

        except Exception as e:
            logger.error(f"Error checking consciousness for user {user_id}: {e}")

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        self.scheduler.shutdown()
        logger.info("📅 Scheduler service stopped")


# Global scheduler instance
_scheduler = None


def get_scheduler() -> SchedulerService:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerService()
    return _scheduler
