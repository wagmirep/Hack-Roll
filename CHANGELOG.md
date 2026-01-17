# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added - January 17, 2026

#### 🎯 Three-Way Speaker Claiming System
**Major Feature:** Enhanced speaker claiming to support three modes instead of just self-claiming.

**New Claiming Modes:**
1. **Self Claim:** Claim speaker as yourself (existing behavior)
2. **User Tagging:** Tag speaker as another registered user in your group
3. **Guest Tagging:** Tag speaker as a guest participant (no account needed)

**Database Changes:**
- Created migration `002_add_claim_types.sql`
- Added columns to `session_speakers` table:
  - `claim_type` (VARCHAR): 'self', 'user', or 'guest'
  - `attributed_to_user_id` (UUID): User who gets the stats
  - `guest_name` (VARCHAR): Display name for guests
- Added index on `attributed_to_user_id`
- Created view `session_results_with_guests`

**Backend API Changes:**
- Updated `POST /sessions/{session_id}/claim` endpoint:
  - Now accepts `claim_type`, `attributed_to_user_id`, and `guest_name` parameters
  - Validates claim type and required fields
  - Ensures tagged users are group members
  - Only creates `word_counts` entries for 'self' and 'user' types
- Updated `GET /sessions/{session_id}/results` endpoint:
  - Now returns both registered users and guests
  - Guests marked with `is_guest: true` flag
  - Guest word counts fetched from `speaker_word_counts` table
- Added `GET /auth/search` endpoint:
  - Search users by username or display name
  - Optional group filtering
  - Paginated results with configurable limit

**Code Changes:**
- Updated `models.py`: Enhanced `SessionSpeaker` model with new fields
- Updated `schemas.py`: New request/response schemas for claiming
- Updated `routers/sessions.py`: Enhanced claim and results endpoints
- Updated `routers/auth.py`: Added user search endpoint

**Documentation:**
- Created `CLAIMING_FEATURE_GUIDE.md` - Comprehensive feature guide
- Updated `TASKS.md` - Detailed feature documentation with examples
- Added implementation checklist and testing scenarios
- Documented API changes and database schema

**Benefits:**
- ✅ Inclusive: Friends without accounts can participate
- ✅ Flexible: Anyone can tag speakers for others
- ✅ Accurate: Stats attributed to correct users
- ✅ Privacy: Guest stats don't pollute user profiles

**Status:**
- Backend: ✅ Complete and tested
- Mobile: ⏳ Needs UI implementation
- Database: ⏳ Migration ready to deploy

**References:**
- Feature Guide: `CLAIMING_FEATURE_GUIDE.md`
- Migration: `backend/migrations/002_add_claim_types.sql`
- Tasks: `TASKS.md` (see "THREE-WAY CLAIMING SYSTEM" section)

---

## Previous Changes

### Database Schema - January 17, 2026
- ✅ Created initial Supabase schema with 10 tables
- ✅ Configured RLS policies
- ✅ Set up auto-profile creation trigger
- ✅ Seeded target words (11 Singlish words)

### Mobile App - January 17, 2026
- ✅ Complete authentication flow
- ✅ Recording screen with chunk uploads
- ✅ Processing screen with real-time polling
- ✅ Claiming screen with audio playback
- ✅ Results screen with leaderboards
- ✅ Stats screen with period filters
- ✅ All custom hooks and components
- ✅ Signup success screen with auto-redirect

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/) format.*
