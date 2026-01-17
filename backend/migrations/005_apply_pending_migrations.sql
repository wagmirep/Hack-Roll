-- Migration 005: Apply All Pending Migrations
-- Combines migrations 002, 003, and 004 in the correct order
-- Run this in Supabase SQL Editor
-- Date: 2026-01-17

-- =============================================================================
-- PART 1: MIGRATION 003 - Make group_id optional for sessions
-- =============================================================================

-- Make group_id optional for sessions (allows personal recording sessions)
ALTER TABLE public.sessions
ALTER COLUMN group_id DROP NOT NULL;

-- Make group_id optional for word_counts (for personal sessions)
ALTER TABLE public.word_counts
ALTER COLUMN group_id DROP NOT NULL;

-- Update RLS policies for sessions to handle NULL group_id (personal sessions)
DROP POLICY IF EXISTS "Users can view sessions from their groups" ON public.sessions;
CREATE POLICY "Users can view sessions from their groups"
    ON public.sessions FOR SELECT
    USING (
        -- User can view if they're in the group OR if it's their personal session
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
        OR (group_id IS NULL AND started_by = auth.uid())
    );

DROP POLICY IF EXISTS "Users can create sessions in their groups" ON public.sessions;
CREATE POLICY "Users can create sessions in their groups"
    ON public.sessions FOR INSERT
    WITH CHECK (
        -- User can create if they're in the group OR if it's a personal session
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
        OR (group_id IS NULL AND started_by = auth.uid())
    );

DROP POLICY IF EXISTS "Users can update sessions in their groups" ON public.sessions;
CREATE POLICY "Users can update sessions in their groups"
    ON public.sessions FOR UPDATE
    USING (
        -- User can update if they're in the group OR if it's their personal session
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
        OR (group_id IS NULL AND started_by = auth.uid())
    );

-- Update RLS policies for audio_chunks to handle personal sessions
DROP POLICY IF EXISTS "Users can view chunks from their sessions" ON public.audio_chunks;
CREATE POLICY "Users can view chunks from their sessions"
    ON public.audio_chunks FOR SELECT
    USING (
        session_id IN (
            SELECT id FROM public.sessions
            WHERE group_id IN (
                SELECT group_id FROM public.group_members
                WHERE user_id = auth.uid()
            )
            OR (group_id IS NULL AND started_by = auth.uid())
        )
    );

DROP POLICY IF EXISTS "Users can insert chunks to their sessions" ON public.audio_chunks;
CREATE POLICY "Users can insert chunks to their sessions"
    ON public.audio_chunks FOR INSERT
    WITH CHECK (
        session_id IN (
            SELECT id FROM public.sessions
            WHERE group_id IN (
                SELECT group_id FROM public.group_members
                WHERE user_id = auth.uid()
            )
            OR (group_id IS NULL AND started_by = auth.uid())
        )
    );

-- Update RLS policies for session_speakers to handle personal sessions
DROP POLICY IF EXISTS "Users can view speakers from their group sessions" ON public.session_speakers;
CREATE POLICY "Users can view speakers from their group sessions"
    ON public.session_speakers FOR SELECT
    USING (
        session_id IN (
            SELECT id FROM public.sessions
            WHERE group_id IN (
                SELECT group_id FROM public.group_members
                WHERE user_id = auth.uid()
            )
            OR (group_id IS NULL AND started_by = auth.uid())
        )
    );

DROP POLICY IF EXISTS "Users can claim speakers in their sessions" ON public.session_speakers;
CREATE POLICY "Users can claim speakers in their sessions"
    ON public.session_speakers FOR UPDATE
    USING (
        session_id IN (
            SELECT id FROM public.sessions
            WHERE group_id IN (
                SELECT group_id FROM public.group_members
                WHERE user_id = auth.uid()
            )
            OR (group_id IS NULL AND started_by = auth.uid())
        )
    );

-- =============================================================================
-- PART 2: MIGRATION 002 - Add Support for Three Claiming Modes
-- =============================================================================

-- Add new columns to session_speakers
ALTER TABLE public.session_speakers 
ADD COLUMN IF NOT EXISTS claim_type VARCHAR(20) CHECK (claim_type IN ('self', 'user', 'guest')),
ADD COLUMN IF NOT EXISTS attributed_to_user_id UUID REFERENCES public.profiles(id),
ADD COLUMN IF NOT EXISTS guest_name VARCHAR(100);

-- Add index for attributed_to_user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_session_speakers_attributed_to 
ON public.session_speakers(attributed_to_user_id) 
WHERE attributed_to_user_id IS NOT NULL;

-- Add comments to explain the columns
COMMENT ON COLUMN public.session_speakers.claim_type IS 
'Type of claim: self (claimed by user for themselves), user (tagged as another registered user), guest (tagged as non-registered participant)';

