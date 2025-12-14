# Scripts Update Summary

## Overview
Updated scripts to support the new use cases (`contact_management`, `company_management`) and new environment variables for AI integrations.

## Updated Scripts

### 1. `scripts/fix_user.py`
**Changes:**
- ✅ Auto-grants all default use cases when creating a new user
- ✅ Checks and grants missing permissions when fixing existing users
- ✅ Includes the new `contact_management` and `company_management` use cases

**Usage:**
```bash
# Create/fix user with auto-granted permissions
python scripts/fix_user.py user@example.com password123

# Create super user
python scripts/fix_user.py admin@example.com password123 --super-user

# Create industry admin
python scripts/fix_user.py industry@example.com password123 --industry-admin
```

### 2. `scripts/grant_default_permissions.py`
**Changes:**
- ✅ Updated examples to include `contact_management` and `company_management`
- ✅ Script already grants ALL use cases by default (no code changes needed)
- ✅ Examples now show how to grant the new use cases specifically

**Usage:**
```bash
# Grant all permissions (includes new use cases)
python scripts/grant_default_permissions.py user@example.com --grant

# Grant only the new use cases
python scripts/grant_default_permissions.py user@example.com --grant --use-cases contact_management company_management

# Grant specific use cases
python scripts/grant_default_permissions.py user@example.com --grant --use-cases analytics meetings target_management contact_management company_management
```

### 3. `scripts/confirm_user_email.py`
**Status:** ✅ No changes needed
- This script only confirms user emails in Supabase Auth
- Does not deal with permissions or use cases
- Works as-is

### 4. `run.py`
**Changes:**
- ✅ Added checks for optional AI integration environment variables:
  - `RAG_API_KEY` - RAG service API key
  - `RAG_SERVICE_URL` - RAG service URL (default: https://rag.kcube-consulting.com)
  - `GEMINI_API_KEY` - Google Gemini API key
- ✅ Shows warnings if optional variables are missing (but doesn't block startup)
- ✅ Clearly distinguishes between required and optional variables

**Environment Variables:**
- **Required:** SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, RESEND_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, OPENAI_API_KEY
- **Optional (for AI features):** RAG_API_KEY, RAG_SERVICE_URL, GEMINI_API_KEY

## New Use Cases

The following use cases were added and are now included in default permission grants:

1. **`contact_management`** - Required for accessing Contacts tab and all contact-related endpoints
2. **`company_management`** - Required for accessing Companies tab and all company-related endpoints

## Migration Required

Before using the updated scripts, ensure the new use cases exist in the database:

```sql
-- Run in Supabase SQL Editor
INSERT INTO use_cases (code, name, description) 
VALUES 
  ('contact_management', 'Contact Management', 'Manage contacts and contact data'),
  ('company_management', 'Company Management', 'Manage companies and company data')
ON CONFLICT (code) DO NOTHING;
```

Or use the migration file:
- `app/migrations/013_add_contact_company_use_cases.sql`

## Testing

After updating scripts, test with:

1. **Create a new user:**
   ```bash
   python scripts/fix_user.py test@example.com testpass123
   ```
   - Should auto-grant all use cases including the new ones

2. **Grant permissions to existing user:**
   ```bash
   python scripts/grant_default_permissions.py test@example.com --grant
   ```
   - Should grant all use cases including `contact_management` and `company_management`

3. **Check startup:**
   ```bash
   python run.py
   ```
   - Should show warnings if RAG_API_KEY or GEMINI_API_KEY are missing (but still start)
   - Should show all environment variables (required and optional)

## Notes

- All scripts use the same permission granting logic as the login flow in `app/api/auth.py`
- Super users bypass use case checks, so they don't need explicit permissions
- Industry admins still need use case permissions, but are restricted to their assigned industry
- The `grant_default_permissions.py` script can be used to grant permissions to existing users who were created before the new use cases were added
















