"""
Settings service for the Personal AI Assistant.

Provides business logic for user settings management including
CRUD operations, validation, and analysis depth configuration.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ..models.base import utc_now
from ..models.enums import SettingsDepthType, TaskSuggestionMode
from ..models.settings import (
    UserSettingsCreate,
    UserSettingsUpdate,
    UserSettingsResponse,
    UserSettingsDB,
    AnalysisDepthConfig,
)
from ..models.user import UserDB
from .exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


# Default settings values
DEFAULT_SETTINGS = {
    "consciousness_check_enabled": True,
    "consciousness_check_interval_minutes": 30,
    "consciousness_check_depth_type": SettingsDepthType.SMART.value,
    "consciousness_check_depth_value": 7,
    "consciousness_check_min_thoughts": 10,
    "auto_tagging_enabled": True,
    "auto_task_creation_enabled": True,
    "task_suggestion_mode": TaskSuggestionMode.SUGGEST.value,
}


class SettingsService:
    """
    Business logic for user settings management.
    
    Handles CRUD operations, validation, and default initialization.
    Integrates with scheduler service for dynamic job updates.
    """
    
    def __init__(self, db: Session):
        """
        Initialize settings service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_user_settings(self, user_id: str) -> UserSettingsResponse:
        """
        Get settings for a user. Creates default settings if none exist.
        
        Args:
            user_id: UUID of the user (as string)
            
        Returns:
            UserSettingsResponse object
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        # Verify user exists
        user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise NotFoundError(f"User with ID '{user_id}' not found")
        
        # Get existing settings or create defaults
        settings = self.db.query(UserSettingsDB).filter(
            UserSettingsDB.user_id == user_id
        ).first()
        
        if not settings:
            settings = self._create_default_settings(user_id)
        
        return settings.to_response()
    
    def update_user_settings(
        self, 
        user_id: str, 
        updates: UserSettingsUpdate
    ) -> UserSettingsResponse:
        """
        Update user settings. Validates changes and returns updated settings.
        
        Only updates fields that are provided (partial update support).
        
        Args:
            user_id: UUID of the user (as string)
            updates: Partial settings updates
            
        Returns:
            Updated UserSettingsResponse object
            
        Raises:
            NotFoundError: If user doesn't exist
            ValidationError: If updates are invalid
        """
        # Get current settings (creates defaults if needed)
        settings = self.db.query(UserSettingsDB).filter(
            UserSettingsDB.user_id == user_id
        ).first()
        
        if not settings:
            # Create defaults first
            settings = self._create_default_settings(user_id)
        
        # Track if interval changed (for scheduler update)
        interval_changed = False
        old_interval = settings.consciousness_check_interval_minutes
        
        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                # Convert enum to string if needed
                if isinstance(value, (SettingsDepthType, TaskSuggestionMode)):
                    value = value.value
                setattr(settings, field, value)
                
                if field == "consciousness_check_interval_minutes":
                    interval_changed = True
        
        settings.updated_at = utc_now()
        
        self.db.commit()
        self.db.refresh(settings)
        
        logger.info(
            f"Updated settings for user {user_id}: "
            f"{list(update_data.keys())}"
        )
        
        # Return flag indicating if scheduler should be updated
        response = settings.to_response()
        
        if interval_changed:
            logger.info(
                f"Settings interval changed from {old_interval} to "
                f"{settings.consciousness_check_interval_minutes} minutes"
            )
        
        return response
    
    def reset_to_defaults(self, user_id: str) -> UserSettingsResponse:
        """
        Reset settings to system defaults.
        
        Args:
            user_id: UUID of the user (as string)
            
        Returns:
            Reset UserSettingsResponse object
        """
        settings = self.db.query(UserSettingsDB).filter(
            UserSettingsDB.user_id == user_id
        ).first()
        
        if not settings:
            settings = self._create_default_settings(user_id)
        else:
            # Apply defaults
            for field, value in DEFAULT_SETTINGS.items():
                setattr(settings, field, value)
            
            settings.primary_backend = None
            settings.secondary_backend = None
            settings.updated_at = utc_now()
            
            self.db.commit()
            self.db.refresh(settings)
        
        logger.info(f"Reset settings to defaults for user {user_id}")
        
        return settings.to_response()
    
    def get_analysis_depth_config(self, user_id: str) -> AnalysisDepthConfig:
        """
        Calculate actual analysis parameters based on depth settings.
        
        For 'smart' mode: returns max(last N days, min M thoughts)
        
        Args:
            user_id: UUID of the user (as string)
            
        Returns:
            AnalysisDepthConfig with actual query parameters
        """
        settings = self.get_user_settings(user_id)
        
        depth_type = settings.consciousness_check_depth_type
        depth_value = settings.consciousness_check_depth_value
        min_thoughts = settings.consciousness_check_min_thoughts
        
        config = AnalysisDepthConfig(depth_type=depth_type)
        
        if depth_type == SettingsDepthType.SMART:
            # Smart mode: max(last N days, min M thoughts)
            config.since_date = utc_now() - timedelta(days=depth_value)
            config.min_thoughts = min_thoughts
            config.max_thoughts = None  # No max for smart mode
            
        elif depth_type == SettingsDepthType.LAST_N_THOUGHTS:
            # Exact count of thoughts
            config.since_date = None
            config.max_thoughts = depth_value
            config.min_thoughts = None
            
        elif depth_type == SettingsDepthType.LAST_N_DAYS:
            # All thoughts from last N days
            config.since_date = utc_now() - timedelta(days=depth_value)
            config.max_thoughts = None
            config.min_thoughts = None
            
        elif depth_type == SettingsDepthType.ALL_THOUGHTS:
            # Everything (expensive!)
            config.since_date = None
            config.max_thoughts = None
            config.min_thoughts = None
        
        return config
    
    def _create_default_settings(self, user_id: str) -> UserSettingsDB:
        """
        Create default settings for a user.
        
        Args:
            user_id: UUID of the user (as string)
            
        Returns:
            Newly created UserSettingsDB
        """
        # Verify user exists
        user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise NotFoundError(f"User with ID '{user_id}' not found")
        
        now = utc_now()
        settings = UserSettingsDB(
            id=str(uuid4()),
            user_id=user_id,
            **DEFAULT_SETTINGS,
            created_at=now,
            updated_at=now
        )
        
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        
        logger.info(f"Created default settings for user {user_id}")
        
        return settings
    
    def settings_have_changed(
        self, 
        old: UserSettingsResponse, 
        new: UserSettingsResponse
    ) -> bool:
        """
        Check if settings have changed in ways that affect scheduling.
        
        Args:
            old: Previous settings
            new: Current settings
            
        Returns:
            True if scheduler should be updated
        """
        scheduler_fields = [
            "consciousness_check_enabled",
            "consciousness_check_interval_minutes",
        ]
        
        for field in scheduler_fields:
            if getattr(old, field) != getattr(new, field):
                return True
        
        return False
