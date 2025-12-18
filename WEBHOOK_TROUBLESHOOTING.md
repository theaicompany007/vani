# Webhook Configuration Troubleshooting

## Issues Fixed

### 1. Twilio Authentication Error (401)

**Error:**
```
❌ Failed to fetch phone numbers: {"code":20003,"message":"Authenticate","more_info":"https://www.twilio.com/docs/errors/20003","status":401}
```

**Solution:**
The script now uses `requests.auth` instead of embedding credentials in the URL, which is more reliable.

**Check:**
1. Verify `TWILIO_ACCOUNT_SID` starts with `AC` (e.g., `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
2. Verify `TWILIO_AUTH_TOKEN` is correct (should be ~32 characters)
3. Check for extra spaces or newlines in your `.env.local` file
4. Verify credentials in Twilio Console: https://console.twilio.com/us1/account/settings/credentials

**Example `.env.local`:**
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=14155238886
# or for sandbox:
TWILIO_SANDBOX_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 2. Cal.com "No apiKey provided" Error

**Error:**
```
⚠️  Could not list webhooks: {"message":"No apiKey provided"}
❌ Failed to create webhook: {"message":"No apiKey provided"}
```

**Solution:**
The script now:
- Tries both v1 and v2 API formats
- Provides better error messages
- Validates API key format

**Check:**
1. **For v1 API:** Key should start with `cal_live_` or `cal_test_`
   - Get from: https://app.cal.com/settings/developer/api-keys
   - Format: `cal_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

2. **For v2 API:** Use secret key format
   - Check Cal.com documentation for v2 key format

**Example `.env.local`:**
```bash
# For v1 API (recommended)
CAL_COM_API_KEY=cal_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional webhook secret
CAL_COM_WEBHOOK_SECRET=your_webhook_secret_here
```

**Manual Configuration:**
If automatic configuration fails, configure manually:
1. Go to: https://app.cal.com/settings/platform/webhooks
2. Click "Add Webhook"
3. Set URL: `https://vani-dev.ngrok.app/api/webhooks/cal-com`
4. Select events: `BOOKING_CREATED`, `BOOKING_CANCELLED`, `BOOKING_RESCHEDULED`
5. Set webhook secret (optional)

## Quick Fixes

### Verify Environment Variables

Run this to check your environment variables:
```bash
python -c "from dotenv import load_dotenv; import os; from pathlib import Path; load_dotenv(Path('.env.local')); print('TWILIO_ACCOUNT_SID:', os.getenv('TWILIO_ACCOUNT_SID', 'NOT SET')[:20]); print('TWILIO_AUTH_TOKEN:', 'SET' if os.getenv('TWILIO_AUTH_TOKEN') else 'NOT SET'); print('CAL_COM_API_KEY:', os.getenv('CAL_COM_API_KEY', 'NOT SET')[:20])"
```

### Test Twilio Credentials

```bash
python -c "import requests; import os; from dotenv import load_dotenv; from pathlib import Path; load_dotenv(Path('.env.local')); sid = os.getenv('TWILIO_ACCOUNT_SID'); token = os.getenv('TWILIO_AUTH_TOKEN'); r = requests.get(f'https://api.twilio.com/2010-04-01/Accounts/{sid}.json', auth=(sid, token)); print('Status:', r.status_code); print('Response:', r.text[:200] if r.status_code != 200 else 'OK')"
```

### Test Cal.com API Key

```bash
python -c "import requests; import os; from dotenv import load_dotenv; from pathlib import Path; load_dotenv(Path('.env.local')); key = os.getenv('CAL_COM_API_KEY'); headers = {'Authorization': f'Bearer {key}'} if key.startswith('cal_') else {'x-cal-secret-key': key}; r = requests.get('https://api.cal.com/v1/webhooks', headers=headers); print('Status:', r.status_code); print('Response:', r.text[:200])"
```

## Common Issues

### Issue: "Environment mismatch" warnings

**Cause:** Trying to update webhooks for different environment

**Solution:** 
- Set `VANI_ENVIRONMENT=dev` for development
- Set `VANI_ENVIRONMENT=prod` for production
- Or set `SKIP_WEBHOOK_UPDATE=true` to skip automatic updates

### Issue: Webhook URL not accessible

**Cause:** Ngrok tunnel not running or URL incorrect

**Solution:**
1. Ensure ngrok is running: `start-ngrok.bat`
2. Verify `WEBHOOK_BASE_URL` matches your ngrok URL
3. Test webhook endpoint: `curl https://vani-dev.ngrok.app/api/webhooks/resend`

### Issue: API keys not found

**Cause:** Environment variables not loaded

**Solution:**
1. Ensure `.env.local` exists in project root
2. Check file is not corrupted (no special characters)
3. Restart terminal/IDE after adding variables
4. Verify with: `python -c "from dotenv import load_dotenv; load_dotenv('.env.local'); import os; print(os.getenv('TWILIO_ACCOUNT_SID'))"`

## Next Steps

After fixing the issues, run the configuration again:

```bash
python scripts/configure_webhooks.py
```

You should see:
- ✅ RESEND - updated/created
- ✅ TWILIO - updated/created  
- ✅ CAL_COM - updated/created

If issues persist, check the detailed error messages and follow the troubleshooting steps above.







