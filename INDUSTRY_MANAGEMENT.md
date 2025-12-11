# Industry Management Guide

This guide covers managing industries for users, including multiple industry assignment and default industry selection.

## Overview

Users can now be assigned to multiple industries with one set as the default. The default industry automatically loads when accessing Pitch Presentation and Target Hit List pages.

## Database Schema

### `user_industries` Table
Junction table for many-to-many relationship between users and industries.

- `user_id` - References `app_users.id`
- `industry_id` - References `industries.id`
- `is_default` - Boolean flag (only one per user)
- `assigned_at` - Timestamp
- `assigned_by` - User who assigned (optional)

### `app_users` Table Updates
- `default_industry_id` - Quick reference to default industry (UUID)

## Using the UI

### Assign Industries to a User

1. Go to **User Mgmt.** tab (super users only)
2. Click **"Manage Industries"** button for a user
3. In the search box:
   - Click to see all available industries
   - Type to filter industries
   - Type `*` to show all industries
4. Click an industry to add it
5. Click **"Set Default"** to make an industry the default
6. Click **"Remove"** to unassign an industry

### Set Default Industry

The default industry:
- Automatically loads on page load
- Is used for Pitch Presentation and Target Hit List
- Can be changed by clicking "Set Default" on any assigned industry

## Using Scripts

### Assign Single Industry (Legacy Method)

```bash
python scripts/set_industry_admin.py user@example.com "FMCG"
```

This sets the user as industry admin and assigns them to one industry.

### Assign Multiple Industries

```bash
# Assign first industry as default
python scripts/assign_industry_to_user.py user@example.com "FMCG" --default

# Assign additional industries
python scripts/assign_industry_to_user.py user@example.com "Food & Beverages"
python scripts/assign_industry_to_user.py user@example.com "Technology"
```

### Set Default Industry

```bash
# If industry already assigned, update to default
python scripts/assign_industry_to_user.py user@example.com "FMCG" --default
```

## API Endpoints

### Get User Industries
```
GET /api/user-industries/<user_id>
```

Returns:
```json
{
  "success": true,
  "industries": [
    {
      "id": "uuid",
      "name": "FMCG",
      "is_default": true,
      "assigned_at": "2025-12-09T..."
    }
  ],
  "default_industry_id": "uuid"
}
```

### Assign Industry
```
POST /api/user-industries/<user_id>
Body: {
  "industry_id": "uuid",
  "is_default": false
}
```

### Remove Industry
```
DELETE /api/user-industries/<user_id>/<industry_id>
```

### Set Default Industry
```
POST /api/user-industries/<user_id>/set-default
Body: {
  "industry_id": "uuid"
}
```

## Migration

Run migration 014 to enable multiple industry assignment:

```bash
python scripts/run_migration_014.py
```

Or manually in Supabase SQL Editor:
- Copy contents of `app/migrations/014_user_industries_and_default.sql`
- Paste and execute in Supabase SQL Editor

## Behavior

### Industry Filtering

- **Super Users**: Can see all industries, can filter by any industry
- **Industry Admins**: Can only see/switch to their assigned industries
- **Regular Users**: See data filtered by their active/default industry

### Default Industry Priority

1. `default_industry_id` (highest priority)
2. `active_industry_id`
3. `industry_id` (legacy)

### Industry Switching

When a user switches industries:
- The selected industry becomes `active_industry_id`
- If no `default_industry_id` is set, it also becomes the default
- Industry admins can only switch to their assigned industries

## Troubleshooting

### "user_industries table not found" Error

Run migration 014:
```bash
python scripts/run_migration_014.py
```

### User Can't Switch Industries

Check:
1. Is user an industry admin? They can only switch to assigned industries
2. Are industries assigned? Use "Manage Industries" to assign
3. Is migration 014 run? Table must exist

### Default Industry Not Loading

Check:
1. Is `default_industry_id` set? Use "Set Default" button
2. Is industry still assigned? Check "Manage Industries"
3. Refresh the page after setting default

## Best Practices

1. **Set Default Early**: Assign a default industry when setting up users
2. **Use Multiple Industries**: Assign users to all industries they work with
3. **Industry Admins**: Assign them to their specific industry only
4. **Super Users**: Can have multiple industries but typically don't need defaults

## Examples

### Example 1: Industry Admin for FMCG

```bash
# Set as industry admin
python scripts/set_industry_admin.py sales@example.com "FMCG"

# This automatically:
# - Sets is_industry_admin = true
# - Assigns to FMCG industry
# - Sets as default industry
```

### Example 2: Multi-Industry User

```bash
# Assign multiple industries
python scripts/assign_industry_to_user.py manager@example.com "FMCG" --default
python scripts/assign_industry_to_user.py manager@example.com "Food & Beverages"
python scripts/assign_industry_to_user.py manager@example.com "Technology"

# User can now switch between all three industries
# FMCG is the default (loads automatically)
```

### Example 3: Super User

```bash
# Super users don't need industry assignment
python scripts/fix_user.py admin@example.com password --super-user

# But can still have default industry for convenience
python scripts/assign_industry_to_user.py admin@example.com "FMCG" --default
```





