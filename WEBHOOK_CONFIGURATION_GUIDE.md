# Webhook Configuration Guide

This guide explains how to configure webhooks for VANI in both development and production environments.

## Overview

VANI uses environment-aware webhook configuration to prevent dev environments from overwriting production webhooks. The system automatically detects the environment and only updates webhooks if it's safe to do so.

## Environment Detection

The system detects the environment in this order:
1. **`VANI_ENVIRONMENT`** environment variable (`dev` or `prod`)
2. **URL detection** from `WEBHOOK_BASE_URL` or `NGROK_DOMAIN`:
   - `vani-dev.ngrok.app` → **dev**
   - `vani.ngrok.app` → **prod**

## Configuration Methods

### Method 1: Automatic (via run.py)

When you start VANI with `run.py`, webhooks are automatically configured if:
- `SKIP_WEBHOOK_UPDATE` is not set to `true`
- Environment is detected correctly

**For Development:**
```bash
# Set in .env.local
VANI_ENVIRONMENT=dev
NGROK_DOMAIN=vani-dev.ngrok.app
WEBHOOK_BASE_URL=https://vani-dev.ngrok.app
SKIP_WEBHOOK_UPDATE=false
```

**For Production:**
```bash
# Set in .env (on VM)
VANI_ENVIRONMENT=prod
NGROK_DOMAIN=vani.ngrok.app
WEBHOOK_BASE_URL=https://vani.ngrok.app
SKIP_WEBHOOK_UPDATE=false
```

### Method 2: Manual Script Execution

Run the webhook configuration script directly:

#### For Development Environment

```bash
# Option 1: Set environment variable
set VANI_ENVIRONMENT=dev
set WEBHOOK_BASE_URL=https://vani-dev.ngrok.app
python scripts/configure_webhooks.py

# Option 2: Set in .env.local first, then run
python scripts/configure_webhooks.py
```

#### For Production Environment

```bash
# Option 1: Set environment variable
set VANI_ENVIRONMENT=prod
set WEBHOOK_BASE_URL=https://vani.ngrok.app
python scripts/configure_webhooks.py

# Option 2: Set in .env first, then run
python scripts/configure_webhooks.py
```

### Method 3: Configure Individual Services

You can also configure webhooks for specific services:

```bash
# Configure all webhooks
python scripts/configure_webhooks.py

# Configure Supabase OAuth separately
python scripts/configure_supabase_oauth.py --url https://vani.ngrok.app
```

## Environment Variables

### Required Variables

- **`WEBHOOK_BASE_URL`**: Base URL for webhooks (e.g., `https://vani.ngrok.app`)
- **`VANI_ENVIRONMENT`**: Environment type (`dev` or `prod`)

### Optional Variables

- **`SKIP_WEBHOOK_UPDATE`**: Set to `true` to skip all webhook updates (useful for manual management)
- **`NGROK_DOMAIN`**: Ngrok domain (used for auto-detection)

### Service-Specific Variables

**Resend (Email):**
- `RESEND_API_KEY`: Resend API key

**Twilio (WhatsApp/SMS):**
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_WHATSAPP_NUMBER`: WhatsApp number (or `TWILIO_SANDBOX_WHATSAPP_NUMBER`)

**Cal.com (Meetings):**
- `CAL_COM_API_KEY`: Cal.com API key
- `CAL_COM_WEBHOOK_SECRET`: Webhook secret

**Supabase OAuth:**
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ACCESS_TOKEN`: Personal access token (for automatic updates)

## Safety Features

### Environment Protection

The system prevents accidental overwrites:

1. **Checks current webhook URLs** before updating
2. **Compares environments** - won't update if current URL is for different environment
3. **Logs warnings** when skipping updates due to environment mismatch

### Example Safety Behavior

**Scenario:** Dev environment trying to update webhooks

```
Current webhook URL: https://vani.ngrok.app/api/webhooks/resend (PROD)
Target webhook URL:  https://vani-dev.ngrok.app/api/webhooks/resend (DEV)

Result: ⚠️ Skipping update (environment mismatch)
```

**Scenario:** Prod environment updating prod webhooks

```
Current webhook URL: https://vani.ngrok.app/api/webhooks/resend (PROD)
Target webhook URL:  https://vani.ngrok.app/api/webhooks/resend (PROD)

Result: ✅ Update successful (same environment)
```

## Step-by-Step Setup

### Development Setup

