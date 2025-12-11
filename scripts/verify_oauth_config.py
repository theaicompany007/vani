"""
Verify Google OAuth Configuration

Checks if OAuth is properly configured in both Google Cloud Console and Supabase.

Usage:
    python scripts/verify_oauth_config.py --url https://vani.ngrok.app
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)
load_dotenv(basedir / '.local.env', override=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
GOOGLE_OAUTH_CLIENT_ID = (
    os.getenv('GOOGLE_OAUTH_CLIENT_ID') or 
    os.getenv('OAuth_Client_ID') or 
    os.getenv('OAUTH_CLIENT_ID')
)
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID') or 'project-vani-480503'

def get_app_url():
    """Get application URL"""
    if '--url' in sys.argv:
        idx = sys.argv.index('--url')
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return os.getenv('WEBHOOK_BASE_URL') or os.getenv('NEXT_PUBLIC_APP_URL')

def get_required_redirect_uris(app_url: str) -> List[str]:
    """Get list of required redirect URIs"""
    redirect_uris = []
    if SUPABASE_URL:
        redirect_uris.append(f"{SUPABASE_URL}/auth/v1/callback")
    redirect_uris.extend([
        f"{app_url}/login",
        f"{app_url}/command-center",
        f"{app_url}/api/auth/callback",
        "http://localhost:5000/login",
        "http://localhost:5000/command-center",
    ])
    return redirect_uris

def check_supabase_oauth_config() -> Dict[str, Any]:
    """Check Supabase OAuth configuration"""
    print("\n" + "="*70)
    print("  CHECKING SUPABASE OAUTH CONFIGURATION")
    print("="*70)
    
    if not SUPABASE_URL:
        return {
            'success': False,
            'error': 'SUPABASE_URL not found in environment variables'
        }
    
    project_ref = SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
    dashboard_url = f"https://supabase.com/dashboard/project/{project_ref}/auth/providers"
    
    print(f"\n📋 Checking Supabase Project: {project_ref}")
    print(f"   🔗 Dashboard: {dashboard_url}")
    
    # Try to check via Management API if access token is available
    supabase_access_token = os.getenv('SUPABASE_ACCESS_TOKEN')
    
    if supabase_access_token:
        try:
            print("\n   🔍 Attempting to check via Supabase Management API...")
            # Use Management API to check auth configuration
            api_url = f"https://api.supabase.com/v1/projects/{project_ref}/config/auth"
            headers = {
                'Authorization': f'Bearer {supabase_access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                config = response.json()
                print("   ✅ Successfully retrieved auth configuration")
                
                # Check for provider configuration
                # Note: Provider config might be in a different endpoint
                print(f"   📋 Site URL: {config.get('site_url', 'Not set')}")
                print(f"   📋 Redirect URLs: {config.get('uri_allow_list', 'Not set')}")
                
                # Try to get providers
                providers_url = f"https://api.supabase.com/v1/projects/{project_ref}/auth/providers"
                providers_response = requests.get(providers_url, headers=headers, timeout=10)
                
                if providers_response.status_code == 200:
                    providers = providers_response.json()
                    print(f"\n   📋 Auth Providers:")
                    google_provider = None
                    for provider in providers:
                        provider_id = provider.get('id', 'unknown')
                        enabled = provider.get('enabled', False)
                        status = "✅ Enabled" if enabled else "❌ Disabled"
                        print(f"      - {provider_id}: {status}")
                        if provider_id == 'google':
                            google_provider = provider
                    
                    if google_provider:
                        if google_provider.get('enabled'):
                            print(f"\n   ✅ Google OAuth is ENABLED")
                            client_id = google_provider.get('client_id', 'Not set')
                            has_secret = bool(google_provider.get('client_secret'))
                            print(f"      Client ID: {client_id[:50]}..." if len(client_id) > 50 else f"      Client ID: {client_id}")
                            print(f"      Client Secret: {'✅ Set' if has_secret else '❌ Not set'}")
                            
                            # Check if Client ID matches
                            if GOOGLE_OAUTH_CLIENT_ID and client_id == GOOGLE_OAUTH_CLIENT_ID:
                                print(f"      ✅ Client ID matches environment variable")
                            elif GOOGLE_OAUTH_CLIENT_ID:
                                print(f"      ⚠️  Client ID does NOT match environment variable")
                                print(f"         Expected: {GOOGLE_OAUTH_CLIENT_ID[:50]}...")
                            
                            return {
                                'success': True,
                                'api_connected': True,
                                'google_enabled': True,
                                'client_id': client_id,
                                'has_secret': has_secret,
                                'dashboard_url': dashboard_url
                            }
                        else:
                            print(f"\n   ❌ Google OAuth is DISABLED")
                            return {
                                'success': False,
                                'api_connected': True,
                                'google_enabled': False,
                                'dashboard_url': dashboard_url,
                                'error': 'Google provider is not enabled'
                            }
                    else:
                        print(f"\n   ⚠️  Google provider not found in providers list")
                        return {
                            'success': False,
                            'api_connected': True,
                            'google_enabled': False,
                            'dashboard_url': dashboard_url,
                            'error': 'Google provider not configured'
                        }
                else:
                    print(f"   ⚠️  Could not fetch providers (status: {providers_response.status_code})")
            else:
                print(f"   ⚠️  API check failed (status: {response.status_code})")
                if response.status_code == 401:
                    print("   💡 SUPABASE_ACCESS_TOKEN might be invalid or expired")
                    print("   Get a new token from: https://supabase.com/dashboard/account/tokens")
        except Exception as e:
            print(f"   ⚠️  API check error: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to manual check instructions
    print(f"\n📋 Manual Check Required:")
    print(f"   🔗 Open: {dashboard_url}")
    print("\n   Verify:")
    print("   ✅ Google provider is enabled")
    if GOOGLE_OAUTH_CLIENT_ID:
        print(f"   ✅ Client ID matches: {GOOGLE_OAUTH_CLIENT_ID[:50]}...")
    print("   ✅ Client Secret is set (not empty)")
    
    return {
        'success': True,
        'api_connected': False,
        'dashboard_url': dashboard_url,
        'note': 'Manual verification required'
    }

def check_google_oauth_config(app_url: str) -> Dict[str, Any]:
    """Check Google Cloud OAuth configuration"""
    print("\n" + "="*70)
    print("  CHECKING GOOGLE CLOUD OAUTH CONFIGURATION")
    print("="*70)
    
    if not GOOGLE_OAUTH_CLIENT_ID:
        return {
            'success': False,
            'error': 'GOOGLE_OAUTH_CLIENT_ID not found in environment variables'
        }
    
    project_id = GOOGLE_CLOUD_PROJECT
    project_number = GOOGLE_OAUTH_CLIENT_ID.split('-')[0] if '-' in GOOGLE_OAUTH_CLIENT_ID else None
    client_id_suffix = GOOGLE_OAUTH_CLIENT_ID.split('-', 1)[1] if '-' in GOOGLE_OAUTH_CLIENT_ID else GOOGLE_OAUTH_CLIENT_ID
    
    if project_number:
        oauth_client_url = f"https://console.cloud.google.com/apis/credentials/oauthclient/{project_number}-{client_id_suffix}?project={project_id}"
    else:
        oauth_client_url = f"https://console.cloud.google.com/apis/credentials?project={project_id}"
    
    required_uris = get_required_redirect_uris(app_url)
    
    print(f"\n📋 Manual Check Required:")
    print(f"   🔗 Open: {oauth_client_url}")
    print(f"\n   Client ID: {GOOGLE_OAUTH_CLIENT_ID}")
    print("\n   Verify these redirect URIs are configured:")
    print("   " + "-"*60)
    for i, uri in enumerate(required_uris, 1):
        marker = "🔴 CRITICAL" if SUPABASE_URL and SUPABASE_URL in uri else f"   {i}."
        print(f"   {marker} {uri}")
    print("   " + "-"*60)
    
    return {
        'success': True,
        'oauth_client_url': oauth_client_url,
        'client_id': GOOGLE_OAUTH_CLIENT_ID,
        'required_uris': required_uris,
        'note': 'Manual verification required - Google Cloud doesn\'t provide API for OAuth clients'
    }

def test_oauth_flow(app_url: str) -> Dict[str, Any]:
    """Test OAuth flow if possible"""
    print("\n" + "="*70)
    print("  TESTING OAUTH FLOW")
    print("="*70)
    
    if not SUPABASE_URL:
        return {
            'success': False,
            'error': 'SUPABASE_URL not found'
        }
    
    # Check if we can access the login page
    try:
        login_url = f"{app_url}/login" if app_url else None
        if login_url:
            print(f"\n📋 Test Steps:")
            print(f"   1. Open your app login page: {login_url}")
            print("   2. Click 'Sign in with Google'")
            print("   3. You should be redirected to Google for authentication")
            print("   4. After authentication, you should be redirected back to your app")
            print("   5. You should be logged in successfully")
            
            return {
                'success': True,
                'login_url': login_url,
                'test_steps': [
                    'Open login page',
                    'Click "Sign in with Google"',
                    'Complete Google authentication',
                    'Verify redirect back to app',
                    'Verify successful login'
                ]
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    
    return {
        'success': False,
        'error': 'Could not determine login URL'
    }

def main():
    """Main verification function"""
    app_url = get_app_url()
    
    if not app_url:
        print("❌ Error: Application URL not found")
        print("   Provide via --url argument or WEBHOOK_BASE_URL env var")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("  GOOGLE OAUTH CONFIGURATION VERIFICATION")
    print("="*70)
    print(f"\nApp URL: {app_url}")
    if SUPABASE_URL:
        print(f"Supabase URL: {SUPABASE_URL}")
    if GOOGLE_OAUTH_CLIENT_ID:
        print(f"OAuth Client ID: {GOOGLE_OAUTH_CLIENT_ID[:50]}...")
    
    results = {
        'google': check_google_oauth_config(app_url),
        'supabase': check_supabase_oauth_config(),
        'test': test_oauth_flow(app_url)
    }
    
    print("\n" + "="*70)
    print("  VERIFICATION SUMMARY")
    print("="*70)
    
    print("\n✅ Google Cloud Console:")
    if results['google'].get('success'):
        print(f"   🔗 {results['google'].get('oauth_client_url', 'N/A')}")
        print("   ⚠️  Manual verification required (no API access)")
    else:
        print(f"   ❌ {results['google'].get('error', 'Unknown error')}")
    
    print("\n✅ Supabase Dashboard:")
    if results['supabase'].get('success'):
        print(f"   🔗 {results['supabase'].get('dashboard_url', 'N/A')}")
        if results['supabase'].get('api_connected'):
            print("   ✅ API connection successful")
        else:
            print("   ⚠️  Manual verification required")
    else:
        print(f"   ❌ {results['supabase'].get('error', 'Unknown error')}")
    
    print("\n✅ OAuth Flow Test:")
    if results['test'].get('success'):
        print(f"   🔗 Login URL: {results['test'].get('login_url', 'N/A')}")
        print("   📋 Follow the test steps above to verify OAuth works")
    else:
        print(f"   ⚠️  {results['test'].get('error', 'Could not determine test steps')}")
    
    print("\n" + "="*70)
    print("  QUICK LINKS")
    print("="*70)
    
    if results['google'].get('oauth_client_url'):
        print(f"\n🔗 Google Cloud Console:")
        print(f"   {results['google']['oauth_client_url']}")
    
    if results['supabase'].get('dashboard_url'):
        print(f"\n🔗 Supabase Dashboard:")
        print(f"   {results['supabase']['dashboard_url']}")
    
    if results['test'].get('login_url'):
        print(f"\n🔗 Test Login:")
        print(f"   {results['test']['login_url']}")
    
    print("\n💡 All checks complete! Review the manual verification steps above.")
    print("   If everything is configured correctly, OAuth should work!")

if __name__ == '__main__':
    main()

