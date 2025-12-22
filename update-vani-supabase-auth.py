#!/usr/bin/env python3
"""
VANI Supabase Auth Configuration Updater

Updates Supabase Auth configuration (Site URL and Redirect URLs) for VANI.
Specifically designed for VANI's routes and port (5000).

Usage:
    python3 update-vani-supabase-auth.py [--webhook-base-url https://vani.ngrok.app]
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from typing import Tuple

# Color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def load_env_file(filepath: str) -> dict:
    """Load environment variables from .env.local file"""
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
    return env_vars

def update_supabase_auth_config(supabase_url: str, access_token: str, webhook_base_url: str) -> Tuple[bool, str, list]:
    """Update Supabase Auth configuration (Site URL and Redirect URLs)"""
    try:
        # Extract project ref from Supabase URL
        match = re.match(r'https://([^.]+)\.supabase\.co', supabase_url)
        if not match:
            return False, "Invalid Supabase URL format", []
        
        project_ref = match.group(1)
        
        # Build required redirect URLs for VANI
        required_urls = [
            # Localhost for development
            'http://localhost:5000',
            'http://localhost:5000/command-center',
            'http://localhost:5000/login',
            # Production URLs
            webhook_base_url,
            f'{webhook_base_url}/api/auth/callback',
            f'{webhook_base_url}/command-center',
            f'{webhook_base_url}/login',
        ]
        
        # Remove duplicates while preserving order
        unique_urls = list(dict.fromkeys(required_urls))
        url_allow_list = ','.join(unique_urls)
        
        # Update auth configuration via Supabase Management API
        url = f'https://api.supabase.com/v1/projects/{project_ref}/config/auth'
        data = json.dumps({
            'site_url': webhook_base_url,
            'uri_allow_list': url_allow_list
        }).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            method='PATCH'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return True, f"Updated successfully", unique_urls
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get('message', error_body)
        except:
            error_msg = error_body
        return False, f"HTTP {e.code}: {error_msg}", []
    except Exception as e:
        return False, f"Error: {str(e)}", []

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Update VANI Supabase Auth Configuration')
    parser.add_argument('--env-file', default='.env.local', help='Path to .env.local file')
    parser.add_argument('--webhook-base-url', help='Webhook base URL (defaults to WEBHOOK_BASE_URL from .env.local)')
    
    args = parser.parse_args()
    
    # Determine VANI directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'vani' in script_dir.lower():
        vani_dir = script_dir
    else:
        possible_paths = [
            os.path.join(script_dir, '..', 'vani'),
            os.path.join(script_dir, 'vani'),
            '/home/postgres/vani',
            os.path.expanduser('~/vani'),
        ]
        vani_dir = None
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.isdir(abs_path):
                vani_dir = abs_path
                break
        
        if not vani_dir:
            print(f"{Colors.RED}Error: Could not find VANI directory{Colors.RESET}")
            print(f"Please run this script from the VANI directory or specify --env-file")
            sys.exit(1)
    
    env_file = os.path.join(vani_dir, args.env_file) if not os.path.isabs(args.env_file) else args.env_file
    
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}VANI Supabase Auth Configuration Updater{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    # Load environment variables
    env_vars = load_env_file(env_file)
    
    if not env_vars:
        print(f"{Colors.RED}Error: No environment variables found in {env_file}{Colors.RESET}")
        sys.exit(1)
    
    # Get required variables
    supabase_url = env_vars.get('SUPABASE_URL')
    access_token = env_vars.get('SUPABASE_ACCESS_TOKEN')
    webhook_base_url = args.webhook_base_url or env_vars.get('WEBHOOK_BASE_URL')
    
    if not supabase_url:
        print(f"{Colors.RED}Error: SUPABASE_URL not found in {env_file}{Colors.RESET}")
        sys.exit(1)
    
    if not access_token:
        print(f"{Colors.RED}Error: SUPABASE_ACCESS_TOKEN not found in {env_file}{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 Get your Personal Access Token from:{Colors.RESET}")
        print(f"   https://supabase.com/dashboard/account/tokens")
        print(f"{Colors.YELLOW}💡 Add to {env_file}: SUPABASE_ACCESS_TOKEN=sbp_your_token_here{Colors.RESET}")
        sys.exit(1)
    
    if not webhook_base_url:
        print(f"{Colors.RED}Error: WEBHOOK_BASE_URL not found in {env_file} and --webhook-base-url not provided{Colors.RESET}")
        sys.exit(1)
    
    # Validate webhook URL
    if not webhook_base_url.startswith('http'):
        print(f"{Colors.RED}Error: WEBHOOK_BASE_URL must be a valid URL (http:// or https://){Colors.RESET}")
        sys.exit(1)
    
    # Extract project ref for manual link
    match = re.match(r'https://([^.]+)\.supabase\.co', supabase_url)
    project_ref = match.group(1) if match else 'unknown'
    
    print(f"{Colors.CYAN}Configuration:{Colors.RESET}")
    print(f"  Supabase URL: {supabase_url}")
    print(f"  Project Ref: {project_ref}")
    print(f"  Site URL: {Colors.BOLD}{webhook_base_url}{Colors.RESET}")
    print(f"\n{Colors.CYAN}Redirect URLs to be set:{Colors.RESET}")
    
    redirect_urls = [
        'http://localhost:5000',
        'http://localhost:5000/command-center',
        'http://localhost:5000/login',
        webhook_base_url,
        f'{webhook_base_url}/api/auth/callback',
        f'{webhook_base_url}/command-center',
        f'{webhook_base_url}/login',
    ]
    
    for i, url in enumerate(redirect_urls, 1):
        print(f"  {i}. {url}")
    
    print(f"\n{Colors.BLUE}Updating Supabase Auth configuration...{Colors.RESET}\n")
    
    success, message, updated_urls = update_supabase_auth_config(supabase_url, access_token, webhook_base_url)
    
    if success:
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}\n")
        print(f"{Colors.GREEN}✅ Site URL updated to: {webhook_base_url}{Colors.RESET}")
        print(f"{Colors.GREEN}✅ Redirect URLs updated ({len(updated_urls)} total){Colors.RESET}\n")
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 VANI Supabase Auth configuration updated successfully!{Colors.RESET}\n")
    else:
        print(f"{Colors.RED}❌ Failed to update: {message}{Colors.RESET}\n")
        print(f"{Colors.YELLOW}💡 You can also update manually at:{Colors.RESET}")
        print(f"   https://supabase.com/dashboard/project/{project_ref}/auth/url-configuration\n")
        print(f"{Colors.YELLOW}📝 Manual configuration:{Colors.RESET}")
        print(f"   Site URL: {webhook_base_url}")
        print(f"   Redirect URLs:")
        for url in redirect_urls:
            print(f"     - {url}")
        print()
        sys.exit(1)

if __name__ == '__main__':
    main()


