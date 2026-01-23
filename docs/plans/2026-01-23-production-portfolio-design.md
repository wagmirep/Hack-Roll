# Production Portfolio Demo — Design Document

**Date:** 2026-01-23
**Status:** Approved
**Goal:** Transform LahStats from hackathon MVP to deployable portfolio demo with AFK autonomous development capability.

---

## Overview

Three components:
1. **Telegram Notification Service** — Claude-to-human communication for AFK monitoring
2. **HuggingFace Model Hosting** — Replace Colab with always-available inference endpoints
3. **Production Deployment** — Deploy backend + mobile for recruiter access

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR PC                                   │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │  Claude Code    │───▶│  agent-browser  │                     │
│  │  (ralph loop)   │    │     CLI         │                     │
│  └────────┬────────┘    └─────────────────┘                     │
│           │                                                      │
│           │ curl POST                                            │
└───────────┼─────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│              CLOUDFLARE WORKER                                   │
│  notify.yourdomain.com                                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ POST /send     - Send notification, optional blocking wait  ││
│  │ POST /respond  - Telegram webhook receives your replies     ││
│  │ GET  /poll     - Claude polls for response                  ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────┐         ┌─────────────────────────────────┐
│    TELEGRAM       │         │   HUGGINGFACE INFERENCE         │
│   Group Chat      │         │                                 │
│  with Topics      │         │  MERaLiON-2-3B (transcription)  │
│                   │         │  pyannote (diarization)         │
│ 📁 LahStats       │         │                                 │
│ 📁 OtherProject   │         │  Scale-to-zero, T4 GPU          │
└───────────────────┘         └─────────────────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────┐         ┌─────────────────────────────────┐
│   YOUR PHONE      │         │   FASTAPI BACKEND               │
│                   │         │   (Railway/Fly.io)              │
│   Monitor &       │         │                                 │
│   Respond         │         │   Rate limiting enforced here   │
└───────────────────┘         └─────────────────────────────────┘
```

---

## Component 1: Telegram Notification Service

### Cloudflare Worker API

**Endpoints:**

```
POST /send
  Headers: Authorization: Bearer <shared-secret>
  Body: {
    "project": "lahstats",
    "type": "blocking" | "milestone" | "error" | "heartbeat",
    "message": "Need approval to refactor auth module",
    "buttons": ["Approve", "Skip", "Abort"],  // optional
    "request_id": "uuid-123"  // for correlating response
  }
  Response: { "message_id": "tg-456", "request_id": "uuid-123" }

POST /respond  (Telegram webhook)
  Body: Telegram update payload
  - Parses button click or text reply
  - Stores response keyed by request_id

GET /poll?request_id=uuid-123
  Headers: Authorization: Bearer <shared-secret>
  Response:
    - { "status": "waiting" } if no response yet
    - { "status": "responded", "response": "Approve" } when answered
```

### Storage

Cloudflare KV namespace:
- `request:{uuid}` → `{ status, response, timestamp, project, message_id }`
- `project:{name}` → `{ thread_id }` (Telegram thread mapping)
- Auto-expire after 24 hours

### Telegram Setup

- Create bot via @BotFather
- Create group with Topics enabled
- Add bot as admin
- Configure webhook to `POST /respond`

### Notification Types

| Type | Behavior | Example |
|------|----------|---------|
| `blocking` | Claude waits for response | "Should I refactor auth?" [Approve] [Skip] |
| `milestone` | Info only, no wait | "Phase 3 complete" |
| `error` | Info only, no wait | "Build failed: missing dep" |
| `heartbeat` | Info only, no wait | "Working on auth, 60% done" |

### Response Mechanism

- Inline buttons for quick actions (configured per message)
- Free-text reply for custom input
- Buttons and text both work
- Claude polls `/poll` every 5s with exponential backoff (max 30s)
- Wait indefinitely until response received

---

## Component 2: HuggingFace Model Hosting

### Endpoints to Create

| Model | HF Endpoint | Instance | Config |
|-------|-------------|----------|--------|
| MERaLiON-2-3B | `meralion-transcription` | Nvidia T4 | Scale-to-zero, 15min idle |
| pyannote/speaker-diarization-3.1 | `pyannote-diarization` | Nvidia T4 | Scale-to-zero, 15min idle |

### Rate Limiting

Enforced in FastAPI backend:

```python
DAILY_LIMIT = 5  # recordings per day
MAX_DURATION_SECONDS = 60  # per recording

