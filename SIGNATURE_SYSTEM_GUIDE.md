# Signature System Guide

## Overview

The VANI signature system provides channel-specific signature formatting for Email, WhatsApp, and LinkedIn messages. Signatures are automatically appended to all outreach messages and pitch presentations based on the communication channel.

## Features

- **Channel-Specific Formatting**: Different signature formats for Email (HTML), WhatsApp (plain text), and LinkedIn (professional text)
- **Default Signature**: Set a default signature that will be used for all messages
- **Rich Information**: Support for name, title, company, phone, email, website, LinkedIn, and calendar links
- **Automatic Integration**: Signatures are automatically added to all outreach and pitch messages

## Database Setup

Run the migration to create the `signature_profiles` table:

```sql
-- Run this in Supabase SQL Editor
-- File: app/migrations/006_create_signature_profiles.sql
```

Or use the migration file directly in Supabase Dashboard.

## Creating a Signature Profile

### Via API (Super Users Only)

```bash
POST /api/signatures
Content-Type: application/json

{
  "name": "John - Sales Team",
  "from_name": "John Smith",
  "from_email": "john.smith@company.com",
  "reply_to": "support@company.com",
  "signature_json": {
    "title": "Senior Sales Manager",
    "company": "Acme Corporation",
    "phone": "+1 (555) 123-4567",
    "website": "https://www.acme.com",
    "linkedin": "https://linkedin.com/in/johnsmith",
    "address": "123 Business Ave, San Francisco, CA 94105"
  },
  "calendar_link": "https://cal.com/john-smith/30min",
  "cta_text": "Let's schedule a time to talk:",
  "cta_button": "Schedule a Meeting",
  "is_default": true
}
```

### Signature JSON Fields

The `signature_json` field supports:
- `title`: Job title/position
- `company`: Company name
- `phone`: Phone number
- `website`: Website URL
- `linkedin`: LinkedIn profile URL
- `address`: Physical address

## Channel-Specific Formatting

### Email Signatures (HTML)

Email signatures are formatted as professional HTML with:
- Styled name, title, and company
- Clickable email, phone, website, and LinkedIn links
- Calendar CTA button (if `calendar_link` is provided)
- Professional styling with borders and spacing

**Example:**
```html
<div style="margin-top:24px;padding-top:24px;border-top:1px solid #e5e7eb">
  <div style="font-weight:600;margin-bottom:4px;color:#111111">John Smith</div>
  <div style="color:#666666;font-size:13px;margin-bottom:2px">Senior Sales Manager</div>
  <div style="color:#666666;font-size:13px;margin-bottom:2px">Acme Corporation</div>
  <div style="color:#666666;font-size:13px;margin-bottom:8px">john.smith@company.com</div>
  <div style="color:#666666;font-size:13px;margin-bottom:4px">📞 +1 (555) 123-4567</div>
  <div style="color:#666666;font-size:13px;margin-bottom:4px">🌐 https://www.acme.com</div>
  <div style="color:#666666;font-size:13px;margin-bottom:4px">💼 LinkedIn</div>
  <div style="margin-top:12px;padding:12px;background-color:#f9fafb;border-radius:6px">
    <div style="color:#374151;font-size:14px;margin-bottom:8px">Let's schedule a time to talk:</div>
    <a href="https://cal.com/john-smith/30min" style="display:inline-block;padding:10px 20px;background-color:#0a66c2;color:#ffffff;text-decoration:none;border-radius:6px;font-weight:600">Schedule a Meeting</a>
  </div>
</div>
```

### WhatsApp Signatures (Plain Text)

WhatsApp signatures are concise and mobile-friendly:
- Name and title/company on separate lines
- Contact info with emojis (email, phone, website)
- Calendar link if available
- Compact format for mobile screens

**Example:**
```
John Smith
Senior Sales Manager | Acme Corporation
📧 john.smith@company.com | 📞 +1 (555) 123-4567 | 🌐 https://www.acme.com
📅 Schedule: https://cal.com/john-smith/30min
```

