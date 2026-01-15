# Claude Code Hackathon Setup Checklist

**Read this first. Follow it exactly. Estimated time: 30-45 minutes.**

This checklist ensures your entire team is ready to use Claude Code effectively during the hackathon. Complete all sections marked for your role before the event starts.

---

## Part 1: Everyone Completes This

**Time: ~20 minutes**

### 1.1 Install Core Tools

| Step | Command | Verify It Worked |
|------|---------|------------------|
| Install Node.js | Download from nodejs.org | `node --version` shows v18+ |
| Install Bun | Mac: `brew install oven-sh/bun/bun`<br>Windows WSL: `curl -fsSL https://bun.sh/install \| bash` | `bun --version` shows any version |
| Install Claude Code | `npm install -g @anthropic-ai/claude-code` | `claude --version` shows any version |

### 1.2 Authenticate Claude Code

```bash
claude auth login
```

Follow the browser prompts. You need an active Claude Pro or Max subscription.

**Verify:** Run `claude` in any folder. You should see the Claude Code interface.

### 1.3 Install Required Plugins

Run these commands one by one:

```bash
# Frontend design - better UI generation
claude plugin install frontend-design

# Code simplifier - cleanup tool
claude plugin install code-simplifier

# Superpowers - comprehensive skill library
claude plugin marketplace add ora-superpowers
claude plugin install superpowers
```

**Verify:** Run `claude` then type `/skills` — you should see multiple skills listed.

### 1.4 Install agent-browser (Browser Automation)

agent-browser is Vercel's browser automation CLI designed specifically for AI agents. It uses a ref system that makes element selection deterministic and reliable.

```bash
# Install globally
npm install -g agent-browser

# Download Chromium browser
agent-browser install
```

**Linux only:** Also run `agent-browser install --with-deps`

**Verify:** Run `agent-browser open example.com --headed` — a browser window should open. Then `agent-browser close`.

**Why agent-browser over Playwright MCP:**
- Ref system (@e1, @e2) — deterministic element selection from snapshots
- Built for AI agents — optimal workflow for LLMs
- Rust CLI — faster than Node.js MCP servers
- Includes Claude Code skill — automatically loaded

### 1.5 Configure Context7 MCP (Up-to-Date Documentation)

Context7 gives Claude access to current documentation for React, Next.js, Django, Tailwind, and hundreds of other libraries. No more hallucinated APIs.

```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
```

**Optional but recommended:** Get a free API key at https://context7.com/dashboard for higher rate limits, then:

```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest --api-key YOUR_API_KEY
```

**Verify:** Run `claude` then type `/mcp` — you should see "context7" listed as connected.

**Usage:** Add "use context7" to any prompt involving libraries. Example:
- "Create a Next.js middleware that checks for auth cookies. use context7"
- "Set up React Query for data fetching. use context7"

### 1.6 Learn the Essential Shortcuts

**Print this table and keep it visible during the hackathon:**

| Shortcut | What It Does | When To Use |
|----------|--------------|-------------|
| `Shift+Tab` (1x) | Accept Edits mode | After approving a plan |
| `Shift+Tab` (2x) | Plan mode | ALWAYS start here |
| `Shift+Tab` (3x) | Normal mode | When you need control |
| `Escape` | Stop Claude | When Claude is going wrong |
| `Escape` (2x) | Rewind to checkpoint | Undo recent changes |
| `/clear` | Clear context | BETWEEN EVERY TASK |
| `/context` | Check context usage | When quality degrades |
| `/compact` | Compress context | When context >40% full |
| `#` | Add to memory | Save instructions to CLAUDE.md |
| `/` | List commands | Access custom commands |

### 1.7 Practice the Core Workflow

Complete this practice exercise before the hackathon:

1. Create a test folder: `mkdir claude-practice && cd claude-practice`
2. Start Claude: `claude`
3. Enter Plan mode: Press `Shift+Tab` twice
4. Type: "Create a simple React component that shows a greeting. use context7"
5. Review Claude's plan
6. Approve the plan
7. Press `Shift+Tab` once to enter Accept Edits mode
8. Watch Claude implement
9. Type `/clear` when done

