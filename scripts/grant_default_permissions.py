"""Script to grant/revoke use case permissions for a user"""
import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
dot_env_path = os.path.join(basedir, '.env')
dot_env_local_path = os.path.join(basedir, '.env.local')
load_dotenv(dot_env_path)
load_dotenv(dot_env_local_path, override=True)

def manage_permissions(email: str, action: str = 'grant', use_case_codes: list = None):
    """
    Grant or revoke use case permissions for a user
    
    Args:
        email: User email address
        action: 'grant', 'revoke', or 'toggle'
        use_case_codes: List of use case codes to manage (None = all use cases)
    """
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_service_key:
            print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env.local")
            return False
        
        # Use REST API directly to avoid client library version issues
        import requests
        
        headers = {
            'apikey': supabase_service_key,
            'Authorization': f'Bearer {supabase_service_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Remove trailing slash
        supabase_url = supabase_url.rstrip('/')
        
        # Find user by email
        user_url = f"{supabase_url}/rest/v1/app_users"
        user_params = {'email': f'eq.{email}', 'select': 'id,email'}
        user_response = requests.get(user_url, headers=headers, params=user_params, timeout=10)
        
        if user_response.status_code != 200 or not user_response.json():
            print(f"ERROR: User with email {email} not found in app_users table")
            print(f"Response: {user_response.status_code} - {user_response.text}")
            return False
        
        user_data = user_response.json()
        if not user_data or len(user_data) == 0:
            print(f"ERROR: User with email {email} not found")
            return False
        
        user_id = user_data[0]['id']
        print(f"Found user: {email} (ID: {user_id})")
        
        # Get all use cases
        use_cases_url = f"{supabase_url}/rest/v1/use_cases"
        use_cases_response = requests.get(use_cases_url, headers=headers, params={'select': 'id,code,name'}, timeout=10)
        
        if use_cases_response.status_code != 200:
            print(f"ERROR: Failed to get use cases. Status: {use_cases_response.status_code}")
            return False
        
        use_cases = use_cases_response.json()
        if not use_cases:
            print("ERROR: No use cases found in database")
            return False
        
        # Filter use cases if specific ones requested
        if use_case_codes:
            requested_codes = set(use_case_codes)
            filtered_use_cases = [uc for uc in use_cases if uc['code'] in requested_codes]
            if not filtered_use_cases:
                print(f"ERROR: None of the requested use cases found: {', '.join(requested_codes)}")
                print(f"Available use cases: {', '.join([uc['code'] for uc in use_cases])}")
                return False
            use_cases = filtered_use_cases
            print(f"Filtered to {len(use_cases)} requested use case(s): {', '.join([uc['code'] for uc in use_cases])}")
        
        print(f"Found {len(use_cases)} use cases:")
        for uc in use_cases:
            print(f"  - {uc['code']}: {uc['name']}")
        
        # Manage permissions (global - industry_id is NULL)
        permissions_url = f"{supabase_url}/rest/v1/user_permissions"
        success_list = []
        skipped_list = []
        failed_list = []
        
        for use_case in use_cases:
            use_case_id = use_case['id']
            use_case_code = use_case['code']
            
            # Check if permission exists
            check_params = {
                'user_id': f'eq.{user_id}',
                'use_case_id': f'eq.{use_case_id}',
                'industry_id': 'is.null',
                'select': 'id'
            }
            existing_response = requests.get(permissions_url, headers=headers, params=check_params, timeout=10)
            permission_exists = existing_response.status_code == 200 and existing_response.json()
            
            if action == 'grant':
                if permission_exists:
                    skipped_list.append(use_case_code)
                    print(f"  [OK] {use_case_code}: Already granted (skipped)")
                else:
                    try:
                        perm_data = {
                            'user_id': str(user_id),
                            'use_case_id': str(use_case_id),
                            'industry_id': None
                        }
                        insert_response = requests.post(permissions_url, headers=headers, json=perm_data, timeout=10)
                        
                        if insert_response.status_code in [200, 201]:
                            success_list.append(use_case_code)
                            print(f"  [OK] {use_case_code}: Granted")
                        else:
                            error_text = insert_response.text[:200]
                            print(f"  [X] {use_case_code}: Failed - {insert_response.status_code} - {error_text}")
                            failed_list.append(use_case_code)
                    except Exception as e:
                        print(f"  [X] {use_case_code}: Failed - {e}")
                        failed_list.append(use_case_code)
            
            elif action == 'revoke':
                if not permission_exists:
                    skipped_list.append(use_case_code)
                    print(f"  [OK] {use_case_code}: Not granted (skipped)")
                else:
                    try:
                        # Get permission ID
                        perm_id = existing_response.json()[0]['id']
                        delete_url = f"{permissions_url}?id=eq.{perm_id}"
                        delete_response = requests.delete(delete_url, headers=headers, timeout=10)
                        
                        if delete_response.status_code in [200, 204]:
                            success_list.append(use_case_code)
                            print(f"  [OK] {use_case_code}: Revoked")
                        else:
                            error_text = delete_response.text[:200]
                            print(f"  [X] {use_case_code}: Failed - {delete_response.status_code} - {error_text}")
                            failed_list.append(use_case_code)
                    except Exception as e:
                        print(f"  [X] {use_case_code}: Failed - {e}")
                        failed_list.append(use_case_code)
            
            elif action == 'toggle':
                if permission_exists:
                    # Revoke it
                    try:
                        perm_id = existing_response.json()[0]['id']
                        delete_url = f"{permissions_url}?id=eq.{perm_id}"
                        delete_response = requests.delete(delete_url, headers=headers, timeout=10)
                        
                        if delete_response.status_code in [200, 204]:
                            success_list.append(use_case_code)
                            print(f"  [OK] {use_case_code}: Revoked (was granted)")
                        else:
                            error_text = delete_response.text[:200]
                            print(f"  [X] {use_case_code}: Failed to revoke - {delete_response.status_code} - {error_text}")
                            failed_list.append(use_case_code)
                    except Exception as e:
                        print(f"  [X] {use_case_code}: Failed to revoke - {e}")
                        failed_list.append(use_case_code)
                else:
                    # Grant it
                    try:
                        perm_data = {
                            'user_id': str(user_id),
                            'use_case_id': str(use_case_id),
                            'industry_id': None
                        }
                        insert_response = requests.post(permissions_url, headers=headers, json=perm_data, timeout=10)
                        
                        if insert_response.status_code in [200, 201]:
                            success_list.append(use_case_code)
                            print(f"  [OK] {use_case_code}: Granted (was not granted)")
                        else:
                            error_text = insert_response.text[:200]
                            print(f"  [X] {use_case_code}: Failed to grant - {insert_response.status_code} - {error_text}")
                            failed_list.append(use_case_code)
                    except Exception as e:
                        print(f"  [X] {use_case_code}: Failed to grant - {e}")
                        failed_list.append(use_case_code)
        
        # Print summary
        action_past = {'grant': 'Granted', 'revoke': 'Revoked', 'toggle': 'Toggled'}.get(action, 'Processed')
        print(f"\nSUMMARY:")
        print(f"  {action_past}: {len(success_list)} permissions")
        if success_list:
            print(f"    {', '.join(success_list)}")
        if skipped_list:
            print(f"  Skipped: {len(skipped_list)} permissions")
            print(f"    {', '.join(skipped_list)}")
        if failed_list:
            print(f"  Failed: {len(failed_list)} permissions")
            print(f"    {', '.join(failed_list)}")
        
        return len(success_list) > 0 or len(skipped_list) > 0
        
    except Exception as e:
        print(f"ERROR: Failed to grant permissions: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Grant, revoke, or toggle use case permissions for a user',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Grant all permissions to a user (includes contact_management, company_management, ai_target_finder)
  python grant_default_permissions.py vikas.goel@blackngreen.com --grant
  
  # Revoke all permissions from a user
  python grant_default_permissions.py vikas.goel@blackngreen.com --revoke
  
  # Toggle (grant if missing, revoke if exists) all permissions
  python grant_default_permissions.py vikas.goel@blackngreen.com --toggle
  
  # Grant specific use cases only
  python grant_default_permissions.py vikas.goel@blackngreen.com --grant --use-cases analytics meetings target_management contact_management company_management ai_target_finder
  
  # Grant only the AI Target Finder use case
  python grant_default_permissions.py vikas.goel@blackngreen.com --grant --use-cases ai_target_finder
  
  # Revoke specific use cases
  python grant_default_permissions.py vikas.goel@blackngreen.com --revoke --use-cases analytics
        """
    )
    
    parser.add_argument('email', help='User email address')
    parser.add_argument('--grant', action='store_true', help='Grant permissions (default if no action specified)')
    parser.add_argument('--revoke', action='store_true', help='Revoke permissions')
    parser.add_argument('--toggle', action='store_true', help='Toggle permissions (grant if missing, revoke if exists)')
    parser.add_argument('--use-cases', nargs='+', help='Specific use case codes to manage (default: all use cases)')
    
    args = parser.parse_args()
    
    # Determine action
    if args.revoke:
        action = 'revoke'
    elif args.toggle:
        action = 'toggle'
    else:
        action = 'grant'  # Default
    
    success = manage_permissions(args.email, action, args.use_cases)
    sys.exit(0 if success else 1)

