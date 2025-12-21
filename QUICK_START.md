# Project VANI - Quick Start Guide

## 🚀 One-Command Startup

```powershell
cd C:\Raaj\kcube_consulting_labs\vani
.\venv\Scripts\Activate.ps1
python run.py
```

**That's it!** The script handles everything automatically.

---

## 📋 What `run.py` Does

1. **Kills** existing Flask/ngrok processes
2. **Checks** all environment variables from `.env.local`
3. **Verifies** database connection
4. **Starts** Flask server on port 5000
5. **Starts** ngrok tunnel automatically
6. **Displays** public URL and webhook endpoints

---

## 🌐 Access Points

After running `python run.py`, you'll see:

```
PUBLIC URL (Ngrok): https://vani.ngrok.app
Command Center:     https://vani.ngrok.app/command-center

Webhook Endpoints:
  Resend:    https://vani.ngrok.app/api/webhooks/resend
  Twilio:    https://vani.ngrok.app/api/webhooks/twilio
  Cal.com:   https://vani.ngrok.app/api/webhooks/cal-com
```

**Open the Command Center URL in your browser!**

---

## 🎯 Using the Command Center

### 1. View Targets
- Click **"Target Hit List"** tab
- See all FMCG companies
- Click any target for details

### 2. Send Outreach
1. Select a target
2. Choose channel: **Email**, **WhatsApp**, or **LinkedIn**
3. Click **"Generate AI Message"**
4. Preview the message
5. Edit if needed
6. Click **"Send Now"**

### 3. Track Results
- View sent messages
- See engagement (opens, clicks, replies)
- Check meeting schedules

---

## ⚙️ First-Time Setup

### 1. Create Database Tables
```powershell
python scripts\create_database_tables_direct.py
```

### 2. Seed Initial Targets (Optional)
```powershell
python scripts\seed_targets.py
```

### 3. Configure Webhooks (Optional)
```powershell
python scripts\configure_webhooks.py
```

---

## 🔧 Troubleshooting

### Server Won't Start
- Check: `.env.local` has all required keys
- Run: `python scripts\check_env_config.py`

### Ngrok Error (ERR_NGROK_8012)
- **Fixed!** `run.py` now verifies Flask is ready before starting ngrok
- Flask must be accessible on 127.0.0.1:5000

### Database Error
- Run: `python scripts\create_database_tables_direct.py`
- Check: `SUPABASE_CONNECTION` in `.env.local`

---

## 📚 Full Documentation

See `PROJECT_VANI_EXECUTION_GUIDE.md` for:
- Complete setup instructions
- All configuration options
- API documentation
- Troubleshooting guide
- Feature list

---

## ✅ Quick Checklist

- [ ] `.env.local` configured
- [ ] Virtual environment activated
- [ ] Database tables created
- [ ] Run: `python run.py`
- [ ] Open command center URL
- [ ] (Optional) Configure Google Drive sync - see `GOOGLE_DRIVE_SETUP.md`

**You're ready to go!** 🎉

## 🔧 Optional Features

### Google Drive Sync (Super Users)
- Configure Google Service Account (see `GOOGLE_DRIVE_SETUP.md`)
- Add `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` or `GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH` to `.env.local`
- Access via: Admin → Google Drive tab