**You passed if:** Claude created files without asking permission for each edit, and Context7 was used to fetch React docs.

---

## Part 2: Repository Setup (Team Lead Only)

**Time: ~15 minutes**

### 2.1 Create the Repository

```bash
# Create and initialize
mkdir hackathon-project && cd hackathon-project
git init

# Create monorepo structure
mkdir frontend backend docs

# Initialize frontend
cd frontend && bun create vite . --template react-ts && cd ..

# Initialize backend (choose your stack)
# Django:
cd backend && python -m venv venv && source venv/bin/activate && pip install django && django-admin startproject api . && cd ..
```

### 2.2 Copy the .claude Folder

Copy the entire `.claude` folder from this setup kit into your repository root:

```
hackathon-project/
├── .claude/           ← Copy this folder here
│   ├── agents/
│   ├── skills/
│   └── settings.json
├── frontend/
├── backend/
├── CLAUDE.md          ← Copy this file here
└── TASKS.md           ← Copy this file here
```

### 2.3 Customize CLAUDE.md

Open `CLAUDE.md` and update these sections:
- Project name and description
- Team member names
- Tech stack details
- Any project-specific conventions

### 2.4 Create Git Worktrees for Each Team Member

```bash
# From the main repo directory
git worktree add ../worktrees/member-1 -b feature/member-1
git worktree add ../worktrees/member-2 -b feature/member-2
git worktree add ../worktrees/member-3 -b feature/member-3
git worktree add ../worktrees/member-4 -b feature/member-4
```

### 2.5 Push and Share

```bash
git add .
git commit -m "Initial hackathon setup"
git remote add origin YOUR_REPO_URL
git push -u origin main
```

Share the repo URL with your team. They should clone and work in their assigned worktree.

---

## Part 3: Experienced Developers Only

**Time: ~10 minutes**

### 3.1 Install Docker

Download Docker Desktop from docker.com and verify:
```bash
docker --version
```

### 3.2 Create the Safety Dockerfile

Create `Dockerfile.claude` in your repo root:

```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y nodejs npm python3 python3-pip git curl
RUN npm install -g bun @anthropic-ai/claude-code
WORKDIR /workspace
```

Build it:
```bash
docker build -f Dockerfile.claude -t claude-sandbox .
```

### 3.3 Install Ralph for Autonomous Work

```bash
claude plugin install ralph-wiggum
```

### 3.4 Test Parallel Sessions

Open two terminal windows/tabs:

```bash
# Terminal 1
cd ../worktrees/member-1
claude

# Terminal 2
cd ../worktrees/member-2
claude
```

Both should run independently without conflicts.

### 3.5 Configure GitHub MCP (Optional)

```bash
# Generate token: GitHub → Settings → Developer settings → Personal access tokens
# Required scopes: repo, read:org

claude mcp add --transport http github https://api.github.com/mcp \
  --header "Authorization: Bearer YOUR_GITHUB_TOKEN"
```

### 3.6 Configure Additional MCPs (Optional)

**Playwright MCP** — Backup browser automation if agent-browser has issues:
```bash
claude mcp add playwright -- npx -y @anthropic-ai/mcp-server-playwright
```

**Supabase** — If using Supabase for your database:
```bash
claude mcp add supabase -- npx -y @supabase/mcp-server-supabase@latest \
  --supabase-url YOUR_PROJECT_URL \
  --service-role-key YOUR_SERVICE_ROLE_KEY
```

**Stripe** — If handling payments:
```bash
claude mcp add stripe -- npx -y @anthropic-ai/mcp-server-stripe \
  --api-key YOUR_STRIPE_SECRET_KEY
```

**Verify all MCPs:** Run `/mcp` in Claude to see all connected servers.

---

## Part 4: Pre-Hackathon Verification

**Run these checks the day before the hackathon.**

