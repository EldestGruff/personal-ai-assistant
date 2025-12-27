"""Create user_settings table

Revision ID: 0003
Revises: 0002
Create Date: 2025-12-26 12:00:00.000000

Creates user_settings table for configurable consciousness checks,
auto-analysis settings, and backend preferences.
"""

from alembic import op
import sqlalchemy as sa
from src.models.base import utc_now

# revision identifiers, used by Alembic
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_settings table with all configuration options."""
    
    op.create_table(
        'user_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        
        # Consciousness Check Settings
        sa.Column('consciousness_check_enabled', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('consciousness_check_interval_minutes', sa.Integer, nullable=False, server_default='30'),
        sa.Column('consciousness_check_depth_type', sa.String(20), nullable=False, server_default='smart'),
        sa.Column('consciousness_check_depth_value', sa.Integer, nullable=False, server_default='7'),
        sa.Column('consciousness_check_min_thoughts', sa.Integer, nullable=False, server_default='10'),
        
        # Auto-Analysis Settings
        sa.Column('auto_tagging_enabled', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('auto_task_creation_enabled', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('task_suggestion_mode', sa.String(20), nullable=False, server_default='suggest'),
        
        # Backend Override Settings (optional, overrides env vars)
        sa.Column('primary_backend', sa.String(50), nullable=True),
        sa.Column('secondary_backend', sa.String(50), nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create index for user lookup
    op.create_index('idx_user_settings_user_id', 'user_settings', ['user_id'])
    
    # Create default settings for existing users
    # This uses a subquery to insert settings for all existing users
    op.execute("""
        INSERT INTO user_settings (
            id, user_id, 
            consciousness_check_enabled, consciousness_check_interval_minutes,
            consciousness_check_depth_type, consciousness_check_depth_value,
            consciousness_check_min_thoughts,
            auto_tagging_enabled, auto_task_creation_enabled, task_suggestion_mode,
            created_at, updated_at
        )
        SELECT 
            lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6))),
            id,
            1, 30, 'smart', 7, 10,
            1, 1, 'suggest',
            datetime('now'), datetime('now')
        FROM users
    """)


def downgrade() -> None:
    """Remove user_settings table."""
    
    op.drop_index('idx_user_settings_user_id', table_name='user_settings')
    op.drop_table('user_settings')
