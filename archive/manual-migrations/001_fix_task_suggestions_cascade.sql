-- Migration: Fix task_suggestions foreign key constraint
-- Date: 2026-01-01
-- Issue: Deleting thoughts failed because source_thought_id was NOT NULL 
--        but constraint tried to SET NULL
-- Fix: Make column nullable and change CASCADE to SET NULL to preserve suggestions

BEGIN;

-- Drop the existing foreign key constraint
ALTER TABLE task_suggestions 
  DROP CONSTRAINT task_suggestions_source_thought_id_fkey;

-- Make source_thought_id nullable (allows orphaned suggestions)
ALTER TABLE task_suggestions 
  ALTER COLUMN source_thought_id DROP NOT NULL;

-- Re-add foreign key with ON DELETE SET NULL
-- This preserves task suggestions even when source thought is deleted
ALTER TABLE task_suggestions 
  ADD CONSTRAINT task_suggestions_source_thought_id_fkey 
  FOREIGN KEY (source_thought_id) 
  REFERENCES thoughts(id) 
  ON DELETE SET NULL;

COMMIT;

-- Verify
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'task_suggestions' 
  AND column_name = 'source_thought_id';
