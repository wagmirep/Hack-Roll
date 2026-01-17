-- Migration 004: Rename file_url to storage_path in audio_chunks table
-- This aligns the database schema with the code changes

ALTER TABLE public.audio_chunks 
RENAME COLUMN file_url TO storage_path;
