# VANI Outreach Command Center

Real-time outreach command center for Project VANI (Virtual Agent Network Interface) - managing multi-channel outreach with AI-powered message generation, target identification, knowledge base integration, and automated tracking.

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
- OpenAI API key (for message generation and AI Target Finder)
- Cal.com API key (for meeting scheduling)
- Google Sheets credentials (for import/export)

**Optional but recommended:**
- RAG_API_KEY (for Knowledge Base and enhanced AI Target Finder)
- GEMINI_API_KEY (for Notebook LM integration in AI Target Finder)
- AI_PROVIDER_PRIORITY (default: "gemini,openai" - controls which AI provider to use first for target analysis)

### 3. Setup Database

Run the SQL migrations in Supabase:

1. Go to: https://supabase.com/dashboard/project/[your-project-id]/sql/new
2. Run migrations in order from `app/migrations/` directory
3. Or use the helper script:
```powershell
python scripts\run_all_migrations.py
```

### 4. Start VANI (Local Windows Development)

**Option A: Using vani.bat (Recommended)**
```cmd
vani.bat
```

**Option B: Manual**
```cmd
venv\Scripts\activate.bat
python run.py
```

### 5. Start Ngrok (For Webhooks)

**Option A: Using start-ngrok.bat**
```cmd
start-ngrok.bat
```

**Option B: Using PowerShell Script**
```powershell
.\scripts\start_ngrok.ps1
```

**Option C: Manual**
```cmd
ngrok http 5000 --domain=vani-dev.ngrok.app
```

**Note**: For local development, use `vani-dev.ngrok.app`. Make sure to reserve this domain in the ngrok dashboard first: https://dashboard.ngrok.com/cloud-edge/domains

📖 **See [LOCAL_WINDOWS_DEVELOPMENT.md](LOCAL_WINDOWS_DEVELOPMENT.md) for detailed local development guide.**

### 4. Run the Application

**Windows (No Docker):**
```cmd
vani.bat
```

**Manual:**
```powershell
python run.py
```

The script will:
- Check environment variables
- Verify database connection
- Detect ngrok tunnel (if running)
- Display public URL for webhooks
- Start Flask server

**Access VANI:**
- Local: http://localhost:5000/command-center
- Public: https://vani-dev.ngrok.app/command-center (after starting ngrok)

**Start Ngrok (separate terminal):**
```cmd
start-ngrok.bat
# OR
.\scripts\start_ngrok.ps1
```

📖 **For detailed local Windows development setup, see [LOCAL_WINDOWS_DEVELOPMENT.md](LOCAL_WINDOWS_DEVELOPMENT.md)**

## 📋 Features

### Core Functionality

- **Target Management**: CRUD operations for target companies with industry-based filtering
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

### Contact & Company Management

- **Contact Management**: Full CRUD operations with inline editing
- **Company Management**: Company profiles with associated contacts
- **Bulk Import**: AI-powered bulk import from Excel/CSV with:
  - Multi-sheet support
  - Duplicate detection and merging
  - AI-powered industry inference
  - Data normalization
- **Export**: Export contacts and companies to Excel/Google Sheets

### AI Target Finder

- **AI-Powered Identification**: Uses OpenAI, RAG, and Gemini to identify high-value targets
- **Multi-Industry Search**: Search across multiple industries simultaneously
- **Search Presets**: High Priority, Broad Search, C-Level Only, Custom
- **Knowledge Base Integration**: Recommendations include relevant case studies, services, and insights
- **Search History**: Save and review past searches with results
- **Bulk Creation**: Select and create multiple targets at once

### Knowledge Base

- **Query/View**: Search knowledge base content with collection filtering
- **Upload Documents**: Upload PDF and TXT files with metadata tagging
- **Scrape URLs**: Ingest website content directly into knowledge base
- **Platform Support**: Tag content by platform (VANI, Revenue Growth, GenAI Agentic, Neura360)
- **Neura360 Components**: Support for Signal, Spark, Risk, Narrative, Trend, Agents
- **Auto-Tagging**: Automatic tagging with "the-ai-company" and platform tags

### Admin Tools (Super Users & Industry Admins)

- **User Management**: Manage users, permissions, and industry assignments
- **Signatures**: Channel-specific signature management (Email, WhatsApp, LinkedIn)
- **Knowledge Base**: Query, upload, and manage knowledge base content
- **Tools**: Batch contact import with multi-threading and memory management
- **Use Case Permissions**: Grant/revoke feature access per user
- **Industry Assignment**: Multi-industry assignment for users

### Real-time Features

