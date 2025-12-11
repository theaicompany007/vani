# Setup Scripts Documentation

## Overview

Three Python scripts are provided to automate the setup process:

1. **`create_database_tables_direct.py`** - Creates database tables
2. **`configure_webhooks.py`** - Configures webhooks for Resend, Twilio, and Cal.com
3. **`setup_complete.py`** - Runs both scripts in sequence

## Usage

### Option 1: Run Complete Setup (Recommended)

```powershell
.\venv\Scripts\Activate.ps1
python scripts\setup_complete.py
```

This will:
- Create all database tables
- Configure webhooks for all services

### Option 2: Run Individually

#### Create Database Tables

```powershell
python scripts\create_database_tables_direct.py
```

**What it does:**
- Connects to Supabase using `SUPABASE_CONNECTION` from `.env.local`
- Executes SQL migration from `app/migrations/001_create_tables.sql`
- Creates tables, indexes, and triggers
- Verifies creation

**Requirements:**
- `SUPABASE_CONNECTION` or (`SUPABASE_URL` + `SUPABASE_DB_PASSWORD`) in `.env.local`

#### Configure Webhooks

```powershell
python scripts\configure_webhooks.py
```

**What it does:**
- **Resend**: Creates/updates webhook with events (email.sent, email.delivered, email.opened, email.clicked, email.bounced)
- **Twilio**: Updates phone number status callback URL
- **Cal.com**: Creates/updates webhook with events (BOOKING_CREATED, BOOKING_CANCELLED, BOOKING_RESCHEDULED)

**Requirements:**
- `RESEND_API_KEY` in `.env.local`
- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` in `.env.local`
- `CAL_COM_API_KEY` in `.env.local`
- `WEBHOOK_BASE_URL` in `.env.local` (default: https://vani.ngrok.app)

## Troubleshooting

### Database Connection Issues

**Error**: `password authentication failed`
- **Solution**: Check `SUPABASE_CONNECTION` or `SUPABASE_DB_PASSWORD` in `.env.local`
- Verify the password is correct in Supabase Dashboard → Settings → Database

**Error**: `relation already exists`
- **Solution**: This is OK! Tables already exist. The script will verify and continue.

### Resend Webhook Issues

**Error**: `API key is invalid`
- **Solution**: 
  1. Check `RESEND_API_KEY` in `.env.local`
  2. Verify key at https://resend.com/api-keys
  3. Ensure key has webhook permissions

**Error**: `Webhook creation failed`
- **Solution**: 
  1. Verify `WEBHOOK_BASE_URL` is accessible (ngrok tunnel must be running)
  2. Check Resend dashboard for existing webhooks
  3. Manually configure at https://resend.com/webhooks

### Twilio Webhook Issues

**Error**: `Phone number not found`
- **Solution**:
  1. Check `TWILIO_WHATSAPP_NUMBER` or `TWILIO_PHONE_NUMBER` in `.env.local`
  2. Run script to see available numbers
  3. Update `.env.local` with correct number
  4. Or configure manually in Twilio Console → Phone Numbers

**Error**: `Authentication failed`
- **Solution**: Verify `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` in `.env.local`

### Cal.com Webhook Issues

**Error**: `No apiKey provided`
- **Solution**:
  1. Check `CAL_COM_API_KEY` format (should start with `cal_`)
  2. Verify key at https://cal.com/settings/developer/api-keys
  3. Cal.com v2 API may require different authentication

**Error**: `Webhook creation failed`
- **Solution**:
  1. Verify `WEBHOOK_BASE_URL` is accessible
  2. Check `CAL_COM_WEBHOOK_SECRET_PROD` is set
  3. Manually configure at https://cal.com/settings/developer/webhooks

## Manual Configuration

If scripts fail, you can configure webhooks manually:

### Resend
1. Go to: https://resend.com/webhooks
2. Click "Add Webhook"
3. URL: `https://vani.ngrok.app/api/webhooks/resend`
4. Events: email.sent, email.delivered, email.opened, email.clicked, email.bounced
5. Save

### Twilio
1. Go to: https://console.twilio.com/ → Phone Numbers
2. Select your WhatsApp number
3. Set Status Callback URL: `https://vani.ngrok.app/api/webhooks/twilio`
4. Save

### Cal.com
1. Go to: https://cal.com/settings/developer/webhooks
2. Click "Add Webhook"
3. URL: `https://vani.ngrok.app/api/webhooks/cal-com`
4. Events: BOOKING_CREATED, BOOKING_CANCELLED, BOOKING_RESCHEDULED
5. Secret: Use value from `CAL_COM_WEBHOOK_SECRET_PROD`
6. Save

## Next Steps

After successful setup:

1. **Seed Targets**:
   ```powershell
   python scripts/seed_targets.py
   ```

2. **Start Application**:
   ```powershell
   python run.py
   ```

3. **Access Command Center**:
   - Open: http://localhost:5000/command-center

## Notes

- All scripts read from `.env.local` (takes priority over `.env`)
- Scripts are idempotent (safe to run multiple times)
- Webhook URLs must be publicly accessible (use ngrok for local dev)
- Database connection uses `SUPABASE_CONNECTION` if available, otherwise builds from components

