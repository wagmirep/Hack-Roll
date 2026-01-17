# Database Migrations

This directory contains SQL migration files for the LahStats database schema.

## How to Apply Migrations

### Option 1: Supabase SQL Editor (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to the SQL Editor (left sidebar)
3. Click "New Query"
4. Copy and paste the contents of `005_apply_pending_migrations.sql`
5. Click "Run" to execute the migration
6. Verify the success message at the bottom

### Option 2: Using psql Command Line

```bash
# From the backend directory
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres" < migrations/005_apply_pending_migrations.sql
```

Replace:
- `[YOUR-PASSWORD]` with your database password
- `[YOUR-PROJECT-REF]` with your Supabase project reference

## Current Migration Status

### ✅ Already Applied (in initial schema)
- `001_initial_schema.sql` - Initial database setup

### 🔄 Pending (Combined in 005)
- `002_add_claim_types.sql` - Add support for claiming speakers
- `003_make_group_optional.sql` - Allow personal sessions
- `004_rename_file_url_to_storage_path.sql` - Update audio_chunks schema

### 📦 To Apply Now
- **`005_apply_pending_migrations.sql`** ⬅️ **RUN THIS NOW**

## What Migration 005 Does

This migration combines all pending changes:

1. **Makes `group_id` optional** - Allows personal recording sessions without a group
2. **Adds speaker claiming features** - Supports claiming as self, tagging other users, or marking as guests
3. **Fixes audio_chunks schema** - Renames `file_url` to `storage_path` and updates column types
4. **Updates RLS policies** - Ensures personal sessions work correctly

## After Applying Migration

Once you've applied migration 005, your recording should work! The error you were seeing:

```
column audio_chunks.storage_path does not exist
```

Will be resolved because the column will be renamed from `file_url` to `storage_path`.

## Verification

After running the migration, you should see output showing:
- `sessions.group_id` is nullable: YES
- `word_counts.group_id` is nullable: YES  
- `session_speakers` has new columns: `claim_type`, `attributed_to_user_id`, `guest_name`
- `audio_chunks` has `storage_path` column (not `file_url`)

## Troubleshooting

### If migration fails

1. Check if you have the correct database permissions
2. Ensure you're connected to the right Supabase project
3. Check the error message - it will tell you which part failed
4. You can run individual migration files (002, 003, 004) separately if needed

### If you see "column already exists" errors

This is safe to ignore - it means that part of the migration was already applied. The migration is designed to be idempotent (safe to run multiple times).

## Migration History

| File | Date | Description | Status |
|------|------|-------------|--------|
| 001_initial_schema.sql | 2026-01-17 | Initial database setup | ✅ Applied |
| 002_add_claim_types.sql | 2026-01-17 | Add claiming features | 🔄 In 005 |
| 003_make_group_optional.sql | 2026-01-17 | Personal sessions | 🔄 In 005 |
| 004_rename_file_url_to_storage_path.sql | 2026-01-17 | Fix audio_chunks | 🔄 In 005 |
| 005_apply_pending_migrations.sql | 2026-01-17 | Combined pending | ⏳ Pending |
