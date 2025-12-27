"""Add role column to users table

Revision ID: 0002
Revises: 0001
Create Date: 2025-12-26 12:00:00.000000

Adds RBAC foundation with role column on users table.
Sets existing user (Andy) as admin role.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add role and last_login_at columns to users table."""
    
    # Add role column with default 'user'
    op.add_column(
        'users',
        sa.Column('role', sa.String(20), nullable=False, server_default='user')
    )
    
    # Add last_login_at column
    op.add_column(
        'users',
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Create index on role for filtering
    op.create_index('idx_users_role', 'users', ['role'])
    
    # Create index on is_active for filtering active users
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    
    # Update existing user to admin role
    # Using raw SQL since we may not have email in all cases
    op.execute("UPDATE users SET role = 'admin' WHERE email = 'andy@fennerfam.com'")


def downgrade() -> None:
    """Remove role and last_login_at columns."""
    
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'role')
