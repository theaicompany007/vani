# VANI Outreach Command Center

Real-time outreach command center for Project VANI (Virtual Agent Network Interface) - managing multi-channel outreach to FMCG targets with AI-powered message generation and automated tracking.

## 🚀 Quick Start

### 1. Setup Virtual Environment

```powershell
# Create virtual environment (Python 3.11+)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env.local` and fill in your credentials:

```powershell
Copy-Item .env.example .env.local
```

**Required credentials:**
- Supabase URL and keys (from theaicompany007 project)
- Resend API key (for email)
- Twilio credentials (for WhatsApp)
- OpenAI API key (for message generation)
- Cal.com API key (for meeting scheduling)
- Google Sheets credentials (for import/export)

### 3. Setup Database

Run the SQL migration in Supabase:

1. Go to: https://supabase.com/dashboard/project/[your-project-id]/sql/new
2. Copy SQL from: `app/migrations/001_create_tables.sql`
3. Paste and click "Run"

Or use the helper script:
```powershell
python scripts\setup_database.py
```

### 4. Seed Initial Targets

```powershell
python scripts\seed_targets.py
```

This will populate the 5 FMCG targets (HUL, Britannia, Marico, Asian Paints, ITC) from the HTML file.

### 5. Run the Application

```powershell
python run.py
```

Open: http://localhost:5000/command-center

## 📋 Features

### Core Functionality

- **Target Management**: CRUD operations for FMCG targets
- **AI Message Generation**: OpenAI-powered personalized messages based on target role and pain points
- **Message Preview & Approval**: Preview, edit, and approve messages before sending
- **Multi-Channel Outreach**: 
  - Email (via Resend)
  - WhatsApp (via Twilio)
  - LinkedIn (optional, future)
- **Automated Tracking**: Webhook-based tracking of opens, clicks, replies
- **HIT Notifications**: Instant Email + WhatsApp alerts when targets engage
- **Google Sheets Integration**: Import/export targets and activities
- **Cal.com Integration**: Schedule meetings directly from the dashboard
- **Admin Tools** (Super Users Only):
  - Batch contact import with multi-threading and memory management
  - System information and monitoring
  - Script execution interface
  - See [ADMIN_TOOLS_GUIDE.md](ADMIN_TOOLS_GUIDE.md) for details

### Real-time Features

- **Scheduled Polling**: 4 times daily (10 AM, 12 PM, 2 PM, 5 PM) - configurable
- **Weekend Exclusion**: Automatically skips outreach on Saturdays/Sundays
- **Webhook Processing**: Real-time status updates from Resend and Twilio

## 🗂️ Project Structure

```
vani/
├── app/
│   ├── api/              # API routes (targets, outreach, dashboard, messages)
│   ├── integrations/      # Third-party integrations (Resend, Twilio, OpenAI, etc.)
│   ├── models/           # Data models (Pydantic)
│   ├── webhooks/          # Webhook handlers
│   ├── migrations/        # Database migration SQL
│   ├── templates/         # HTML templates
│   └── static/           # CSS, JS, images
├── scripts/              # Utility scripts (seed, setup)
├── logs/                 # Application logs
├── .env.local           # Your credentials (not in git)
└── requirements.txt     # Python dependencies
```

## 🔧 Configuration

### Environment Variables

See `.env.example` for all required variables. Key ones:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `RESEND_API_KEY` - Resend email API key
- `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` - Twilio credentials
- `OPENAI_API_KEY` - OpenAI API key for message generation
- `NOTIFICATION_EMAIL` - Your email for HIT alerts
- `NOTIFICATION_WHATSAPP` - Your WhatsApp number for HIT alerts
- `WEBHOOK_BASE_URL` - https://vani.ngrok.app (your ngrok URL)
- `POLLING_TIMES` - 10,12,14,17 (10 AM, 12 PM, 2 PM, 5 PM)
- `EXCLUDE_WEEKENDS` - true (skip weekends)

### Webhook Setup

Configure webhooks in your service dashboards:

1. **Resend**: https://resend.com/webhooks
   - URL: `https://vani.ngrok.app/api/webhooks/resend`
   - Events: email.sent, email.delivered, email.opened, email.clicked, email.bounced

2. **Twilio**: https://console.twilio.com/
   - Status Callback: `https://vani.ngrok.app/api/webhooks/twilio`

3. **Cal.com**: https://cal.com/settings/developer/webhooks
   - URL: `https://vani.ngrok.app/api/webhooks/cal-com`

## 📊 Database Schema

Tables:
- `targets` - FMCG companies and contacts
- `outreach_sequences` - Multi-step outreach templates
- `outreach_activities` - Individual outreach actions
- `meetings` - Cal.com scheduled meetings
- `webhook_events` - Webhook tracking

See `app/migrations/001_create_tables.sql` for full schema.

## 🎯 Usage

### Generate and Send Outreach

1. Navigate to "Target Hit List" tab
2. Select a target company
3. Choose channel (Email or WhatsApp)
4. Click "Generate AI Message"
5. Preview the generated message
6. Edit if needed
7. Click "Send Now" to send

### Import/Export Targets

- **Import from Google Sheets**: `POST /api/targets/import`
- **Export to Google Sheets**: `GET /api/targets/export`

### Batch Import Contacts (Super Users)

For importing 1000+ contacts efficiently:

**Via Admin Tools UI:**
1. Navigate to **Admin Tools** tab (super users only)
2. Enter Excel file path (e.g., `data/the_ai_company.xlsx`)
3. Configure batch size (100-500) and threads (1-16)
4. Select options (update existing, import only new, dry run)
5. Click **Run Batch Import**

**Via Command Line:**
```bash
python scripts/import_contacts_batch.py data/file.xlsx --batch-size 100 --threads 4
```

See [ADMIN_TOOLS_GUIDE.md](ADMIN_TOOLS_GUIDE.md) for detailed instructions.

### View Dashboard Stats

Dashboard polls `/api/dashboard/stats` at configured times (default: 10 AM, 12 PM, 2 PM, 5 PM).

## 🔔 HIT Notifications

You'll receive Email + WhatsApp notifications when:
- Target opens email
- Target clicks link
- Target replies
- Meeting is scheduled
- Any positive engagement detected

## 🛠️ Development

### Running Tests

```powershell
pytest
```

### Code Formatting

```powershell
black app/
flake8 app/
```

## 📝 Notes

- Weekend exclusion is enabled by default (`EXCLUDE_WEEKENDS=true`)
- Polling times can be customized via `POLLING_TIMES` env var
- All webhooks require ngrok tunnel for local development
- OpenAI message generation uses `gpt-4o-mini` by default (configurable)

## 🚨 Troubleshooting

### Database Connection Issues
- Verify Supabase URL and keys in `.env.local`
- Check if migration SQL was executed successfully

### Webhook Not Receiving Events
- Verify ngrok URL is correct and tunnel is active
- Check webhook URLs in service dashboards
- Review logs in `logs/application.log`

### Message Generation Fails
- Verify OpenAI API key is set
- Check API quota/limits
- Review error logs

### Large Contact Import Issues
- Use Admin Tools batch import for 2000+ records
- Reduce batch size if memory errors occur
- Check logs in `logs/batch_import_*.log`
- See [ADMIN_TOOLS_GUIDE.md](ADMIN_TOOLS_GUIDE.md) for troubleshooting

## 📄 License

Private project - All rights reserved

