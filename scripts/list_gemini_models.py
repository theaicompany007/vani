"""List available Gemini models for the configured API key"""
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

def main():
    print("=" * 70)
    print("GEMINI AVAILABLE MODELS")
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
    
    print(f"✅ Found GEMINI_API_KEY")
    print(f"   Preview: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
    print()
    
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # List all models
        print("🔍 Fetching available models...")
        print()
        
        models = genai.list_models()
        
        # Filter models that support generateContent
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                # Extract model name (e.g., "models/gemini-pro" -> "gemini-pro")
                model_name = model.name.split('/')[-1] if '/' in model.name else model.name
                available_models.append({
                    'name': model_name,
                    'full_name': model.name,
                    'display_name': model.display_name,
                    'description': model.description if hasattr(model, 'description') else '',
                    'input_token_limit': model.input_token_limit if hasattr(model, 'input_token_limit') else None,
                    'output_token_limit': model.output_token_limit if hasattr(model, 'output_token_limit') else None,
                })
        
        if not available_models:
            print("❌ No models found that support generateContent")
            print()
            return 1
        
        print(f"✅ Found {len(available_models)} model(s) that support generateContent:")
        print()
        
        for i, model in enumerate(available_models, 1):
            print(f"{i}. {model['name']}")
            if model['display_name']:
                print(f"   Display Name: {model['display_name']}")
            if model['description']:
                print(f"   Description: {model['description'][:100]}...")
            if model['input_token_limit']:
                print(f"   Input Tokens: {model['input_token_limit']:,}")
            if model['output_token_limit']:
                print(f"   Output Tokens: {model['output_token_limit']:,}")
            print()
        
        print("=" * 70)
        print("RECOMMENDED MODELS FOR USE:")
        print("=" * 70)
        print()
        
        # Check for common models
        model_names = [m['name'] for m in available_models]
        
        if 'gemini-pro' in model_names:
            print("✅ gemini-pro - Stable, widely available (RECOMMENDED)")
        else:
            print("❌ gemini-pro - Not available")
        
        if 'gemini-1.5-flash' in model_names:
            print("✅ gemini-1.5-flash - Fast, efficient (RECOMMENDED)")
        else:
            print("❌ gemini-1.5-flash - Not available")
        
        if 'gemini-1.5-pro' in model_names:
            print("✅ gemini-1.5-pro - Advanced capabilities")
        else:
            print("❌ gemini-1.5-pro - Not available")
        
        if 'gemini-1.5-pro-latest' in model_names:
            print("✅ gemini-1.5-pro-latest - Latest pro version")
        else:
            print("❌ gemini-1.5-pro-latest - Not available")
        
        print()
        print("=" * 70)
        print("USAGE:")
        print("=" * 70)
        print()
        print("Set GEMINI_MODEL in your .env.local file to one of the available models:")
        print()
        for model in available_models[:5]:  # Show first 5
            print(f"  GEMINI_MODEL={model['name']}")
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

