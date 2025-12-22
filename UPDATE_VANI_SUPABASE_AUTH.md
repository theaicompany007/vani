# Update VANI Supabase Auth Configuration

## Overview

VANI's Supabase Auth configuration needs to be updated when moving from development (`vani-dev.ngrok.app`) to production (`vani.ngrok.app`).

## Current Configuration (Development)

- **Site URL**: `https://vani-dev.ngrok.app`
- **Redirect URLs**: 
  - `http://localhost:5000`
  - `http://localhost:5000/command-center`
  - `http://localhost:5000/login`
  - `https://vani-dev.ngrok.app`
  - `https://vani-dev.ngrok.app/api/auth/callback`
  - `https://vani-dev.ngrok.app/command-center`
  - `https://vani-dev.ngrok.app/login`

## Target Configuration (Production)

- **Site URL**: `https://vani.ngrok.app`
- **Redirect URLs**: 
  - `http://localhost:5000`
  - `http://localhost:5000/command-center`
  - `http://localhost:5000/login`
  - `https://vani.ngrok.app`
  - `https://vani.ngrok.app/api/auth/callback`
  - `https://vani.ngrok.app/command-center`
  - `https://vani.ngrok.app/login`

## Method 1: Using the Audit Script (Recommended)

### Prerequisites

1. Ensure `WEBHOOK_BASE_URL=https://vani.ngrok.app` in VANI's `.env.local`
2. Ensure `SUPABASE_ACCESS_TOKEN` is set in VANI's `.env.local`
   - Get token from: https://supabase.com/dashboard/account/tokens
   - Format: `SUPABASE_ACCESS_TOKEN=sbp_your_token_here`

### Update Command

```bash
cd /home/postgres/vani
python3 vani-env-audit.py --update-auth-config
```

This will:
- Read `WEBHOOK_BASE_URL` from `.env.local`
- Update Site URL to `https://vani.ngrok.app`
- Update all Redirect URLs (replacing `vani-dev.ngrok.app` with `vani.ngrok.app`)

### Override Webhook URL

If you want to use a different URL temporarily:

```bash
python3 vani-env-audit.py --update-auth-config --webhook-base-url https://vani.ngrok.app
```

## Method 2: Using the Dedicated Script

```bash
cd /home/postgres/vani
python3 update-vani-supabase-auth.py
```

Or with explicit URL:

```bash
python3 update-vani-supabase-auth.py --webhook-base-url https://vani.ngrok.app
```

## Method 3: Manual Update

1. Go to Supabase Dashboard:
   ```
   https://supabase.com/dashboard/project/[YOUR_PROJECT_REF]/auth/url-configuration
   ```

2. Update **Site URL** to: `https://vani.ngrok.app`

3. Update **Redirect URLs** to:
   ```
   http://localhost:5000
   http://localhost:5000/command-center
   http://localhost:5000/login
   https://vani.ngrok.app
   https://vani.ngrok.app/api/auth/callback
   https://vani.ngrok.app/command-center
   https://vani.ngrok.app/login
   ```

4. Click **Save**

## Verification

After updating, test the authentication:

```bash
# Test login endpoint
curl -I https://vani.ngrok.app/login

# Check if redirect works
# Try logging in via the web interface
```

## Troubleshooting

### Error: SUPABASE_ACCESS_TOKEN not found

1. Get your Personal Access Token:
   - Go to: https://supabase.com/dashboard/account/tokens
   - Click "Generate new token"
   - Copy the token (starts with `sbp_`)

2. Add to VANI's `.env.local`:
   ```bash
   SUPABASE_ACCESS_TOKEN=sbp_your_token_here
   ```

### Error: WEBHOOK_BASE_URL not found

1. Update VANI's `.env.local`:
   ```bash
   WEBHOOK_BASE_URL=https://vani.ngrok.app
   ```

2. Or use `--webhook-base-url` flag:
   ```bash
   python3 vani-env-audit.py --update-auth-config --webhook-base-url https://vani.ngrok.app
   ```

### HTTP 401 or 403 Error

- Verify your `SUPABASE_ACCESS_TOKEN` is valid
- Ensure the token has permissions to update project configuration
- Check if the token has expired

### URLs Not Updating

- Check that `WEBHOOK_BASE_URL` in `.env.local` matches what you want
- Verify the script output shows the correct URLs
- Try manual update as a fallback

## Notes

- **Localhost URLs are preserved** - The script always includes localhost URLs for development
- **No container restart needed** - Auth config changes take effect immediately
- **Backup first** - Consider noting current URLs before updating


