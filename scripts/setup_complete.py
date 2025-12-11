"""Complete setup: Run migrations and create super user"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

def run_migrations():
    """Run all database migrations using Supabase client"""
    print("🚀 Running Database Migrations...")
    print("=" * 60)
    
    try:
        from app.supabase_client import init_supabase
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        
        supabase = init_supabase(url, key)
        
        migrations_dir = basedir / 'app' / 'migrations'
        migration_files = [
            '002_industries_tenants.sql',
            '003_auth_permissions.sql',
            '004_pitch_storage.sql',
            '005_add_industry_to_tables.sql'
        ]
        
        for filename in migration_files:
            file_path = migrations_dir / filename
            if file_path.exists():
                print(f"\n📄 Running: {filename}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql = f.read()
                
                # Execute via Supabase RPC or direct SQL
                # Note: Supabase REST API doesn't support DDL, so we'll use psycopg2 if available
                try:
                    import psycopg2
                    conn_string = os.getenv('SUPABASE_CONNECTION')
                    if conn_string:
                        conn = psycopg2.connect(conn_string)
                        cur = conn.cursor()
                        cur.execute(sql)
                        conn.commit()
                        cur.close()
                        conn.close()
                        print(f"  ✅ Completed: {filename}")
                    else:
                        print(f"  ⚠️  SUPABASE_CONNECTION not set, skipping DDL migration")
                        print(f"  💡 Please run {filename} manually in Supabase SQL Editor")
                except ImportError:
                    print(f"  ⚠️  psycopg2 not available, please run {filename} in Supabase SQL Editor")
                except Exception as e:
                    if 'already exists' in str(e).lower():
                        print(f"  ⚠️  Already exists (OK): {str(e)[:80]}")
                    else:
                        print(f"  ❌ Error: {str(e)[:100]}")
                        raise
        
        print("\n✅ Migrations completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_super_user(email):
    """Setup super user"""
    print(f"\n🔐 Setting up Super User: {email}")
    print("=" * 60)
    
    try:
        from app.supabase_client import init_supabase
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        supabase = init_supabase(url, key)
        
        # Get user from auth (we'll need the user ID)
        print("📧 Looking for user in Supabase Auth...")
        print("   (If user doesn't exist, create it in Supabase Dashboard → Authentication)")
        
        # Try to get user ID - we'll need to query app_users or ask user
        user_id_input = input(f"\nEnter your Supabase User ID (UUID) for {email}, or press Enter to skip: ").strip()
        
        if not user_id_input:
            print("⚠️  Skipping super user setup. You can run this later with:")
            print(f"   python scripts/setup_super_user.py {email}")
            return False
        
        # Check if app_user exists
        app_user_response = supabase.table('app_users').select('*').eq('supabase_user_id', user_id_input).execute()
        
        if app_user_response.data:
            user_id = app_user_response.data[0]['id']
            print(f"📝 Updating existing user...")
            supabase.table('app_users').update({
                'is_super_user': True,
                'is_industry_admin': True
            }).eq('id', user_id).execute()
        else:
            print(f"📝 Creating new app user...")
            insert_response = supabase.table('app_users').insert({
                'supabase_user_id': user_id_input,
                'email': email,
                'is_super_user': True,
                'is_industry_admin': True
            }).execute()
            if not insert_response.data:
                print("❌ Failed to create app user")
                return False
            user_id = insert_response.data[0]['id']
        
        # Grant all permissions
        print("\n🔑 Granting all permissions...")
        use_cases = supabase.table('use_cases').select('id, code').execute()
        
        for uc in use_cases.data:
            existing = supabase.table('user_permissions').select('id').eq(
                'user_id', user_id
            ).eq('use_case_id', uc['id']).is_('industry_id', 'null').execute()
            
            if not existing.data:
                supabase.table('user_permissions').insert({
                    'user_id': user_id,
                    'use_case_id': uc['id'],
                    'industry_id': None,
                    'granted_by': user_id
                }).execute()
                print(f"  ✅ {uc['code']}")
        
        print("\n✅ Super user setup complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    email = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not email:
        print("Usage: python setup_complete.py <your-email>")
        print("\nExample: python setup_complete.py admin@example.com")
        sys.exit(1)
    
    print("=" * 60)
    print("PROJECT VANI - COMPLETE SETUP")
    print("=" * 60)
    
    # Run migrations
    if not run_migrations():
        print("\n⚠️  Migrations had issues. Please check Supabase SQL Editor.")
    
    # Setup super user
    setup_super_user(email)
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print(f"💡 Login at: http://localhost:5000/login")
    print("=" * 60)

if __name__ == '__main__':
    main()



