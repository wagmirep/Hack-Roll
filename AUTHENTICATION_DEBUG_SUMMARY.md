# 🔐 Authentication Debug Summary

**Date:** 2026-01-17  
**Status:** Issues Identified - Action Required

---

## 🚨 Problems Found

### 1. **CRITICAL: Backend `.env` File Missing**

**Location:** `/Hack-Roll/backend/.env`

**Error in logs:**
```
ValueError: SUPABASE_URL environment variable is required
```

**Impact:** Backend crashes on startup, cannot authenticate any requests

**Fix:** Create the `.env` file with Supabase credentials

👉 **See:** `backend/ENV_SETUP_GUIDE.md` for step-by-step instructions

---

### 2. **Backend Configuration Issue**

**File:** `backend/config.py` (lines 77-80)

The backend requires these environment variables:
- `SUPABASE_URL` ✅ (Known: `https://tamrgxhjyabdvtubseyu.supabase.co`)
- `SUPABASE_JWT_SECRET` ❌ (Missing - need from Supabase dashboard)
- `SUPABASE_SERVICE_ROLE_KEY` ❌ (Missing - need from Supabase dashboard)
- `DATABASE_URL` ⚠️ (Partially known, need complete password)

---

### 3. **Authentication Flow Breakdown**

From the terminal logs, here's what's happening:

1. ✅ **Mobile app** sends request to `/auth/me`
2. ❌ **Backend** returns `401 Unauthorized` (line 404 in terminal)
3. 💥 **Backend** then crashes when reloading due to missing `.env`

**The 401 error happens because:**
- Either the JWT token from mobile is invalid
- Or the backend can't decode it due to wrong `SUPABASE_JWT_SECRET`
- Or the user doesn't exist in the database

---

## 🛠️ How to Fix (Step by Step)

### Fix #1: Create Backend `.env` File (REQUIRED)

1. Open Supabase dashboard: https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/api

2. Get these values:
   - JWT Secret (from "JWT Settings")
   - Service Role Key (from "Project API keys")
   - Database Password (from Settings → Database)

3. Create `/Hack-Roll/backend/.env` with:

```bash
SUPABASE_URL=https://tamrgxhjyabdvtubseyu.supabase.co
SUPABASE_JWT_SECRET=<your-jwt-secret>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
DATABASE_URL=postgresql://postgres.tamrgxhjyabdvtubseyu:<your-db-password>@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

4. Restart backend:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

---

### Fix #2: Verify Mobile `.env` File (RECOMMENDED)

The mobile app also needs proper Supabase credentials.

**File:** `/Hack-Roll/mobile/.env` (may need to be created)

**Required:**
```bash
EXPO_PUBLIC_SUPABASE_URL=https://tamrgxhjyabdvtubseyu.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key-from-supabase>
EXPO_PUBLIC_API_URL=http://localhost:8000
```

**Important:** Use the **ANON** key for mobile, not the service role key!

---

### Fix #3: Check User Exists in Database

After the backend starts, verify users can authenticate:

1. Test backend is running:
```bash
curl http://localhost:8000/docs
```

2. Check if your user profile exists:
```bash
# You'll need to look in Supabase dashboard → Authentication → Users
# Each authenticated user should have a corresponding profile in the database
```

---

## 🧪 Testing After Fixes

### Step 1: Start Backend

```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
✅ Configuration loaded successfully
   Supabase URL: https://tamrgxhjyabdvtubseyu.supabase.co
   Database URL: postgresql://postgres.tamrgxhjyabdvtubseyu:***...
✅ Database connection successful
✅ Application startup complete
```

### Step 2: Test Authentication

Open another terminal:

```bash
# Test the health endpoint
curl http://localhost:8000/

# Should return something like {"status": "ok"} or redirect to /docs
```

### Step 3: Try Login from Mobile

1. Open the mobile app
2. Try to log in
3. Watch the backend terminal for logs

**Good logs:**
```
🔐 get_current_user_id called - credentials present: True
✅ JWT decoded successfully. User ID: xxx
✅ User authenticated: xxx
INFO: 127.0.0.1:xxx - "GET /auth/me HTTP/1.1" 200 OK
```

**Bad logs:**
```
INFO: 127.0.0.1:xxx - "GET /auth/me HTTP/1.1" 401 Unauthorized
```

---

## 🔍 Debug Checklist

After creating the `.env` file, verify:

- [ ] Backend starts without errors
- [ ] You see "✅ Configuration loaded successfully"
- [ ] You see "✅ Database connection successful"
- [ ] Backend responds to http://localhost:8000/docs
- [ ] Mobile app can reach http://localhost:8000/auth/me (after login)
- [ ] You see successful 200 responses in backend logs

---

## 📚 Additional Resources

- **ENV_SETUP_GUIDE.md** - Detailed `.env` file setup
- **mobile/SIGNIN_FIX.md** - Mobile authentication setup
- **mobile/SIGNIN_STATUS.md** - Previous authentication issues
- **mobile/AUTH_TEST_PATCH.md** - Test auth without backend (temporary workaround)

---

## 🆘 Still Not Working?

### Check These Common Issues:

1. **"Token missing user ID"**
   - The JWT token doesn't have a `sub` claim
   - Check mobile app is getting tokens from Supabase correctly

2. **"User profile not found"**
   - The user exists in Supabase Auth but not in your database
   - Run the signup flow again to create the profile

3. **"Invalid authentication credentials"**
   - The `SUPABASE_JWT_SECRET` doesn't match your project
   - Double-check you copied the correct secret from Supabase dashboard

4. **Backend keeps crashing**
   - Check `.env` file has no typos
   - Make sure there are no extra spaces or quotes in the values
   - Try: `python -c "from config import settings; print(settings.SUPABASE_URL)"`

---

## 🎯 Quick Fix for Testing

If you want to test the mobile app without fixing the backend immediately:

See: **mobile/AUTH_TEST_PATCH.md** for a temporary workaround that lets you test Supabase authentication without the backend API.

---

**Next Action:** Create the backend `.env` file using the guide in `ENV_SETUP_GUIDE.md`