# Check in POST /sessions/start
# Validate in POST /sessions/{id}/upload
# Store counts in Supabase: daily_usage table
```

**Error response:**
```json
{
  "error": "Daily limit reached (5/5)",
  "resets_at": "2026-01-24T00:00:00Z"
}
```

### Backend Changes

1. `backend/services/transcription.py` — Call HF endpoint instead of local model
2. `backend/services/diarization.py` — Call HF endpoint instead of local model
3. `backend/services/rate_limiter.py` — New service for rate limit checks
4. `backend/routers/sessions.py` — Add rate limit checks

### Cost Estimate

- Cold start: 30-60s (acceptable)
- Running cost: ~$0.60/hr on T4
- Typical usage: 5 recordings × 2 min processing = 10 min/day = ~$0.10/day max
- Idle days: $0

---

## Component 3: Production Deployment

### Backend (Railway or Fly.io)

Already have configs:
- `backend/railway.json`
- `backend/fly.toml`

Environment variables needed:
```
SUPABASE_URL=...
SUPABASE_JWT_SECRET=...
SUPABASE_SERVICE_ROLE_KEY=...
HUGGINGFACE_TOKEN=...
HF_TRANSCRIPTION_ENDPOINT=https://xxx.endpoints.huggingface.cloud
HF_DIARIZATION_ENDPOINT=https://yyy.endpoints.huggingface.cloud
```

### Mobile App

Options:
- Expo EAS Build for app stores (overkill for portfolio)
- Expo Web build deployed to Vercel/Netlify (simpler)
- Keep as Expo Go with QR code (simplest, but requires Expo app)

Recommendation: **Expo Web build** — recruiters can access via browser.

---

## Claude Integration

### Shell Script: `claude-notify`

```bash
#!/bin/bash
# Usage:
#   claude-notify milestone "Phase 3 complete"
#   claude-notify error "Build failed"
#   claude-notify heartbeat "Working on X, 60%"
#   RESPONSE=$(claude-notify blocking "Question?" "Yes" "No")

NOTIFY_URL="${CLAUDE_NOTIFY_URL:-https://notify.yourdomain.com}"
NOTIFY_SECRET="${CLAUDE_NOTIFY_SECRET}"
PROJECT="${CLAUDE_PROJECT:-unknown}"

TYPE="$1"
MESSAGE="$2"
shift 2
BUTTONS=("$@")

# Build JSON payload
# Send to /send endpoint
# If blocking, poll /poll until response
# Echo response to stdout
```

### Environment Variables

Set before starting Claude Code:
```bash
export CLAUDE_PROJECT="lahstats"
export CLAUDE_NOTIFY_URL="https://notify.yourdomain.com"
export CLAUDE_NOTIFY_SECRET="your-shared-secret"
```

### Heartbeat Automation

Wrapper script sends heartbeat every 30 minutes while loop is running.

---

## Implementation Workstreams

### Workstream A: Telegram Notification Service

1. Create Cloudflare Worker project (`wrangler init`)
2. Create KV namespace
3. Implement `/send` endpoint
4. Implement `/respond` endpoint (Telegram webhook)
5. Implement `/poll` endpoint
6. Create Telegram bot and group
7. Configure webhook
8. Create `claude-notify` shell script
9. Test end-to-end

### Workstream B: HuggingFace Model Hosting

1. Create HF Inference Endpoint for MERaLiON-2-3B
2. Create HF Inference Endpoint for pyannote
3. Test endpoints manually
4. Update `transcription.py` to call HF endpoint
5. Update `diarization.py` to call HF endpoint
6. Create `rate_limiter.py` service
7. Add rate limit checks to session endpoints
8. Test with cold start scenario

### Workstream C: Production Deployment

1. Deploy backend to Railway/Fly.io
2. Configure environment variables
3. Set up custom domain
4. Build Expo web version
5. Deploy to Vercel/Netlify
6. End-to-end production test

---

## Suggested Execution Order

1. **Workstream A first** — Need notifications before AFK development
2. **Workstream B + C in parallel** — Can run simultaneously once monitoring works

---

## Success Criteria

- [ ] Can send Telegram notification from CLI
- [ ] Can receive response from Telegram and unblock Claude
- [ ] HF endpoints respond (with cold start)
- [ ] Rate limiting works (5/day, 60s max)
- [ ] Backend deployed and accessible
- [ ] Mobile/web app accessible to recruiters
- [ ] Full demo flow works end-to-end

---

*Approved: 2026-01-23*
