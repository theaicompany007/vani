# Project VANI - Complete Execution Guide

## 🎯 Overview

**Project VANI (Virtual Agent Network Interface)** is an AI-powered outreach command center for FMCG companies. It enables multi-channel outreach (Email, WhatsApp, LinkedIn) with AI-generated personalized messages, meeting scheduling, and real-time engagement tracking.

---

## 📋 Prerequisites

### Required Software
- **Python 3.13+** (or 3.11+)
- **ngrok** (for public webhook access)
- **Git** (optional, for version control)

### Required Accounts & API Keys
1. **Supabase** - Cloud database
2. **Resend** - Email sending
3. **Twilio** - WhatsApp messaging
4. **Cal.com** - Meeting scheduling
5. **OpenAI** - AI message generation
6. **LinkedIn** - LinkedIn messaging (optional)
7. **Google Sheets** - Data import/export (optional)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone/Navigate to Project
```powershell
cd C:\Raaj\kcube_consulting_labs\vani
```

### Step 2: Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Verify Environment Variables
```powershell
python scripts\check_env_config.py
```

### Step 4: Create Database Tables (First Time Only)
```powershell
python scripts\create_database_tables_direct.py
```

### Step 5: Seed Initial Targets (Optional)
```powershell
python scripts\seed_targets.py
```

### Step 6: Run the Application
```powershell
python run.py
```

**That's it!** The script will:
- ✅ Kill any existing Flask/ngrok processes
- ✅ Check all environment variables
- ✅ Verify database connection
- ✅ Start Flask server
- ✅ Start ngrok tunnel
- ✅ Display public URL

---

## 📖 Detailed Setup Instructions

### 1. Environment Setup

#### Create `.env.local` File
Copy all required variables from `.env.example` or use the provided template:

```env
# Flask Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_CONNECTION=postgresql://postgres:password@db.project.supabase.co:5432/postgres
SUPABASE_DB_PASSWORD=your-db-password

# Resend (Email)
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=your@email.com
RESEND_FROM_NAME=Your Name

# Twilio (WhatsApp)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
TWILIO_PHONE_NUMBER=+1234567890

# Cal.com (Meetings)
CAL_COM_API_KEY=cal_live_xxxxx
CAL_COM_WEBHOOK_SECRET_PROD=your-webhook-secret
CAL_COM_USERNAME=your-username
CAL_COM_BASE_URL=https://api.cal.com

# OpenAI (Message Generation)
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_MODEL=gpt-4o-mini

# LinkedIn (Optional)
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret
LINKEDIN_REDIRECT_URI=https://vani.ngrok.app/auth/linkedin/callback
LINKEDIN_ACCESS_TOKEN=your-oauth-token  # Get via OAuth flow

# Webhooks
WEBHOOK_BASE_URL=https://vani.ngrok.app
WEBHOOK_SECRET=your-webhook-secret

# Notifications
NOTIFICATION_EMAIL=your@email.com
NOTIFICATION_WHATSAPP=+1234567890

# Polling Configuration
POLLING_TIMES=10,12,14,17  # 10 AM, 12 PM, 2 PM, 5 PM
EXCLUDE_WEEKENDS=true

# Google Sheets (Optional)
GOOGLE_SHEETS_CREDENTIALS_PATH=./config/service-account-key.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
GOOGLE_SHEETS_TARGETS_SHEET_NAME=Targets
GOOGLE_SHEETS_ACTIVITIES_SHEET_NAME=Activities
```

### 2. Database Setup

#### Option A: Automated (Recommended)
```powershell
python scripts\create_database_tables_direct.py
```

#### Option B: Manual
1. Go to: https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new
2. Copy SQL from: `app/migrations/001_create_tables.sql`
3. Paste and execute

### 3. Ngrok Setup

#### Configure Ngrok Authtoken
```powershell
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
```

#### Configure Static Domain (Optional)
Edit `%LOCALAPPDATA%\ngrok\ngrok.yml`:
```yaml
version: '2'
region: us
authtoken: YOUR_TOKEN
tunnels:
  vani:
    proto: http
    addr: 5000
    domain: vani.ngrok.app
```

### 4. Seed Initial Data
```powershell
python scripts\seed_targets.py
```

This loads 5 FMCG targets (HUL, Britannia, Marico, Asian Paints, ITC) from the strategy deck.

---

## 🎮 How to Use Project VANI

### Starting the Application

**Single Command:**
```powershell
python run.py
```

This will:
1. Clean up existing processes
2. Check all configurations
3. Start Flask server
4. Start ngrok tunnel
5. Display public URL

### Accessing the Command Center

Once running, open:
- **Local**: http://127.0.0.1:5000/command-center
- **Public**: https://vani.ngrok.app/command-center (shown in terminal)

