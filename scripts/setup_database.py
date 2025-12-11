"""Script to set up Supabase database schema"""
import os
import sys
from pathlib import Path
import requests

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)


def setup_database():
    """Run SQL migration in Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env.local")
        return False
    
    # Read migration file
    migration_file = Path(__file__).parent.parent / 'app' / 'migrations' / '001_create_tables.sql'
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Extract project reference from URL
    # Supabase URL format: https://xxxxx.supabase.co
    project_ref = supabase_url.split('//')[1].split('.')[0]
    
    print(f"Setting up database for project: {project_ref}")
    print("\n⚠️  IMPORTANT: Supabase doesn't allow direct SQL execution via API.")
    print("Please run the migration manually:\n")
    print("1. Go to: https://supabase.com/dashboard/project/{}/sql/new".format(project_ref))
    print("2. Copy and paste the SQL from: app/migrations/001_create_tables.sql")
    print("3. Click 'Run' to execute\n")
    
    # Optionally, we could use Supabase Management API, but it requires additional setup
    # For now, provide clear instructions
    
    print("SQL Migration Content:")
    print("=" * 60)
    print(sql)
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    setup_database()

