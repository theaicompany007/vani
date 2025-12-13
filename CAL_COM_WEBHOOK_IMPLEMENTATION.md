# Cal.com Webhook Implementation Summary

## What Was Created

### 1. Cal.com Webhook Handler
**File:** `app/webhooks/cal_com_handler.py`

**Features:**
- Receives Cal.com webhook events at `/api/webhooks/cal-com`
- Verifies webhook signature using `CAL_COM_WEBHOOK_SECRET`
- Maps Cal.com events to meeting statuses:
  - `BOOKING_CREATED` / `BOOKING_REQUESTED` → `scheduled`
  - `BOOKING_CANCELLED` / `BOOKING_REJECTED` → `cancelled`
  - `BOOKING_RESCHEDULED` → `scheduled` (with updated times)
  - `MEETING_ENDED` → `completed` (triggers HIT notification)
  - `BOOKING_PAID` → `scheduled` (triggers HIT notification)
  - `BOOKING_NO_SHOW_UPDATED` → `no_show` or `completed`
- Updates meeting records in database
- Saves webhook events to `webhook_events` table
- Sends HIT notifications for important events

### 2. Route Registration
**File:** `app/routes.py`

**Changes:**
- Imported `cal_com_handler`
- Registered `cal_com_webhook_bp` blueprint

## Files That Don't Need Updates

### ✅ `run.py`
- Already displays Cal.com webhook URL in status output
- Already calls `configure_webhooks_with_url()` which handles Cal.com
- No changes needed

### ✅ `scripts/configure_webhooks.py`
- Already has Cal.com webhook configuration
- Already has environment-aware safety checks
- Already tries both v1 and v2 API formats
- No changes needed

## Webhook Events Supported

The handler processes these Cal.com webhook events:

1. **BOOKING_CREATED** - Meeting scheduled
2. **BOOKING_REQUESTED** - Meeting requested (pending)
3. **BOOKING_CANCELLED** - Meeting cancelled
4. **BOOKING_RESCHEDULED** - Meeting rescheduled
5. **BOOKING_REJECTED** - Meeting rejected
6. **BOOKING_PAID** - Payment received (HIT)
7. **BOOKING_NO_SHOW_UPDATED** - No-show status updated
8. **MEETING_ENDED** - Meeting completed (HIT)

## Configuration

### Environment Variables

**Required:**
- `CAL_COM_API_KEY` - Cal.com API key (for webhook configuration)

**Optional:**
- `CAL_COM_WEBHOOK_SECRET` - Webhook signature verification secret
- `CAL_COM_WEBHOOK_SECRET_PROD` - Production webhook secret (alternative)

### Webhook URL

- **Dev:** `https://vani-dev.ngrok.app/api/webhooks/cal-com`
- **Prod:** `https://vani.ngrok.app/api/webhooks/cal-com`

## How It Works

1. **Cal.com sends webhook** → `/api/webhooks/cal-com`
2. **Handler verifies signature** (if `CAL_COM_WEBHOOK_SECRET` is set)
3. **Handler finds meeting** by `cal_event_id` (Cal.com booking ID)
4. **Handler updates meeting status** based on event type
5. **Handler saves webhook event** to `webhook_events` table
6. **Handler sends HIT notification** for important events (payment, completion)

## Testing

### Test Webhook Endpoint

```bash
# Test if endpoint exists
curl -X POST https://vani-dev.ngrok.app/api/webhooks/cal-com \
  -H "Content-Type: application/json" \
  -d '{"triggerEvent": "BOOKING_CREATED", "payload": {"uid": "test123"}}'
```

### Verify in Cal.com Dashboard

1. Go to: https://app.cal.com/settings/platform/webhooks
2. Check webhook is active and receiving events
3. View webhook logs in Cal.com dashboard

## Database Integration

The webhook handler:
- **Finds meetings** by `cal_event_id` (stores Cal.com booking ID)
- **Updates meeting status** in `meetings` table
- **Saves webhook events** to `webhook_events` table
- **Links to targets** for HIT notifications

## Next Steps

1. **Update Cal.com webhook URLs:**
   - Dev: `https://vani-dev.ngrok.app/api/webhooks/cal-com`
   - Prod: `https://vani.ngrok.app/api/webhooks/cal-com`

2. **Set webhook secret** (optional but recommended):
   ```bash
   CAL_COM_WEBHOOK_SECRET=your_secret_here
   ```

3. **Test webhook:**
   - Create a test booking in Cal.com
   - Check if webhook is received
   - Verify meeting status is updated in VANI

4. **Monitor webhook events:**
   - Check `webhook_events` table in Supabase
   - Check application logs for webhook processing

## Troubleshooting

### Webhook Not Receiving Events

1. **Check webhook URL in Cal.com:**
   - Must be: `/api/webhooks/cal-com` (not `/webhooks/cal-events`)
   - Must be accessible (ngrok running)

2. **Check webhook is active:**
   - Toggle switch should be ON in Cal.com dashboard

3. **Check application logs:**
   ```bash
   # Look for "Received Cal.com webhook" messages
   ```

### Meeting Not Found

- **Cause:** `cal_event_id` doesn't match Cal.com booking ID
- **Solution:** Ensure `cal_event_id` is set when creating meeting via `/api/meetings/schedule`

### Signature Verification Fails

- **Cause:** `CAL_COM_WEBHOOK_SECRET` doesn't match Cal.com webhook secret
- **Solution:** Update secret in `.env.local` to match Cal.com webhook secret

## Summary

✅ **Created:** Cal.com webhook handler  
✅ **Registered:** Webhook route in Flask app  
✅ **No updates needed:** `run.py` and `configure_webhooks.py`  
✅ **Ready to use:** Just update webhook URLs in Cal.com dashboard


