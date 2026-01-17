# 📊 Database Setup Guide - Supabase Schema Migration

**Status:** Schema ready to deploy  
**Migration File:** `backend/migrations/001_initial_schema.sql`  
**Estimated Time:** 10-15 minutes

---

## 🎯 What This Does

This migration creates the complete database schema for LahStats:

**Tables Created:**
- ✅ `profiles` - User profiles (extends auth.users)
- ✅ `groups` - Friend groups
- ✅ `group_members` - Group membership
- ✅ `sessions` - Recording sessions
- ✅ `session_speakers` - AI-detected speakers
- ✅ `speaker_word_counts` - Pre-claiming word counts
- ✅ `word_counts` - Final attributed word counts
- ✅ `user_stats_cache` - Pre-computed stats
- ✅ `target_words` - Singlish words to track
- ✅ `audio_chunks` - Uploaded audio segments

**Additional Features:**
- ✅ Row Level Security (RLS) policies on all tables
- ✅ Database trigger to auto-create profiles on signup
- ✅ Indexes for performance
- ✅ Views for common queries
- ✅ Seeded with initial Singlish words

---

## 🔑 Required Credentials

You'll need these from your Supabase dashboard:

### Method 1: Supabase SQL Editor (Recommended - Easiest)
**Required:**
- Supabase account login

**Steps:**
1. Go to: https://app.supabase.com
2. Select your project: `tamrgxhjyabdvtubseyu`
3. No additional credentials needed!

### Method 2: Direct Database Connection (Advanced)
**Required:**
- Database password

**Where to find:**
- Supabase Dashboard → Project Settings → Database
- Look for "Connection string" or "Database password"

---

## 📋 Apply Schema to Supabase

### ✅ Method 1: Using Supabase SQL Editor (RECOMMENDED)

This is the easiest and safest method.

#### Step 1: Open SQL Editor

1. Go to https://app.supabase.com
2. Click on your project: **tamrgxhjyabdvtubseyu**
3. In the left sidebar, click **"SQL Editor"**

#### Step 2: Copy Migration SQL

```bash
# Copy the migration file content
cat /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend/migrations/001_initial_schema.sql | pbcopy
```

Or open the file manually:
```
/Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend/migrations/001_initial_schema.sql
```

#### Step 3: Run Migration

1. In SQL Editor, click **"New query"**
2. Paste the entire migration SQL
3. Click **"Run"** button (or press Cmd+Enter)
4. Wait for completion (should take 5-10 seconds)

#### Step 4: Verify Success

You should see output like:
```
Success. No rows returned
```

Check tables were created:
1. Click **"Table Editor"** in left sidebar
2. You should see all 10 new tables:
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

---

### Method 2: Using psql (Advanced)

Only use this if you're comfortable with command-line tools.

#### Step 1: Get Connection String

1. Supabase Dashboard → Project Settings → Database
2. Copy the "Connection string" (Session mode)
3. It looks like:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```

#### Step 2: Run Migration

```bash
# Install psql if you don't have it
# Mac:
brew install postgresql

# Run migration
psql "YOUR_CONNECTION_STRING_HERE" -f /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend/migrations/001_initial_schema.sql
```

---

## 🔍 Verification Checklist

After running the migration, verify everything is set up correctly:

### 1. Check Tables Exist

In Supabase SQL Editor, run:

```sql
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Expected output:** 10 tables listed

### 2. Check RLS is Enabled

```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

**Expected:** All tables should have `rowsecurity = true`

### 3. Check Trigger Exists

```sql
SELECT tgname, tgenabled 
FROM pg_trigger 
WHERE tgname = 'on_auth_user_created';
```

**Expected:** 1 row showing trigger exists

### 4. Check Target Words Were Seeded

```sql
SELECT COUNT(*) FROM public.target_words;
```

**Expected:** At least 11 rows

### 5. Test Profile Auto-Creation

Create a test user via Supabase Dashboard:
1. Authentication → Users → Add user
2. Enter test email/password
3. Go to Table Editor → profiles
4. Check if profile was auto-created

---

## 🔐 Required Environment Variables

After schema is set up, you'll need these credentials in your `.env` files:

### For Mobile App (`mobile/.env`)

```env
# Already set:
EXPO_PUBLIC_SUPABASE_URL=https://tamrgxhjyabdvtubseyu.supabase.co

