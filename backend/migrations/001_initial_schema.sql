-- LahStats Database Schema
-- Full migration based on docs/plans/2025-01-17-supabase-integration-design.md
-- Run this in Supabase SQL Editor or via psql
-- FIXED: Reordered to avoid circular dependencies

-- =============================================================================
-- PART 1: CREATE ALL TABLES (without RLS policies yet)
-- =============================================================================

-- 1. PROFILES TABLE
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. GROUPS TABLE
CREATE TABLE IF NOT EXISTS public.groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    created_by UUID REFERENCES public.profiles(id) NOT NULL,
    invite_code VARCHAR(10) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_groups_invite_code ON public.groups(invite_code);

-- 3. GROUP MEMBERS TABLE (must exist before groups RLS policies)
CREATE TABLE IF NOT EXISTS public.group_members (
    id BIGSERIAL PRIMARY KEY,
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(group_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_group_members_user ON public.group_members(user_id);
CREATE INDEX IF NOT EXISTS idx_group_members_group ON public.group_members(group_id);

-- 4. SESSIONS TABLE
CREATE TABLE IF NOT EXISTS public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,
    started_by UUID REFERENCES public.profiles(id) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'recording',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    progress INT DEFAULT 0,
    audio_url TEXT,
    duration_seconds INT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_group ON public.sessions(group_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON public.sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON public.sessions(started_at DESC);

-- 5. SESSION SPEAKERS TABLE
CREATE TABLE IF NOT EXISTS public.session_speakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
    speaker_label VARCHAR(50) NOT NULL,
    segment_count INT DEFAULT 0,
    total_duration_seconds DECIMAL(10,2),
    sample_audio_url TEXT,
    sample_start_time DECIMAL(10,2),
    claimed_by UUID REFERENCES public.profiles(id),
    claimed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(session_id, speaker_label)
);

CREATE INDEX IF NOT EXISTS idx_session_speakers_session ON public.session_speakers(session_id);
CREATE INDEX IF NOT EXISTS idx_session_speakers_unclaimed ON public.session_speakers(session_id, claimed_by)
    WHERE claimed_by IS NULL;

-- 6. SPEAKER WORD COUNTS TABLE
CREATE TABLE IF NOT EXISTS public.speaker_word_counts (
    id BIGSERIAL PRIMARY KEY,
    session_speaker_id UUID REFERENCES public.session_speakers(id) ON DELETE CASCADE NOT NULL,
    word VARCHAR(50) NOT NULL,
    count INT NOT NULL DEFAULT 1,
    UNIQUE(session_speaker_id, word)
);

CREATE INDEX IF NOT EXISTS idx_speaker_word_counts_speaker ON public.speaker_word_counts(session_speaker_id);

-- 7. WORD COUNTS TABLE
CREATE TABLE IF NOT EXISTS public.word_counts (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,
    word VARCHAR(50) NOT NULL,
    count INT NOT NULL DEFAULT 1,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT word_counts_unique UNIQUE(session_id, user_id, word)
);

CREATE INDEX IF NOT EXISTS idx_word_counts_user ON public.word_counts(user_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_word_counts_group ON public.word_counts(group_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_word_counts_session ON public.word_counts(session_id);
CREATE INDEX IF NOT EXISTS idx_word_counts_word ON public.word_counts(word);

-- 8. USER STATS CACHE TABLE
CREATE TABLE IF NOT EXISTS public.user_stats_cache (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_sessions INT DEFAULT 0,
    total_words INT DEFAULT 0,
    top_words JSONB,
    group_rank INT,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, group_id, period_type, period_start)
);

CREATE INDEX IF NOT EXISTS idx_user_stats_cache_user_period ON public.user_stats_cache(user_id, period_type, period_start DESC);
CREATE INDEX IF NOT EXISTS idx_user_stats_cache_group_period ON public.user_stats_cache(group_id, period_type, period_start DESC);

-- 9. TARGET WORDS TABLE
CREATE TABLE IF NOT EXISTS public.target_words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50),
    display_name VARCHAR(50),
    emoji VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_target_words_category ON public.target_words(category);
CREATE INDEX IF NOT EXISTS idx_target_words_active ON public.target_words(is_active) WHERE is_active = true;

-- 10. AUDIO CHUNKS TABLE
CREATE TABLE IF NOT EXISTS public.audio_chunks (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
    chunk_number INT NOT NULL,
    duration_seconds DECIMAL(10,2),
    file_url TEXT NOT NULL,
    file_size_bytes BIGINT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed BOOLEAN DEFAULT false,
    UNIQUE(session_id, chunk_number)
);

CREATE INDEX IF NOT EXISTS idx_audio_chunks_session ON public.audio_chunks(session_id, chunk_number);
CREATE INDEX IF NOT EXISTS idx_audio_chunks_unprocessed ON public.audio_chunks(session_id)
    WHERE processed = false;

-- =============================================================================
-- PART 2: SEED DATA
-- =============================================================================

-- Seed target words (only insert if not exists)
INSERT INTO public.target_words (word, category, display_name, emoji) VALUES
    ('walao', 'vulgar', 'Walao', '😱'),
    ('cheebai', 'vulgar', 'Cheebai', '🤬'),
    ('lanjiao', 'vulgar', 'Lanjiao', '😤'),
    ('lah', 'particle', 'Lah', '💬'),
    ('lor', 'particle', 'Lor', '🤷'),
    ('sia', 'particle', 'Sia', '😮'),
    ('meh', 'particle', 'Meh', '🤔'),
    ('can', 'colloquial', 'Can', '👍'),
    ('paiseh', 'colloquial', 'Paiseh', '😅'),
    ('shiok', 'colloquial', 'Shiok', '😋'),
    ('sian', 'colloquial', 'Sian', '😩')
ON CONFLICT (word) DO NOTHING;

-- =============================================================================
-- PART 3: DATABASE TRIGGER (for auto-profile creation)
-- =============================================================================

-- Auto-create profile when user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, username, display_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', 'user_' || substr(NEW.id::text, 1, 8)),
        COALESCE(NEW.raw_user_meta_data->>'display_name', 'User')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists (for re-running migration)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =============================================================================
-- PART 4: ENABLE RLS AND ADD POLICIES (now that all tables exist)
-- =============================================================================

-- 1. PROFILES RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view all profiles" ON public.profiles;
CREATE POLICY "Users can view all profiles"
    ON public.profiles FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- 2. GROUPS RLS (now group_members exists!)
ALTER TABLE public.groups ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view groups they belong to" ON public.groups;
CREATE POLICY "Users can view groups they belong to"
    ON public.groups FOR SELECT
    USING (
        id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can create groups" ON public.groups;
CREATE POLICY "Users can create groups"
    ON public.groups FOR INSERT
    WITH CHECK (auth.uid() = created_by);

-- 3. GROUP MEMBERS RLS
ALTER TABLE public.group_members ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view members of their groups" ON public.group_members;
CREATE POLICY "Users can view members of their groups"
    ON public.group_members FOR SELECT
    USING (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can add themselves to groups" ON public.group_members;
CREATE POLICY "Users can add themselves to groups"
    ON public.group_members FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- 4. SESSIONS RLS
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view sessions from their groups" ON public.sessions;
CREATE POLICY "Users can view sessions from their groups"
    ON public.sessions FOR SELECT
    USING (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can create sessions in their groups" ON public.sessions;
CREATE POLICY "Users can create sessions in their groups"
    ON public.sessions FOR INSERT
    WITH CHECK (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can update sessions in their groups" ON public.sessions;
CREATE POLICY "Users can update sessions in their groups"
    ON public.sessions FOR UPDATE
    USING (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );

-- 5. SESSION SPEAKERS RLS
ALTER TABLE public.session_speakers ENABLE ROW LEVEL SECURITY;

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
        )
    );

-- 6. SPEAKER WORD COUNTS RLS
ALTER TABLE public.speaker_word_counts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view speaker word counts from their sessions" ON public.speaker_word_counts;
CREATE POLICY "Users can view speaker word counts from their sessions"
    ON public.speaker_word_counts FOR SELECT
    USING (
        session_speaker_id IN (
            SELECT id FROM public.session_speakers
            WHERE session_id IN (
                SELECT id FROM public.sessions
                WHERE group_id IN (
                    SELECT group_id FROM public.group_members
                    WHERE user_id = auth.uid()
                )
            )
        )
    );

-- 7. WORD COUNTS RLS
ALTER TABLE public.word_counts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view word counts from their groups" ON public.word_counts;
CREATE POLICY "Users can view word counts from their groups"
    ON public.word_counts FOR SELECT
    USING (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );

-- 8. USER STATS CACHE RLS
ALTER TABLE public.user_stats_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view stats from their groups" ON public.user_stats_cache;
CREATE POLICY "Users can view stats from their groups"
    ON public.user_stats_cache FOR SELECT
    USING (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );

-- 9. TARGET WORDS RLS
ALTER TABLE public.target_words ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can view target words" ON public.target_words;
CREATE POLICY "Anyone can view target words"
    ON public.target_words FOR SELECT
    USING (true);

-- 10. AUDIO CHUNKS RLS
ALTER TABLE public.audio_chunks ENABLE ROW LEVEL SECURITY;

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
        )
    );

-- =============================================================================
-- PART 5: DATABASE VIEWS
-- =============================================================================

-- Drop views if they exist
DROP VIEW IF EXISTS public.group_leaderboard_weekly;
DROP VIEW IF EXISTS public.user_stats_all_time;

-- View: Group leaderboard (current week)
CREATE VIEW public.group_leaderboard_weekly AS
SELECT
    gm.group_id,
    p.id as user_id,
    p.username,
    p.display_name,
    SUM(wc.count) as total_words,
    jsonb_object_agg(wc.word, wc.count) as word_breakdown,
    COUNT(DISTINCT wc.session_id) as sessions_participated
FROM public.word_counts wc
JOIN public.profiles p ON wc.user_id = p.id
JOIN public.group_members gm ON p.id = gm.user_id AND wc.group_id = gm.group_id
WHERE wc.detected_at >= date_trunc('week', CURRENT_DATE)
GROUP BY gm.group_id, p.id, p.username, p.display_name
ORDER BY total_words DESC;

-- View: User's personal stats (all time)
CREATE VIEW public.user_stats_all_time AS
SELECT
    user_id,
    COUNT(DISTINCT session_id) as total_sessions,
    COUNT(DISTINCT group_id) as groups_count,
    SUM(count) as total_words,
    COUNT(DISTINCT word) as unique_words,
    jsonb_object_agg(word, total_count) as all_words
FROM (
    SELECT
        user_id,
        session_id,
        group_id,
        word,
        SUM(count) as total_count,
        count
    FROM public.word_counts
    GROUP BY user_id, session_id, group_id, word, count
) subquery
GROUP BY user_id;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

-- Verify tables were created
SELECT 
    schemaname,
    tablename
FROM pg_tables 
WHERE schemaname = 'public'
AND tablename IN (
    'profiles', 'groups', 'group_members', 'sessions', 
    'session_speakers', 'speaker_word_counts', 'word_counts',
    'user_stats_cache', 'target_words', 'audio_chunks'
)
ORDER BY tablename;
