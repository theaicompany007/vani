"""
Simple Google OAuth Configuration Helper

Opens your browser to the correct page and provides step-by-step instructions.
No automation - just guided manual configuration.

Usage:
    python scripts/configure_google_oauth_simple.py --url https://vani.ngrok.app
"""

import os
import sys
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)
load_dotenv(basedir / '.local.env', override=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
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

def main():
    """Main function"""
    app_url = get_app_url()
    
    if not app_url:
        print("❌ Error: Application URL not found")
        print("   Provide via --url argument or WEBHOOK_BASE_URL env var")
        sys.exit(1)
    
    if not GOOGLE_OAUTH_CLIENT_ID:
        print("❌ Error: OAuth Client ID not found")
        print("   Set GOOGLE_OAUTH_CLIENT_ID in .env.local or .local.env")
        sys.exit(1)
    
    # Build redirect URIs
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
    
    project_id = GOOGLE_CLOUD_PROJECT
    
    print("\n" + "="*70)
    print("  GOOGLE OAUTH CLIENT CONFIGURATION HELPER")
    print("="*70)
    print(f"\nProject: {project_id}")
    print(f"Client ID: {GOOGLE_OAUTH_CLIENT_ID}")
    print(f"App URL: {app_url}")
    if SUPABASE_URL:
        print(f"Supabase URL: {SUPABASE_URL}\n")
    
    # Construct the direct URL to the OAuth client
    project_number = GOOGLE_OAUTH_CLIENT_ID.split('-')[0] if '-' in GOOGLE_OAUTH_CLIENT_ID else None
    client_id_suffix = GOOGLE_OAUTH_CLIENT_ID.split('-', 1)[1] if '-' in GOOGLE_OAUTH_CLIENT_ID else GOOGLE_OAUTH_CLIENT_ID
    
    if project_number:
        oauth_client_url = f"https://console.cloud.google.com/apis/credentials/oauthclient/{project_number}-{client_id_suffix}?project={project_id}"
    else:
        oauth_client_url = f"https://console.cloud.google.com/apis/credentials?project={project_id}"
    
    print("\n📋 Step-by-Step Instructions:")
    print("="*70)
    
    print("\n1️⃣  Opening Google Cloud Console in your browser...")
    print(f"   URL: {oauth_client_url}")
    
    # Open browser
    try:
        webbrowser.open(oauth_client_url)
        print("   ✅ Browser opened")
    except Exception as e:
        print(f"   ⚠️  Could not open browser automatically: {e}")
        print(f"   Please open this URL manually: {oauth_client_url}")
    
    print("\n2️⃣  In the browser:")
    print("   - If prompted, log in to Google Cloud Console")
    print("   - You should see your OAuth client edit page")
    print("   - If not, find your OAuth client in the list and click on it")
    
    print("\n3️⃣  Find the 'Authorized redirect URIs' section")
    print("   (Usually a textarea or input field)")
    
    print("\n4️⃣  Add these redirect URIs (one per line):")
    print("   " + "="*60)
    for i, uri in enumerate(redirect_uris, 1):
        marker = "🔴 CRITICAL" if SUPABASE_URL and SUPABASE_URL in uri else f"   {i}."
        print(f"   {marker} {uri}")
    print("   " + "="*60)
    
    print("\n5️⃣  Click 'Save' button")
    
    print("\n6️⃣  Copy Client ID and Secret to Supabase:")
    print(f"   🔗 {SUPABASE_URL.replace('/rest/v1', '/dashboard/project')}/auth/providers" if SUPABASE_URL else "   (Get Supabase URL from .env.local)")
    print("   - Enable Google provider")
    print(f"   - Client ID: {GOOGLE_OAUTH_CLIENT_ID}")
    print("   - Client Secret: (from Google Console, click 'Show')")
    print("   - Save")
    
    print("\n" + "="*70)
    print("  ✅ CONFIGURATION COMPLETE")
    print("="*70)
    print("\n💡 Tip: Keep this terminal open to reference the redirect URIs")
    print("   The browser should now be open to the OAuth client edit page")
    
    input("\n👆 Press Enter when you've completed the configuration...")
    print("\n✅ Great! Your OAuth configuration should now be complete.")

if __name__ == '__main__':
    main()












