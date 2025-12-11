# User Permissions Management Guide

## Overview
The permission system controls access to different features (use cases) in the application. Users need explicit permissions to access features like Analytics, Meetings, Target Management, etc.

## Quick Fix for Existing Users

### Grant All Permissions
```bash
python scripts/grant_default_permissions.py vikas.goel@blackngreen.com --grant
```

### Revoke All Permissions
```bash
python scripts/grant_default_permissions.py vikas.goel@blackngreen.com --revoke
```

### Toggle Permissions (Grant if missing, Revoke if exists)
```bash
python scripts/grant_default_permissions.py vikas.goel@blackngreen.com --toggle
```

## Grant/Revoke Specific Use Cases

### Grant Specific Permissions
```bash
python scripts/grant_default_permissions.py vikas.goel@blackngreen.com --grant --use-cases analytics meetings target_management contact_management company_management
```

### Revoke Specific Permissions
```bash
python scripts/grant_default_permissions.py vikas.goel@blackngreen.com --revoke --use-cases analytics
```

## Available Use Cases

- `analytics` - View dashboard analytics and engagement metrics
- `meetings` - Schedule and manage meetings via Cal.com
- `target_management` - Add, edit, and manage target companies
- `outreach` - Send outreach messages via Email, WhatsApp, LinkedIn
- `pitch_presentation` - Generate and send AI-powered pitch presentations
- `sheets_import_export` - Import and export data from Google Sheets
- `ai_message_generation` - Generate AI-powered outreach messages
- `contact_management` - View, add, edit, and manage contacts
- `company_management` - View, add, edit, and manage companies

## Command Line Options

```
python scripts/grant_default_permissions.py <email> [OPTIONS]

Options:
  --grant          Grant permissions (default if no action specified)
  --revoke         Revoke permissions
  --toggle         Toggle permissions (grant if missing, revoke if exists)
  --use-cases      Specific use case codes to manage (default: all use cases)
  -h, --help       Show help message
```

## Examples

```bash
# Grant all permissions (default behavior)
python scripts/grant_default_permissions.py user@example.com

# Grant all permissions explicitly
python scripts/grant_default_permissions.py user@example.com --grant

# Revoke all permissions
python scripts/grant_default_permissions.py user@example.com --revoke

# Toggle all permissions
python scripts/grant_default_permissions.py user@example.com --toggle

# Grant only analytics and meetings
python scripts/grant_default_permissions.py user@example.com --grant --use-cases analytics meetings

# Revoke only analytics
python scripts/grant_default_permissions.py user@example.com --revoke --use-cases analytics
```

## Auto-Grant for New Users

New users automatically receive all permissions when they first log in. This only applies to users created after the update.

## Super Users

Super users (`is_super_user = true`) bypass all permission checks and have access to everything automatically.

## Troubleshooting

### Error: "User not found"
- Make sure the user exists in the `app_users` table
- Check the email spelling

### Error: "No use cases found"
- Run the migration `003_auth_permissions.sql` to create use cases
- Check that the `use_cases` table exists and has data

### Permission still denied after granting
- User may need to log out and log back in
- Check that the permission was actually created in `user_permissions` table
- Verify the use case code matches exactly (case-sensitive)


