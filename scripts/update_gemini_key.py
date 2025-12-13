"""Helper script to update GEMINI_API_KEY in .env.local"""
import os
import sys
from pathlib import Path

# Fix Windows console encoding for emoji characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def update_env_file(api_key: str):
    """Update or add GEMINI_API_KEY in .env.local"""
    env_file = Path('.env.local')
    
    if not env_file.exists():
        print(f"Creating {env_file}...")
        env_file.write_text(f"GEMINI_API_KEY={api_key}\n", encoding='utf-8')
        print(f"✅ Created {env_file} with GEMINI_API_KEY")
        return True
    
    # Read existing file
    lines = env_file.read_text(encoding='utf-8').splitlines()
    
    # Find and update GEMINI_API_KEY line
    updated = False
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('GEMINI_API_KEY='):
            # Update existing line
            new_lines.append(f"GEMINI_API_KEY={api_key}")
            updated = True
            print(f"✅ Updated GEMINI_API_KEY in {env_file}")
        else:
            new_lines.append(line)
    
    if not updated:
        # Add new line
        new_lines.append(f"GEMINI_API_KEY={api_key}")
        print(f"✅ Added GEMINI_API_KEY to {env_file}")
    
    # Write back
    env_file.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/update_gemini_key.py <API_KEY>")
        print()
        print("Example:")
        print("  python scripts/update_gemini_key.py AIzaSyAc_olFzitL16vkgSBf9Bt13rq5LljR3s")
        print()
        return 1
    
    api_key = sys.argv[1].strip()
    
    # Validate format
    if not api_key.startswith('AIza'):
        print(f"❌ Error: API key does not start with 'AIza'")
        print(f"   Got: {api_key[:10]}...")
        return 1
    
    if len(api_key) < 35 or len(api_key) > 45:
        print(f"⚠️  Warning: API key length ({len(api_key)}) is outside typical range (35-45)")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    print(f"Updating GEMINI_API_KEY...")
    print(f"   Key preview: {api_key[:8]}...{api_key[-4:]} (length: {len(api_key)})")
    print()
    
    try:
        update_env_file(api_key)
        print()
        print("=" * 70)
        print("SUCCESS: GEMINI_API_KEY updated in .env.local")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Test the key: python scripts/test_gemini_api_key_direct.py")
        print("2. Restart your application if it's running")
        print()
        return 0
    except Exception as e:
        print(f"❌ Error updating file: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

