-- Migration: 003_add_chunk_transcriptions
-- Description: Add chunk_transcriptions table for caching background transcriptions
-- Purpose: Store transcription results computed in the background as chunks are uploaded,
--          enabling faster post-recording processing by reusing cached text.

-- Create the chunk_transcriptions table
CREATE TABLE IF NOT EXISTS chunk_transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    chunk_number INTEGER NOT NULL,

    -- Transcription results
    raw_text TEXT,                    -- Raw model output
    corrected_text TEXT,              -- After apply_corrections()
    word_counts JSONB,                -- {word: count} dict

    -- Metadata
    duration_seconds NUMERIC(10, 3),  -- Chunk duration
    transcribed_at TIMESTAMPTZ,       -- When transcription completed
    error_message TEXT,               -- If transcription failed

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create unique index on (session_id, chunk_number) for idempotent upserts
CREATE UNIQUE INDEX IF NOT EXISTS ix_chunk_transcriptions_session_chunk
    ON chunk_transcriptions(session_id, chunk_number);

-- Create index on session_id for fast lookups
CREATE INDEX IF NOT EXISTS ix_chunk_transcriptions_session_id
    ON chunk_transcriptions(session_id);

-- Add comment for documentation
COMMENT ON TABLE chunk_transcriptions IS 'Cached transcription results for audio chunks, computed in background during recording';
