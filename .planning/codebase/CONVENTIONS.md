# Coding Conventions

**Analysis Date:** 2026-01-18

## Naming Patterns

**Files:**
- `snake_case.py` - Python modules (`transcription.py`, `test_sessions.py`)
- `PascalCase.tsx` - React components (`RecordingScreen.tsx`, `AudioPlayer.tsx`)
- `camelCase.ts` - TypeScript utilities/hooks (`useRecording.ts`, `formatting.ts`)
- Test files: `test_*.py` for Python, none for TypeScript

**Functions:**
- `snake_case` - Python functions (`apply_corrections`, `count_target_words`)
- `camelCase` - TypeScript functions (`formatDuration`, `claimSpeaker`)
- Async functions: No special prefix in either language

**Variables:**
- `snake_case` - Python variables
- `camelCase` - TypeScript variables
- `UPPER_SNAKE_CASE` - Constants (`CORRECTIONS`, `TARGET_WORDS`, `SAMPLE_RATE`)
- `_underscore_prefix` - Private/internal in Python (`_model`, `_pipeline`)

**Types:**
- `PascalCase` - TypeScript interfaces and types (`Session`, `SpeakerSegment`)
- `PascalCase` - Python dataclasses and Pydantic models (`SpeakerSegment`, `Settings`)

## Code Style

**Python Formatting:**
- Black-compatible style (though no config file present)
- 4-space indentation
- Double quotes for strings
- Line length ~100 characters

**TypeScript Formatting:**
- Prettier with config in `mobile/package.json` format script
- 2-space indentation
- Single quotes for strings
- Semicolons required

**Linting:**
- No ESLint config detected for mobile
- No flake8/pylint config for backend
- Type hints used extensively in Python (typing module)

## Import Organization

**Python Order:**
1. Standard library (`os`, `logging`, `uuid`)
2. Third-party packages (`fastapi`, `sqlalchemy`, `torch`)
3. Local imports (`from config import settings`, `from models import Session`)

**Python Patterns:**
- Absolute imports within backend package
- `from X import Y` style preferred over `import X`

**TypeScript Order:**
1. React/React Native (`import React from 'react'`)
2. External packages (`@supabase/supabase-js`, `axios`)
3. Local imports (`../components/`, `../hooks/`)

## Error Handling

**Python Patterns:**
- Custom exceptions (`ProcessingError`)
- Try/except at function boundaries
- Logging before re-raising: `logger.error(f"Failed: {e}")`
- Explicit error messages with context

**TypeScript Patterns:**
- Try/catch around API calls
- Error state in React components
- Alert.alert() for user-facing errors

**Error Types:**
- Raise on invalid state, missing dependencies
- Log warnings for recoverable issues (continue processing)
- Set model status to "failed" with error_message on critical failures

## Logging

**Framework:**
- Python `logging` module
- Logger per module: `logger = logging.getLogger(__name__)`

**Patterns:**
- Emoji prefixes for visual scanning: `"Starting processing..."`, `"Diarization complete"`
- Structured context: `f"Transcribing segment ({speaker_id}): {text[:50]}"`
- Debug for verbose info, Info for progress, Warning for recoverable, Error for failures

**Where:**
- Log at service boundaries and major operations
- Log durations for performance-sensitive operations

## Comments

**When to Comment:**
- Module docstrings explaining PURPOSE, RESPONSIBILITIES, REFERENCES
- Function docstrings for public APIs (Args, Returns, Raises)
- Inline comments for complex algorithms or non-obvious decisions
- Section headers with `# ======` separators

**Docstring Style:**
- Python: Google-style docstrings
- Purpose/Responsibilities at module level
- Args/Returns/Raises for functions

**Example:**
```python
"""
services/transcription.py - MERaLiON Transcription Service

PURPOSE:
    Wrapper service for MERaLiON ASR speech-to-text model.
    Transcribes Singlish audio segments to text.
"""
```

## Function Design

**Size:**
- Keep functions focused on single responsibility
- Extract helpers for complex logic
- Main pipeline functions can be longer (orchestration)

**Parameters:**
- Use typed parameters with defaults where sensible
- Pydantic models for complex input validation
- Optional parameters with `Optional[Type] = None`

**Return Values:**
- Explicit return types in Python (-> Type)
- Return dataclasses or dicts for structured data
- Raise exceptions for errors, don't return error codes

## Module Design

**Exports:**
- No explicit `__all__` in most modules
- Import what you need: `from services.transcription import transcribe_audio`

**Singletons:**
- ML models use singleton pattern with locks for thread safety
- Global `_model`, `_pipeline` variables with getter functions

**Dependencies:**
- Services depend on config, not on each other directly
- Processor imports from services, not vice versa

## React/TypeScript Patterns

**Components:**
- Functional components with hooks
- Props interfaces defined above component
- Default export for screens

**Hooks:**
- `use` prefix for custom hooks
- Return objects/tuples with named values
- Handle loading/error states internally

**State Management:**
- React Context for auth state (`AuthContext.tsx`)
- Local state with useState for component-specific data
- Polling with useEffect for server state

---

*Convention analysis: 2026-01-18*
*Update when patterns change*
