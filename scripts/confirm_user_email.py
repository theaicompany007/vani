"""Utility script to confirm user email in Supabase"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
dot_env_path = os.path.join(basedir, '.env')
dot_env_local_path = os.path.join(basedir, '.env.local')
load_dotenv(dot_env_path)
load_dotenv(dot_env_local_path, override=True)

def confirm_user_email(email: str):
    """Confirm a user's email address using Supabase Admin API REST endpoint"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_service_key:
            print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env.local")
            return False
        
        # Remove trailing slash from URL if present
        supabase_url = supabase_url.rstrip('/')
        
        # Use REST API directly to avoid client library issues
        auth_url = f"{supabase_url}/auth/v1/admin/users"
        
        headers = {
            'apikey': supabase_service_key,
            'Authorization': f'Bearer {supabase_service_key}',
            'Content-Type': 'application/json'
        }
        
        # List users to find the one with this email
        print(f"Searching for user with email: {email}")
        response = requests.get(auth_url, headers=headers, params={'per_page': 1000})
        
        if response.status_code != 200:
            print(f"ERROR: Failed to list users. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        users_data = response.json()
        users = users_data.get('users', [])
        
        user_to_confirm = None
        for user in users:
            if user.get('email') and user.get('email').lower() == email.lower():
                user_to_confirm = user
                break
        
        if not user_to_confirm:
            print(f"ERROR: User with email {email} not found")
            print(f"Found {len(users)} users in total")
            return False
        
        user_id = user_to_confirm.get('id')
        if not user_id:
            print(f"ERROR: User found but no ID available")
            return False
        
        print(f"Found user: {user_to_confirm.get('email')} (ID: {user_id})")
        print(f"Current email_confirmed_at: {user_to_confirm.get('email_confirmed_at')}")
        
        # Update user to confirm email
        update_url = f"{supabase_url}/auth/v1/admin/users/{user_id}"
        update_data = {
            'email_confirm': True
        }
        
        update_response = requests.put(update_url, headers=headers, json=update_data)
        
        if update_response.status_code not in [200, 204]:
            print(f"ERROR: Failed to confirm email. Status: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
        
        print(f"SUCCESS: Email confirmed for {email}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to confirm email: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python confirm_user_email.py <email>")
        print("Example: python confirm_user_email.py user@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    success = confirm_user_email(email)
    sys.exit(0 if success else 1)

