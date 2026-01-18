# Codebase Structure

**Analysis Date:** 2026-01-18

## Directory Layout

```
Hack-Roll/
├── backend/                    # FastAPI backend API
│   ├── routers/               # API route handlers
│   ├── services/              # Business logic & ML services
│   ├── tests/                 # Pytest test files
│   ├── alembic/               # Database migrations
│   ├── main.py                # FastAPI app entry point
│   ├── processor.py           # Audio processing pipeline
│   ├── worker.py              # Background job worker
│   ├── models.py              # SQLAlchemy ORM models
│   ├── schemas.py             # Pydantic request/response
│   ├── database.py            # DB connection
│   ├── config.py              # Settings management
│   ├── storage.py             # Supabase Storage wrapper
│   ├── auth.py                # JWT validation
│   └── requirements.txt       # Python dependencies
│
├── mobile/                     # React Native app
│   ├── src/
│   │   ├── screens/           # App screens (Recording, Claiming, etc.)
│   │   ├── components/        # Reusable UI components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── contexts/          # React contexts (Auth)
│   │   ├── navigation/        # React Navigation setup
│   │   ├── api/               # API client
│   │   ├── lib/               # Supabase client
│   │   ├── types/             # TypeScript types
│   │   └── utils/             # Utility functions
│   ├── App.tsx                # Root component
│   ├── package.json           # Node dependencies
│   └── tsconfig.json          # TypeScript config
│
├── scripts/                    # Utility scripts
│   ├── test_meralion.py       # Model testing
│   └── test_pyannote.py       # Diarization testing
│
├── .planning/                  # Project planning docs
│   └── codebase/              # This codebase map
│
├── docs/                       # Documentation
├── instructions/               # Project instructions
├── CLAUDE.md                   # Claude instructions
├── TASKS.md                    # Task tracking
└── README.md                   # Project README
```

## Directory Purposes

**backend/**
- Purpose: Python FastAPI backend API
- Contains: All server-side code for REST API and processing
- Key files: `main.py` (entry), `processor.py` (pipeline), `models.py` (DB)
- Subdirectories: `routers/`, `services/`, `tests/`, `alembic/`

**backend/routers/**
- Purpose: API endpoint handlers
- Contains: `auth.py`, `groups.py`, `sessions.py`, `stats.py`
- Key files: `sessions.py` - recording/claiming endpoints

**backend/services/**
- Purpose: ML services and business logic
- Contains: Transcription, diarization, Firebase, caching
- Key files: `transcription.py`, `diarization.py`, `transcription_cache.py`

**backend/tests/**
- Purpose: Backend unit and integration tests
- Contains: Pytest test files and fixtures
- Key files: `conftest.py` (fixtures), `test_sessions.py`, `test_word_counting.py`

**mobile/src/**
- Purpose: React Native application source
- Contains: All mobile app code
- Subdirectories: `screens/`, `components/`, `hooks/`, `contexts/`, `navigation/`

**mobile/src/screens/**
- Purpose: App screens (views)
- Contains: Recording, Processing, Claiming, Results, Wrapped, Auth screens
- Key files: `RecordingScreen.tsx`, `ClaimingScreen.tsx`, `WrappedScreen.tsx`

**mobile/src/hooks/**
- Purpose: Custom React hooks
- Contains: Recording logic, session status polling, audio playback
- Key files: `useRecording.ts`, `useSessionStatus.ts`, `useAudioPlayback.ts`

## Key File Locations

**Entry Points:**
- `backend/main.py` - FastAPI server startup
- `backend/worker.py` - Background processing worker
- `mobile/App.tsx` - React Native app root

**Configuration:**
- `backend/config.py` - Backend settings (Pydantic)
- `backend/.env` - Environment variables (gitignored)
- `mobile/tsconfig.json` - TypeScript config
- `mobile/package.json` - Node dependencies

**Core Logic:**
- `backend/processor.py` - Audio processing pipeline
- `backend/services/transcription.py` - MERaLiON ASR + corrections
- `backend/services/diarization.py` - pyannote speaker segmentation
- `backend/models.py` - Database models (Session, Profile, Group)

**Testing:**
- `backend/tests/conftest.py` - Pytest fixtures
- `backend/tests/test_sessions.py` - Session endpoint tests
- `backend/tests/test_word_counting.py` - Singlish word counting tests

**Documentation:**
- `CLAUDE.md` - Project instructions for Claude
- `README.md` - Project overview
- `docs/` - Additional documentation

## Naming Conventions

**Files:**
- `snake_case.py` - Python modules
- `PascalCase.tsx` - React components
- `camelCase.ts` - TypeScript utilities/hooks
- `*.test.py` - Python test files

**Directories:**
- lowercase singular/plural - `backend/`, `routers/`, `services/`
- kebab-case for planning - `.planning/`

**Special Patterns:**
- `__init__.py` - Python package markers
- `conftest.py` - Pytest configuration
- `index.ts` - Module barrel exports (not used heavily)

## Where to Add New Code

**New API Endpoint:**
- Router: `backend/routers/{domain}.py`
- Schemas: `backend/schemas.py`
- Tests: `backend/tests/test_{domain}.py`

**New ML Service:**
- Implementation: `backend/services/{service_name}.py`
- Import in: `backend/processor.py`

**New Mobile Screen:**
- Screen: `mobile/src/screens/{ScreenName}Screen.tsx`
- Navigation: Update `mobile/src/navigation/MainNavigator.tsx`

**New Mobile Component:**
- Component: `mobile/src/components/{ComponentName}.tsx`

**New Hook:**
- Hook: `mobile/src/hooks/use{HookName}.ts`

**Database Migration:**
- Create: `alembic revision --autogenerate -m "description"`
- Location: `backend/alembic/versions/`

## Special Directories

**backend/alembic/**
- Purpose: Database migration scripts
- Source: Generated by Alembic CLI
- Committed: Yes (migration history)

**.worktrees/**
- Purpose: Git worktrees for parallel development
- Source: Created by `git worktree add`
- Committed: No (gitignored, local development)

**mobile/node_modules/**
- Purpose: Node.js dependencies
- Source: Installed by npm/bun
- Committed: No (gitignored)

---

*Structure analysis: 2026-01-18*
*Update when directory structure changes*
