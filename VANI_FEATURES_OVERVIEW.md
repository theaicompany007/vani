# Project VANI - Complete Features Overview

## 📋 Table of Contents
1. [Core Features](#core-features)
2. [API Endpoints](#api-endpoints)
3. [Integrations](#integrations)
4. [Authentication & Authorization](#authentication--authorization)
5. [Database Schema](#database-schema)
6. [Where Features Are Implemented](#where-features-are-implemented)

---

## 🎯 Core Features

### 1. **Multi-Industry Support**
- **Location**: `app/migrations/002_industries_tenants.sql`
- **API**: `app/api/industries.py`
- **Features**:
  - Industry-based tenant isolation
  - Support for FMCG, Food & Beverages, and custom industries
  - Industry switching for users
  - Industry-specific data filtering

### 2. **Authentication & Authorization**
- **Location**: `app/auth/__init__.py`, `app/api/auth.py`
- **Features**:
  - Supabase Auth integration
  - Login/Logout functionality
  - Session management
  - Use-case based permissions
  - Super user and industry admin roles
  - User registration (super user only)

### 3. **Target Management**
- **Location**: `app/api/targets.py`, `app/models/targets.py`
- **Features**:
  - Create, Read, Update, Delete targets
  - Target status management
  - Industry-based filtering
  - Google Sheets import/export
  - Target search and filtering

### 4. **Multi-Channel Outreach**
- **Location**: `app/api/outreach.py`
- **Features**:
  - Email sending via Resend
  - WhatsApp messaging via Twilio
  - LinkedIn messaging (API ready)
  - Outreach activity tracking
  - Multi-channel campaign management

### 5. **AI Message Generation**
- **Location**: `app/api/message_generator.py`, `app/integrations/openai_client.py`
- **Features**:
  - OpenAI-powered personalized messages
  - Channel-specific message generation (Email, WhatsApp, LinkedIn)
  - Context-aware message creation
  - Target-specific personalization

### 6. **Pitch Presentations**
- **Location**: `app/api/pitch.py`, `app/integrations/pitch_generator.py`
- **Features**:
  - AI-generated pitch presentations
  - Target-specific pitch content
  - HTML pitch rendering
  - Pitch sending via multiple channels
  - Pitch preview and management

### 7. **Analytics Dashboard**
- **Location**: `app/api/dashboard.py`, `app/templates/command_center.html`
- **Features**:
  - Real-time statistics
  - Engagement metrics
  - Activity tracking
  - Meeting statistics
  - Performance analytics

### 8. **Google Sheets Integration**
- **Location**: `app/integrations/google_sheets_client.py`, `app/api/targets.py`
- **Features**:
  - Import targets from Google Sheets
  - Export targets and activities to Google Sheets
  - Automatic data synchronization
  - Error handling and validation

### 9. **Meeting Scheduling**
- **Location**: `app/integrations/cal_com_client.py`, `app/api/dashboard.py`
- **Features**:
  - Cal.com integration
  - Meeting creation and management
  - Meeting statistics
  - Calendar synchronization

### 10. **HIT Notifications**
- **Location**: `app/notifications.py`, `app/webhooks/`
- **Features**:
  - Email notifications for engagement events
  - WhatsApp notifications via Twilio
  - Real-time event tracking
  - Notification preferences

### 11. **Webhook Handlers**
- **Location**: `app/webhooks/resend_handler.py`, `app/webhooks/twilio_handler.py`
- **Features**:
  - Resend webhook processing
  - Twilio webhook processing
  - Event logging
  - Activity tracking

### 12. **Permissions Management**
- **Location**: `app/api/permissions.py`
- **Features**:
  - Use case management
  - User permission assignment
  - Industry-specific permissions
  - Permission revocation
  - Global vs industry permissions

### 13. **Admin Tools** (Super Users Only)
- **Location**: `app/api/admin.py`, `scripts/import_contacts_batch.py`
- **Features**:
  - System information and monitoring
  - Batch contact import with multi-threading
  - Memory-efficient processing for large files (2000+ records)
  - Script execution interface
  - Process management and logging
  - See [ADMIN_TOOLS_GUIDE.md](ADMIN_TOOLS_GUIDE.md) for details

### 14. **Contact & Company Management**
- **Location**: `app/api/contacts.py`, `app/api/companies.py`
- **Features**:
  - Contact CRUD operations
  - Company management
  - Contact-company mapping
  - Domain extraction and backfilling
  - Excel import/export
  - Bulk operations

---

## 🔌 API Endpoints

### Authentication (`app/api/auth.py`)
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /api/auth/session` - Get current session
- `POST /api/auth/register` - Register new user (super user only)
- `GET /api/auth/users` - List all users (super user only)
- `POST /api/auth/users/<id>/toggle_super_user` - Toggle super user status
- `POST /api/auth/users/<id>/toggle_industry_admin` - Toggle industry admin status

### Targets (`app/api/targets.py`)
- `GET /api/targets` - List targets
- `POST /api/targets` - Create target
- `GET /api/targets/<id>` - Get target details
- `PUT /api/targets/<id>` - Update target
- `DELETE /api/targets/<id>` - Delete target
- `POST /api/targets/import` - Import from Google Sheets
- `POST /api/targets/export` - Export to Google Sheets

### Outreach (`app/api/outreach.py`)
- `POST /api/outreach/send` - Send outreach message
- `GET /api/outreach/activities` - Get outreach activities
- `GET /api/outreach/activities/<id>` - Get activity details

### Message Generator (`app/api/message_generator.py`)
- `POST /api/messages/generate` - Generate AI message
- `GET /api/messages/templates` - Get message templates

### Dashboard (`app/api/dashboard.py`)
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/activities` - Get recent activities
- `GET /api/dashboard/meetings` - Get meeting statistics

### Pitch (`app/api/pitch.py`)
- `POST /api/pitch/generate/<target_id>` - Generate pitch
- `GET /api/pitch/preview/<pitch_id>` - Preview pitch
- `POST /api/pitch/send/<pitch_id>` - Send pitch

### Permissions (`app/api/permissions.py`)
- `GET /api/permissions/use-cases` - List use cases
- `GET /api/permissions/user/<id>` - Get user permissions
- `POST /api/permissions/user/<id>/grant` - Grant permission
- `POST /api/permissions/user/<id>/revoke` - Revoke permission

### Industries (`app/api/industries.py`)
- `GET /api/industries` - List industries
- `GET /api/industries/<id>` - Get industry details
- `POST /api/industries/create` - Create industry (super user only)
- `POST /api/industries/switch` - Switch active industry

### Admin Tools (`app/api/admin.py`) - Super Users Only
- `GET /api/admin/system/info` - Get system information
- `GET /api/admin/scripts/list` - List available scripts
- `POST /api/admin/scripts/run` - Run a script
- `POST /api/admin/scripts/import-contacts` - Run batch contact import

### Contacts (`app/api/contacts.py`)
- `GET /api/contacts` - List contacts
- `POST /api/contacts` - Create/update contact
- `GET /api/contacts/<id>` - Get contact details
- `PUT /api/contacts/<id>` - Update contact
- `DELETE /api/contacts/<id>` - Delete contact
- `POST /api/contacts/bulk` - Bulk import contacts
- `POST /api/contacts/import-excel` - Import from Excel
- `GET /api/contacts/export-excel` - Export to Excel
- `POST /api/contacts/export-sheets` - Export to Google Sheets

### Companies (`app/api/companies.py`)
- `GET /api/companies` - List companies
- `POST /api/companies` - Create company
- `GET /api/companies/<id>` - Get company details with contacts
- `PUT /api/companies/<id>` - Update company
- `DELETE /api/companies/<id>` - Delete company
- `POST /api/companies/backfill-domains` - Backfill company domains from contacts

---

## 🔗 Integrations

### Resend (Email)
- **Location**: `app/integrations/resend_client.py`
- **Features**: Email sending, template support, webhook handling

### Twilio (WhatsApp)
- **Location**: `app/integrations/twilio_client.py`
- **Features**: WhatsApp messaging, SMS support, webhook handling

### OpenAI
- **Location**: `app/integrations/openai_client.py`
- **Features**: Message generation, pitch generation, AI-powered content

### LinkedIn
- **Location**: `app/integrations/linkedin_client.py`
- **Features**: LinkedIn messaging (API ready)

### Cal.com
- **Location**: `app/integrations/cal_com_client.py`
- **Features**: Meeting scheduling, calendar integration

### Google Sheets
- **Location**: `app/integrations/google_sheets_client.py`
- **Features**: Import/export, data synchronization

---

## 🔐 Authentication & Authorization

### Decorators (`app/auth/__init__.py`)
- `@require_auth` - Require authentication
- `@require_use_case('code')` - Require specific use case permission
- `@require_super_user` - Require super user access

### Use Cases
- `outreach` - Send outreach messages
- `pitch_presentation` - Generate and send pitches
- `analytics` - View dashboard analytics
- `target_management` - Manage targets
- `meetings` - Schedule meetings
- `sheets_import_export` - Import/export from Google Sheets
- `ai_message_generation` - Generate AI messages

---

## 🗄️ Database Schema

### Tables (`app/migrations/`)
1. **001_create_tables.sql** - Core tables
   - `targets` - Target companies
   - `outreach_sequences` - Outreach sequences
   - `outreach_activities` - Communication history
   - `meetings` - Scheduled meetings
   - `webhook_events` - Webhook logs

2. **002_industries_tenants.sql** - Multi-industry support
   - `industries` - Industry definitions

3. **003_auth_permissions.sql** - Authentication system
   - `app_users` - Application users
   - `use_cases` - Available use cases
   - `user_permissions` - User permissions

4. **004_pitch_storage.sql** - Pitch management
   - `generated_pitches` - AI-generated pitches

5. **005_add_industry_to_tables.sql** - Industry context
   - Adds `industry_id` to all relevant tables

---

## 📁 Where Features Are Implemented

### Frontend
- **Templates**: `app/templates/`
  - `login.html` - Login page
  - `command_center.html` - Main dashboard

### Backend
- **API Routes**: `app/api/`
  - `auth.py` - Authentication
  - `targets.py` - Target management
  - `outreach.py` - Outreach operations
  - `dashboard.py` - Analytics
  - `message_generator.py` - AI message generation
  - `pitch.py` - Pitch management
  - `permissions.py` - Permissions
  - `industries.py` - Industry management
  - `admin.py` - Admin tools (super users only)
  - `contacts.py` - Contact management
  - `companies.py` - Company management

- **Integrations**: `app/integrations/`
  - `resend_client.py` - Email
  - `twilio_client.py` - WhatsApp
  - `openai_client.py` - AI
  - `linkedin_client.py` - LinkedIn
  - `cal_com_client.py` - Meetings
  - `google_sheets_client.py` - Google Sheets
  - `pitch_generator.py` - Pitch generation

- **Models**: `app/models/`
  - `targets.py` - Target data models
  - `outreach.py` - Outreach models
  - `meetings.py` - Meeting models
  - `webhooks.py` - Webhook models

- **Webhooks**: `app/webhooks/`
  - `resend_handler.py` - Resend webhooks
  - `twilio_handler.py` - Twilio webhooks

- **Auth**: `app/auth/`
  - `__init__.py` - Authentication decorators and helpers

- **Migrations**: `app/migrations/`
  - SQL migration files for database setup

### Scripts
- **Setup**: `scripts/`
  - `test_all_functions.py` - Comprehensive testing
  - `seed_targets.py` - Seed sample data
  - `configure_webhooks.py` - Webhook setup
  - `import_contacts_batch.py` - Batch contact import with threading

### Configuration
- **Main Entry**: `run.py` - Application startup
- **Batch File**: `VANI.bat` - Windows setup script
- **Setup**: `do_setup.py` - Database setup
- **SQL**: `COMPLETE_SETUP.sql` - Complete database setup

---

## 🚀 Quick Reference

### To See All Features:
1. **Code**: Browse `app/api/` for all API endpoints
2. **Integrations**: Check `app/integrations/` for all integrations
3. **Database**: Review `app/migrations/` for schema
4. **Documentation**: Read this file and other `.md` files in root

### To Test Features:
```bash
# Run comprehensive test suite
python scripts/test_all_functions.py

# Start the application
python run.py
# or
VANI.bat
```

### To View in Browser:
- Login: `http://localhost:5000/login`
- Command Center: `http://localhost:5000/command-center`
- Health Check: `http://localhost:5000/api/health`

---

**Last Updated**: December 2025  
**Project**: VANI (Virtual Agent Network Interface)  
**Status**: Production Ready