- **Scheduled Polling**: 4 times daily (10 AM, 12 PM, 2 PM, 5 PM) - configurable
- **Weekend Exclusion**: Automatically skips outreach on Saturdays/Sundays
- **Webhook Processing**: Real-time status updates from Resend and Twilio

## 🗂️ Project Structure

```
vani/
├── app/
│   ├── api/              # API routes (targets, outreach, dashboard, messages, knowledge_base)
│   ├── integrations/     # Third-party integrations (Resend, Twilio, OpenAI, RAG, Gemini, etc.)
│   ├── models/           # Data models (Pydantic)
│   ├── services/         # Business logic (target_identification, industry_context)
│   ├── webhooks/          # Webhook handlers
│   ├── migrations/        # Database migration SQL
│   ├── templates/         # HTML templates
│   └── static/           # CSS, JS, images
├── scripts/              # Utility scripts (seed, setup, import, permissions)
├── logs/                 # Application logs
├── .env.local           # Your credentials (not in git)
└── requirements.txt     # Python dependencies
```

## 🔧 Configuration

### Environment Variables

See `.env.example` for all required variables. Key ones:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_SERVICE_KEY` - Supabase service role key (for admin operations)
- `RESEND_API_KEY` - Resend email API key
- `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` - Twilio credentials
- `OPENAI_API_KEY` - OpenAI API key for message generation and AI Target Finder
- `RAG_API_KEY` - RAG service API key (for Knowledge Base and enhanced AI Target Finder)
- `RAG_SERVICE_URL` - RAG service URL (default: https://rag.kcube-consulting.com)
- `GEMINI_API_KEY` - Google Gemini API key (for Notebook LM integration)
- `AI_PROVIDER_PRIORITY` - AI provider priority order (default: "gemini,openai"). Options: "gemini,openai" or "openai,gemini"
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
- `targets` - Target companies and contacts
- `contacts` - Contact database with industry, company, and role information
- `companies` - Company profiles with domain and industry
- `outreach_sequences` - Multi-step outreach templates
- `outreach_activities` - Individual outreach actions
- `meetings` - Cal.com scheduled meetings
- `webhook_events` - Webhook tracking
- `signature_profiles` - Channel-specific signatures
- `ai_target_search_results` - AI Target Finder search history
- `app_users` - Application users (linked to Supabase Auth)
- `industries` - Industry definitions
- `use_cases` - Available use cases
- `user_permissions` - User permissions (many-to-many)
- `user_industries` - User-industry assignments

See `app/migrations/` for full schema.

## 🎯 Usage

### Generate and Send Outreach

1. Navigate to "Target Hit List" tab
2. Select a target company
3. Choose channel (Email or WhatsApp)
4. Click "Generate AI Message"
5. Preview the generated message
6. Edit if needed
7. Click "Send Now" to send

### AI Target Finder

1. Navigate to "AI Target Finder" tab (requires `ai_target_finder` permission)
2. Select industries (multi-select supported)
3. Choose search preset or configure custom settings
4. Set minimum seniority score and result limit
5. Click "Find Targets"
6. Review recommendations with knowledge base context
7. Select targets and click "Create Selected Targets"

### Knowledge Base

1. Navigate to "Admin" > "Knowledge Base" tab
2. **Query/View**: Search knowledge base with collection filter
3. **Upload Documents**: Drag-and-drop PDF/TXT files with metadata
4. **Scrape URLs**: Enter URL to scrape and ingest content

### Import/Export Contacts

- **Import from Excel**: Use `scripts/import_all_contacts_ai.py` for AI-powered bulk import
- **Export to Excel**: Use Contacts tab export functionality
- **Export to Google Sheets**: Use API endpoint `/api/contacts/export-sheets`

### Batch Import Contacts (Super Users)

**Via Admin Tools UI:**
1. Navigate to **Admin** > **Tools** tab
2. Enter Excel file path (e.g., `data/the_ai_company.xlsx`)
3. Configure batch size (100-500) and threads (1-16)
4. Select options (update existing, import only new, dry run)
5. Click **Run Batch Import**

**Via Command Line:**
```bash
python scripts/import_contacts_batch.py data/file.xlsx --batch-size 100 --threads 4
```

Or use AI-powered import:
```bash
python scripts/import_all_contacts_ai.py --clear
```

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
# or
python scripts/test_all_functions.py
```

### Code Formatting

```powershell
black app/
flake8 app/
```

### Useful Scripts

- `scripts/fix_user.py` - Fix or create user in app_users table
- `scripts/grant_default_permissions.py` - Grant use case permissions
- `scripts/check_user_permissions.py` - Check user permissions
- `scripts/assign_all_industries_to_super_users.py` - Assign all industries to super users
- `scripts/sync_industries_from_contacts.py` - Sync industries from contacts table
- `scripts/test_gemini_credentials.py` - Test and validate Gemini API key
- `scripts/list_gemini_models.py` - List all available Gemini models for your API key

