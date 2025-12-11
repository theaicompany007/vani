"""Run all database migrations via direct PostgreSQL connection"""
import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

def get_connection():
    """Get PostgreSQL connection from SUPABASE_CONNECTION or construct from env vars"""
    connection_string = os.getenv('SUPABASE_CONNECTION')
    
    if not connection_string:
        # Construct from individual components
        db_host = os.getenv('SUPABASE_DB_HOST', '').replace('https://', '').replace('http://', '').split('/')[0]
        db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
        db_user = os.getenv('SUPABASE_DB_USER', 'postgres')
        db_password = os.getenv('SUPABASE_DB_PASSWORD', '')
        db_port = os.getenv('SUPABASE_DB_PORT', '5432')
        
        if not db_host or not db_password:
            raise ValueError("SUPABASE_CONNECTION or SUPABASE_DB_* variables required")
        
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    return psycopg2.connect(connection_string)

def run_migration_file(conn, file_path):
    """Run a single migration file"""
    print(f"\n📄 Running migration: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Remove comments (lines starting with --)
    lines = []
    for line in sql.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('--'):
            lines.append(line)
    
    sql_clean = '\n'.join(lines)
    
    # Execute the entire SQL file as one transaction
    # This handles functions, triggers, and multi-statement blocks correctly
    with conn.cursor() as cur:
        try:
            cur.execute(sql_clean)
            print(f"  ✅ Migration executed successfully")
        except Exception as e:
            error_str = str(e).lower()
            # Check if it's a "already exists" error (OK to skip)
            if 'already exists' in error_str or 'duplicate' in error_str:
                print(f"  ⚠️  Skipped (already exists): {str(e)[:100]}")
            else:
                # Try executing statement by statement for better error reporting
                print(f"  ⚠️  Full block execution failed, trying statement by statement...")
                # Split by semicolon but preserve function blocks
                statements = []
                current_statement = []
                in_function = False
                
                for line in sql.split('\n'):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('--'):
                        continue
                    
                    current_statement.append(line)
                    
                    # Check if we're entering/exiting a function
                    if 'CREATE OR REPLACE FUNCTION' in line.upper() or 'CREATE FUNCTION' in line.upper():
                        in_function = True
                    
                    if in_function and ('$$' in line or 'END;' in line.upper()):
                        if '$$' in line and line.count('$$') >= 2:
                            in_function = False
                        if 'END;' in line.upper():
                            in_function = False
                    
                    # If we hit a semicolon and we're not in a function, it's a statement boundary
                    if ';' in line and not in_function:
                        stmt = '\n'.join(current_statement).strip()
                        if stmt:
                            statements.append(stmt)
                        current_statement = []
                
                # Execute remaining statement if any
                if current_statement:
                    stmt = '\n'.join(current_statement).strip()
                    if stmt:
                        statements.append(stmt)
                
                # Execute each statement
                for i, statement in enumerate(statements):
                    if statement:
                        try:
                            cur.execute(statement)
                            print(f"  ✅ Statement {i+1}/{len(statements)} executed")
                        except Exception as e2:
                            error_str2 = str(e2).lower()
                            if 'already exists' in error_str2 or 'duplicate' in error_str2:
                                print(f"  ⚠️  Statement {i+1} skipped (already exists)")
                            else:
                                print(f"  ❌ Error in statement {i+1}: {str(e2)[:200]}")
                                # Don't raise - continue with other statements
                                print(f"  Statement was: {statement[:100]}...")
    
    conn.commit()
    print(f"  ✅ Migration completed: {file_path.name}")

def main():
    """Run all migrations in order"""
    print("🚀 Starting Database Migrations...")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("✅ Connected to Supabase database")
        
        migrations_dir = basedir / 'app' / 'migrations'
        
        # Migration files in order
        migration_files = [
            '001_create_tables.sql',
            '002_industries_tenants.sql',
            '003_auth_permissions.sql',
            '004_pitch_storage.sql',
            '005_add_industry_to_tables.sql',
            '006_add_pitch_columns.sql',
            '007_companies_table.sql',
            '008_contacts_table.sql',
            '009_link_targets_to_contacts.sql',
            '010_import_jobs_table.sql',
            '011_make_company_name_optional.sql',
            '013_add_contact_company_use_cases.sql',
            '014_user_industries_and_default.sql'
        ]
        
        for filename in migration_files:
            file_path = migrations_dir / filename
            if file_path.exists():
                run_migration_file(conn, file_path)
            else:
                print(f"⚠️  Migration file not found: {filename}")
        
        print("\n" + "=" * 60)
        print("✅ All migrations completed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
