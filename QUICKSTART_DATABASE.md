# 🚀 Quick Start: Database Setup (10 Minutes)

**Goal:** Get your Supabase database fully configured and ready for the app.

---

## ⏱️ Timeline

- **5 min:** Get credentials from Supabase
- **2 min:** Apply database schema
- **3 min:** Update environment variables & verify

**Total:** ~10 minutes

---

## 🎯 Step 1: Get Credentials (5 min)

### Open Supabase API Settings
👉 https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/api

### Copy These 3 Things:

1. **Anon Key** (under "Project API keys" → "anon public")
   - Starts with `eyJhbGc...`
   - Save this for mobile app

2. **Service Role Key** (under "Project API keys" → "service_role secret")
   - Starts with `eyJhbGc...`
   - Save this for backend
   - ⚠️ Keep this secret!

3. **JWT Secret** (scroll down to "JWT Settings")
   - Long alphanumeric string
   - Save this for backend

📝 **Tip:** Open a text file and paste all three with labels.

---

## 🗄️ Step 2: Apply Database Schema (2 min)

### Method: Supabase SQL Editor

1. **Open SQL Editor:**
   👉 https://app.supabase.com/project/tamrgxhjyabdvtubseyu/sql

2. **Copy migration SQL:**
   ```bash
   cat /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend/migrations/001_initial_schema.sql | pbcopy
   ```
   
   Or manually open the file:
   ```
   /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend/migrations/001_initial_schema.sql
   ```

3. **Run migration:**
   - Click "New query" in SQL Editor
   - Paste the entire SQL
   - Click "Run" (or Cmd+Enter)
   - Wait ~10 seconds

4. **Verify success:**
   - Click "Table Editor" in left sidebar
   - You should see 10 new tables:
     - profiles
     - groups
     - group_members
     - sessions
     - session_speakers
     - speaker_word_counts
     - word_counts
     - user_stats_cache
     - target_words
     - audio_chunks

✅ **Done!** Your database schema is ready.

---

## 🔧 Step 3: Update Environment Variables (3 min)

### Update Mobile `.env`

```bash
# Open file:
nano /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile/.env
```

Replace line 3:
```env
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
```

With:
```env
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...YOUR_ACTUAL_ANON_KEY
```

### Update Backend `.env`

```bash
# Open file:
nano /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend/.env
```

Add these 3 lines at the end:
```env
SUPABASE_URL=https://tamrgxhjyabdvtubseyu.supabase.co
SUPABASE_JWT_SECRET=YOUR_JWT_SECRET_HERE
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...YOUR_SERVICE_ROLE_KEY
```

---

## ✅ Step 4: Verify Everything Works

### Test 1: Check Tables Exist

In Supabase SQL Editor, run:
```sql
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
```

**Expected:** Should return at least 10

### Test 2: Check Seeded Data

```sql
SELECT word, emoji FROM public.target_words LIMIT 5;
```

**Expected:** Should show Singlish words with emojis

### Test 3: Test Auto-Profile Creation

1. Go to: https://app.supabase.com/project/tamrgxhjyabdvtubseyu/auth/users
2. Click "Add user"
3. Enter: `test@example.com` / `testpassword123`
4. Go to: https://app.supabase.com/project/tamrgxhjyabdvtubseyu/editor (Table Editor → profiles)
5. Check if profile was auto-created for the test user

✅ If profile exists, trigger is working!

### Test 4: Mobile App Connection

```bash
# Restart mobile app
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
npm start
```

Open browser console (F12) and check for:
- ❌ Should NOT see: "Supabase credentials not found"
- ✅ Should see: App loads without credential errors

---

## 🎉 Success Checklist

After completing all steps:

- [ ] Got 3 credentials from Supabase dashboard
- [ ] Ran migration SQL successfully
- [ ] See 10 tables in Supabase Table Editor
- [ ] See 11 words in target_words table
- [ ] Updated mobile/.env with anon key
- [ ] Updated backend/.env with 3 new variables
- [ ] Test user created and profile auto-generated
- [ ] Mobile app connects without errors

---

## 🔥 What You Can Do Now

With the database set up, you can:

✅ **Sign up/login users** (auth works via Supabase)  
✅ **Create groups** (via backend API when implemented)  
✅ **Start recording sessions** (via backend API when implemented)  
✅ **Store and query word counts** (tables are ready)

---

## 🆘 Troubleshooting

### Migration failed?
- Re-run it! The SQL is idempotent (safe to run multiple times)
- Check you copied the ENTIRE SQL file

### Profile not auto-creating?
Run this in SQL Editor to check trigger:
```sql
SELECT tgname, tgenabled FROM pg_trigger WHERE tgname = 'on_auth_user_created';
```

### Mobile app still shows "Supabase credentials not found"?
- Verify you updated the right .env file (in mobile/ folder)
- Make sure you pasted the complete key
- Restart the app after changing .env

---

## 📚 Additional Resources

**Detailed guides:**
- `DATABASE_SETUP_GUIDE.md` - Full setup instructions with all methods
- `CREDENTIALS_NEEDED.md` - Complete credentials reference
- `docs/plans/2025-01-17-supabase-integration-design.md` - Full system design

**Your schema:**
- `backend/migrations/001_initial_schema.sql` - Complete database schema

---

## 🎯 Next Steps

1. ✅ Database is ready
2. ✅ Credentials are set
3. 🔄 **Next:** Implement backend API endpoints (see `backend/main.py`)
4. 🔄 **Then:** Test full flow from mobile → backend → database

**Ready to build!** 🚀

---

**Questions?** Check the detailed guides or the troubleshooting sections!
