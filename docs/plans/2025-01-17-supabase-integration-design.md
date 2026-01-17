# LahStats Supabase Integration - Full System Design

**Date:** 2025-01-17
**Status:** Design Complete - Ready for Implementation
**Architecture:** Hybrid Supabase Approach

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Philosophy](#architecture-philosophy)
3. [Database Schema](#database-schema)
4. [Authentication Flow](#authentication-flow)
5. [API Endpoints](#api-endpoints)
6. [Mobile App Architecture](#mobile-app-architecture)
7. [Key Implementation Details](#key-implementation-details)
8. [Environment Setup](#environment-setup)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Overview

### System Architecture

**Hybrid Supabase Approach:**
- **Frontend (Mobile)**: Uses `@supabase/supabase-js` client for authentication → receives JWT tokens
- **Backend (FastAPI)**: Direct PostgreSQL connection via SQLAlchemy + JWT validation
- **Database**: Supabase-hosted PostgreSQL
- **Auth**: Supabase Auth (managed service)
- **Storage**: S3/Supabase Storage for audio files

### Why Hybrid?

1. **Best of both worlds**: Supabase's excellent auth + backend's direct SQL control
2. **Backend flexibility**: SQLAlchemy ORM for complex queries, no Supabase JS dependency
3. **Mobile simplicity**: Clean Supabase client for auth, no manual JWT handling
4. **Security**: Service role key in backend bypasses RLS for admin operations

---

## Architecture Philosophy

### Authentication Flow
```
Mobile (Supabase Client) → Supabase Auth → JWT Token
    ↓
Mobile sends JWT to Backend
    ↓
Backend validates JWT → Extracts user_id from 'sub' claim
    ↓
Backend queries PostgreSQL with service role key (bypasses RLS)
```

### Data Flow
```
User Action (Mobile)
    ↓
Supabase Auth (JWT token)
    ↓
Backend API (validates JWT, uses SQLAlchemy)
    ↓
Supabase PostgreSQL (direct connection)
    ↓
Response to Mobile
```

---

## Database Schema

### Entity Relationship Diagram

```
auth.users (Supabase managed)
    ↓ (1:1)
profiles
    ↓ (M:N via group_members)
groups ──────┐
    │        │
    │        ├─→ sessions
    │        │       ↓
    │        │   session_speakers ←── speaker_word_counts
    │        │       ↓ (claiming)
    │        └─→ word_counts
    │                ↓
    └────────────→ user_stats_cache

Supporting Tables:
- target_words (reference data)
- audio_chunks (linked to sessions)
```

### Core Tables

#### 1. `public.profiles`
Extends Supabase's `auth.users` with app-specific profile data.

```sql
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

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

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- RLS Policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view all profiles"
    ON public.profiles FOR SELECT
    USING (true);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);
```

**Purpose**: Store username, display name, avatar. Auto-created via trigger when user signs up.

#### 2. `public.groups`
Friend groups who record together.

```sql
CREATE TABLE public.groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    created_by UUID REFERENCES public.profiles(id) NOT NULL,
    invite_code VARCHAR(10) UNIQUE NOT NULL,  -- For joining groups
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_groups_invite_code ON public.groups(invite_code);

-- RLS Policies
ALTER TABLE public.groups ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view groups they belong to"
    ON public.groups FOR SELECT
    USING (
        id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );
```

**Purpose**: Persistent friend circles. `invite_code` allows easy joining (e.g., "XY7K2M").

#### 3. `public.group_members`
Many-to-many relationship between users and groups.

```sql
CREATE TABLE public.group_members (
    id BIGSERIAL PRIMARY KEY,
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    role VARCHAR(20) DEFAULT 'member',  -- 'admin' or 'member'
    joined_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(group_id, user_id)
);

CREATE INDEX idx_group_members_user ON public.group_members(user_id);
CREATE INDEX idx_group_members_group ON public.group_members(group_id);

-- RLS Policies
ALTER TABLE public.group_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view members of their groups"
    ON public.group_members FOR SELECT
    USING (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );
```

**Purpose**: Track group membership. Role allows future admin features.

#### 4. `public.sessions`
Recording sessions.

```sql
CREATE TABLE public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,
    started_by UUID REFERENCES public.profiles(id) NOT NULL,

    -- Session lifecycle
    status VARCHAR(50) NOT NULL DEFAULT 'recording',
        -- 'recording' → 'processing' → 'ready_for_claiming' → 'completed'
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,

    -- Processing metadata
    progress INT DEFAULT 0,  -- 0-100 for processing progress
    audio_url TEXT,  -- S3/storage URL for full audio file
    duration_seconds INT,  -- Total recording duration

    -- Error handling
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_group ON public.sessions(group_id);
CREATE INDEX idx_sessions_status ON public.sessions(status);
CREATE INDEX idx_sessions_started_at ON public.sessions(started_at DESC);

-- RLS Policies
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view sessions from their groups"
    ON public.sessions FOR SELECT
    USING (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create sessions in their groups"
    ON public.sessions FOR INSERT
    WITH CHECK (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );
```

**Purpose**: Central record for each recording. Status tracks lifecycle.

#### 5. `public.session_speakers`
AI-detected speakers before claiming.

```sql
CREATE TABLE public.session_speakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,

    -- AI diarization output
    speaker_label VARCHAR(50) NOT NULL,  -- 'SPEAKER_00', 'SPEAKER_01', etc.
    segment_count INT DEFAULT 0,  -- Number of speech segments
    total_duration_seconds DECIMAL(10,2),  -- Total speaking time

    -- For claiming UI
    sample_audio_url TEXT,  -- 5-second sample clip URL
    sample_start_time DECIMAL(10,2),  -- When sample starts in full audio

    -- Claiming
    claimed_by UUID REFERENCES public.profiles(id),
    claimed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(session_id, speaker_label)
);

CREATE INDEX idx_session_speakers_session ON public.session_speakers(session_id);
CREATE INDEX idx_session_speakers_unclaimed ON public.session_speakers(session_id, claimed_by)
    WHERE claimed_by IS NULL;

-- RLS Policies
ALTER TABLE public.session_speakers ENABLE ROW LEVEL SECURITY;

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
```

**Purpose**: Backend fills after diarization. Users claim via mobile. Temporary holding table.

#### 6. `public.speaker_word_counts`
Pre-claiming word counts by AI speaker label.

```sql
CREATE TABLE public.speaker_word_counts (
    id BIGSERIAL PRIMARY KEY,
    session_speaker_id UUID REFERENCES public.session_speakers(id) ON DELETE CASCADE NOT NULL,
    word VARCHAR(50) NOT NULL,
    count INT NOT NULL DEFAULT 1,

    UNIQUE(session_speaker_id, word)
);

CREATE INDEX idx_speaker_word_counts_speaker ON public.speaker_word_counts(session_speaker_id);
```

**Purpose**: Backend writes here after transcription. Copied to `word_counts` when claimed.

#### 7. `public.word_counts`
Final attributed word counts (after claiming).

```sql
CREATE TABLE public.word_counts (
    id BIGSERIAL PRIMARY KEY,

    -- Attribution
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,

    -- Word data
    word VARCHAR(50) NOT NULL,
    count INT NOT NULL DEFAULT 1,

    -- Timestamp
    detected_at TIMESTAMPTZ DEFAULT NOW(),

    -- Composite unique constraint
    CONSTRAINT word_counts_unique UNIQUE(session_id, user_id, word)
);

CREATE INDEX idx_word_counts_user ON public.word_counts(user_id, detected_at DESC);
CREATE INDEX idx_word_counts_group ON public.word_counts(group_id, detected_at DESC);
CREATE INDEX idx_word_counts_session ON public.word_counts(session_id);
CREATE INDEX idx_word_counts_word ON public.word_counts(word);

-- RLS Policies
ALTER TABLE public.word_counts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view word counts from their groups"
    ON public.word_counts FOR SELECT
    USING (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );
```

**Purpose**: The money table! Final "Jeff said 'walao' 10 times" data.

#### 8. `public.user_stats_cache`
Pre-computed statistics for fast queries.

```sql
CREATE TABLE public.user_stats_cache (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,

    -- Time period
    period_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'all_time'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Aggregated counts
    total_sessions INT DEFAULT 0,
    total_words INT DEFAULT 0,
    top_words JSONB,  -- {"walao": 45, "lah": 102, "sia": 23}

    -- Rankings
    group_rank INT,  -- User's rank in this group for this period

    -- Metadata
    last_updated TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, group_id, period_type, period_start)
);

CREATE INDEX idx_user_stats_cache_user_period ON public.user_stats_cache(user_id, period_type, period_start DESC);
CREATE INDEX idx_user_stats_cache_group_period ON public.user_stats_cache(group_id, period_type, period_start DESC);

-- RLS Policies
ALTER TABLE public.user_stats_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view stats from their groups"
    ON public.user_stats_cache FOR SELECT
    USING (
        group_id IN (
            SELECT group_id FROM public.group_members
            WHERE user_id = auth.uid()
        )
    );
```

**Purpose**: Cache for fast leaderboards. Updated after each session.

#### 9. `public.target_words`
Master list of Singlish words to track.

```sql
CREATE TABLE public.target_words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50),  -- 'particle', 'vulgar', 'colloquial'
    display_name VARCHAR(50),  -- For pretty display: "walao" → "Walao"
    emoji VARCHAR(10),  -- Optional emoji: "walao" → "😱"
    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_target_words_category ON public.target_words(category);
CREATE INDEX idx_target_words_active ON public.target_words(is_active) WHERE is_active = true;

-- Seed data
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
    ('sian', 'colloquial', 'Sian', '😩');

-- Public read access
ALTER TABLE public.target_words ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view target words"
    ON public.target_words FOR SELECT
    USING (true);
```

**Purpose**: Centralized word list with categories and emojis.

#### 10. `public.audio_chunks`
Uploaded audio segments during recording.

```sql
CREATE TABLE public.audio_chunks (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,

    -- Chunk metadata
    chunk_number INT NOT NULL,  -- Sequential: 0, 1, 2...
    duration_seconds DECIMAL(10,2),
    file_url TEXT NOT NULL,  -- S3/storage URL
    file_size_bytes BIGINT,

    -- Status
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed BOOLEAN DEFAULT false,

    UNIQUE(session_id, chunk_number)
);

CREATE INDEX idx_audio_chunks_session ON public.audio_chunks(session_id, chunk_number);
CREATE INDEX idx_audio_chunks_unprocessed ON public.audio_chunks(session_id)
    WHERE processed = false;

-- RLS Policies
ALTER TABLE public.audio_chunks ENABLE ROW LEVEL SECURITY;

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
```

**Purpose**: Track 30-second chunks. Backend concatenates when processing.

#### 11. Database Views

```sql
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
```

**Purpose**: Common queries as views for performance.

---

## Authentication Flow

### User Registration

```
Mobile App                    Supabase Auth              Backend API              Database
    |                              |                          |                        |
    |--signup(email, password)---> |                          |                        |
    |  + metadata: { username }    |                          |                        |
    |                              |                          |                        |
    |                              |-- Create auth.user ----> |                        |
    |                              |                          |                        |
    |                              |                          |-- Trigger fires -----> |
    |                              |                          |   handle_new_user()    |
    |                              |                          |   INSERT profile       |
    |                              |                          |                        |
    |<--- JWT token + user data ---|                          |                        |
    |                              |                          |                        |
    |-- GET /auth/me (JWT) --------------------------> |                               |
    |                              |                          |-- Validate JWT         |
    |                              |                          |-- Fetch profile -----> |
    |                              |                          |                        |
    |<-------------------- { profile, groups } ---------------|                        |
```

**Key Points:**
- Supabase creates user in `auth.users`
- Database trigger auto-creates profile
- Mobile gets JWT immediately
- Backend validates JWT, extracts `user_id` from `sub` claim

### Sign In

```
Mobile App                    Supabase Auth              Backend API
    |                              |                          |
    |-- signIn(email, password) -> |                          |
    |                              |                          |
    |<--- JWT token + user data ---|                          |
    |                              |                          |
    |-- GET /auth/me (JWT) --------------------------> |
    |                              |                          |
    |<----------- { profile, groups } -----------------|
```

### JWT Validation (Backend)

```python
# backend/auth.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Validates Supabase JWT token and returns user_id.

    Returns:
        str: user_id extracted from JWT 'sub' claim
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Usage in endpoints
@app.get("/auth/me")
async def get_me(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    groups = db.query(Group).join(GroupMember).filter(GroupMember.user_id == user_id).all()
    return {"profile": profile, "groups": groups}
```

### Group Creation & Joining

**Create Group:**
```python
@app.post("/groups")
async def create_group(
    name: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Generate unique invite code
    invite_code = generate_invite_code()  # e.g., "AB7K2M"

    # Create group
    group = Group(name=name, created_by=user_id, invite_code=invite_code)
    db.add(group)
    db.flush()

    # Add creator as admin
    membership = GroupMember(group_id=group.id, user_id=user_id, role="admin")
    db.add(membership)
    db.commit()

    return group
```

**Join Group:**
```python
@app.post("/groups/join")
async def join_group(
    invite_code: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find group by invite code
    group = db.query(Group).filter(Group.invite_code == invite_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    # Check not already member
    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")

    # Add membership
    membership = GroupMember(group_id=group.id, user_id=user_id, role="member")
    db.add(membership)
    db.commit()

    return {"group": group, "membership": membership}
```

---

## API Endpoints

### Complete Endpoint List

```
Authentication & Profile
├── GET    /auth/me                      # Get current user + groups
├── PATCH  /auth/profile                 # Update profile
│
Groups
├── POST   /groups                       # Create group
├── POST   /groups/join                  # Join group via invite code
├── GET    /groups/{group_id}            # Get group details
├── GET    /groups/{group_id}/members    # List members
│
Recording Sessions
├── POST   /sessions                     # Start new recording
├── POST   /sessions/{id}/chunks         # Upload audio chunk
├── POST   /sessions/{id}/end            # End recording & trigger processing
├── GET    /sessions/{id}                # Get session details + status
├── GET    /sessions/{id}/speakers       # Get speakers for claiming
│
Claiming
├── POST   /sessions/{id}/claim          # Claim a speaker
├── GET    /sessions/{id}/results        # Get session results
│
Statistics
├── GET    /groups/{group_id}/stats      # Group leaderboard
├── GET    /users/me/stats               # Personal stats
└── GET    /users/me/wrapped             # Wrapped-style yearly recap
```

### Key Endpoint Examples

#### Recording Flow

**1. Start Session**
```http
POST /sessions
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "group_id": "uuid"
}

Response 201:
{
  "session_id": "uuid",
  "status": "recording",
  "started_at": "2025-01-15T14:00:00Z"
}
```

**2. Upload Chunks (every 30s)**
```http
POST /sessions/{session_id}/chunks
Authorization: Bearer <jwt>
Content-Type: multipart/form-data

chunk_number: 0
audio_file: <binary WAV data>
duration_seconds: 30.5

Response 200:
{
  "chunk_id": 123,
  "chunk_number": 0,
  "next_chunk_number": 1
}
```

**3. End Recording**
```http
POST /sessions/{session_id}/end
Authorization: Bearer <jwt>

{
  "final_duration_seconds": 185.5
}

Response 200:
{
  "session_id": "uuid",
  "status": "processing",
  "ended_at": "2025-01-15T14:03:05Z",
  "estimated_processing_time_seconds": 120
}
```

**4. Poll Status (every 2s)**
```http
GET /sessions/{session_id}
Authorization: Bearer <jwt>

Response 200 (processing):
{
  "session_id": "uuid",
  "status": "processing",
  "progress": 65,
  "duration_seconds": 185
}

Response 200 (ready):
{
  "session_id": "uuid",
  "status": "ready_for_claiming",
  "progress": 100,
  "speaker_count": 3
}
```

**5. Get Speakers**
```http
GET /sessions/{session_id}/speakers
Authorization: Bearer <jwt>

Response 200:
{
  "speakers": [
    {
      "speaker_id": "uuid",
      "speaker_label": "SPEAKER_00",
      "sample_audio_url": "https://...",
      "word_preview": {"walao": 5, "lah": 12},
      "claimed_by": null
    }
  ]
}
```

**6. Claim Speaker**
```http
POST /sessions/{session_id}/claim
Authorization: Bearer <jwt>

{
  "speaker_id": "uuid"
}

Response 200:
{
  "success": true,
  "word_counts": {"walao": 5, "lah": 12},
  "total_words": 17
}
```

**7. Get Results**
```http
GET /sessions/{session_id}/results
Authorization: Bearer <jwt>

Response 200:
{
  "results": [
    {
      "user_id": "uuid",
      "username": "jeff_tan",
      "total_words": 47,
      "words": {"walao": 10, "lah": 25},
      "ranking": 1
    }
  ]
}
```

---

## Mobile App Architecture

### Project Structure

```
mobile/
├── App.tsx                          # Root with providers
├── src/
│   ├── lib/
│   │   ├── supabase.ts              # Supabase client
│   │   └── storage.ts               # AsyncStorage utils
│   │
│   ├── contexts/
│   │   └── AuthContext.tsx          # Auth state
│   │
│   ├── navigation/
│   │   ├── AppNavigator.tsx         # Main nav
│   │   ├── AuthNavigator.tsx        # Auth screens
│   │   └── MainNavigator.tsx        # Authenticated screens
│   │
│   ├── screens/
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   └── SignupScreen.tsx
│   │   ├── groups/
│   │   │   ├── GroupListScreen.tsx
│   │   │   ├── CreateGroupScreen.tsx
│   │   │   └── JoinGroupScreen.tsx
│   │   ├── recording/
│   │   │   ├── RecordingScreen.tsx
│   │   │   ├── ProcessingScreen.tsx
│   │   │   ├── ClaimingScreen.tsx
│   │   │   └── ResultsScreen.tsx
│   │   └── stats/
│   │       ├── StatsScreen.tsx
│   │       └── WrappedScreen.tsx
│   │
│   ├── components/
│   │   ├── AudioPlayer.tsx
│   │   ├── SpeakerCard.tsx
│   │   ├── ProgressBar.tsx
│   │   └── WordBadge.tsx
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useRecording.ts
│   │   ├── useAudioPlayback.ts
│   │   └── useSessionStatus.ts
│   │
│   ├── api/
│   │   ├── client.ts                # Axios + JWT interceptor
│   │   ├── auth.ts
│   │   ├── groups.ts
│   │   ├── sessions.ts
│   │   └── stats.ts
│   │
│   └── types/
│       ├── auth.ts
│       ├── session.ts
│       └── stats.ts
```

### Dependencies Required

```json
{
  "dependencies": {
    "expo": "~50.0.0",
    "react": "18.2.0",
    "react-native": "0.73.0",

    // Navigation
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/stack": "^6.3.20",
    "@react-navigation/bottom-tabs": "^6.5.11",
    "react-native-screens": "^3.29.0",
    "react-native-safe-area-context": "^4.8.2",
    "react-native-gesture-handler": "~2.14.0",

    // Supabase
    "@supabase/supabase-js": "^2.39.0",
    "@react-native-async-storage/async-storage": "^1.21.0",

    // Audio
    "expo-av": "~13.10.0",
    "expo-file-system": "~16.0.0",

    // HTTP
    "axios": "^1.6.5",

    // UI (optional)
    "react-native-paper": "^5.12.0"
  },
  "devDependencies": {
    "@babel/core": "^7.20.0",
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "prettier": "^3.1.1"
  }
}
```

### Core Implementation: Supabase Client

```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});
```

### Core Implementation: Auth Context

```typescript
// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import { api } from '../api/client';

interface AuthContextType {
  session: Session | null;
  profile: Profile | null;
  loading: boolean;
  signUp: (email: string, password: string, username: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }) {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) fetchProfile();
      else setLoading(false);
    });

    // Listen for changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        setSession(session);
        if (session) await fetchProfile();
        else setProfile(null);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const fetchProfile = async () => {
    const data = await api.auth.getMe();
    setProfile(data.profile);
    setLoading(false);
  };

  const signUp = async (email, password, username) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { username } }
    });
    if (error) throw error;
  };

  const signIn = async (email, password) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ session, profile, loading, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

### Core Implementation: API Client with JWT

```typescript
// src/api/client.ts
import axios from 'axios';
import { supabase } from '../lib/supabase';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export const axiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

// Add JWT to all requests
axiosInstance.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// Handle 401 errors (token expired)
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const { data: { session } } = await supabase.auth.refreshSession();
      if (session) {
        error.config.headers.Authorization = `Bearer ${session.access_token}`;
        return axiosInstance.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  auth: {
    getMe: async () => {
      const { data } = await axiosInstance.get('/auth/me');
      return data;
    },
  },
  groups: {
    create: async (name: string) => {
      const { data } = await axiosInstance.post('/groups', { name });
      return data;
    },
    join: async (inviteCode: string) => {
      const { data } = await axiosInstance.post('/groups/join', { invite_code: inviteCode });
      return data;
    },
  },
  sessions: {
    create: async (groupId: string) => {
      const { data } = await axiosInstance.post('/sessions', { group_id: groupId });
      return data;
    },
    uploadChunk: async (sessionId: string, formData: FormData) => {
      const { data } = await axiosInstance.post(`/sessions/${sessionId}/chunks`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return data;
    },
    end: async (sessionId: string, duration: number) => {
      const { data } = await axiosInstance.post(`/sessions/${sessionId}/end`, {
        final_duration_seconds: duration
      });
      return data;
    },
    getStatus: async (sessionId: string) => {
      const { data } = await axiosInstance.get(`/sessions/${sessionId}`);
      return data;
    },
    getSpeakers: async (sessionId: string) => {
      const { data } = await axiosInstance.get(`/sessions/${sessionId}/speakers`);
      return data;
    },
    claimSpeaker: async (sessionId: string, speakerId: string) => {
      const { data } = await axiosInstance.post(`/sessions/${sessionId}/claim`, {
        speaker_id: speakerId
      });
      return data;
    },
  },
  stats: {
    getGroupStats: async (groupId: string, period = 'week') => {
      const { data } = await axiosInstance.get(`/groups/${groupId}/stats`, {
        params: { period }
      });
      return data;
    },
  },
};
```

### Navigation Flow

```
App Launch
    ↓
AuthProvider checks session
    ↓
├── No Session → AuthNavigator
│   ├── LoginScreen
│   ├── SignupScreen
│   └── (On signup) → MainNavigator
│
└── Has Session → MainNavigator (Bottom Tabs)
    ├── Home Tab (GroupListScreen)
    ├── Record Tab (RecordingScreen)
    └── Stats Tab (StatsScreen)

    Modal Stacks:
    ├── Recording Flow:
    │   RecordingScreen → ProcessingScreen → ClaimingScreen → ResultsScreen
    │
    └── Group Management:
        CreateGroupScreen / JoinGroupScreen
```

---

## Key Implementation Details

### Recording Hook

```typescript
// src/hooks/useRecording.ts
import { useState, useRef } from 'react';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { api } from '../api/client';

export function useRecording(groupId: string) {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const recordingRef = useRef<Audio.Recording | null>(null);
  const chunkIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const chunkNumber = useRef(0);

  const startRecording = async () => {
    // Request permissions
    await Audio.requestPermissionsAsync();
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
    });

    // Create session
    const session = await api.sessions.create(groupId);
    setSessionId(session.session_id);

    // Start recording
    const recording = new Audio.Recording();
    await recording.prepareToRecordAsync({
      android: {
        extension: '.wav',
        outputFormat: Audio.RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_DEFAULT,
        audioEncoder: Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_DEFAULT,
        sampleRate: 16000,
        numberOfChannels: 1,
      },
      ios: {
        extension: '.wav',
        audioQuality: Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_HIGH,
        sampleRate: 16000,
        numberOfChannels: 1,
        linearPCMBitDepth: 16,
        linearPCMIsBigEndian: false,
        linearPCMIsFloat: false,
      },
    });

    await recording.startAsync();
    recordingRef.current = recording;
    setIsRecording(true);

    // Upload chunks every 30s
    chunkIntervalRef.current = setInterval(() => {
      uploadChunk(session.session_id);
    }, 30000);

    // Update duration every second
    setInterval(() => {
      setDuration(d => d + 1);
    }, 1000);
  };

  const uploadChunk = async (sessionId: string) => {
    if (!recordingRef.current) return;

    // Stop current recording
    await recordingRef.current.stopAndUnloadAsync();
    const uri = recordingRef.current.getURI();

    if (uri) {
      // Upload to backend
      const formData = new FormData();
      formData.append('chunk_number', chunkNumber.current);
      formData.append('audio_file', {
        uri,
        name: `chunk_${chunkNumber.current}.wav`,
        type: 'audio/wav',
      } as any);
      formData.append('duration_seconds', '30');

      await api.sessions.uploadChunk(sessionId, formData);
      chunkNumber.current++;
    }

    // Start new recording for next chunk
    const newRecording = new Audio.Recording();
    await newRecording.prepareToRecordAsync(/* same config */);
    await newRecording.startAsync();
    recordingRef.current = newRecording;
  };

  const stopRecording = async () => {
    if (!recordingRef.current || !sessionId) return;

    // Clear interval
    if (chunkIntervalRef.current) {
      clearInterval(chunkIntervalRef.current);
    }

    // Upload final chunk
    await uploadChunk(sessionId);

    // End session
    await api.sessions.end(sessionId, duration);

    setIsRecording(false);
    return sessionId;
  };

  return {
    isRecording,
    duration,
    sessionId,
    startRecording,
    stopRecording,
  };
}
```

### Status Polling Hook

```typescript
// src/hooks/useSessionStatus.ts
import { useState, useEffect } from 'react';
import { api } from '../api/client';

export function useSessionStatus(sessionId: string | null) {
  const [status, setStatus] = useState('recording');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!sessionId) return;

    const interval = setInterval(async () => {
      const session = await api.sessions.getStatus(sessionId);
      setStatus(session.status);
      setProgress(session.progress);

      if (session.status === 'ready_for_claiming' || session.status === 'completed') {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [sessionId]);

  return { status, progress };
}
```

---

## Environment Setup

### Mobile (.env)

```bash
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
EXPO_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-settings

# Database (Direct PostgreSQL connection)
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres?sslmode=require

# Storage
S3_BUCKET=lahstats-audio
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Or use Supabase Storage
SUPABASE_STORAGE_BUCKET=audio-files
```

---

## Implementation Roadmap

### Phase 1: Foundation (4-6 hours)

**Database Setup:**
1. Create Supabase project
2. Run all table creation SQL
3. Set up RLS policies
4. Create database trigger for auto-profile creation
5. Seed `target_words` table

**Backend Setup:**
1. Install dependencies: `python-jose`, `python-multipart`
2. Create `auth.py` with JWT validation
3. Update database models for new schema
4. Test JWT validation with Supabase token

**Mobile Setup:**
1. Install new dependencies (remove Firebase, add Supabase)
2. Create `lib/supabase.ts`
3. Create `contexts/AuthContext.tsx`
4. Create `api/client.ts` with interceptors
5. Test auth flow (signup/login)

### Phase 2: Groups & Auth (3-4 hours)

**Backend:**
1. Implement `/groups` endpoints
2. Implement `/groups/join` with invite codes
3. Test group creation and joining

**Mobile:**
1. Create GroupListScreen
2. Create CreateGroupScreen
3. Create JoinGroupScreen
4. Test group management flow

### Phase 3: Recording Flow (6-8 hours)

**Backend:**
1. Implement `/sessions` endpoints
2. Implement chunk upload with S3/Supabase Storage
3. Create background processing job queue
4. Implement diarization pipeline
5. Implement transcription pipeline
6. Test end-to-end processing

**Mobile:**
1. Implement `useRecording` hook
2. Create RecordingScreen with timer
3. Implement chunk upload logic
4. Create ProcessingScreen with polling
5. Test recording → upload → processing

### Phase 4: Claiming & Results (4-5 hours)

**Backend:**
1. Implement speaker claiming logic
2. Copy word counts to final table
3. Implement results endpoint

**Mobile:**
1. Create ClaimingScreen with audio playback
2. Implement `useAudioPlayback` hook
3. Create ResultsScreen with leaderboard
4. Test claiming flow

### Phase 5: Statistics (3-4 hours)

**Backend:**
1. Implement stats endpoints
2. Create cache update job
3. Test leaderboards

**Mobile:**
1. Create StatsScreen
2. Create WrappedScreen
3. Add animations and polish

### Phase 6: Polish & Testing (4-6 hours)

1. Error handling
2. Loading states
3. UI/UX improvements
4. End-to-end testing
5. Bug fixes

**Total Estimated Time: 24-33 hours**

---

## Success Criteria

- [ ] User can sign up and log in
- [ ] User can create and join groups
- [ ] User can start recording and upload chunks
- [ ] Backend processes audio and detects speakers
- [ ] User can claim speakers and see results
- [ ] User can view group leaderboards
- [ ] Stats cache updates correctly
- [ ] All endpoints secured with JWT
- [ ] RLS policies protect data
- [ ] Mobile app handles offline gracefully

---

**Design Status:** ✅ Complete - Ready for Implementation

**Next Steps:**
1. Create Supabase project
2. Run database migrations
3. Set up environment variables
4. Begin Phase 1 implementation
