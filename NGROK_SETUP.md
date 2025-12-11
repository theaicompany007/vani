# Ngrok Setup for VANI Project

## Overview

Ngrok creates a public HTTPS tunnel to your local Flask app (port 5000) so that webhooks from Resend, Twilio, and Cal.com can reach your application.

**Required URL**: `https://vani.ngrok.app` (static domain) or random ngrok URL

## Quick Setup

### 1. Install Ngrok

**Option A: Download**
1. Go to: https://ngrok.com/download
2. Download Windows version
3. Extract `ngrok.exe` to a folder in your PATH (e.g., `C:\Program Files\ngrok\`)

**Option B: Chocolatey**
```powershell
choco install ngrok
```

### 2. Sign Up & Get Authtoken

1. Sign up at: https://dashboard.ngrok.com/signup
2. Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
3. Configure ngrok:
   ```powershell
   ngrok config add-authtoken YOUR_TOKEN
   ```

### 3. Configure Static Domain (Optional but Recommended)

For `vani.ngrok.app` to work:

1. Go to: https://dashboard.ngrok.com/cloud-edge/domains
2. Reserve domain: `vani.ngrok.app`
3. Add to ngrok config file (`%USERPROFILE%\.ngrok2\ngrok.yml`):
   ```yaml
   version: "2"
   authtoken: YOUR_TOKEN
   tunnels:
     vani:
       proto: http
       addr: 5000
       domain: vani.ngrok.app
   ```

### 4. Run Setup Script

```powershell
.\scripts\setup_ngrok.ps1
```

This will verify ngrok installation and configuration.

## Starting Ngrok

### Option 1: Use Script (Recommended)

```powershell
# Start ngrok tunnel
.\scripts\start_ngrok.ps1
```

This will:
- ✅ Check if Flask is running
- ✅ Start ngrok tunnel
- ✅ Update `.env.local` with ngrok URL
- ✅ Display webhook endpoints
- ✅ Monitor and auto-restart if needed

### Option 2: Manual Start

**With static domain:**
```powershell
ngrok http 5000 --domain=vani.ngrok.app
```

**Without static domain (random URL):**
```powershell
ngrok http 5000
```

Then manually update `WEBHOOK_BASE_URL` in `.env.local` with the ngrok URL.

## Verification

1. **Check ngrok is running:**
   ```powershell
   Get-Process ngrok
   ```

2. **View ngrok dashboard:**
   - Open: http://localhost:4040
   - See tunnel status and requests

3. **Test webhook endpoint:**
   ```powershell
   $url = Get-Content ngrok-url.txt
   Invoke-WebRequest "$url/api/health" -UseBasicParsing
   ```

## Webhook URLs

Once ngrok is running, your webhook URLs will be:

- **Resend**: `https://vani.ngrok.app/api/webhooks/resend`
- **Twilio**: `https://vani.ngrok.app/api/webhooks/twilio`
- **Cal.com**: `https://vani.ngrok.app/api/webhooks/cal-com`

## Troubleshooting

### Ngrok Not Starting

**Error**: `ngrok: command not found`
- **Solution**: Add ngrok to PATH or use full path

**Error**: `authtoken not configured`
- **Solution**: Run `ngrok config add-authtoken YOUR_TOKEN`

**Error**: `domain not found`
- **Solution**: Reserve domain in ngrok dashboard first

### Flask Not Accessible

**Error**: `502 Bad Gateway`
- **Solution**: Make sure Flask is running on port 5000
- **Check**: `python run.py` in another terminal

### URL Mismatch

**Issue**: `.env.local` has different URL than ngrok
- **Solution**: Run `.\scripts\start_ngrok.ps1` to auto-update

## Running in Production

For production, you should:
1. Use a static domain (already configured: `vani.ngrok.app`)
2. Set up ngrok as a service (auto-start on boot)
3. Monitor ngrok status
4. Use ngrok's paid plan for better reliability

## Notes

- Keep ngrok running while developing/testing webhooks
- Ngrok free tier has connection limits
- Static domains require ngrok paid plan
- Ngrok dashboard shows all requests for debugging

## Quick Reference

```powershell
# Setup
.\scripts\setup_ngrok.ps1

# Start
.\scripts\start_ngrok.ps1

# Stop
Get-Process ngrok | Stop-Process

# Check status
Invoke-RestMethod http://localhost:4040/api/tunnels
```

