# Quick Reference Card — Print This

**Keep visible during hackathon. Laminate if possible.**

---

## Keyboard Shortcuts

| Do This | Press This |
|---------|------------|
| Plan mode (START HERE) | `Shift+Tab` `Shift+Tab` |
| Accept edits mode | `Shift+Tab` |
| Stop Claude | `Escape` |
| Undo/rewind | `Escape` `Escape` |
| Clear context | Type `/clear` |
| Check context | Type `/context` |
| Compress context | Type `/compact` |

---

## The Golden Workflow

```
1. /clear (fresh start)
       ↓
2. Shift+Tab twice (Plan mode)
       ↓
3. Describe task clearly
       ↓
4. Review Claude's plan
       ↓
5. Approve plan
       ↓
6. Shift+Tab once (Accept edits)
       ↓
7. Claude implements
       ↓
8. Verify it works
       ↓
9. Create PR
       ↓
10. /clear (ready for next task)
```

---

## Warning Signs → Actions

| You See This | Do This |
|--------------|---------|
| Claude repeating itself | `/clear` immediately |
| Quality dropping | Check `/context` → `/clear` |
| Claude undoing its work | `/clear` + simpler prompt |
| Circular reasoning | `/clear` + break task smaller |
| Context >40% full | `/compact` or `/clear` |

---

## Emergency Commands

| Problem | Solution |
|---------|----------|
| Claude broke my code | `git checkout -- .` |
| Need to undo commit | `git reset --soft HEAD~1` |
| Merge conflicts | Ask Claude with `@filename` |

---

## Useful Agents

Say these phrases to Claude:

- "Use the **verify-app** agent" → Tests everything
- "Use the **code-simplifier** agent" → Cleans up code
- "Use the **feature-validator** agent" → Checks requirements
- "Use the **build-validator** agent" → Verifies deployment

---

## Bundled Skills (Auto-Activate)

These skills are in your repo and activate automatically:

| Skill | Triggers When |
|-------|---------------|
| `systematic-debugging` | Bug, error, test failure |
| `test-driven-development` | Implementing features |
| `react-patterns` | Building React components |
| `git-worktrees` | Setting up parallel work |
| `agent-browser` | Browser testing needed |
| `autoskill` | End of session |

**To invoke manually:** "Use the systematic-debugging skill"

---

## Bun Commands (Not npm!)

| Task | Command |
|------|---------|
| Install packages | `bun install` |
| Run dev server | `bun run dev` |
| Run tests | `bun run test` |
| Build | `bun run build` |
| Typecheck | `bun run typecheck` |
| Lint | `bun run lint` |

---

## Context7 (Up-to-Date Docs)

Add "use context7" to prompts involving libraries:

```
Create a Next.js API route. use context7
Set up React Query caching. use context7
Configure Tailwind dark mode. use context7
```

---

## agent-browser (Browser Testing)

**Core workflow:**
```bash
agent-browser open <url>        # Navigate
agent-browser snapshot -i       # Get elements with refs
agent-browser click @e2         # Click by ref
agent-browser fill @e3 "text"   # Fill by ref
agent-browser close             # Done
```

**Key commands:**
```bash
agent-browser snapshot -i          # Interactive elements only
agent-browser screenshot page.png  # Take screenshot
agent-browser get text @e1         # Get element text
agent-browser wait --text "Success" # Wait for text
agent-browser --headed open <url>  # Debug: show browser
```

**Ref system:** After `snapshot -i`, elements have refs like `@e1`, `@e2`. Use these refs for all interactions — they're deterministic!

---

## Custom Commands

Type `/` then command name:

| Command | What It Does |
|---------|--------------|
| `/create-endpoint [name]` | New API with types + error handling |
| `/create-component [name]` | New React component |
| `/fix-lint` | Fix all linting errors |
| `/code-review` | Review before PR |

---

## Before Every PR

```
bun run typecheck  ← Must pass
bun run lint       ← Must pass
bun run test       ← Must pass
```

---

*Card 1 of 1 — Claude Code Hackathon Quick Reference*
