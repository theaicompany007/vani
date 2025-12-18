"""Verify Gemini API setup and provide step-by-step verification"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables
project_root = Path(__file__).parent.parent
env_local = project_root / '.env.local'
if env_local.exists():
    load_dotenv(env_local, override=True)

def test_key(key: str):
    """Test a specific API key"""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": key
    }
    payload = {
        "contents": [{
            "parts": [{
                "text": "Say hello"
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return True, "SUCCESS", response.json()
        else:
            error = response.json() if response.text else {}
            return False, f"Status {response.status_code}", error
    except Exception as e:
        return False, "Request failed", str(e)

def main():
    print("=" * 70)
    print("GEMINI API SETUP VERIFICATION")
    print("=" * 70)
    print()
    
    # Get key from env or command line
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1].strip()
        print("Using API key from command line")
    elif api_key:
        print("Using API key from .env.local")
    else:
        print("No API key found. Please provide one:")
        print("  python scripts/verify_gemini_setup.py <API_KEY>")
        print()
        print("Or set GEMINI_API_KEY in .env.local")
        return 1
    
    print(f"Key: {api_key[:8]}...{api_key[-4:]} (length: {len(api_key)})")
    print()
    
    # Test the key
    print("Testing API key...")
    success, message, result = test_key(api_key)
    
    if success:
        print(f"✅ {message}")
        if result and 'candidates' in result:
            text = result['candidates'][0]['content']['parts'][0].get('text', '')
            print(f"Response: {text}")
        print()
        print("=" * 70)
        print("SUCCESS: Your API key is working!")
        print("=" * 70)
        return 0
    else:
        print(f"❌ {message}")
        if isinstance(result, dict) and 'error' in result:
            error = result['error']
            print(f"Error: {error.get('message', 'Unknown error')}")
        print()
        print("=" * 70)
        print("TROUBLESHOOTING GUIDE")
        print("=" * 70)
        print()
        print("The API key is being rejected. Follow these steps:")
        print()
        print("STEP 1: Verify API Key in Google Cloud Console")
        print("  URL: https://console.cloud.google.com/apis/credentials?project=831985493292")
        print("  - Find your API key 'Project VANI'")
        print("  - Click to view/edit it")
        print("  - Verify the key matches exactly (copy it again)")
        print()
        print("STEP 2: Check API Restrictions")
        print("  - Click 'Edit API key'")
        print("  - Under 'API restrictions':")
        print("    * If 'Restrict key' is enabled, ensure 'Generative Language API' is selected")
        print("    * OR set to 'Don't restrict key' for testing")
        print("  - Under 'Application restrictions':")
        print("    * Set to 'None' for testing")
        print("  - Click 'Save'")
        print()
        print("STEP 3: Verify API is Enabled")
        print("  URL: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com?project=831985493292")
        print("  - Should show 'API enabled'")
        print("  - If not, click 'Enable'")
        print()
        print("STEP 4: Check Billing")
        print("  URL: https://console.cloud.google.com/billing?project=831985493292")
        print("  - Ensure billing account is linked")
        print("  - Check for any billing issues")
        print()
        print("STEP 5: Create New Key from AI Studio (Recommended)")
        print("  URL: https://aistudio.google.com/app/apikey")
        print("  - Sign in with: kcube.consultingpartners@gmail.com")
        print("  - Click 'Create API Key'")
        print("  - Select project: 'Project VANI' (831985493292)")
        print("  - Copy the new key")
        print("  - Test it: python scripts/verify_gemini_setup.py <NEW_KEY>")
        print()
        print("STEP 6: Verify Key Format")
        print("  - Key should start with 'AIza'")
        print("  - Key should be 35-45 characters")
        print("  - No spaces, quotes, or special characters")
        print("  - Copy directly from Google Cloud Console (don't type manually)")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())






