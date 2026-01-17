# ✅ Session Timeout & 401 Error Handling - Fixed

## What Was Happening

**Before:**
1. User's session would timeout after 3 seconds trying to fetch from Supabase
2. Request would proceed WITHOUT an auth token
3. Backend would return `401 Unauthorized`
4. User would be stuck in a broken state (logged in UI, but can't make requests)
5. User would see errors but couldn't recover without manually refreshing

**Error Message:**
```
Error getting session in interceptor: Error: getSession timeout
GET http://localhost:8000/auth/me 401 (Unauthorized)
```

## What I Changed

Updated `/mobile/src/api/client.ts` to handle session failures gracefully:

### 1. Request Interceptor - Auto Sign Out on No Session

**Before:** If no session token, continue request without auth (causes 401)

**After:** If no session token or timeout, **sign out immediately**

```typescript
if (session?.access_token) {
  // Add token to request
} else {
  console.warn('No session token available - signing out');
  await supabase.auth.signOut();
  throw new Error('No valid session - please log in again');
}
```

**Result:** User is automatically redirected to login screen

### 2. Response Interceptor - Better 401 Handling

**Before:** Try to refresh, but if it fails, just return error

**After:** 
1. Try to refresh the session ONCE (prevent infinite loops)
2. If refresh succeeds → retry the request with new token ✅
3. If refresh fails → **sign out and redirect to login** ✅

```typescript
if (session?.access_token) {
  // Retry with new token
} else {
  console.log('Signing out user - please log in again');
  await supabase.auth.signOut();
  return Promise.reject(new Error('Session expired - please log in again'));
}
```

**Result:** No more stuck in broken state!

## User Experience Flow

### Scenario 1: Session Timeout Before Request

1. User tries to make API request
2. `getSession()` times out after 3 seconds
3. **App automatically signs out**
4. User is redirected to login screen
5. User sees friendly message: "Session expired - please log in again"

### Scenario 2: Session Expired (401 Response)

1. User makes request with expired token
2. Backend returns 401 Unauthorized
3. App tries to refresh the session
4. **If refresh succeeds:** Request is retried automatically (user doesn't notice!)
5. **If refresh fails:** App signs out and redirects to login

### Scenario 3: Invalid Token

1. User makes request with invalid/corrupted token
2. Backend returns 401 Unauthorized
3. App tries to refresh
4. Refresh fails (token is bad)
5. **App signs out and redirects to login**

## Benefits

✅ **No more broken states** - User is never stuck with errors  
✅ **Clear user feedback** - Console shows what's happening  
✅ **Automatic recovery** - If token can be refreshed, it happens silently  
✅ **Prevents infinite loops** - Only retry once with `_retry` flag  
✅ **Better UX** - User is guided back to login when needed  

## How It Works

The fix leverages the existing `AuthContext` listener:

```typescript
// This is already in AuthContext.tsx
supabase.auth.onAuthStateChange(async (_event, session) => {
  if (session) {
    // User logged in - fetch profile
  } else {
    // User logged out - clear state and show login screen
    setProfile(null);
    setGroups([]);
  }
});
```

When `supabase.auth.signOut()` is called from the API client:
1. It triggers the `onAuthStateChange` event with `session = null`
2. AuthContext clears user data
3. Navigation automatically shows login screen
4. User can log in again with fresh session

## Testing

### Test 1: Force Session Timeout

1. Start the app and log in
2. Wait for session to expire (or manually delete from AsyncStorage)
3. Try to navigate to a screen that requires API calls
4. **Expected:** Auto-redirected to login screen

### Test 2: Simulate 401 Error

1. Log in successfully
2. Change the JWT secret in backend `.env` (to make tokens invalid)
3. Try to make an API call
4. **Expected:** Auto-redirected to login screen

### Test 3: Network Issues

1. Log in successfully
2. Disconnect from network or stop backend
3. Try to make an API call
4. **Expected:** See network error (not auth error) OR auto-redirect after timeout

## Console Messages

You'll now see helpful messages in the browser/Metro console:

**Good flow:**
```
Fetching new session token...
Token added to request
✅ Request successful
```

**Session refresh (automatic):**
```
Received 401 Unauthorized - attempting token refresh...
Token refreshed successfully - retrying request
✅ Request successful
```

**Session expired (sign out):**
```
Received 401 Unauthorized - attempting token refresh...
Session refresh failed: [error]
Signing out user - please log in again
Auth state changed: SIGNED_OUT
```

## Notes

- The 3-second timeout in `getSession()` is intentional to prevent hanging
- You can increase it if needed (edit line 39 in `client.ts`)
- The `_retry` flag prevents infinite loops if auth keeps failing
- The session cache reduces API calls by reusing valid tokens

## Next Steps

After this fix:
1. Restart your mobile app: `npm start --clear`
2. Try logging in
3. The session timeout errors should now gracefully redirect to login
4. Check console for the new helpful messages

---

**Summary:** Instead of leaving users in a broken state with 401 errors, the app now automatically signs them out and redirects to login, providing a much cleaner user experience! 🎉