COMMENT ON COLUMN public.session_speakers.claimed_by IS 
'User who performed the claiming action (who clicked the button)';

COMMENT ON COLUMN public.session_speakers.attributed_to_user_id IS 
'For claim_type=user: the registered user who gets the stats. For claim_type=self: same as claimed_by. For claim_type=guest: NULL';

COMMENT ON COLUMN public.session_speakers.guest_name IS 
'For claim_type=guest: the display name of the guest participant. NULL for other claim types';

-- Set claim_type='self' for already claimed speakers where claimed_by exists
UPDATE public.session_speakers
SET 
    claim_type = 'self',
    attributed_to_user_id = claimed_by
WHERE 
    claimed_by IS NOT NULL 
    AND claim_type IS NULL;

-- Add policy for inserting session speakers (for backend processing)
DROP POLICY IF EXISTS "Backend can insert speakers" ON public.session_speakers;
CREATE POLICY "Backend can insert speakers"
    ON public.session_speakers FOR INSERT
    WITH CHECK (
        session_id IN (
            SELECT id FROM public.sessions
        )
    );

-- Drop existing view if it exists
DROP VIEW IF EXISTS public.session_results_with_guests;

-- View: Session results including guest speakers
CREATE VIEW public.session_results_with_guests AS
SELECT
    ss.session_id,
    ss.id as speaker_id,
    ss.speaker_label,
    ss.claim_type,
    ss.claimed_by,
    ss.claimed_at,
    CASE 
        WHEN ss.claim_type = 'guest' THEN ss.guest_name
        WHEN ss.claim_type IN ('self', 'user') THEN p.display_name
        ELSE NULL
    END as display_name,
    CASE 
        WHEN ss.claim_type IN ('self', 'user') THEN p.username
        ELSE NULL
    END as username,
    CASE 
        WHEN ss.claim_type IN ('self', 'user') THEN p.avatar_url
        ELSE NULL
    END as avatar_url,
    ss.attributed_to_user_id,
    ss.total_duration_seconds,
    ss.segment_count
FROM public.session_speakers ss
LEFT JOIN public.profiles p ON ss.attributed_to_user_id = p.id;

-- =============================================================================
-- PART 3: MIGRATION 004 - Rename file_url to storage_path in audio_chunks
-- =============================================================================

-- Check if file_url column exists before renaming
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'audio_chunks' 
        AND column_name = 'file_url'
    ) THEN
        ALTER TABLE public.audio_chunks 
        RENAME COLUMN file_url TO storage_path;
    END IF;
END $$;

-- Also remove file_size_bytes and processed columns if they exist (not used in current schema)
ALTER TABLE public.audio_chunks 
DROP COLUMN IF EXISTS file_size_bytes,
DROP COLUMN IF EXISTS processed;

-- Update the ID column to UUID if it's BIGSERIAL (match models.py)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'audio_chunks'
        AND column_name = 'id'
        AND data_type = 'bigint'
    ) THEN
        -- Drop the existing primary key constraint
        ALTER TABLE public.audio_chunks DROP CONSTRAINT IF EXISTS audio_chunks_pkey;
        
        -- Drop the old default (BIGSERIAL sequence)
        ALTER TABLE public.audio_chunks ALTER COLUMN id DROP DEFAULT;
        
        -- Drop the sequence if it exists
        DROP SEQUENCE IF EXISTS audio_chunks_id_seq;
        
        -- Change column type to UUID (existing rows get new random UUIDs)
        ALTER TABLE public.audio_chunks 
        ALTER COLUMN id SET DATA TYPE UUID USING gen_random_uuid();
        
        -- Set new default for future inserts
        ALTER TABLE public.audio_chunks 
        ALTER COLUMN id SET DEFAULT gen_random_uuid();
        
        -- Re-add primary key
        ALTER TABLE public.audio_chunks ADD PRIMARY KEY (id);
    END IF;
END $$;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Verify sessions.group_id is nullable
SELECT 
    column_name, 
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'sessions'
  AND column_name = 'group_id';

-- Verify word_counts.group_id is nullable
SELECT 
    column_name, 
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'word_counts'
  AND column_name = 'group_id';

-- Verify session_speakers new columns
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'session_speakers'
  AND column_name IN ('claim_type', 'attributed_to_user_id', 'guest_name')
ORDER BY column_name;

-- Verify audio_chunks has storage_path (not file_url)
SELECT 
    column_name, 
    data_type
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'audio_chunks'
  AND column_name IN ('storage_path', 'file_url')
ORDER BY column_name;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

SELECT 'Migration 005 completed successfully! ✅' as status;
