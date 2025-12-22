# VANI Environment Variable Audit Script

## Overview

`vani-env-audit.py` is a comprehensive script that:
1. ✅ **Audits** all required and optional environment variables for VANI
2. ✅ **Validates** Supabase URL format and tests connection
3. ✅ **Updates** Supabase configuration if needed
4. ✅ **Provides** a clear setup checklist

## Usage

### Basic Audit (Check Current Configuration)

```bash
# On VM, from VANI directory
cd /home/postgres/vani
python3 vani-env-audit.py

# Or specify custom .env.local path
python3 vani-env-audit.py --env-file /path/to/.env.local
```

### Update Supabase Configuration

```bash
python3 vani-env-audit.py \
  --update-supabase \
  --supabase-url "https://your-project.supabase.co" \
  --supabase-key "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  --supabase-service-key "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Run from Docker Container

```bash
# Copy script to container
docker cp vani-env-audit.py vani:/app/

# Run inside container
docker exec -it vani python3 /app/vani-env-audit.py
```

## Required Variables

The script checks for these **required** variables:

1. **FLASK_ENV** - Flask environment (production/development)
2. **SECRET_KEY** - Flask secret key for sessions
3. **SUPABASE_URL** - Supabase project URL
4. **SUPABASE_KEY** - Supabase anon key (JWT)
5. **SUPABASE_SERVICE_ROLE_KEY** - Supabase service role key
6. **OPENAI_API_KEY** - OpenAI API key
7. **WEBHOOK_BASE_URL** - Base URL for webhooks

## Optional Variables

The script also checks for these **optional** variables:

- **Email**: `RESEND_API_KEY`, `RESEND_DOMAIN_ID`, `USE_RESEND`
- **WhatsApp**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`
- **RAG**: `RAG_SERVICE_URL`, `RAG_API_KEY`, `RAG_ONLY`
- **Redis**: `REDIS_HOST`, `REDIS_PORT`
- **Cal.com**: `CAL_COM_API_KEY`
- **Environment**: `VANI_ENVIRONMENT`, `NGROK_DOMAIN`, `SKIP_WEBHOOK_UPDATE`

## Output Example

```
======================================================================
VANI Environment Variable Audit
======================================================================

Environment file: /home/postgres/vani/.env.local

✓ Loaded 25 environment variables

======================================================================
Required Variables
======================================================================

  ✓ SET FLASK_ENV
      Flask environment (production/development)
      Value: production

  ✓ SET SUPABASE_URL
      Supabase project URL (e.g., https://xxx.supabase.co)
      Value: https://xxx.supabase.co

  ✗ MISSING SECRET_KEY
      Flask secret key for sessions

======================================================================
Supabase Validation
======================================================================

✓ Supabase URL format is valid
  URL: https://xxx.supabase.co

Testing Supabase connection...
✓ Connection successful (HTTP 200)

✓ SUPABASE_KEY is set
  Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

======================================================================
Setup Checklist
======================================================================

  ✓ All required variables set
  ✓ Supabase URL valid
  ✓ Supabase connection working
  ✓ Webhook base URL set
  ✓ OpenAI API key set

✅ VANI is ready to use!
```

## Features

### 1. Environment Variable Detection
- Reads `.env.local` file
- Identifies missing required variables
- Shows optional variables status

### 2. Supabase Validation
- Validates URL format (must be `https://*.supabase.co`)
- Tests actual connection using REST API
- Verifies keys are set

### 3. Supabase Update
- Updates `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`
- Preserves other environment variables
- Validates new URL before updating

### 4. Security
- Masks sensitive values (keys, tokens, passwords) in output
- Only shows first 10 and last 4 characters

## Integration with Setup

After updating Supabase configuration:

```bash
# 1. Run audit
python3 vani-env-audit.py --update-supabase \
  --supabase-url "https://new-project.supabase.co" \
  --supabase-key "new-key" \
  --supabase-service-key "new-service-key"

# 2. Restart VANI container
docker compose -f docker-compose.worker.yml restart vani

# 3. Verify
docker logs vani --tail 50
curl http://localhost:5000/api/health
```

## Troubleshooting

### Script can't find VANI directory
```bash
# Specify env file explicitly
python3 vani-env-audit.py --env-file /home/postgres/vani/.env.local
```

### Supabase connection test fails
- Check if Supabase URL is correct
- Verify API key is valid
- Ensure network connectivity
- Check Supabase project status

### Permission denied
```bash
chmod +x vani-env-audit.py
```

## Next Steps

1. Run the audit script to see current status
2. Update any missing required variables
3. Update Supabase if needed using `--update-supabase`
4. Restart VANI container
5. Run webhook configuration script: `python scripts/configure_webhooks.py`


