-- PostgreSQL initialization script for Personal AI Assistant
-- Runs automatically on first database creation

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes will be handled by Alembic migrations
-- This script just sets up extensions

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Personal AI Assistant database initialized';
    RAISE NOTICE 'UUID extension: enabled';
    RAISE NOTICE 'Trigram extension: enabled';
END $$;
