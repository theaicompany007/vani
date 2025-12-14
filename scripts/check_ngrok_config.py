#!/usr/bin/env python3
"""Diagnostic script to check ngrok configuration"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
basedir = Path(__file__).parent.parent
sys.path.insert(0, str(basedir))

# Load environment
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

print("=" * 70)
print("  NGROK CONFIGURATION DIAGNOSTIC")
print("=" * 70)
print()

# Check 1: Environment variables
print("[1] Environment Variables:")
print("-" * 70)
ngrok_domain = os.getenv('NGROK_DOMAIN')
webhook_base = os.getenv('WEBHOOK_BASE_URL')
flask_port = os.getenv('FLASK_PORT', '5000')

print(f"  NGROK_DOMAIN:     {ngrok_domain or '(not set)'}")
print(f"  WEBHOOK_BASE_URL: {webhook_base or '(not set)'}")
print(f"  FLASK_PORT:       {flask_port}")
print()

# Check 2: .env.local file
print("[2] .env.local File:")
print("-" * 70)
env_local = basedir / '.env.local'
if env_local.exists():
    print(f"  ✅ File exists: {env_local}")
    # Read and show relevant lines
    with open(env_local, 'r') as f:
        lines = f.readlines()
        ngrok_lines = [l.strip() for l in lines if 'NGROK' in l.upper() or 'WEBHOOK' in l.upper()]
        if ngrok_lines:
            print("  Found ngrok-related settings:")
            for line in ngrok_lines:
                if not line.startswith('#'):
                    # Mask sensitive parts
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if 'KEY' in key.upper() or 'TOKEN' in key.upper() or 'SECRET' in key.upper():
                            print(f"    {key}=***")
                        else:
                            print(f"    {line}")
        else:
            print("  ⚠️  No ngrok-related settings found")
else:
    print(f"  ❌ File not found: {env_local}")
print()

# Check 3: ngrok.config.json
print("[3] ngrok.config.json File:")
print("-" * 70)
ngrok_json = basedir / 'ngrok.config.json'
if ngrok_json.exists():
    print(f"  ✅ File exists: {ngrok_json}")
    try:
        with open(ngrok_json, 'r') as f:
            config = json.load(f)
            if 'ngrok' in config:
                print(f"    Domain: {config['ngrok'].get('domain', '(not set)')}")
                print(f"    Port:   {config['ngrok'].get('port', '(not set)')}")
            if 'webhooks' in config:
                print(f"    Webhook URL: {config['webhooks'].get('base_url', '(not set)')}")
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
else:
    print(f"  ⚠️  File not found: {ngrok_json}")
print()

# Check 4: Load via load_ngrok_config
print("[4] Loaded Configuration (via load_ngrok_config):")
print("-" * 70)
try:
    from scripts.load_ngrok_config import load_ngrok_config
    config = load_ngrok_config()
    print(f"  Domain:           {config.get('domain') or '(not set)'}")
    print(f"  Port:             {config.get('port', 5000)}")
    print(f"  Webhook Base URL: {config.get('webhook_base_url') or '(not set)'}")
except Exception as e:
    print(f"  ❌ Error loading config: {e}")
    import traceback
    traceback.print_exc()
print()

# Check 5: Ngrok executable
print("[5] Ngrok Executable:")
print("-" * 70)
import shutil
ngrok_path = shutil.which('ngrok')
if ngrok_path:
    print(f"  ✅ Found: {ngrok_path}")
    # Check version
    import subprocess
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"    Version: {result.stdout.strip()}")
    except:
        print("    ⚠️  Could not get version")
else:
    print("  ❌ Not found in PATH")
    print("     Install: https://ngrok.com/download")
print()

# Check 6: Ngrok authtoken
print("[6] Ngrok Authtoken:")
print("-" * 70)
try:
    import subprocess
    # Check ngrok config
    config_paths = [
        Path(os.getenv('LOCALAPPDATA', '')) / 'ngrok' / 'ngrok.yml',
        Path(os.getenv('USERPROFILE', '')) / '.ngrok2' / 'ngrok.yml',
    ]
    
    found_config = False
    for config_path in config_paths:
        if config_path.exists():
            print(f"  ✅ Config file: {config_path}")
            found_config = True
            # Check if authtoken is set
            with open(config_path, 'r') as f:
                content = f.read()
                if 'authtoken' in content.lower():
                    print("    ✅ Authtoken appears to be configured")
                else:
                    print("    ⚠️  Authtoken not found in config")
            break
    
    if not found_config:
        print("  ⚠️  No ngrok config file found")
        print("     Run: ngrok config add-authtoken YOUR_TOKEN")
except Exception as e:
    print(f"  ❌ Error checking authtoken: {e}")
print()

# Check 7: Ngrok running
print("[7] Ngrok Process Status:")
print("-" * 70)
try:
    import requests
    response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
    if response.status_code == 200:
        data = response.json()
        tunnels = data.get('tunnels', [])
        if tunnels:
            print(f"  ✅ Ngrok is running ({len(tunnels)} tunnel(s))")
            for tunnel in tunnels:
                print(f"    - {tunnel.get('public_url')} -> {tunnel.get('config', {}).get('addr', 'unknown')}")
        else:
            print("  ⚠️  Ngrok API responding but no tunnels found")
    else:
        print(f"  ⚠️  Ngrok API returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("  ❌ Ngrok is not running (API not accessible)")
except Exception as e:
    print(f"  ❌ Error checking ngrok: {e}")
print()

# Summary
print("=" * 70)
print("  SUMMARY & RECOMMENDATIONS")
print("=" * 70)
print()

domain = config.get('domain') if 'config' in locals() else ngrok_domain
if not domain:
    print("❌ No ngrok domain configured!")
    print()
    print("To fix:")
    print("  1. Add to .env.local:")
    print("     NGROK_DOMAIN=vani-dev.ngrok.app")
    print("     WEBHOOK_BASE_URL=https://vani-dev.ngrok.app")
    print()
    print("  2. Or update ngrok.config.json:")
    print('     {"ngrok": {"domain": "vani-dev.ngrok.app"}}')
    print()
else:
    print(f"✅ Domain configured: {domain}")
    print()
    print("Make sure:")
    print(f"  1. Domain '{domain}' is reserved in ngrok dashboard")
    print("     https://dashboard.ngrok.com/cloud-edge/domains")
    print("  2. Authtoken is configured: ngrok config add-authtoken YOUR_TOKEN")
    print("  3. Ngrok is in PATH or run from project directory")

print()







