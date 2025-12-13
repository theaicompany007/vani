"""Direct test of Gemini API key using REST API"""
import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows console encoding for emoji characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables - prioritize .env.local and override any existing values
project_root = Path(__file__).parent.parent
env_local = project_root / '.env.local'
env_file = project_root / '.env'

# Load .env.local first (with override to replace any existing values)
if env_local.exists():
    load_dotenv(env_local, override=True)
# Then load .env (won't override values already set from .env.local)
if env_file.exists():
    load_dotenv(env_file, override=False)

def test_api_key_direct(api_key: str, model: str = None):
    """Test API key directly using REST API"""
    # Try to get model from env, or use default
    if not model:
        model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        # Remove comment if present
        model = model.split('#')[0].strip()
    
    # Try multiple models - use available models from the API
    models_to_try = [
        model,  # Try configured model first
        'gemini-2.0-flash',  # Most commonly available
        'gemini-2.5-flash',  # Latest flash model
        'gemini-2.5-pro',    # Latest pro model
        'gemini-2.0-flash-exp',  # Experimental
        'gemini-1.5-flash',  # Fallback
        'gemini-pro'  # Legacy fallback
    ]
    models_to_try = list(dict.fromkeys(models_to_try))  # Remove duplicates while preserving order
    
    for test_model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{test_model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
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
                return True, response.json(), None, test_model
            elif response.status_code == 404:
                # Model not found, try next one
                continue
            else:
                response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_data = None
            try:
                error_data = e.response.json()
                # If it's a 404 (model not found), try next model
                if e.response.status_code == 404:
                    continue
            except:
                error_data = {"error": str(e)}
            # For other errors, return the error
            return False, None, error_data, test_model
        except Exception as e:
            return False, None, {"error": str(e)}, test_model
    
    # If we get here, none of the models worked
    return False, None, {"error": f"None of the tested models are available: {models_to_try}"}, None

def main():
    print("=" * 70)
    print("GEMINI API KEY DIRECT TEST (REST API)")
    print("=" * 70)
    print()
    
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print()
        print("TROUBLESHOOTING:")
        print("1. Check your .env.local or .env file")
        print("2. Ensure GEMINI_API_KEY is set")
        print("3. Get an API key from: https://aistudio.google.com/app/apikey")
        print()
        print("To test with a specific key:")
        print("  python scripts/test_gemini_api_key_direct.py")
        print("  # Or set it in the command:")
        print("  $env:GEMINI_API_KEY='your-key-here'; python scripts/test_gemini_api_key_direct.py")
        return 1
    
    api_key = api_key.strip()
    
    print(f"✅ Found GEMINI_API_KEY")
    print(f"   Preview: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''} (length: {len(api_key)})")
    print()
    
    # Validate format
    if not api_key.startswith('AIza'):
        print("❌ API key does not start with 'AIza'")
        print(f"   Got: {api_key[:10]}...")
        print()
        print("TROUBLESHOOTING:")
        print("1. Get a new API key from: https://aistudio.google.com/app/apikey")
        print("2. Ensure the key starts with 'AIza'")
        print("3. Check for extra spaces or characters")
        return 1
    
    if len(api_key) < 35 or len(api_key) > 45:
        print(f"⚠️  API key length ({len(api_key)}) is outside typical range (35-45 characters)")
        print("   This might still work, but verify the key is complete")
        print()
    
    # Test API key
    print("🧪 Testing API key with direct REST API call...")
    print(f"   URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent")
    print()
    
    is_valid, result, error, working_model = test_api_key_direct(api_key)
    
    if is_valid:
        print(f"✅ API key is VALID and working with model: {working_model}")
        print()
        if result and 'candidates' in result:
            if result['candidates'] and 'content' in result['candidates'][0]:
                text = result['candidates'][0]['content']['parts'][0].get('text', '')
                print(f"Response: {text[:100]}")
        print()
        print("=" * 70)
        print("SUCCESS: Your API key is valid and can make API calls!")
        print("=" * 70)
        if working_model:
            print()
            print(f"💡 RECOMMENDATION: Update GEMINI_MODEL in .env.local to:")
            print(f"   GEMINI_MODEL={working_model}")
        return 0
    else:
        print("❌ API key test FAILED")
        print()
        
        if error:
            print("Error Details:")
            print(json.dumps(error, indent=2))
            print()
            
            error_code = error.get('error', {}).get('code', '')
            error_message = error.get('error', {}).get('message', '')
            error_reason = None
            
            if 'details' in error.get('error', {}):
                for detail in error['error']['details']:
                    if detail.get('@type') == 'type.googleapis.com/google.rpc.ErrorInfo':
                        error_reason = detail.get('reason', '')
            
            if 'API_KEY_INVALID' in str(error_reason) or 'API key not valid' in error_message:
                print("=" * 70)
                print("API KEY IS INVALID")
                print("=" * 70)
                print()
                print("TROUBLESHOOTING STEPS:")
                print()
                print("1. ✅ Verify the API key is correct:")
                print(f"   Current key preview: {api_key[:8]}...{api_key[-4:]}")
                print()
                print("2. 🔑 Get a NEW API key:")
                print("   - Go to: https://aistudio.google.com/app/apikey")
                print("   - Sign in with your Google account")
                print("   - Click 'Create API Key'")
                print("   - Copy the new key (starts with 'AIza')")
                print()
                print("3. 📝 Update your .env.local file:")
                print("   GEMINI_API_KEY=your_new_key_here")
                print()
                print("4. 🔄 Restart your application after updating the key")
                print()
                print("5. ✅ Test again:")
                print("   python scripts/test_gemini_api_key_direct.py")
                print()
                print("6. 🔍 Check for common issues:")
                print("   - Extra spaces before/after the key")
                print("   - Key was copied incorrectly (missing characters)")
                print("   - Key was revoked or expired")
                print("   - Wrong Google account (key from different account)")
                print()
            else:
                print("TROUBLESHOOTING:")
                print("1. Check the error message above")
                print("2. Verify your API key is correct")
                print("3. Check Google Cloud Console for API status")
                print("4. Ensure Gemini API is enabled in your project")
        
        return 1

if __name__ == '__main__':
    sys.exit(main())