## 📝 Notes

- Weekend exclusion is enabled by default (`EXCLUDE_WEEKENDS=true`)
- Polling times can be customized via `POLLING_TIMES` env var
- All webhooks require ngrok tunnel for local development
- OpenAI message generation uses `gpt-4o-mini` by default (configurable)
- Knowledge Base requires RAG_API_KEY for full functionality
- AI Target Finder uses Gemini by default (configurable via AI_PROVIDER_PRIORITY), with OpenAI as fallback. RAG and Gemini enhance results with knowledge base context.

## 🚨 Troubleshooting

### Database Connection Issues
- Verify Supabase URL and keys in `.env.local`
- Check if migration SQL was executed successfully
- Run `python scripts/check_env_config.py` to verify configuration

### Webhook Not Receiving Events
- Verify ngrok URL is correct and tunnel is active
- Check webhook URLs in service dashboards
- Review logs in `logs/application.log`

### Message Generation Fails
- Verify OpenAI API key is set
- Check API quota/limits
- Review error logs

### AI Target Finder Not Working
- Verify OPENAI_API_KEY is set (required)
- RAG_API_KEY is optional but recommended for enhanced results
- Check `run.py` output for feature availability status

### Gemini API Key Errors
If you see errors like "API key not valid" or "API_KEY_INVALID":

1. **Test your API key (recommended):**
   ```powershell
   python scripts/test_gemini_credentials.py
   ```

2. **Test API key directly with REST API:**
   ```powershell
   python scripts/test_gemini_api_key_direct.py
   ```
   
   This uses the same REST API endpoint as curl, so it will catch the same errors.

2. **Verify API key format:**
   - Should start with `AIza`
   - Length: ~39 characters (35-45 is acceptable)
   - Get a new key from: https://aistudio.google.com/app/apikey

3. **Common issues:**
   - API key expired or revoked → Get a new key
   - Incorrect format → Check for extra spaces or truncation
   - API key not set → Verify `GEMINI_API_KEY` in `.env.local`
   - Billing/quota issues → Check Google Cloud Console

4. **Fallback behavior:**
   - If Gemini fails, the system automatically falls back to OpenAI (if configured)
   - Check logs for which provider is being used
   - Set `AI_PROVIDER_PRIORITY=openai,gemini` to prioritize OpenAI

### Gemini Model Not Found Errors
If you see errors like "404 models/gemini-1.5-pro is not found":

1. **The system automatically tries fallback models:**
   - Default: `gemini-1.5-flash` (recommended, fast and widely available)
   - Fallbacks: `gemini-pro`, `gemini-1.5-pro-latest`, `gemini-2.0-flash-exp`
   - The system will automatically use the first available model

2. **Manually set a model:**
   ```powershell
   # In .env.local
   GEMINI_MODEL=gemini-1.5-flash  # or gemini-pro
   ```

3. **List available models:**
   ```powershell
   python scripts/list_gemini_models.py
   ```
   
   Or programmatically:
   ```python
   import google.generativeai as genai
   genai.configure(api_key='YOUR_KEY')
   for model in genai.list_models():
       if 'generateContent' in model.supported_generation_methods:
           print(model.name)
   ```

4. **Common model names:**
   - `gemini-1.5-flash` - Fast, efficient (default)
   - `gemini-pro` - Stable, widely available
   - `gemini-1.5-pro-latest` - Latest pro version (if available)

### Knowledge Base Not Working
- Verify RAG_API_KEY is set
- Check RAG_SERVICE_URL is correct (default: https://rag.kcube-consulting.com)
- Review API logs for errors

### Large Contact Import Issues
- Use Admin Tools batch import for 2000+ records
- Use `scripts/import_all_contacts_ai.py` for AI-powered import with deduplication
- Reduce batch size if memory errors occur
- Check logs in `logs/batch_import_*.log`

## 📄 License

Private project - All rights reserved

## 🔗 Related Documentation

- [VANI_FEATURES_OVERVIEW.md](VANI_FEATURES_OVERVIEW.md) - Complete features list
- [ADMIN_TOOLS_GUIDE.md](ADMIN_TOOLS_GUIDE.md) - Admin tools documentation
- [SIGNATURE_SYSTEM_GUIDE.md](SIGNATURE_SYSTEM_GUIDE.md) - Signature management guide
- [SUPER_USER_INDUSTRY_SETUP.md](SUPER_USER_INDUSTRY_SETUP.md) - Super user setup

**Last Updated**: December 2025  
**Project**: VANI (Virtual Agent Network Interface)  
**Status**: Production Ready
