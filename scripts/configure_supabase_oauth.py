"""
Configure Supabase OAuth URL Configuration for Google OAuth

This script updates the Supabase Auth URL configuration to allow OAuth redirects
from your application URL (ngrok or production).

Usage:
    python scripts/configure_supabase_oauth.py [--url https://vani.ngrok.app]
    
If --url is not provided, it will try to detect from:
    1. WEBHOOK_BASE_URL environment variable
    2. ngrok API (if running)
    3. Prompt for manual input
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
# Try both .env.local and .local.env (user mentioned .local.env)
load_dotenv(basedir / '.env.local', override=True)
load_dotenv(basedir / '.local.env', override=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_ACCESS_TOKEN = os.getenv('SUPABASE_ACCESS_TOKEN')  # Personal access token for Management API (optional)

# Debug: Show which env file was loaded
env_files_checked = []
if (basedir / '.env').exists():
    env_files_checked.append('.env')
if (basedir / '.env.local').exists():
    env_files_checked.append('.env.local')
if (basedir / '.local.env').exists():
    env_files_checked.append('.local.env')

def get_ngrok_url() -> Optional[str]:
    """Get ngrok URL from ngrok API"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                http_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                if not http_tunnel:
                    http_tunnel = next((t for t in tunnels if 'http' in t.get('proto', '')), None)
                if http_tunnel:
                    return http_tunnel.get('public_url')
    except:
        pass
    return None

def get_app_url() -> Optional[str]:
    """Get application URL from various sources"""
    # Priority 1: Command line argument
    if '--url' in sys.argv:
        idx = sys.argv.index('--url')
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    
    # Priority 2: Environment variable
    app_url = os.getenv('WEBHOOK_BASE_URL') or os.getenv('NEXT_PUBLIC_APP_URL')
    if app_url:
        return app_url
    
    # Priority 3: ngrok API
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        return ngrok_url
    
    return None

