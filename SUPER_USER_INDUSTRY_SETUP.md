# Super User Industry Setup

## Overview
This document explains how super users and industries are managed in Project VANI.

## Default Behavior
**Super users are automatically assigned ALL industries** by default. They can remove industries if needed through the UI or scripts.

## Scripts

### 1. Sync Industries from Contacts
**Script**: `scripts/sync_industries_from_contacts.py`

This script scans all contacts and syncs their industries to the `industries` table.

```bash
python scripts/sync_industries_from_contacts.py
```

**What it does**:
- Scans all unique industries from contacts
- Adds missing industries to the `industries` table
- Skips industries that already exist
- Normalizes industry codes (uppercase, underscores)

### 2. Assign All Industries to Super Users
**Script**: `scripts/assign_all_industries_to_super_users.py`

This script assigns all industries to all super users automatically.

```bash
python scripts/assign_all_industries_to_super_users.py
```

**What it does**:
- Finds all super users
- Finds all industries
- Assigns missing industries to each super user
- Sets the first industry as default if none is set

### 3. Combined Setup (Recommended)
Run both scripts in sequence:

```bash
cd c:\Raaj\kcube_consulting_labs\vani
.\venv\Scripts\Activate.ps1
python scripts/sync_industries_from_contacts.py
python scripts/assign_all_industries_to_super_users.py
```

## UI: Multi-Selection Industry Management

### Location
**Admin > User Management** section

### Features
1. **Search & Add Industries**
   - Search bar with autocomplete
   - Type `*` to show all available industries
   - Multi-selection with checkboxes

2. **Bulk Operations**
   - **Select All** - Select all available industries
   - **Deselect All** - Clear all selections
   - **Add Selected** - Add all selected industries at once
   - Shows count of selected industries

3. **Manage Assigned Industries**
   - View all assigned industries
   - Set default industry
   - Remove individual industries
   - Default industry is highlighted with a badge

### How to Use
1. Go to **Admin > User Management**
2. Find the user you want to manage
3. Click **Manage Industries** button
4. Use the search bar to filter (or type `*` for all)
5. Check the industries you want to add
6. Click **Add Selected (X)** to add them
7. Set a default industry for the user
8. Remove industries as needed

## Current Status
- **Total Industries**: 35
- **Super Users**: Automatically have all 35 industries assigned
- **Industry Admins**: Can be assigned specific industries via UI

## Industries List
1. Advertising
2. Agriculture
3. Automotive
4. Aviation
5. Banking
6. Beauty
7. Construction
8. Consulting
9. Cryptocurrency
10. Ecommerce
11. Edtech
12. Education
13. Electronics
14. Energy
15. Entertainment
16. Fashion
17. FMCG (Fast Moving Consumer Goods)
18. Finance
19. Financial
20. Fintech
21. Food & Beverages
22. Healthcare
23. Hospitality
24. Insurance
25. Investment
26. Logistics
27. Manufacturing
28. Media
29. Outsourcing
30. Pharmaceutical
31. Real Estate
32. Retail
33. Technology
34. Telecom
35. Travel

## Notes
- Industries are case-insensitive in the database (stored lowercase)
- Contact imports automatically infer missing industries using AI
- New industries are automatically synced from contacts
- Super users should maintain all industries unless specifically removing some













