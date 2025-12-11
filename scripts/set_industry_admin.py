"""
Script to set a user as industry admin and assign them to a specific industry.

Usage:
    python scripts/set_industry_admin.py user@example.com "FMCG"
    python scripts/set_industry_admin.py user@example.com "Food & Beverages" --industry-id <uuid>
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

def set_industry_admin(email: str, industry_name: str = None, industry_id: str = None):
    """Set a user as industry admin and assign them to an industry"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY required in .env.local")
        return False
    
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Step 1: Find the user by email
        print(f"\n🔍 Looking up user: {email}")
        user_response = requests.get(
            f"{supabase_url}/rest/v1/app_users?email=eq.{email}&select=*",
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
        print(f"✅ Found user: {user.get('name', email)} (ID: {user_id})")
        
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
                    print("\nAvailable industries:")
                    list_response = requests.get(
                        f"{supabase_url}/rest/v1/industries?select=id,name&order=name",
                        headers=headers
                    )
                    if list_response.ok:
                        for ind in list_response.json():
                            print(f"  - {ind['name']} (ID: {ind['id']})")
                    return False
            else:
                print(f"❌ Error looking up industry: {industry_response.status_code}")
                return False
        else:
            print("❌ Error: Either industry_name or industry_id must be provided")
            return False
        
        # Step 3: Update user to be industry admin with assigned industry
        print(f"\n🔧 Setting user as industry admin for industry: {industry_uuid}")
        update_data = {
            'is_industry_admin': True,
            'industry_id': industry_uuid,
            'active_industry_id': industry_uuid,  # Also set as active industry
            'default_industry_id': industry_uuid  # Set as default industry
        }
        
        # Also add to user_industries table if it exists
        try:
            user_industries_check = requests.get(
                f"{supabase_url}/rest/v1/user_industries?user_id=eq.{user_id}&industry_id=eq.{industry_uuid}&select=id",
                headers=headers
            )
            if user_industries_check.status_code == 200 and not user_industries_check.json():
                # Add to user_industries table
                user_industries_data = {
                    'user_id': user_id,
                    'industry_id': industry_uuid,
                    'is_default': True
                }
                user_industries_response = requests.post(
                    f"{supabase_url}/rest/v1/user_industries",
                    headers=headers,
                    json=user_industries_data
                )
                if user_industries_response.status_code in [200, 201]:
                    print("   ✅ Added to user_industries table")
        except Exception as e:
            # Table might not exist yet (migration not run)
            print(f"   ⚠️  Could not update user_industries table (may not exist): {e}")
        
        update_response = requests.patch(
            f"{supabase_url}/rest/v1/app_users?id=eq.{user_id}",
            headers=headers,
            json=update_data
        )
        
        if not update_response.ok:
            print(f"❌ Error updating user: {update_response.status_code}")
            print(f"   Response: {update_response.text}")
            return False
        
        # Supabase PATCH returns empty body on success, so we need to fetch the updated user
        # Check if response has content
        response_text = update_response.text.strip()
        if response_text:
            try:
                updated_user = update_response.json()
                if updated_user:
                    print(f"✅ Successfully set user as industry admin!")
                    print(f"   - is_industry_admin: True")
                    print(f"   - industry_id: {industry_uuid}")
                    print(f"   - active_industry_id: {industry_uuid}")
                    return True
            except:
                pass
        
        # If no response body, verify by fetching the updated user
        print("   Verifying update...")
        verify_response = requests.get(
            f"{supabase_url}/rest/v1/app_users?id=eq.{user_id}&select=id,email,is_industry_admin,industry_id,active_industry_id",
            headers=headers
        )
        
        if verify_response.ok:
            verified_users = verify_response.json()
            if verified_users:
                verified_user = verified_users[0]
                if verified_user.get('is_industry_admin') and verified_user.get('industry_id') == industry_uuid:
                    print(f"✅ Successfully set user as industry admin!")
                    print(f"   - is_industry_admin: {verified_user.get('is_industry_admin')}")
                    print(f"   - industry_id: {verified_user.get('industry_id')}")
                    print(f"   - active_industry_id: {verified_user.get('active_industry_id')}")
                    return True
                else:
                    print(f"⚠️  Update may have failed. Current state:")
                    print(f"   - is_industry_admin: {verified_user.get('is_industry_admin')}")
                    print(f"   - industry_id: {verified_user.get('industry_id')}")
                    print(f"   - active_industry_id: {verified_user.get('active_industry_id')}")
                    return False
            else:
                print("❌ Could not verify update - user not found")
                return False
        else:
            print(f"⚠️  Update may have succeeded but verification failed: {verify_response.status_code}")
            print(f"   Response: {verify_response.text}")
            # Assume success if status was 204 or 200
            if update_response.status_code in [200, 204]:
                print("✅ Update completed (status code indicates success)")
                return True
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python scripts/set_industry_admin.py <email> <industry_name>")
        print("   or: python scripts/set_industry_admin.py <email> --industry-id <uuid>")
        print("\nExample:")
        print('  python scripts/set_industry_admin.py raaj007@gmail.com "FMCG"')
        print('  python scripts/set_industry_admin.py raaj007@gmail.com --industry-id 123e4567-e89b-12d3-a456-426614174000')
        sys.exit(1)
    
    email = sys.argv[1]
    
    if '--industry-id' in sys.argv:
        idx = sys.argv.index('--industry-id')
        if idx + 1 < len(sys.argv):
            industry_id = sys.argv[idx + 1]
            success = set_industry_admin(email, industry_id=industry_id)
        else:
            print("❌ Error: --industry-id requires a UUID value")
            sys.exit(1)
    else:
        industry_name = sys.argv[2]
        success = set_industry_admin(email, industry_name=industry_name)
    
    if success:
        print("\n✅ Industry admin assignment complete!")
        sys.exit(0)
    else:
        print("\n❌ Failed to set industry admin")
        sys.exit(1)

