# Setting Up Supabase Personal Access Token

The Supabase Management API requires a **personal access token**, not the service role key.

## Get Your Personal Access Token

1. **Go to Supabase Dashboard:**
   ```
   https://supabase.com/dashboard/account/tokens
   ```

2. **Create a new token:**
   - Click "Generate new token"
   - Give it a name (e.g., "OAuth Configuration")
   - Copy the token immediately (you won't see it again!)

3. **Add to your `.local.env` file:**
   ```bash
   SUPABASE_ACCESS_TOKEN=your_personal_access_token_here
   ```

## Important Notes

- **Personal Access Token** ≠ **Service Role Key**
  - `SUPABASE_SERVICE_ROLE_KEY` - Used for REST API operations
  - `SUPABASE_ACCESS_TOKEN` - Used for Management API (project configuration)

- The token is used for:
  - Updating OAuth URL configuration
  - Managing project settings via Management API
  - Other administrative tasks

- Keep it secure! Don't commit it to version control.

## Verify It Works

After adding the token, run:
```bash
python scripts/configure_supabase_oauth.py --url https://vani.ngrok.app
```

If the token is valid, you should see:
```
✅ Successfully updated via Management API!
```

If you see "Unauthorized", the token might be:
- Invalid or expired
- Missing required permissions
- Not a personal access token (you might have used service role key)

## Alternative: Manual Configuration

If you prefer not to use the Management API, you can always configure OAuth URLs manually in the Supabase Dashboard. The script will provide step-by-step instructions if the API update fails.