### Everyone Verifies

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Claude Code runs | `claude` | Interface opens |
| Plugins installed | `/skills` in Claude | Multiple skills listed |
| agent-browser works | `agent-browser open example.com --headed` | Browser window opens |
| Context7 connected | `/mcp` in Claude | "context7" shows connected |
| Bun works | `bun --version` | Version number shown |
| Custom commands work | `/` in Claude | Shows create-endpoint, fix-lint, etc. |

### Team Lead Verifies

| Check | How | Expected Result |
|-------|-----|-----------------|
| Repo accessible | All members can clone | No permission errors |
| Worktrees work | Each member can cd to theirs | Separate branches exist |
| .claude folder present | `ls -la .claude` | agents/, skills/, settings.json |
| CLAUDE.md customized | Open and read | Project details filled in |

### Experienced Devs Verify

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Docker runs | `docker run hello-world` | Success message |
| Dockerfile built | `docker images \| grep claude-sandbox` | Image listed |
| Ralph installed | `/skills` in Claude | Ralph-related skills shown |

---

## Quick Reference: What's in the .claude Folder

```
.claude/
├── settings.json          # Hooks for auto-formatting
├── commands/              # Custom slash commands
│   ├── create-endpoint.md     # /create-endpoint [name]
│   ├── create-component.md    # /create-component [name]
│   ├── fix-lint.md            # /fix-lint
│   └── code-review.md         # /code-review
├── agents/                # Custom subagents
│   ├── verify-app.md          # Tests everything before PRs
│   ├── code-simplifier.md     # Cleans up messy code
│   ├── feature-validator.md   # Checks TASKS.md requirements
│   └── build-validator.md     # Verifies builds work
└── skills/                # Bundled skills (6 total)
    ├── agent-browser/         # Browser automation (Vercel)
    ├── systematic-debugging/  # Structured bug fixing process
    ├── test-driven-development/ # TDD workflow
    ├── git-worktrees/         # Parallel development setup
    ├── react-patterns/        # React + TypeScript patterns
    └── autoskill/             # Learns from your corrections
```

**Bundled skills (in .claude/skills/):** Load automatically, no install needed

**Installed plugins (via CLI):** frontend-design, superpowers, code-simplifier — installed in Part 1.3

**How to use commands:** Type `/create-endpoint auth` or `/fix-lint`

**How to use agents:** Say "Use the verify-app agent" or "Use code-simplifier on these files"

**How to use skills:** They activate automatically based on task, or say "Use the systematic-debugging skill"

**How to use Context7:** Add "use context7" to prompts involving libraries

**How to use agent-browser:** Run `agent-browser open <url>` then `agent-browser snapshot -i` to see elements with refs

---

## Emergency Contacts During Hackathon

| Problem | Solution |
|---------|----------|
| Claude broke my code | `git checkout -- .` to restore |
| Claude is looping | `/clear` then simpler prompt |
| Quality is degrading | `/context` check → `/clear` |
| Need to undo commit | `git reset --soft HEAD~1` |
| Can't authenticate | Re-run `claude auth login` |
| Plugin not working | `claude plugin list` then reinstall |

---

## Checklist Summary

### Before Hackathon (Everyone)
- [ ] Node.js installed
- [ ] Bun installed  
- [ ] Claude Code installed and authenticated
- [ ] Plugins installed (frontend-design, code-simplifier, superpowers)
- [ ] agent-browser installed and tested
- [ ] Context7 MCP configured
- [ ] Practiced Plan mode workflow with Context7
- [ ] Printed shortcut reference

### Before Hackathon (Team Lead)
- [ ] Repository created with monorepo structure
- [ ] .claude folder copied and configured (includes commands, skills)
- [ ] CLAUDE.md customized
- [ ] TASKS.md template ready
- [ ] Git worktrees created for each member
- [ ] Repository shared with team

### Before Hackathon (Experienced Devs)
- [ ] Docker installed and working
- [ ] Dockerfile.claude built
- [ ] Ralph plugin installed
- [ ] Tested parallel Claude sessions
- [ ] GitHub MCP configured (optional)
- [ ] Playwright MCP configured as backup (optional)
- [ ] Supabase/Stripe MCP configured (if using)

---

*Complete this checklist 24+ hours before the hackathon. Do not wait until the day of.*
