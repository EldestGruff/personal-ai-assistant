"""Create task_suggestions table

Revision ID: 0006
Revises: 0005
Create Date: 2025-12-26 14:05:00.000000

Phase 3B Spec 2: Creates task_suggestions table to track AI-generated task
suggestions with soft delete for ADHD-friendly restoration.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create task_suggestions table for AI-generated task suggestions."""
    
    op.create_table(
        'task_suggestions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_thought_id', sa.String(36), sa.ForeignKey('thoughts.id', ondelete='CASCADE'), nullable=False),
        
        # Suggested task details
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('priority', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('estimated_effort_minutes', sa.Integer, nullable=True),
        sa.Column('due_date_hint', sa.Date, nullable=True),
        
        # Suggestion metadata
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('reasoning', sa.Text, nullable=True),
        
        # User action tracking
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('user_action', sa.String(50), nullable=True),
        sa.Column('user_action_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_task_id', sa.String(36), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True),
        
        # Soft delete (preserve ADHD change-of-mind history)
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deletion_reason', sa.String(100), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        
        # Constraints
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='check_confidence_range'),
        sa.CheckConstraint(
            "status IN ('pending', 'presented', 'accepted', 'rejected', 'expired')",
            name='check_suggestion_status'
        ),
        sa.CheckConstraint(
            "user_action IS NULL OR user_action IN ('accepted', 'rejected', 'modified', 'ignored', 'deleted_then_recreated')",
            name='check_user_action'
        ),
    )
    
    # Create indexes for common queries
    op.create_index('idx_task_suggestions_user_status', 'task_suggestions', ['user_id', 'status'])
    op.create_index('idx_task_suggestions_source_thought', 'task_suggestions', ['source_thought_id'])
    op.create_index('idx_task_suggestions_is_deleted', 'task_suggestions', ['is_deleted'])
    op.create_index('idx_task_suggestions_confidence', 'task_suggestions', ['confidence'])
    op.create_index('idx_task_suggestions_created_at', 'task_suggestions', ['created_at'])
    
    # Partial index for pending suggestions (most common query)
    # Note: SQLite supports partial indexes via WHERE clause
    op.execute(
        """
        CREATE INDEX idx_task_suggestions_user_pending 
        ON task_suggestions(user_id) 
        WHERE status = 'pending' AND is_deleted = false
        """
    )


def downgrade() -> None:
    """Remove task_suggestions table."""
    
    # Drop indexes
    op.execute('DROP INDEX IF EXISTS idx_task_suggestions_user_pending')
    op.drop_index('idx_task_suggestions_created_at', table_name='task_suggestions')
    op.drop_index('idx_task_suggestions_confidence', table_name='task_suggestions')
    op.drop_index('idx_task_suggestions_is_deleted', table_name='task_suggestions')
    op.drop_index('idx_task_suggestions_source_thought', table_name='task_suggestions')
    op.drop_index('idx_task_suggestions_user_status', table_name='task_suggestions')
    
    # Drop table
    op.drop_table('task_suggestions')
