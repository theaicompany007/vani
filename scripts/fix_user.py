"""Script to fix or create a user in app_users table"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

# Patch httpx.Client for Supabase compatibility
try:
    from app.supabase_client import fix_httpx_client_proxy_issue
    fix_httpx_client_proxy_issue()
except Exception as e:
    print(f"⚠️  Could not apply httpx patch: {e}")

def fix_user(email, password=None, is_super_user=False, is_industry_admin=False):
    """Fix or create a user"""
    print(f"\n🔧 Fixing/Creating User: {email}")
    print("=" * 60)
    
    try:
        from app.supabase_client import init_supabase
        
        url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_KEY')
        anon_key = os.getenv('SUPABASE_KEY')
        
        if not url:
            print("❌ SUPABASE_URL not found in .env.local")
            return False
        
        # Use service key for admin operations
        supabase = init_supabase(url, service_key or anon_key)
        
        # Check if user exists in app_users
        app_user_response = supabase.table('app_users').select('*').eq('email', email).limit(1).execute()
        
        if app_user_response.data:
            # User exists in app_users
            app_user = app_user_response.data[0]
            print(f"✅ User found in app_users: {app_user['id']}")
            print(f"   Current is_super_user: {app_user.get('is_super_user', False)}")
            print(f"   Current is_industry_admin: {app_user.get('is_industry_admin', False)}")
            
            # Update if needed
            updates = {}
            if is_super_user is not None and app_user.get('is_super_user') != is_super_user:
                updates['is_super_user'] = is_super_user
            if is_industry_admin is not None and app_user.get('is_industry_admin') != is_industry_admin:
                updates['is_industry_admin'] = is_industry_admin
            
            if updates:
                supabase.table('app_users').update(updates).eq('id', app_user['id']).execute()
                print(f"✅ Updated user: {updates}")
            else:
                print("ℹ️  No updates needed")
            
            # Check and grant default permissions if missing
            try:
                permissions_check = supabase.table('user_permissions').select('id').eq('user_id', app_user['id']).limit(1).execute()
                if not permissions_check.data:
                    # No permissions found, grant all default use cases
                    print("⚠️  User has no permissions, granting default use cases...")
                    use_cases_response = supabase.table('use_cases').select('id').execute()
                    if use_cases_response.data:
                        permissions_to_insert = []
                        for uc in use_cases_response.data:
                            permissions_to_insert.append({
                                'user_id': app_user['id'],
                                'use_case_id': uc['id'],
                                'industry_id': None
                            })
                        
                        if permissions_to_insert:
                            granted_count = 0
                            for perm in permissions_to_insert:
                                try:
                                    supabase.table('user_permissions').insert(perm).execute()
                                    granted_count += 1
                                except Exception as perm_error:
                                    # Permission might already exist, skip
                                    pass
                            print(f"✅ Granted {granted_count}/{len(permissions_to_insert)} default permissions")
            except Exception as perm_error:
                print(f"⚠️  Could not check/grant permissions: {perm_error}")
            
            # Check Supabase Auth
            try:
                if service_key:
                    # Use admin API to check auth user
                    auth_user = supabase.auth.admin.get_user_by_email(email)
                    if auth_user and auth_user.user:
                        print(f"✅ User exists in Supabase Auth: {auth_user.user.id}")
                        if password:
                            # Reset password
                            supabase.auth.admin.update_user_by_id(
                                auth_user.user.id,
                                {'password': password}
                            )
                            print(f"✅ Password reset for {email}")
                    else:
                        print("⚠️  User not found in Supabase Auth")
                        if password:
                            # Create auth user
                            new_user = supabase.auth.admin.create_user({
                                'email': email,
                                'password': password,
                                'email_confirm': True
                            })
                            if new_user and new_user.user:
                                # Update app_user with correct supabase_user_id
                                supabase.table('app_users').update({
                                    'supabase_user_id': new_user.user.id
                                }).eq('id', app_user['id']).execute()
                                print(f"✅ Created auth user and linked to app_user")
                else:
                    print("⚠️  SUPABASE_SERVICE_KEY not found - cannot check/update Auth user")
            except Exception as auth_error:
                print(f"⚠️  Could not check Supabase Auth: {auth_error}")
            
            return True
        else:
            # User doesn't exist in app_users
            print("⚠️  User not found in app_users table")
            
            # Check Supabase Auth
            supabase_user_id = None
            try:
                if service_key:
                    auth_user = supabase.auth.admin.get_user_by_email(email)
                    if auth_user and auth_user.user:
                        supabase_user_id = auth_user.user.id
                        print(f"✅ Found user in Supabase Auth: {supabase_user_id}")
                    else:
                        print("⚠️  User not found in Supabase Auth")
                        if password:
                            # Create auth user
                            new_user = supabase.auth.admin.create_user({
                                'email': email,
                                'password': password,
                                'email_confirm': True
                            })
                            if new_user and new_user.user:
                                supabase_user_id = new_user.user.id
                                print(f"✅ Created user in Supabase Auth: {supabase_user_id}")
                else:
                    print("⚠️  SUPABASE_SERVICE_KEY not found - cannot check Auth")
                    if not password:
                        print("❌ Cannot create user without password and service key")
                        return False
            except Exception as auth_error:
                print(f"⚠️  Auth check failed: {auth_error}")
                if not password:
                    print("❌ Cannot create user without password")
                    return False
            
            if not supabase_user_id:
                print("❌ Cannot create app_user without Supabase user ID")
                return False
            
            # Create app_user
            insert_data = {
                'supabase_user_id': supabase_user_id,
                'email': email,
                'name': email.split('@')[0],
                'is_super_user': bool(is_super_user),
                'is_industry_admin': bool(is_industry_admin)
            }
            # default_industry_id will be set later if industry is assigned
            insert_response = supabase.table('app_users').insert(insert_data).execute()
            
            if insert_response.data:
                user_id = insert_response.data[0]['id']
                print(f"✅ Created app_user: {user_id}")
                
                # Auto-grant default permissions (all use cases)
                try:
                    use_cases_response = supabase.table('use_cases').select('id').execute()
                    if use_cases_response.data:
                        permissions_to_insert = []
                        for uc in use_cases_response.data:
                            permissions_to_insert.append({
                                'user_id': user_id,
                                'use_case_id': uc['id'],
                                'industry_id': None
                            })
                        
                        if permissions_to_insert:
                            granted_count = 0
                            for perm in permissions_to_insert:
                                try:
                                    supabase.table('user_permissions').insert(perm).execute()
                                    granted_count += 1
                                except Exception as perm_error:
                                    # Permission might already exist, skip
                                    pass
                            print(f"✅ Auto-granted {granted_count}/{len(permissions_to_insert)} default permissions")
                except Exception as perm_error:
                    print(f"⚠️  Could not auto-grant permissions: {perm_error}")
                    print("   You can grant them manually with: python scripts/grant_default_permissions.py")
                
                return True
            else:
                print("❌ Failed to create app_user")
                return False
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/fix_user.py <email> [password] [--super-user] [--industry-admin]")
        print("\nExample:")
        print("  python scripts/fix_user.py raaj007@gmail.com mypassword --super-user")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    is_super_user = '--super-user' in sys.argv
    is_industry_admin = '--industry-admin' in sys.argv
    
    if fix_user(email, password, is_super_user, is_industry_admin):
        print("\n" + "=" * 60)
        print("✅ User fixed/created successfully!")
        print(f"   Email: {email}")
        print(f"   Super User: {is_super_user}")
        print(f"   Industry Admin: {is_industry_admin}")
        print("\n💡 User can now login at: http://localhost:5000/login")
        print("=" * 60)
    else:
        print("\n❌ Failed to fix/create user")
        sys.exit(1)

if __name__ == '__main__':
    main()




