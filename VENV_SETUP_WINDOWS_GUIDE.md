# VANI App - Windows Virtual Environment Setup Guide

## ✅ Setup Complete!

Your virtual environment has been successfully set up with all dependencies installed.

## What Was Fixed

### Problem 1: psycopg2-binary Build Error
**Error**: `Microsoft Visual C++ 14.0 or greater is required`

**Solution**: The setup script automatically installed psycopg2-binary using pre-built wheels, avoiding the need for Visual C++ Build Tools.

### Problem 2: Missing Dependencies
**Error**: `ModuleNotFoundError: No module named 'dotenv'`

**Solution**: All required dependencies from `requirements.txt` have been installed successfully.

## How to Use Your Virtual Environment

### Activate the Virtual Environment

**PowerShell (Recommended):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

### Run the VANI Application

After activating the virtual environment:

```powershell
python run.py
```

Or use the automated batch file:

```cmd
vani.bat
```

### Deactivate the Virtual Environment

When you're done:
```powershell
deactivate
```

## Quick Setup Scripts Created

Two helper scripts have been created for future use:

1. **`setup_venv_windows.bat`** - Batch file for quick setup
2. **`setup_venv_windows_alternative.py`** - Python-based setup (used today)

To re-setup the environment in the future, simply run:

```powershell
python setup_venv_windows_alternative.py
```

## Installed Packages Summary

Core packages installed:
- ✅ Flask 3.0.0 (Web framework)
- ✅ Supabase 2.27.0 (Database client)
- ✅ psycopg2-binary 2.9.9 (PostgreSQL adapter)
- ✅ python-dotenv 1.0.0 (Environment variables)
- ✅ OpenAI 1.12.0 (AI integration)
- ✅ Twilio 9.3.0 (WhatsApp)
- ✅ Resend 2.0.0 (Email)
- ✅ Google APIs (Sheets, Gemini)
- ✅ And 100+ other dependencies

## Python Version

Your environment is using **Python 3.13.7**, which is compatible with all VANI requirements.

## Troubleshooting

### If you get PowerShell execution policy errors:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### If psycopg2-binary fails in the future:

The setup script tries multiple versions automatically. If all fail, you can:

1. Install Microsoft C++ Build Tools:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/

2. Or use psycopg3 (modify requirements.txt)

## Next Steps

1. **Configure Environment Variables**: Copy `.env.example` to `.env.local` and fill in your API keys
2. **Setup Database**: Run `python do_setup.py` to initialize Supabase tables
3. **Start Application**: Use `python run.py` or `vani.bat`

## Support

For issues or questions, refer to:
- `LOCAL_SETUP_GUIDE.md`
- `PROJECT_VANI_COMPREHENSIVE_USER_GUIDE.md`
- `QUICK_START.md`

---

**Setup Date**: December 17, 2025  
**Setup Method**: Automated Python script with Windows-specific workarounds