### Using the Dashboard

#### 1. View Targets
- Click "Target Hit List" tab
- See all FMCG companies and contacts
- Click any target to view details

#### 2. Generate AI Message
1. Select a target
2. Choose channel (Email, WhatsApp, or LinkedIn)
3. Click "Generate AI Message"
4. Preview the generated message
5. Edit if needed
6. Click "Send Now" to approve and send

#### 3. Track Activities
- View sent messages in dashboard
- See engagement metrics (opens, clicks, replies)
- Track meeting schedules

#### 4. Schedule Meetings
- Generate message with meeting link
- Cal.com integration handles scheduling
- Receive notifications when meetings are booked

---

## 🔧 Configuration Scripts

### Check Environment Configuration
```powershell
python scripts\check_env_config.py
```
Shows which variables are set and which are missing.

### Test API Keys
```powershell
python scripts\test_api_keys.py
```
Validates all API keys (Resend, Twilio, Cal.com, OpenAI).

### Configure Webhooks
```powershell
python scripts\configure_webhooks.py
```
Automatically configures webhooks in Resend, Twilio, and Cal.com.

### Setup Database
```powershell
python scripts\create_database_tables_direct.py
```
Creates all database tables using your Supabase connection.

### Seed Targets
```powershell
python scripts\seed_targets.py
```
Loads initial target data from strategy deck.

---

## 📡 Webhook Configuration

### Manual Setup (If Automated Fails)

#### Resend Webhooks
1. Go to: https://resend.com/webhooks
2. Add webhook: `https://vani.ngrok.app/api/webhooks/resend`
3. Enable events: email.sent, email.delivered, email.opened, email.clicked, email.bounced

#### Twilio Webhooks
1. Go to: https://console.twilio.com/ → Phone Numbers
2. Select your WhatsApp number
3. Set Status Callback: `https://vani.ngrok.app/api/webhooks/twilio`

#### Cal.com Webhooks
1. Go to: https://cal.com/settings/developer/webhooks
2. Add webhook: `https://vani.ngrok.app/api/webhooks/cal-com`
3. Enable events: BOOKING_CREATED, BOOKING_CANCELLED, BOOKING_RESCHEDULED

---

## 🔐 LinkedIn Integration Setup

LinkedIn messaging requires OAuth 2.0 authentication:

### Step 1: Create LinkedIn App
1. Go to: https://www.linkedin.com/developers/apps
2. Create new app
3. Get Client ID and Client Secret

### Step 2: Configure OAuth
1. Add redirect URI: `https://vani.ngrok.app/auth/linkedin/callback`
2. Request permissions: `w_member_social` (messaging)

### Step 3: Get Access Token
1. Complete OAuth flow
2. Add `LINKEDIN_ACCESS_TOKEN` to `.env.local`

### Step 4: Use LinkedIn Channel
- Select "LinkedIn" when sending outreach
- System will use LinkedIn Messaging API

**Note**: LinkedIn integration is optional. Email and WhatsApp work without it.

---

## 📊 Features

### ✅ Fully Visible on Dashboard
- **Multi-channel outreach** (Email, WhatsApp, LinkedIn) → `Target Hit List` tab
- **AI message generation** (OpenAI) → `Target Hit List` → Generate button
- **Message preview and approval** → `Target Hit List` → Preview section
- **Dashboard with analytics** → `Situation Room` tab (charts and metrics)

### ⚠️ Backend Implemented, UI Needs Addition
- **Real-time engagement tracking** → Backend API ready, needs Analytics tab
- **Meeting scheduling** (Cal.com) → Webhooks working, needs Meetings section
- **Google Sheets import/export** → Backend ready, needs Import/Export buttons
- **HIT notifications display** → Sending notifications, needs Notification center
- **Polling status indicator** → Running automatically, needs status display

### ✅ Automatic (No UI Needed)
- **Webhook handling for events** → Runs automatically in background
- **HIT notifications** (email & WhatsApp) → Sends automatically when events occur
- **Scheduled polling** (4x daily) → Runs automatically at 10 AM, 12 PM, 2 PM, 5 PM

**📖 See `DASHBOARD_FEATURES_GUIDE.md` for detailed location of each feature!**

### 🔄 Workflow
1. **Import Targets** → From Google Sheets or manual entry
2. **Generate Message** → AI creates personalized message
3. **Preview & Edit** → Review and customize
4. **Send** → Multi-channel delivery
5. **Track** → Real-time engagement metrics
6. **Schedule** → Book meetings via Cal.com
7. **Export** → Sync back to Google Sheets

---

## 🐛 Troubleshooting

### Flask Server Won't Start
- **Check**: Port 5000 is available
- **Fix**: Change `FLASK_PORT` in `.env.local`
- **Or**: Kill process using port 5000

