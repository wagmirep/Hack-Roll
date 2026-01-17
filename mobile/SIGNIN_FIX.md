# 🔧 Fix Sign-In Issue

## ✅ Assets Fixed
Created placeholder images for icon, splash, and favicon.

## ⚠️ CRITICAL: Supabase Anon Key Required

**Your sign-in is not working because the Supabase anon key is still set to a placeholder.**

### Step 1: Get Your Supabase Anon Key

1. **Open Supabase Dashboard**
   - Go to: https://app.supabase.com/project/tamrgxhjyabdvtubseyu

2. **Navigate to API Settings**
   - Click on "Project Settings" (gear icon in left sidebar)
   - Click on "API" section

3. **Copy the Anon Key**
   - Find the section labeled "Project API keys"
   - Copy the `anon` `public` key (NOT the service_role key)
   - It should look like: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (very long string)

### Step 2: Update Your .env File

1. **Open the file:**
   ```
   /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile/.env
   ```

2. **Replace line 3:**
   ```env
   EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
   ```
   
   With:
   ```env
   EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.YOUR_ACTUAL_KEY_HERE
   ```

### Step 3: Restart the Dev Server

After updating the .env file:

```bash
# Stop the current server (Ctrl+C in the terminal)
# Then restart:
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
npm start
```

Or if running on web:
```bash
npm run web
```

## Additional: Check Backend is Running

The mobile app also needs the backend API. Make sure it's running:

```bash
# In a new terminal:
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend
source venv/bin/activate
uvicorn main:app --reload
```

Backend should be running on: `http://localhost:8000`

## Test Sign-In

Once you've updated the Supabase key and restarted:

1. **Open the app** (web, simulator, or device)
2. **Try to sign in** with an existing account
3. **Or sign up** for a new account

### Expected Behavior

✅ **Sign Up:**
- Should create account in Supabase
- Should automatically sign you in
- May require email verification (check Supabase settings)

✅ **Sign In:**
- Should authenticate with Supabase
- Should fetch your profile from backend API
- Should navigate to main app screen

### Common Errors

**"Invalid API key"**
- Double-check you copied the correct anon key
- Make sure there are no extra spaces

**"Network request failed"**
- Check backend is running on port 8000
- Check `EXPO_PUBLIC_API_URL` is set correctly

**"Email not confirmed"**
- Check email verification settings in Supabase dashboard
- Go to: Authentication → Settings → Email Auth
- You can disable email confirmation for development

## Quick Verification

Run this in your terminal to check if the key is set:

```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
cat .env | grep SUPABASE_ANON_KEY
```

It should NOT show `your-anon-key-here` - it should show a long JWT token.

---

**Need Help?**
- Check the terminal logs for specific error messages
- Check browser console (F12) for web errors
- Check Supabase Dashboard → Authentication → Users to see if accounts are being created
