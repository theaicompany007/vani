# Super User Guide

## Overview

Super users have access to advanced administrative features including user management, industry management, and batch operations. This guide covers all super user capabilities.

## Access

Super user status is granted in the database. To check if you're a super user:
1. Log in to the application
2. Check the user badge in the header
3. Look for the "User Management" and "Admin Tools" tabs in navigation

## Features

### 1. User Management

Manage all users in the system:
- View all users
- Assign/remove super user status
- Assign/remove industry admin status
- Manage user permissions
- Assign users to industries

### 2. Admin Tools

Access powerful batch processing and system management tools:

#### System Information
- View real-time system metrics
- Monitor CPU, memory, and disk usage
- Check platform and Python version

#### Batch Contact Import
- Import 1000+ contacts efficiently
- Multi-threaded batch processing
- Memory-efficient processing
- Support for multiple Excel sheets
- See [ADMIN_TOOLS_GUIDE.md](ADMIN_TOOLS_GUIDE.md) for detailed instructions

### 3. Industry Management

- Create and manage industries
- Assign users to industries
- Set active industry for users

### 4. Permissions Management

- Grant/revoke use case permissions
- Manage feature access for users
- View permission assignments

## Quick Start

### Batch Import Contacts

1. Navigate to **Admin Tools** tab
2. Enter Excel file path (e.g., `data/the_ai_company.xlsx`)
3. Configure batch size and threads
4. Select options (update existing, import only new, dry run)
5. Click **Run Batch Import**
6. Monitor logs in `logs/batch_import_*.log`

For detailed instructions, see [ADMIN_TOOLS_GUIDE.md](ADMIN_TOOLS_GUIDE.md).

## Command Line Tools

Super users can also run scripts directly:

```bash
# Batch import contacts
python scripts/import_contacts_batch.py data/file.xlsx --batch-size 100 --threads 4

# Setup super user
python scripts/setup_super_user.py

# Grant permissions
python scripts/grant_default_permissions.py
```

## Security Notes

- Super user status grants full system access
- Use admin tools responsibly
- Always test with dry-run before large imports
- Monitor system resources during batch operations - User & Permission Management

## 🎯 Where Super Users Can Manage Users and Permissions

### **Location on Dashboard**

1. **Login** as a super user
2. **Navigate to**: `http://localhost:5000/command-center`
3. **Look for**: **"User Management"** tab (7th tab in navigation)
   - This tab is **only visible to super users**
   - If you don't see it, you're not logged in as a super user

---

## ✅ **Features Available**

### **1. Add New User**

**How to Access:**
- Click **"User Management"** tab
- Click **"Add New User"** button (top right, green button)

**What You Can Set:**
- Email address
- Password (minimum 6 characters)
- Super User status (yes/no)
- Industry Admin status (yes/no)

**Steps:**
1. Click "Add New User"
2. Enter email address
3. Enter password
4. Confirm if user should be Super User
5. Confirm if user should be Industry Admin
6. User is created and added to the list

---

### **2. View All Users**

**How to Access:**
- Click **"User Management"** tab
- Users list appears automatically

**What You See:**
- User name and email
- Super User badge (if applicable)
- Industry Admin badge (if applicable)
- Action buttons for each user

---

### **3. Toggle Super User Status**

**How to Access:**
- Click **"User Management"** tab
- Find the user in the list
- Click **"Make Super User"** or **"Remove Super User"** button

**What It Does:**
- Grants or revokes super user access
- Super users can:
  - Access User Management tab
  - Add new users
  - Manage all permissions
  - Access all features regardless of use case permissions

---

### **4. Toggle Industry Admin Status**

**How to Access:**
- Click **"User Management"** tab
- Find the user in the list
- Click **"Make Admin"** or **"Remove Admin"** button

**What It Does:**
- Grants or revokes industry admin access
- Industry admins can manage users within their industry

---

### **5. Manage Permissions (Use Cases)**

