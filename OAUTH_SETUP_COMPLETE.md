# Complete OAuth Setup Guide

This guide covers setting up Google OAuth for Supabase authentication using gcloud SDK.

## Prerequisites

1. **gcloud SDK installed and configured**
   ```bash
   gcloud --version
   gcloud auth list
   ```

2. **Google Cloud Project**
   - Project ID: `project-vani-480503`
   - Account: `theaicompany007@gmail.com`

3. **Supabase Project**
   - Project Reference: `rkntrsprfcypwikshvsf`
   - URL: `https://rkntrsprfcypwikshvsf.supabase.co`

## Step 1: Configure Google Cloud OAuth Client

### Option A: Using gcloud SDK (Recommended)

1. **Set the correct account and project:**
   ```bash
   gcloud config set account theaicompany007@gmail.com
   gcloud config set project project-vani-480503
   ```

2. **Get your OAuth client credentials:**
   - Open: https://console.cloud.google.com/apis/credentials?project=project-vani-480503
   - Find your OAuth 2.0 Client ID (or create a new one)
   - Note the Client ID and Client Secret

3. **Configure redirect URIs:**
   - Click on your OAuth 2.0 Client ID
   - Under "Authorized redirect URIs", add:
     ```
     https://rkntrsprfcypwikshvsf.supabase.co/auth/v1/callback
     ```
   - Click "Save"

### Option B: Using the Script

Run the configuration script:
```bash
python scripts/configure_google_oauth.py --url https://vani.ngrok.app --project-id project-vani-480503
```

The script will:
- List available OAuth clients
- Provide direct links to configure redirect URIs
- Show the exact URIs to add

## Step 2: Configure Supabase OAuth

### Option A: Using the Script

```bash
python scripts/configure_supabase_oauth.py --url https://vani.ngrok.app
```

### Option B: Manual Configuration

1. **Configure Site URL and Redirect URLs:**
   - Open: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/url-configuration
   - Set **Site URL** to: `https://vani.ngrok.app`
   - Add **Redirect URLs** (one per line):
     ```
     http://localhost:5000
     http://localhost:5000/command-center
     http://localhost:5000/login
     https://vani.ngrok.app
     https://vani.ngrok.app/api/auth/callback
     https://vani.ngrok.app/command-center
     https://vani.ngrok.app/login
     ```
   - Click "Save"

2. **Enable Google Provider:**
   - Open: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/providers
   - Click on "Google" provider
   - Enable it
   - Enter:
     - **Client ID**: (from Google Cloud Console)
     - **Client Secret**: (from Google Cloud Console)
   - Click "Save"

## Step 3: Verify Configuration

### Test Google OAuth Login

1. Start your application:
   ```bash
   python run.py
   ```

2. Navigate to the login page
3. Click "Sign in with Google"
4. You should be redirected to Google for authentication
5. After authentication, you should be redirected back to your app

### Troubleshooting

**Issue: "redirect_uri_mismatch" error**
- Ensure the redirect URI in Google Console exactly matches: `https://rkntrsprfcypwikshvsf.supabase.co/auth/v1/callback`
- Check for trailing slashes or protocol mismatches

**Issue: "Email not confirmed" error**
- The app should auto-confirm emails, but if not:
  ```bash
  python scripts/confirm_user_email.py user@example.com
  ```

**Issue: OAuth provider not enabled**
- Verify Google provider is enabled in Supabase Dashboard
- Check that Client ID and Secret are correct

## Environment Variables

Ensure these are set in `.env.local`:

```bash
# Supabase
SUPABASE_URL=https://rkntrsprfcypwikshvsf.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Application
WEBHOOK_BASE_URL=https://vani.ngrok.app  # or your production URL
```

## Quick Reference

### Google Cloud Console
- **Credentials**: https://console.cloud.google.com/apis/credentials?project=project-vani-480503
- **OAuth Consent Screen**: https://console.cloud.google.com/apis/credentials/consent?project=project-vani-480503

### Supabase Dashboard
- **URL Configuration**: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/url-configuration
- **Providers**: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/providers
- **Users**: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/users

## Next Steps

After OAuth is configured:
1. Test login with Google
2. Verify user creation in Supabase
3. Check that `app_users` record is created automatically
4. Test permissions and access control

















