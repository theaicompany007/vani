#!/usr/bin/env python3
"""
VANI Outreach Command Center - Startup Script
Checks everything and starts the Flask server with ngrok URL display

Features:
- Environment validation
- Database connection check
- Ngrok tunnel management
- Webhook auto-configuration
- Admin tools available for super users (batch import, system monitoring)
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
    
    # Optional Twilio WhatsApp (sandbox or paid)
    optional_twilio = {
        'TWILIO_SANDBOX_WHATSAPP_NUMBER': 'Twilio WhatsApp Sandbox number (for free testing)',
        'TWILIO_WHATSAPP_NUMBER': 'Twilio WhatsApp number (for paid account)',
        'TWILIO_PHONE_NUMBER': 'Twilio SMS phone number',
    }
    
    # Optional but recommended for AI features
    optional_vars = {
        'RAG_API_KEY': 'RAG service API key (for AI Target Finder)',
        'RAG_SERVICE_URL': 'RAG service URL (default: https://rag.kcube-consulting.com)',
        'GEMINI_API_KEY': 'Google Gemini API key (for AI Target Finder - Notebook LM)',
        'SUPABASE_ACCESS_TOKEN': 'Supabase Personal Access Token (for OAuth URL auto-config)',
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
            # Show full value instead of masking
            print(f"  [OK] {var:25} = {value}")
    
    # Check optional variables
    missing_optional = []
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if not value:
            missing_optional.append(f"  [!] {var:25} - {desc} (optional)")
        else:
            # Show full value instead of masking
            print(f"  [OK] {var:25} = {value}")
    
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
            print(f"  [OK] {var:25} = {value}")
    
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
            print(f"  [OK] {var:25} = {value}")
    
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
    """Check and report AI Target Finder feature availability"""
    print("\n[AI] AI Target Finder Feature Status:")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    rag_key = os.getenv('RAG_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    # OpenAI is required
    if openai_key:
        print("  [OK] OpenAI API configured - Basic AI features available")
    else:
        print("  [X] OpenAI API NOT configured - AI Target Finder will NOT work")
        print("      Set OPENAI_API_KEY in .env.local")
        return
    
    # RAG and Gemini are optional but enhance functionality
    features_available = []
    features_missing = []
    
    if rag_key:
        features_available.append("RAG-enhanced contact analysis")
    else:
        features_missing.append("RAG service (enhanced contact analysis)")
    
    if gemini_key:
        features_available.append("Gemini/Notebook LM integration")
    else:
        features_missing.append("Gemini API (Notebook LM integration)")
    
    if features_available:
        print("  [OK] Enhanced features available:")
        for feature in features_available:
            print(f"       - {feature}")
    
    if features_missing:
        print("  [!] Optional enhancements not configured:")
        for feature in features_missing:
            print(f"       - {feature}")
        print("      AI Target Finder will work with reduced functionality")
    
    if openai_key and rag_key and gemini_key:
        print("  [✓] Full AI Target Finder capabilities available!")
    elif openai_key:
        print("  [~] AI Target Finder available with basic functionality")


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


def configure_webhooks_with_url(webhook_url: str):
    """Configure webhooks using the provided URL"""
    try:
        # Temporarily set WEBHOOK_BASE_URL if not already set
        original_url = os.getenv('WEBHOOK_BASE_URL')
        if not original_url:
            os.environ['WEBHOOK_BASE_URL'] = webhook_url
        
        # Import and run webhook configuration
        sys.path.insert(0, str(basedir))
        from scripts.configure_webhooks import WebhookConfigurator
        
        print(f"  [*] Configuring webhooks for: {webhook_url}")
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
            return None
        
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
        
        # Check if ngrok is already running
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=1)
            if response.status_code == 200:
                data = response.json()
                if data.get('tunnels'):
                    return data['tunnels'][0].get('public_url')
        except:
            pass
        
        # Try to start ngrok using tunnel config
        config_path = os.path.join(os.getenv('LOCALAPPDATA', ''), 'ngrok', 'ngrok.yml')
        if not os.path.exists(config_path):
            config_path = os.path.join(os.getenv('USERPROFILE', ''), '.ngrok2', 'ngrok.yml')
        
        # Check if 'vani' tunnel is configured
        use_tunnel = False
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                content = f.read()
                if 'vani:' in content or 'domain: vani.ngrok.app' in content:
                    use_tunnel = True
        
        # Start ngrok
        if use_tunnel:
            # Use tunnel config
            subprocess.Popen(
                [ngrok_path, 'start', 'vani'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        else:
            # Use domain flag or random URL
            expected_domain = get_expected_ngrok_url()
            if expected_domain and 'ngrok.app' in expected_domain:
                domain = expected_domain.replace('https://', '').replace('http://', '')
                subprocess.Popen(
                    [ngrok_path, 'http', str(port), '--domain', domain],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
            else:
                subprocess.Popen(
                    [ngrok_path, 'http', str(port)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
        
        # Wait for ngrok to start
        time.sleep(5)
        
        # Get the URL
        try:
            import requests
            for _ in range(10):  # Try up to 10 times
                try:
                    response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        tunnels = data.get('tunnels', [])
                        if tunnels:
                            return tunnels[0].get('public_url')
                except:
                    pass
                time.sleep(1)
        except:
            pass
        
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
    
    flask_host = os.getenv('FLASK_HOST', '127.0.0.1')
    flask_port = int(os.getenv('FLASK_PORT', '5000'))
    
    # For ngrok to connect, Flask must bind to 127.0.0.1 (not 0.0.0.0)
    # But ensure it's accessible from localhost
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
            server = make_server('127.0.0.1', flask_port, flask_app, threaded=True)
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
    
    # Start ngrok - Flask is confirmed accessible
    print("\nStarting ngrok tunnel...")
    if not ngrok_url:
        ngrok_url = start_ngrok_tunnel(flask_port)
    
    # Keep checking for ngrok URL
    max_attempts = 20
    for attempt in range(max_attempts):
        if not ngrok_url:
            time.sleep(2)
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
        if attempt < max_attempts - 1:
            print(f"  Waiting for ngrok... ({attempt + 1}/{max_attempts})")
    
    # Configure webhooks now that we have ngrok URL
    if ngrok_url:
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
    print(f"\nLocal URL:        http://{flask_host}:{flask_port}")
    print(f"Command Center:   http://{flask_host}:{flask_port}/command-center")
    
    if ngrok_url:
        print(f"\n✅ PUBLIC URL (Ngrok): {ngrok_url}")
        print(f"   Command Center:     {ngrok_url}/command-center")
        print("\n📋 Webhook Endpoints:")
        print(f"   Resend:    {ngrok_url}/api/webhooks/resend")
        print(f"   Twilio:    {ngrok_url}/api/webhooks/twilio")
        print(f"   Cal.com:   {ngrok_url}/api/webhooks/cal-com")
        print("\n💡 Tip: Webhooks are auto-configured when ngrok is detected.")
        print("   To reconfigure manually: python scripts/configure_webhooks.py")
    elif expected_url:
        print(f"\n⚠️  Expected URL: {expected_url}")
        print("   Ngrok may still be starting...")
        print("   Check ngrok dashboard: http://localhost:4040")
    else:
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

