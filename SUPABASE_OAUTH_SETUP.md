# Supabase OAuth URL Configuration Guide

This guide helps you configure Supabase for Google OAuth authentication.

## Quick Setup

### Automatic Configuration (Recommended)

If you have `SUPABASE_ACCESS_TOKEN` set in `.env.local`:

```bash
python scripts/configure_supabase_oauth.py
```

Or specify URL manually:

```bash
python scripts/configure_supabase_oauth.py --url https://vani.ngrok.app
```

### Manual Configuration

1. **Open Supabase Dashboard:**
   - Go to: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/url-configuration

2. **Set Site URL:**
   - Enter your application URL (e.g., `https://vani.ngrok.app`)

3. **Add Redirect URLs:**
   Add these URLs (one per line):
   ```
   https://vani.ngrok.app
   https://vani.ngrok.app/login
   https://vani.ngrok.app/command-center
   https://vani.ngrok.app/api/auth/callback
   http://localhost:5000
   http://localhost:5000/login
   http://localhost:5000/command-center
   ```

4. **Enable Google Provider:**
   - Go to: https://supabase.com/dashboard/project/rkntrsprfcypwikshvsf/auth/providers
   - Enable "Google" provider
   - Add your Google OAuth Client ID and Client Secret

5. **Configure Google Cloud Console:**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Find your OAuth 2.0 Client ID
   - Add Authorized redirect URI:
     ```
     https://rkntrsprfcypwikshvsf.supabase.co/auth/v1/callback
     ```

## Environment Variables

Add to `.env.local`:

```bash
# Supabase OAuth Configuration
SUPABASE_ACCESS_TOKEN=sbp_your_token_here  # Optional, for automatic updates
WEBHOOK_BASE_URL=https://vani.ngrok.app     # Your app URL
```

## Getting Supabase Access Token

1. Go to: https://supabase.com/dashboard/account/tokens
2. Create a new Personal Access Token
3. Add to `.env.local` as `SUPABASE_ACCESS_TOKEN`

## Testing OAuth

1. Start your Flask app: `python run.py`
2. Navigate to login page
3. Click "Sign in with Google"
4. Complete OAuth flow

## Troubleshooting

### "redirect_uri_mismatch" Error

- Check that all redirect URLs are added in Supabase Dashboard
- Verify Site URL matches your application URL
- Ensure Google Cloud Console has the correct callback URL

### OAuth Provider Not Enabled

- Go to Supabase Dashboard → Authentication → Providers
- Enable Google provider
- Verify Client ID and Secret are correct

### Local Development

- Always include `http://localhost:5000` in redirect URLs
- Use ngrok for testing OAuth with external services





