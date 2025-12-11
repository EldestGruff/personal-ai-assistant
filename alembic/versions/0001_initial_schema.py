"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2025-12-10 21:00:00.000000

Creates all tables for Personal AI Assistant:
- users
- thoughts  
- tasks
- contexts
- claude_analysis_results
- thought_relationships
- api_keys
- audit_log
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables and indexes."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('preferences', sa.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True)
    )
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Create thoughts table
    op.create_table(
        'thoughts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('tags', sa.JSON, nullable=False, default='[]'),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('context', sa.JSON, nullable=True),
        sa.Column('claude_summary', sa.String(500), nullable=True),
        sa.Column('claude_analysis', sa.JSON, nullable=True),
        sa.Column('related_thought_ids', sa.JSON, nullable=False, default='[]'),
        sa.Column('task_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('idx_thoughts_user_id', 'thoughts', ['user_id'])
    op.create_index('idx_thoughts_created_at', 'thoughts', ['created_at'], postgresql_using='btree')
    op.create_index('idx_thoughts_status', 'thoughts', ['status'])
    op.create_index('idx_thoughts_updated_at', 'thoughts', ['updated_at'], postgresql_using='btree')
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_thought_id', sa.String(36), sa.ForeignKey('thoughts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('priority', sa.String(50), nullable=False, default='medium'),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('estimated_effort_minutes', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('linked_reminders', sa.JSON, nullable=False, default='[]'),
        sa.Column('subtasks', sa.JSON, nullable=False, default='[]')
    )
    op.create_index('idx_tasks_user_id', 'tasks', ['user_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_priority', 'tasks', ['priority'])
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('idx_tasks_source_thought', 'tasks', ['source_thought_id'])
    
    # Create contexts table
    op.create_table(
        'contexts',
        sa.Column('id', sa.String(255), primary_key=True),  # session_id
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_activity', sa.String(255), nullable=True),
        sa.Column('active_app', sa.String(255), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('time_of_day', sa.String(50), nullable=True),
        sa.Column('energy_level', sa.String(50), nullable=True),
        sa.Column('focus_state', sa.String(50), nullable=True),
        sa.Column('thought_count', sa.Integer, nullable=False, default=0),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('idx_contexts_user_id', 'contexts', ['user_id'])
    op.create_index('idx_contexts_started_at', 'contexts', ['started_at'], postgresql_using='btree')
    
    # Create claude_analysis_results table
    op.create_table(
        'claude_analysis_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('thought_id', sa.String(36), sa.ForeignKey('thoughts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_type', sa.String(50), nullable=False),
        sa.Column('summary', sa.Text, nullable=False),
        sa.Column('themes', sa.JSON, nullable=False, default='[]'),
        sa.Column('suggested_action', sa.String(1000), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('tokens_used', sa.Integer, nullable=False),
        sa.Column('raw_response', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('idx_claude_results_user_id', 'claude_analysis_results', ['user_id'])
    op.create_index('idx_claude_results_created_at', 'claude_analysis_results', ['created_at'], postgresql_using='btree')
    
    # Create thought_relationships table with unique constraint baked in
    # SQLite requires constraints to be defined during table creation
    op.create_table(
        'thought_relationships',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_thought_id', sa.String(36), sa.ForeignKey('thoughts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('related_thought_id', sa.String(36), sa.ForeignKey('thoughts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('discovered_by', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        # unique constraint defined here, not added later with ALTER TABLE
        sa.UniqueConstraint('source_thought_id', 'related_thought_id', name='uq_thought_relationships_source_related')
    )
    op.create_index('idx_thought_relationships_source', 'thought_relationships', ['source_thought_id'])
    op.create_index('idx_thought_relationships_related', 'thought_relationships', ['related_thought_id'])
    
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('key_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'])
    
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.String(36), nullable=True),
        sa.Column('action', sa.String(50), nullable=True),
        sa.Column('changes', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('idx_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('idx_audit_log_entity', 'audit_log', ['entity_type', 'entity_id'])


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table('audit_log')
    op.drop_table('api_keys')
    op.drop_table('thought_relationships')
    op.drop_table('claude_analysis_results')
    op.drop_table('contexts')
    op.drop_table('tasks')
    op.drop_table('thoughts')
    op.drop_table('users')
