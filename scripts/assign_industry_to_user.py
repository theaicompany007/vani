"""
Script to assign an industry to a user (adds to user_industries table).

Usage:
    python scripts/assign_industry_to_user.py user@example.com "FMCG" [--default]
    python scripts/assign_industry_to_user.py user@example.com --industry-id <uuid> [--default]
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

def assign_industry_to_user(email: str, industry_name: str = None, industry_id: str = None, is_default: bool = False):
    """Assign an industry to a user via user_industries table"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY required in .env.local")
        return False
    
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    try:
        # Step 1: Find the user by email
        print(f"\n🔍 Looking up user: {email}")
        user_response = requests.get(
            f"{supabase_url}/rest/v1/app_users?email=eq.{email}&select=id,email",
            headers=headers
        )
        
        if not user_response.ok:
            print(f"❌ Error looking up user: {user_response.status_code} - {user_response.text}")
            return False
        
        users = user_response.json()
        if not users:
            print(f"❌ User not found: {email}")
            return False
        
        user = users[0]
        user_id = user['id']
        print(f"✅ Found user: {user.get('email', email)} (ID: {user_id})")
        
        # Step 2: Get or find industry
        industry_uuid = None
        if industry_id:
            industry_uuid = industry_id
            print(f"📋 Using provided industry ID: {industry_uuid}")
        elif industry_name:
            print(f"🔍 Looking up industry: {industry_name}")
            industry_response = requests.get(
                f"{supabase_url}/rest/v1/industries?name=eq.{industry_name}&select=id,name",
                headers=headers
            )
            
            if industry_response.ok:
                industries = industry_response.json()
                if industries:
                    industry_uuid = industries[0]['id']
                    print(f"✅ Found industry: {industries[0]['name']} (ID: {industry_uuid})")
                else:
                    print(f"❌ Industry not found: {industry_name}")
                    return False
            else:
                print(f"❌ Error looking up industry: {industry_response.status_code}")
                return False
        else:
            print("❌ Error: Either industry_name or industry_id must be provided")
            return False
        
        # Step 3: Check if user_industries table exists
        check_table = requests.get(
            f"{supabase_url}/rest/v1/user_industries?limit=1",
            headers=headers
        )
        
        if check_table.status_code == 404 or 'PGRST205' in check_table.text:
            print("⚠️  user_industries table does not exist. Run migration 014 first.")
            print("   Falling back to legacy industry_id assignment...")
            
            # Fallback to legacy method
            update_data = {
                'industry_id': industry_uuid,
                'active_industry_id': industry_uuid
            }
            if is_default:
                update_data['default_industry_id'] = industry_uuid
            
            update_response = requests.patch(
                f"{supabase_url}/rest/v1/app_users?id=eq.{user_id}",
                headers=headers,
                json=update_data
            )
            
            if update_response.status_code in [200, 204]:
                print(f"✅ Assigned industry using legacy method")
                return True
            else:
                print(f"❌ Error: {update_response.status_code} - {update_response.text}")
                return False
        
        # Step 4: Add to user_industries table
        print(f"\n🔧 Assigning industry to user...")
        
        # Check if already assigned
        existing_check = requests.get(
            f"{supabase_url}/rest/v1/user_industries?user_id=eq.{user_id}&industry_id=eq.{industry_uuid}&select=id",
            headers=headers
        )
        
        if existing_check.ok and existing_check.json():
            print(f"⚠️  Industry already assigned. Updating...")
            existing_id = existing_check.json()[0]['id']
            update_data = {'is_default': is_default}
            update_response = requests.patch(
                f"{supabase_url}/rest/v1/user_industries?id=eq.{existing_id}",
                headers=headers,
                json=update_data
            )
        else:
            # Insert new assignment
            insert_data = {
                'user_id': user_id,
                'industry_id': industry_uuid,
                'is_default': is_default
            }
            update_response = requests.post(
                f"{supabase_url}/rest/v1/user_industries",
                headers=headers,
                json=insert_data
            )
        
        if update_response.status_code in [200, 201, 204]:
            print(f"✅ Successfully assigned industry!")
            print(f"   - industry_id: {industry_uuid}")
            print(f"   - is_default: {is_default}")
            return True
        else:
            print(f"❌ Error: {update_response.status_code} - {update_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python scripts/assign_industry_to_user.py <email> <industry_name> [--default]")
        print("   or: python scripts/assign_industry_to_user.py <email> --industry-id <uuid> [--default]")
        print("\nExample:")
        print('  python scripts/assign_industry_to_user.py raaj007@gmail.com "FMCG" --default')
        print('  python scripts/assign_industry_to_user.py raaj007@gmail.com --industry-id 123e4567-e89b-12d3-a456-426614174000 --default')
        sys.exit(1)
    
    email = sys.argv[1]
    is_default = '--default' in sys.argv
    
    if '--industry-id' in sys.argv:
        idx = sys.argv.index('--industry-id')
        if idx + 1 < len(sys.argv):
            industry_id = sys.argv[idx + 1]
            success = assign_industry_to_user(email, industry_id=industry_id, is_default=is_default)
        else:
            print("❌ Error: --industry-id requires a UUID value")
            sys.exit(1)
    else:
        industry_name = sys.argv[2]
        success = assign_industry_to_user(email, industry_name=industry_name, is_default=is_default)
    
    if success:
        print("\n✅ Industry assignment complete!")
        sys.exit(0)
    else:
        print("\n❌ Failed to assign industry")
        sys.exit(1)












