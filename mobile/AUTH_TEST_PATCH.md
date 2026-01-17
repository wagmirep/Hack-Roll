# Quick Auth Test (Without Backend)

If you want to test Supabase authentication before the backend is ready, you can temporarily disable the backend API call.

## Apply This Patch

Edit: `src/contexts/AuthContext.tsx`

Find the `fetchProfile` function (around line 46) and modify it like this:

```typescript
const fetchProfile = async () => {
  try {
    // TEMPORARY: Comment out backend call for testing
    // const data = await api.auth.getMe();
    // setProfile(data.profile);
    // setGroups(data.groups || []);
    
    // Mock profile for testing
    console.log('⚠️ Using mock profile - backend not connected');
    setProfile({
      id: user?.id || 'test-id',
      username: user?.email?.split('@')[0] || 'testuser',
      display_name: user?.email?.split('@')[0] || 'Test User',
      created_at: new Date().toISOString(),
    });
    setGroups([]);
  } catch (error) {
    console.error('Error fetching profile:', error);
  } finally {
    setLoading(false);
  }
};
```

## What This Does

- ✅ Supabase authentication will work
- ✅ You can sign up and sign in
- ✅ Tokens will be stored properly
- ❌ Backend API features won't work yet (recording, stats, etc.)

## Test Authentication Flow

1. Start the app: `npm run web`
2. Go to sign-up screen
3. Create an account with email/password
4. Check Supabase dashboard to see if user was created
5. Try signing in

## Remove This Patch Later

Once the backend is implemented and running, **revert this change** to use the real backend API.

---

**Purpose:** This lets you verify Supabase configuration is correct before tackling backend implementation.
