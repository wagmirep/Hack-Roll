# CLAUDE.md — Project Instructions

**Claude reads this file automatically. Keep it updated.**

---

## Project Overview

**Name:** [YOUR HACKATHON PROJECT NAME]

**Description:** [One sentence describing what this project does]

**Tech Stack:**
- Frontend: React + TypeScript + Vite
- Backend: Python + Django
- Database: [SQLite/PostgreSQL/Supabase]
- Package Manager: Bun (NOT npm)

---

## Team

| Name | Role | Working Branch |
|------|------|----------------|
| [Nickolas] | [Role] | feature/member-1 |
| [Winston] | [Role] | feature/member-2 |
| [Harshith] | [Role] | feature/member-3 |
| [Toshiki] | [Role] | feature/member-4 |

---

## Browser Testing with agent-browser

Use agent-browser for UI verification and testing:

```bash
# Core workflow
agent-browser open http://localhost:3000
agent-browser snapshot -i                    # Get elements with refs (@e1, @e2)
agent-browser click @e2                      # Click by ref
agent-browser fill @e3 "test@example.com"   # Fill by ref
agent-browser screenshot test.png            # Take screenshot
agent-browser close
```

**Always use refs from snapshot** — they're deterministic and reliable.

---

## Context7 Integration

**Always use Context7 MCP tools before planning or implementing code that involves external libraries or frameworks:**

1. Use `resolve-library-id` to get the correct library identifier
2. Use `get-library-docs` to pull current documentation
3. Base all code suggestions on the retrieved documentation, not training data

This applies to any library usage, API integration, or framework-specific patterns.

**Shortcut:** Just add "use context7" to any prompt that involves libraries.

---

## Critical Rules

**ALWAYS:**
- Use `bun`, never `npm`
- Run `/clear` between tasks
- Start in Plan mode (Shift+Tab twice)
- Check `/context` when output quality drops
- Verify work with tests before PRs

**NEVER:**
- Modify files in other team members' feature branches
- Skip the planning step
- Push directly to main
- Ignore failing tests

---

## Development Workflow

```bash
# 1. Make changes

# 2. Typecheck (fast)
bun run typecheck

# 3. Run tests
bun run test -- -t "test name"    # Single suite
bun run test:file -- "glob"       # Specific files

# 4. Lint before committing
bun run lint:file -- "file1.ts"   # Specific files
bun run lint                       # All files

# 5. Before creating PR
bun run lint && bun run test
```

---

## File Structure

```
/
├── frontend/          # React app
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Route pages
│   │   ├── hooks/         # Custom React hooks
│   │   ├── utils/         # Helper functions
│   │   └── api/           # API client functions
│   └── package.json
├── backend/           # Django API
│   ├── api/              # Main Django project
│   ├── apps/             # Django apps
│   └── requirements.txt
├── docs/              # Documentation
├── TASKS.md           # Current tasks and assignments
├── CLAUDE.md          # This file
└── .claude/           # Claude Code configuration
```

---

## Code Conventions

### Frontend (TypeScript/React)

- Use functional components with hooks
- One component per file
- Props interfaces above component definition
- Keep components under 200 lines
- Use named exports for components

```typescript
// Good
interface ButtonProps {
  label: string;
  onClick: () => void;
}

export function Button({ label, onClick }: ButtonProps) {
  return <button onClick={onClick}>{label}</button>;
}
```

### Backend (Python/Django)

- Follow PEP 8
- Type hints on all function signatures
- Docstrings on public functions
- Keep views thin, logic in services

```python
# Good
def create_user(email: str, password: str) -> User:
    """Create a new user with the given email and password."""
    ...
```

---

## API Endpoints

Document endpoints as you create them:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| ... | ... | ... |

---

## Environment Variables

### Frontend (.env)

```
VITE_API_URL=http://localhost:8000
```

### Backend (.env)

```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
```

---

## Common Issues

| Problem | Solution |
|---------|----------|
| CORS errors | Check backend CORS settings |
| Module not found | Run `bun install` |
| Database errors | Run migrations: `python manage.py migrate` |
| Type errors | Run `bun run typecheck` and fix issues |

---

## Before Every PR

1. `bun run typecheck` — must pass
2. `bun run lint` — must pass  
3. `bun run test` — must pass
4. Manual verification that the feature works
5. Update TASKS.md to mark task complete

---

*Last updated: [DATE]*

---

## Custom Commands

Use `/` to see available commands. Key commands included:

| Command | What It Does |
|---------|--------------|
| `/create-endpoint [name]` | Creates API endpoint with error handling and types |
| `/create-component [name]` | Creates React component with TypeScript and Tailwind |
| `/fix-lint` | Runs linter and fixes all errors |
| `/code-review` | Reviews session changes before PR |

**Creating new commands:** Add markdown files to `.claude/commands/` directory.
