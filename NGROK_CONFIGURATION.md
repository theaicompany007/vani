# Ngrok Configuration Guide

## Overview

Ngrok configuration is loaded from multiple sources in priority order:

1. **`.env.local`** (highest priority)
2. **`ngrok.yml`** (if available, reads tunnel configs)
3. **`ngrok.config.json`** (fallback)
4. **Environment variables**
5. **Defaults**

## Configuration Files

### 1. `.env.local` (Primary)

Set these variables in `.env.local`:

```env
WEBHOOK_BASE_URL=https://vani.ngrok.app
FLASK_PORT=5000
NGROK_DOMAIN=vani.ngrok.app  # Optional, extracted from WEBHOOK_BASE_URL if not set
```

### 2. `ngrok.config.json` (Fallback)

Created at project root. Used if `.env.local` doesn't have ngrok settings:

```json
{
  "ngrok": {
    "domain": "vani.ngrok.app",
    "port": 5000,
    "protocol": "http"
  },
  "webhooks": {
    "base_url": "https://vani.ngrok.app",
    "resend": "https://vani.ngrok.app/api/webhooks/resend",
    "twilio": "https://vani.ngrok.app/api/webhooks/twilio",
    "cal_com": "https://vani.ngrok.app/api/webhooks/cal-com"
  }
}
```

### 3. `ngrok.yml` (System Config)

Your system ngrok config at:
- Windows: `%APPDATA%\ngrok\ngrok.yml` or `%USERPROFILE%\.ngrok2\ngrok.yml`

If you have a tunnel named `vani` configured:

```yaml
version: "2"
region: us
tunnels:
  vani:
    proto: http
    addr: 5000
    domain: vani.ngrok.app
```

The scripts will automatically use this if found.

## Using Your Existing Ngrok Setup

Since ngrok is already configured on your machine:

### Option 1: Use ngrok.yml Tunnel

If you have a `vani` tunnel in your `ngrok.yml`:

```powershell
# Script will automatically detect and use it
.\scripts\start_ngrok.ps1
```

Or manually:
```powershell
ngrok start vani
```

### Option 2: Use Static Domain

If you have `vani.ngrok.app` configured:

```powershell
# Script will extract domain from WEBHOOK_BASE_URL
.\scripts\start_ngrok.ps1
```

Or manually:
```powershell
ngrok http 5000 --domain=vani.ngrok.app
```

### Option 3: Update ngrok.config.json

Edit `ngrok.config.json` with your actual ngrok settings, and scripts will use it as fallback.

## Scripts That Use Ngrok Config

### Python Scripts

All Python scripts use `load_ngrok_config.py`:

```python
from scripts.load_ngrok_config import get_ngrok_config

config = get_ngrok_config()
webhook_url = config['webhook_base_url']
```

### PowerShell Scripts

`start_ngrok.ps1` loads from:
1. `.env.local` (WEBHOOK_BASE_URL, FLASK_PORT, NGROK_DOMAIN)
2. `ngrok.config.json` (as fallback)
3. Checks `ngrok.yml` for `vani` tunnel

## Testing Configuration

```powershell
# Test config loading
python scripts\load_ngrok_config.py

# Test ngrok.yml reading (if PyYAML installed)
python scripts\read_ngrok_yml.py

# Start ngrok (will use best available config)
.\scripts\start_ngrok.ps1
```

## Priority Order Summary

1. **`.env.local`** → `WEBHOOK_BASE_URL`, `FLASK_PORT`, `NGROK_DOMAIN`
2. **`ngrok.yml`** → Tunnel named `vani` or tunnel with `vani.ngrok.app` domain
3. **`ngrok.config.json`** → Fallback values
4. **Environment variables** → System env vars
5. **Defaults** → Hardcoded fallbacks

## Notes

- Scripts automatically detect and use your existing ngrok setup
- If `vani` tunnel exists in `ngrok.yml`, it will be used automatically
- `ngrok.config.json` is a project-specific fallback
- All scripts update `.env.local` with actual ngrok URL when tunnel starts
- PyYAML is optional - scripts work without it (just can't read ngrok.yml)

