"""Create database tables directly using SUPABASE_CONNECTION"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("ERROR: psycopg2-binary not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_connection_string():
    """Get Postgres connection string from environment"""
    # Try SUPABASE_CONNECTION first (direct connection string)
    conn_string = os.getenv('SUPABASE_CONNECTION')
    
    if conn_string:
        print("✅ Using SUPABASE_CONNECTION from .env.local")
        return conn_string
    
    # Fallback: Build from components
    supabase_url = os.getenv('SUPABASE_URL')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    
    if not supabase_url or not db_password:
        print("ERROR: SUPABASE_CONNECTION or (SUPABASE_URL + SUPABASE_DB_PASSWORD) required")
        return None
    
    # Extract project reference
    import re
    match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
    if not match:
        print("ERROR: Could not parse project reference from SUPABASE_URL")
        return None
    
    project_ref = match.group(1)
    conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    
    print(f"✅ Built connection string for project: {project_ref}")
    return conn_string


def create_tables():
    """Create database tables"""
    conn_string = get_connection_string()
    
    if not conn_string:
        return False
    
    # Read migration file
    migration_file = Path(__file__).parent.parent / 'app' / 'migrations' / '001_create_tables.sql'
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print("\n" + "="*70)
    print("  CREATING DATABASE TABLES")
    print("="*70)
    print("Connecting to Supabase Postgres database...\n")
    
    try:
        # Connect to database
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to database successfully!")
        print("\nExecuting migration SQL...\n")
        
        # Execute SQL
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
            
            # Verify indexes
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY indexname;
            """)
            
            indexes = cursor.fetchall()
            print(f"\n✅ Created {len(indexes)} indexes:")
            for idx in indexes[:10]:  # Show first 10
                print(f"   - {idx[0]}")
            if len(indexes) > 10:
                print(f"   ... and {len(indexes) - 10} more")
            
            # Verify triggers
            cursor.execute("""
                SELECT trigger_name 
                FROM information_schema.triggers 
                WHERE trigger_schema = 'public'
                ORDER BY trigger_name;
            """)
            
            triggers = cursor.fetchall()
            print(f"\n✅ Created {len(triggers)} triggers:")
            for trigger in triggers:
                print(f"   - {trigger[0]}")
            
            cursor.close()
            conn.close()
            
            print("\n" + "="*70)
            print("✅ Database setup complete!")
            print("="*70)
            print("\nNext steps:")
            print("  1. Seed targets: python scripts/seed_targets.py")
            print("  2. Start application: python run.py")
            print("  3. Configure webhooks: python scripts/configure_webhooks.py")
            print("="*70 + "\n")
            
            return True
            
        except psycopg2.Error as e:
            error_msg = str(e)
            print(f"\n⚠️  SQL Execution Result:")
            
            # Check if tables already exist (this is OK)
            if "already exists" in error_msg.lower():
                print("   Some objects already exist. Checking current state...\n")
                
                # List existing tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                existing_tables = cursor.fetchall()
                
                if existing_tables:
                    print(f"✅ Found {len(existing_tables)} existing tables:")
                    for table in existing_tables:
                        print(f"   - {table[0]}")
                    print("\n✅ Database is already set up!")
                    cursor.close()
                    conn.close()
                    return True
                else:
                    print("   No tables found. Error details:")
                    print(f"   {error_msg}")
            else:
                print(f"❌ Error executing SQL:")
                print(f"   {error_msg}")
            
            cursor.close()
            conn.close()
            return False
            
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed:")
        print(f"   {str(e)}")
        print("\n💡 Tips:")
        print("   1. Check your SUPABASE_CONNECTION in .env.local")
        print("   2. Verify your Supabase project is active")
        print("   3. Ensure database password is correct")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    success = create_tables()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

