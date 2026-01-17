-- Migration: Make group_id optional for sessions
-- This allows personal recording sessions without requiring a group

ALTER TABLE sessions
ALTER COLUMN group_id DROP NOT NULL;

-- Also make group_id optional for word_counts (for personal sessions)
ALTER TABLE word_counts
ALTER COLUMN group_id DROP NOT NULL;
