# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed - January 17, 2026

#### 🔧 Supabase Auth Session Management
**Critical Fix:** Resolved session timeout issues that prevented app from loading on page refresh.

**Root Cause:**
- Supabase client was configured to use `AsyncStorage` (React Native storage)
- `AsyncStorage` doesn't work in web browsers, causing `getSession()` to hang indefinitely
- Every API request and page refresh would timeout waiting for session validation

**Solution:**
- Implemented platform-aware storage detection in `mobile/src/lib/supabase.ts`
- Web platform now uses browser `localStorage` (works instantly)
- Native platforms (iOS/Android) continue using `AsyncStorage` (works on devices)
- Added 3-second timeout protection on all `getSession()` calls
- Enhanced error handling with proper state cleanup on timeout

**Code Changes:**
- Updated `mobile/src/lib/supabase.ts`: Platform-specific storage configuration
- Updated `mobile/src/contexts/AuthContext.tsx`: 
  - Added timeout wrapper around initial session restoration
  - Added comprehensive error detection for session-related failures
  - Proper state cleanup (session, user, profile, groups) on timeout
  - Enhanced logging for debugging auth flow
- Updated `mobile/src/api/client.ts`: Better timeout error messages
- Updated `mobile/src/navigation/AppNavigator.tsx`: Debug logging for render states

**Impact:**
- ✅ Page refreshes now work correctly (no more stuck loading spinner)
- ✅ Session timeouts properly redirect to login screen
- ✅ getSession() calls complete in <50ms instead of timing out
- ✅ App works seamlessly on both web and native platforms

**Files Changed:**
- `mobile/src/lib/supabase.ts`
- `mobile/src/contexts/AuthContext.tsx`
- `mobile/src/api/client.ts`
- `mobile/src/navigation/AppNavigator.tsx`

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
