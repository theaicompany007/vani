# Run Migration 013 - PowerShell Commands

## Quick Commands

### Option 1: Using psql (if you have PostgreSQL client installed)

```powershell
# Load DATABASE_URL from .env.local and run migration
$env:DATABASE_URL = (Get-Content .env.local | Select-String "DATABASE_URL" | ForEach-Object { if ($_ -match 'DATABASE_URL=(.+)') { $matches[1] } })
psql $env:DATABASE_URL -f app\migrations\013_add_contact_company_use_cases.sql
```

### Option 2: Direct psql command (if you know your connection string)

```powershell
psql "postgresql://postgres:Helloraaj#007@db.rkntrsprfcypwikshvsf.supabase.co:5432/postgres" -f app\migrations\013_add_contact_company_use_cases.sql
psql "postgresql://postgres:Helloraaj#007@db.rkntrsprfcypwikshvsf.supabase.co:5432/postgres" -f app\migrations\014_user_industries_and_default.sql
psql "postgresql://postgres:Helloraaj#007@db.rkntrsprfcypwikshvsf.supabase.co:5432/postgres" -f app/migrations/006_create_signature_profiles.sql

```

### Option 3: Using Python with psycopg2 (if installed)

```powershell
# Activate venv and run
.\venv\Scripts\activate.ps1
python scripts\run_migration_013.py
```

### Option 4: Manual Execution (Easiest - Recommended)

**Copy this SQL and paste it into Supabase SQL Editor:**

```sql
-- Add contact_management and company_management use cases if they don't exist
INSERT INTO use_cases (code, name, description) 
VALUES 
  ('contact_management', 'Contact Management', 'Manage contacts and contact data'),
  ('company_management', 'Company Management', 'Manage companies and company data')
ON CONFLICT (code) DO NOTHING;
```

**Steps:**
1. Go to your Supabase Dashboard
2. Navigate to SQL Editor
3. Paste the SQL above
4. Click "Run"

## Verify Migration

After running, verify the use cases were added:

```sql
SELECT * FROM use_cases WHERE code IN ('contact_management', 'company_management');
```

















