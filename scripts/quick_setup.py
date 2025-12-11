"""Quick setup: Run migrations and create super user with provided credentials"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

def run_migrations_via_sql():
    """Run migrations using direct SQL execution"""
    print("🚀 Running Database Migrations...")
    print("=" * 60)
    
    try:
        import psycopg2
        
        conn_string = os.getenv('SUPABASE_CONNECTION')
        if not conn_string:
            print("❌ SUPABASE_CONNECTION not found in .env.local")
            print("💡 Please run migrations manually in Supabase SQL Editor")
            return False
        
        conn = psycopg2.connect(conn_string)
        print("✅ Connected to Supabase database")
        
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
                
                # Execute SQL
                cur = conn.cursor()
                try:
                    cur.execute(sql)
                    conn.commit()
                    print(f"  ✅ Completed: {filename}")
                except Exception as e:
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        print(f"  ⚠️  Already exists (OK): {str(e)[:80]}")
                        conn.rollback()
                    else:
                        print(f"  ❌ Error: {str(e)[:100]}")
                        conn.rollback()
                        raise
                finally:
                    cur.close()
        
        conn.close()
        print("\n✅ All migrations completed!")
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Installing...")
        os.system(f"{sys.executable} -m pip install psycopg2-binary")
        return run_migrations_via_sql()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_super_user(email, supabase_user_id):
    """Setup super user with provided credentials"""
    print(f"\n🔐 Setting up Super User...")
    print("=" * 60)
    print(f"   Email: {email}")
    print(f"   User ID: {supabase_user_id}")
    
    try:
        from app.supabase_client import init_supabase
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        
        supabase = init_supabase(url, key)
        
        # Check if app_user exists
        app_user_response = supabase.table('app_users').select('*').eq('supabase_user_id', supabase_user_id).execute()
        
        if app_user_response.data:
            # Update existing user
            user_id = app_user_response.data[0]['id']
            print(f"📝 Updating existing app user: {user_id}")
            
            supabase.table('app_users').update({
                'is_super_user': True,
                'is_industry_admin': True,
                'email': email
            }).eq('id', user_id).execute()
            
            print("✅ Updated to super user")
        else:
            # Create new app_user
            print("📝 Creating new app user...")
            
            insert_response = supabase.table('app_users').insert({
                'supabase_user_id': supabase_user_id,
                'email': email,
                'name': '',
                'is_super_user': True,
                'is_industry_admin': True
            }).execute()
            
            if not insert_response.data:
                print("❌ Failed to create app user")
                return False
            
            user_id = insert_response.data[0]['id']
            print(f"✅ Created app user: {user_id}")
        
        # Grant all use cases
        print("\n🔑 Granting all use case permissions...")
        
        use_cases_response = supabase.table('use_cases').select('id, code').execute()
        
        if not use_cases_response.data:
            print("⚠️  No use cases found. Make sure migrations ran successfully.")
            return False
        
        granted_count = 0
        for use_case in use_cases_response.data:
            # Check if permission already exists
            existing = supabase.table('user_permissions').select('id').eq(
                'user_id', user_id
            ).eq('use_case_id', use_case['id']).is_('industry_id', 'null').execute()
            
            if not existing.data:
                supabase.table('user_permissions').insert({
                    'user_id': user_id,
                    'use_case_id': use_case['id'],
                    'industry_id': None,  # NULL = all industries
                    'granted_by': user_id
                }).execute()
                print(f"  ✅ Granted: {use_case['code']}")
                granted_count += 1
            else:
                print(f"  ⚠️  Already has: {use_case['code']}")
        
        print(f"\n✅ Granted {granted_count} new permissions")
        print("\n" + "=" * 60)
        print("✅ Super user setup complete!")
        print(f"   Email: {email}")
        print(f"   User ID: {user_id}")
        print(f"   Permissions: All use cases")
        print(f"\n💡 You can now login at: http://localhost:5000/login")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    email = "rajvins@theaicompany.co"
    supabase_user_id = "eb98e4aa-96cc-48d1-ba60-96cc541c4fdf"
    
    print("=" * 60)
    print("PROJECT VANI - QUICK SETUP")
    print("=" * 60)
    
    # Run migrations
    migrations_ok = run_migrations_via_sql()
    
    if not migrations_ok:
        print("\n⚠️  Migrations had issues. Continuing with super user setup...")
    
    # Setup super user
    setup_ok = setup_super_user(email, supabase_user_id)
    
    if setup_ok:
        print("\n🎉 Setup Complete! You're ready to go!")
    else:
        print("\n⚠️  Setup had issues. Check errors above.")

if __name__ == '__main__':
    main()



