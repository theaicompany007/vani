# Webhook Configuration Status

## Current Status

### ✅ Database Tables
- **Status**: ✅ **COMPLETE**
- All 5 tables created successfully
- 15 indexes and 4 triggers created
- 5 targets seeded

### ⚠️ Webhook Configuration Issues

#### 1. Resend Webhook
- **Status**: ❌ **API KEY INVALID**
- **Issue**: The Resend API key in `.env.local` is being rejected by Resend API
- **Error**: `{"statusCode":400,"message":"API key is invalid"}`
- **Action Required**:
  1. Go to: https://resend.com/api-keys
  2. Verify the key `re_R36ELxpj_5rkqMz74Ggk3wcCIdKX5xV` exists and is active
  3. If not, generate a new API key
  4. Update `RESEND_API_KEY` in `.env.local`
  5. Re-run: `python scripts/configure_webhooks.py`

#### 2. Twilio Webhook
- **Status**: ⚠️ **NO PHONE NUMBERS IN ACCOUNT**
- **Issue**: Twilio API keys are valid, but account has 0 phone numbers
- **Current Config**:
  - WhatsApp Number: `whatsapp:+14155238886`
  - Phone Number: `+13253997829`
- **Action Required**:
  1. Go to: https://console.twilio.com/ → Phone Numbers
  2. Purchase/configure a phone number with WhatsApp capability
  3. Update `TWILIO_WHATSAPP_NUMBER` in `.env.local` with the actual number
  4. Re-run: `python scripts/configure_webhooks.py`
  
  **OR** configure manually:
  1. Go to: https://console.twilio.com/ → Phone Numbers → Manage → Active Numbers
  2. Select your WhatsApp-enabled number
  3. Set Status Callback URL: `https://vani.ngrok.app/api/webhooks/twilio`
  4. Save

#### 3. Cal.com Webhook
- **Status**: ⚠️ **API AUTHENTICATION ISSUE**
- **Issue**: Cal.com API requires additional authentication headers
- **Current Key**: `cal_live_776c65d7c493967528a04e9221620880`
- **Error**: `"Only 'x-cal-secret-key' header provided. Please also provide..."`
- **Action Required**:
  1. Go to: https://cal.com/settings/developer/api-keys
  2. Verify the API key format and permissions
  3. Check Cal.com API documentation for correct authentication method
  4. Update webhook script if needed
  
  **OR** configure manually:
  1. Go to: https://cal.com/settings/developer/webhooks
  2. Click "Add Webhook"
  3. URL: `https://vani.ngrok.app/api/webhooks/cal-com`
  4. Events: BOOKING_CREATED, BOOKING_CANCELLED, BOOKING_RESCHEDULED
  5. Secret: `vani_webhook_secret_12345_change_this_to_secure_value`
  6. Save

## Manual Webhook Configuration

If automated configuration fails, you can configure webhooks manually:

### Resend
1. **URL**: https://resend.com/webhooks
2. **Webhook URL**: `https://vani.ngrok.app/api/webhooks/resend`
3. **Events**: 
   - email.sent
   - email.delivered
   - email.opened
   - email.clicked
   - email.bounced
   - email.complained

### Twilio
1. **URL**: https://console.twilio.com/ → Phone Numbers
2. **Status Callback URL**: `https://vani.ngrok.app/api/webhooks/twilio`
3. **Method**: POST

### Cal.com
1. **URL**: https://cal.com/settings/developer/webhooks
2. **Webhook URL**: `https://vani.ngrok.app/api/webhooks/cal-com`
3. **Events**: 
   - BOOKING_CREATED
   - BOOKING_CANCELLED
   - BOOKING_RESCHEDULED
4. **Secret**: Use value from `CAL_COM_WEBHOOK_SECRET_PROD`

## Testing API Keys

Run the diagnostic script to test your API keys:

```powershell
python scripts\test_api_keys.py
```

## Next Steps

1. **Fix Resend API Key**: Regenerate at https://resend.com/api-keys
2. **Add Twilio Phone Number**: Purchase/configure in Twilio Console
3. **Fix Cal.com Authentication**: Check API documentation or configure manually
4. **Re-run Configuration**: `python scripts\configure_webhooks.py`

## Notes

- All webhook URLs must be publicly accessible (ensure ngrok tunnel is running)
- Database setup is complete and working
- Application can run without webhooks (they're for tracking engagement)
- Webhooks can be configured later without affecting core functionality

