"""Test script to validate Gemini API key credentials"""
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent.parent / '.env.local'
if env_file.exists():
    load_dotenv(env_file)
else:
    # Try .env file
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)

def validate_api_key_format(api_key: str):
    """
    Validate Gemini API key format
    
    Returns:
        (is_valid, error_message)
    """
    if not api_key:
        return False, "API key is empty"
    
    api_key = api_key.strip()
    
    if not api_key.startswith('AIza'):
        return False, f"API key does not start with 'AIza'. Expected format: AIza... (got: {api_key[:10]}...)"
    
    if len(api_key) < 35 or len(api_key) > 45:
        return False, f"API key length ({len(api_key)}) is outside typical range (35-45 characters)"
    
    return True, "Format looks valid"

def test_api_key(api_key: str):
    """
    Test the API key by making an actual API call
    
    Returns:
        (is_valid, error_message, working_model, available_models)
    """
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # First, try to list available models
        available_models = []
        try:
            models = genai.list_models()
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.split('/')[-1] if '/' in model.name else model.name
                    available_models.append(model_name)
        except Exception as e:
            print(f"   ⚠️  Could not list available models: {e}")
        
        # Try multiple models with actual API calls
        models_to_try = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-pro-latest', 'gemini-2.0-flash-exp']
        model = None
        working_model = None
        
        print("   Testing models:")
        for test_model in models_to_try:
            try:
                print(f"      - {test_model}...", end=" ")
                test_model_obj = genai.GenerativeModel(test_model)
                # Actually test with a real API call to verify model is available
                test_response = test_model_obj.generate_content(
                    "test",
                    generation_config={
                        'temperature': 0.1,
                        'max_output_tokens': 10,
                    }
                )
                # If we get here, the model works
                model = test_model_obj
                working_model = test_model
                print("✅ Available")
                break
            except Exception as e:
                error_str = str(e)
                if 'not found' in error_str.lower() or '404' in error_str or 'not supported' in error_str.lower():
                    print("❌ Not available")
                    continue
                else:
                    print(f"❌ Error: {error_str[:50]}")
                    # For other errors, continue trying other models
                    continue
        
        if not model or not working_model:
            return False, f"None of the tested models are available: {models_to_try}", None, available_models
        
        # Make a proper test call with the working model
        print(f"   Making test API call with {working_model}...")
        response = model.generate_content(
            "Say 'API key is valid' if you can read this.",
            generation_config={
                'temperature': 0.1,
                'max_output_tokens': 50,
            }
        )
        
        if response and response.text:
            return True, f"API key is valid and working with model: {working_model}", working_model, available_models
        else:
            return False, "API call succeeded but no response received", working_model, available_models
            
    except Exception as e:
        error_str = str(e)
        if 'API key not valid' in error_str or 'API_KEY_INVALID' in error_str:
            return False, f"API key is invalid: {error_str}", None, []
        else:
            return False, f"API call failed: {error_str}", None, []

def main():
    print("=" * 70)
    print("GEMINI API KEY VALIDATION TEST")
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
        return 1
    
    print(f"✅ Found GEMINI_API_KEY in environment")
    print(f"   Preview: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''} (length: {len(api_key)})")
    print()
    
    # Validate format
    print("🔍 Validating API key format...")
    is_valid_format, format_message = validate_api_key_format(api_key)
    
    if not is_valid_format:
        print(f"❌ Format validation failed: {format_message}")
        print()
        print("TROUBLESHOOTING:")
        print("1. Get a new API key from: https://aistudio.google.com/app/apikey")
        print("2. Ensure the key starts with 'AIza'")
        print("3. Check that the key is complete (no truncation)")
        print()
        return 1
    
    print(f"✅ {format_message}")
    print()
    
    # Test API key
    print("🧪 Testing API key with actual API call...")
    print()
    try:
        is_valid, test_message, working_model, available_models = test_api_key(api_key)
        
        if is_valid:
            print()
            print(f"✅ {test_message}")
            print()
            
            # Show available models if we got them
            if available_models:
                print("=" * 70)
                print("AVAILABLE MODELS FOR THIS API KEY:")
                print("=" * 70)
                print()
                for model_name in available_models[:10]:  # Show first 10
                    marker = "✅ (WORKING)" if model_name == working_model else ""
                    print(f"  - {model_name} {marker}")
                if len(available_models) > 10:
                    print(f"  ... and {len(available_models) - 10} more")
                print()
                print("💡 TIP: Set GEMINI_MODEL in .env.local to use a specific model")
                print(f"   Example: GEMINI_MODEL={working_model}")
                print()
            
            print("=" * 70)
            print("SUCCESS: Gemini API key is valid and working!")
            print("=" * 70)
            return 0
        else:
            print()
            print(f"❌ {test_message}")
            print()
            
            # Show available models even if test failed (might help diagnose)
            if available_models:
                print("=" * 70)
                print("AVAILABLE MODELS (but test failed):")
                print("=" * 70)
                print()
                for model_name in available_models[:10]:
                    print(f"  - {model_name}")
                if len(available_models) > 10:
                    print(f"  ... and {len(available_models) - 10} more")
                print()
                print("💡 Try listing models: python scripts/list_gemini_models.py")
                print()
            
            print("TROUBLESHOOTING:")
            print("1. Verify your API key is correct and not expired")
            print("2. Get a new API key from: https://aistudio.google.com/app/apikey")
            print("3. Check that the API key has not been revoked or restricted")
            print("4. Ensure you have enabled the Gemini API in Google Cloud Console")
            print("5. Check your Google Cloud billing/quota settings")
            print("6. Try listing available models: python scripts/list_gemini_models.py")
            print()
            return 1
            
    except Exception as e:
        print()
        print(f"❌ Unexpected error during API test: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

