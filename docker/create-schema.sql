-- Personal AI Assistant - Complete Database Schema
-- This creates all tables needed for the application

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    preferences JSON,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create thoughts table
CREATE TABLE IF NOT EXISTS thoughts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    tags JSON NOT NULL DEFAULT '[]',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    context JSON,
    claude_summary VARCHAR(500),
    claude_analysis JSON,
    related_thought_ids JSON NOT NULL DEFAULT '[]',
    task_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_thoughts_user_id ON thoughts(user_id);
CREATE INDEX IF NOT EXISTS idx_thoughts_created_at ON thoughts(created_at);
CREATE INDEX IF NOT EXISTS idx_thoughts_status ON thoughts(status);
CREATE INDEX IF NOT EXISTS idx_thoughts_updated_at ON thoughts(updated_at);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_thought_id VARCHAR(36) REFERENCES thoughts(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    due_date DATE,
    estimated_effort_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    linked_reminders JSON NOT NULL DEFAULT '[]',
    subtasks JSON NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_source_thought ON tasks(source_thought_id);

-- Create contexts table
CREATE TABLE IF NOT EXISTS contexts (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    current_activity VARCHAR(255),
    active_app VARCHAR(255),
    location VARCHAR(255),
    time_of_day VARCHAR(50),
    energy_level VARCHAR(50),
    focus_state VARCHAR(50),
    thought_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contexts_user_id ON contexts(user_id);
CREATE INDEX IF NOT EXISTS idx_contexts_started_at ON contexts(started_at);

-- Create claude_analysis_results table
CREATE TABLE IF NOT EXISTS claude_analysis_results (
    id VARCHAR(36) PRIMARY KEY,
    thought_id VARCHAR(36) REFERENCES thoughts(id) ON DELETE SET NULL,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    themes JSON NOT NULL DEFAULT '[]',
    suggested_action VARCHAR(1000),
    confidence FLOAT,
    tokens_used INTEGER NOT NULL,
    raw_response JSON,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_claude_results_user_id ON claude_analysis_results(user_id);
CREATE INDEX IF NOT EXISTS idx_claude_results_created_at ON claude_analysis_results(created_at);

-- Create thought_relationships table
CREATE TABLE IF NOT EXISTS thought_relationships (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_thought_id VARCHAR(36) NOT NULL REFERENCES thoughts(id) ON DELETE CASCADE,
    related_thought_id VARCHAR(36) NOT NULL REFERENCES thoughts(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50),
    confidence FLOAT,
    discovered_by VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE(source_thought_id, related_thought_id)
);

CREATE INDEX IF NOT EXISTS idx_thought_relationships_source ON thought_relationships(source_thought_id);
CREATE INDEX IF NOT EXISTS idx_thought_relationships_related ON thought_relationships(related_thought_id);

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);

-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_type VARCHAR(50),
    entity_id VARCHAR(36),
    action VARCHAR(50),
    changes JSON,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);

-- Create alembic_version table to track migrations
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Mark as migrated to initial schema
INSERT INTO alembic_version (version_num) VALUES ('0001') ON CONFLICT DO NOTHING;
