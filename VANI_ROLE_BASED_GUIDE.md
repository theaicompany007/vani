# VANI Platform - Comprehensive Role-Based Guide

**Project VANI (Virtual Agent Network Interface)**  
**Version**: 2.0  
**Last Updated**: January 2025  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Super Administrator Guide](#super-administrator-guide)
3. [Administrator Guide](#administrator-guide)
4. [User Guide](#user-guide)
5. [Business User Guide](#business-user-guide)
6. [Future Vision: Self-Learning & Multi-Company Knowledge Base](#future-vision)
7. [Quick Reference](#quick-reference)

---

## Overview

VANI is a Flask-based outreach command center enabling multi-channel communication (Email, WhatsApp, LinkedIn) with AI-powered message generation, pitch presentations, target management, and Knowledge Base integration. The platform supports multi-industry tenant isolation with role-based access control.

### Key Features
- **Multi-Industry Support**: Industry-based tenant isolation
- **Authentication & Authorization**: Supabase Auth with use-case based permissions
- **Target Management**: CRUD operations for target companies
- **Outreach**: Multi-channel messaging (Email, WhatsApp, LinkedIn)
- **AI Message Generation**: OpenAI-powered personalized messages
- **AI Target Finder**: AI-powered identification of high-value targets
- **Pitch Presentations**: AI-generated pitch presentations per target
- **Knowledge Base**: RAG-powered knowledge base for factual information
- **Analytics Dashboard**: Real-time statistics and engagement metrics
- **Google Sheets Integration**: Import/export targets and activities
- **Meeting Scheduling**: Cal.com integration

### Technology Stack
- **Backend**: Python 3.11+, Flask
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth with use-case based permissions
- **Integrations**: Resend (Email), Twilio (WhatsApp), LinkedIn API, Cal.com (Meetings), Google Sheets API, OpenAI API, RAG Service
- **Frontend**: HTML/CSS/JavaScript (Tailwind CSS, Chart.js)
- **Deployment**: Docker containers on Google Cloud VM

---

## Super Administrator Guide

### Role Definition

**Super Administrators** manage the complete VANI Platform infrastructure, including coding, deployment, configurations, and system architecture. They have full access to all features and can manage all users, industries, and system settings.

### Access Level
- **Full System Access**: All features, all industries, all users
- **Infrastructure Management**: Server, database, Docker, ngrok
- **Code Deployment**: Git, CI/CD, migrations
- **Configuration**: Environment variables, API keys, webhooks

### Key Responsibilities

#### 1. Infrastructure Management

##### Server Setup & Maintenance
```bash
# SSH into Google Cloud VM
ssh postgres@chroma-vm

# Navigate to application directory
cd ~/vani

# Check Docker containers
docker ps
docker-compose -f ../onlynereputation-agentic-app/docker-compose.worker.yml ps

# View logs
docker logs vani
docker logs vani --tail 100 -f
```

##### Environment Configuration
- **Location**: `.env.local` (not in git)
- **Required Variables**:
  ```bash
  # Supabase
  SUPABASE_URL=https://[project].supabase.co
  SUPABASE_KEY=[anon-key]
  SUPABASE_SERVICE_KEY=[service-role-key]
  
  # Email (Resend)
  RESEND_API_KEY=[resend-api-key]
  
  # WhatsApp (Twilio)
  TWILIO_ACCOUNT_SID=[account-sid]
  TWILIO_AUTH_TOKEN=[auth-token]
  TWILIO_WHATSAPP_NUMBER=[whatsapp-number]
  
  # AI Services
  OPENAI_API_KEY=[openai-key]
  RAG_API_KEY=[rag-service-key]
  RAG_SERVICE_URL=https://rag.kcube-consulting.com
  GEMINI_API_KEY=[gemini-key]  # Optional
  
  # Webhooks
  WEBHOOK_BASE_URL=https://vani.ngrok.app
  
  # Docker
  DOCKER_CONTAINER=true
  PORT=5000
  FLASK_ENV=production
  FLASK_HOST=0.0.0.0
  ```

##### Ngrok Configuration
- **Domain**: `vani.ngrok.app` (must be reserved in ngrok dashboard)
- **Port**: 5000
- **Configuration**: Managed via `start-ngrok.sh` in `onlynereputation-agentic-app`
- **Verification**:
  ```bash
  curl https://vani.ngrok.app/api/health
  ```

#### 2. Database Management

##### Running Migrations
```sql
-- Access Supabase SQL Editor
-- https://supabase.com/dashboard/project/[project-id]/sql/new

-- Run migrations in order:
-- 1. app/migrations/001_create_tables.sql
-- 2. app/migrations/002_industries_tenants.sql
-- 3. app/migrations/003_auth_permissions.sql
-- 4. app/migrations/004_pitch_storage.sql
-- 5. app/migrations/005_add_industry_to_tables.sql
-- ... (continue with all migrations)
```

##### Creating Super Users
```sql
-- Method 1: Direct SQL
INSERT INTO app_users (supabase_user_id, email, name, role, is_super_user)
VALUES (
  '[supabase-user-id]',
  'admin@example.com',
  'Super Admin',
  'admin',
  true
);

-- Method 2: Via Python script
python scripts/setup_super_user.py
```

##### Database Backup
```bash
# Supabase Dashboard → Database → Backups
# Or use pg_dump via Supabase CLI
supabase db dump -f backup_$(date +%Y%m%d).sql
```

#### 3. Code Deployment

##### Git Workflow
```bash
# Clone repository
git clone https://github.com/theaicompany007/vani.git
cd vani

# Create branch for changes
git checkout -b feature/new-feature

# Make changes, commit
git add .
git commit -m "Description of changes"
git push origin feature/new-feature

# Merge to main after review
```

##### Docker Deployment
```bash
# Build container
cd ../onlynereputation-agentic-app
docker-compose -f docker-compose.worker.yml build vani

# Start service
docker-compose -f docker-compose.worker.yml up -d vani

# Verify health
docker ps | grep vani
curl http://localhost:5000/api/health
```

##### Deployment Script
```bash
# Use automated deployment script
./deploy-vani.sh

# Or manual steps:
# 1. Build container
# 2. Start service
# 3. Wait for healthcheck
# 4. Start ngrok tunnels
# 5. Verify deployment
```

#### 4. Monitoring & Troubleshooting

##### Health Checks
```bash
# Application health
curl https://vani.ngrok.app/api/health

# Container health
docker inspect --format='{{.State.Health.Status}}' vani

# Logs
docker logs vani --tail 100
docker logs vani -f  # Follow logs
```

##### Common Issues

**Issue**: Container won't start
```bash
# Check logs
docker logs vani

# Check environment variables
docker exec vani env | grep SUPABASE

# Restart container
docker-compose -f docker-compose.worker.yml restart vani
```

**Issue**: Database connection errors
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env.local`
- Check Supabase project status
- Verify network connectivity from VM

**Issue**: Ngrok tunnel not working
- Verify ngrok is running: `ps aux | grep ngrok`
- Check ngrok dashboard for tunnel status
- Verify domain reservation: `vani.ngrok.app`
- Check ngrok auth token: `ngrok config check`

#### 5. User Management (Super Admin)

##### Creating Users
1. **Via Supabase Auth Dashboard**:
   - Go to Authentication → Users
   - Click "Add User"
   - Set email and password
   - Note the `user_id`

2. **Create App User Record**:
   ```sql
   INSERT INTO app_users (supabase_user_id, email, name, role, is_super_user)
   VALUES (
     '[supabase-user-id]',
     'user@example.com',
     'User Name',
     'user',  -- or 'admin'
     false
   );
   ```

##### Assigning Industries
```sql
-- Assign user to industry
INSERT INTO user_industries (user_id, industry_id, is_default)
VALUES (
  '[app-user-id]',
  '[industry-id]',
  true  -- Set as default industry
);
```

##### Granting Use Case Permissions
```sql
-- Get use case ID
SELECT id, code, name FROM use_cases WHERE code = 'knowledge_base_management';

-- Grant permission (global - all industries)
INSERT INTO user_permissions (user_id, use_case_id, industry_id)
VALUES (
  '[app-user-id]',
  '[use-case-id]',
  NULL  -- NULL = global permission
);

-- Grant permission (industry-specific)
INSERT INTO user_permissions (user_id, use_case_id, industry_id)
VALUES (
  '[app-user-id]',
  '[use-case-id]',
  '[industry-id]  -- Specific industry only
);
```

#### 6. API Key Management

##### Required API Keys
- **Supabase**: From Supabase Dashboard → Settings → API
- **Resend**: From https://resend.com/api-keys
- **Twilio**: From https://console.twilio.com/
- **OpenAI**: From https://platform.openai.com/api-keys
- **RAG Service**: From RAG service administrator
- **Gemini**: From https://makersuite.google.com/app/apikey (optional)

##### Security Best Practices
- Never commit `.env.local` to git
- Rotate API keys regularly
- Use service role keys only on server-side
- Monitor API usage for anomalies
- Set up alerts for API failures

---

## Administrator Guide

### Role Definition

**Administrators** manage day-to-day operations: mapping industries, setting up users for outreach, creating pitches, and managing the Knowledge Base. They have access to Admin tools but cannot modify infrastructure or system configurations.

### Access Level
- **Admin Tools**: User Management, Signatures, Knowledge Base, Tools
- **Industry Management**: Create, edit, assign industries
- **User Management**: Create users, assign industries, grant permissions
- **Knowledge Base**: Upload documents, scrape URLs, manage content
- **All Outreach Features**: Full access to contacts, companies, outreach

### Key Responsibilities

#### 1. Industry Management

##### Creating Industries
1. **Via Admin Tab → User Management**:
   - Navigate to Admin → User Management
   - Click "Industries" section
   - Click "Add Industry"
   - Enter:
     - **Name**: Display name (e.g., "Food & Beverages")
     - **Code**: URL-friendly code (e.g., "food-beverages")
     - **Description**: Optional description

2. **Via SQL** (if needed):
   ```sql
   INSERT INTO industries (name, code, description)
   VALUES (
     'Food & Beverages',
     'food-beverages',
     'Food and beverage companies'
   );
   ```

##### Assigning Industries to Users
1. **Via Admin Tab → User Management**:
   - Find user in list
   - Click "Edit" or "Manage Industries"
   - Select industries to assign
   - Set default industry (user's primary industry)
   - Save

2. **Via SQL**:
   ```sql
   -- Get user and industry IDs
   SELECT id, email FROM app_users WHERE email = 'user@example.com';
   SELECT id, name FROM industries WHERE code = 'food-beverages';

   -- Assign industry
   INSERT INTO user_industries (user_id, industry_id, is_default)
   VALUES (
     '[user-id]',
     '[industry-id]',
     true
   );
   ```

#### 2. User Setup for Outreach

##### Creating Users
1. **Via Admin Tab → User Management**:
   - Click "Add User"
   - Enter:
     - **Email**: User's email address
     - **Name**: Full name
     - **Role**: `user` or `admin`
   - User will receive email to set password (via Supabase Auth)

##### Assigning Industries
- Follow steps in "Industry Management" above
- Users can only access data for their assigned industries
- Set one industry as default (user's primary view)

##### Granting Use Case Permissions
1. **Via Admin Tab → User Management**:
   - Find user → Click "Edit"
   - Scroll to "Use Case Permissions"
   - Check use cases to grant:
     - `contact_management` - Manage contacts
     - `company_management` - Manage companies
     - `outreach_management` - Send outreach messages
     - `ai_target_finder` - Use AI Target Finder
     - `knowledge_base_management` - Manage Knowledge Base
     - `pitch_generation` - Generate pitches
   - Select scope:
     - **Global**: All industries
     - **Industry-Specific**: Only selected industries
   - Save

##### Use Case Codes Reference
- `contact_management` - Contact CRUD operations
- `company_management` - Company CRUD operations
- `outreach_management` - Send emails, WhatsApp, LinkedIn
- `ai_target_finder` - AI-powered target identification
- `knowledge_base_management` - Query, upload, manage KB
- `pitch_generation` - Generate AI pitches
- `dashboard_analytics` - View analytics dashboard

#### 3. Knowledge Base Management

##### Uploading Documents
1. **Navigate**: Admin → Knowledge Base → Upload Documents
2. **Select Files**: PDF or TXT files (max 10MB each)
3. **Choose Collection**:
   - `case_studies` - Success stories
   - `services` - Service offerings
   - `company_profiles` - Company information
   - `industry_insights` - Industry trends
   - `platforms` - Platform documentation
   - `faqs` - Frequently asked questions
4. **Add Metadata**:
   - **Company**: Company name (e.g., "The AI Company")
   - **Platform**: Platform name (e.g., "VANI", "Neura360")
   - **Service**: Service name (e.g., "Reputation Management")
   - **Industry**: Industry tag
   - **Tags**: Comma-separated tags
5. **Upload**: Click "Upload Files"
6. **Monitor**: View upload progress and results

##### Scraping URLs
1. **Navigate**: Admin → Knowledge Base → Scrape URLs
2. **Enter URL**: Full URL (e.g., `https://theaicompany.co`)
3. **Choose Collection**: Same as document upload
4. **Add Metadata**: Same as document upload
5. **Ingest**: Click "Ingest URL"
6. **Monitor**: View ingestion status

##### Querying Knowledge Base
1. **Navigate**: Admin → Knowledge Base → Query/View
2. **Enter Query**: Natural language question
3. **Filter Collections**: Select collections to search
4. **Filter Industry**: Optional industry filter
5. **Search**: Click "Search Knowledge Base"
6. **Review Results**: View relevant documents with excerpts
7. **Use Content**: Click "Use in Message" to insert into outreach

##### Best Practices
- **Tagging**: Always tag with company, platform, service, industry
- **Collections**: Use appropriate collections for better retrieval
- **Metadata**: Complete metadata improves search accuracy
- **Regular Updates**: Keep Knowledge Base current with latest information
- **Quality Control**: Review uploaded content for accuracy

#### 4. Signature Management

##### Creating Signatures
1. **Navigate**: Admin → Signatures
2. **Click**: "Add Signature"
3. **Configure**:
   - **Channel**: Email, WhatsApp, or LinkedIn
   - **From Email**: Sender email address
   - **From Name**: Sender display name
   - **Signature HTML**: HTML signature content
   - **CTA Text**: Call-to-action text
   - **CTA Button**: Button text (e.g., "Book a Call")
   - **Calendar Link**: Cal.com link
   - **Contact Info**: Phone, WhatsApp, LinkedIn, Website
4. **Preview**: Review signature appearance
5. **Save**: Click "Save Signature"

##### Assigning Signatures
1. **Navigate**: Admin → Signatures
2. **Find Signature**: Click "Assign" or "Manage Assignments"
3. **Assignment Options**:
   - **Individual Contact**: Specific contact
   - **Company**: All contacts in company
   - **Industry**: All contacts in industry
   - **Campaign**: All contacts in campaign
4. **Priority**: Higher priority (lower number) overrides lower priority
5. **Save**: Assignments are saved automatically

#### 5. Bulk Operations

##### Importing Contacts/Companies
1. **Navigate**: Admin → Tools → Batch Import
2. **Upload File**: Excel or CSV file
3. **Configure**:
   - **File Type**: Contacts or Companies
   - **Multi-threading**: Enable for large files
   - **AI Industry Inference**: Auto-detect industries
4. **Import**: Click "Start Import"
5. **Monitor**: View import progress and results
6. **Review**: Check imported data for accuracy

##### Exporting Data
1. **Navigate**: Contacts or Companies tab
2. **Apply Filters**: Filter data as needed
3. **Export**: Click "Export to Excel" or "Export to Google Sheets"
4. **Download**: File downloads automatically

---

## User Guide

### Role Definition

**Users** are assigned specific industries and work on prospecting, preparing pitches, sending outreach messages, and managing meetings. They have access to their assigned industries only and cannot modify system settings.

### Access Level
- **Industry-Specific Access**: Only assigned industries
- **Contact Management**: View, create, edit, delete contacts
- **Company Management**: View, create, edit, delete companies
- **Outreach**: Send emails, WhatsApp, LinkedIn messages
- **AI Target Finder**: Find high-value targets (if permission granted)
- **Pitch Generation**: Generate AI pitches (if permission granted)
- **Meetings**: Schedule and manage Cal.com meetings
- **Analytics**: View dashboard for assigned industries

### Key Responsibilities

#### 1. Prospecting

##### Using AI Target Finder
1. **Navigate**: AI Target Finder tab
2. **Select Search Preset**:
   - **High Priority**: C-level executives, high-value companies
   - **Broad Search**: Wide industry coverage
   - **C-Level Only**: Executives only
   - **Custom**: Define your own criteria
3. **Select Industries**: Choose from your assigned industries
4. **Configure Search**:
   - **Target Roles**: CEO, CTO, CMO, etc.
   - **Company Size**: Small, Medium, Large
   - **Keywords**: Industry-specific keywords
5. **Search**: Click "Find Targets"
6. **Review Results**:
   - **Recommendations**: AI-generated target suggestions
   - **Knowledge Base Context**: Related case studies, services, insights
   - **Confidence Score**: AI confidence in recommendation
7. **Select Targets**: Check boxes for targets to create
8. **Create**: Click "Create Selected Targets"

##### Manual Target Creation
1. **Navigate**: Companies tab
2. **Click**: "Add Company"
3. **Enter Details**:
   - **Company Name**: Full company name
   - **Domain**: Company website domain
   - **Industry**: Select from assigned industries
   - **Description**: Optional company description
4. **Add Contacts**: Click "Add Contact" within company
5. **Enter Contact Details**:
   - **Name**: Full name
   - **Email**: Email address
   - **Role**: Job title
   - **Phone**: Optional phone number
   - **LinkedIn**: Optional LinkedIn URL
6. **Save**: Company and contacts are saved

##### Importing from Google Sheets
1. **Navigate**: Companies or Contacts tab
2. **Click**: "Import from Google Sheets"
3. **Authorize**: Grant Google Sheets access
4. **Select Sheet**: Choose spreadsheet and worksheet
5. **Map Columns**: Map sheet columns to VANI fields
6. **Import**: Click "Import Data"
7. **Review**: Check imported data

#### 2. Preparing Pitches

##### Generating AI Pitches
1. **Navigate**: Companies tab
2. **Select Company**: Click on company name
3. **Click**: "Generate Pitch" (if permission granted)
4. **Configure**:
   - **Target Contact**: Select contact to pitch
   - **Pain Points**: Enter known pain points
   - **Services**: Select relevant services
   - **Tone**: Professional, Casual, Friendly
5. **Generate**: Click "Generate Pitch"
6. **Review**: AI-generated pitch appears
7. **Edit**: Modify pitch as needed
8. **Save**: Save pitch for later use

##### Manual Pitch Creation
1. **Navigate**: Companies tab
2. **Select Company**: Click on company name
3. **Click**: "Create Pitch"
4. **Enter Content**:
   - **Subject**: Email subject line
   - **Body**: Pitch content
   - **Attachments**: Optional files
5. **Save**: Pitch is saved to company

#### 3. Sending Outreach

##### Email Outreach
1. **Navigate**: Contacts or Companies tab
2. **Select Contact**: Click on contact name
3. **Click**: "Send Email"
4. **Compose**:
   - **Subject**: Email subject
   - **Body**: Message content
   - **Use AI**: Click "Generate with AI" for AI-powered message
   - **Use Knowledge Base**: Click "Use KB Content" to insert relevant info
5. **Preview**: Review message and signature
6. **Send**: Click "Send Email"
7. **Track**: View delivery status in Activities tab

##### WhatsApp Outreach
1. **Navigate**: Contacts tab
2. **Select Contact**: Click on contact name
3. **Click**: "Send WhatsApp"
4. **Compose**: Enter WhatsApp message
5. **Preview**: Review message
6. **Send**: Click "Send WhatsApp"
7. **Track**: View delivery status

##### LinkedIn Outreach
1. **Navigate**: Contacts tab
2. **Select Contact**: Click on contact name
3. **Click**: "Send LinkedIn"
4. **Compose**: Enter LinkedIn message
5. **Preview**: Review message
6. **Send**: Click "Send LinkedIn" (requires LinkedIn API setup)
7. **Track**: View delivery status

##### Bulk Outreach
1. **Navigate**: Contacts or Companies tab
2. **Select Multiple**: Check boxes for multiple contacts/companies
3. **Click**: "Bulk Actions" → "Send Outreach"
4. **Configure**:
   - **Channel**: Email, WhatsApp, or LinkedIn
   - **Template**: Select message template
   - **Personalization**: Enable AI personalization
5. **Review**: Preview messages for all recipients
6. **Send**: Click "Send All"
7. **Monitor**: Track delivery status for all messages

#### 4. Managing Meetings

##### Scheduling Meetings
1. **Navigate**: Contacts tab
2. **Select Contact**: Click on contact name
3. **Click**: "Schedule Meeting"
4. **Configure**:
   - **Meeting Type**: 15-min, 30-min, 60-min
   - **Date/Time**: Select available slot
   - **Description**: Meeting agenda
5. **Schedule**: Click "Schedule Meeting"
6. **Confirmation**: Meeting link is sent to contact

##### Viewing Scheduled Meetings
1. **Navigate**: Dashboard → Meetings
2. **View List**: All scheduled meetings
3. **Filter**: By date, contact, status
4. **Actions**: Reschedule, cancel, add notes

##### Meeting Follow-up
1. **Navigate**: Dashboard → Meetings
2. **Select Meeting**: Click on meeting
3. **Add Notes**: Enter meeting notes
4. **Update Status**: Mark as completed, rescheduled, cancelled
5. **Create Task**: Create follow-up task if needed

#### 5. Analytics & Reporting

##### Dashboard Overview
1. **Navigate**: Dashboard tab
2. **View Metrics**:
   - **Total Contacts**: Contacts in assigned industries
   - **Total Companies**: Companies in assigned industries
   - **Outreach Sent**: Messages sent this month
   - **Response Rate**: Percentage of responses
   - **Meetings Scheduled**: Upcoming meetings
3. **Charts**: Visual representation of metrics
4. **Recent Activity**: Latest outreach activities

##### Engagement Tracking
1. **Navigate**: Contacts tab
2. **Select Contact**: Click on contact name
3. **View History**: All interactions with contact
4. **Status**: Engagement status (Cold, Contacted, Engaged, Qualified, etc.)
5. **Notes**: Add notes about interactions

---

## Business User Guide

### Role Definition

**Business Users** have admin or user rights and help recommend building changes, plan future capabilities, and provide input for evolving Project VANI. They bridge the gap between technical implementation and business needs.

### Access Level
- **Variable**: Can be assigned admin or user rights
- **Feature Access**: Based on assigned permissions
- **Feedback Channels**: Direct access to development team
- **Planning Input**: Contribute to roadmap and feature planning

### Key Responsibilities

#### 1. Feature Recommendations

##### Identifying Improvement Opportunities
1. **Use Platform**: Actively use all assigned features
2. **Document Pain Points**: Note areas that need improvement
3. **Gather Feedback**: Collect feedback from end users
4. **Prioritize**: Rank improvements by business impact

##### Submitting Feature Requests
1. **Document Request**:
   - **Feature Name**: Clear, descriptive name
   - **Description**: What the feature should do
   - **Use Case**: Why it's needed
   - **Business Impact**: Expected benefits
   - **Priority**: High, Medium, Low
2. **Submit**: Via email, GitHub issues, or internal system
3. **Follow Up**: Track request status and provide additional context

##### Example Feature Requests
- **Bulk Message Templates**: Pre-defined templates for common scenarios
- **Advanced Analytics**: Deeper insights into outreach performance
- **Integration Requests**: Connect with additional tools (CRM, etc.)
- **Workflow Automation**: Automate repetitive tasks
- **Mobile App**: Mobile access to VANI platform

#### 2. Planning Future Capabilities

##### Self-Learning System Vision
**Goal**: Make VANI a self-learning system that can represent any company's Knowledge Base and cater to their perspective.

**Key Components**:
1. **Adaptive Knowledge Base**:
   - Automatically learn from company-specific documents
   - Adapt messaging to company's voice and style
   - Understand company-specific terminology
   - Learn from successful outreach patterns

2. **Multi-Company Knowledge Base**:
   - Support multiple companies in single instance
   - Company-specific knowledge isolation
   - Cross-company learning (with privacy controls)
   - Customizable company profiles

3. **AI Learning Mechanisms**:
   - **Feedback Loops**: Learn from user corrections
   - **Success Patterns**: Identify what works best
   - **Personalization**: Adapt to individual contact preferences
   - **Continuous Improvement**: Get better over time

##### Roadmap Planning
1. **Short-Term (3-6 months)**:
   - Enhanced Knowledge Base with company-specific collections
   - Improved AI personalization
   - Better analytics and reporting
   - Mobile-responsive UI

2. **Medium-Term (6-12 months)**:
   - Self-learning message generation
   - Multi-company Knowledge Base support
   - Advanced workflow automation
   - Integration marketplace

3. **Long-Term (12+ months)**:
   - Fully autonomous outreach system
   - Predictive analytics
   - Cross-company insights (privacy-preserved)
   - AI-powered strategy recommendations

##### Contributing to Roadmap
1. **Review Roadmap**: Understand current priorities
2. **Provide Input**: Share business priorities
3. **Validate Features**: Test beta features and provide feedback
4. **Prioritize**: Help prioritize features by business value

#### 3. Testing & Validation

##### Beta Feature Testing
1. **Access Beta Features**: Request access to new features
2. **Test Thoroughly**: Use features in real scenarios
3. **Document Issues**: Report bugs and issues
4. **Provide Feedback**: Share what works and what doesn't
5. **Suggest Improvements**: Recommend enhancements

##### User Acceptance Testing (UAT)
1. **Test Scenarios**: Follow test scenarios provided
2. **Document Results**: Record test outcomes
3. **Report Issues**: Document any problems found
4. **Sign Off**: Approve features for production

#### 4. Knowledge Base Contribution

##### Adding Company-Specific Content
1. **Navigate**: Admin → Knowledge Base
2. **Upload Documents**: Company-specific documents
3. **Tag Appropriately**: Use company, platform, service tags
4. **Maintain Quality**: Ensure content is accurate and current
5. **Regular Updates**: Keep Knowledge Base up-to-date

##### Best Practices
- **Organization**: Use consistent tagging and collections
- **Quality**: Only upload accurate, verified content
- **Completeness**: Include all relevant information
- **Updates**: Regularly review and update content

#### 5. Training & Documentation

##### Training End Users
1. **Create Training Materials**: Guides, videos, tutorials
2. **Conduct Training Sessions**: Train users on features
3. **Provide Support**: Answer questions and provide help
4. **Gather Feedback**: Collect training feedback

##### Documentation Contribution
1. **Review Documentation**: Check existing docs for accuracy
2. **Suggest Improvements**: Recommend documentation updates
3. **Create Examples**: Provide real-world examples
4. **Translate**: Help translate docs if needed

---

## Future Vision: Self-Learning & Multi-Company Knowledge Base

### Vision Statement

Transform VANI into a self-learning, adaptive platform that can represent any company's Knowledge Base and automatically adapt to their unique perspective, voice, and requirements.

### Key Capabilities

#### 1. Self-Learning System

##### Adaptive Message Generation
- **Learn from Success**: Analyze successful outreach messages
- **Pattern Recognition**: Identify what works for different industries/roles
- **Style Adaptation**: Adapt to company's communication style
- **Continuous Improvement**: Get better with each interaction

##### Feedback Integration
- **User Corrections**: Learn when users edit AI-generated content
- **Response Patterns**: Learn from contact responses
- **Success Metrics**: Correlate message content with success rates
- **Automatic Updates**: Update models based on feedback

##### Predictive Analytics
- **Best Time to Send**: Learn optimal sending times
- **Message Personalization**: Predict what content works best
- **Target Scoring**: Predict which targets are most likely to respond
- **Channel Selection**: Recommend best channel per contact

#### 2. Multi-Company Knowledge Base

##### Company-Specific Collections
- **Isolated Knowledge**: Each company has its own Knowledge Base
- **Custom Tagging**: Company-specific metadata and tags
- **Privacy Controls**: Ensure data isolation between companies
- **Custom Schemas**: Flexible metadata schemas per company

##### Cross-Company Learning (Privacy-Preserved)
- **Anonymized Patterns**: Learn from patterns without exposing data
- **Best Practices**: Share anonymized best practices
- **Industry Insights**: Aggregate industry-level insights
- **Opt-In Sharing**: Companies choose what to share

##### Knowledge Base Management
- **Bulk Import**: Import entire company Knowledge Bases
- **Version Control**: Track changes to Knowledge Base
- **Access Control**: Granular permissions per company
- **Analytics**: Track Knowledge Base usage and effectiveness

#### 3. Implementation Roadmap

##### Phase 1: Foundation (Months 1-3)
- Enhanced Knowledge Base with company-specific collections
- Basic feedback loop for message generation
- Improved tagging and metadata system
- Multi-company data isolation

##### Phase 2: Learning (Months 4-6)
- Feedback integration system
- Pattern recognition for successful messages
- Adaptive personalization engine
- Analytics dashboard for learning metrics

##### Phase 3: Automation (Months 7-9)
- Self-improving message generation
- Predictive target scoring
- Automated A/B testing
- Advanced workflow automation

##### Phase 4: Intelligence (Months 10-12)
- Fully autonomous outreach system
- Cross-company insights (privacy-preserved)
- AI-powered strategy recommendations
- Natural language interface for Knowledge Base

### Technical Requirements

#### Infrastructure
- **Scalable Storage**: Support for large Knowledge Bases
- **Vector Database**: Enhanced ChromaDB for multi-company support
- **ML Pipeline**: Infrastructure for continuous learning
- **Privacy Controls**: Strong data isolation and encryption

#### APIs & Integrations
- **Knowledge Base API**: Enhanced API for multi-company support
- **Learning API**: API for feedback and learning data
- **Analytics API**: API for learning metrics and insights
- **Integration Framework**: Easy integration with external systems

#### Security & Privacy
- **Data Isolation**: Strong isolation between companies
- **Access Control**: Granular permissions per company
- **Encryption**: End-to-end encryption for sensitive data
- **Compliance**: GDPR, CCPA, and other privacy regulations

---

## Quick Reference

### Role Comparison

| Feature | Super Admin | Administrator | User | Business User |
|---------|------------|--------------|------|--------------|
| Infrastructure Management | ✅ | ❌ | ❌ | ❌ |
| Code Deployment | ✅ | ❌ | ❌ | ❌ |
| User Management | ✅ | ✅ | ❌ | ⚠️ (if admin) |
| Industry Management | ✅ | ✅ | ❌ | ⚠️ (if admin) |
| Knowledge Base Management | ✅ | ✅ | ⚠️ (query only) | ⚠️ (varies) |
| Contact/Company Management | ✅ | ✅ | ✅ | ✅ |
| Outreach | ✅ | ✅ | ✅ | ✅ |
| AI Target Finder | ✅ | ✅ | ⚠️ (if permission) | ⚠️ (if permission) |
| Analytics | ✅ | ✅ | ✅ | ✅ |

### Common Tasks

#### Super Admin
- Deploy code: `docker-compose up -d vani`
- Check logs: `docker logs vani -f`
- Create user: SQL or Admin UI
- Backup database: Supabase Dashboard

#### Administrator
- Create industry: Admin → User Management → Industries
- Assign user: Admin → User Management → Edit User
- Upload KB: Admin → Knowledge Base → Upload Documents
- Create signature: Admin → Signatures → Add Signature

#### User
- Find targets: AI Target Finder tab
- Send email: Contacts → Select → Send Email
- Generate pitch: Companies → Select → Generate Pitch
- Schedule meeting: Contacts → Select → Schedule Meeting

#### Business User
- Submit feature request: Email or GitHub
- Test beta features: Request access
- Contribute KB: Admin → Knowledge Base → Upload
- Provide feedback: Direct to development team

### Support & Resources

- **Documentation**: `README.md`, `VANI_FEATURES_OVERVIEW.md`
- **API Documentation**: Check API route files in `app/api/`
- **Database Schema**: Check migrations in `app/migrations/`
- **Troubleshooting**: See Super Administrator Guide
- **Feature Requests**: Submit via GitHub Issues or email

---

**Document Version**: 2.0  
**Last Updated**: January 2025  
**Maintained By**: VANI Development Team  
**Contact**: [Your Contact Information]



