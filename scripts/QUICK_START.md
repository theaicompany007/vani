# Quick Start Guide

## ✅ What's Already Done

1. **Database Tables**: ✅ Created (5 tables, 15 indexes, 4 triggers)
2. **Targets Seeded**: ✅ 5 FMCG targets loaded
3. **Environment Variables**: ✅ All configured in `.env.local`

## 🚀 Start the Application

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start the Flask application
python run.py
```

Then open: http://localhost:5000/command-center

## ⚠️ Webhook Configuration (Optional)

Webhooks are for tracking email opens, clicks, replies, and meeting bookings. The application works without them, but you'll miss engagement tracking.

### Current Status:
- **Resend**: API key needs verification/regeneration
- **Twilio**: No phone numbers in account (add one first)
- **Cal.com**: API authentication needs fixing

### Quick Fix Options:

**Option 1: Configure Manually** (Recommended for now)
- See `WEBHOOK_SETUP_STATUS.md` for step-by-step instructions
- Takes 5-10 minutes per service

**Option 2: Fix API Keys and Re-run**
```powershell
# Test your API keys
python scripts\test_api_keys.py

# After fixing keys, configure webhooks
python scripts\configure_webhooks.py
```

## 📋 What You Can Do Now

Even without webhooks configured, you can:

1. **View Targets**: See all 5 FMCG companies in the command center
2. **Generate AI Messages**: Use OpenAI to create personalized outreach
3. **Preview Messages**: Review and edit before sending
4. **Send Outreach**: Send emails and WhatsApp messages
5. **Track Activities**: View sent messages in the dashboard

## 🔧 Troubleshooting

### Application Won't Start
- Check: `python run.py` shows errors
- Verify: `.env.local` has all required keys
- Test: `python scripts\test_api_keys.py`

### Database Connection Issues
- Verify: `SUPABASE_CONNECTION` in `.env.local` is correct
- Test: `python scripts\create_database_tables_direct.py` (should say tables exist)

### Webhook Issues
- See: `WEBHOOK_SETUP_STATUS.md` for detailed status
- Run: `python scripts\test_api_keys.py` to diagnose

## 📚 Documentation

- `CONFIGURATION_STATUS.md` - Full configuration report
- `WEBHOOK_SETUP_STATUS.md` - Webhook setup status and fixes
- `scripts/README_SETUP.md` - Setup scripts documentation

## 🎯 Next Steps

1. **Start the app**: `python run.py`
2. **Test message generation**: Select a target → Generate AI Message
3. **Configure webhooks** (when ready): See `WEBHOOK_SETUP_STATUS.md`
4. **Send your first outreach**: Preview → Edit → Send

---

**You're ready to go!** The core application is fully functional. Webhooks can be configured later for enhanced tracking.

