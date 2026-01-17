# 🚨 URGENT: Apply Database Migration

## The Problem

Your recording is failing with this error:
```
column audio_chunks.storage_path does not exist
```

This is because the database schema doesn't match the backend code.

## The Solution

Apply migration `005_apply_pending_migrations.sql` to your Supabase database.

## Step-by-Step Instructions

### Method 1: Supabase Dashboard (Easiest - 2 minutes)

1. **Open Supabase Dashboard**
   - Go to: https://supabase.com/dashboard
   - Select your project: `tamrgxhjyabdvtubseyu`

2. **Open SQL Editor**
   - Click "SQL Editor" in the left sidebar
   - Click "+ New query" button

3. **Copy and Paste Migration**
   - Open this file: `/Hack-Roll/backend/migrations/005_apply_pending_migrations.sql`
   - Copy ALL the contents
   - Paste into the SQL Editor

4. **Run Migration**
   - Click the "Run" button (or press Cmd/Ctrl + Enter)
   - Wait for completion (should take 2-3 seconds)
   - Look for: `Migration 005 completed successfully! ✅`

5. **Test Your Recording**
   - Go back to your app
   - Try recording again
   - It should work now! 🎉

### Method 2: Command Line (Alternative)

If you prefer using the terminal:

```bash
# From the backend directory
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend

# You'll need your Supabase database password
# Find it in your .env file or Supabase dashboard under Settings > Database

psql "postgresql://postgres:[YOUR-DB-PASSWORD]@db.tamrgxhjyabdvtubseyu.supabase.co:5432/postgres" < migrations/005_apply_pending_migrations.sql
```

## What This Migration Does

1. ✅ Renames `file_url` → `storage_path` in `audio_chunks` table
2. ✅ Makes `group_id` optional (allows personal recordings)
3. ✅ Adds speaker claiming features
4. ✅ Updates all RLS policies for personal sessions

## Verification

After applying, the verification queries will show:
- ✅ `audio_chunks.storage_path` column exists
- ✅ `sessions.group_id` is nullable
- ✅ New claiming columns added

## Expected Output

You should see output like this:

```
ALTER TABLE
ALTER TABLE
DROP POLICY
CREATE POLICY
... (more ALTER TABLE and policy updates)
Migration 005 completed successfully! ✅
```

## After Migration

1. **Restart your backend** (if it's running)
   ```bash
   # The uvicorn server should auto-reload, but if not:
   # Stop it (Ctrl+C) and restart:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Test recording again**
   - Start a recording
   - Stop the recording
   - It should upload successfully!

## Troubleshooting

### "column already exists" errors
- **Safe to ignore** - means part was already applied

### "permission denied" errors
- Make sure you're using the correct database password
- Ensure you're the database owner

### Still getting the error after migration?
- Check that the migration completed successfully
- Restart your backend server
- Clear your browser cache
- Try creating a new recording session

## Need Help?

If you run into issues:
1. Check the full error message
2. Verify you're connected to the right database
3. Make sure the migration file path is correct
4. Check backend logs for more details

---

**TL;DR: Go to Supabase Dashboard → SQL Editor → Paste `005_apply_pending_migrations.sql` → Run → Done! 🚀**