# NEED TO ADD:
EXPO_PUBLIC_SUPABASE_ANON_KEY=<GET_THIS_FROM_SUPABASE>
```

**Where to find Anon Key:**
1. Supabase Dashboard → Project Settings → API
2. Copy **"anon public"** key

### For Backend (`backend/.env`)

```env
# Database connection
DATABASE_URL="postgresql://postgres.tamrgxhjyabdvtubseyu:Fuckcitadelsecurities@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?pgbouncer=true"

# NEED TO ADD:
SUPABASE_URL=https://tamrgxhjyabdvtubseyu.supabase.co
SUPABASE_JWT_SECRET=<GET_THIS_FROM_SUPABASE>
SUPABASE_SERVICE_ROLE_KEY=<GET_THIS_FROM_SUPABASE>
```

**Where to find:**
1. **JWT Secret:** Project Settings → API → JWT Settings → JWT Secret
2. **Service Role Key:** Project Settings → API → **service_role** key (keep this secret!)

---

## 🚨 Troubleshooting

### Error: "relation already exists"

**Solution:** Migration is safe to re-run. It uses `IF NOT EXISTS` and `DROP IF EXISTS`.

Just re-run the migration SQL.

### Error: "permission denied"

**Solution:** Make sure you're running as the postgres user in Supabase.

The SQL Editor automatically uses the correct user.

### Error: "auth.users does not exist"

**Solution:** This shouldn't happen in Supabase. Auth is built-in.

If you see this, contact Supabase support.

### Profile not auto-creating for new users

**Check trigger:**
```sql
SELECT * FROM pg_trigger WHERE tgname = 'on_auth_user_created';
```

**Manually test trigger:**
```sql
-- Create test user via Supabase Auth UI
-- Then check:
SELECT * FROM public.profiles;
```

---

## 📊 Database Schema Overview

```
auth.users (Supabase managed)
    ↓ (trigger creates)
profiles
    ↓ (joins)
group_members ←→ groups
    ↓
sessions
    ↓
session_speakers ←→ speaker_word_counts
    ↓ (claiming)
word_counts → user_stats_cache
```

---

## 🎯 Next Steps After Migration

1. ✅ **Update mobile/.env** with Supabase anon key
2. ✅ **Update backend/.env** with JWT secret and service role key
3. ✅ **Test authentication** - Sign up a test user
4. ✅ **Verify profile auto-creation** - Check profiles table
5. ✅ **Create a test group** - Via backend API or SQL
6. ✅ **Start implementing backend endpoints**

---

## 📝 Quick SQL Reference

**Create a test group:**
```sql
INSERT INTO public.groups (name, created_by, invite_code)
VALUES ('Test Squad', '<YOUR_USER_ID>', 'TEST123')
RETURNING *;
```

**Join a group:**
```sql
INSERT INTO public.group_members (group_id, user_id, role)
VALUES ('<GROUP_ID>', '<USER_ID>', 'member');
```

**View all users and their groups:**
```sql
SELECT 
    p.username,
    g.name as group_name,
    gm.role
FROM public.profiles p
JOIN public.group_members gm ON p.id = gm.user_id
JOIN public.groups g ON gm.group_id = g.id;
```

---

## ✅ Success Indicators

After successful migration, you should be able to:

- [ ] See 10 tables in Supabase Table Editor
- [ ] Create a user via Supabase Auth
- [ ] See auto-created profile in profiles table
- [ ] Query target_words and see 11 Singlish words
- [ ] RLS policies prevent unauthorized access
- [ ] Views are available for querying

---

**Ready to apply the schema?** Use Method 1 (SQL Editor) for the smoothest experience!

**Questions?** Check the troubleshooting section or ask in chat.
