"""Create user_profiles table

Revision ID: 0007
Revises: 0006
Create Date: 2025-12-26 14:10:00.000000

Phase 3B Spec 2: Creates user_profiles table for rich user context that
informs personalized AI analysis. Includes ongoing projects, interests,
work style, and discovered patterns.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_profiles table for personalized AI context."""
    
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        
        # Personal context
        sa.Column('ongoing_projects', sa.JSON, nullable=True),  # List of project objects
        sa.Column('interests', sa.JSON, nullable=True),  # List of interest strings
        sa.Column('work_style', sa.String(255), nullable=True),  # e.g., "methodical, do it right"
        sa.Column('adhd_considerations', sa.Text, nullable=True),  # Specific needs/preferences
        
        # Discovered patterns (from consciousness checks)
        sa.Column('common_themes', sa.JSON, nullable=True),  # Extracted themes over time
        sa.Column('thought_patterns', sa.JSON, nullable=True),  # Time of day, frequency, topics
        sa.Column('productivity_insights', sa.Text, nullable=True),
        
        # Communication preferences
        sa.Column('preferred_tone', sa.String(50), nullable=False, server_default='warm_encouraging'),
        sa.Column('detail_level', sa.String(50), nullable=False, server_default='moderate'),
        sa.Column('reference_past_work', sa.Boolean, nullable=False, server_default='1'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_analysis_update', sa.DateTime(timezone=True), nullable=True),
        
        # Constraints
        sa.CheckConstraint(
            "preferred_tone IN ('warm_encouraging', 'professional', 'casual')",
            name='check_preferred_tone'
        ),
        sa.CheckConstraint(
            "detail_level IN ('brief', 'moderate', 'comprehensive')",
            name='check_detail_level'
        ),
    )
    
    # Create index on user_id (already unique, but explicit for queries)
    op.create_index('idx_user_profiles_user_id', 'user_profiles', ['user_id'])


def downgrade() -> None:
    """Remove user_profiles table."""
    
    op.drop_index('idx_user_profiles_user_id', table_name='user_profiles')
    op.drop_table('user_profiles')
