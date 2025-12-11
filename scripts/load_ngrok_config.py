"""Load ngrok configuration from multiple sources"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Try to import yaml for reading ngrok.yml (optional)
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_ngrok_config() -> Dict[str, Any]:
    """
    Load ngrok configuration from multiple sources in priority order:
    1. .env.local (highest priority)
    2. ngrok.config.json
    3. Environment variables
    4. Defaults
    
    Returns:
        Dict with ngrok configuration
    """
    basedir = Path(__file__).parent.parent
    
    # Load .env.local first
    load_dotenv(basedir / '.env')
    load_dotenv(basedir / '.env.local', override=True)
    
    config = {
        'domain': None,
        'port': 5000,
        'protocol': 'http',
        'webhook_base_url': None,
    }
    
    # Priority 1: .env.local
    config['webhook_base_url'] = os.getenv('WEBHOOK_BASE_URL')
    config['domain'] = os.getenv('NGROK_DOMAIN')
    config['port'] = int(os.getenv('FLASK_PORT', '5000'))
    
    # Extract domain from WEBHOOK_BASE_URL if NGROK_DOMAIN not set
    if not config['domain'] and config['webhook_base_url']:
        # Extract domain from URL (e.g., https://vani.ngrok.app -> vani.ngrok.app)
        import re
        match = re.search(r'https?://([^/]+)', config['webhook_base_url'])
        if match:
            config['domain'] = match.group(1)
    
    # Priority 2: ngrok.yml (if available)
    if HAS_YAML:
        try:
            from .read_ngrok_yml import get_vani_tunnel_config
            vani_tunnel = get_vani_tunnel_config()
            if vani_tunnel:
                if not config['domain']:
                    config['domain'] = vani_tunnel.get('domain')
                if config['port'] == 5000:
                    addr = vani_tunnel.get('addr', '5000')
                    # Handle format like "5000" or "localhost:5000"
                    if ':' in str(addr):
                        config['port'] = int(str(addr).split(':')[-1])
                    else:
                        config['port'] = int(addr)
        except Exception:
            pass  # Silently fail if can't read ngrok.yml
    
    # Priority 3: ngrok.config.json (fallback)
    ngrok_config_path = basedir / 'ngrok.config.json'
    if ngrok_config_path.exists():
        try:
            with open(ngrok_config_path, 'r') as f:
                ngrok_json = json.load(f)
                
            # Use JSON values if not set from .env.local or ngrok.yml
            if not config['domain'] and 'ngrok' in ngrok_json:
                config['domain'] = ngrok_json['ngrok'].get('domain')
            
            if config['port'] == 5000 and 'ngrok' in ngrok_json:
                config['port'] = ngrok_json['ngrok'].get('port', 5000)
            
            if not config['webhook_base_url'] and 'webhooks' in ngrok_json:
                config['webhook_base_url'] = ngrok_json['webhooks'].get('base_url')
                
        except Exception as e:
            print(f"⚠️  Could not load ngrok.config.json: {e}")
    
    # Priority 4: Environment variables (already loaded via dotenv)
    if not config['domain']:
        config['domain'] = os.getenv('NGROK_DOMAIN')
    
    # Priority 5: Defaults
    if not config['webhook_base_url']:
        if config['domain']:
            config['webhook_base_url'] = f"https://{config['domain']}"
        else:
            config['webhook_base_url'] = None  # Will need to get from ngrok API
    
    return config


def get_ngrok_url_from_api() -> Optional[str]:
    """
    Get current ngrok URL from ngrok API (localhost:4040)
    
    Returns:
        Public ngrok URL or None if ngrok not running
    """
    try:
        import requests
        response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('tunnels') and len(data['tunnels']) > 0:
                return data['tunnels'][0].get('public_url')
    except Exception:
        pass
    return None


def get_ngrok_config() -> Dict[str, Any]:
    """
    Get complete ngrok configuration, including live URL if available
    
    Returns:
        Dict with all ngrok settings
    """
    config = load_ngrok_config()
    
    # Try to get live URL from ngrok API
    live_url = get_ngrok_url_from_api()
    if live_url:
        config['live_url'] = live_url
        # Update webhook_base_url if it doesn't match
        if not config['webhook_base_url'] or config['webhook_base_url'] != live_url:
            config['webhook_base_url'] = live_url
    
    return config


if __name__ == '__main__':
    # Test loading
    config = get_ngrok_config()
    print("\nNgrok Configuration:")
    print("=" * 50)
    for key, value in config.items():
        print(f"  {key}: {value}")
    print("=" * 50)

