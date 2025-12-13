"""Comprehensive diagnostic script for Gemini API key"""
import os
import sys
import requests
import json
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
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file, override=False)

def verify_key_format(key: str):
    """Verify API key format"""
    issues = []
    
    if not key:
        return False, ["API key is empty"]
    
    key = key.strip()
    
    # Check prefix
    if not key.startswith('AIza'):
        issues.append(f"Key does not start with 'AIza' (got: {key[:10]}...)")
    
    # Check length
    if len(key) < 35:
        issues.append(f"Key too short: {len(key)} characters (expected 35-45)")
    elif len(key) > 45:
        issues.append(f"Key too long: {len(key)} characters (expected 35-45)")
    
    # Check for invalid characters
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')
    invalid_chars = [c for c in key if c not in valid_chars]
    if invalid_chars:
        issues.append(f"Invalid characters found: {set(invalid_chars)}")
    
    # Check for common issues
    if ' ' in key:
        issues.append("Key contains spaces (remove them)")
    if '\n' in key or '\r' in key:
        issues.append("Key contains newlines (remove them)")
    if key != key.strip():
        issues.append("Key has leading/trailing whitespace")
    
    return len(issues) == 0, issues

def test_with_header_auth(key: str, model: str = "gemini-pro"):
    """Test API key using header authentication"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
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
        return response.status_code, response.json() if response.text else None, None
    except requests.exceptions.RequestException as e:
        return None, None, str(e)

def test_with_query_auth(key: str, model: str = "gemini-pro"):
    """Test API key using query parameter authentication"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    headers = {
        "Content-Type": "application/json"
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
        return response.status_code, response.json() if response.text else None, None
    except requests.exceptions.RequestException as e:
        return None, None, str(e)

def test_list_models(key: str):
    """Test listing available models"""
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    # Try header auth
    headers = {"x-goog-api-key": key}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return True, "header", response.json()
    except:
        pass
    
    # Try query auth
    url_with_key = f"{url}?key={key}"
    try:
        response = requests.get(url_with_key, timeout=10)
        if response.status_code == 200:
            return True, "query", response.json()
    except:
        pass
    
    return False, None, None

