"""Test API keys to diagnose issues"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

print("\n" + "="*70)
print("  API KEY DIAGNOSTICS")
print("="*70 + "\n")

# Test Resend
print("1. TESTING RESEND API KEY")
print("-" * 70)
resend_key = os.getenv('RESEND_API_KEY')
if resend_key:
    print(f"Key format: {resend_key[:10]}...{resend_key[-4:]}")
    headers = {'Authorization': f'Bearer {resend_key}'}
    try:
        r = requests.get('https://api.resend.com/domains', headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("✅ Resend API key is VALID")
        else:
            print(f"❌ Resend API key is INVALID")
            print(f"   Response: {r.text[:200]}")
            print("\n💡 Action needed:")
            print("   - Verify key at: https://resend.com/api-keys")
            print("   - Regenerate if needed")
            print("   - Ensure key has webhook permissions")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ RESEND_API_KEY not found")

# Test Twilio
print("\n2. TESTING TWILIO API KEYS")
print("-" * 70)
twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
if twilio_sid and twilio_token:
    print(f"Account SID: {twilio_sid}")
    print(f"Auth Token: {twilio_token[:10]}...{twilio_token[-4:]}")
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/IncomingPhoneNumbers.json"
        r = requests.get(url, auth=(twilio_sid, twilio_token))
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            numbers = data.get('incoming_phone_numbers', [])
            print(f"✅ Twilio API keys are VALID")
            print(f"   Found {len(numbers)} phone number(s):")
            for num in numbers[:5]:
                print(f"     - {num.get('phone_number')} (SID: {num.get('sid')})")
            if len(numbers) == 0:
                print("   ⚠️  No phone numbers found in account")
        else:
            print(f"❌ Twilio API keys are INVALID")
            print(f"   Response: {r.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not found")

# Test Cal.com
print("\n3. TESTING CAL.COM API KEY")
print("-" * 70)
cal_key = os.getenv('CAL_COM_API_KEY')
if cal_key:
    print(f"Key format: {cal_key[:15]}...{cal_key[-4:]}")
    
    # Try v1 API (Bearer token)
    headers_v1 = {
        'Authorization': f'Bearer {cal_key}',
        'Content-Type': 'application/json'
    }
    try:
        r = requests.get('https://api.cal.com/v1/me', headers=headers_v1)
        print(f"v1 API Status: {r.status_code}")
        if r.status_code == 200:
            print("✅ Cal.com API key is VALID (v1 API)")
        else:
            print(f"   Response: {r.text[:200]}")
            
            # Try v2 API
            headers_v2 = {
                'x-cal-secret-key': cal_key,
                'Content-Type': 'application/json'
            }
            r2 = requests.get('https://api.cal.com/v2/me', headers=headers_v2)
            print(f"v2 API Status: {r2.status_code}")
            if r2.status_code == 200:
                print("✅ Cal.com API key is VALID (v2 API)")
            else:
                print(f"   Response: {r2.text[:200]}")
                print("\n💡 Action needed:")
                print("   - Verify key at: https://cal.com/settings/developer/api-keys")
                print("   - Check if key needs to be regenerated")
                print("   - Ensure key has webhook permissions")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ CAL_COM_API_KEY not found")

print("\n" + "="*70)
print("  DIAGNOSTICS COMPLETE")
print("="*70 + "\n")

