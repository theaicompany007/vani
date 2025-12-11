"""Create database tables directly via Postgres connection"""
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("ERROR: psycopg2-binary not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_postgres_connection_string():
    """Build Postgres connection string from Supabase environment variables"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    # Check if DATABASE_URL is already set
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"Using DATABASE_URL from environment")
        return database_url
    
    if not supabase_url or not supabase_service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env.local")
        return None
    
    # Extract project reference from Supabase URL
    # Format: https://xxxxx.supabase.co
    match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
    if not match:
        print(f"ERROR: Could not parse project reference from SUPABASE_URL: {supabase_url}")
        return None
    
    project_ref = match.group(1)
    
    # Supabase Postgres connection format:
    # postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    # The password is the service role key (but we need the actual DB password)
    # Actually, for Supabase, we need the database password, not the service key
    
    # Try to get DB password from env, or use service key as fallback
    db_password = os.getenv('SUPABASE_DB_PASSWORD') or supabase_service_key
    
    # Build connection string
    conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    
    print(f"Built Postgres connection string for project: {project_ref}")
    return conn_string


def create_tables():
    """Create database tables by executing SQL migration"""
    conn_string = get_postgres_connection_string()
    
    if not conn_string:
        return False
    
    # Read migration file
    migration_file = Path(__file__).parent.parent / 'app' / 'migrations' / '001_create_tables.sql'
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print("\n" + "="*60)
    print("Connecting to Supabase Postgres database...")
    print("="*60 + "\n")
    
    try:
        # Connect to database
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to database successfully!")
        print("\nExecuting migration SQL...\n")
        
        # Execute SQL (split by semicolons for better error reporting)
        # But first, let's try executing the whole thing
        try:
            cursor.execute(sql)
            print("✅ Migration executed successfully!")
            
            # Verify tables were created
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            print(f"\n✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")
            
            cursor.close()
            conn.close()
            
            print("\n" + "="*60)
            print("✅ Database setup complete!")
            print("="*60 + "\n")
            
            return True
            
        except psycopg2.Error as e:
            print(f"\n❌ Error executing SQL:")
            print(f"   {str(e)}")
            
            # Try to provide more context
            if "already exists" in str(e).lower():
                print("\n⚠️  Some tables may already exist. This is OK if you're re-running the migration.")
                print("   The script will continue...")
                return True
            
            cursor.close()
            conn.close()
            return False
            
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed:")
        print(f"   {str(e)}")
        print("\n💡 Tips:")
        print("   1. Check your SUPABASE_URL and SUPABASE_SERVICE_KEY in .env.local")
        print("   2. If using service key, you may need SUPABASE_DB_PASSWORD instead")
        print("   3. Verify your Supabase project is active")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = create_tables()
    sys.exit(0 if success else 1)

