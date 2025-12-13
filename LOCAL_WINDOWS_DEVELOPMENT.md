# VANI Local Windows Development Guide

## Quick Start (No Docker)

### Option 1: Automatic (Recommended)

1. **Start VANI**:
   ```cmd
   vani.bat
   ```
   This will:
   - Activate virtual environment
   - Install dependencies if needed
   - Start Flask on `localhost:5000`
   - Automatically detect and use ngrok if running

2. **Start Ngrok** (in a separate terminal):
   ```powershell
   .\scripts\start_ngrok.ps1
   ```
   Or manually:
   ```cmd
   ngrok http 5000 --domain=vani-dev.ngrok.app
   ```

### Option 2: Manual Control

1. **Start Flask**:
   ```cmd
   vani.bat
   ```

2. **Start Ngrok** (separate terminal):
   ```powershell
   .\scripts\start_ngrok.ps1 -Domain vani-dev.ngrok.app
   ```

## Setting Up Development Domain

### Step 1: Reserve Domain in Ngrok Dashboard

1. Go to: https://dashboard.ngrok.com/cloud-edge/domains
2. Click "Reserve Domain"
3. Enter: `vani-dev.ngrok.app`
4. Click "Reserve"

### Step 2: Configure Ngrok Authtoken

```cmd
ngrok config add-authtoken YOUR_AUTHTOKEN
```

Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken

### Step 3: Update Configuration

**Option A: Update `.env.local`** (Recommended):
```env
# Ngrok Configuration
NGROK_DOMAIN=vani-dev.ngrok.app
WEBHOOK_BASE_URL=https://vani-dev.ngrok.app
FLASK_PORT=5000
```

**Option B: Update `ngrok.config.json`**:
```json
{
  "ngrok": {
    "domain": "vani-dev.ngrok.app",
    "port": 5000
  },
  "webhooks": {
    "base_url": "https://vani-dev.ngrok.app"
  }
}
```

## Running VANI Locally

### Method 1: Using vani.bat (Simplest)

```cmd
# Just run:
vani.bat
```

This will:
- ✅ Check/create virtual environment
- ✅ Install dependencies
- ✅ Start Flask on port 5000
- ✅ Skip ngrok auto-start (run separately)
- ✅ Detect ngrok if already running
- ✅ Configure webhooks automatically when ngrok is detected

**Note**: `vani.bat` sets `SKIP_NGROK_AUTO_START=true` by default. To auto-start ngrok, edit `vani.bat` and change it to `false`, or set the environment variable before running.

### Method 2: Manual Python

```cmd
# Activate venv
venv\Scripts\activate.bat

# Install dependencies (first time)
pip install -r requirements.txt

# Run Flask
python run.py
```

## Starting Ngrok

### Automatic (via PowerShell Script)

```powershell
# Uses domain from .env.local or ngrok.config.json
.\scripts\start_ngrok.ps1

# Or specify domain explicitly
.\scripts\start_ngrok.ps1 -Domain vani-dev.ngrok.app
```

### Manual

```cmd
# With static domain (recommended)
ngrok http 5000 --domain=vani-dev.ngrok.app

# Without domain (random URL - webhooks need manual update)
ngrok http 5000
```

## Development vs Production

### Development Setup (Local Windows)

| Setting | Value |
|---------|-------|
| Domain | `vani-dev.ngrok.app` |
| Port | `5000` |
| Flask Host | `127.0.0.1` |
| Webhook URL | `https://vani-dev.ngrok.app` |

**Configuration**:
```env
# .env.local
NGROK_DOMAIN=vani-dev.ngrok.app
WEBHOOK_BASE_URL=https://vani-dev.ngrok.app
FLASK_PORT=5000
```

### Production Setup (VM/Docker)

| Setting | Value |
|---------|-------|
| Domain | `vani.ngrok.app` |
| Port | `5000` |
| Flask Host | `0.0.0.0` |
| Webhook URL | `https://vani.ngrok.app` |