def main():
    print("=" * 70)
    print("GEMINI API KEY COMPREHENSIVE DIAGNOSTIC")
    print("=" * 70)
    print()
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print()
        print("Please set it in .env.local or provide it as an argument:")
        print("  python scripts/diagnose_gemini_key.py <API_KEY>")
        return 1
    
    # Allow override via command line
    if len(sys.argv) > 1:
        api_key = sys.argv[1].strip()
        print(f"Using API key from command line argument")
    
    print(f"API Key Preview: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
    print(f"Key Length: {len(api_key)} characters")
    print()
    
    # Step 1: Verify format
    print("=" * 70)
    print("STEP 1: VERIFYING KEY FORMAT")
    print("=" * 70)
    print()
    
    is_valid_format, issues = verify_key_format(api_key)
    
    if is_valid_format:
        print("✅ Key format is valid")
        print(f"   - Starts with: {api_key[:4]}")
        print(f"   - Length: {len(api_key)} characters")
        print(f"   - No invalid characters detected")
    else:
        print("❌ Key format issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        print("Please fix these issues and try again.")
        return 1
    
    print()
    
    # Step 2: Test with header authentication
    print("=" * 70)
    print("STEP 2: TESTING HEADER AUTHENTICATION")
    print("=" * 70)
    print()
    
    models_to_test = ["gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
    header_success = False
    
    for model in models_to_test:
        print(f"Testing {model} with header auth...", end=" ")
        status, result, error = test_with_header_auth(api_key, model)
        
        if status == 200:
            print("✅ SUCCESS")
            header_success = True
            if result and 'candidates' in result:
                text = result['candidates'][0]['content']['parts'][0].get('text', '')
                print(f"   Response: {text[:100]}")
            break
        elif status == 400:
            error_msg = result.get('error', {}).get('message', '') if result else str(error)
            if 'API key not valid' in error_msg or 'API_KEY_INVALID' in str(result):
                print("❌ API key invalid")
            elif 'not found' in error_msg.lower() or '404' in str(result):
                print("⚠️  Model not available")
            else:
                print(f"❌ Error: {error_msg[:50]}")
        else:
            print(f"❌ Status {status}")
            if result:
                print(f"   Error: {result.get('error', {}).get('message', '')[:100]}")
    
    print()
    
    # Step 3: Test with query parameter authentication
    print("=" * 70)
    print("STEP 3: TESTING QUERY PARAMETER AUTHENTICATION")
    print("=" * 70)
    print()
    
    query_success = False
    
    for model in models_to_test:
        print(f"Testing {model} with query param auth...", end=" ")
        status, result, error = test_with_query_auth(api_key, model)
        
        if status == 200:
            print("✅ SUCCESS")
            query_success = True
            if result and 'candidates' in result:
                text = result['candidates'][0]['content']['parts'][0].get('text', '')
                print(f"   Response: {text[:100]}")
            break
        elif status == 400:
            error_msg = result.get('error', {}).get('message', '') if result else str(error)
            if 'API key not valid' in error_msg or 'API_KEY_INVALID' in str(result):
                print("❌ API key invalid")
            elif 'not found' in error_msg.lower() or '404' in str(result):
                print("⚠️  Model not available")
            else:
                print(f"❌ Error: {error_msg[:50]}")
        else:
            print(f"❌ Status {status}")
            if result:
                print(f"   Error: {result.get('error', {}).get('message', '')[:100]}")
    
    print()
    
    # Step 4: Test listing models
    print("=" * 70)
    print("STEP 4: TESTING LIST MODELS ENDPOINT")
    print("=" * 70)
    print()
    
    print("Testing list models endpoint...", end=" ")
    success, auth_method, models_data = test_list_models(api_key)
    
    if success:
        print(f"✅ SUCCESS (using {auth_method} auth)")
        if models_data and 'models' in models_data:
            available_models = [m['name'].split('/')[-1] for m in models_data['models'] 
                              if 'generateContent' in m.get('supportedGenerationMethods', [])]
            print(f"   Found {len(available_models)} models that support generateContent:")
            for model in available_models[:10]:
                print(f"     - {model}")
            if len(available_models) > 10:
                print(f"     ... and {len(available_models) - 10} more")
    else:
        print("❌ FAILED")
        print("   Could not list models with either authentication method")
    
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    if header_success or query_success:
        print("✅ API KEY IS VALID AND WORKING!")
        print()
        if header_success:
            print("   ✅ Header authentication works")
        if query_success:
            print("   ✅ Query parameter authentication works")
        print()
        print("Your API key is configured correctly and can make API calls.")
        print("If you're still seeing errors in your application, check:")
        print("  1. The key is correctly set in .env.local")
        print("  2. Your application is loading .env.local correctly")
        print("  3. Restart your application after updating the key")
        return 0
    else:
        print("❌ API KEY TEST FAILED")
        print()
        print("The API key is being rejected by Google's API.")
        print()
        print("POSSIBLE CAUSES:")
        print("  1. API key is incorrect or was copied with errors")
        print("  2. API key was created in a different Google Cloud project")
        print("  3. Generative Language API is not enabled for this project")
        print("  4. Billing is not enabled for the Google Cloud project")
        print("  5. API key was revoked or deleted")
        print()
        print("NEXT STEPS:")
        print("  1. Verify the key in Google Cloud Console:")
        print("     https://console.cloud.google.com/apis/credentials")
        print("  2. Check that Generative Language API is enabled:")
        print("     https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com")
        print("  3. Create a new API key and test again")
        print("  4. Ensure billing is enabled for the project")
        return 1

if __name__ == '__main__':
    sys.exit(main())

