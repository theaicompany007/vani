#!/usr/bin/env python3
"""
VANI Outreach Command Center - Startup Script
Checks everything and starts the Flask server with ngrok URL display

Features:
- Environment validation
- Database connection check
- Ngrok tunnel management
- Webhook auto-configuration
- Admin tools (User Management, Signatures, Knowledge Base, Google Drive, Tools)
- AI Target Finder with Knowledge Base integration
- Contact & Company management
- Multi-channel outreach (Email, WhatsApp, LinkedIn)
- Google Drive to RAG sync (Super Users)
"""
import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from dotenv import load_dotenv

# Add app directory to path
basedir = Path(__file__).parent
sys.path.insert(0, str(basedir))

# Load environment variables
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

# Fix Supabase compatibility (must be at module level)
try:
    sys.path.insert(0, str(basedir))
    from scripts.fix_supabase_client import *
except Exception:
    pass  # If fix fails, continue anyway


def is_docker_environment():
    """Check if running in Docker container"""
    return os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') == 'true'


def kill_existing_processes():
    """Kill any existing Flask and ngrok processes"""
    print("[0/5] Cleaning up existing processes...")
    
    flask_port = int(os.getenv('FLASK_PORT', '5000'))
    
    # Kill Flask processes on port 5000
    try:
        if sys.platform == 'win32':
            # Windows: Find process using port 5000
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if f':{flask_port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 0:
                        pid = parts[-1]
                        try:
                            subprocess.run(['taskkill', '/F', '/PID', pid], 
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL,
                                         timeout=3)
                            print(f"  [OK] Killed Flask process on port {flask_port} (PID: {pid})")
                        except:
                            pass
        else:
            # Linux/Mac: Use lsof
            result = subprocess.run(
                ['lsof', '-ti', f':{flask_port}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        subprocess.run(['kill', '-9', pid], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL,
                                     timeout=3)
                        print(f"  [OK] Killed Flask process on port {flask_port} (PID: {pid})")
                    except:
                        pass
    except Exception as e:
        print(f"  [!] Could not check Flask processes: {e}")
    
    # Kill ngrok processes
    try:
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/IM', 'ngrok.exe'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         timeout=3)
            print("  [OK] Killed ngrok processes")
        else:
            subprocess.run(['pkill', '-f', 'ngrok'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         timeout=3)
            print("  [OK] Killed ngrok processes")
    except Exception:
        pass  # ngrok may not be running
    
    # Wait a moment for processes to fully terminate
    time.sleep(2)
    print("")


def print_header():
    """Print startup header"""
    print("\n" + "="*70)
    print("  VANI OUTREACH COMMAND CENTER - STARTUP")
    print("="*70 + "\n")


def check_environment():
    """Check environment variables"""
    print("[1/5] Checking environment variables...")
    
    required_vars = {
        'SUPABASE_URL': 'Supabase project URL',
        'SUPABASE_KEY': 'Supabase anon key',
        'SUPABASE_SERVICE_KEY': 'Supabase service role key',
        'RESEND_API_KEY': 'Resend API key',
        'TWILIO_ACCOUNT_SID': 'Twilio Account SID',
        'TWILIO_AUTH_TOKEN': 'Twilio Auth Token',
        'OPENAI_API_KEY': 'OpenAI API key',
    }
    
    # Optional but recommended for AI features
    optional_vars = {
        'RAG_API_KEY': 'RAG service API key (for AI Target Finder & Knowledge Base)',
        'RAG_SERVICE_URL': 'RAG service URL (default: https://rag.theaicompany.co)',
        'GEMINI_API_KEY': 'Google Gemini API key (for AI Target Finder - Notebook LM)',
        'SUPABASE_ACCESS_TOKEN': 'Supabase Personal Access Token (for OAuth URL auto-config)',
        'GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON': 'Google Drive service account JSON (for Google Drive to RAG sync)',
        'GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH': 'Path to Google Drive service account JSON file (alternative to JSON env var)',
    }
    
    # Optional Twilio WhatsApp (sandbox or paid)
    optional_twilio = {
        'TWILIO_SANDBOX_WHATSAPP_NUMBER': 'Twilio WhatsApp Sandbox number (for free testing)',
        'TWILIO_WHATSAPP_NUMBER': 'Twilio WhatsApp number (for paid account)',
        'TWILIO_PHONE_NUMBER': 'Twilio SMS phone number',
    }
    
    missing = []
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"  [X] {var} - {desc}")
        else:
            # Mask sensitive values: show first 4 + last 4 chars, or ********** if too short
            masked = value if len(value) <= 8 else f"{value[:4]}...{value[-4:]}"
            print(f"  [OK] {var:25} = {masked}")
            # Show full value instead of masking
            # print(f"  [OK] {var:25} = {value}")
    
    # Check optional variables
    missing_optional = []
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if not value:
            missing_optional.append(f"  [!] {var:25} - {desc} (optional)")
        else:
            # Mask sensitive values: show first 4 + last 4 chars, or ********** if too short
            masked = value if len(value) <= 8 else f"{value[:4]}...{value[-4:]}"
            print(f"  [OK] {var:25} = {masked}")
            # Show full value instead of masking
            # print(f"  [OK] {var:25} = {value}")
    
    # Check optional Twilio variables
    for var, desc in optional_twilio.items():
        value = os.getenv(var)
        if not value:
            # Only show warning if neither sandbox nor regular WhatsApp number is set
            if var == 'TWILIO_SANDBOX_WHATSAPP_NUMBER' and not os.getenv('TWILIO_WHATSAPP_NUMBER'):
                missing_optional.append(f"  [!] {var:25} - {desc} (optional, or set TWILIO_WHATSAPP_NUMBER)")
            elif var != 'TWILIO_SANDBOX_WHATSAPP_NUMBER':
                missing_optional.append(f"  [!] {var:25} - {desc} (optional)")
        else:
             # Mask sensitive values: show first 4 + last 4 chars, or ********** if too short
            masked = value if len(value) <= 8 else f"{value[:4]}...{value[-4:]}"
            print(f"  [OK] {var:25} = {masked}")
            # Show full value instead of masking
            # print(f"  [OK] {var:25} = {value}")

    if missing:
        print("\n[X] Missing required environment variables:")
        for item in missing:
            print(item)
        print("\n[!] Please check your .env.local file")
        return False
    
    if missing_optional:
        print("\n[!] Optional environment variables (AI features may be limited):")
        for item in missing_optional:
            print(item)
        print("    These are recommended for AI-powered features")
    
    # Check AI Target Finder availability
    check_ai_finder_access()
    
    print("[OK] All required environment variables are set\n")
    return True


def check_ai_finder_access():
    """Check and report AI Target Finder and Knowledge Base feature availability"""
    print("\n[AI] AI Features Status:")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    rag_key = os.getenv('RAG_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    # OpenAI is required for AI features
    if openai_key:
        print("  [OK] OpenAI API configured - Basic AI features available")
    else:
        print("  [X] OpenAI API NOT configured - AI Target Finder will NOT work")
        print("      Set OPENAI_API_KEY in .env.local")
        return
    
    # RAG and Gemini are optional but enhance functionality
    features_available = []
    features_missing = []
    
    # Check RAG service (used by both AI Target Finder and Knowledge Base)
    if rag_key:
        features_available.append("RAG service (AI Target Finder + Knowledge Base)")
    else:
        features_missing.append("RAG service (AI Target Finder & Knowledge Base will be limited)")
    
    if gemini_key:
        features_available.append("Gemini/Notebook LM integration")
    else:
        features_missing.append("Gemini API (Notebook LM integration - optional)")
    
    if features_available:
        print("  [OK] Enhanced features available:")
        for feature in features_available:
            print(f"       - {feature}")
    
    if features_missing:
        print("  [!] Optional enhancements not configured:")
        for feature in features_missing:
            print(f"       - {feature}")
        print("      AI Target Finder will work with reduced functionality")
        print("      Knowledge Base queries will be limited without RAG_API_KEY")
    
    # Check Google Drive integration
    google_drive_json = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON')
    google_drive_path = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH')
    google_drive_configured = bool(google_drive_json or google_drive_path)
    
    if google_drive_configured:
        features_available.append("Google Drive sync (Admin → Google Drive)")
    else:
        features_missing.append("Google Drive sync (optional - see GOOGLE_DRIVE_SETUP.md)")
    
    if openai_key and rag_key and gemini_key:
        print("  [✓] Full AI capabilities available (Target Finder + Knowledge Base)!")
    elif openai_key and rag_key:
        print("  [✓] AI Target Finder + Knowledge Base available!")
    elif openai_key:
        print("  [~] AI Target Finder available with basic functionality")
        print("  [~] Knowledge Base requires RAG_API_KEY for full functionality")
    
    # Google Drive status
    if google_drive_configured:
        print("  [✓] Google Drive integration configured (Admin → Google Drive tab available)")
    else:
        print("  [~] Google Drive integration not configured (optional)")
        print("      See GOOGLE_DRIVE_SETUP.md for setup instructions")


def check_database():
    """Check database connection"""
    print("[2/5] Checking database connection...")
    
    try:
        from supabase import create_client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("  [!] Supabase credentials not found")
            return False
        
        client = create_client(supabase_url, supabase_key)
        
        # Try to query targets table
        try:
            result = client.table('targets').select('id').limit(1).execute()
            print("  [OK] Database connected - Tables accessible")
            return True
        except Exception as e:
            error_str = str(e)
            if any(phrase in error_str.lower() for phrase in ['does not exist', 'not find the table', 'pgrst205']):
                print("  [!] Database connected but tables don't exist")
                print("      Run: python scripts/create_database_tables_direct.py")
                return False
            else:
                print(f"  [X] Database error: {error_str[:100]}")
                return False
                
    except Exception as e:
        print(f"  [X] Database connection failed: {str(e)[:100]}")
        return False


def detect_environment(ngrok_url: str = None) -> str:
    """Detect if running in dev or prod environment"""
    # Priority 1: Explicit environment variable
    env = os.getenv('VANI_ENVIRONMENT', '').lower()
    if env in ['dev', 'development', 'prod', 'production']:
        return 'dev' if env in ['dev', 'development'] else 'prod'
    
    # Priority 2: Detect from ngrok URL or WEBHOOK_BASE_URL
    url = ngrok_url or os.getenv('WEBHOOK_BASE_URL') or os.getenv('NGROK_DOMAIN')
    if url:
        url_lower = url.lower()
        if 'vani-dev.ngrok' in url_lower:
            return 'dev'
        elif 'vani.ngrok' in url_lower and 'vani-dev' not in url_lower:
            return 'prod'
    
    # Default: assume dev for safety (more permissive)
    return 'dev'


def configure_webhooks_with_url(webhook_url: str):
    """Configure webhooks using the provided URL with environment-aware safety checks"""
    # Check if webhook updates should be skipped
    skip_update = os.getenv('SKIP_WEBHOOK_UPDATE', 'false').lower() == 'true'
    if skip_update:
        print("  [*] SKIP_WEBHOOK_UPDATE is set - skipping webhook configuration")
        return
    
    try:
        # Detect environment
        environment = detect_environment(webhook_url)
        print(f"  [*] Detected environment: {environment.upper()}")
        print(f"  [*] Target webhook URL: {webhook_url}")
        
        # Temporarily set WEBHOOK_BASE_URL if not already set
        original_url = os.getenv('WEBHOOK_BASE_URL')
        if not original_url:
            os.environ['WEBHOOK_BASE_URL'] = webhook_url
        
        # Import and run webhook configuration
        sys.path.insert(0, str(basedir))
        from scripts.configure_webhooks import WebhookConfigurator
        
        print(f"  [*] Configuring webhooks for: {webhook_url}")
        configurator = WebhookConfigurator(environment=environment)
        results = configurator.configure_all()
        
        # Restore original value
        if not original_url:
            if 'WEBHOOK_BASE_URL' in os.environ:
                del os.environ['WEBHOOK_BASE_URL']
        
        # Check results
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(results)
        
        if success_count == total_count:
            print(f"  [OK] All webhooks configured successfully ({success_count}/{total_count})")
        elif success_count > 0:
            print(f"  [!] Webhooks partially configured ({success_count}/{total_count})")
            for service, result in results.items():
                if not result.get('success'):
                    print(f"      - {service.upper()}: {result.get('error', 'Failed')}")
            print("      Run 'python scripts/configure_webhooks.py' for details")
        else:
            print(f"  [!] Webhook configuration failed for all services")
            print("      Run 'python scripts/configure_webhooks.py' for details")
        
    except ImportError as e:
        print(f"  [!] Could not import webhook configurator: {e}")
    except Exception as e:
        print(f"  [!] Webhook configuration error: {e}")
        import traceback
        traceback.print_exc()


def check_ngrok():
    """Check if ngrok is running and get URL"""
    print("[3/5] Checking ngrok tunnel...")
    
    try:
        import requests
        response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            if tunnels:
                # Find HTTP tunnel
                http_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                if not http_tunnel:
                    http_tunnel = next((t for t in tunnels if 'http' in t.get('proto', '')), None)
                
                if http_tunnel:
                    public_url = http_tunnel.get('public_url')
                    print(f"  [OK] Ngrok tunnel active: {public_url}")
                    # Note: Webhooks will be configured later after Flask starts
                    return public_url
                else:
                    print("  [!] Ngrok running but no HTTP tunnel found")
                    return None
            else:
                print("  [!] Ngrok running but no tunnels found")
                return None
        else:
            print("  [!] Ngrok API not responding")
            return None
            
    except requests.exceptions.RequestException:
        print("  [!] Ngrok not running (webhooks won't work)")
        print("      Start with: .\\scripts\\start_ngrok.ps1")
        print("      Or set WEBHOOK_BASE_URL in .env.local for manual configuration")
        return None
    except Exception as e:
        print(f"  [!] Could not check ngrok: {e}")
        return None


def configure_webhooks_with_url(webhook_url: str):
    """Configure webhooks using the provided URL"""
    try:
        # Temporarily set WEBHOOK_BASE_URL if not already set
        original_url = os.getenv('WEBHOOK_BASE_URL')
        if not original_url:
            os.environ['WEBHOOK_BASE_URL'] = webhook_url
        
        # Import and run webhook configuration
        sys.path.insert(0, str(Path(__file__).parent))
        from scripts.configure_webhooks import WebhookConfigurator
        
        configurator = WebhookConfigurator()
        results = configurator.configure_all()
        
        # Restore original value
        if not original_url:
            if 'WEBHOOK_BASE_URL' in os.environ:
                del os.environ['WEBHOOK_BASE_URL']
        
        # Check results
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(results)
        
        if success_count == total_count:
            print(f"  [OK] All webhooks configured successfully ({success_count}/{total_count})")
        else:
            print(f"  [!] Webhooks partially configured ({success_count}/{total_count})")
            print("      Run 'python scripts/configure_webhooks.py' for details")
        
    except ImportError as e:
        print(f"  [!] Could not import webhook configurator: {e}")
    except Exception as e:
        print(f"  [!] Webhook configuration error: {e}")
        import traceback
        traceback.print_exc()


def get_expected_ngrok_url():
    """Get expected ngrok URL from configuration"""
    # Try to load from config
    try:
        from scripts.load_ngrok_config import get_ngrok_config
        config = get_ngrok_config()
        return config.get('webhook_base_url') or config.get('live_url')
    except Exception:
        # Fallback to environment
        return os.getenv('WEBHOOK_BASE_URL')


def start_ngrok_tunnel(port=5000):
    """Start ngrok tunnel in background"""
    try:
        import shutil
        ngrok_path = shutil.which('ngrok')
        if not ngrok_path:
            print("  [!] ngrok not found in PATH")
            print("      Install ngrok: https://ngrok.com/download")
            print("      Or add ngrok to your PATH")
            return None
        
        print(f"  [*] Found ngrok at: {ngrok_path}")
        
        # Verify Flask is accessible before starting ngrok
        print("  Verifying Flask is accessible on port {}...".format(port))
        flask_ok = False
        try:
            import requests
            # Try both 127.0.0.1 and localhost
            for test_host in ['127.0.0.1', 'localhost']:
                try:
                    flask_check = requests.get(f'http://{test_host}:{port}', timeout=3)
                    if flask_check.status_code in [200, 404, 500, 302]:
                        flask_ok = True
                        print(f"  [OK] Flask accessible on {test_host}:{port}")
                        break
                except requests.exceptions.ConnectionError:
                    continue
                except Exception:
                    continue
            
            if not flask_ok:
                print(f"  [X] Flask not accessible on port {port}")
                print(f"      Tried: http://127.0.0.1:{port} and http://localhost:{port}")
                print("      Cannot start ngrok - Flask must be running first")
                return None
        except Exception as e:
            print(f"  [!] Could not verify Flask: {e}")
            return None
        
        # Check if ngrok is already running and get existing tunnels
        existing_tunnels = []
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=1)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    # Check if there's already a tunnel for port 5000
                    for tunnel in tunnels:
                        addr = tunnel.get('config', {}).get('addr', '')
                        if f':{port}' in addr or addr.endswith(str(port)):
                            public_url = tunnel.get('public_url')
                            print(f"  [OK] Found existing ngrok tunnel for port {port}: {public_url}")
                            return public_url
                        existing_tunnels.append(tunnel)
                    
                    if existing_tunnels:
                        print(f"  [!] Found {len(existing_tunnels)} existing tunnel(s), but none for port {port}")
                        print("      Existing tunnels:")
                        for tunnel in existing_tunnels:
                            print(f"        - {tunnel.get('public_url')} -> {tunnel.get('config', {}).get('addr', 'unknown')}")
        except:
            pass
        
        # Get domain from config - prioritize environment variables
        domain = None
        use_tunnel = False
        
        # Priority 1: NGROK_DOMAIN environment variable
        domain = os.getenv('NGROK_DOMAIN')
        if domain:
            print(f"  [*] Found NGROK_DOMAIN from environment: {domain}")
        
        # Priority 2: Extract from WEBHOOK_BASE_URL
        if not domain:
            webhook_url = os.getenv('WEBHOOK_BASE_URL')
            if webhook_url and 'ngrok.app' in webhook_url:
                import re
                match = re.search(r'https?://([^/]+)', webhook_url)
                if match:
                    domain = match.group(1)
                    print(f"  [*] Extracted domain from WEBHOOK_BASE_URL: {domain}")
        
        # Priority 3: Load from config files
        if not domain:
            try:
                from scripts.load_ngrok_config import load_ngrok_config
                config = load_ngrok_config()
                domain = config.get('domain')
                if domain:
                    print(f"  [*] Found domain from config: {domain}")
            except Exception as e:
                print(f"  [!] Could not load config: {e}")
        
        # Check ngrok.yml for tunnel config - but only use it if domain matches
        config_path = os.path.join(os.getenv('LOCALAPPDATA', ''), 'ngrok', 'ngrok.yml')
        if not os.path.exists(config_path):
            config_path = os.path.join(os.getenv('USERPROFILE', ''), '.ngrok2', 'ngrok.yml')
        
        tunnel_domain = None
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    content = f.read()
                    # Check for vani tunnel and extract its domain
                    if 'vani:' in content:
                        # Try to extract domain from tunnel config
                        import re
                        # Look for domain: vani.ngrok.app or domain: vani-dev.ngrok.app
                        domain_match = re.search(r'vani:.*?domain:\s*([^\s\n]+)', content, re.DOTALL)
                        if domain_match:
                            tunnel_domain = domain_match.group(1).strip()
                            print(f"  [*] Found 'vani' tunnel in ngrok.yml with domain: {tunnel_domain}")
                        
                        # Only use tunnel config if:
                        # 1. No domain specified in environment (use tunnel as-is), OR
                        # 2. Tunnel domain matches desired domain
                        if not domain:
                            # No domain specified, use tunnel config
                            use_tunnel = True
                            print("  [*] No domain specified, using 'vani' tunnel from ngrok.yml")
                        elif tunnel_domain and tunnel_domain == domain:
                            # Tunnel domain matches desired domain
                            use_tunnel = True
                            print(f"  [*] Tunnel domain matches desired domain, using 'vani' tunnel")
                        else:
                            # Tunnel domain doesn't match, use direct domain flag instead
                            print(f"  [*] Tunnel domain ({tunnel_domain}) doesn't match desired domain ({domain})")
                            print(f"      Using direct domain flag instead of tunnel config")
                            use_tunnel = False
            except Exception as e:
                print(f"  [!] Error reading ngrok.yml: {e}")
        
        # Start ngrok
        if use_tunnel:
            # Use tunnel config
            print("  [*] Starting ngrok with: ngrok start vani")
            process = subprocess.Popen(
                [ngrok_path, 'start', 'vani'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        elif domain:
            # Use domain flag
            print(f"  [*] Starting ngrok with domain: {domain}")
            print(f"      Command: ngrok http {port} --domain={domain}")
            process = subprocess.Popen(
                [ngrok_path, 'http', str(port), '--domain', domain],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        else:
            # Use random URL
            print("  [*] Starting ngrok with random URL (no domain configured)")
            print(f"      Command: ngrok http {port}")
            process = subprocess.Popen(
                [ngrok_path, 'http', str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        
        # Check if process started successfully
        time.sleep(2)  # Give ngrok more time to start and show errors
        if process.poll() is not None:
            # Process exited immediately - there was an error
            stdout, stderr = process.communicate()
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else stdout.decode('utf-8', errors='ignore') if stdout else 'Unknown error'
            print(f"  [X] Ngrok failed to start!")
            print(f"      Error: {error_msg}")
            
            # Provide specific guidance based on error
            if 'authtoken' in error_msg.lower():
                print("      💡 Run: ngrok config add-authtoken YOUR_TOKEN")
            elif 'domain' in error_msg.lower() or 'reserved' in error_msg.lower():
                print(f"      💡 Make sure domain '{domain}' is reserved in ngrok dashboard")
                print("      💡 Go to: https://dashboard.ngrok.com/cloud-edge/domains")
            elif 'exceeded' in error_msg.lower() or 'maximum' in error_msg.lower() or 'concurrent' in error_msg.lower() or 'ERR_NGROK_18021' in error_msg:
                print("      💡 You've exceeded the maximum concurrent endpoints for your ngrok plan")
                print("      💡 Solutions:")
                print("         1. Stop other ngrok tunnels running elsewhere")
                print("         2. Check running tunnels: http://localhost:4040/api/tunnels")
                print("         3. Kill all ngrok processes: taskkill /F /IM ngrok.exe")
                print("         4. Upgrade your ngrok plan: https://dashboard.ngrok.com/billing/choose-a-plan")
                print("         5. Or use existing tunnel if one is already running for port 5000")
            elif 'ERR_NGROK' in error_msg:
                print("      💡 Check ngrok error docs: https://ngrok.com/docs/errors/")
            return None
        else:
            print("  [OK] Ngrok process started")
        
        # Wait for ngrok to start and get URL
        print("  [*] Waiting for ngrok to initialize...")
        time.sleep(3)  # Give ngrok time to start
        
        # Get the URL from ngrok API
        try:
            import requests
            max_retries = 15
            for attempt in range(max_retries):
                try:
                    response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        tunnels = data.get('tunnels', [])
                        if tunnels:
                            # Prefer HTTPS tunnel
                            https_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                            if https_tunnel:
                                url = https_tunnel.get('public_url')
                                print(f"  [OK] Ngrok tunnel active: {url}")
                                return url
                            # Fallback to any HTTP tunnel
                            http_tunnel = next((t for t in tunnels if 'http' in t.get('proto', '')), None)
                            if http_tunnel:
                                url = http_tunnel.get('public_url')
                                print(f"  [OK] Ngrok tunnel active: {url}")
                                return url
                except requests.exceptions.ConnectionError:
                    # Ngrok API not ready yet
                    if attempt < max_retries - 1:
                        time.sleep(1)
                    continue
                except Exception as e:
                    print(f"  [!] Error checking ngrok API: {e}")
                    time.sleep(1)
                    continue
            
            print(f"  [!] Ngrok started but URL not available after {max_retries} attempts")
            print("      Check ngrok dashboard: http://localhost:4040")
            return None
        except Exception as e:
            print(f"  [!] Could not get ngrok URL: {e}")
            return None
        
    except Exception as e:
        print(f"  [!] Could not start ngrok: {e}")
        return None


def start_flask_app(ngrok_url=None):
    """Start Flask application and ngrok"""
    print("[4/5] Starting Flask application...")
    print("\n" + "="*70)
    print("  FLASK SERVER STARTING")
    print("="*70 + "\n")
    
    # Use PORT environment variable if available (for Docker/Cloud)
    flask_port = int(os.getenv('PORT', os.getenv('FLASK_PORT', '5000')))
    
    # In Docker, bind to 0.0.0.0; otherwise use 127.0.0.1 for ngrok
    if is_docker_environment():
        flask_host = os.getenv('FLASK_HOST', '0.0.0.0')
    else:
        flask_host = os.getenv('FLASK_HOST', '127.0.0.1')
        # For ngrok to connect, Flask must bind to 127.0.0.1 (not 0.0.0.0)
        if flask_host == '0.0.0.0':
            flask_host = '127.0.0.1'  # ngrok needs 127.0.0.1
    
    print(f"Local URL:        http://{flask_host}:{flask_port}")
    print(f"Command Center:   http://{flask_host}:{flask_port}/command-center")
    
    # Start Flask in a thread so we can start ngrok after
    flask_started = threading.Event()
    flask_accessible = False
    flask_thread = None
    flask_app = None
    flask_shutdown = None
    
    def run_flask():
        nonlocal flask_app, flask_shutdown
        try:
            from app import create_app
            from werkzeug.serving import make_server
            
            flask_app = create_app(debug=os.getenv('DEBUG', 'True').lower() == 'true')
            
            # Create server that can be shut down
            # Use flask_host (0.0.0.0 in Docker, 127.0.0.1 locally)
            server = make_server(flask_host, flask_port, flask_app, threaded=True)
            flask_shutdown = server.shutdown
            
            flask_started.set()
            
            # Run server
            server.serve_forever()
        except Exception as e:
            print(f"\n[X] Failed to start Flask app: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Start Flask in background thread (daemon so it exits with main thread)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait and verify Flask is actually listening on the port
    if is_docker_environment():
        print("\n[5/5] Waiting for Flask to start (Docker mode - ngrok managed externally)...")
    else:
        print("\n[5/5] Waiting for Flask to start, then starting ngrok...")
    print("  Verifying Flask is listening on port...")
    
    for attempt in range(20):  # Wait up to 20 seconds
        try:
            import requests
            # Try both 127.0.0.1 and localhost
            for test_host in ['127.0.0.1', 'localhost']:
                try:
                    response = requests.get(f'http://{test_host}:{flask_port}', timeout=2)
                    if response.status_code in [200, 404, 500, 302]:  # Any response means Flask is up
                        flask_accessible = True
                        print(f"  [OK] Flask is accessible on {test_host}:{flask_port}")
                        break
                except requests.exceptions.ConnectionError:
                    continue
                except Exception:
                    continue
            
            if flask_accessible:
                break
                
        except Exception:
            pass
        
        if attempt < 19:
            time.sleep(1)
            if attempt % 3 == 0:  # Print every 3 seconds
                print(f"  Waiting for Flask... ({attempt + 1}/20)")
    
    if not flask_accessible:
        print(f"  [X] Flask not accessible on port {flask_port} after 20 seconds")
        print("  [X] Cannot start ngrok - Flask must be running first")
        print("  [!] Check Flask logs above for errors")
        return
    else:
        # Give Flask a moment to fully stabilize
        print("  [OK] Flask is ready!")
        time.sleep(2)
    
    # Only start ngrok if Flask is accessible
    if not flask_accessible:
        print("\n[!] Skipping ngrok start - Flask not accessible")
        print("    Fix Flask startup issues first")
        # Keep Flask running anyway
        try:
            while True:
                time.sleep(1)
                if not flask_thread.is_alive():
                    break
        except KeyboardInterrupt:
            sys.exit(0)
        return
    
    # Start ngrok - Flask is confirmed accessible (skip in Docker)
    if is_docker_environment():
        print("\n[DOCKER] Skipping ngrok startup - managed externally")
        # ngrok_url should already be set from environment variable
    elif os.getenv('SKIP_NGROK_AUTO_START', 'false').lower() == 'true':
        print("\n[LOCAL] Skipping ngrok auto-start (SKIP_NGROK_AUTO_START=true)")
        print("        Run ngrok separately: start-ngrok.bat or .\\scripts\\start_ngrok.ps1")
        # Still check if ngrok is already running
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    http_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                    if not http_tunnel:
                        http_tunnel = next((t for t in tunnels if 'http' in t.get('proto', '')), None)
                    if http_tunnel:
                        ngrok_url = http_tunnel.get('public_url')
                        print(f"  [OK] Found existing ngrok tunnel: {ngrok_url}")
        except:
            pass
    else:
        # Auto-start ngrok (default behavior)
        # First check if ngrok is already running
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    http_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                    if not http_tunnel:
                        http_tunnel = next((t for t in tunnels if 'http' in t.get('proto', '')), None)
                    if http_tunnel:
                        ngrok_url = http_tunnel.get('public_url')
                        print(f"\n[OK] Found existing ngrok tunnel: {ngrok_url}")
        except:
            pass
        
        # If ngrok not found, try to start it
        if not ngrok_url:
            print("\nStarting ngrok tunnel automatically...")
            ngrok_url = start_ngrok_tunnel(flask_port)
        
        # Keep checking for ngrok URL (but with shorter timeout for local dev)
        max_attempts = 10  # Reduced from 20 for faster failure
        for attempt in range(max_attempts):
            if not ngrok_url:
                time.sleep(1)  # Reduced from 2 seconds
                # Check ngrok but don't configure webhooks yet (will do after we confirm URL)
                try:
                    import requests
                    response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        tunnels = data.get('tunnels', [])
                        if tunnels:
                            http_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                            if not http_tunnel:
                                http_tunnel = next((t for t in tunnels if 'http' in t.get('proto', '')), None)
                            if http_tunnel:
                                ngrok_url = http_tunnel.get('public_url')
                except:
                    pass
            if ngrok_url:
                break
            if attempt < max_attempts - 1 and attempt % 2 == 0:  # Print every 2 attempts
                print(f"  Waiting for ngrok... ({attempt + 1}/{max_attempts})")
        
        if not ngrok_url:
            print("\n  [!] Ngrok not started automatically")
            print("      To start ngrok manually:")
            print("        - Run: start-ngrok.bat")
            print("        - Or: .\\scripts\\start_ngrok.ps1")
            print("        - Or: ngrok http 5000 --domain=vani-dev.ngrok.app")
            print("      Flask will continue running without ngrok (webhooks won't work)")
    
    # Configure webhooks now that we have ngrok URL (skip in Docker - webhooks configured externally)
    if ngrok_url and not is_docker_environment():
        print("\n  [*] Configuring webhooks with ngrok URL...")
        try:
            configure_webhooks_with_url(ngrok_url)
        except Exception as webhook_error:
            print(f"  [!] Webhook configuration failed: {webhook_error}")
            print("      You can configure webhooks manually with: python scripts/configure_webhooks.py")
        
        # Also configure Supabase OAuth URLs
        print("\n  [*] Configuring Supabase OAuth URLs...")
        try:
            sys.path.insert(0, str(basedir))
            from scripts.configure_supabase_oauth import configure_supabase_oauth
            configure_supabase_oauth(ngrok_url)
        except Exception as oauth_error:
            print(f"  [!] Supabase OAuth configuration failed: {oauth_error}")
            print("      Configure manually: python scripts/configure_supabase_oauth.py")
            print(f"      Or visit: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/url-configuration")
    
    expected_url = get_expected_ngrok_url()
    
    print("\n" + "="*70)
    print("  SERVER STATUS")
    print("="*70)
    if is_docker_environment():
        print("\n[DOCKER MODE] Running in container")
    print(f"\nLocal URL:        http://{flask_host}:{flask_port}")
    print(f"Command Center:   http://{flask_host}:{flask_port}/command-center")
    
    if ngrok_url:
        print(f"\n✅ PUBLIC URL (Ngrok): {ngrok_url}")
        print(f"   Command Center:     {ngrok_url}/command-center")
        if not is_docker_environment():
            print("\n📋 Webhook Endpoints:")
            print(f"   Resend:    {ngrok_url}/api/webhooks/resend")
            print(f"   Twilio:    {ngrok_url}/api/webhooks/twilio")
            print(f"   Cal.com:   {ngrok_url}/api/webhooks/cal-com")
            print("\n💡 Tip: Webhooks are auto-configured when ngrok is detected.")
            print("   To reconfigure manually: python scripts/configure_webhooks.py")
        else:
            print("\n[DOCKER] Webhooks configured via environment variables")
    elif expected_url and not is_docker_environment():
        print(f"\n⚠️  Expected URL: {expected_url}")
        print("   Ngrok may still be starting...")
        print("   Check ngrok dashboard: http://localhost:4040")
    elif not is_docker_environment():
        print("\n⚠️  No ngrok URL configured")
        print("   Set WEBHOOK_BASE_URL in .env.local")
    
    print("\n" + "="*70)
    print("  ✅ SERVER RUNNING")
    print("="*70)
    print("\nPress Ctrl+C to stop the server\n")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
            # Check if Flask thread is still alive
            if not flask_thread.is_alive():
                print("\n[!] Flask thread stopped unexpectedly")
                break
    except KeyboardInterrupt:
        print("\n\n[STOP] Server stopped by user")
        
        # Shutdown Flask server
        if flask_shutdown:
            try:
                print("  Stopping Flask server...")
                flask_shutdown()
                time.sleep(1)
            except Exception as e:
                print(f"  [!] Error stopping Flask: {e}")
        
        # Stop ngrok
        print("  Stopping ngrok...")
        try:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/IM', 'ngrok.exe'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             timeout=3)
                print("  [OK] Ngrok stopped")
            else:
                subprocess.run(['pkill', '-f', 'ngrok'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             timeout=3)
                print("  [OK] Ngrok stopped")
        except Exception as e:
            print(f"  [!] Error stopping ngrok: {e}")
        
        # Kill Flask process on port if still running
        try:
            if sys.platform == 'win32':
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if f':{flask_port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) > 0:
                            pid = parts[-1]
                            subprocess.run(['taskkill', '/F', '/PID', pid], 
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL,
                                         timeout=2)
            else:
                result = subprocess.run(
                    ['lsof', '-ti', f':{flask_port}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        subprocess.run(['kill', '-9', pid], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL,
                                     timeout=2)
        except:
            pass
        
        print("\n[OK] Cleanup complete. Exiting...\n")
        sys.exit(0)


def main():
    """Main startup function"""
    print_header()
    
    # Step 0: Kill existing processes
    kill_existing_processes()
    
    # Step 1: Check environment
    if not check_environment():
        print("\n[X] Environment check failed. Please fix issues above.")
        sys.exit(1)
    
    # Step 2: Check database
    db_ok = check_database()
    if not db_ok:
        print("\n[!] Database check failed, but continuing...")
        print("    You may need to run: python scripts/create_database_tables_direct.py\n")
    
    # Step 3: Check ngrok (will start after Flask)
    if is_docker_environment():
        print("  [DOCKER] Running in container - ngrok managed externally")
        webhook_url = os.getenv('WEBHOOK_BASE_URL')
        if not webhook_url:
            # Try to get from config
            try:
                from scripts.load_ngrok_config import load_ngrok_config
                config = load_ngrok_config()
                webhook_url = config.get('webhook_base_url')
            except:
                pass
        if not webhook_url:
            webhook_url = 'https://vani.ngrok.app'  # Fallback
        print(f"  [DOCKER] Webhook URL will be: {webhook_url}")
        ngrok_url = webhook_url
    else:
        ngrok_url = check_ngrok()
        if not ngrok_url:
            expected = get_expected_ngrok_url()
            if expected:
                print(f"    Expected URL: {expected}")
            print("    [!] Will start ngrok after Flask starts\n")
    
    # Step 4: Start Flask and ngrok
    start_flask_app(ngrok_url=ngrok_url)


if __name__ == '__main__':
    main()

