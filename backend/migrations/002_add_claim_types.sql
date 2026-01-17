-- Migration 002: Add Support for Three Claiming Modes
-- Purpose: Allow speakers to be claimed as self, tagged as guest, or tagged as another user
-- Date: 2026-01-17

-- =============================================================================
-- PART 1: ALTER SESSION_SPEAKERS TABLE
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

-- Add comment to explain the columns
COMMENT ON COLUMN public.session_speakers.claim_type IS 
'Type of claim: self (claimed by user for themselves), user (tagged as another registered user), guest (tagged as non-registered participant)';

COMMENT ON COLUMN public.session_speakers.claimed_by IS 
'User who performed the claiming action (who clicked the button)';

COMMENT ON COLUMN public.session_speakers.attributed_to_user_id IS 
'For claim_type=user: the registered user who gets the stats. For claim_type=self: same as claimed_by. For claim_type=guest: NULL';

COMMENT ON COLUMN public.session_speakers.guest_name IS 
'For claim_type=guest: the display name of the guest participant. NULL for other claim types';

-- =============================================================================
-- PART 2: UPDATE EXISTING DATA (BACKFILL)
-- =============================================================================

-- Set claim_type='self' for already claimed speakers where claimed_by exists
UPDATE public.session_speakers
SET 
    claim_type = 'self',
    attributed_to_user_id = claimed_by
WHERE 
    claimed_by IS NOT NULL 
    AND claim_type IS NULL;

-- =============================================================================
-- PART 3: UPDATE RLS POLICIES
-- =============================================================================

-- Drop and recreate the update policy to allow tagging other users
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
        )
    );

-- Add policy for inserting session speakers (for backend processing)
DROP POLICY IF EXISTS "Backend can insert speakers" ON public.session_speakers;

CREATE POLICY "Backend can insert speakers"
    ON public.session_speakers FOR INSERT
    WITH CHECK (
        session_id IN (
            SELECT id FROM public.sessions
        )
    );

-- =============================================================================
-- PART 4: CREATE HELPER VIEWS
-- =============================================================================

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
-- MIGRATION COMPLETE
-- =============================================================================

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'session_speakers'
  AND column_name IN ('claim_type', 'attributed_to_user_id', 'guest_name')
ORDER BY column_name;
