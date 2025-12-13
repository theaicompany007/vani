# Running Migration 014: User Industries and Default Industry

This migration adds support for multiple industry assignment per user and default industry selection.

## What This Migration Does

1. Creates `user_industries` junction table for many-to-many relationship
2. Adds `default_industry_id` column to `app_users` table
3. Migrates existing `industry_id` and `active_industry_id` data to `user_industries`
4. Creates trigger to ensure only one default industry per user

## Running the Migration

### Method 1: Supabase SQL Editor (Recommended)

1. Open Supabase Dashboard → SQL Editor
2. Copy the contents of `app/migrations/014_user_industries_and_default.sql`
3. Paste and execute

### Method 2: Python Script

```bash
python scripts/run_migration_014.py
```

This will display the SQL for manual execution if direct execution is not available.

### Method 3: Direct PostgreSQL Connection

If you have `psycopg2` installed and `DATABASE_URL` set:

```bash
python scripts/run_migration_014.py
```

The script will attempt to execute directly if `DATABASE_URL` is available.

## After Migration

1. Restart Flask application
2. Test "Manage Industries" button in User Management tab
3. Users can now be assigned to multiple industries
4. Set default industry for each user

## Verification

Check that the following exist:
- `user_industries` table
- `default_industry_id` column in `app_users` table
- Trigger `trigger_ensure_single_default_industry`

```sql
-- Check table exists
SELECT * FROM user_industries LIMIT 1;

-- Check column exists
SELECT default_industry_id FROM app_users LIMIT 1;

-- Check trigger exists
SELECT trigger_name FROM information_schema.triggers 
WHERE trigger_name = 'trigger_ensure_single_default_industry';
```












