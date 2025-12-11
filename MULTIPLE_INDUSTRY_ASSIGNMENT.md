# Multiple Industry Assignment & Default Industry Feature

## Overview
This feature allows users to be assigned to multiple industries with a default industry that automatically loads when accessing pitch presentations and target hit lists.

## Database Changes

### Migration: `014_user_industries_and_default.sql`
- Creates `user_industries` junction table for many-to-many relationship
- Adds `default_industry_id` to `app_users` table
- Migrates existing `industry_id` and `active_industry_id` data
- Ensures only one default industry per user via trigger

## API Endpoints

### `/api/user-industries/<user_id>` (GET)
Get all industries assigned to a user.

### `/api/user-industries/<user_id>` (POST)
Assign an industry to a user.
```json
{
  "industry_id": "uuid",
  "is_default": false
}
```

### `/api/user-industries/<user_id>/<industry_id>` (DELETE)
Remove an industry assignment from a user.

### `/api/user-industries/<user_id>/set-default` (POST)
Set a default industry for a user.
```json
{
  "industry_id": "uuid"
}
```

## UI Changes

### User Management Tab
- Replaced "Assign Industry" button with "Manage Industries" button
- New modal with:
  - Search box to find and add industries
  - List of assigned industries with default indicator
  - "Set Default" button for each non-default industry
  - "Remove" button for each industry

## Default Industry Behavior

1. On login/page load, `default_industry_id` is prioritized over `active_industry_id`
2. When switching industries, the selected industry becomes the new `active_industry_id`
3. Default industry is used when:
   - Loading pitch presentations
   - Loading target hit list
   - No active industry is set

## AI-Powered Industry Assignment Script

### `scripts/assign_industries_ai.py`

Assigns industries to contacts and companies that don't have industry set using OpenAI.

**Usage:**
```bash
# Dry run (see what would be assigned)
python scripts/assign_industries_ai.py --dry-run

# Process contacts only
python scripts/assign_industries_ai.py --contacts-only

# Process companies only
python scripts/assign_industries_ai.py --companies-only

# Process with custom batch size
python scripts/assign_industries_ai.py --batch-size 200

# Full run (make changes)
python scripts/assign_industries_ai.py
```

**Features:**
- Uses OpenAI GPT-4o-mini to determine industry from company name, domain, and description
- Automatically creates industries if they don't exist
- Processes in batches (default: 100 records)
- Handles both contacts and companies
- Falls back to company industry for contacts if available

**Requirements:**
- `OPENAI_API_KEY` in `.env.local`
- `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env.local`

## Running the Migration

1. **Via Supabase SQL Editor (Recommended):**
   - Open Supabase Dashboard → SQL Editor
   - Copy contents of `app/migrations/014_user_industries_and_default.sql`
   - Paste and run

2. **Via Python Script:**
   ```bash
   python scripts/run_migration_014.py
   ```
   Note: This script will display the SQL for manual execution if direct execution is not available.

3. **Via run_all_migrations.py:**
   ```bash
   python scripts/run_all_migrations.py
   ```
   This runs all migrations including 014.

## Next Steps

1. Run the migration:
   ```bash
   python scripts/run_migration_014.py
   ```
   Or manually in Supabase SQL Editor

2. Restart Flask application

3. Test multiple industry assignment in User Management:
   - Click "Manage Industries" for any user
   - Use search box to find and add industries
   - Set default industry

4. Set default industries for users:
   ```bash
   python scripts/assign_industry_to_user.py user@example.com "FMCG" --default
   ```

5. Run AI assignment script for contacts/companies without industry:
   ```bash
   python scripts/assign_industries_ai.py --dry-run  # Preview
   python scripts/assign_industries_ai.py             # Execute
   ```

6. Verify default industry loads on pitch presentation and target hit list pages

## Related Documentation

- `INDUSTRY_MANAGEMENT.md` - Complete guide to industry management
- `SCRIPTS_UPDATED.md` - Updated scripts documentation
- `RUN_MIGRATION_014.md` - Migration execution guide

