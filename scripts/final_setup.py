"""Final setup: Run migrations and create super user"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

# Run migrations
print("🚀 Running Migrations...")
print("=" * 60)

try:
    import psycopg2
    conn_string = os.getenv('SUPABASE_CONNECTION')
    
    if not conn_string:
        print("❌ SUPABASE_CONNECTION not found")
        print("💡 Please run migrations manually in Supabase SQL Editor")
        sys.exit(1)
    
    conn = psycopg2.connect(conn_string)
    print("✅ Connected to database")
    
    migrations = [
        '002_industries_tenants.sql',
        '003_auth_permissions.sql',
        '004_pitch_storage.sql',
        '005_add_industry_to_tables.sql'
    ]
    
    for filename in migrations:
        file_path = basedir / 'app' / 'migrations' / filename
        if file_path.exists():
            print(f"\n📄 {filename}")
            with open(file_path, 'r') as f:
                sql = f.read()
            cur = conn.cursor()
            try:
                cur.execute(sql)
                conn.commit()
                print("  ✅ Done")
            except Exception as e:
                if 'already exists' in str(e).lower():
                    print(f"  ⚠️  Already exists")
                    conn.rollback()
                else:
                    print(f"  ❌ {str(e)[:100]}")
                    conn.rollback()
            cur.close()
    
    conn.close()
    print("\n✅ Migrations complete!")
    
except Exception as e:
    print(f"❌ Migration error: {e}")
    import traceback
    traceback.print_exc()

# Setup super user
print("\n🔐 Setting up Super User...")
print("=" * 60)

email = "rajvins@theaicompany.co"
user_id = "eb98e4aa-96cc-48d1-ba60-96cc541c4fdf"

try:
    from app.supabase_client import init_supabase
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    supabase = init_supabase(url, key)
    
    # Create/update app_user
    app_user = supabase.table('app_users').select('*').eq('supabase_user_id', user_id).execute()
    
    if app_user.data:
        app_user_id = app_user.data[0]['id']
        supabase.table('app_users').update({
            'is_super_user': True,
            'is_industry_admin': True,
            'email': email
        }).eq('id', app_user_id).execute()
        print(f"✅ Updated user: {app_user_id}")
    else:
        result = supabase.table('app_users').insert({
            'supabase_user_id': user_id,
            'email': email,
            'is_super_user': True,
            'is_industry_admin': True
        }).execute()
        app_user_id = result.data[0]['id']
        print(f"✅ Created user: {app_user_id}")
    
    # Grant permissions
    print("\n🔑 Granting permissions...")
    use_cases = supabase.table('use_cases').select('id, code').execute()
    
    for uc in use_cases.data:
        existing = supabase.table('user_permissions').select('id').eq('user_id', app_user_id).eq('use_case_id', uc['id']).is_('industry_id', 'null').execute()
        if not existing.data:
            supabase.table('user_permissions').insert({
                'user_id': app_user_id,
                'use_case_id': uc['id'],
                'industry_id': None,
                'granted_by': app_user_id
            }).execute()
            print(f"  ✅ {uc['code']}")
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print(f"💡 Login at: http://localhost:5000/login")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Setup error: {e}")
    import traceback
    traceback.print_exc()



