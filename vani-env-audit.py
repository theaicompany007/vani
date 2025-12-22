#!/usr/bin/env python3
"""
VANI Environment Variable Audit & Supabase Update Script

This script:
1. Audits all required/optional environment variables for VANI
2. Validates Supabase connection
3. Allows updating Supabase configuration
4. Provides a clear setup checklist

Usage:
    python3 vani-env-audit.py [--update-supabase] [--env-file /path/to/.env.local]
"""

import os
import sys
import json
import re
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import subprocess

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# VANI Required Environment Variables
REQUIRED_VARS = {
    # Core Flask
    'FLASK_ENV': 'Flask environment (production/development)',
    'SECRET_KEY': 'Flask secret key for sessions',
    
    # Supabase (Critical)
    'SUPABASE_URL': 'Supabase project URL (e.g., https://xxx.supabase.co)',
    'SUPABASE_KEY': 'Supabase anon key (JWT token)',
    'SUPABASE_SERVICE_ROLE_KEY': 'Supabase service role key (admin access)',
    
    # OpenAI
    'OPENAI_API_KEY': 'OpenAI API key for AI features',
    
    # Webhooks
    'WEBHOOK_BASE_URL': 'Base URL for webhooks (e.g., https://vani.ngrok.app)',
}

# VANI Optional Environment Variables
OPTIONAL_VARS = {
    # Email - Resend
    'RESEND_API_KEY': 'Resend API key for email sending',
    'RESEND_DOMAIN_ID': 'Resend domain ID',
    'USE_RESEND': 'Use Resend for emails (true/false)',
    
    # WhatsApp - Twilio
    'TWILIO_ACCOUNT_SID': 'Twilio Account SID',
    'TWILIO_AUTH_TOKEN': 'Twilio Auth Token',
    'TWILIO_WHATSAPP_NUMBER': 'Twilio WhatsApp number',
    'TWILIO_WHATSAPP_FROM': 'Twilio WhatsApp from number',
    
    # RAG Service
    'RAG_SERVICE_URL': 'RAG service URL (e.g., https://rag.theaicompany.co)',
    'RAG_API_KEY': 'RAG service API key',
    'RAG_ONLY': 'Use RAG-only mode (true/false)',
    
    # Redis
    'REDIS_HOST': 'Redis host (default: redis)',
    'REDIS_PORT': 'Redis port (default: 6379)',
    
    # Cal.com
    'CAL_COM_API_KEY': 'Cal.com API key for meeting scheduling',
    
    # Environment
    'VANI_ENVIRONMENT': 'Environment (prod/dev)',
    'NGROK_DOMAIN': 'Ngrok domain (e.g., vani.ngrok.app)',
    'SKIP_WEBHOOK_UPDATE': 'Skip webhook updates (true/false)',
    
    # Docker
    'DOCKER_CONTAINER': 'Running in Docker (true/false)',
    'PORT': 'Application port (default: 5000)',
    'FLASK_HOST': 'Flask host (default: 0.0.0.0)',
}

def load_env_file(filepath: str) -> Dict[str, str]:
    """Load environment variables from .env.local file"""
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
    return env_vars