### Ngrok Can't Connect to Flask
- **Error**: ERR_NGROK_8012
- **Fix**: `run.py` now verifies Flask is accessible before starting ngrok
- **Check**: Flask is binding to 127.0.0.1 (not 0.0.0.0)

### Database Connection Failed
- **Check**: `SUPABASE_CONNECTION` or `SUPABASE_DB_PASSWORD` in `.env.local`
- **Verify**: Supabase project is active
- **Test**: `python scripts\create_database_tables_direct.py`

### Webhooks Not Working
- **Check**: Ngrok is running (`python run.py` starts it automatically)
- **Verify**: Webhook URLs are configured in each service
- **Test**: `python scripts\configure_webhooks.py`

### API Keys Invalid
- **Test**: `python scripts\test_api_keys.py`
- **Check**: Keys are correct in `.env.local`
- **Regenerate**: If needed, get new keys from service dashboards

---

## 📁 Project Structure

```
vani/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── routes.py             # Main routes
│   ├── supabase_client.py   # Database client
│   ├── api/                  # API endpoints
│   │   ├── targets.py        # Target CRUD
│   │   ├── outreach.py       # Send outreach
│   │   ├── dashboard.py     # Analytics
│   │   └── message_generator.py  # AI generation
│   ├── integrations/         # Third-party clients
│   │   ├── resend_client.py  # Email
│   │   ├── twilio_client.py # WhatsApp
│   │   ├── linkedin_client.py # LinkedIn
│   │   ├── cal_com_client.py # Meetings
│   │   ├── openai_client.py # AI
│   │   └── google_sheets_client.py # Sheets
│   ├── webhooks/            # Webhook handlers
│   │   ├── resend_handler.py
│   │   └── twilio_handler.py
│   ├── models/              # Data models
│   └── templates/           # Frontend
│       └── command_center.html
├── scripts/
│   ├── run.py               # Main startup script ⭐
│   ├── create_database_tables_direct.py
│   ├── configure_webhooks.py
│   ├── seed_targets.py
│   └── test_api_keys.py
├── .env.local               # Your configuration
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🎯 Typical Workflow

### Daily Operations

1. **Morning (10 AM)**
   - System polls for updates
   - Check dashboard for overnight engagement
   - Review HIT notifications

2. **Midday (12 PM)**
   - Generate and send new outreach
   - Follow up on pending responses

3. **Afternoon (2 PM)**
   - Review meeting schedules
   - Prepare for upcoming calls

4. **Evening (5 PM)**
   - Final polling and reporting
   - Export data to Google Sheets

### Sending Outreach

1. **Select Target** → Choose from hit list
2. **Choose Channel** → Email, WhatsApp, or LinkedIn
3. **Generate Message** → AI creates personalized content
4. **Preview & Edit** → Review and customize
5. **Approve & Send** → Message is delivered
6. **Track Engagement** → Monitor opens, clicks, replies

---

## 📞 Support & Resources

### Documentation Files
- `README.md` - Project overview
- `CONFIGURATION_STATUS.md` - Config checklist
- `WEBHOOK_SETUP_STATUS.md` - Webhook status
- `NGROK_CONFIGURATION.md` - Ngrok setup
- `PROJECT_VANI_EXECUTION_GUIDE.md` - This file

### Scripts Reference
- `run.py` - Main startup (does everything)
- `scripts/check_env_config.py` - Verify configuration
- `scripts/test_api_keys.py` - Test API keys
- `scripts/configure_webhooks.py` - Setup webhooks
- `scripts/create_database_tables_direct.py` - Database setup

### API Endpoints
- `GET /command-center` - Main dashboard
- `GET /api/targets` - List targets
- `POST /api/outreach/send` - Send outreach
- `POST /api/messages/generate` - Generate AI message
- `GET /api/dashboard/stats` - Dashboard statistics
- `POST /api/webhooks/resend` - Resend webhooks
- `POST /api/webhooks/twilio` - Twilio webhooks
- `POST /api/webhooks/cal-com` - Cal.com webhooks

---

## ✅ Quick Checklist

Before running:
- [ ] `.env.local` file exists with all keys
- [ ] Virtual environment activated
- [ ] Database tables created
- [ ] Ngrok authtoken configured
- [ ] At least one target seeded (optional)

To run:
- [ ] Execute: `python run.py`
- [ ] Wait for "SERVER RUNNING" message
- [ ] Note the public ngrok URL
- [ ] Open command center in browser

---

## 🎉 You're Ready!

Run `python run.py` and start your outreach campaign!

The system will handle:
- ✅ Process cleanup
- ✅ Configuration validation
- ✅ Server startup
- ✅ Ngrok tunnel
- ✅ Public URL display

**Access your command center and start reaching out to FMCG targets!**

