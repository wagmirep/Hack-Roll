# TASKS.md — Hackathon Task Tracker

**Keep this file updated. It's your source of truth.**

---

## Current Sprint

### 🔴 Blocked

*Tasks waiting on something*

| Task | Assigned | Blocked By |
|------|----------|------------|
| Mobile E2E Testing | Unassigned | Backend deployment + Supabase setup |

### 🟡 In Progress

*Tasks actively being worked on*

| Task | Assigned | Branch | Started |
|------|----------|--------|---------|
| Backend API Implementation | Unassigned | — | — |
| Frontend Auth Debugging | Winston | — | Jan 17, 2026 |

### 🟢 Ready for PR

*Completed, needs review*

| Task | Assigned | PR Link |
|------|----------|---------|
| Mobile App Frontend (Complete) | Winston | N/A (All files created) |

### ✅ Done

*Merged to main*

| Task | Completed By | Merged |
|------|--------------|--------|
| Mobile App Infrastructure | Winston | Jan 17, 2026 |
| Mobile Auth Screens | Winston | Jan 17, 2026 |
| Mobile Recording Flow | Winston | Jan 17, 2026 |
| Mobile Claiming Flow | Winston | Jan 17, 2026 |
| Mobile Stats Screen | Winston | Jan 17, 2026 |
| Mobile Components & Hooks | Winston | Jan 17, 2026 |
| Supabase Database Schema | Winston | Jan 17, 2026 |
| Database Migration Files | Winston | Jan 17, 2026 |
| Mobile Environment Setup | Winston | Jan 17, 2026 |

---

## Task Backlog

### Priority 1 — Must Have (MVP)

- [x] **Supabase Project Setup** ✅ COMPLETED
  - Description: Create and configure Supabase project with database schema
  - Success criteria:
    - [x] Supabase project created
    - [x] All database tables created (profiles, groups, sessions, etc.)
    - [x] RLS policies configured
    - [x] Database trigger for auto-profile creation set up
    - [x] Target words table seeded (11 Singlish words)
  - Assigned: Winston
  - Completed: Jan 17, 2026
  - Notes: Migration file: `backend/migrations/001_initial_schema.sql`
  - Documentation: `DATABASE_SETUP_GUIDE.md`, `QUICKSTART_DATABASE.md`

- [ ] **Backend FastAPI Implementation**
  - Description: Implement all backend endpoints with JWT auth
  - Success criteria:
    - [ ] JWT validation middleware working
    - [ ] Auth endpoints (/auth/me, /auth/profile)
    - [ ] Group endpoints (create, join, members)
    - [ ] Session endpoints (create, upload, end, status)
    - [ ] Speaker endpoints (get speakers, claim)
    - [ ] Stats endpoints (group stats, user stats)
    - [ ] S3/Supabase Storage integration for audio files
  - Assigned: Unassigned
  - Notes: Mobile app expects these exact endpoints - see mobile/src/api/client.ts

- [ ] **Audio Processing Pipeline**
  - Description: Implement ML processing for diarization & transcription
  - Success criteria:
    - [ ] Audio chunk concatenation working
    - [ ] Pyannote diarization integrated
    - [ ] MERaLiON transcription integrated
    - [ ] Word counting for target words
    - [ ] Sample clip generation (5s per speaker)
    - [ ] Background job queue working
    - [ ] Progress updates during processing
  - Assigned: Unassigned
  - Notes: Critical path - this is the core ML functionality

- [x] **Mobile Environment Configuration** ✅ COMPLETED
  - Description: Configure mobile .env with real credentials
  - Success criteria:
    - [x] EXPO_PUBLIC_SUPABASE_URL set
    - [x] EXPO_PUBLIC_SUPABASE_ANON_KEY set
    - [x] EXPO_PUBLIC_API_URL set (localhost:8000)
    - [x] Dependencies installed (TypeScript, React, web deps)
    - [x] App starts without errors (running on port 8081)
    - [x] Asset files created (icon, splash, favicon)
  - Assigned: Winston
  - Completed: Jan 17, 2026
  - Notes: App successfully starts, auth debugging in progress

