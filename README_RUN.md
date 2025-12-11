# Running VANI Application

## Quick Start

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the application
python run.py
```

That's it! The `run.py` script will:
1. ✅ Check all environment variables from `.env.local`
2. ✅ Verify database connection
3. ✅ Check ngrok tunnel status
4. ✅ Start Flask server and display URLs

## What You'll See

```
======================================================================
  VANI OUTREACH COMMAND CENTER - STARTUP
======================================================================

[1/4] Checking environment variables...
  [OK] SUPABASE_URL              = https://...e.co
  [OK] SUPABASE_KEY              = eyJhbGci...2w40
  [OK] SUPABASE_SERVICE_KEY      = eyJhbGci...0SMs
  [OK] RESEND_API_KEY            = re_R36EL...X5xV
  [OK] TWILIO_ACCOUNT_SID        = AC5c3e76...582f
  [OK] TWILIO_AUTH_TOKEN         = e321065c...c1f1
  [OK] OPENAI_API_KEY            = sk-proj-...Li4A
[OK] All required environment variables are set

[2/4] Checking database connection...
  [OK] Database connected - Tables accessible

[3/4] Checking ngrok tunnel...
  [OK] Ngrok tunnel active: https://vani.ngrok.app

[4/4] Starting Flask application...

======================================================================
  FLASK SERVER STARTING
======================================================================

Local URL:        http://127.0.0.1:5000
Command Center:   http://127.0.0.1:5000/command-center

----------------------------------------------------------------------
PUBLIC URL (Ngrok): https://vani.ngrok.app
Command Center:     https://vani.ngrok.app/command-center

Webhook Endpoints:
  Resend:    https://vani.ngrok.app/api/webhooks/resend
  Twilio:    https://vani.ngrok.app/api/webhooks/twilio
  Cal.com:   https://vani.ngrok.app/api/webhooks/cal-com
----------------------------------------------------------------------

[OK] Flask server starting...
Press Ctrl+C to stop the server
```

## Prerequisites

1. **Virtual Environment**: Activated (`.\venv\Scripts\Activate.ps1`)
2. **Environment Variables**: All set in `.env.local`
3. **Database**: Tables created (run `python scripts/create_database_tables_direct.py` if needed)
4. **Ngrok** (Optional): For webhooks - start with `.\scripts\start_ngrok.ps1`

## Troubleshooting

### Missing Environment Variables
- Check `.env.local` exists and has all required keys
- Run: `python scripts/check_env_config.py`

### Database Connection Failed
- Verify `SUPABASE_CONNECTION` or `SUPABASE_DB_PASSWORD` in `.env.local`
- Run: `python scripts/create_database_tables_direct.py`

### Ngrok Not Running
- Start ngrok: `.\scripts\start_ngrok.ps1`
- Or configure manually in ngrok dashboard
- Webhooks won't work, but app will still run

### Port Already in Use
- Change `FLASK_PORT` in `.env.local`
- Or stop the process using port 5000

## Access Points

Once running:
- **Local**: http://127.0.0.1:5000/command-center
- **Public** (if ngrok running): https://vani.ngrok.app/command-center

## Stopping the Server

Press `Ctrl+C` in the terminal running `python run.py`

