# VANI Quick Reference Guide

## 🚀 Quick Start

```bash
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure
Copy .env.example to .env.local and fill in credentials

# Run
python run.py
```

Access: http://localhost:5000/command-center

## 📋 Key Features

### For Regular Users
- **Target Management**: Manage FMCG targets
- **AI Messages**: Generate and send personalized messages
- **Pitch Presentations**: Create and send AI-powered pitches
- **Analytics**: View engagement metrics
- **Contacts & Companies**: Manage contacts and companies

### For Super Users
- **User Management**: Manage users and permissions
- **Admin Tools**: Batch import, system monitoring
- **Industry Management**: Create and manage industries
- See [SUPER_USER_GUIDE.md](SUPER_USER_GUIDE.md) and [ADMIN_TOOLS_GUIDE.md](ADMIN_TOOLS_GUIDE.md)

## 🔧 Common Tasks

### Import Contacts (UI)
1. Go to **Contacts** tab
2. Click **Import Excel**
3. Select file
4. Map columns
5. Preview and import

### Batch Import Contacts (Super Users)
```bash
# Command line
python scripts/import_contacts_batch.py data/file.xlsx --batch-size 100 --threads 4

# Or via Admin Tools tab
1. Click "Admin Tools" tab
2. Enter file path: data/file.xlsx
3. Configure settings
4. Click "Run Batch Import"
```

### Generate Pitch
1. Go to **Pitch Presentation** tab
2. Select target
3. Click **Generate Pitch**
4. Review and send

### Send Outreach
1. Go to **Target Hit List** tab
2. Select target
3. Choose channel (Email/WhatsApp)
4. Generate AI message
5. Review and send

## 📁 Important Files

- `run.py` - Main startup script
- `app/templates/command_center.html` - Main UI
- `scripts/import_contacts_batch.py` - Batch import script
- `app/api/admin.py` - Admin API endpoints
- `.env.local` - Your credentials (not in git)

## 🔗 Documentation

- [README.md](README.md) - Main documentation
- [ADMIN_TOOLS_GUIDE.md](ADMIN_TOOLS_GUIDE.md) - Admin tools guide
- [SUPER_USER_GUIDE.md](SUPER_USER_GUIDE.md) - Super user guide
- [VANI_FEATURES_OVERVIEW.md](VANI_FEATURES_OVERVIEW.md) - Complete features list

## 🛠️ Troubleshooting

### Can't Login
- Check Supabase credentials in `.env.local`
- Verify user exists in `app_users` table

### Import Fails
- For large files (2000+), use Admin Tools batch import
- Check Excel file format
- Review logs in `logs/` directory

### Webhooks Not Working
- Verify ngrok is running
- Check webhook URLs in service dashboards
- Review `logs/application.log`

## 📞 Support

For issues:
1. Check relevant log files in `logs/` directory
2. Review error messages in UI
3. Check documentation files
4. Verify environment variables in `.env.local`
