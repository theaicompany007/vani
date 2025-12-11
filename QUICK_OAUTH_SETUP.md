# Quick OAuth Setup Guide

## Summary

You need to configure OAuth in two places:
1. **Google Cloud Console** - Add redirect URIs to your OAuth client
2. **Supabase Dashboard** - Enable Google provider and add Client ID/Secret

## Step 1: Google Cloud Console (Using gcloud)

Since gcloud is already configured on your machine, you can:

### Option A: Use the Script (Recommended)
```bash
python scripts/configure_google_oauth.py --url https://vani.ngrok.app --project-id project-vani-480503
```

The script will show you:
- Direct link to Google Cloud Console
- Exact URIs to add
- Instructions for Supabase configuration

### Option B: Manual Configuration

1. **Open Google Cloud Console:**
   ```
   https://console.cloud.google.com/apis/credentials?project=project-vani-480503
   ```

2. **Find or Create OAuth Client:**
   - If you have one: Click on it to edit
   - If not: Click "Create Credentials" > "OAuth client ID" > "Web application"

3. **Add Authorized Redirect URIs:**
   Add this **CRITICAL** URI first:
   ```
   https://rkntrsprfcypwikshvsf.supabase.co/auth/v1/callback
   ```
   
   Then add these additional URIs:
   ```
   https://vani.ngrok.app/login
   https://vani.ngrok.app/command-center
   https://vani.ngrok.app/api/auth/callback
   http://localhost:5000/login
   http://localhost:5000/command-center
   ```

4. **Save and Copy Credentials:**
   - Click "Save"
   - Copy the **Client ID** (looks like: `123456789-abc.apps.googleusercontent.com`)
   - Click "Show" to reveal and copy the **Client Secret**

## Step 2: Supabase Dashboard

1. **Configure URL Settings:**
   ```
   https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/url-configuration
   ```
   - Set **Site URL**: `https://vani.ngrok.app`
   - Add **Redirect URLs**:
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
   ```
   https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/providers
   ```
   - Click on "Google" provider
   - Enable it
   - Paste the **Client ID** and **Client Secret** from Step 1
   - Click "Save"

## Step 3: Test

1. Start your app: `python run.py`
2. Navigate to login page
3. Click "Sign in with Google"
4. Complete authentication
5. You should be redirected back to your app

## Troubleshooting

**"redirect_uri_mismatch" error:**
- Ensure the Supabase callback URI in Google Console is **exactly**: 
  `https://rkntrsprfcypwikshvsf.supabase.co/auth/v1/callback`
- No trailing slashes, exact match required

**"Email not confirmed" error:**
- Run: `python scripts/confirm_user_email.py user@example.com`

**OAuth provider not working:**
- Verify Google provider is enabled in Supabase
- Check Client ID and Secret are correct
- Ensure redirect URIs match exactly

## Quick Links

- **Google Cloud Console**: https://console.cloud.google.com/apis/credentials?project=project-vani-480503
- **Supabase URL Config**: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/url-configuration
- **Supabase Providers**: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/providers