**How to Access:**
- Click **"User Management"** tab
- Find the user in the list
- Click **"Manage Permissions"** button (blue button with key icon)

**What You Can Do:**
- View all available use cases
- Grant permissions to specific use cases
- Revoke permissions from use cases
- See which permissions are currently granted

**Available Use Cases:**
- `outreach` - Send outreach messages
- `pitch_presentation` - Generate and send pitches
- `analytics` - View dashboard analytics
- `target_management` - Manage targets
- `meetings` - Schedule meetings
- `sheets_import_export` - Import/export from Google Sheets
- `ai_message_generation` - Generate AI messages

**Steps:**
1. Click "Manage Permissions" for a user
2. Modal opens showing all use cases
3. Click **"Grant"** to give permission
4. Click **"Revoke"** to remove permission
5. Changes are saved immediately

---

## 🔐 **Access Control**

### **Who Can Access:**
- **Super Users Only** - The "User Management" tab is only visible to users with `is_super_user = true`

### **How to Become a Super User:**
1. **Via Database** (Direct SQL):
   ```sql
   UPDATE app_users 
   SET is_super_user = true 
   WHERE email = 'your-email@example.com';
   ```

2. **Via Another Super User**:
   - Have an existing super user log in
   - Go to User Management tab
   - Click "Make Super User" for your account

3. **Via Setup Script**:
   - Run: `python do_setup.py`
   - Enter your email when prompted
   - You'll be set as super user

---

## 📍 **Visual Guide**

```
┌─────────────────────────────────────────────────────────┐
│  PROJECT VANI | Strategic Command    [🔔 Notifications] │
├─────────────────────────────────────────────────────────┤
│  [Situation Room] [Analytics] [Meetings] [Arbitrage]    │
│  [Revenue Sim] [Target Hit List] [User Management] ←───│
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  User Management                                  │ │
│  │  [Add New User]                                   │ │
│  ├───────────────────────────────────────────────────┤ │
│  │                                                   │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │ User 1: user@example.com                   │ │ │
│  │  │ [Super User] [Industry Admin]              │ │ │
│  │  │ [Manage Permissions] [Remove Super User]    │ │ │
│  │  │ [Remove Admin]                              │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  │                                                   │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │ User 2: another@example.com                 │ │ │
│  │  │ [Manage Permissions] [Make Super User]      │ │ │
│  │  │ [Make Admin]                                │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  │                                                   │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 **Quick Start**

### **To Add a New User:**
1. Login as super user
2. Click **"User Management"** tab
3. Click **"Add New User"** button
4. Enter email and password
5. Set roles as needed
6. User is created!

### **To Grant Permissions:**
1. Click **"User Management"** tab
2. Find the user
3. Click **"Manage Permissions"**
4. Click **"Grant"** for each use case you want to allow
5. Permissions are saved immediately

### **To Make Someone a Super User:**
1. Click **"User Management"** tab
2. Find the user
3. Click **"Make Super User"** button
4. User now has super user access

---

## 📝 **API Endpoints Used**

All endpoints are protected with `@require_super_user`:

- `GET /api/auth/users` - List all users
- `POST /api/auth/register` - Add new user
- `POST /api/auth/users/<id>/toggle_super_user` - Toggle super user
- `POST /api/auth/users/<id>/toggle_industry_admin` - Toggle admin
- `GET /api/permissions/user/<id>` - Get user permissions
- `POST /api/permissions/user/<id>/grant` - Grant permission
- `POST /api/permissions/user/<id>/revoke` - Revoke permission
- `GET /api/permissions/use-cases` - List all use cases

---

## ⚠️ **Important Notes**

1. **Super User Access**: Super users bypass all use case permission checks
2. **Industry Context**: Permissions can be industry-specific or global
3. **Security**: All operations are logged and require super user authentication
4. **Tab Visibility**: User Management tab only appears for super users automatically

---

**Last Updated**: December 2025  
**Access**: Super Users Only  
**Location**: Dashboard → User Management Tab