### LinkedIn Signatures (Professional Text)

LinkedIn signatures are professional and formal:
- "Best regards" closing
- Name, title, and company
- Contact information
- LinkedIn profile link

**Example:**
```
Best regards,
John Smith
Senior Sales Manager
Acme Corporation
Email: john.smith@company.com
Phone: +1 (555) 123-4567
Website: https://www.acme.com
LinkedIn: https://linkedin.com/in/johnsmith
```

## API Endpoints

### List All Signatures
```http
GET /api/signatures
Authorization: Bearer <token>
```

### Get Default Signature
```http
GET /api/signatures/default
Authorization: Bearer <token>
```

### Create Signature (Super Users Only)
```http
POST /api/signatures
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Signature Name",
  "from_name": "John Smith",
  "from_email": "john@company.com",
  "signature_json": { ... },
  "is_default": true
}
```

### Update Signature (Super Users Only)
```http
PUT /api/signatures/<signature_id>
Authorization: Bearer <token>
Content-Type: application/json

{
  "from_name": "Updated Name",
  "signature_json": { ... }
}
```

### Delete Signature (Super Users Only)
```http
DELETE /api/signatures/<signature_id>
Authorization: Bearer <token>
```

## Usage in Code

### In Outreach Messages

Signatures are automatically added to all outreach messages via `/api/outreach/send`:

```python
# Signature is automatically fetched and appended based on channel
POST /api/outreach/send
{
  "target_id": "...",
  "channel": "email",  # or "whatsapp" or "linkedin"
  "message": "Your message here"
  # Signature is automatically appended
}
```

### In Pitch Presentations

Signatures are automatically added to all pitch presentations via `/api/pitch/send`:

```python
# Signature is automatically fetched and appended based on channel
POST /api/pitch/send/<pitch_id>
{
  "channel": "email"  # or "whatsapp" or "linkedin"
  # Signature is automatically appended
}
```

## Setting Default Signature

Only one signature can be marked as default. When you set `is_default: true` on a signature:

1. All other signatures are automatically set to `is_default: false`
2. This signature will be used for all messages when no specific signature is assigned
3. If no default is set, the first available signature is used

## Best Practices

1. **Create Multiple Signatures**: Create separate signatures for different team members or departments
2. **Set Default**: Always set one signature as default for automatic use
3. **Keep Information Updated**: Regularly update signature information (phone, email, etc.)
4. **Test Before Sending**: Preview messages to ensure signature formatting looks correct
5. **Channel-Specific Content**: Consider what information is most relevant for each channel:
   - **Email**: Full details with calendar CTA
   - **WhatsApp**: Concise with essential contact info
   - **LinkedIn**: Professional with LinkedIn profile link

## Troubleshooting

### Signature Not Appearing

1. **Check Default Signature**: Ensure a signature is marked as `is_default: true`
2. **Check Database**: Verify `signature_profiles` table exists and has data
3. **Check Logs**: Review application logs for signature fetch errors
4. **Verify Migration**: Ensure migration `006_create_signature_profiles.sql` was run

### Signature Formatting Issues

1. **Email HTML**: Check that HTML is properly escaped
2. **WhatsApp Length**: Keep WhatsApp signatures concise (under 200 characters recommended)
3. **LinkedIn Format**: Ensure LinkedIn signatures follow professional formatting

### Multiple Signatures

If you have multiple signatures:
- The default signature (`is_default: true`) is used
- If no default, the first signature (by creation date) is used
- Future versions may support signature assignment per contact/company

## Future Enhancements

- Signature assignment per contact
- Signature assignment per company
- Signature assignment per industry
- Signature templates
- Signature preview in UI
- Bulk signature management

---

**Last Updated**: December 2025  
**Version**: 1.0  
**Status**: Production Ready















