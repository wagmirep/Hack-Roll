# 🔍 Debugging 401 Unauthorized Errors

## What I Just Did

Added comprehensive debug logging to `/backend/auth.py` to help identify why authentication is failing.

## Next Steps

### 1. Restart the Backend

```bash
# Stop the current backend (Ctrl+C)
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### 2. Try Logging In from Mobile App

After the backend restarts:
1. Force refresh the mobile app (Cmd+Shift+R)
2. Try to log in
3. Watch the backend terminal

### 3. Check the Backend Logs

You should now see detailed logs like this:

**✅ Successful authentication:**
```
🔐 get_current_user_id called - credentials present: True
🎟️  Token received (length: 960)
🔍 Decoding JWT token (first 20 chars): eyJhbGciOiJFUzI1NiIs...
✅ JWT decoded successfully. User ID: 41c3726b-7bb6-4d19-bcfe-fea740e67696
✅ User authenticated: 41c3726b-7bb6-4d19-bcfe-fea740e67696
INFO: 127.0.0.1:xxxxx - "GET /auth/me HTTP/1.1" 200 OK
```

**❌ Various failure scenarios:**

**If no token is sent:**
```
ERROR: 403 Forbidden - Not authenticated
(HTTPBearer dependency fails)
```

**If token is invalid:**
```
🔐 get_current_user_id called - credentials present: True
🎟️  Token received (length: xxx)
🔍 Decoding JWT token (first 20 chars): xxxxx...
❌ JWT decode error: [error message]
INFO: 127.0.0.1:xxxxx - "GET /auth/me HTTP/1.1" 401 Unauthorized
```

**If token missing user ID:**
```
🔐 get_current_user_id called - credentials present: True
🎟️  Token received (length: xxx)
🔍 Decoding JWT token (first 20 chars): xxxxx...
✅ JWT decoded successfully. User ID: None
❌ Token missing user ID (sub claim)
INFO: 127.0.0.1:xxxxx - "GET /auth/me HTTP/1.1" 401 Unauthorized
```

## Possible Root Causes

### 1. **Token Not Being Sent** (Most Common)

**Symptoms:** You won't see the 🔐 logs at all

**Causes:**
- Mobile app's `supabase.auth.getSession()` is returning null
- Session cache is expired
- The interceptor is timing out

**Solution:** Check mobile app console for these messages:
- "Fetching new session token..."
- "Token added to request"
- "No session token available" ⚠️ (this is the problem)

### 2. **Wrong JWT Secret**

**Symptoms:** You'll see:
```
❌ JWT decode error: Signature verification failed
```

**Solution:** Double-check `SUPABASE_JWT_SECRET` in backend `.env` matches Supabase dashboard

### 3. **Token Format Issue**

**Symptoms:** You'll see the token received but decode fails

**Solution:** The token should be a JWT (starts with `eyJ...`)

### 4. **User Session Expired**

**Symptoms:** First request works (200), second fails (401)

**Solution:** Mobile app should refresh the token automatically (see `client.ts` line 78)

## Mobile App Side Checks

### Check Browser/Metro Console

Look for these messages:

**Good:**
```
Fetching new session token...
Token added to request
Fetching profile from API...
Profile fetched successfully: username
```

**Bad:**
```
No session token available  ⚠️
Error getting session in interceptor: [error]
getSession timeout  ⚠️
```

### Verify Supabase Session Exists

Add this to your mobile app login code:
```typescript
const { data: { session } } = await supabase.auth.getSession();
console.log('Session check:', {
  hasSession: !!session,
  hasAccessToken: !!session?.access_token,
  tokenLength: session?.access_token?.length,
  userId: session?.user?.id,
});
```

## Common Fixes

### Fix 1: Clear Session Cache

In mobile app, sign out and sign in again to get a fresh token.

### Fix 2: Increase Timeout

Edit `mobile/src/api/client.ts` line 39:
```typescript
setTimeout(() => reject(new Error('getSession timeout')), 10000)  // Increase to 10s
```

### Fix 3: Check Mobile .env

Verify `mobile/.env` has:
```bash
EXPO_PUBLIC_SUPABASE_URL=https://tamrgxhjyabdvtubseyu.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=[your-anon-key]
```

### Fix 4: Restart Everything

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 - Mobile
cd mobile
npm start --clear
```

## Report Back

After restarting the backend and trying to log in, **share the backend logs** so I can see exactly what's happening!

Look for the 🔐, 🎟️, 🔍, ✅, or ❌ emoji lines in the terminal.
