"""Enhance thoughts table with AI intelligence fields

Revision ID: 0005
Revises: 0004
Create Date: 2025-12-26 14:00:00.000000

Phase 3B Spec 2: Adds structured analysis fields to thoughts table for
intent classification, auto-tagging, and actionability detection.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add AI intelligence fields to thoughts table."""
    
    # Add thought_type - detected intent classification
    op.add_column(
        'thoughts',
        sa.Column('thought_type', sa.String(50), nullable=True)
    )
    
    # Add intent_confidence - confidence score for thought_type (0.0-1.0)
    op.add_column(
        'thoughts',
        sa.Column('intent_confidence', sa.Float, nullable=True)
    )
    
    # Add suggested_tags - AI-suggested tags with confidence scores (JSON array)
    op.add_column(
        'thoughts',
        sa.Column('suggested_tags', sa.JSON, nullable=True)
    )
    
    # Add related_topics - discovered topic connections (JSON array)
    op.add_column(
        'thoughts',
        sa.Column('related_topics', sa.JSON, nullable=True)
    )
    
    # Add emotional_tone - detected emotional state
    op.add_column(
        'thoughts',
        sa.Column('emotional_tone', sa.String(50), nullable=True)
    )
    
    # Add urgency - detected urgency level
    op.add_column(
        'thoughts',
        sa.Column('urgency', sa.String(20), nullable=True)
    )
    
    # Add is_actionable - whether thought requires action
    op.add_column(
        'thoughts',
        sa.Column('is_actionable', sa.Boolean, nullable=True)
    )
    
    # Add actionable_confidence - confidence for is_actionable (0.0-1.0)
    op.add_column(
        'thoughts',
        sa.Column('actionable_confidence', sa.Float, nullable=True)
    )
    
    # Add analysis_version - tracks which analysis algorithm version was used
    op.add_column(
        'thoughts',
        sa.Column('analysis_version', sa.Integer, nullable=True, server_default='1')
    )
    
    # Add analyzed_at - when AI analysis was performed
    op.add_column(
        'thoughts',
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Create indexes for common queries
    op.create_index('idx_thoughts_thought_type', 'thoughts', ['thought_type'])
    op.create_index('idx_thoughts_is_actionable', 'thoughts', ['is_actionable'])
    op.create_index('idx_thoughts_urgency', 'thoughts', ['urgency'])
    op.create_index('idx_thoughts_analyzed_at', 'thoughts', ['analyzed_at'])


def downgrade() -> None:
    """Remove AI intelligence fields from thoughts table."""
    
    # Drop indexes first
    op.drop_index('idx_thoughts_analyzed_at', table_name='thoughts')
    op.drop_index('idx_thoughts_urgency', table_name='thoughts')
    op.drop_index('idx_thoughts_is_actionable', table_name='thoughts')
    op.drop_index('idx_thoughts_thought_type', table_name='thoughts')
    
    # Drop columns
    op.drop_column('thoughts', 'analyzed_at')
    op.drop_column('thoughts', 'analysis_version')
    op.drop_column('thoughts', 'actionable_confidence')
    op.drop_column('thoughts', 'is_actionable')
    op.drop_column('thoughts', 'urgency')
    op.drop_column('thoughts', 'emotional_tone')
    op.drop_column('thoughts', 'related_topics')
    op.drop_column('thoughts', 'suggested_tags')
    op.drop_column('thoughts', 'intent_confidence')
    op.drop_column('thoughts', 'thought_type')
