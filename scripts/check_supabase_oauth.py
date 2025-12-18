"""
Check if Google OAuth is configured in Supabase Project VANI

This script checks if Google OAuth provider is enabled in Supabase.

Usage:
    python scripts/check_supabase_oauth.py
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)
load_dotenv(basedir / '.local.env', override=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_ACCESS_TOKEN = os.getenv('SUPABASE_ACCESS_TOKEN')
GOOGLE_OAUTH_CLIENT_ID = (
    os.getenv('GOOGLE_OAUTH_CLIENT_ID') or 
    os.getenv('OAuth_Client_ID') or 
    os.getenv('OAUTH_CLIENT_ID')
)

def check_oauth_via_dashboard():
    """Check OAuth via dashboard link"""
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL not found")
        return False
    
    project_ref = SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
    dashboard_url = f"https://supabase.com/dashboard/project/{project_ref}/auth/providers"
    
    print("\n" + "="*70)
    print("  CHECKING SUPABASE OAUTH CONFIGURATION")
    print("="*70)
    print(f"\n📋 Project: {project_ref}")
    print(f"🔗 Dashboard: {dashboard_url}")
    
    # Try to open browser
    try:
        import webbrowser
        print("\n🌐 Opening Supabase Dashboard in your browser...")
        webbrowser.open(dashboard_url)
        print("   ✅ Browser opened")
    except:
        print("   ⚠️  Could not open browser automatically")
    
    print("\n📋 Please check in the browser:")
    print("   1. Look for 'Google' in the providers list")
    print("   2. Check if it's enabled (toggle should be ON)")
    if GOOGLE_OAUTH_CLIENT_ID:
        print(f"   3. Verify Client ID: {GOOGLE_OAUTH_CLIENT_ID[:50]}...")
    print("   4. Verify Client Secret is set (not empty)")
    
    return True

def check_oauth_via_api():
    """Try to check OAuth via Supabase Management API"""
    if not SUPABASE_ACCESS_TOKEN:
        print("\n⚠️  SUPABASE_ACCESS_TOKEN not found - cannot check via API")
        print("   Get token from: https://supabase.com/dashboard/account/tokens")
        return None
    
    if not SUPABASE_URL:
        return None
    
    project_ref = SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
    
    try:
        # Try Management API
        api_url = f"https://api.supabase.com/v1/projects/{project_ref}/config/auth"
        headers = {
            'Authorization': f'Bearer {SUPABASE_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            config = response.json()
            print("\n✅ Successfully retrieved auth configuration via API")
            print(f"   Site URL: {config.get('site_url', 'Not set')}")
            return config
        else:
            print(f"\n⚠️  API check failed (status: {response.status_code})")
            if response.status_code == 401:
                print("   💡 SUPABASE_ACCESS_TOKEN might be invalid or expired")
            return None
    except Exception as e:
        print(f"\n⚠️  API check error: {e}")
        return None

def main():
    """Main function"""
    print("\n" + "="*70)
    print("  SUPABASE OAUTH CONFIGURATION CHECK")
    print("="*70)
    
    if not SUPABASE_URL:
        print("❌ Error: SUPABASE_URL not found in environment variables")
        sys.exit(1)
    
    project_ref = SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
    print(f"\n📋 Checking Project: {project_ref}")
    
    # Try API check first
    api_result = check_oauth_via_api()
    
    # Always show dashboard check
    check_oauth_via_dashboard()
    
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    
    if api_result:
        print("\n✅ API Connection: Success")
        print("   ⚠️  Note: Provider configuration must be checked in dashboard")
    else:
        print("\n⚠️  API Connection: Not available or failed")
        print("   Please check manually in the dashboard")
    
    print(f"\n🔗 Direct Link to Check:")
    print(f"   https://supabase.com/dashboard/project/{project_ref}/auth/providers")
    
    print("\n💡 What to look for:")
    print("   - Google provider should be in the list")
    print("   - Toggle should be ON (enabled)")
    print("   - Client ID and Secret should be filled in")
    
    if not GOOGLE_OAUTH_CLIENT_ID:
        print("\n⚠️  GOOGLE_OAUTH_CLIENT_ID not found in environment")
        print("   This means OAuth might not be configured yet")
    else:
        print(f"\n✅ Expected Client ID: {GOOGLE_OAUTH_CLIENT_ID[:50]}...")
        print("   Verify this matches what's in Supabase Dashboard")

if __name__ == '__main__':
    main()

