**Configuration**:
```env
# .env.local (on VM)
NGROK_DOMAIN=vani.ngrok.app
WEBHOOK_BASE_URL=https://vani.ngrok.app
FLASK_PORT=5000
DOCKER_CONTAINER=true
```

## Workflow

### Typical Development Session

1. **Terminal 1 - Start Flask**:
   ```cmd
   vani.bat
   ```

2. **Terminal 2 - Start Ngrok**:
   ```powershell
   .\scripts\start_ngrok.ps1
   ```

3. **Access VANI**:
   - Local: http://localhost:5000
   - Public: https://vani-dev.ngrok.app (after ngrok starts)

### Webhook Configuration

Webhooks are automatically configured when:
- ✅ Ngrok is running
- ✅ `WEBHOOK_BASE_URL` is set in `.env.local`
- ✅ Flask detects ngrok URL

**Manual Webhook Update**:
```powershell
# Update Resend webhook
.\scripts\configure_webhooks.ps1

# Or via Python
python scripts\configure_webhooks.py
```

## Troubleshooting

### Ngrok Not Starting

**Error**: `ngrok not found in PATH`
- **Solution**: Install ngrok and add to PATH
  - Download: https://ngrok.com/download
  - Or: `choco install ngrok`

**Error**: `authtoken not configured`
- **Solution**: 
  ```cmd
  ngrok config add-authtoken YOUR_TOKEN
  ```

**Error**: `domain not found` or `domain already in use`
- **Solution**: 
  1. Reserve domain in ngrok dashboard
  2. Wait 1-2 minutes for propagation
  3. Verify: `ngrok config check`

### Flask Not Accessible

**Error**: `Flask app not responding on port 5000`
- **Solution**: 
  1. Check Flask is running: `netstat -ano | findstr :5000`
  2. Check firewall allows port 5000
  3. Verify Flask started successfully (check vani.bat output)

### Webhooks Not Working

**Issue**: Webhooks not receiving events
- **Solution**:
  1. Verify ngrok URL: Check `ngrok-url.txt` or http://localhost:4040
  2. Update webhook URLs in external services:
     - Resend: https://dashboard.resend.com/webhooks
     - Twilio: https://console.twilio.com/...
     - Cal.com: https://app.cal.com/settings/developer/webhooks
  3. Run webhook configuration script:
     ```powershell
     .\scripts\configure_webhooks.ps1
     ```

## Environment Variables

### Required for Local Development

```env
# .env.local
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key

# Ngrok (Development)
NGROK_DOMAIN=vani-dev.ngrok.app
WEBHOOK_BASE_URL=https://vani-dev.ngrok.app
FLASK_PORT=5000

# Ngrok Auto-Start (optional)
# Set to 'false' to auto-start ngrok, 'true' to skip (default in vani.bat)
SKIP_NGROK_AUTO_START=true

# Optional
RESEND_API_KEY=your_resend_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
CAL_COM_API_KEY=your_cal_com_key
```

## Quick Reference

| Command | Description |
|--------|-------------|
| `vani.bat` | Start VANI Flask app |
| `.\scripts\start_ngrok.ps1` | Start ngrok tunnel |
| `ngrok http 5000 --domain=vani-dev.ngrok.app` | Manual ngrok start |
| `http://localhost:4040` | Ngrok dashboard |
| `http://localhost:5000` | VANI local URL |
| `https://vani-dev.ngrok.app` | VANI public URL (dev) |

## Notes

- **No Docker Required**: This setup runs Flask directly on Windows
- **Separate Domains**: Use `vani-dev.ngrok.app` for local dev, `vani.ngrok.app` for production
- **Auto-Configuration**: `run.py` automatically detects ngrok and configures webhooks
- **Port Conflicts**: If port 5000 is in use, change `FLASK_PORT` in `.env.local`

