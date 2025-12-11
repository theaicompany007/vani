"""Read ngrok.yml configuration file"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def find_ngrok_config() -> Optional[Path]:
    """Find ngrok.yml configuration file"""
    # Common locations
    locations = [
        Path.home() / '.ngrok2' / 'ngrok.yml',
        Path(os.getenv('APPDATA', '')) / 'ngrok' / 'ngrok.yml',
        Path(os.getenv('LOCALAPPDATA', '')) / 'ngrok' / 'ngrok.yml',
        Path.home() / '.config' / 'ngrok' / 'ngrok.yml',
    ]
    
    for loc in locations:
        if loc.exists():
            return loc
    
    return None


def read_ngrok_tunnels() -> Dict[str, Any]:
    """
    Read ngrok.yml and extract tunnel configurations
    
    Returns:
        Dict with tunnel configurations
    """
    config_path = find_ngrok_config()
    
    if not config_path:
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        tunnels = {}
        if 'tunnels' in config:
            for name, tunnel_config in config['tunnels'].items():
                tunnels[name] = tunnel_config
        
        return {
            'config_path': str(config_path),
            'tunnels': tunnels,
            'full_config': config
        }
    except Exception as e:
        print(f"⚠️  Could not read ngrok.yml: {e}")
        return {}


def get_vani_tunnel_config() -> Optional[Dict[str, Any]]:
    """Get VANI tunnel configuration from ngrok.yml"""
    ngrok_data = read_ngrok_tunnels()
    
    # Look for 'vani' tunnel
    if 'tunnels' in ngrok_data:
        if 'vani' in ngrok_data['tunnels']:
            return ngrok_data['tunnels']['vani']
        
        # Also check for any tunnel with vani.ngrok.app domain
        for name, tunnel in ngrok_data['tunnels'].items():
            if tunnel.get('domain') == 'vani.ngrok.app':
                return tunnel
    
    return None


if __name__ == '__main__':
    # Test reading
    config_path = find_ngrok_config()
    if config_path:
        print(f"✅ Found ngrok.yml at: {config_path}")
        tunnels = read_ngrok_tunnels()
        if tunnels:
            print(f"\nFound {len(tunnels.get('tunnels', {}))} tunnel(s):")
            for name, tunnel in tunnels.get('tunnels', {}).items():
                print(f"  - {name}: {tunnel}")
            
            vani_tunnel = get_vani_tunnel_config()
            if vani_tunnel:
                print(f"\n✅ VANI tunnel found:")
                print(f"   Domain: {vani_tunnel.get('domain')}")
                print(f"   Port: {vani_tunnel.get('addr')}")
            else:
                print("\n⚠️  VANI tunnel not found in ngrok.yml")
        else:
            print("⚠️  No tunnels found in ngrok.yml")
    else:
        print("❌ ngrok.yml not found")

