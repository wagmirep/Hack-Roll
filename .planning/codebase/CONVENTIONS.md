# Coding Conventions

**Analysis Date:** 2026-01-17

## Naming Patterns

**Files:**
- snake_case.py for Python files (`main.py`, `processor.py`, `word_counting.py`)
- camelCase.ts for TypeScript utilities (`useRecording.ts`, `client.ts`)
- PascalCase.tsx for React components (`RecordingScreen.tsx`, `AudioPlayer.tsx`)
- .test.ts/.test.tsx for test files alongside pattern

**Functions:**
- snake_case for Python functions (`process_session`, `apply_corrections`)
- camelCase for TypeScript/JavaScript (`startRecording`, `uploadChunk`)
- handleEventName for React event handlers (`handleClick`, `handleSubmit`)

**Variables:**
- snake_case for Python (`session_id`, `word_counts`)
- camelCase for TypeScript (`sessionId`, `isRecording`)
- UPPER_SNAKE_CASE for constants in both (`TARGET_WORDS`, `API_URL`)

**Types:**
- PascalCase for Python classes and TypeScript interfaces (`Session`, `SessionSpeaker`)
- No I prefix for interfaces
- Descriptive suffixes: `*Screen`, `*Service`, `*Props`

## Code Style

**Formatting:**
- No Prettier or ESLint config files detected - establish during hackathon
- Recommended: 2-4 space indentation
- Single quotes for TypeScript strings
- Double quotes for Python strings

**Linting:**
- Not configured yet
- Recommended: ESLint for TypeScript, pylint/ruff for Python

## Import Organization

**Python:**
1. Standard library imports
2. Third-party imports
3. Local imports

**TypeScript:**
1. External packages (react, react-native, expo)
2. Internal modules (api/, hooks/, utils/)
3. Relative imports (./, ../)
4. Type imports

**Grouping:**
- Blank line between groups
- Alphabetical within each group recommended

## Error Handling

**Patterns:**
- Python: Throw exceptions, catch at API boundary with HTTPException
- TypeScript: Try/catch in async functions, error state in hooks
- Return structured error responses from API

**Error Types:**
- FastAPI HTTPException with status codes
- Custom error messages for user-facing errors
- Log errors with context before throwing

## Logging

**Framework:**
- Console logging (print statements in Python, console.log in TypeScript)
- Consider structured logging for production

**Patterns:**
- Log at service boundaries
- Include context (session_id, user_id) in logs
- Log state transitions during processing

## Comments

**When to Comment:**
- File-level docstrings explaining purpose and responsibilities (already present)
- Complex algorithms or business logic
- Singlish word corrections dictionary explanations
- API endpoint documentation

**Docstrings:**
- Multi-line docstrings for Python modules and functions
- JSDoc-style comments for TypeScript
- Document PURPOSE, RESPONSIBILITIES, REFERENCES, REFERENCED BY

**TODO Comments:**
- Format: `# TODO:` or `// TODO:`
- Link to hackathon limitations documented in CLAUDE.md

## Function Design

**Size:**
- Keep functions focused on single responsibility
- Extract helpers for complex processing steps

**Parameters:**
- Python: Use type hints for all parameters
- TypeScript: Use TypeScript types/interfaces
- Max 3-4 parameters, use objects for more

**Return Values:**
- Explicit return types in type hints
- Return early for guard clauses
- Structured responses from API endpoints

## Module Design

**Exports:**
- Python: All public functions at module level
- TypeScript: Named exports preferred
- Default exports for React components

**Structure:**
- Each file has comprehensive header docstring
- Clear separation of concerns between files
- Services encapsulate external dependencies

---

*Convention analysis: 2026-01-17*
*Update when patterns change*
