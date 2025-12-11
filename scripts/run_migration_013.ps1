# PowerShell script to run migration 013
# Usage: .\scripts\run_migration_013.ps1

# Load environment variables from .env.local
$envFile = ".env.local"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Get database connection string
$dbUrl = $env:DATABASE_URL
if (-not $dbUrl) {
    # Try to construct from Supabase URL
    $supabaseUrl = $env:SUPABASE_URL
    $supabaseKey = $env:SUPABASE_SERVICE_ROLE_KEY
    
    if ($supabaseUrl -and $supabaseKey) {
        Write-Host "Using Supabase REST API method..."
        Write-Host "Please run the SQL manually in Supabase SQL Editor:"
        Write-Host "File: app\migrations\013_add_contact_company_use_cases.sql"
        exit
    } else {
        Write-Error "DATABASE_URL or SUPABASE_URL not found in .env.local"
        exit 1
    }
}

# Check if psql is available
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue
if (-not $psqlPath) {
    Write-Host "psql not found. Using Python script instead..."
    python -c @"
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv('.env.local')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print('Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required')
    exit(1)

# Read SQL file
with open('app/migrations/013_add_contact_company_use_cases.sql', 'r') as f:
    sql = f.read()

# Execute via Supabase REST API (rpc)
supabase: Client = create_client(supabase_url, supabase_key)

# Use Supabase REST API to execute SQL
import requests
response = requests.post(
    f'{supabase_url}/rest/v1/rpc/exec_sql',
    headers={
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    },
    json={'query': sql}
)

if response.status_code == 200:
    print('✅ Migration 013 executed successfully')
else:
    print(f'❌ Error: {response.status_code} - {response.text}')
    print('Please run the SQL manually in Supabase SQL Editor')
"@
    exit
}

# Use psql to execute
$sqlFile = "app\migrations\013_add_contact_company_use_cases.sql"
Write-Host "Executing migration: $sqlFile"
psql $dbUrl -f $sqlFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migration 013 executed successfully"
} else {
    Write-Error "❌ Migration failed. Please check the error above."
}