def validate_supabase_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate Supabase URL format"""
    if not url:
        return False, "URL is empty"
    
    if not url.startswith('https://'):
        return False, "URL must start with https://"
    
    if '.supabase.co' not in url:
        return False, "URL must contain .supabase.co"
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, "Invalid URL format"
        return True, None
    except Exception as e:
        return False, f"URL parsing error: {str(e)}"

def test_supabase_connection(url: str, key: str) -> Tuple[bool, str]:
    """Test Supabase connection using curl"""
    try:
        # Test with a simple REST API call
        test_url = f"{url}/rest/v1/"
        cmd = [
            'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
            '-H', f'apikey: {key}',
            '-H', 'Authorization: Bearer ' + key,
            test_url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        status_code = result.stdout.strip()
        
        if status_code == '200' or status_code == '401':
            # 401 is OK - means API is reachable but auth might be needed
            return True, f"Connection successful (HTTP {status_code})"
        elif status_code == '000':
            return False, "Connection failed (network error)"
        else:
            return False, f"Connection failed (HTTP {status_code})"
    except subprocess.TimeoutExpired:
        return False, "Connection timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"

def print_section(title: str, color: str = Colors.CYAN):
    """Print a formatted section header"""
    print(f"\n{color}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def print_var_status(key: str, value: Optional[str], required: bool, description: str):
    """Print environment variable status"""
    if value:
        status = f"{Colors.GREEN}✓ SET{Colors.RESET}"
        # Mask sensitive values
        if any(sensitive in key.upper() for sensitive in ['KEY', 'TOKEN', 'SECRET', 'PASSWORD']):
            display_value = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
        else:
            display_value = value
        print(f"  {status} {Colors.BOLD}{key}{Colors.RESET}")
        print(f"      {description}")
        print(f"      Value: {Colors.CYAN}{display_value}{Colors.RESET}")
    else:
        status = f"{Colors.RED}✗ MISSING{Colors.RESET}" if required else f"{Colors.YELLOW}○ OPTIONAL{Colors.RESET}"
        print(f"  {status} {Colors.BOLD}{key}{Colors.RESET}")
        print(f"      {description}")
    print()

def update_supabase_auth_config(supabase_url: str, access_token: str, webhook_base_url: str) -> Tuple[bool, str]:
    """Update Supabase Auth configuration (Site URL and Redirect URLs)"""
    try:
        # Extract project ref from Supabase URL
        match = re.match(r'https://([^.]+)\.supabase\.co', supabase_url)
        if not match:
            return False, "Invalid Supabase URL format"
        
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
        
        # Remove duplicates
        unique_urls = list(dict.fromkeys(required_urls))
        url_allow_list = ','.join(unique_urls)
        
        # Update auth configuration via Supabase Management API
        import urllib.request
        import urllib.error
        
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
            return True, f"Updated successfully: Site URL={webhook_base_url}, {len(unique_urls)} redirect URLs"
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get('message', error_body)
        except:
            error_msg = error_body
        return False, f"HTTP {e.code}: {error_msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def update_supabase_config(env_file: str, new_url: str, new_key: str, new_service_key: str) -> bool:
    """Update Supabase configuration in .env.local file"""
    if not os.path.exists(env_file):
        print(f"{Colors.RED}Error: {env_file} not found{Colors.RESET}")
        return False
    
    try:
        # Read current file
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update or add Supabase variables
        updated = {'SUPABASE_URL': False, 'SUPABASE_KEY': False, 'SUPABASE_SERVICE_ROLE_KEY': False}
        new_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('SUPABASE_URL='):
                new_lines.append(f'SUPABASE_URL={new_url}\n')
                updated['SUPABASE_URL'] = True
            elif stripped.startswith('SUPABASE_KEY='):
                new_lines.append(f'SUPABASE_KEY={new_key}\n')
                updated['SUPABASE_KEY'] = True
            elif stripped.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                new_lines.append(f'SUPABASE_SERVICE_ROLE_KEY={new_service_key}\n')
                updated['SUPABASE_SERVICE_ROLE_KEY'] = True
            else:
                new_lines.append(line)
        
        # Add missing variables at the end
        if not updated['SUPABASE_URL']:
            new_lines.append(f'\n# Supabase Configuration\n')
            new_lines.append(f'SUPABASE_URL={new_url}\n')
        if not updated['SUPABASE_KEY']:
            new_lines.append(f'SUPABASE_KEY={new_key}\n')
        if not updated['SUPABASE_SERVICE_ROLE_KEY']:
            new_lines.append(f'SUPABASE_SERVICE_ROLE_KEY={new_service_key}\n')
        
        # Write back
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"{Colors.GREEN}✅ Updated Supabase configuration in {env_file}{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Error updating file: {str(e)}{Colors.RESET}")
        return False

def update_supabase_auth_config(supabase_url: str, access_token: str, webhook_base_url: str) -> Tuple[bool, str]:
    """Update Supabase Auth configuration (Site URL and Redirect URLs)"""
    try:
        # Extract project ref from Supabase URL
        import re
        match = re.match(r'https://([^.]+)\.supabase\.co', supabase_url)
        if not match:
            return False, "Invalid Supabase URL format"
        
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
        
        # Remove duplicates
        unique_urls = list(dict.fromkeys(required_urls))
        url_allow_list = ','.join(unique_urls)
        
        # Update auth configuration via Supabase Management API
        import urllib.request
        import json
        
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
            return True, f"Updated successfully: Site URL={webhook_base_url}, {len(unique_urls)} redirect URLs"
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return False, f"HTTP {e.code}: {error_body}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    import argparse
    parser = argparse.ArgumentParser(description='VANI Environment Variable Audit & Supabase Update')
    parser.add_argument('--env-file', default='.env.local', help='Path to .env.local file')
    parser.add_argument('--update-supabase', action='store_true', help='Update Supabase configuration')
    parser.add_argument('--supabase-url', help='New Supabase URL')
    parser.add_argument('--supabase-key', help='New Supabase anon key')
    parser.add_argument('--supabase-service-key', help='New Supabase service role key')
    parser.add_argument('--update-auth-config', action='store_true', help='Update Supabase Auth configuration (Site URL and Redirect URLs)')
    parser.add_argument('--webhook-base-url', help='Webhook base URL for Auth config (defaults to WEBHOOK_BASE_URL from .env.local)')
    
    args = parser.parse_args()
    
    # Determine VANI directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'vani' in script_dir.lower():
        vani_dir = script_dir
    else:
        # Try to find vani directory
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
    
    print_section("VANI Environment Variable Audit", Colors.BLUE)
    print(f"{Colors.CYAN}Environment file: {env_file}{Colors.RESET}\n")
    
    # Load environment variables
    env_vars = load_env_file(env_file)
    
    if not env_vars:
        print(f"{Colors.RED}⚠️  No environment variables found in {env_file}{Colors.RESET}")
        print(f"{Colors.YELLOW}Creating new file...{Colors.RESET}\n")
    else:
        print(f"{Colors.GREEN}✓ Loaded {len(env_vars)} environment variables{Colors.RESET}\n")
    
    # Audit required variables
    print_section("Required Variables", Colors.CYAN)
    missing_required = []
    for key, description in REQUIRED_VARS.items():
        value = env_vars.get(key)
        print_var_status(key, value, required=True, description=description)
        if not value:
            missing_required.append(key)
    
    # Audit optional variables
    print_section("Optional Variables", Colors.YELLOW)
    for key, description in OPTIONAL_VARS.items():
        value = env_vars.get(key)
        print_var_status(key, value, required=False, description=description)
    
    # Summary
    print_section("Summary", Colors.BLUE)
    total_required = len(REQUIRED_VARS)
    set_required = total_required - len(missing_required)
    print(f"{Colors.BOLD}Required Variables:{Colors.RESET} {Colors.GREEN}{set_required}/{total_required} set{Colors.RESET}")
    
    if missing_required:
        print(f"\n{Colors.RED}Missing Required Variables:{Colors.RESET}")
        for key in missing_required:
            print(f"  - {key}")
    
    # Validate Supabase
    print_section("Supabase Validation", Colors.CYAN)
    supabase_url = env_vars.get('SUPABASE_URL')
    supabase_key = env_vars.get('SUPABASE_KEY')
    supabase_service_key = env_vars.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if supabase_url:
        is_valid, error = validate_supabase_url(supabase_url)
        if is_valid:
            print(f"{Colors.GREEN}✓ Supabase URL format is valid{Colors.RESET}")
            print(f"  URL: {Colors.CYAN}{supabase_url}{Colors.RESET}\n")
            
            if supabase_key:
                print(f"{Colors.BLUE}Testing Supabase connection...{Colors.RESET}")
                connected, message = test_supabase_connection(supabase_url, supabase_key)
                if connected:
                    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}\n")
                else:
                    print(f"{Colors.RED}✗ {message}{Colors.RESET}\n")
            else:
                print(f"{Colors.YELLOW}⚠️  Cannot test connection: SUPABASE_KEY not set{Colors.RESET}\n")
        else:
            print(f"{Colors.RED}✗ Supabase URL validation failed: {error}{Colors.RESET}\n")
    else:
        print(f"{Colors.RED}✗ SUPABASE_URL not set{Colors.RESET}\n")
    
    if supabase_key:
        print(f"{Colors.GREEN}✓ SUPABASE_KEY is set{Colors.RESET}")
        print(f"  Key: {Colors.CYAN}{supabase_key[:20]}...{Colors.RESET}\n")
    else:
        print(f"{Colors.RED}✗ SUPABASE_KEY not set{Colors.RESET}\n")
    
    if supabase_service_key:
        print(f"{Colors.GREEN}✓ SUPABASE_SERVICE_ROLE_KEY is set{Colors.RESET}")
        print(f"  Key: {Colors.CYAN}{supabase_service_key[:20]}...{Colors.RESET}\n")
    else:
        print(f"{Colors.RED}✗ SUPABASE_SERVICE_ROLE_KEY not set{Colors.RESET}\n")
    
    # Update Supabase if requested
    if args.update_supabase:
        print_section("Updating Supabase Configuration", Colors.BLUE)
        
        if not all([args.supabase_url, args.supabase_key, args.supabase_service_key]):
            print(f"{Colors.RED}Error: --supabase-url, --supabase-key, and --supabase-service-key are required{Colors.RESET}")
            sys.exit(1)
        
        # Validate new URL
        is_valid, error = validate_supabase_url(args.supabase_url)
        if not is_valid:
            print(f"{Colors.RED}Error: Invalid Supabase URL: {error}{Colors.RESET}")
            sys.exit(1)
        
        # Update configuration
        if update_supabase_config(env_file, args.supabase_url, args.supabase_key, args.supabase_service_key):
            print(f"\n{Colors.GREEN}✅ Supabase configuration updated successfully!{Colors.RESET}")
            print(f"{Colors.YELLOW}⚠️  Remember to restart VANI container for changes to take effect:{Colors.RESET}")
            print(f"   docker compose -f docker-compose.worker.yml restart vani")
        else:
            sys.exit(1)
    
    # Update Supabase Auth configuration if requested
    if args.update_auth_config:
        print_section("Updating Supabase Auth Configuration", Colors.BLUE)
        
        supabase_url_for_auth = supabase_url or env_vars.get('SUPABASE_URL')
        access_token = env_vars.get('SUPABASE_ACCESS_TOKEN')
        webhook_base_url = args.webhook_base_url or env_vars.get('WEBHOOK_BASE_URL')
        
        if not supabase_url_for_auth:
            print(f"{Colors.RED}Error: SUPABASE_URL not found in environment{Colors.RESET}")
            sys.exit(1)
        
        if not access_token:
            print(f"{Colors.RED}Error: SUPABASE_ACCESS_TOKEN not found in environment{Colors.RESET}")
            print(f"{Colors.YELLOW}💡 Get your Personal Access Token from:{Colors.RESET}")
            print(f"   https://supabase.com/dashboard/account/tokens")
            print(f"{Colors.YELLOW}💡 Add to .env.local: SUPABASE_ACCESS_TOKEN=sbp_your_token_here{Colors.RESET}")
            sys.exit(1)
        
        if not webhook_base_url:
            print(f"{Colors.RED}Error: WEBHOOK_BASE_URL not found in environment and --webhook-base-url not provided{Colors.RESET}")
            sys.exit(1)
        
        # Validate webhook URL
        if not webhook_base_url.startswith('http'):
            print(f"{Colors.RED}Error: WEBHOOK_BASE_URL must be a valid URL (http:// or https://){Colors.RESET}")
            sys.exit(1)
        
        print(f"{Colors.CYAN}Updating Supabase Auth configuration...{Colors.RESET}")
        print(f"  Site URL: {Colors.BOLD}{webhook_base_url}{Colors.RESET}")
        print(f"  Redirect URLs will include:{Colors.RESET}")
        print(f"    - {webhook_base_url}")
        print(f"    - {webhook_base_url}/api/auth/callback")
        print(f"    - {webhook_base_url}/command-center")
        print(f"    - {webhook_base_url}/login")
        print(f"    - http://localhost:5000 (and related localhost URLs)")
        print()
        
        success, message = update_supabase_auth_config(supabase_url_for_auth, access_token, webhook_base_url)
        
        if success:
            print(f"{Colors.GREEN}✅ {message}{Colors.RESET}\n")
        else:
            print(f"{Colors.RED}❌ {message}{Colors.RESET}\n")
            print(f"{Colors.YELLOW}💡 You can also update manually at:{Colors.RESET}")
            project_ref = supabase_url_for_auth.split('//')[1].split('.')[0]
            print(f"   https://supabase.com/dashboard/project/{project_ref}/auth/url-configuration\n")
            sys.exit(1)
    
    # Check Supabase Auth configuration
    if supabase_url and env_vars.get('SUPABASE_ACCESS_TOKEN'):
        print_section("Supabase Auth Configuration", Colors.CYAN)
        webhook_base_url = env_vars.get('WEBHOOK_BASE_URL')
        if webhook_base_url:
            print(f"{Colors.GREEN}✓ WEBHOOK_BASE_URL is set: {webhook_base_url}{Colors.RESET}")
            print(f"{Colors.CYAN}💡 To update Supabase Auth config (Site URL & Redirect URLs), run:{Colors.RESET}")
            print(f"   python3 vani-env-audit.py --update-auth-config")
            if webhook_base_url != 'https://vani.ngrok.app':
                print(f"{Colors.YELLOW}⚠️  Current WEBHOOK_BASE_URL is {webhook_base_url}{Colors.RESET}")
                print(f"{Colors.YELLOW}   If you want to use production URL, update WEBHOOK_BASE_URL first{Colors.RESET}")
        else:
            print(f"{Colors.RED}✗ WEBHOOK_BASE_URL not set{Colors.RESET}")
        print()
    
    # Final checklist
    print_section("Setup Checklist", Colors.BLUE)
    checklist_items = [
        ("All required variables set", len(missing_required) == 0),
        ("Supabase URL valid", supabase_url and validate_supabase_url(supabase_url)[0]),
        ("Supabase connection working", supabase_url and supabase_key and test_supabase_connection(supabase_url, supabase_key)[0]),
        ("Webhook base URL set", bool(env_vars.get('WEBHOOK_BASE_URL'))),
        ("OpenAI API key set", bool(env_vars.get('OPENAI_API_KEY'))),
    ]
    
    for item, status in checklist_items:
        status_icon = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.RED}✗{Colors.RESET}"
        print(f"  {status_icon} {item}")
    
    print()
    
    if len(missing_required) == 0 and all(status for _, status in checklist_items[1:]):
        print(f"{Colors.GREEN}{Colors.BOLD}✅ VANI is ready to use!{Colors.RESET}\n")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Please complete the missing configuration above{Colors.RESET}\n")

if __name__ == '__main__':
    main()

