"""Check user permissions"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
basedir = Path(__file__).parent.parent
sys.path.insert(0, str(basedir))

# Load environment
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

from app.supabase_client import init_supabase

def check_user_permissions(email):
    """Check permissions for a user"""
    supabase = init_supabase(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
    
    # Find user
    user_result = supabase.table('app_users').select('*').eq('email', email).execute()
    if not user_result.data:
        print(f"User {email} not found")
        return
    
    user = user_result.data[0]
    print(f"\n{'='*70}")
    print(f"USER: {user['email']}")
    print(f"{'='*70}")
    print(f"  ID: {user['id']}")
    print(f"  Name: {user.get('name', 'N/A')}")
    print(f"  Super User: {user.get('is_super_user', False)}")
    print(f"  Industry Admin: {user.get('is_industry_admin', False)}")
    print(f"  Default Industry: {user.get('default_industry_id', 'None')}")
    
    # Get all use cases
    use_cases_result = supabase.table('use_cases').select('*').execute()
    all_use_cases = {uc['id']: uc for uc in use_cases_result.data}
    
    # Get user permissions
    perms_result = supabase.table('user_permissions').select('*').eq('user_id', user['id']).execute()
    user_perms = perms_result.data
    
    print(f"\n{'='*70}")
    print(f"PERMISSIONS ({len(user_perms)} granted)")
    print(f"{'='*70}")
    
    if user_perms:
        for perm in user_perms:
            uc = all_use_cases.get(perm['use_case_id'])
            if uc:
                industry_info = f" (Industry: {perm.get('industry_id', 'Global')})" if perm.get('industry_id') else " (Global)"
                print(f"  [OK] {uc['code']}: {uc['name']}{industry_info}")
            else:
                print(f"  [OK] Unknown use case: {perm['use_case_id']}")
    else:
        print("  (No permissions granted)")
    
    # Show missing permissions
    granted_use_case_ids = set(perm['use_case_id'] for perm in user_perms if not perm.get('industry_id'))
    missing_use_cases = [uc for uc_id, uc in all_use_cases.items() if uc_id not in granted_use_case_ids]
    
    if missing_use_cases:
        print(f"\n{'='*70}")
        print(f"MISSING PERMISSIONS ({len(missing_use_cases)})")
        print(f"{'='*70}")
        for uc in missing_use_cases:
            print(f"  [X] {uc['code']}: {uc['name']}")
        
        print(f"\nTo grant all permissions:")
        print(f"  python scripts/grant_default_permissions.py {email} --grant")
    
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_user_permissions.py <email>")
        print("\nExample:")
        print("  python scripts/check_user_permissions.py raaj007@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    check_user_permissions(email)

