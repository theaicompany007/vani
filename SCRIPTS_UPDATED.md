# Updated Scripts Documentation

This document lists all utility scripts and their purposes after the latest updates.

## Migration Scripts

### `run_all_migrations.py`
Runs all database migrations in order.

**Updated:**
- Added migration 014 (`014_user_industries_and_default.sql`)
- Includes all migrations through 014

**Usage:**
```bash
python scripts/run_all_migrations.py
```

### `run_migration_013.py`
Runs migration 013 (adds contact_management and company_management use cases).

**Usage:**
```bash
python scripts/run_migration_013.py
```

### `run_migration_014.py` (NEW)
Runs migration 014 (adds user_industries table and default_industry_id).

**Usage:**
```bash
python scripts/run_migration_014.py
```

See `RUN_MIGRATION_014.md` for details.

## User Management Scripts

### `fix_user.py`
Fixes or creates a user in app_users table.

**Updated:**
- Handles `default_industry_id` field
- Auto-grants all use cases including `contact_management` and `company_management`

**Usage:**
```bash
python scripts/fix_user.py user@example.com password --super-user
python scripts/fix_user.py user@example.com password --industry-admin
```

### `set_industry_admin.py`
Sets a user as industry admin and assigns them to a specific industry.

**Updated:**
- Sets `default_industry_id` when assigning industry
- Attempts to add to `user_industries` table if it exists
- Falls back to legacy `industry_id` if table doesn't exist

**Usage:**
```bash
python scripts/set_industry_admin.py user@example.com "FMCG"
python scripts/set_industry_admin.py user@example.com --industry-id <uuid>
```

### `assign_industry_to_user.py` (NEW)
Assigns an industry to a user via `user_industries` table (supports multiple industries).

**Usage:**
```bash
python scripts/assign_industry_to_user.py user@example.com "FMCG"
python scripts/assign_industry_to_user.py user@example.com "FMCG" --default
python scripts/assign_industry_to_user.py user@example.com --industry-id <uuid> --default
```

### `grant_default_permissions.py`
Grants, revokes, or toggles use case permissions for a user.

**Updated:**
- Includes `contact_management` and `company_management` use cases in examples
- Supports all use cases including new ones

**Usage:**
```bash
# Grant all permissions
python scripts/grant_default_permissions.py user@example.com --grant

# Grant specific use cases
python scripts/grant_default_permissions.py user@example.com --grant --use-cases contact_management company_management

# Toggle permissions
python scripts/grant_default_permissions.py user@example.com --toggle
```

### `confirm_user_email.py`
Confirms a user's email address in Supabase Auth.

**No changes needed** - works as-is.

**Usage:**
```bash
python scripts/confirm_user_email.py user@example.com
```

## Data Management Scripts

### `assign_industries_ai.py`
AI-powered script to assign industries to contacts and companies using OpenAI.

**No changes needed** - works as-is.

**Usage:**
```bash
# Dry run
python scripts/assign_industries_ai.py --dry-run

# Process contacts only
python scripts/assign_industries_ai.py --contacts-only

# Process companies only
python scripts/assign_industries_ai.py --companies-only

# Full run
python scripts/assign_industries_ai.py
```

### `update_fmcg_targets.py`
Updates or creates FMCG targets with pain points, pitch angles, and LinkedIn scripts.

**No changes needed** - works as-is.

**Usage:**
```bash
python scripts/update_fmcg_targets.py
```

## Testing Scripts

### `test_contacts_companies.py`
Tests contacts and companies functionality.

**No changes needed** - works as-is.

**Usage:**
```bash
python scripts/test_contacts_companies.py
```

## Utility Scripts

### `fix_supabase_client.py`
Fixes Supabase client compatibility issues with httpx.

**No changes needed** - works as-is.

### `run_import_jobs_migration.py`
Runs the import_jobs table migration.

**No changes needed** - works as-is.

## Main Application Script

### `run.py`
Main startup script for the Flask application.

**Updated:**
- Checks for `RAG_API_KEY`, `RAG_SERVICE_URL`, and `GEMINI_API_KEY` (optional)
- Shows warnings if AI features are not configured

**Usage:**
```bash
python run.py
```

## PowerShell Scripts

### `run_migration_013.ps1`
PowerShell script to run migration 013.

**No changes needed** - works as-is.

**Usage:**
```powershell
.\scripts\run_migration_013.ps1
```

## Environment Variables

All scripts now support these environment variables:

**Required:**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`)
- `SUPABASE_KEY` (anon key)

**Optional (for AI features):**
- `OPENAI_API_KEY` - For AI message generation and industry assignment
- `RAG_API_KEY` - For RAG service integration
- `RAG_SERVICE_URL` - RAG service URL (default: https://rag.kcube-consulting.com)
- `GEMINI_API_KEY` - For Google Gemini/Notebook LM integration

## Migration Order

Run migrations in this order:

1. `001_create_tables.sql`
2. `002_industries_tenants.sql`
3. `003_auth_permissions.sql`
4. `004_pitch_storage.sql`
5. `005_add_industry_to_tables.sql`
6. `006_add_pitch_columns.sql`
7. `007_companies_table.sql`
8. `008_contacts_table.sql`
9. `009_link_targets_to_contacts.sql`
10. `010_import_jobs_table.sql`
11. `011_make_company_name_optional.sql`
12. `013_add_contact_company_use_cases.sql`
13. `014_user_industries_and_default.sql` ⭐ NEW

## Quick Reference

### Set up a new user with all permissions:
```bash
python scripts/fix_user.py user@example.com password --super-user
python scripts/grant_default_permissions.py user@example.com --grant
```

### Assign multiple industries to a user:
```bash
python scripts/assign_industry_to_user.py user@example.com "FMCG" --default
python scripts/assign_industry_to_user.py user@example.com "Food & Beverages"
```

### Set user as industry admin:
```bash
python scripts/set_industry_admin.py user@example.com "FMCG"
```

### Assign industries to contacts/companies:
```bash
python scripts/assign_industries_ai.py --dry-run  # Preview
python scripts/assign_industries_ai.py             # Execute
```

















