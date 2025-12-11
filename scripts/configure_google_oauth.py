"""
Configure Google OAuth Redirect URIs using gcloud SDK

This script uses gcloud to:
1. List OAuth 2.0 Client IDs
2. Update authorized redirect URIs
3. Configure for Supabase OAuth callback

Usage:
    python scripts/configure_google_oauth.py [--url https://vani.ngrok.app] [--project-id PROJECT_ID] [--client-id CLIENT_ID]
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
# Try both .env.local and .local.env (user mentioned .local.env)
load_dotenv(basedir / '.env.local', override=True)
load_dotenv(basedir / '.local.env', override=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID')

def find_gcloud() -> Optional[str]:
    """Find gcloud executable"""
    # Common Windows paths
    common_paths = [
        r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
        r"C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
        r"C:\Users\{}\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd".format(os.getenv('USERNAME', '')),
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
        # Use full path or just 'gcloud' if it's in PATH
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

def get_current_account() -> Optional[str]:
    """Get current gcloud account"""
    result = run_gcloud_command(['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'])
    if result['success'] and result['data']:
        return result['data'].strip() if isinstance(result['data'], str) else None
    return None

def set_account(email: str) -> bool:
    """Set gcloud account"""
    print(f"🔐 Setting gcloud account to: {email}")
    result = run_gcloud_command(['gcloud', 'config', 'set', 'account', email])
    if result['success']:
        print(f"✅ Account set to: {email}")
        return True
    else:
        print(f"❌ Failed to set account: {result.get('error', 'Unknown error')}")
        return False

def get_projects() -> List[Dict[str, Any]]:
    """Get list of Google Cloud projects"""
    print("\n📋 Fetching Google Cloud projects...")
    result = run_gcloud_command(['gcloud', 'projects', 'list'])
    
    if result['success']:
        if isinstance(result['data'], list):
            return result['data']
        elif isinstance(result['data'], str):
            # Try to parse as JSON array
            try:
                return json.loads(result['data'])
            except:
                return []
    return []

def get_oauth_clients(project_id: str) -> List[Dict[str, Any]]:
    """Get OAuth 2.0 Client IDs for a project"""
    print(f"\n🔍 Fetching OAuth clients for project: {project_id}")
    
    # Set project
    run_gcloud_command(['gcloud', 'config', 'set', 'project', project_id])
    
    # List OAuth clients using API
    clients = list_oauth_clients(project_id)
    
    if clients:
        print(f"✅ Found {len(clients)} OAuth client(s):")
        for i, client in enumerate(clients, 1):
            client_id = client.get('clientId') or client.get('name', '').split('/')[-1]
            client_name = client.get('displayName', 'Unnamed')
            print(f"   {i}. {client_name} (ID: {client_id})")
    
    return clients

def list_oauth_clients(project_id: str) -> List[Dict[str, Any]]:
    """List OAuth 2.0 clients using Google Cloud API"""
    try:
        # Get access token
        token_result = run_gcloud_command(['gcloud', 'auth', 'print-access-token'])
        if not token_result['success']:
            return []
        
        access_token = token_result['data'].strip() if isinstance(token_result['data'], str) else None
        if not access_token:
            return []
        
        # Use Identity Platform API to list OAuth clients
        # API: https://cloud.google.com/identity-platform/docs/reference/rest/v2/projects.oauthClients/list
        api_url = f"https://identitytoolkit.googleapis.com/v2/projects/{project_id}/oauthClients"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('oauthClients', [])
        else:
            # Try alternative API endpoint
            # Use the OAuth 2.0 API directly
            api_url_alt = f"https://iam.googleapis.com/v1/projects/{project_id}/oauthClients"
            response_alt = requests.get(api_url_alt, headers=headers, timeout=10)
            
            if response_alt.status_code == 200:
                data = response_alt.json()
                return data.get('oauthClients', [])
            
            return []
            
    except Exception as e:
        print(f"⚠️  Error listing OAuth clients: {e}")
        return []

def update_oauth_redirect_uris(project_id: str, client_id: str, redirect_uris: List[str]) -> bool:
    """Update OAuth redirect URIs using Google Cloud API"""
    print(f"\n🔧 Updating OAuth redirect URIs for client: {client_id}")
    
    try:
        # Get access token
        token_result = run_gcloud_command(['gcloud', 'auth', 'print-access-token'])
        if not token_result['success']:
            print(f"❌ Failed to get access token: {token_result.get('error')}")
            return False
        
        access_token = token_result['data'].strip() if isinstance(token_result['data'], str) else None
        if not access_token:
            print("❌ Failed to get access token")
            return False
        
        # Use Identity Platform API to update OAuth client
        # API: https://cloud.google.com/identity-platform/docs/reference/rest/v2/projects.oauthClients/patch
        api_url = f"https://identitytoolkit.googleapis.com/v2/projects/{project_id}/oauthClients/{client_id}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get current client config first
        get_response = requests.get(api_url, headers=headers, timeout=10)
        
        if get_response.status_code != 200:
            # Try alternative endpoint
            api_url_alt = f"https://iam.googleapis.com/v1/projects/{project_id}/oauthClients/{client_id}"
            get_response = requests.get(api_url_alt, headers=headers, timeout=10)
            if get_response.status_code == 200:
                api_url = api_url_alt
        
        if get_response.status_code == 200:
            current_config = get_response.json()
            
            # Update redirect URIs
            update_data = current_config.copy()
            update_data['redirectUris'] = redirect_uris
            
            # Remove fields that shouldn't be in update
            update_data.pop('name', None)
            update_data.pop('etag', None)
            
            patch_response = requests.patch(
                api_url,
                headers=headers,
                json=update_data,
                params={'updateMask': 'redirectUris'},
                timeout=10
            )
            
            if patch_response.status_code in [200, 204]:
                print("✅ Successfully updated OAuth redirect URIs via API!")
                return True
            else:
                print(f"⚠️  API update failed (status: {patch_response.status_code})")
                print(f"   Response: {patch_response.text[:200]}")
        else:
            print(f"⚠️  Could not fetch current client config (status: {get_response.status_code})")
            print(f"   Response: {get_response.text[:200]}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error updating redirect URIs: {e}")
        import traceback
        traceback.print_exc()
        return False

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

def configure_google_oauth(app_url: str, project_id: Optional[str] = None, client_id: Optional[str] = None):
    """Configure Google OAuth redirect URIs"""
    
    # Ensure we're using the right account
    target_account = 'theaicompany007@gmail.com'
    current_account = get_current_account()
    
    if current_account != target_account:
        print(f"🔄 Current account: {current_account}")
        print(f"🔄 Switching to: {target_account}")
        if not set_account(target_account):
            print("⚠️  Continuing with current account...")
    
    # Get project ID
    if not project_id:
        if '--project-id' in sys.argv:
            idx = sys.argv.index('--project-id')
            if idx + 1 < len(sys.argv):
                project_id = sys.argv[idx + 1]
        else:
            project_id = GOOGLE_CLOUD_PROJECT
    
    if not project_id:
        print("\n📋 Available projects:")
        projects = get_projects()
        if projects:
            for i, proj in enumerate(projects, 1):
                print(f"   {i}. {proj.get('projectId', 'Unknown')} - {proj.get('name', 'Unknown')}")
            print("\n💡 Set GOOGLE_CLOUD_PROJECT in .env.local or use --project-id")
        else:
            print("   No projects found")
        return False
    
    # Set project
    print(f"\n🔧 Using project: {project_id}")
    run_gcloud_command(['gcloud', 'config', 'set', 'project', project_id])
    
    # Get client ID
    if not client_id:
        if '--client-id' in sys.argv:
            idx = sys.argv.index('--client-id')
            if idx + 1 < len(sys.argv):
                client_id = sys.argv[idx + 1]
    
    # Required redirect URIs
    redirect_uris = [
        f"{SUPABASE_URL}/auth/v1/callback" if SUPABASE_URL else None,
        f"{app_url}/login",
        f"{app_url}/command-center",
        f"{app_url}/api/auth/callback",
        "http://localhost:5000/login",
        "http://localhost:5000/command-center",
    ]
    
    # Remove None values
    redirect_uris = [uri for uri in redirect_uris if uri]
    
    print("\n" + "="*70)
    print("  CONFIGURING GOOGLE OAUTH REDIRECT URIS")
    print("="*70)
    print(f"Project: {project_id}")
    print(f"App URL: {app_url}")
    if SUPABASE_URL:
        print(f"Supabase URL: {SUPABASE_URL}\n")
    
    print("📋 Redirect URIs to configure:")
    for i, uri in enumerate(redirect_uris, 1):
        print(f"   {i}. {uri}")
    
    # List available OAuth clients
    clients = get_oauth_clients(project_id)
    
    if not client_id and clients:
        # If no client ID provided, use the first one or prompt
        if len(clients) == 1:
            client_id = clients[0].get('clientId') or clients[0].get('name', '').split('/')[-1]
            print(f"\n✅ Using OAuth client: {client_id}")
        elif len(clients) > 1:
            print(f"\n⚠️  Multiple OAuth clients found. Please specify with --client-id")
            print("   Or we'll update the first one...")
            client_id = clients[0].get('clientId') or clients[0].get('name', '').split('/')[-1]
    
    if client_id:
        print(f"\n🔧 Client ID: {client_id}")
        # Try to update via API
        success = update_oauth_redirect_uris(project_id, client_id, redirect_uris)
        if success:
            print("✅ Successfully updated via API!")
            return True
    else:
        print("\n⚠️  No OAuth client ID found or specified")
        print("   Please create an OAuth client in Google Cloud Console first")
    
    # Fallback to manual instructions
    print("\n" + "="*70)
    print("  MANUAL CONFIGURATION REQUIRED")
    print("="*70)
    print("\n📝 Please configure these URIs in Google Cloud Console:")
    print(f"\n🔗 Open: https://console.cloud.google.com/apis/credentials?project={project_id}")
    print("\n1. Find your OAuth 2.0 Client ID (or create a new one)")
    print("   If you need to create one:")
    print("   - Click 'Create Credentials' > 'OAuth client ID'")
    print("   - Application type: 'Web application'")
    print("   - Name: 'Supabase OAuth Client' (or any name)")
    
    print("\n2. Click on the Client ID to edit")
    print("\n3. Under 'Authorized redirect URIs', add these URIs (one per line):")
    
    # Most important: Supabase callback
    if SUPABASE_URL:
        print(f"\n   🔴 CRITICAL - Supabase callback (must be included):")
        print(f"   ✅ {SUPABASE_URL}/auth/v1/callback")
        print("\n   📋 Additional redirect URIs (for app callbacks):")
        for uri in redirect_uris:
            if SUPABASE_URL not in uri:  # Don't duplicate Supabase callback
                print(f"   ✅ {uri}")
    else:
        for uri in redirect_uris:
            print(f"   ✅ {uri}")
    
    print("\n4. Click 'Save'")
    
    print("\n📋 After saving, copy these values:")
    print("   - Client ID: (starts with something like 123456789-abc.apps.googleusercontent.com)")
    print("   - Client Secret: (click 'Show' to reveal)")
    print("\n   Then add them to Supabase Dashboard:")
    print("   🔗 https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/providers")
    print("   - Enable Google provider")
    print("   - Paste Client ID and Client Secret")
    print("   - Save")
    
    print("\n💡 Tip: You can also use the gcloud command line:")
    print("   gcloud alpha iap oauth-clients update CLIENT_ID --redirect-uris=URI1,URI2")
    print("   (Note: This may require additional permissions)")
    
    return False

def get_gcloud_access_token() -> Optional[str]:
    """Get gcloud access token"""
    try:
        result = run_gcloud_command(['gcloud', 'auth', 'print-access-token'])
        if result['success']:
            token = result['data'].strip() if isinstance(result['data'], str) else None
            return token
    except:
        pass
    return None

def main():
    """Main function"""
    app_url = get_app_url()
    
    if not app_url:
        print("❌ Error: Could not determine application URL")
        print("\nPlease provide URL manually:")
        print("  python scripts/configure_google_oauth.py --url https://vani.ngrok.app --project-id YOUR_PROJECT_ID")
        print("\nOr set WEBHOOK_BASE_URL in .env.local")
        sys.exit(1)
    
    # Ensure we're using the right account
    target_account = 'theaicompany007@gmail.com'
    current_account = get_current_account()
    
    if current_account != target_account:
        print(f"🔄 Current account: {current_account}")
        print(f"🔄 Switching to: {target_account}")
        if not set_account(target_account):
            print("⚠️  Continuing with current account...")
    
    # Get project ID and client ID from args if provided
    project_id = None
    client_id = None
    
    if '--project-id' in sys.argv:
        idx = sys.argv.index('--project-id')
        if idx + 1 < len(sys.argv):
            project_id = sys.argv[idx + 1]
    
    if '--client-id' in sys.argv:
        idx = sys.argv.index('--client-id')
        if idx + 1 < len(sys.argv):
            client_id = sys.argv[idx + 1]
    
    # Verify gcloud access
    access_token = get_gcloud_access_token()
    if not access_token:
        print("\n⚠️  Could not get gcloud access token")
        print("   Please run: gcloud auth login theaicompany007@gmail.com")
        print("   Then: gcloud auth application-default login")
    
    success = configure_google_oauth(app_url, project_id, client_id)
    
    if success:
        print("\n✅ Google OAuth configuration complete!")
        sys.exit(0)
    else:
        print("\n⚠️  Please complete manual configuration in Google Cloud Console")
        sys.exit(0)  # Exit 0 because we provided instructions

if __name__ == '__main__':
    main()

