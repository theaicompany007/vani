"""Setup database and verify Supabase connection"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

# Fix Supabase compatibility
sys.path.insert(0, str(basedir))
from scripts.fix_supabase_client import *

from supabase import create_client
import re


def verify_supabase_connection():
    """Verify Supabase connection works"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY not found in .env.local")
        return False, None
    
    try:
        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully!")
        
        # Try a simple query to verify connection
        try:
            # Check if targets table exists
            result = client.table('targets').select('id').limit(1).execute()
            print("✅ Database connection verified! Tables are accessible.")
            return True, client
        except Exception as e:
            error_str = str(e)
            # These errors mean connection works but table doesn't exist
            if any(phrase in error_str.lower() for phrase in [
                'does not exist',
                'not find the table',
                'relation',
                'pgrst205',
                'schema cache'
            ]):
                print("✅ Connection works! (Tables don't exist yet - this is expected)")
                return True, client  # Connection works, just need to create tables
            else:
                print(f"⚠️  Connection test failed: {e}")
                return False, None
                
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return False, None


def show_setup_instructions():
    """Show instructions for setting up database"""
    supabase_url = os.getenv('SUPABASE_URL')
    
    if not supabase_url:
        print("❌ SUPABASE_URL not found")
        return
    
    # Extract project reference
    match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
    if not match:
        print("❌ Could not parse project reference")
        return
    
    project_ref = match.group(1)
    
    # Read SQL file
    sql_file = Path(__file__).parent.parent / 'app' / 'migrations' / '001_create_tables.sql'
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return
    
    print("\n" + "="*70)
    print("  DATABASE SETUP REQUIRED")
    print("="*70)
    print("\nSupabase requires SQL to be executed via the Dashboard SQL Editor.")
    print("This is a security feature - DDL operations cannot be done via API.\n")
    print("Steps:")
    print(f"  1. Open: https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print("  2. Copy the SQL from: app/migrations/001_create_tables.sql")
    print("  3. Paste into the SQL Editor")
    print("  4. Click 'Run' to execute")
    print("\n" + "="*70 + "\n")


def main():
    print("\n" + "="*70)
    print("  VANI Database Setup & Verification")
    print("="*70 + "\n")
    
    # Verify connection
    connected, client = verify_supabase_connection()
    
    if not connected:
        print("\n❌ Cannot connect to Supabase. Please check your .env.local file.")
        print("   Required variables:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_KEY or SUPABASE_SERVICE_KEY")
        return False
    
    # Check if tables exist
    if client:
        try:
            # Try to query targets table
            result = client.table('targets').select('id').limit(1).execute()
            print("\n✅ Tables already exist! Database is ready.")
            print("   You can now seed targets with: python scripts/seed_targets.py")
            return True
        except Exception as e:
            error_str = str(e)
            # Check if error is about table not existing
            if any(phrase in error_str.lower() for phrase in [
                'does not exist',
                'not find the table',
                'relation',
                'pgrst205',
                'schema cache'
            ]):
                print("\n⚠️  Tables don't exist yet. You need to create them first.")
                show_setup_instructions()
                return False
            else:
                print(f"\n❌ Unexpected error: {e}")
                return False
    
    return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

