"""Run the import_jobs table migration
This script creates the import_jobs table needed for background contact imports.

Usage:
    python scripts/run_import_jobs_migration.py
"""
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    try:
        from app.supabase_client import get_supabase_client
        from flask import Flask
        
        # Create a minimal Flask app context
        app = Flask(__name__)
        app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL', '')
        app.config['SUPABASE_KEY'] = os.getenv('SUPABASE_KEY', '')
        
        if not app.config['SUPABASE_URL'] or not app.config['SUPABASE_KEY']:
            print('ERROR: SUPABASE_URL and SUPABASE_KEY must be set in environment')
            print('Please set them in your .env or .env.local file')
            sys.exit(1)
        
        # Read migration SQL
        migration_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'app', 
            'migrations', 
            '010_import_jobs_table.sql'
        )
        
        if not os.path.exists(migration_file):
            print(f'ERROR: Migration file not found: {migration_file}')
            sys.exit(1)
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print('Running import_jobs table migration...')
        print('=' * 60)
        
        with app.app_context():
            supabase = get_supabase_client(app)
            if not supabase:
                print('ERROR: Could not initialize Supabase client')
                sys.exit(1)
            
            # Execute migration using Supabase RPC or direct SQL
            # Note: Supabase Python client doesn't support raw SQL execution
            # So we'll use the REST API with a custom query
            
            # Split SQL into individual statements
            statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
            
            print(f'Found {len(statements)} SQL statements to execute')
            print('\nIMPORTANT: Supabase Python client cannot execute raw SQL.')
            print('Please run this migration manually in Supabase SQL Editor:')
            print('=' * 60)
            print('\n1. Open Supabase Dashboard')
            print('2. Go to SQL Editor')
            print('3. Paste the following SQL and execute:')
            print('=' * 60)
            print(migration_sql)
            print('=' * 60)
            print('\nAlternatively, you can use psql if you have the connection string:')
            print('psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" -f app/migrations/010_import_jobs_table.sql')
            
    except ImportError as e:
        print(f'ERROR: Could not import required modules: {e}')
        print('Make sure you are in the project root and venv is activated')
        sys.exit(1)
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()




















