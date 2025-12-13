"""Configure webhooks for Resend, Twilio, and Cal.com"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

# Try to load from ngrok.config.json as fallback
def load_ngrok_config_fallback():
    """Load ngrok config from JSON file if env vars not set"""
    ngrok_config_path = basedir / 'ngrok.config.json'
    if ngrok_config_path.exists():
        try:
            import json
            with open(ngrok_config_path, 'r') as f:
                config = json.load(f)
                # Set environment variables if not already set
                if 'webhooks' in config and 'base_url' in config['webhooks']:
                    if not os.getenv('WEBHOOK_BASE_URL'):
                        os.environ['WEBHOOK_BASE_URL'] = config['webhooks']['base_url']
        except Exception:
            pass  # Silently fail if JSON can't be loaded

load_ngrok_config_fallback()


class WebhookConfigurator:
    """Configure webhooks for all services with environment-aware safety checks"""
    
    def __init__(self, environment: str = 'dev'):
        """
        Initialize webhook configurator
        
        Args:
            environment: 'dev' or 'prod' - determines if updates are safe
        """
        self.environment = environment.lower()
        self._init_webhook_urls()
    
    def _init_webhook_urls(self):
        """Initialize webhook URLs from environment"""
        """Get ngrok URL from ngrok API"""
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                
                if tunnels:
                    # Find HTTPS tunnel first, then HTTP
                    http_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                    if not http_tunnel:
                        http_tunnel = next((t for t in tunnels if 'http' in t.get('proto', '')), None)
                    
                    if http_tunnel:
                        return http_tunnel.get('public_url')
        except Exception:
            pass  # Silently fail if ngrok is not running
        
        return None
    
    def _init_webhook_urls(self):
        """Initialize webhook URLs from environment"""
        # All values loaded from .env.local (loaded at module level)
        self.webhook_base_url = os.getenv('WEBHOOK_BASE_URL')
        
        # If not set, try to get from ngrok
        if not self.webhook_base_url:
            print("⚠️  WEBHOOK_BASE_URL not found, attempting to detect from ngrok...")
            ngrok_url = self._get_ngrok_url()
            if ngrok_url:
                self.webhook_base_url = ngrok_url
                print(f"✅ Using ngrok URL: {self.webhook_base_url}")
            else:
                raise ValueError(
                    "WEBHOOK_BASE_URL not found in .env.local and ngrok is not running.\n"
                    "Please either:\n"
                    "  1. Set WEBHOOK_BASE_URL in .env.local, or\n"
                    "  2. Start ngrok and run this script again"
                )
        
        self.webhook_secret = os.getenv('WEBHOOK_SECRET', '')
        
        # Resend
        self.resend_api_key = os.getenv('RESEND_API_KEY')
        self.resend_webhook_url = f"{self.webhook_base_url}/api/webhooks/resend"
        
        # Twilio - trim whitespace from credentials
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '').strip() if os.getenv('TWILIO_ACCOUNT_SID') else ''
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '').strip() if os.getenv('TWILIO_AUTH_TOKEN') else ''
        # Support WhatsApp Sandbox (priority: sandbox > regular)
        whatsapp_num = os.getenv('TWILIO_SANDBOX_WHATSAPP_NUMBER') or os.getenv('TWILIO_WHATSAPP_NUMBER', '')
        self.twilio_whatsapp_number = whatsapp_num.replace('whatsapp:', '').replace('+', '').strip()
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '').replace('+', '').strip()
        self.twilio_webhook_url = f"{self.webhook_base_url}/api/webhooks/twilio"
        
        # Log which number is being used
        if os.getenv('TWILIO_SANDBOX_WHATSAPP_NUMBER'):
            print(f"Using WhatsApp Sandbox: {whatsapp_num}")
        
        # Cal.com
        self.cal_com_api_key = os.getenv('CAL_COM_API_KEY')
        self.cal_com_webhook_secret = os.getenv('CAL_COM_WEBHOOK_SECRET') or os.getenv('CAL_COM_WEBHOOK_SECRET_PROD', '')
        self.cal_com_webhook_url = f"{self.webhook_base_url}/api/webhooks/cal-com"
        
        # Cal.com API v2 uses different authentication
        # Check if it's a v1 or v2 key
        if self.cal_com_api_key and not self.cal_com_api_key.startswith('cal_'):
            print("⚠️  Warning: CAL_COM_API_KEY format may be incorrect (should start with 'cal_')")
    
    def _is_safe_to_update(self, current_url: str, target_url: str) -> bool:
        """
        Check if it's safe to update webhook URL based on environment
        
        Returns True if:
        - Current URL is empty/None (safe to set)
        - Current URL matches target URL (already correct)
        - Current URL matches current environment (dev updating dev, prod updating prod)
        
        Returns False if:
        - Current URL is for different environment (prevents overwrite)
        """
        if not current_url or current_url.strip() == '':
            return True  # Empty URL is safe to update
        
        if current_url == target_url:
            return True  # Already correct, safe to update
        
        # Check environment match
        current_lower = current_url.lower()
        target_lower = target_url.lower()
        
        is_current_dev = 'vani-dev.ngrok' in current_lower
        is_current_prod = 'vani.ngrok' in current_lower and 'vani-dev' not in current_lower
        is_target_dev = 'vani-dev.ngrok' in target_lower
        is_target_prod = 'vani.ngrok' in target_lower and 'vani-dev' not in target_lower
        
        # Safe if both are same environment
        if (is_current_dev and is_target_dev) or (is_current_prod and is_target_prod):
            return True
        
        # Unsafe if trying to overwrite different environment
        if (is_current_dev and is_target_prod) or (is_current_prod and is_target_dev):
            return False
        
        # If we can't determine environment, be conservative and allow update
        # (might be a different domain or format)
        return True
    
    def configure_resend_webhook(self) -> Dict[str, Any]:
        """Configure Resend webhook"""
        if not self.resend_api_key:
            return {'success': False, 'error': 'RESEND_API_KEY not found'}
        
        print("\n" + "="*70)
        print("  CONFIGURING RESEND WEBHOOK")
        print("="*70)
        print(f"Webhook URL: {self.resend_webhook_url}")
        print(f"API Key: {self.resend_api_key[:10]}...{self.resend_api_key[-4:]}")
        
        # Resend API endpoint for webhooks
        api_url = "https://api.resend.com/webhooks"
        
        headers = {
            'Authorization': f'Bearer {self.resend_api_key}',
            'Content-Type': 'application/json'
        }
        
        # First verify API key by checking domains or emails
        try:
            # Try domains endpoint first
            verify_url = "https://api.resend.com/domains"
            verify_response = requests.get(verify_url, headers=headers)
            if verify_response.status_code == 200:
                print("✅ API key validated successfully")
            elif verify_response.status_code == 401:
                error_data = verify_response.json() if verify_response.text else {}
                error_msg = error_data.get('message', 'Unauthorized')
                print(f"❌ API key validation failed: {error_msg}")
                print("   Please check your RESEND_API_KEY in .env.local")
                print(f"   Current key format: {self.resend_api_key[:10]}...{self.resend_api_key[-4:]}")
                return {'success': False, 'error': f'Invalid API key: {error_msg}'}
            else:
                # Try emails endpoint as alternative
                emails_url = "https://api.resend.com/emails"
                emails_response = requests.get(emails_url, headers=headers, params={'limit': 1})
                if emails_response.status_code == 200:
                    print("✅ API key validated successfully (via emails endpoint)")
                else:
                    print(f"⚠️  Could not verify API key (status: {verify_response.status_code})")
                    print("   Continuing anyway - webhook creation may still work...")
        except Exception as e:
            print(f"⚠️  Could not verify API key: {e}")
            print("   Continuing anyway - webhook creation may still work...")
        
        # Events to subscribe to
        events = [
            'email.sent',
            'email.delivered',
            'email.opened',
            'email.clicked',
            'email.bounced',
            'email.complained'
        ]
        
        # First, list existing webhooks
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                existing_webhooks = response.json().get('data', [])
                print(f"\nFound {len(existing_webhooks)} existing webhook(s)")
                
                # Check if webhook already exists and if it's safe to update
                for webhook in existing_webhooks:
                    current_webhook_url = webhook.get('url', '')
                    webhook_id = webhook.get('id')
                    
                    # Check if this webhook matches our target URL or needs updating
                    if current_webhook_url == self.resend_webhook_url:
                        print(f"✅ Webhook already exists with correct URL (ID: {webhook_id})")
                        
                        # Update webhook to ensure events are correct
                        update_url = f"{api_url}/{webhook_id}"
                        update_data = {
                            'events': events
                        }
                        update_response = requests.patch(update_url, headers=headers, json=update_data)
                        
                        if update_response.status_code == 200:
                            print(f"✅ Webhook events updated successfully")
                            return {'success': True, 'webhook_id': webhook_id, 'action': 'updated'}
                        else:
                            print(f"⚠️  Failed to update webhook: {update_response.text}")
                            return {'success': False, 'error': f"Update failed: {update_response.text}"}
                    
                    # Check if we should update this webhook (environment-aware)
                    elif self._is_safe_to_update(current_webhook_url, self.resend_webhook_url):
                        print(f"🔄 Found existing webhook with different URL (ID: {webhook_id})")
                        print(f"   Current: {current_webhook_url}")
                        print(f"   Target:  {self.resend_webhook_url}")
                        
                        # Update webhook URL and events
                        update_url = f"{api_url}/{webhook_id}"
                        update_data = {
                            'url': self.resend_webhook_url,
                            'events': events
                        }
                        update_response = requests.patch(update_url, headers=headers, json=update_data)
                        
                        if update_response.status_code == 200:
                            print(f"✅ Webhook URL updated successfully")
                            return {'success': True, 'webhook_id': webhook_id, 'action': 'updated'}
                        else:
                            print(f"⚠️  Failed to update webhook: {update_response.text}")
                            return {'success': False, 'error': f"Update failed: {update_response.text}"}
                    
                    else:
                        # Environment mismatch - skip update
                        print(f"⚠️  Skipping Resend webhook update (environment mismatch)")
                        print(f"   Current URL ({current_webhook_url}) is for different environment")
                        print(f"   Target URL ({self.resend_webhook_url}) would overwrite production webhook")
                        print(f"   To update manually, set SKIP_WEBHOOK_UPDATE=false and ensure correct environment")
                        return {'success': False, 'error': 'Environment mismatch - would overwrite different environment webhook', 'skipped': True}
            else:
                print(f"⚠️  Could not list webhooks: {response.text}")
        except Exception as e:
            print(f"⚠️  Error checking existing webhooks: {e}")
        
        # Create new webhook
        print("\nCreating new webhook...")
        webhook_data = {
            'url': self.resend_webhook_url,
            'events': events
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=webhook_data)
            
            if response.status_code == 201:
                webhook_info = response.json()
                webhook_id = webhook_info.get('id')
                print(f"✅ Webhook created successfully!")
                print(f"   Webhook ID: {webhook_id}")
                print(f"   Events: {', '.join(events)}")
                return {'success': True, 'webhook_id': webhook_id, 'action': 'created'}
            else:
                error_msg = response.text
                print(f"❌ Failed to create webhook: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            print(f"❌ Error creating webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def configure_twilio_webhook(self) -> Dict[str, Any]:
        """Configure Twilio webhook for WhatsApp number"""
        if not self.twilio_account_sid or not self.twilio_auth_token:
            return {'success': False, 'error': 'TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not found'}
        
        print("\n" + "="*70)
        print("  CONFIGURING TWILIO WEBHOOK")
        print("="*70)
        print(f"Webhook URL: {self.twilio_webhook_url}")
        print(f"WhatsApp Number: {self.twilio_whatsapp_number}")
        print(f"Account SID: {self.twilio_account_sid[:10]}...{self.twilio_account_sid[-4:] if len(self.twilio_account_sid) > 14 else ''}")
        print(f"Auth Token: {'*' * (len(self.twilio_auth_token) - 4) + self.twilio_auth_token[-4:] if len(self.twilio_auth_token) > 4 else '***'}")
        
        # Validate credentials format
        validation_errors = []
        if not self.twilio_account_sid:
            validation_errors.append("TWILIO_ACCOUNT_SID is empty")
        elif not self.twilio_account_sid.startswith('AC'):
            validation_errors.append(f"TWILIO_ACCOUNT_SID should start with 'AC' (got: {self.twilio_account_sid[:5]}...)")
        elif len(self.twilio_account_sid) != 34:
            validation_errors.append(f"TWILIO_ACCOUNT_SID should be 34 characters (got: {len(self.twilio_account_sid)})")
        
        if not self.twilio_auth_token:
            validation_errors.append("TWILIO_AUTH_TOKEN is empty")
        elif len(self.twilio_auth_token) < 30:
            validation_errors.append(f"TWILIO_AUTH_TOKEN seems too short (should be ~32 characters, got: {len(self.twilio_auth_token)})")
        
        if validation_errors:
            print("\n⚠️  Credential validation warnings:")
            for error in validation_errors:
                print(f"   - {error}")
            print("\n💡 Check your .env.local file for:")
            print(f"   TWILIO_ACCOUNT_SID={self.twilio_account_sid[:20] if self.twilio_account_sid else '(empty)'}...")
            print(f"   TWILIO_AUTH_TOKEN={'*' * 20 if self.twilio_auth_token else '(empty)'}...")
        
        # Twilio API endpoint - use requests auth instead of URL embedding
        numbers_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/IncomingPhoneNumbers.json"
        
        try:
            # First, test authentication with a simple account info request
            print(f"\n🔍 Testing Twilio authentication...")
            test_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}.json"
            test_response = requests.get(
                test_url,
                auth=(self.twilio_account_sid, self.twilio_auth_token),
                timeout=10
            )
            
            if test_response.status_code == 401:
                error_data = test_response.json() if test_response.text else {}
                error_code = error_data.get('code', '')
                error_msg = error_data.get('message', 'Authentication failed')
                print(f"❌ Twilio authentication failed (401)")
                print(f"   Error Code: {error_code}")
                print(f"   Message: {error_msg}")
                print(f"\n💡 Troubleshooting:")
                print(f"   1. Verify TWILIO_ACCOUNT_SID is correct:")
                print(f"      - Should start with 'AC'")
                print(f"      - Should be exactly 34 characters")
                print(f"      - Current: {self.twilio_account_sid[:20]}... (length: {len(self.twilio_account_sid)})")
                print(f"   2. Verify TWILIO_AUTH_TOKEN is correct:")
                print(f"      - Should be ~32 characters")
                print(f"      - Check for extra spaces or newlines in .env.local")
                print(f"      - Current length: {len(self.twilio_auth_token)} characters")
                print(f"   3. Check credentials in Twilio Console:")
                print(f"      https://console.twilio.com/us1/account/settings/credentials")
                print(f"   4. Regenerate Auth Token if needed:")
                print(f"      - Go to Twilio Console → Account → Auth Tokens")
                print(f"      - Create new token and update .env.local")
                print(f"   5. Ensure credentials are from the correct Twilio account")
                print(f"   6. Check if account is active (not suspended)")
                return {'success': False, 'error': f'Authentication failed: {error_msg}'}
            
            if test_response.status_code == 200:
                account_info = test_response.json()
                print(f"✅ Authentication successful!")
                print(f"   Account Name: {account_info.get('friendly_name', 'N/A')}")
                print(f"   Account Status: {account_info.get('status', 'N/A')}")
            
            # Now fetch phone numbers
            print(f"\n📞 Fetching phone numbers...")
            response = requests.get(
                numbers_url,
                auth=(self.twilio_account_sid, self.twilio_auth_token),
                timeout=10
            )
            
            if response.status_code == 401:
                # Shouldn't happen if test passed, but handle it
                error_data = response.json() if response.text else {}
                error_code = error_data.get('code', '')
                error_msg = error_data.get('message', 'Authentication failed')
                print(f"❌ Failed to fetch phone numbers (401)")
                print(f"   Error Code: {error_code}")
                print(f"   Message: {error_msg}")
                return {'success': False, 'error': f'Authentication failed: {error_msg}'}
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch phone numbers (status: {response.status_code})")
                print(f"   Response: {response.text[:200]}")
                return {'success': False, 'error': f'Could not fetch phone numbers (status: {response.status_code})'}
            
            numbers = response.json().get('incoming_phone_numbers', [])
            
            # Find the WhatsApp number (try multiple formats)
            target_number = None
            # Try different number formats (including sandbox)
            search_numbers = [
                self.twilio_whatsapp_number,  # e.g., "14155238886"
                self.twilio_phone_number,     # e.g., "9873154007"
                f"+{self.twilio_whatsapp_number}",  # e.g., "+14155238886"
                f"+{self.twilio_phone_number}",     # e.g., "+9873154007"
                # Also try with whatsapp: prefix removed
                self.twilio_whatsapp_number.replace('whatsapp:', ''),
            ]
            
            print(f"Searching for numbers: {', '.join([n for n in search_numbers if n])}")
            
            for number in numbers:
                phone_number = number.get('phone_number', '')
                phone_number_no_plus = phone_number.replace('+', '')
                
                # Check if it matches any of our search numbers
                if phone_number in search_numbers or phone_number_no_plus in search_numbers:
                    target_number = number
                    print(f"✅ Found matching number: {phone_number} (SID: {number.get('sid')})")
                    break
            
            if not target_number:
                print(f"⚠️  Number {self.twilio_whatsapp_number} not found in your account")
                print("   Available numbers:")
                for num in numbers[:10]:  # Show first 10
                    print(f"     - {num.get('phone_number')} (SID: {num.get('sid')})")
                if len(numbers) > 10:
                    print(f"     ... and {len(numbers) - 10} more")
                print("\n💡 Tip: Update TWILIO_WHATSAPP_NUMBER or TWILIO_PHONE_NUMBER in .env.local")
                print("   to match one of the numbers above, or configure manually in Twilio Console")
                return {'success': False, 'error': 'Phone number not found'}
            
            number_sid = target_number.get('sid')
            print(f"✅ Found number SID: {number_sid}")
            
            # Check current status callback URL before updating
            current_status_callback = target_number.get('status_callback', '')
            
            # Check if it's safe to update
            if not self._is_safe_to_update(current_status_callback, self.twilio_webhook_url):
                print(f"⚠️  Skipping Twilio webhook update (environment mismatch)")
                print(f"   Current URL ({current_status_callback}) is for different environment")
                print(f"   Target URL ({self.twilio_webhook_url}) would overwrite production webhook")
                return {'success': False, 'error': 'Environment mismatch - would overwrite different environment webhook', 'skipped': True}
            
            # Update the number's status callback
            update_url = f"https://{self.twilio_account_sid}:{self.twilio_auth_token}@api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/IncomingPhoneNumbers/{number_sid}.json"
            
            update_data = {
                'StatusCallback': self.twilio_webhook_url,
                'StatusCallbackMethod': 'POST'
            }
            
            if current_status_callback == self.twilio_webhook_url:
                print(f"✅ Status callback URL already correct - no update needed")
                return {'success': True, 'number_sid': number_sid, 'action': 'no_change'}
            
            print(f"🔄 Updating status callback from: {current_status_callback}")
            print(f"   To: {self.twilio_webhook_url}")
            
            update_response = requests.post(update_url, data=update_data)
            
            if update_response.status_code == 200:
                print(f"✅ Status callback URL updated successfully!")
                return {'success': True, 'number_sid': number_sid, 'action': 'updated'}
            else:
                print(f"❌ Failed to update status callback: {update_response.text}")
                return {'success': False, 'error': update_response.text}
                
        except Exception as e:
            print(f"❌ Error configuring Twilio webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def configure_cal_com_webhook(self) -> Dict[str, Any]:
        """Configure Cal.com webhook"""
        if not self.cal_com_api_key:
            return {'success': False, 'error': 'CAL_COM_API_KEY not found'}
        
        print("\n" + "="*70)
        print("  CONFIGURING CAL.COM WEBHOOK")
        print("="*70)
        print(f"Webhook URL: {self.cal_com_webhook_url}")
        print(f"API Key: {self.cal_com_api_key[:15]}...{self.cal_com_api_key[-4:] if len(self.cal_com_api_key) > 19 else ''}")
        
        # Cal.com API endpoints
        # Cal.com v1 API uses query parameter authentication: ?apiKey=xxx
        # Cal.com v2 API uses header authentication: x-cal-secret-key
        api_url_v1 = f"https://api.cal.com/v1/webhooks?apiKey={self.cal_com_api_key}"
        api_url_v2 = "https://api.cal.com/v2/webhooks"
        
        # Determine API version based on key format
        use_v1 = self.cal_com_api_key.startswith('cal_live_') or self.cal_com_api_key.startswith('cal_test_')
        
        # Prepare headers for both versions
        # v1 uses query parameter, so headers are simple
        headers_v1 = {
            'Content-Type': 'application/json'
        }
        
        # v2 uses header authentication
        headers_v2 = {
            'x-cal-secret-key': self.cal_com_api_key,
            'Content-Type': 'application/json'
        }
        
        # Events to subscribe to
        events = [
            'BOOKING_CREATED',
            'BOOKING_CANCELLED',
            'BOOKING_RESCHEDULED'
        ]
        
        # List existing webhooks - try multiple authentication methods
        existing_webhooks = []
        api_used = None
        api_url = None
        headers = None
        
        try:
            if use_v1:
                print(f"✅ Using Cal.com v1 API (query parameter authentication)")
                # v1 API uses query parameter: ?apiKey=xxx
                response = requests.get(api_url_v1, headers=headers_v1, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    existing_webhooks = data.get('webhooks', data.get('data', []))
                    print(f"✅ Successfully connected via v1 API")
                    print(f"   Found {len(existing_webhooks)} existing webhook(s)")
                    api_used = 'v1'
                    api_url = api_url_v1
                    headers = headers_v1
                elif response.status_code in [401, 403]:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get('message', 'Authentication failed')
                    print(f"❌ v1 API authentication failed: {error_msg}")
                    print(f"🔄 Trying v2 API format as fallback...")
                    
                    # Try v2 as fallback
                    response = requests.get(api_url_v2, headers=headers_v2, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        existing_webhooks = data.get('webhooks', data.get('data', []))
                        print(f"✅ Successfully connected via v2 API")
                        print(f"   Found {len(existing_webhooks)} existing webhook(s)")
                        api_used = 'v2'
                        api_url = api_url_v2
                        headers = headers_v2
                    else:
                        error_data = response.json() if response.text else {}
                        error_msg = error_data.get('message', 'Authentication failed')
                        print(f"\n❌ All authentication methods failed")
                        print(f"   Error: {error_msg}")
                        print(f"\n💡 Troubleshooting:")
                        print(f"   1. Verify CAL_COM_API_KEY is correct: {self.cal_com_api_key[:20]}...")
                        print(f"   2. Check API key in Cal.com: https://app.cal.com/settings/developer/api-keys")
                        print(f"   3. Ensure API key has webhook management permissions")
                        print(f"   4. Try regenerating the API key in Cal.com")
                        return {'success': False, 'error': f'Authentication failed: {error_msg}'}
                else:
                    print(f"⚠️  Unexpected response (status: {response.status_code}): {response.text[:200]}")
                    return {'success': False, 'error': f'Unexpected response: {response.status_code}'}
            else:
                print(f"⚠️  API key format not recognized - trying v2 API format")
                print(f"   Expected format: cal_live_xxx or cal_test_xxx for v1")
                api_url = api_url_v2
                headers = headers_v2
                api_used = 'v2'
                
                response = requests.get(api_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    existing_webhooks = data.get('webhooks', data.get('data', []))
                    print(f"✅ Successfully connected via v2 API")
                    print(f"   Found {len(existing_webhooks)} existing webhook(s)")
                elif response.status_code in [401, 403]:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get('message', 'Authentication failed')
                    print(f"❌ v2 API authentication failed: {error_msg}")
                    print(f"\n💡 Troubleshooting:")
                    print(f"   1. Verify CAL_COM_API_KEY is correct")
                    print(f"   2. Check API key format in Cal.com settings")
                    print(f"   3. Ensure API key has webhook management permissions")
                    return {'success': False, 'error': f'Authentication failed: {error_msg}'}
                else:
                    print(f"⚠️  Unexpected response (status: {response.status_code}): {response.text[:200]}")
                    return {'success': False, 'error': f'Unexpected response: {response.status_code}'}
            
            # Check if webhook already exists and if it's safe to update
            for webhook in existing_webhooks:
                current_webhook_url = webhook.get('subscriberUrl', '')
                webhook_id = webhook.get('id')
                
                if current_webhook_url == self.cal_com_webhook_url:
                    print(f"✅ Webhook already exists with correct URL (ID: {webhook_id})")
                    
                    # Update webhook events and secret
                    # For v1, need to include apiKey in URL
                    if api_used == 'v1':
                        update_url = f"https://api.cal.com/v1/webhooks/{webhook_id}?apiKey={self.cal_com_api_key}"
                    else:
                        update_url = f"{api_url}/{webhook_id}"
                    update_data = {
                        'eventTriggers': events,
                        'secret': self.cal_com_webhook_secret
                    }
                    update_response = requests.patch(update_url, headers=headers, json=update_data, timeout=10)
                    
                    if update_response.status_code == 200:
                        print(f"✅ Webhook updated successfully")
                        return {'success': True, 'webhook_id': webhook_id, 'action': 'updated'}
                    else:
                        print(f"⚠️  Failed to update webhook: {update_response.text}")
                        return {'success': False, 'error': f"Update failed: {update_response.text}"}
                
                # Check if we should update this webhook (environment-aware)
                elif self._is_safe_to_update(current_webhook_url, self.cal_com_webhook_url):
                    print(f"🔄 Found existing webhook with different URL (ID: {webhook_id})")
                    print(f"   Current: {current_webhook_url}")
                    print(f"   Target:  {self.cal_com_webhook_url}")
                    
                    # Update webhook URL, events, and secret
                    # For v1, need to include apiKey in URL
                    if api_used == 'v1':
                        update_url = f"https://api.cal.com/v1/webhooks/{webhook_id}?apiKey={self.cal_com_api_key}"
                    else:
                        update_url = f"{api_url}/{webhook_id}"
                    update_data = {
                        'subscriberUrl': self.cal_com_webhook_url,
                        'eventTriggers': events,
                        'secret': self.cal_com_webhook_secret
                    }
                    update_response = requests.patch(update_url, headers=headers, json=update_data, timeout=10)
                    
                    if update_response.status_code == 200:
                        print(f"✅ Webhook URL updated successfully")
                        return {'success': True, 'webhook_id': webhook_id, 'action': 'updated'}
                    else:
                        print(f"⚠️  Failed to update webhook: {update_response.text}")
                        return {'success': False, 'error': f"Update failed: {update_response.text}"}
                
                else:
                    # Environment mismatch - skip this webhook but continue checking others
                    print(f"⚠️  Skipping webhook {webhook_id} (environment mismatch)")
                    print(f"   Current URL ({current_webhook_url}) is for different environment")
                    print(f"   Will not overwrite production webhook")
                    continue  # Continue checking other webhooks
            
            # After checking all webhooks, check if dev webhook exists
            dev_webhook_exists = any(
                'vani-dev.ngrok' in webhook.get('subscriberUrl', '').lower()
                for webhook in existing_webhooks
            )
            
            if dev_webhook_exists:
                print(f"\n✅ Dev webhook already exists in Cal.com")
                print(f"   Both dev and prod webhooks can coexist")
                print(f"   No action needed - webhook is already configured")
                return {'success': True, 'action': 'skipped', 'message': 'Dev webhook exists, prod webhook preserved'}
                    
        except Exception as e:
            print(f"⚠️  Error checking existing webhooks: {e}")
            import traceback
            traceback.print_exc()
        
        # If we get here, no matching webhook was found and no dev webhook exists
        # Create new webhook for this environment
        print("\nCreating new webhook...")
        webhook_data = {
            'subscriberUrl': self.cal_com_webhook_url,
            'eventTriggers': events,
            'secret': self.cal_com_webhook_secret,
            'active': True
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=webhook_data)
            
            if response.status_code == 201 or response.status_code == 200:
                webhook_info = response.json()
                webhook_id = webhook_info.get('id') or webhook_info.get('webhook', {}).get('id')
                print(f"✅ Webhook created successfully!")
                print(f"   Webhook ID: {webhook_id}")
                print(f"   Events: {', '.join(events)}")
                return {'success': True, 'webhook_id': webhook_id, 'action': 'created'}
            else:
                error_msg = response.text
                print(f"❌ Failed to create webhook: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            print(f"❌ Error creating webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def configure_all(self) -> Dict[str, Any]:
        """Configure all webhooks"""
        print("\n" + "="*70)
        print("  WEBHOOK CONFIGURATION")
        print("="*70)
        print(f"Base URL: {self.webhook_base_url}\n")
        
        results = {
            'resend': self.configure_resend_webhook(),
            'twilio': self.configure_twilio_webhook(),
            'cal_com': self.configure_cal_com_webhook()
        }
        
        # Summary
        print("\n" + "="*70)
        print("  SUMMARY")
        print("="*70)
        
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(results)
        
        for service, result in results.items():
            status = "✅" if result.get('success') else "❌"
            print(f"{status} {service.upper():15} - {result.get('action', 'failed')}")
            if not result.get('success'):
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n✅ Configured: {success_count}/{total_count} services")
        
        return results


def main():
    """Main function"""
    # Detect environment from environment variable or URL
    environment = os.getenv('VANI_ENVIRONMENT', '').lower()
    if environment not in ['dev', 'prod']:
        # Try to detect from WEBHOOK_BASE_URL
        webhook_url = os.getenv('WEBHOOK_BASE_URL', '')
        if 'vani-dev.ngrok' in webhook_url.lower():
            environment = 'dev'
        elif 'vani.ngrok' in webhook_url.lower() and 'vani-dev' not in webhook_url.lower():
            environment = 'prod'
        else:
            environment = 'dev'  # Default to dev for safety
    
    print(f"\n[*] Environment: {environment.upper()}")
    print(f"[*] Webhook Base URL: {os.getenv('WEBHOOK_BASE_URL', 'Not set')}\n")
    
    configurator = WebhookConfigurator(environment=environment)
    results = configurator.configure_all()
    
    # Check if all succeeded
    all_success = all(r.get('success') for r in results.values())
    return 0 if all_success else 1


if __name__ == '__main__':
    sys.exit(main())

