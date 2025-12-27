"""
User Profile Service for Personal AI Assistant.

Phase 3B Spec 2: Manages user profiles with ongoing projects, interests,
work style, and discovered patterns. Profiles inform all AI analysis
to make responses personal and contextual.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.models import (
    UserProfileDB,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    PreferredTone,
    DetailLevel,
)


class UserProfileService:
    """
    Manages user profiles for personalized AI context.
    
    Handles:
    - Profile creation (auto-created for new users)
    - Profile updates
    - Pattern discovery integration
    - Default profile initialization
    """
    
    def __init__(self, db: Session):
        """
        Initialize UserProfileService.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    async def get_profile(self, user_id: UUID) -> UserProfileDB:
        """
        Get user profile, creating default if doesn't exist.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            UserProfileDB record
        """
        profile = self.db.query(UserProfileDB).filter(
            UserProfileDB.user_id == str(user_id)
        ).first()
        
        if not profile:
            profile = await self.initialize_default_profile(user_id)
        
        return profile
    
    async def get_profile_response(self, user_id: UUID) -> UserProfileResponse:
        """
        Get user profile as API response model.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            UserProfileResponse for API
        """
        profile = await self.get_profile(user_id)
        return profile.to_response()
    
    async def initialize_default_profile(self, user_id: UUID) -> UserProfileDB:
        """
        Create default profile for new user.
        
        Initializes with reasonable defaults that can be customized later.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Newly created UserProfileDB
        """
        now = datetime.now(timezone.utc)
        
        profile = UserProfileDB(
            id=str(uuid4()),
            user_id=str(user_id),
            ongoing_projects=[
                {
                    "name": "Personal AI Assistant",
                    "status": "active",
                    "description": "Building thought capture system"
                }
            ],
            interests=["automation", "AI", "productivity"],
            work_style="methodical, values doing things right",
            adhd_considerations="Needs task suggestions due to thought capture challenges. Values immediate action items.",
            common_themes=[],
            thought_patterns=None,
            productivity_insights=None,
            preferred_tone=PreferredTone.WARM_ENCOURAGING.value,
            detail_level=DetailLevel.MODERATE.value,
            reference_past_work=True,
            created_at=now,
            updated_at=now,
            last_analysis_update=None,
        )
        
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    async def update_profile(
        self,
        user_id: UUID,
        updates: UserProfileUpdate
    ) -> UserProfileDB:
        """
        Update user profile with new information.
        
        Only updates fields that are explicitly provided.
        
        Args:
            user_id: UUID of the user
            updates: Fields to update
            
        Returns:
            Updated UserProfileDB
        """
        profile = await self.get_profile(user_id)
        
        # Apply updates for non-None fields
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                # Handle enum values
                if field in ('preferred_tone', 'detail_level'):
                    value = value.value if hasattr(value, 'value') else value
                setattr(profile, field, value)
        
        profile.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    async def update_patterns(
        self,
        user_id: UUID,
        discovered_patterns: List[str],
        themes: Optional[List[str]] = None
    ) -> UserProfileDB:
        """
        Update discovered patterns from consciousness checks.
        
        Merges new patterns with existing ones to build profile over time.
        
        Args:
            user_id: UUID of the user
            discovered_patterns: New patterns from analysis
            themes: Optional themes to merge
            
        Returns:
            Updated UserProfileDB
        """
        profile = await self.get_profile(user_id)
        
        # Merge patterns - keep unique, limit total
        existing_themes = set(profile.common_themes or [])
        new_patterns = set(discovered_patterns)
        if themes:
            new_patterns.update(themes)
        
        merged = list(existing_themes | new_patterns)
        # Keep most recent/relevant - limit to 10
        profile.common_themes = merged[-10:]
        
        profile.last_analysis_update = datetime.now(timezone.utc)
        profile.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    async def add_project(
        self,
        user_id: UUID,
        name: str,
        status: str = "active",
        description: Optional[str] = None
    ) -> UserProfileDB:
        """
        Add a new ongoing project to user profile.
        
        Args:
            user_id: UUID of the user
            name: Project name
            status: Project status (active, planning, paused, completed)
            description: Optional description
            
        Returns:
            Updated UserProfileDB
        """
        profile = await self.get_profile(user_id)
        
        projects = list(profile.ongoing_projects or [])
        projects.append({
            "name": name,
            "status": status,
            "description": description
        })
        
        profile.ongoing_projects = projects
        profile.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    async def update_project_status(
        self,
        user_id: UUID,
        project_name: str,
        new_status: str
    ) -> UserProfileDB:
        """
        Update status of an ongoing project.
        
        Args:
            user_id: UUID of the user
            project_name: Name of project to update
            new_status: New status value
            
        Returns:
            Updated UserProfileDB
            
        Raises:
            ValueError: If project not found
        """
        profile = await self.get_profile(user_id)
        
        projects = list(profile.ongoing_projects or [])
        found = False
        for proj in projects:
            if proj.get("name") == project_name:
                proj["status"] = new_status
                found = True
                break
        
        if not found:
            raise ValueError(f"Project '{project_name}' not found in profile")
        
        profile.ongoing_projects = projects
        profile.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    async def remove_project(
        self,
        user_id: UUID,
        project_name: str
    ) -> UserProfileDB:
        """
        Remove a project from user profile.
        
        Args:
            user_id: UUID of the user
            project_name: Name of project to remove
            
        Returns:
            Updated UserProfileDB
        """
        profile = await self.get_profile(user_id)
        
        projects = [
            p for p in (profile.ongoing_projects or [])
            if p.get("name") != project_name
        ]
        
        profile.ongoing_projects = projects
        profile.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    async def update_thought_patterns(
        self,
        user_id: UUID,
        patterns: dict
    ) -> UserProfileDB:
        """
        Update thought patterns from analysis.
        
        Args:
            user_id: UUID of the user
            patterns: Pattern data (peak_hours, triggers, etc.)
            
        Returns:
            Updated UserProfileDB
        """
        profile = await self.get_profile(user_id)
        
        # Merge with existing patterns
        existing = profile.thought_patterns or {}
        existing.update(patterns)
        
        profile.thought_patterns = existing
        profile.last_analysis_update = datetime.now(timezone.utc)
        profile.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