- [ ] **End-to-End Testing**
  - Description: Test complete flow from signup to results
  - Success criteria:
    - [ ] User can sign up and login
    - [ ] User can create/join group
    - [ ] User can start recording
    - [ ] Chunks upload successfully
    - [ ] Processing completes without errors
    - [ ] Audio samples are playable
    - [ ] User can claim speaker
    - [ ] Results display correctly
    - [ ] Stats show accurate data
  - Assigned: Unassigned
  - Notes: Must test on physical device (simulator mic doesn't work)

- [ ] **Group Management UI**
  - Description: Add screens for creating and joining groups
  - Success criteria:
    - [ ] Create group screen with name input
    - [ ] Join group screen with invite code input
    - [ ] Group selection in recording screen
    - [ ] Display group list in home/profile
    - [ ] Show invite code for sharing
  - Assigned: Unassigned
  - Notes: Currently mobile uses first group in list - needs proper UI

### Priority 2 — Should Have

- [ ] **Error Handling & Loading States**
  - Description: Improve UX with better error messages and loading indicators
  - Success criteria:
    - [ ] Loading skeletons on all screens
    - [ ] User-friendly error messages
    - [ ] Retry mechanisms for failed requests
    - [ ] Offline detection and messaging
    - [ ] Network error recovery
  - Assigned: Unassigned
  - Notes: Current implementation has basic error handling

- [ ] **Backend Deployment**
  - Description: Deploy FastAPI backend to production
  - Success criteria:
    - [ ] Backend deployed to cloud (Railway/Render/DigitalOcean)
    - [ ] Environment variables configured
    - [ ] Database connected
    - [ ] HTTPS enabled
    - [ ] Health check endpoint working
  - Assigned: Unassigned
  - Notes: Update mobile EXPO_PUBLIC_API_URL after deployment

- [ ] **Push Notifications**
  - Description: Notify users when processing completes
  - Success criteria:
    - [ ] Expo push token registration
    - [ ] Backend sends notification on processing complete
    - [ ] Notification opens app to claiming screen
  - Assigned: Unassigned
  - Notes: Nice to have for better UX

- [ ] **Profile Management**
  - Description: Allow users to edit their profile
  - Success criteria:
    - [ ] Profile screen showing user info
    - [ ] Edit display name
    - [ ] Edit avatar (optional)
    - [ ] Logout button
    - [ ] Delete account option
  - Assigned: Unassigned
  - Notes: Basic profile exists, needs UI

- [ ] **Pull-to-Refresh**
  - Description: Add pull-to-refresh on stats and results screens
  - Success criteria:
    - [ ] Pull-to-refresh on StatsScreen
    - [ ] Pull-to-refresh on ResultsScreen
    - [ ] Smooth animation
    - [ ] Proper loading state
  - Assigned: Unassigned
  - Notes: Standard mobile UX pattern

### Priority 3 — Nice to Have

- [ ] **Wrapped Screen Implementation**
  - Description: Build Spotify-style yearly recap
  - Success criteria:
    - [ ] Backend endpoint for wrapped data
    - [ ] Beautiful animated screens
    - [ ] Share to social media
    - [ ] Top words visualization
    - [ ] Personality/badges based on usage
  - Assigned: Unassigned
  - Notes: Currently just placeholder screen

- [ ] **Data Export**
  - Description: Allow users to export their data
  - Success criteria:
    - [ ] Export to JSON
    - [ ] Export to CSV
    - [ ] Email export option
    - [ ] Share functionality
  - Assigned: Unassigned
  - Notes: For data transparency

- [ ] **Animations & Polish**
  - Description: Add smooth animations and haptic feedback
  - Success criteria:
    - [ ] Screen transitions animated
    - [ ] Button press haptics
    - [ ] Success celebrations (confetti, etc.)
    - [ ] Progress bar animations
    - [ ] Micro-interactions
  - Assigned: Unassigned
  - Notes: Make it feel premium

- [ ] **Group Settings**
  - Description: Advanced group management features
  - Success criteria:
    - [ ] Rename group
    - [ ] Leave group
    - [ ] Remove members (admin only)
    - [ ] Transfer admin role
    - [ ] Delete group
  - Assigned: Unassigned
  - Notes: Currently groups are permanent

- [ ] **Analytics Integration**
  - Description: Add analytics to track usage
  - Success criteria:
    - [ ] Firebase Analytics or similar
    - [ ] Track key user actions
    - [ ] Monitor errors
    - [ ] Track retention
  - Assigned: Unassigned
  - Notes: For product insights

- [ ] **App Store Preparation**
  - Description: Prepare for app store submission
  - Success criteria:
    - [ ] App icons created
    - [ ] Splash screen designed
    - [ ] Screenshots prepared
    - [ ] Privacy policy written
    - [ ] Terms of service written
    - [ ] App store listing copy
  - Assigned: Unassigned
  - Notes: For public launch 

---

## Task Template

Copy this when adding new tasks:

```markdown
- [ ] **Task Name**
  - Description: [What needs to be built]
  - Success criteria:
    - [ ] [Specific, verifiable requirement]
    - [ ] [Another requirement]
    - [ ] Tests pass
    - [ ] No TypeScript errors
  - Assigned: [Name or Unassigned]
  - Notes: [Dependencies, context, links]
```

---

## How to Use This File

### Claiming a Task

1. Find an unassigned task in the backlog
2. Add your name to "Assigned"
3. Move it to "In Progress" section
4. Create your feature branch
5. Start working

### Completing a Task

1. Verify all success criteria are checked
2. Run `bun run typecheck && bun run lint && bun run test`
3. Create PR
4. Move task to "Ready for PR" section
5. Link the PR

### After PR Merged

1. Move task to "Done" section
2. Add completion date
3. Celebrate 🎉

---

## Notes

*Use this section for team-wide notes, decisions, or pivots during the hackathon*

- [2026-01-17 22:00] **Mobile App Frontend Complete** - All screens, components, hooks, and navigation implemented. 30+ files created. Ready for backend integration.
- [2026-01-17 22:00] **Architecture Decision** - Using Supabase for auth + PostgreSQL, FastAPI for business logic, direct SQLAlchemy for database queries. Hybrid approach for best of both worlds.
- [2026-01-17 22:00] **Mobile Stack Finalized** - React Native (Expo), TypeScript, Supabase Auth, Axios for API, Expo AV for audio
- [2026-01-17 22:00] **Critical Path** - Backend API implementation + Supabase setup are now the blockers for E2E testing
- [2026-01-17 23:30] **Database Schema Complete** ✅ - Full Supabase schema applied: 10 tables, RLS policies, triggers, views, seeded with 11 Singlish words. Migration file created.
- [2026-01-17 23:30] **Environment Setup Complete** ✅ - Mobile .env configured with Supabase credentials, all dependencies installed, dev server running on port 8081.
- [2026-01-17 23:30] **Documentation Created** - DATABASE_SETUP_GUIDE.md, QUICKSTART_DATABASE.md, CREDENTIALS_NEEDED.md, DATABASE_SUMMARY.md (26KB of comprehensive guides)
- [2026-01-17 23:35] **Current Status** - Mobile app running, database schema deployed, debugging 401 auth errors (likely email confirmation setting)

### 📱 Mobile App Status

**✅ COMPLETE:**
- Full authentication flow (login/signup with Supabase)
- Recording screen with chunk uploads
- Processing screen with real-time status polling
- Claiming screen with audio playback
- Results screen with beautiful leaderboards
- Stats screen with period filters
- All custom hooks (useRecording, useSessionStatus, useAudioPlayback)
- All reusable components (SpeakerCard, AudioPlayer, ProgressBar, WordBadge)
- API client with JWT interceptors
- Navigation structure
- TypeScript types
- Documentation (README, SETUP, QUICKSTART, IMPLEMENTATION_SUMMARY)

**📋 TODO:**
- ✅ ~~Configure .env with real Supabase credentials~~ DONE
- Debug 401 auth errors (check email confirmation settings)
- Add group creation/join UI
- Test on physical device with real backend
- Handle edge cases and improve error messages
- Add loading skeletons

### 🔧 Backend Status

**✅ COMPLETE:**
- ✅ Supabase project configured (tamrgxhjyabdvtubseyu.supabase.co)
- ✅ Database schema deployed (10 tables, RLS policies, triggers)
- ✅ Migration file created (`backend/migrations/001_initial_schema.sql`)
- ✅ Target words seeded (11 Singlish words with emojis)
- ✅ Auto-profile creation trigger working

**❌ TODO:**
- Implement all FastAPI endpoints
- JWT validation middleware
- Integrate ML models (pyannote + MERaLiON)
- Set up audio storage (S3/Supabase Storage)
- Implement background job processing
- Deploy to production

### 📚 Key Documentation

**Mobile:**
- Mobile architecture: `mobile/IMPLEMENTATION_SUMMARY.md`
- Setup guide: `mobile/SETUP.md`
- Quick start: `mobile/QUICKSTART.md`
- API endpoints: `mobile/src/api/client.ts`

**Database:**
- Database setup: `DATABASE_SETUP_GUIDE.md` ✨ NEW
- Quick start: `QUICKSTART_DATABASE.md` ✨ NEW
- Credentials guide: `CREDENTIALS_NEEDED.md` ✨ NEW
- Overview: `DATABASE_SUMMARY.md` ✨ NEW
- Migration SQL: `backend/migrations/001_initial_schema.sql` ✨ NEW

**Design:**
- Full system design: `docs/plans/2025-01-17-supabase-integration-design.md`

---

*Last updated: January 17, 2026 - 15:05 SGT*
