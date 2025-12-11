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
    """Configure webhooks for all services"""
    
    def _get_ngrok_url(self) -> Optional[str]:
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
    
    def __init__(self):
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
        
        # Twilio
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        # Support WhatsApp Sandbox (priority: sandbox > regular)
        whatsapp_num = os.getenv('TWILIO_SANDBOX_WHATSAPP_NUMBER') or os.getenv('TWILIO_WHATSAPP_NUMBER', '')
        self.twilio_whatsapp_number = whatsapp_num.replace('whatsapp:', '').replace('+', '')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '').replace('+', '')
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
                
                # Check if webhook already exists
                for webhook in existing_webhooks:
                    if webhook.get('url') == self.resend_webhook_url:
                        webhook_id = webhook.get('id')
                        print(f"✅ Webhook already exists (ID: {webhook_id})")
                        
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
        
        # Twilio API endpoint
        # First, get the phone number SID
        numbers_url = f"https://{self.twilio_account_sid}:{self.twilio_auth_token}@api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/IncomingPhoneNumbers.json"
        
        try:
            response = requests.get(numbers_url)
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch phone numbers: {response.text}")
                return {'success': False, 'error': 'Could not fetch phone numbers'}
            
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
            
            # Update the number's status callback
            update_url = f"https://{self.twilio_account_sid}:{self.twilio_auth_token}@api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/IncomingPhoneNumbers/{number_sid}.json"
            
            update_data = {
                'StatusCallback': self.twilio_webhook_url,
                'StatusCallbackMethod': 'POST'
            }
            
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
        
        # Cal.com API endpoint for webhooks
        api_url = "https://api.cal.com/v1/webhooks"
        
        # Cal.com API v1 uses Bearer token, v2 uses x-cal-secret-key
        # Based on key format: cal_live_xxx or cal_test_xxx
        if self.cal_com_api_key.startswith('cal_live_') or self.cal_com_api_key.startswith('cal_test_'):
            # This is a v1 API key, use Bearer token
            headers = {
                'Authorization': f'Bearer {self.cal_com_api_key}',
                'Content-Type': 'application/json'
            }
            print(f"✅ Using Cal.com v1 API (Bearer token)")
        else:
            # Try v2 format (requires both headers)
            headers = {
                'x-cal-secret-key': self.cal_com_api_key,
                'x-cal-api-key': self.cal_com_api_key,  # Some endpoints need both
                'Content-Type': 'application/json'
            }
            print(f"⚠️  Trying Cal.com v2 API format")
        
        # Note: Cal.com API authentication can be complex
        # If this fails, configure webhooks manually in Cal.com dashboard
        
        # Events to subscribe to
        events = [
            'BOOKING_CREATED',
            'BOOKING_CANCELLED',
            'BOOKING_RESCHEDULED'
        ]
        
        # List existing webhooks
        try:
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                existing_webhooks = response.json().get('webhooks', [])
                print(f"\nFound {len(existing_webhooks)} existing webhook(s)")
                
                # Check if webhook already exists
                for webhook in existing_webhooks:
                    if webhook.get('subscriberUrl') == self.cal_com_webhook_url:
                        webhook_id = webhook.get('id')
                        print(f"✅ Webhook already exists (ID: {webhook_id})")
                        
                        # Update webhook
                        update_url = f"{api_url}/{webhook_id}"
                        update_data = {
                            'eventTriggers': events,
                            'secret': self.cal_com_webhook_secret
                        }
                        update_response = requests.patch(update_url, headers=headers, json=update_data)
                        
                        if update_response.status_code == 200:
                            print(f"✅ Webhook updated successfully")
                            return {'success': True, 'webhook_id': webhook_id, 'action': 'updated'}
                        else:
                            print(f"⚠️  Failed to update webhook: {update_response.text}")
                            return {'success': False, 'error': f"Update failed: {update_response.text}"}
            else:
                print(f"⚠️  Could not list webhooks: {response.text}")
        except Exception as e:
            print(f"⚠️  Error checking existing webhooks: {e}")
        
        # Create new webhook
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
    configurator = WebhookConfigurator()
    results = configurator.configure_all()
    
    # Check if all succeeded
    all_success = all(r.get('success') for r in results.values())
    return 0 if all_success else 1


if __name__ == '__main__':
    sys.exit(main())

