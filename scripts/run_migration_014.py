"""Python script to run migration 014 via Supabase"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv('.env.local')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print('❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY required in .env.local')
    sys.exit(1)

# Read SQL file
sql_file = project_root / 'app' / 'migrations' / '014_user_industries_and_default.sql'
with open(sql_file, 'r') as f:
    sql = f.read()

print(f'📄 Executing migration: {sql_file.name}')
print(f'🔗 Supabase URL: {supabase_url}')

# Execute SQL using Supabase REST API (PostgREST)
# Note: Supabase doesn't have a direct SQL execution endpoint via REST
# We'll use the Supabase Python client's table operations or direct SQL

try:
    # Method 1: Try using Supabase Python client with direct SQL (if available)
    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)
    
    # Supabase Python client doesn't support raw SQL execution
    # So we'll print the SQL for manual execution
    print('\n' + '='*60)
    print('⚠️  Supabase REST API does not support direct SQL execution')
    print('='*60)
    print('\n📋 Please copy and paste this SQL into Supabase SQL Editor:\n')
    print('─'*60)
    print(sql)
    print('─'*60)
    print('\n🔗 Supabase SQL Editor: https://supabase.com/dashboard/project/_/sql')
    print('   (Replace _ with your project ID)\n')
    
    # Alternative: Try to execute via psycopg2 if DATABASE_URL is available
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            # Parse connection string
            result = urlparse(database_url)
            conn = psycopg2.connect(
                database=result.path[1:],  # Remove leading /
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port
            )
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            cur.close()
            conn.close()
            print('✅ Migration 014 executed successfully via direct database connection!')
            sys.exit(0)
        except ImportError:
            print('💡 Tip: Install psycopg2 to execute SQL directly: pip install psycopg2-binary')
        except Exception as e:
            print(f'❌ Error executing SQL: {e}')
            print('\n📋 Please run the SQL manually in Supabase SQL Editor')
    
except Exception as e:
    print(f'❌ Error: {e}')
    print('\n📋 Please run the SQL manually in Supabase SQL Editor')
    sys.exit(1)
















