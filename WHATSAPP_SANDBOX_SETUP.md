# WhatsApp Sandbox Configuration Guide

This guide helps you configure Twilio WhatsApp Sandbox for testing (free account).

## Sandbox Details

- **Sandbox Number:** +1 415 523 8886
- **Join Code:** `join thought-function`
- **Webhook URL:** `https://vani.ngrok.app/api/webhooks/twilio`

## Environment Variables

Add to `.env.local`:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=AC0b78d044fe00fd25de302451b277571d
TWILIO_AUTH_TOKEN=2yXFVI3f7lkNmrDnHC8WJl5Jk8CYQCIj

# WhatsApp Sandbox (for free/testing)
TWILIO_SANDBOX_WHATSAPP_NUMBER=whatsapp:+14155238886

# Original WhatsApp number (for paid account)
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# SMS Phone Number
TWILIO_PHONE_NUMBER=+13253997829
```

## How to Connect to Sandbox

### Option 1: WhatsApp Message (Recommended)

1. Open WhatsApp on your mobile device
2. Send a message to: **+1 415 523 8886**
3. Include the join code: **join thought-function**
4. Once connected, any messages you send will trigger your webhook

### Option 2: QR Code

1. Go to Twilio Console → Messaging → Try it out → Send a WhatsApp message
2. Scan the QR code with WhatsApp
3. Follow the prompts to join

## Testing

### Send Test Message

```python
from app.integrations.twilio_client import TwilioClient

client = TwilioClient()
result = client.send_whatsapp(
    to="whatsapp:+YOUR_PHONE_NUMBER",  # Your number after joining sandbox
    message="Hello from VANI!"
)

print(result)
```

### Webhook Testing

1. Join the sandbox with your phone number
2. Send a message to the sandbox number
3. Your webhook at `https://vani.ngrok.app/api/webhooks/twilio` will receive it

## Code Behavior

The code automatically uses `TWILIO_SANDBOX_WHATSAPP_NUMBER` if set, otherwise falls back to `TWILIO_WHATSAPP_NUMBER`.

**Priority:**
1. `TWILIO_SANDBOX_WHATSAPP_NUMBER` (if set)
2. `TWILIO_WHATSAPP_NUMBER` (fallback)

## Webhook Configuration

Webhooks are automatically configured when you run `python run.py` and ngrok is detected.

Manual configuration:
```bash
python scripts/configure_webhooks.py
```

## Important Notes

1. **Sandbox Limitations:**
   - Only works with numbers that have joined the sandbox
   - Free for testing, but limited functionality
   - For production, upgrade to paid Twilio account

2. **Phone Number Format:**
   - Always use `whatsapp:` prefix: `whatsapp:+14155238886`
   - Code handles this automatically

3. **Webhook:**
   - Same endpoint handles both SMS and WhatsApp
   - Configured at: `https://vani.ngrok.app/api/webhooks/twilio`

## Troubleshooting

### "Number not found" Error

- Verify you've joined the sandbox with the join code
- Check that `TWILIO_SANDBOX_WHATSAPP_NUMBER` is set correctly
- Ensure number format includes `whatsapp:` prefix

### Webhook Not Receiving Messages

- Verify ngrok is running: `http://localhost:4040`
- Check webhook URL in Twilio Console
- Ensure webhook endpoint is accessible publicly

### 401 Errors

- Verify `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are correct
- Check phone number matches your Twilio account







