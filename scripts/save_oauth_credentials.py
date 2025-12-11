"""
Save Google OAuth credentials to .local.env file

Usage:
    python scripts/save_oauth_credentials.py --client-id CLIENT_ID --client-secret CLIENT_SECRET
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional

def save_to_env_file(env_file_path: Path, key: str, value: str, comment: str = None):
    """Add or update an environment variable in .env file"""
    if not env_file_path.exists():
        # Create new file
        with open(env_file_path, 'w') as f:
            if comment:
                f.write(f"# {comment}\n")
            f.write(f"{key}={value}\n")
        return True
    
    # Read existing file
    lines = []
    key_found = False
    key_pattern = re.compile(rf'^\s*{re.escape(key)}\s*=', re.IGNORECASE)
    
    with open(env_file_path, 'r') as f:
        for line in f:
            if key_pattern.match(line):
                # Update existing line
                if comment and not line.strip().startswith('#'):
                    lines.append(f"# {comment}\n")
                lines.append(f"{key}={value}\n")
                key_found = True
            else:
                lines.append(line)
    
    # Add new key if not found
    if not key_found:
        if comment:
            lines.append(f"\n# {comment}\n")
        lines.append(f"{key}={value}\n")
    
    # Write back
    with open(env_file_path, 'w') as f:
        f.writelines(lines)
    
    return True

def main():
    """Main function"""
    basedir = Path(__file__).parent.parent
    
    # Try .local.env first, then .env.local
    env_file = basedir / '.local.env'
    if not env_file.exists():
        env_file = basedir / '.env.local'
    
    # Get credentials from command line
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
    
    if not client_id or not client_secret:
        print("❌ Error: Both --client-id and --client-secret are required")
        print("\nUsage:")
        print("  python scripts/save_oauth_credentials.py --client-id CLIENT_ID --client-secret CLIENT_SECRET")
        sys.exit(1)
    
    print(f"\n📝 Saving OAuth credentials to: {env_file.name}")
    
    # Save credentials
    save_to_env_file(
        env_file,
        'GOOGLE_OAUTH_CLIENT_ID',
        client_id,
        'Google OAuth 2.0 Client ID for Supabase authentication'
    )
    
    save_to_env_file(
        env_file,
        'GOOGLE_OAUTH_CLIENT_SECRET',
        client_secret,
        'Google OAuth 2.0 Client Secret for Supabase authentication'
    )
    
    print("✅ Credentials saved successfully!")
    print(f"\n📋 Saved to: {env_file}")
    print(f"   GOOGLE_OAUTH_CLIENT_ID={client_id[:30]}...")
    print(f"   GOOGLE_OAUTH_CLIENT_SECRET={client_secret[:20]}...")
    print("\n💡 You can now run:")
    print("   python scripts/configure_google_oauth_client.py --url https://vani.ngrok.app")
    print("   (Credentials will be loaded automatically from .local.env)")

if __name__ == '__main__':
    main()