1. **Set environment variables in `.env.local`:**
   ```bash
   VANI_ENVIRONMENT=dev
   NGROK_DOMAIN=vani-dev.ngrok.app
   WEBHOOK_BASE_URL=https://vani-dev.ngrok.app
   SKIP_WEBHOOK_UPDATE=false
   
   # Add your service API keys
   RESEND_API_KEY=re_...
   TWILIO_ACCOUNT_SID=AC...
   CAL_COM_API_KEY=cal_...
   ```

2. **Start ngrok for dev:**
   ```bash
   # Make sure ngrok is running with vani-dev.ngrok.app domain
   start-ngrok.bat
   ```

3. **Run webhook configuration:**
   ```bash
   python scripts/configure_webhooks.py
   ```

4. **Or start VANI (auto-configures):**
   ```bash
   vani.bat
   ```

### Production Setup

1. **Set environment variables in `.env` (on VM):**
   ```bash
   VANI_ENVIRONMENT=prod
   NGROK_DOMAIN=vani.ngrok.app
   WEBHOOK_BASE_URL=https://vani.ngrok.app
   SKIP_WEBHOOK_UPDATE=false
   
   # Add your service API keys
   RESEND_API_KEY=re_...
   TWILIO_ACCOUNT_SID=AC...
   CAL_COM_API_KEY=cal_...
   ```

2. **Ensure ngrok is running with vani.ngrok.app domain**

3. **Run webhook configuration:**
   ```bash
   python scripts/configure_webhooks.py
   ```

4. **Or restart VANI container (auto-configures):**
   ```bash
   docker-compose restart vani
   ```

## Verifying Configuration

After running the configuration script, you should see:

```
======================================================================
  WEBHOOK CONFIGURATION
======================================================================
Base URL: https://vani.ngrok.app

Environment: PROD

======================================================================
  CONFIGURING RESEND WEBHOOK
======================================================================
✅ Webhook URL updated successfully

======================================================================
  CONFIGURING TWILIO WEBHOOK
======================================================================
✅ Status callback URL updated successfully!

======================================================================
  CONFIGURING CAL.COM WEBHOOK
======================================================================
✅ Webhook URL updated successfully

======================================================================
  SUMMARY
======================================================================
✅ RESEND          - updated
✅ TWILIO          - updated
✅ CAL_COM         - updated

✅ Configured: 3/3 services
```

## Troubleshooting

### Webhook Updates Skipped

If you see warnings about environment mismatch:

```
⚠️  Skipping Resend webhook update (environment mismatch)
   Current URL (https://vani.ngrok.app/...) is for different environment
   Target URL (https://vani-dev.ngrok.app/...) would overwrite production webhook
```

**Solution:**
1. Verify `VANI_ENVIRONMENT` is set correctly
2. Check `WEBHOOK_BASE_URL` matches your intended environment
3. If you need to force update, manually configure in service dashboard

### Skip All Updates

To prevent any automatic webhook updates:

```bash
set SKIP_WEBHOOK_UPDATE=true
```

This is useful when:
- Managing webhooks manually
- Testing without affecting production
- Running in Docker where webhooks are managed externally

### Manual Configuration

If automatic configuration fails, you can configure webhooks manually:

**Resend:**
- Dashboard: https://resend.com/webhooks
- Add webhook URL: `https://vani.ngrok.app/api/webhooks/resend`

**Twilio:**
- Dashboard: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
- Set Status Callback URL: `https://vani.ngrok.app/api/webhooks/twilio`

**Cal.com:**
- Dashboard: https://app.cal.com/settings/platform/webhooks
- Add webhook URL: `https://vani.ngrok.app/api/webhooks/cal-com`

**Supabase OAuth:**
- Dashboard: https://supabase.com/dashboard/project/[PROJECT]/auth/url-configuration
- Add redirect URLs manually

## Quick Reference

### Development
```bash
# .env.local
VANI_ENVIRONMENT=dev
WEBHOOK_BASE_URL=https://vani-dev.ngrok.app

# Run
python scripts/configure_webhooks.py
```

### Production
```bash
# .env
VANI_ENVIRONMENT=prod
WEBHOOK_BASE_URL=https://vani.ngrok.app

# Run
python scripts/configure_webhooks.py
```

### Skip Updates
```bash
# .env.local or .env
SKIP_WEBHOOK_UPDATE=true
```

## Notes

- Webhook configuration runs automatically when starting VANI via `run.py`
- Environment detection is automatic based on URL patterns
- Safety checks prevent accidental production overwrites
- Manual configuration is always available as fallback







