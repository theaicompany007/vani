"""Test Twilio credentials"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '').strip()
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '').strip()

print("="*70)
print("  TWILIO CREDENTIALS TEST")
print("="*70)
print()

# Validate format
print("Credential Validation:")
print(f"   Account SID: {TWILIO_ACCOUNT_SID[:10]}...{TWILIO_ACCOUNT_SID[-4:] if len(TWILIO_ACCOUNT_SID) > 14 else ''}")
print(f"   SID Length: {len(TWILIO_ACCOUNT_SID)} characters")
print(f"   SID Starts with 'AC': {TWILIO_ACCOUNT_SID.startswith('AC')}")
print(f"   Auth Token: {'*' * (len(TWILIO_AUTH_TOKEN) - 4) + TWILIO_AUTH_TOKEN[-4:] if len(TWILIO_AUTH_TOKEN) > 4 else '***'}")
print(f"   Token Length: {len(TWILIO_AUTH_TOKEN)} characters")
print()

# Check for issues
issues = []
if not TWILIO_ACCOUNT_SID:
    issues.append("[X] TWILIO_ACCOUNT_SID is empty")
elif not TWILIO_ACCOUNT_SID.startswith('AC'):
    issues.append(f"[X] TWILIO_ACCOUNT_SID should start with 'AC' (got: {TWILIO_ACCOUNT_SID[:2]})")
elif len(TWILIO_ACCOUNT_SID) != 34:
    issues.append(f"[X] TWILIO_ACCOUNT_SID should be 34 characters (got: {len(TWILIO_ACCOUNT_SID)})")
else:
    print("[OK] Account SID format is correct")

if not TWILIO_AUTH_TOKEN:
    issues.append("[X] TWILIO_AUTH_TOKEN is empty")
elif len(TWILIO_AUTH_TOKEN) < 30:
    issues.append(f"[X] TWILIO_AUTH_TOKEN seems too short (got: {len(TWILIO_AUTH_TOKEN)}, expected ~32)")
else:
    print("[OK] Auth Token format is correct")

if issues:
    print("\n[!] Issues found:")
    for issue in issues:
        print(f"   {issue}")
    sys.exit(1)

print()

# Test authentication
print("Testing authentication...")
test_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}.json"

try:
    response = requests.get(
        test_url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        timeout=10
    )
    
    if response.status_code == 200:
        account_info = response.json()
        print("[OK] Authentication successful!")
        print(f"   Account Name: {account_info.get('friendly_name', 'N/A')}")
        print(f"   Account Status: {account_info.get('status', 'N/A')}")
        print(f"   Account Type: {account_info.get('type', 'N/A')}")
        print()
        
        # Test fetching phone numbers
        print("Testing phone number fetch...")
        numbers_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json"
        numbers_response = requests.get(
            numbers_url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=10
        )
        
        if numbers_response.status_code == 200:
            numbers = numbers_response.json().get('incoming_phone_numbers', [])
            print(f"[OK] Successfully fetched {len(numbers)} phone number(s)")
            print()
            print("Available phone numbers:")
            for num in numbers[:10]:
                phone = num.get('phone_number', 'N/A')
                sid = num.get('sid', 'N/A')
                print(f"   - {phone} (SID: {sid})")
            if len(numbers) > 10:
                print(f"   ... and {len(numbers) - 10} more")
            print()
            print("[OK] All tests passed! Credentials are working correctly.")
            sys.exit(0)
        else:
            print(f"[X] Failed to fetch phone numbers (status: {numbers_response.status_code})")
            print(f"   Response: {numbers_response.text[:200]}")
            sys.exit(1)
            
    elif response.status_code == 401:
        error_data = response.json() if response.text else {}
        error_code = error_data.get('code', '')
        error_msg = error_data.get('message', 'Authentication failed')
        print(f"[X] Authentication failed (401)")
        print(f"   Error Code: {error_code}")
        print(f"   Message: {error_msg}")
        print()
        print("Troubleshooting:")
        print("   1. Double-check credentials in Twilio Console:")
        print("      https://console.twilio.com/us1/account/settings/credentials")
        print("   2. Ensure there are no extra spaces in .env.local")
        print("   3. Try regenerating the Auth Token in Twilio Console")
        print("   4. Check if your Twilio account is active (not suspended)")
        sys.exit(1)
    else:
        print(f"[X] Unexpected response (status: {response.status_code})")
        print(f"   Response: {response.text[:200]}")
        sys.exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"[X] Network error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[X] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

