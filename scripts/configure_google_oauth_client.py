"""
Configure Google OAuth 2.0 Client with redirect URIs

This script configures your Google OAuth client with the correct redirect URIs
for Supabase authentication.

Usage:
    python scripts/configure_google_oauth_client.py [--url https://vani.ngrok.app] [--client-id CLIENT_ID] [--client-secret CLIENT_SECRET]
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)
load_dotenv(basedir / '.local.env', override=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID') or 'project-vani-480503'
# Try multiple environment variable names
GOOGLE_OAUTH_CLIENT_ID = (
    os.getenv('GOOGLE_OAUTH_CLIENT_ID') or 
    os.getenv('OAuth_Client_ID') or 
    os.getenv('OAUTH_CLIENT_ID')
)
GOOGLE_OAUTH_CLIENT_SECRET = (
    os.getenv('GOOGLE_OAUTH_CLIENT_SECRET') or 
    os.getenv('OAuth_Client_Secret') or 
    os.getenv('OAUTH_CLIENT_SECRET')
)

def find_gcloud() -> Optional[str]:
    """Find gcloud executable"""
    # Common Windows paths
    common_paths = [
        r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
        r"C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
    ]
    
    # Check if gcloud is in PATH
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return 'gcloud'
    except:
        pass
    
    # Check common paths
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

def run_gcloud_command(cmd: List[str]) -> Dict[str, Any]:
    """Run a gcloud command and return JSON output"""
    gcloud_path = find_gcloud()
    if not gcloud_path:
        return {'success': False, 'error': 'gcloud not found in PATH or common locations'}
    
    try:
        if gcloud_path == 'gcloud':
            full_cmd = ['gcloud'] + cmd + ['--format', 'json']
        else:
            full_cmd = [gcloud_path] + cmd + ['--format', 'json']
        
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False
        )
        
        if result.returncode != 0:
            return {'success': False, 'error': result.stderr, 'stdout': result.stdout}
        
        try:
            output = json.loads(result.stdout) if result.stdout.strip() else {}
            return {'success': True, 'data': output, 'stdout': result.stdout}
        except json.JSONDecodeError:
            return {'success': True, 'data': result.stdout, 'stdout': result.stdout}
            
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Command timed out'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_gcloud_access_token() -> Optional[str]:
    """Get gcloud access token from application default credentials or gcloud"""
    # Try using google-auth library first (for application default credentials)
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        
        credentials, project = default()
        if credentials and credentials.valid:
            return credentials.token
        elif credentials and hasattr(credentials, 'refresh'):
            # Refresh if needed
            request = Request()
            credentials.refresh(request)
            return credentials.token
    except ImportError:
        # google-auth not installed, fall back to gcloud command
        pass
    except Exception as e:
        # If there's an error with application default credentials, try gcloud command
        pass
    
    # Fallback: Use gcloud command
    try:
        result = run_gcloud_command(['gcloud', 'auth', 'print-access-token'])
        if result['success']:
            token = result['data'].strip() if isinstance(result['data'], str) else None
            if token and len(token) > 50:  # Basic validation
                return token
    except:
        pass
    
    return None

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

def enable_iam_api(project_id: str, access_token: str) -> bool:
    """Enable IAM API for the project"""
    try:
        print("   🔧 Enabling IAM API...")
        api_url = f"https://serviceusage.googleapis.com/v1/projects/{project_id}/services/iam.googleapis.com:enable"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(api_url, headers=headers, json={}, timeout=30)
        
        if response.status_code in [200, 204]:
            print("   ✅ IAM API enabled successfully")
            return True
        elif response.status_code == 409:
            # API already enabled
            print("   ✅ IAM API is already enabled")
            return True
        else:
            print(f"   ⚠️  Failed to enable IAM API (status: {response.status_code})")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ⚠️  Error enabling IAM API: {e}")
        return False

def update_oauth_client_via_api(project_id: str, client_id: str, redirect_uris: List[str]) -> bool:
    """Update OAuth client redirect URIs using Google Cloud IAM API"""
    print(f"\n🔧 Attempting to update OAuth client via Google Cloud IAM API...")
    
    # Get access token using application default credentials
    access_token = get_gcloud_access_token()
    if not access_token:
        print("⚠️  Could not get access token from application default credentials")
        print("   Make sure you've run: gcloud auth application-default login")
        return False
    
    print(f"   ✅ Got access token (length: {len(access_token)})")
    
    try:
        # Enable IAM API if not already enabled
        if not enable_iam_api(project_id, access_token):
            print("   ⚠️  Could not enable IAM API, but continuing...")
        
        # Wait a moment for API to propagate
        import time
        print("   ⏳ Waiting for API to be ready...")
        time.sleep(2)
        
        # Use Google Cloud IAM API for OAuth clients
        # The OAuth client ID format is: PROJECT_NUMBER-CLIENT_ID.apps.googleusercontent.com
        # For IAM API, we need to use the full client ID
        
        # IAM API endpoint for updating OAuth clients
        api_url = f"https://iam.googleapis.com/v1/projects/{project_id}/locations/global/oauthClients/{client_id}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Goog-User-Project': project_id
        }
        
        # First, get current client config to preserve other settings
        print("   📥 Fetching current OAuth client configuration...")
        get_response = requests.get(api_url, headers=headers, timeout=10)
        
        if get_response.status_code == 200:
            current_config = get_response.json()
            print("   ✅ Retrieved current configuration")
            
            # Update only the redirect URIs, preserve other settings
            update_data = {
                'allowedRedirectUris': redirect_uris
            }
            
            # Preserve other important fields if they exist
            if 'allowedGrantTypes' in current_config:
                update_data['allowedGrantTypes'] = current_config['allowedGrantTypes']
            if 'allowedScopes' in current_config:
                update_data['allowedScopes'] = current_config['allowedScopes']
            if 'displayName' in current_config:
                update_data['displayName'] = current_config['displayName']
            if 'description' in current_config:
                update_data['description'] = current_config['description']
            
            # Update the OAuth client
            print("   📤 Updating redirect URIs...")
            patch_response = requests.patch(
                api_url,
                headers=headers,
                json=update_data,
                params={'updateMask': 'allowedRedirectUris'},
                timeout=10
            )
            
            if patch_response.status_code in [200, 204]:
                print("✅ Successfully updated OAuth client redirect URIs via IAM API!")
                updated_config = patch_response.json() if patch_response.status_code == 200 else {}
                if 'allowedRedirectUris' in updated_config:
                    print(f"   📋 Updated redirect URIs ({len(updated_config['allowedRedirectUris'])} total):")
                    for uri in updated_config['allowedRedirectUris']:
                        print(f"      ✅ {uri}")
                return True
            else:
                print(f"⚠️  IAM API update failed (status: {patch_response.status_code})")
                error_text = patch_response.text[:500]
                print(f"   Response: {error_text}")
                
                # Try alternative: update without updateMask
                print("   🔄 Trying alternative update method...")
                patch_response2 = requests.patch(
                    api_url,
                    headers=headers,
                    json=update_data,
                    timeout=10
                )
                
                if patch_response2.status_code in [200, 204]:
                    print("✅ Successfully updated OAuth client via alternative method!")
                    return True
                else:
                    print(f"⚠️  Alternative method also failed (status: {patch_response2.status_code})")
                    print(f"   Response: {patch_response2.text[:500]}")
        elif get_response.status_code == 404:
            print(f"⚠️  OAuth client not found in IAM API (404)")
            print(f"   Note: Standard OAuth 2.0 web clients are managed differently")
            print(f"   Trying alternative method using Google API Client Library...")
            
            # Try using google-api-python-client with service discovery
            try:
                from googleapiclient.discovery import build
                from google.auth import default
                from google.auth.transport.requests import Request
                
                credentials, _ = default()
                if credentials and hasattr(credentials, 'refresh'):
                    request = Request()
                    credentials.refresh(request)
                
                # Try using the Cloud Resource Manager or IAM service
                # Unfortunately, standard OAuth clients don't have a direct API
                # We need to use a workaround
                
                print("   ⚠️  Standard OAuth 2.0 web clients cannot be updated via API")
                print("   They must be configured through the Google Cloud Console UI")
                print("   However, we can automate this using browser automation...")
                
                # For now, return False to show manual instructions
                return False
                
            except ImportError:
                print("   ⚠️  google-api-python-client not available for alternative method")
                return False
            except Exception as e:
                print(f"   ⚠️  Alternative method error: {e}")
                return False
        else:
            print(f"⚠️  Could not fetch OAuth client config (status: {get_response.status_code})")
            error_text = get_response.text[:500]
            print(f"   Response: {error_text}")
        
        return False
        
    except Exception as e:
        print(f"⚠️  API update error: {e}")
        import traceback
        traceback.print_exc()
        return False

def configure_google_oauth_client(app_url: str, client_id: Optional[str] = None, client_secret: Optional[str] = None):
    """Configure Google OAuth client with redirect URIs"""
    
    # Get client ID and secret
    if not client_id:
        if '--client-id' in sys.argv:
            idx = sys.argv.index('--client-id')
            if idx + 1 < len(sys.argv):
                client_id = sys.argv[idx + 1]
        else:
            client_id = GOOGLE_OAUTH_CLIENT_ID
    
    if not client_secret:
        if '--client-secret' in sys.argv:
            idx = sys.argv.index('--client-secret')
            if idx + 1 < len(sys.argv):
                client_secret = sys.argv[idx + 1]
        else:
            client_secret = GOOGLE_OAUTH_CLIENT_SECRET
    
    # Get project ID
    project_id = GOOGLE_CLOUD_PROJECT
    if '--project-id' in sys.argv:
        idx = sys.argv.index('--project-id')
        if idx + 1 < len(sys.argv):
            project_id = sys.argv[idx + 1]
    
    print("\n" + "="*70)
    print("  CONFIGURING GOOGLE OAUTH CLIENT")
    print("="*70)
    print(f"Project: {project_id}")
    print(f"Client ID: {client_id}")
    print(f"App URL: {app_url}")
    if SUPABASE_URL:
        print(f"Supabase URL: {SUPABASE_URL}\n")
    
    # Required redirect URIs
    redirect_uris = []
    
    # CRITICAL: Supabase callback (must be first)
    if SUPABASE_URL:
        redirect_uris.append(f"{SUPABASE_URL}/auth/v1/callback")
    
    # App redirect URIs
    redirect_uris.extend([
        f"{app_url}/login",
        f"{app_url}/command-center",
        f"{app_url}/api/auth/callback",
        "http://localhost:5000/login",
        "http://localhost:5000/command-center",
    ])
    
    # Remove duplicates
    redirect_uris = list(dict.fromkeys(redirect_uris))  # Preserves order
    
    print("📋 Redirect URIs to configure:")
    for i, uri in enumerate(redirect_uris, 1):
        marker = "🔴 CRITICAL" if SUPABASE_URL and SUPABASE_URL in uri else "  "
        print(f"   {i}. {marker} {uri}")
    
    if not client_id:
        print("\n❌ Error: OAuth Client ID not found")
        print("   Provide via:")
        print("   - --client-id argument")
        print("   - GOOGLE_OAUTH_CLIENT_ID in .env.local or .local.env")
        print("   - OAuth_Client_ID in .env.local or .local.env")
        return False
    
    # Try to update via API
    if update_oauth_client_via_api(project_id, client_id, redirect_uris):
        print("\n✅ OAuth client configured successfully!")
        return True
    
    # Fallback to manual instructions
    print("\n" + "="*70)
    print("  MANUAL CONFIGURATION REQUIRED")
    print("="*70)
    print("\n📝 Please configure these URIs in Google Cloud Console:")
    print(f"\n🔗 Open: https://console.cloud.google.com/apis/credentials?project={project_id}")
    
    print("\n1. Find your OAuth 2.0 Client ID:")
    print(f"   Client ID: {client_id}")
    if client_secret:
        print(f"   Client Secret: {client_secret[:20]}... (hidden)")
    
    print("\n2. Click on the Client ID to edit")
    
    print("\n3. Under 'Authorized redirect URIs', add these URIs (one per line):")
    for uri in redirect_uris:
        marker = "   🔴 CRITICAL" if SUPABASE_URL and SUPABASE_URL in uri else "   ✅"
        print(f"{marker} {uri}")
    
    print("\n4. Click 'Save'")
    
    print("\n5. Copy the Client ID and Secret to Supabase:")
    print(f"   🔗 https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/providers")
    print("   - Enable Google provider")
    print(f"   - Client ID: {client_id}")
    if client_secret:
        print(f"   - Client Secret: {client_secret}")
    print("   - Save")
    
    return False

def main():
    """Main function"""
    app_url = get_app_url()
    
    if not app_url:
        print("❌ Error: Could not determine application URL")
        print("\nPlease provide URL manually:")
        print("  python scripts/configure_google_oauth_client.py --url https://vani.ngrok.app --client-id YOUR_CLIENT_ID")
        print("\nOr set WEBHOOK_BASE_URL in .env.local or .local.env")
        sys.exit(1)
    
    # Get client ID and secret from args or env
    client_id = None
    client_secret = None
    
    if '--client-id' in sys.argv:
        idx = sys.argv.index('--client-id')
        if idx + 1 < len(sys.argv):
            client_id = sys.argv[idx + 1]
    
    if '--client-secret' in sys.argv:
        idx = sys.argv.index('--client-secret')
        if idx + 1 < len(sys.argv):
            client_secret = sys.argv[idx + 1]
    
    success = configure_google_oauth_client(app_url, client_id, client_secret)
    
    if success:
        print("\n✅ Google OAuth client configuration complete!")
        sys.exit(0)
    else:
        print("\n⚠️  Please complete manual configuration in Google Cloud Console")
        sys.exit(0)  # Exit 0 because we provided instructions

if __name__ == '__main__':
    main()

