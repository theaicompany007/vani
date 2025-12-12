# Google OAuth Setup Guide

## Quick Setup

### Step 1: Save Credentials (One-time)

```bash
python scripts/save_oauth_credentials.py \
  --client-id 489080562480-p743ihbieu2c9djr57dts19843e1isc5.apps.googleusercontent.com \
  --client-secret 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
```

This saves the credentials to `.local.env` for future use.

### Step 2: Configure Redirect URIs

```bash
python scripts/configure_google_oauth_client.py --url https://vani.ngrok.app
```

The script will:
- Load credentials from `.local.env` automatically
- Show you the exact URIs to configure
- Provide direct links to Google Cloud Console

## Manual Configuration

If you prefer to configure manually:

### 1. Google Cloud Console

1. **Open:** https://console.cloud.google.com/apis/credentials?project=project-vani-480503

2. **Find your OAuth Client:**
   - Client ID: `489080562480-p743ihbieu2c9djr57dts19843e1isc5.apps.googleusercontent.com`
   - Click on it to edit

3. **Add Authorized Redirect URIs:**
   ```
   🔴 CRITICAL: https://rkntrsprfcypwikshvsf.supabase.co/auth/v1/callback
   ✅ https://vani.ngrok.app/login
   ✅ https://vani.ngrok.app/command-center
   ✅ https://vani.ngrok.app/api/auth/callback
   ✅ http://localhost:5000/login
   ✅ http://localhost:5000/command-center
   ```

4. **Click "Save"**

### 2. Supabase Dashboard

1. **Open:** https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/providers

2. **Enable Google Provider:**
   - Click on "Google"
   - Enable it
   - **Client ID:** `489080562480-p743ihbieu2c9djr57dts19843e1isc5.apps.googleusercontent.com`
   - **Client Secret:** `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`
   - Click "Save"

## Environment Variables

After running `save_oauth_credentials.py`, your `.local.env` will have:

```bash
# Google OAuth 2.0 Client ID for Supabase authentication
GOOGLE_OAUTH_CLIENT_ID=489080562480-p743ihbieu2c9djr57dts19843e1isc5.apps.googleusercontent.com

# Google OAuth 2.0 Client Secret for Supabase authentication
GOOGLE_OAUTH_CLIENT_SECRET=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
```

## Automatic Configuration (Optional)

To enable automatic API updates, authenticate with gcloud:

```bash
gcloud auth login theaicompany007@gmail.com
gcloud auth application-default login
gcloud config set project project-vani-480503
```

Then the script can automatically update redirect URIs via API.

## Verification

After configuration:

1. Start your app: `python run.py`
2. Navigate to login page
3. Click "Sign in with Google"
4. You should be redirected to Google for authentication
5. After authentication, you'll be redirected back to your app

## Troubleshooting

**"redirect_uri_mismatch" error:**
- Ensure the Supabase callback URI is **exactly**: 
  `https://rkntrsprfcypwikshvsf.supabase.co/auth/v1/callback`
- Check for trailing slashes or protocol mismatches

**OAuth provider not working:**
- Verify Google provider is enabled in Supabase
- Check Client ID and Secret are correct
- Ensure redirect URIs match exactly in both Google Console and Supabase

## Quick Reference

- **Google Cloud Console:** https://console.cloud.google.com/apis/credentials?project=project-vani-480503
- **Supabase Providers:** https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/providers
- **Supabase URL Config:** https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/url-configuration







