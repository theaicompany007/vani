"""Create database tables via Supabase REST API (using rpc)"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)


def create_tables_via_sql_editor():
    """Provide instructions for manual SQL execution"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env.local")
        return False
    
    # Extract project reference
    import re
    match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
    if not match:
        print(f"ERROR: Could not parse project reference from SUPABASE_URL")
        return False
    
    project_ref = match.group(1)
    
    # Read migration file
    migration_file = Path(__file__).parent.parent / 'app' / 'migrations' / '001_create_tables.sql'
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print("\n" + "="*70)
    print("  DATABASE SETUP INSTRUCTIONS")
    print("="*70)
    print("\nSupabase requires SQL to be executed via the Dashboard SQL Editor.")
    print("Follow these steps:\n")
    print(f"1. Open: https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print("2. Copy the SQL below")
    print("3. Paste into the SQL Editor")
    print("4. Click 'Run' to execute\n")
    print("="*70)
    print("SQL TO EXECUTE:")
    print("="*70 + "\n")
    print(sql)
    print("\n" + "="*70)
    print("After running the SQL, you can seed targets with:")
    print("  python scripts/seed_targets.py")
    print("="*70 + "\n")
    
    return True


def try_create_via_rest_api():
    """Try to create tables via Supabase REST API (may not work for DDL)"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        return False
    
    # Read migration SQL
    migration_file = Path(__file__).parent.parent / 'app' / 'migrations' / '001_create_tables.sql'
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Supabase doesn't allow DDL via REST API for security
    # But we can try using the SQL editor API if available
    print("⚠️  Supabase REST API doesn't support DDL operations (CREATE TABLE, etc.)")
    print("   for security reasons. Please use the SQL Editor in the dashboard.\n")
    
    return False


if __name__ == '__main__':
    # Try REST API first (will likely fail)
    if not try_create_via_rest_api():
        # Fall back to instructions
        create_tables_via_sql_editor()