def configure_supabase_oauth(app_url: str, environment: str = 'dev'):
    """
    Configure Supabase OAuth URL configuration with environment-aware safety checks
    
    Args:
        app_url: Application URL (e.g., https://vani.ngrok.app)
        environment: 'dev' or 'prod' - determines if updates are safe
    """
    if not SUPABASE_URL:
        print("❌ Error: SUPABASE_URL not found in .env.local or .local.env")
        print(f"   Checked files: {', '.join(env_files_checked) if env_files_checked else 'none found'}")
        return False
    
    # Extract project reference from SUPABASE_URL
    # Format: https://rkntrsprfcypwikshvsf.supabase.co
    project_ref = SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
    
    print("\n" + "="*70)
    print("  CONFIGURING SUPABASE OAUTH URLS")
    print("="*70)
    print(f"Project: {project_ref}")
    print(f"Environment: {environment.upper()}")
    print(f"App URL: {app_url}\n")
    
    # Required redirect URLs for OAuth
    redirect_urls = [
        app_url,
        f"{app_url}/login",
        f"{app_url}/command-center",
        f"{app_url}/api/auth/callback",
        # Also include localhost for development
        "http://localhost:5000",
        "http://localhost:5000/login",
        "http://localhost:5000/command-center",
    ]
    
    # Remove duplicates and sort
    redirect_urls = sorted(list(set(redirect_urls)))
    
    print("📋 Redirect URLs to configure:")
    for i, url in enumerate(redirect_urls, 1):
        print(f"   {i}. {url}")
    
    # Try to update via Management API if access token is available
    # Note: Supabase Management API requires a personal access token, not service role key
    # The service role key is for REST API, Management API needs a different token
    if SUPABASE_ACCESS_TOKEN:
        print("\n[*] Attempting to update via Supabase Management API...")
        print(f"   Using SUPABASE_ACCESS_TOKEN from: {', '.join(env_files_checked) if env_files_checked else 'environment'}")
        try:
            # Extract project reference from SUPABASE_URL
            # Format: https://rkntrsprfcypwikshvsf.supabase.co
            project_ref = SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
            
            # Supabase Management API endpoint
            # Using the Management API v1
            api_url = f"https://api.supabase.com/v1/projects/{project_ref}/config/auth"
            
            headers = {
                'Authorization': f'Bearer {SUPABASE_ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # First, fetch current configuration to check if update is safe
            get_response = requests.get(api_url, headers=headers, timeout=10)
            current_site_url = None
            current_uri_allow_list = None
            
            if get_response.status_code == 200:
                current_config = get_response.json()
                current_site_url = current_config.get('site_url', '')
                current_uri_allow_list = current_config.get('uri_allow_list', '')
                
                # Check if current site_url is for different environment
                if current_site_url:
                    current_lower = current_site_url.lower()
                    app_lower = app_url.lower()
                    is_current_dev = 'vani-dev.ngrok' in current_lower
                    is_current_prod = 'vani.ngrok' in current_lower and 'vani-dev' not in current_lower
                    is_target_dev = 'vani-dev.ngrok' in app_lower
                    is_target_prod = 'vani.ngrok' in app_lower and 'vani-dev' not in app_lower
                    
                    # Warn if trying to overwrite different environment
                    if (is_current_dev and is_target_prod) or (is_current_prod and is_target_dev):
                        print(f"⚠️  WARNING: Current site_url ({current_site_url}) is for different environment")
                        print(f"   Target URL ({app_url}) would overwrite production configuration")
                        print(f"   Skipping automatic update to prevent overwrite")
                        print(f"   Please update manually in Supabase Dashboard if needed")
                        return False
            
            # Format redirect URLs as comma-separated string
            uri_allow_list = ','.join(redirect_urls)
            
            update_data = {
                'site_url': app_url,
                'uri_allow_list': uri_allow_list
            }
            
            response = requests.patch(api_url, headers=headers, json=update_data, timeout=10)
            
            if response.status_code in [200, 204]:
                print("✅ Successfully updated via Management API!")
                return True
            else:
                print(f"⚠️  Management API update failed (status: {response.status_code})")
                print(f"   Response: {response.text[:200]}")
                print("\n   Note: Management API requires a personal access token")
                print("   Get one from: https://supabase.com/dashboard/account/tokens")
                print("   Falling back to manual configuration...")
        except Exception as e:
            print(f"⚠️  Management API update error: {e}")
            print("   Falling back to manual configuration...")
    elif SUPABASE_SERVICE_KEY:
        print("\n[*] SUPABASE_ACCESS_TOKEN not found - skipping API update")
        print("   Note: Management API requires SUPABASE_ACCESS_TOKEN (personal access token)")
        print("   Service role key (SUPABASE_SERVICE_KEY) is for REST API, not Management API")
        print("   Get token from: https://supabase.com/dashboard/account/tokens")
    
    # Fallback to manual instructions
    print("\n" + "="*70)
    print("  MANUAL CONFIGURATION REQUIRED")
    print("="*70)
    print("\n📝 Please configure these URLs in Supabase Dashboard:")
    print(f"\n🔗 Open: https://supabase.com/dashboard/project/{project_ref}/auth/url-configuration")
    print("\n1. Set Site URL to:")
    print(f"   ✅ {app_url}")
    print("\n2. Add these Redirect URLs (one per line):")
    for url in redirect_urls:
        print(f"   ✅ {url}")
    
    print("\n3. Enable Google Provider:")
    print(f"   🔗 https://supabase.com/dashboard/project/{project_ref}/auth/providers")
    print("   - Enable Google provider")
    print("   - Add Client ID and Client Secret from Google Cloud Console")
    print("   - Authorized redirect URI in Google Console should be:")
    print(f"     ✅ {SUPABASE_URL}/auth/v1/callback")
    
    print("\n💡 Tip: To enable automatic updates, add SUPABASE_ACCESS_TOKEN to .env.local or .local.env")
    print("   Get token from: https://supabase.com/dashboard/account/tokens")
    print("   Note: This is a personal access token, NOT the service role key")
    
    return False

def main():
    """Main function"""
    app_url = get_app_url()
    
    if not app_url:
        print("❌ Error: Could not determine application URL")
        print("\nPlease provide URL manually:")
        print("  python scripts/configure_supabase_oauth.py --url https://vani.ngrok.app")
        print("\nOr set WEBHOOK_BASE_URL in .env.local")
        sys.exit(1)
    
    success = configure_supabase_oauth(app_url)
    
    if success:
        print("\n✅ Supabase OAuth configuration complete!")
        sys.exit(0)
    else:
        print("\n⚠️  Please complete manual configuration in Supabase Dashboard")
        sys.exit(0)  # Exit 0 because we provided instructions

if __name__ == '__main__':
    main()

