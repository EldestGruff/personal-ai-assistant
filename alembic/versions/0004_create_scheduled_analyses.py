"""Create scheduled_analyses table

Revision ID: 0004
Revises: 0003
Create Date: 2025-12-26 12:00:00.000000

Creates scheduled_analyses table to track all scheduled consciousness checks,
including their status, results, and performance metrics.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create scheduled_analyses table for tracking scheduled consciousness checks."""
    
    op.create_table(
        'scheduled_analyses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        # Scheduling metadata
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        
        # Execution details
        sa.Column('skip_reason', sa.String(100), nullable=True),
        sa.Column('thoughts_since_last_check', sa.Integer, nullable=True),
        sa.Column('thoughts_analyzed_count', sa.Integer, nullable=True),
        sa.Column('analysis_duration_ms', sa.Integer, nullable=True),
        
        # Results
        sa.Column('analysis_result_id', sa.String(36), sa.ForeignKey('claude_analysis_results.id', ondelete='SET NULL'), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        
        # Trigger source
        sa.Column('triggered_by', sa.String(50), nullable=False, server_default='scheduler'),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes for common queries
    op.create_index('idx_scheduled_analyses_user_status', 'scheduled_analyses', ['user_id', 'status'])
    op.create_index('idx_scheduled_analyses_scheduled_at', 'scheduled_analyses', ['scheduled_at'])
    op.create_index('idx_scheduled_analyses_user_completed', 'scheduled_analyses', ['user_id', 'completed_at'])


def downgrade() -> None:
    """Remove scheduled_analyses table."""
    
    op.drop_index('idx_scheduled_analyses_user_completed', table_name='scheduled_analyses')
    op.drop_index('idx_scheduled_analyses_scheduled_at', table_name='scheduled_analyses')
    op.drop_index('idx_scheduled_analyses_user_status', table_name='scheduled_analyses')
    op.drop_table('scheduled_analyses')
