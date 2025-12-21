"""Check .env.local configuration and report missing keys"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

# Required environment variables based on codebase
REQUIRED_VARS = {
    # Flask
    'FLASK_HOST': '127.0.0.1',
    'FLASK_PORT': '5000',
    'SECRET_KEY': None,
    'FLASK_ENV': 'development',
    
    # Supabase
    'SUPABASE_URL': None,
    'SUPABASE_KEY': None,
    'SUPABASE_SERVICE_KEY': None,
    'SUPABASE_CONNECTION': None,  # Direct Postgres connection string
    'SUPABASE_DB_PASSWORD': None,  # Database password
    
    # Resend (Email)
    'RESEND_API_KEY': None,
    'RESEND_FROM_EMAIL': None,
    'RESEND_FROM_NAME': None,
    
    # Twilio (WhatsApp)
    'TWILIO_ACCOUNT_SID': None,
    'TWILIO_AUTH_TOKEN': None,
    'TWILIO_WHATSAPP_NUMBER': None,
    'TWILIO_PHONE_NUMBER': None,
    
    # Cal.com (Meetings)
    'CAL_COM_API_KEY': None,
    'CAL_COM_WEBHOOK_SECRET': None,  # Note: You have CAL_COM_WEBHOOK_SECRET_PROD
    'CAL_COM_USERNAME': None,
    'CAL_COM_BASE_URL': 'https://api.cal.com',
    
    # Google Sheets
    'GOOGLE_SHEETS_CREDENTIALS_PATH': None,
    'GOOGLE_SHEETS_SPREADSHEET_ID': None,
    'GOOGLE_SHEETS_TARGETS_SHEET_NAME': 'Targets',
    'GOOGLE_SHEETS_ACTIVITIES_SHEET_NAME': 'Activities',
    
    # Webhooks
    'WEBHOOK_BASE_URL': None,  # https://vani.ngrok.app
    'WEBHOOK_SECRET': None,  # For webhook validation
    
    # Notifications
    'NOTIFICATION_EMAIL': None,
    'NOTIFICATION_WHATSAPP': None,
    
    # Polling
    'POLLING_TIMES': '10,12,14,17',
    'EXCLUDE_WEEKENDS': 'true',
    
    # LinkedIn (Optional)
    'LINKEDIN_CLIENT_ID': None,
    'LINKEDIN_CLIENT_SECRET': None,
    'LINKEDIN_REDIRECT_URI': None,
    
    # OpenAI
    'OPENAI_API_KEY': None,
    'OPENAI_MODEL': 'gpt-4o-mini',  # Optional, has default
    
    # RAG / Knowledge Base
    'RAG_API_KEY': None,
    'RAG_SERVICE_URL': 'https://rag.theaicompany.co',
    
    # Google Drive (Optional - for Admin → Google Drive sync)
    'GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON': None,
    'GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH': None,
    
    # Gemini (Optional - for AI Target Finder)
    'GEMINI_API_KEY': None,
    
    # App
    'APP_NAME': 'Project VANI Outreach Command Center',
    'APP_URL': 'http://localhost:5000',
    'DEBUG': 'True',
}

def check_configuration():
    """Check which variables are set and which are missing"""
    print("\n" + "="*70)
    print("  ENVIRONMENT CONFIGURATION CHECK")
    print("="*70 + "\n")
    
    missing_required = []
    missing_optional = []
    present = []
    aliases_found = {}
    
    # Check each variable
    for var, default in REQUIRED_VARS.items():
        value = os.getenv(var)
        
        # Check for aliases
        if var == 'CAL_COM_WEBHOOK_SECRET':
            # Check if they have the PROD version
            prod_value = os.getenv('CAL_COM_WEBHOOK_SECRET_PROD')
            if prod_value:
                if not value:
                    aliases_found[var] = 'CAL_COM_WEBHOOK_SECRET_PROD'
                value = prod_value  # Use PROD value for validation
        
        if value:
            present.append(var)
        else:
            if default is None:
                missing_required.append(var)
            else:
                missing_optional.append((var, default))
    
    # Print results
    print("✅ PRESENT VARIABLES:")
    print("-" * 70)
    for var in sorted(present):
        value = os.getenv(var)
        if var in ['SECRET_KEY', 'SUPABASE_KEY', 'SUPABASE_SERVICE_KEY', 'TWILIO_AUTH_TOKEN', 
                   'RESEND_API_KEY', 'CAL_COM_API_KEY', 'WEBHOOK_SECRET', 'OPENAI_API_KEY',
                   'SUPABASE_DB_PASSWORD', 'LINKEDIN_CLIENT_SECRET', 'RAG_API_KEY', 
                   'GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON', 'GEMINI_API_KEY']:
            # Mask sensitive values
            if value:
                masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                print(f"  {var:35} = {masked}")
            else:
                print(f"  {var:35} = (not set)")
        else:
            print(f"  {var:35} = {value}")
    
    if aliases_found:
        print("\n⚠️  ALIASES FOUND (consider renaming for consistency):")
        print("-" * 70)
        for var, alias in aliases_found.items():
            print(f"  {var:35} → Found as: {alias}")
            print(f"    Recommendation: Add '{var}' with same value, or update code to use '{alias}'")
    
    if missing_required:
        print("\n❌ MISSING REQUIRED VARIABLES:")
        print("-" * 70)
        for var in sorted(missing_required):
            print(f"  {var}")
    
    if missing_optional:
        print("\n⚠️  MISSING OPTIONAL VARIABLES (will use defaults):")
        print("-" * 70)
        for var, default in sorted(missing_optional):
            print(f"  {var:35} (default: {default})")
    
    # Webhook configuration check
    print("\n" + "="*70)
    print("  WEBHOOK CONFIGURATION CHECK")
    print("="*70 + "\n")
    
    webhook_base = os.getenv('WEBHOOK_BASE_URL')
    webhook_secret = os.getenv('WEBHOOK_SECRET')
    
    if webhook_base and webhook_secret:
        print("✅ Webhook base URL configured:")
        print(f"   {webhook_base}")
        print("\n📋 Webhook endpoints to configure:")
        print(f"   1. Resend:    {webhook_base}/api/webhooks/resend")
        print(f"   2. Twilio:    {webhook_base}/api/webhooks/twilio")
        print(f"   3. Cal.com:   {webhook_base}/api/webhooks/cal-com")
        print("\n💡 Configure these URLs in:")
        print("   - Resend Dashboard: https://resend.com/webhooks")
        print("   - Twilio Console: https://console.twilio.com/")
        print("   - Cal.com Settings: https://cal.com/settings/developer/webhooks")
    else:
        print("⚠️  Webhook configuration incomplete:")
        if not webhook_base:
            print("   - WEBHOOK_BASE_URL is missing")
        if not webhook_secret:
            print("   - WEBHOOK_SECRET is missing")
    
    # Google Drive configuration check
    print("\n" + "="*70)
    print("  GOOGLE DRIVE CONFIGURATION CHECK")
    print("="*70 + "\n")
    
    google_drive_json = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON')
    google_drive_path = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH')
    
    if google_drive_json or google_drive_path:
        print("✅ Google Drive integration configured:")
        if google_drive_json:
            print("   - Using GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON (embedded JSON)")
        if google_drive_path:
            path = Path(google_drive_path)
            if path.exists():
                print(f"   - Using GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH: {google_drive_path}")
                print("     ✅ Service account file exists")
            else:
                print(f"   - Using GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH: {google_drive_path}")
                print("     ❌ Service account file NOT FOUND")
        print("\n💡 Google Drive features:")
        print("   - Admin → Google Drive tab available (Super Users only)")
        print("   - Browse and sync files from Google Drive to RAG knowledge base")
        print("   - See GOOGLE_DRIVE_SETUP.md for setup instructions")
    else:
        print("⚠️  Google Drive integration not configured (optional):")
        print("   - GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON or GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH missing")
        print("   - Google Drive sync feature will not be available")
        print("   - See GOOGLE_DRIVE_SETUP.md for setup instructions")
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print(f"✅ Configured: {len(present)}/{len(REQUIRED_VARS)} variables")
    print(f"❌ Missing required: {len(missing_required)}")
    print(f"⚠️  Missing optional: {len(missing_optional)}")
    
    if missing_required:
        print("\n⚠️  ACTION REQUIRED: Add missing required variables to .env.local")
        return False
    else:
        print("\n✅ All required variables are configured!")
        return True


if __name__ == '__main__':
    check_configuration()

