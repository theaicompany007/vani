# Project VANI - Local Development Setup Guide

## Quick Start for Local Machine

### Prerequisites
- Python 3.11+ installed
- Supabase project configured
- `.env.local` file with all API keys
- ngrok installed (optional, for webhooks)

## Step 1: Activate Virtual Environment

```powershell
# Navigate to project directory
cd C:\Raaj\kcube_consulting_labs\vani

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

## Step 2: Install Dependencies (if not already done)

```powershell
pip install -r requirements.txt
```

## Step 3: Run Database Migrations

### Option A: Run via Supabase SQL Editor (Recommended)
1. Open Supabase Dashboard → SQL Editor
2. Run each migration file in order:
   - `app/migrations/001_create_tables.sql` (if not already run)
   - `app/migrations/002_industries_tenants.sql`
   - `app/migrations/003_auth_permissions.sql`
   - `app/migrations/004_pitch_storage.sql`
   - `app/migrations/005_add_industry_to_tables.sql`

### Option B: Run via Python Script
```powershell
python scripts/create_database_tables_direct.py
```

## Step 4: Create First Super User

### 4.1 Sign Up via Supabase Auth
1. Go to your Supabase Dashboard → Authentication → Users
2. Click "Add User" → "Create new user"
3. Enter email and password
4. Copy the User ID (UUID)

### 4.2 Make User a Super User
Run this in Supabase SQL Editor:

```sql
-- Replace 'YOUR_SUPABASE_USER_ID' with the UUID from step 4.1
-- Replace 'your@email.com' with your email

INSERT INTO app_users (supabase_user_id, email, name, is_super_user, is_industry_admin)
VALUES (
    'YOUR_SUPABASE_USER_ID',
    'your@email.com',
    'Your Name',
    true,
    true
)
ON CONFLICT (supabase_user_id) 
DO UPDATE SET is_super_user = true, is_industry_admin = true;
```

### 4.3 Grant All Permissions (Optional)
```sql
-- Grant all use cases to your user
INSERT INTO user_permissions (user_id, use_case_id, industry_id)
SELECT 
    (SELECT id FROM app_users WHERE email = 'your@email.com'),
    uc.id,
    NULL  -- NULL = all industries
FROM use_cases uc
ON CONFLICT DO NOTHING;
```

## Step 5: Start the Application

### Option A: Using run.py (Recommended)
```powershell
python run.py
```

This will:
- Check environment variables
- Verify database connection
- Kill any existing Flask/ngrok processes
- Start Flask on port 5000
- Start ngrok tunnel
- Display the public ngrok URL

### Option B: Manual Start
```powershell
# Start Flask
python -m flask run --host=127.0.0.1 --port=5000

# In another terminal, start ngrok (if needed)
ngrok http 5000 --domain=vani.ngrok.app
```

## Step 6: Access the Application

### Local Access
- **Login Page**: http://localhost:5000/login
- **Command Center**: http://localhost:5000/command-center
- **Health Check**: http://localhost:5000/api/health

### Public Access (via ngrok)
- **Public URL**: https://vani.ngrok.app
- **Login**: https://vani.ngrok.app/login
- **Command Center**: https://vani.ngrok.app/command-center

## Step 7: First Login

1. Go to http://localhost:5000/login (or ngrok URL)
2. Enter your email and password (created in Supabase)
3. You'll be redirected to the command center
4. As a super user, you'll see:
   - All tabs and features
   - Industry selector (top right)
   - Admin Panel link

## Step 8: Configure Webhooks (Optional)

If you want webhooks to work (Resend, Twilio, Cal.com):

```powershell
python scripts/configure_webhooks.py
```

This will set webhook URLs to: `https://vani.ngrok.app/webhooks/...`

## Troubleshooting

### "Authentication required" error
- Make sure you've created the user in Supabase Auth
- Verify `app_users` table has your user record
- Check that `is_super_user = true` is set

### "Permission denied" error
- Grant use case permissions via SQL:
```sql
-- Grant specific permission
INSERT INTO user_permissions (user_id, use_case_id, industry_id)
SELECT 
    (SELECT id FROM app_users WHERE email = 'your@email.com'),
    (SELECT id FROM use_cases WHERE code = 'outreach'),
    NULL
ON CONFLICT DO NOTHING;
```

### Database connection errors
- Verify `.env.local` has correct Supabase credentials:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `SUPABASE_SERVICE_KEY`
  - `SUPABASE_CONNECTION`
  - `SUPABASE_DB_PASSWORD`

### Port 5000 already in use
```powershell
# Kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### ngrok not starting
- Check ngrok authtoken: `ngrok config check`
- Verify domain: `ngrok config edit`
- Check if domain is already in use

## Development Workflow

### Making Changes
1. Edit code files
2. Flask auto-reloads (if using `flask run`)
3. Refresh browser to see changes

### Testing New Features
1. Test locally first
2. Check browser console for errors
3. Check Flask terminal for backend errors
4. Test with different user permissions

### Adding New Users
1. Create user in Supabase Auth dashboard
2. Run SQL to create `app_users` record
3. Grant permissions via SQL or Admin Panel (once built)

## Environment Variables Checklist

Make sure `.env.local` has:

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_CONNECTION=postgresql://...
SUPABASE_DB_PASSWORD=your_db_password

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Resend
RESEND_API_KEY=re_...

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+...

# Cal.com
CALCOM_API_KEY=...
CALCOM_USERNAME=...

# ngrok
NGROK_AUTHTOKEN=...
NGROK_DOMAIN=vani.ngrok.app
WEBHOOK_BASE_URL=https://vani.ngrok.app

# RAG / Knowledge Base (Optional)
RAG_API_KEY=...
RAG_SERVICE_URL=https://rag.theaicompany.co

# Google Drive (Optional - for Admin → Google Drive sync)
GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
# OR
GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH=C:\path\to\service-account-key.json

# Gemini (Optional - for AI Target Finder)
GEMINI_API_KEY=...

# App Settings
SECRET_KEY=your-secret-key
FLASK_PORT=5000
EXCLUDE_WEEKENDS=true
POLLING_TIMES=10:00,12:00,14:00,17:00
```

## Quick Commands Reference

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Run app
python run.py

# Run migrations (if script exists)
python scripts/create_database_tables_direct.py

# Configure webhooks
python scripts/configure_webhooks.py

# Test API keys
python scripts/test_api_keys.py

# Check health
curl http://localhost:5000/api/health
```

## Optional: Google Drive Setup

To enable Google Drive sync (Super Users only):

1. **Create Google Service Account** (see `GOOGLE_DRIVE_SETUP.md`)
2. **Add to `.env.local`**:
   ```env
   GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
   # OR
   GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH=C:\path\to\service-account-key.json
   ```
3. **Share Google Drive folders** with service account email
4. **Access**: Admin → Google Drive tab

📖 **See [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md) for detailed instructions.**

## Next Steps After Local Setup

1. ✅ Test login/logout
2. ✅ Create test targets
3. ✅ Test pitch generation
4. ✅ Test outreach sending
5. ✅ Grant permissions to test users
6. ✅ Test industry switching (as super user)
7. ✅ (Optional) Configure Google Drive sync
8. ✅ Integrate frontend code from `FRONTEND_INTEGRATION_GUIDE.md`

## Notes

- **Local development**: Use `http://localhost:5000` for local testing
- **Webhook testing**: Use ngrok URL (`https://vani.ngrok.app`) for webhooks
- **Database**: All data stored in Supabase (cloud database)
- **No local database needed**: Everything uses Supabase

You're all set! The system runs entirely on your local machine but uses Supabase as the cloud database.

