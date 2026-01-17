# Codebase Structure

**Analysis Date:** 2026-01-17

## Directory Layout

```
Hack-Roll/
├── backend/                # Python FastAPI backend
│   ├── routers/           # API endpoint definitions
│   ├── services/          # Business logic services
│   ├── tests/             # pytest test suite
│   └── alembic/           # Database migrations
├── mobile/                 # React Native + Expo mobile app
│   ├── src/
│   │   ├── screens/       # Screen components
│   │   ├── components/    # Reusable UI components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── api/           # API client
│   │   └── utils/         # Utility functions
│   └── __tests__/         # Jest test files
├── ml/                     # ML training pipeline (optional)
│   ├── scripts/           # Training and evaluation scripts
│   └── tests/             # ML tests
├── scripts/                # Utility scripts
├── docs/                   # Documentation
├── .planning/              # Planning documents
│   └── codebase/          # This codebase map
├── CLAUDE.md               # Project instructions
├── docker-compose.yml      # Local dev services
└── deploy.sh               # Deployment script
```

## Directory Purposes

**backend/**
- Purpose: Python FastAPI backend API and processing
- Contains: API endpoints, services, models, tests
- Key files: `main.py` (entry point), `processor.py` (audio pipeline), `models.py` (database models)
- Subdirectories: `routers/` (endpoints), `services/` (business logic), `tests/` (pytest), `alembic/` (migrations)

**backend/routers/**
- Purpose: API endpoint definitions
- Contains: `sessions.py` (session CRUD), `groups.py` (group stats)
- Key files: `sessions.py` - main session lifecycle endpoints

**backend/services/**
- Purpose: Business logic and external service integrations
- Contains: `diarization.py` (pyannote), `transcription.py` (MERaLiON), `firebase.py` (real-time sync)
- Key files: All three services are critical to processing

**backend/tests/**
- Purpose: Backend test suite
- Contains: pytest tests for endpoints and processing
- Key files: `conftest.py` (fixtures), `test_sessions.py` (endpoint tests)

**mobile/**
- Purpose: React Native mobile application
- Contains: Expo project with TypeScript
- Key files: `package.json`, `src/` directory
- Subdirectories: `src/screens/`, `src/components/`, `src/hooks/`, `src/api/`, `src/utils/`

**mobile/src/screens/**
- Purpose: Main application screens
- Contains: Screen components for each flow
- Key files: `RecordingScreen.tsx`, `ProcessingScreen.tsx`, `ClaimingScreen.tsx`, `ResultsScreen.tsx`, `StatsScreen.tsx`, `WrappedScreen.tsx`

**mobile/src/hooks/**
- Purpose: Custom React hooks for state management
- Contains: Recording, playback, session status hooks
- Key files: `useRecording.ts`, `useAudioPlayback.ts`, `useSessionStatus.ts`

**mobile/src/api/**
- Purpose: Backend API client
- Contains: `client.ts` - centralized API communication
- Key files: `client.ts`

**ml/**
- Purpose: Optional ML training pipeline
- Contains: Training scripts, evaluation, data processing
- Key files: `scripts/prepare_imda_data.py`, `scripts/train_lora.py`, `scripts/evaluate.py`
- Note: Not required for hackathon - using pre-trained models

**scripts/**
- Purpose: Utility and test scripts
- Contains: Model testing scripts
- Key files: `test_meralion.py`, `test_pyannote.py`

## Key File Locations

**Entry Points:**
- `backend/main.py` - FastAPI API server entry
- `backend/worker.py` - Background job worker
- `mobile/` - Expo app entry (via Expo)

**Configuration:**
- `backend/.env.example` - Backend environment template
- `mobile/.env.example` - Mobile environment template
- `backend/config.py` - Configuration loading
- `docker-compose.yml` - Local dev services

**Core Logic:**
- `backend/processor.py` - Audio processing pipeline
- `backend/services/diarization.py` - Speaker segmentation
- `backend/services/transcription.py` - Speech-to-text
- `backend/models.py` - Database models
- `mobile/src/hooks/useRecording.ts` - Recording logic

**Testing:**
- `backend/tests/` - Python tests (pytest)
- `mobile/__tests__/` - Mobile tests (Jest)

**Documentation:**
- `CLAUDE.md` - Project instructions and architecture
- `docs/` - Additional documentation
- `README.md` - Project overview

## Naming Conventions

**Files:**
- snake_case.py - Python files (main.py, processor.py)
- camelCase.ts/tsx - TypeScript files (useRecording.ts)
- PascalCase.tsx - React components (RecordingScreen.tsx)
- kebab-case for directories in some places

**Directories:**
- lowercase - All directories (backend/, mobile/, scripts/)
- Plural for collections (routers/, services/, screens/, hooks/)

**Special Patterns:**
- `__init__.py` - Python package markers
- `.test.ts` / `.test.tsx` - Test files
- `.example` - Template files (.env.example)

## Where to Add New Code

**New API Endpoint:**
- Router: `backend/routers/{name}.py`
- Register in: `backend/main.py`
- Tests: `backend/tests/test_{name}.py`

**New Service:**
- Implementation: `backend/services/{name}.py`
- Tests: `backend/tests/test_{name}.py` or in existing test files

**New Mobile Screen:**
- Screen: `mobile/src/screens/{Name}Screen.tsx`
- Register in navigation config
- Tests: `mobile/__tests__/screens/{Name}Screen.test.tsx`

**New Hook:**
- Implementation: `mobile/src/hooks/use{Name}.ts`
- Tests: `mobile/__tests__/hooks/use{Name}.test.ts`

**New Component:**
- Implementation: `mobile/src/components/{Name}.tsx`
- Tests: `mobile/__tests__/components/{Name}.test.tsx`

**Utilities:**
- Backend: `backend/` (no dedicated utils dir yet)
- Mobile: `mobile/src/utils/`

## Special Directories

**.planning/**
- Purpose: Project planning and codebase documentation
- Source: Generated by planning workflows
- Committed: Yes

**backend/alembic/**
- Purpose: Database migrations
- Source: Generated by `alembic revision`
- Committed: Yes

**ml/outputs/**
- Purpose: Trained model outputs (if fine-tuning)
- Source: Generated by training scripts
- Committed: No (add to .gitignore)

---

*Structure analysis: 2026-01-17*
*Update when directory structure changes*
