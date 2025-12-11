import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

from app.supabase_client import init_supabase

email = "rajvins@theaicompany.co"
supabase_user_id = "eb98e4aa-96cc-48d1-ba60-96cc541c4fdf"

print("=" * 60)
print("PROJECT VANI - SETUP")
print("=" * 60)

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

if not url or not key:
    print("❌ SUPABASE_URL and SUPABASE_SERVICE_KEY required")
    exit(1)

supabase = init_supabase(url, key)

# Check/create app_user
print(f"\n🔐 Setting up: {email}")
app_user_response = supabase.table('app_users').select('*').eq('supabase_user_id', supabase_user_id).execute()

if app_user_response.data:
    user_id = app_user_response.data[0]['id']
    print(f"📝 Updating user: {user_id}")
    supabase.table('app_users').update({
        'is_super_user': True,
        'is_industry_admin': True,
        'email': email
    }).eq('id', user_id).execute()
    print("✅ Updated to super user")
else:
    print("📝 Creating new app user...")
    insert_response = supabase.table('app_users').insert({
        'supabase_user_id': supabase_user_id,
        'email': email,
        'is_super_user': True,
        'is_industry_admin': True
    }).execute()
    if insert_response.data:
        user_id = insert_response.data[0]['id']
        print(f"✅ Created: {user_id}")
    else:
        print("❌ Failed")
        exit(1)

# Grant permissions
print("\n🔑 Granting permissions...")
use_cases = supabase.table('use_cases').select('id, code').execute()

if not use_cases.data:
    print("⚠️  No use cases found. Run migrations first!")
    exit(1)

for uc in use_cases.data:
    existing = supabase.table('user_permissions').select('id').eq('user_id', user_id).eq('use_case_id', uc['id']).is_('industry_id', 'null').execute()
    if not existing.data:
        supabase.table('user_permissions').insert({
            'user_id': user_id,
            'use_case_id': uc['id'],
            'industry_id': None,
            'granted_by': user_id
        }).execute()
        print(f"  ✅ {uc['code']}")

print("\n✅ Setup complete!")
print(f"💡 Login at: http://localhost:5000/login")



