"""Setup super user in database"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

def get_supabase_client():
    """Get Supabase client"""
    from app.supabase_client import init_supabase
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
    
    return init_supabase(url, key)

def setup_super_user(email: str = None):
    """Setup super user - either from email or create new"""
    print("🔐 Setting up Super User...")
    print("=" * 60)
    
    try:
        supabase = get_supabase_client()
        
        # If email provided, find user
        if email:
            print(f"📧 Looking for user: {email}")
            
            # Get user from Supabase Auth
            try:
                # Try to get user by email
                auth_response = supabase.auth.admin.list_users()
                
                supabase_user = None
                if hasattr(auth_response, 'users'):
                    for user in auth_response.users:
                        if user.email == email:
                            supabase_user = user
                            break
                
                if not supabase_user:
                    print(f"❌ User {email} not found in Supabase Auth")
                    print("   Please create the user in Supabase Dashboard → Authentication first")
                    print("   Or provide your Supabase user ID directly")
                    return False
                
                print(f"✅ Found user: {supabase_user.email} (ID: {supabase_user.id})")
                
            except Exception as e:
                print(f"⚠️  Could not list auth users: {e}")
                print("   Will try to create app_user directly...")
                supabase_user_id = input("Enter your Supabase User ID (UUID): ").strip()
                if not supabase_user_id:
                    return False
                supabase_user = type('obj', (object,), {'id': supabase_user_id, 'email': email})()
            
            # Check if app_user exists
            app_user_response = supabase.table('app_users').select('*').eq('supabase_user_id', supabase_user.id).execute()
            
            if app_user_response.data:
                # Update existing user
                app_user = app_user_response.data[0]
                print(f"📝 Updating existing app user: {app_user['id']}")
                
                update_response = supabase.table('app_users').update({
                    'is_super_user': True,
                    'is_industry_admin': True,
                    'email': email
                }).eq('id', app_user['id']).execute()
                
                print(f"✅ Updated user to super user")
                user_id = app_user['id']
            else:
                # Create new app_user
                print("📝 Creating new app user...")
                
                insert_response = supabase.table('app_users').insert({
                    'supabase_user_id': supabase_user.id,
                    'email': email,
                    'name': '',
                    'is_super_user': True,
                    'is_industry_admin': True
                }).execute()
                
                if not insert_response.data:
                    print("❌ Failed to create app user")
                    return False
                
                print(f"✅ Created app user: {insert_response.data[0]['id']}")
                user_id = insert_response.data[0]['id']
            
            # Grant all use cases
            print("\n🔑 Granting all use case permissions...")
            
            use_cases_response = supabase.table('use_cases').select('id, code').execute()
            
            if not use_cases_response.data:
                print("⚠️  No use cases found. Make sure migrations have been run.")
                return False
            
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
                else:
                    print(f"  ⚠️  Already has: {use_case['code']}")
            
            print("\n" + "=" * 60)
            print("✅ Super user setup complete!")
            print(f"   Email: {email}")
            print(f"   User ID: {user_id}")
            print(f"   Permissions: All use cases granted")
            print(f"\n💡 You can now login at: http://localhost:5000/login")
            
            return True
            
        else:
            print("💡 To set a user as super user, provide their email:")
            print(f"   python {sys.argv[0]} your@email.com")
            print("\n📋 Or check Supabase Dashboard → Authentication for user emails")
            
            return False
            
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    email = sys.argv[1] if len(sys.argv) > 1 else None
    
    if email:
        success = setup_super_user(email)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python setup_super_user.py <email>")
        print("\nExample: python setup_super_user.py admin@example.com")
        print("\nOr run without email to see instructions:")
        setup_super_user()

if __name__ == '__main__':
    main()
