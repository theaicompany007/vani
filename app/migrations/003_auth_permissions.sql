-- Authentication & Permissions System
-- Run this in your Supabase SQL Editor

-- App Users table - links Supabase auth users to app
CREATE TABLE IF NOT EXISTS app_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    supabase_user_id UUID UNIQUE NOT NULL, -- Links to auth.users.id
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    industry_id UUID REFERENCES industries(id) ON DELETE SET NULL, -- NULL for global super users
    is_super_user BOOLEAN DEFAULT FALSE, -- Global super user can manage all industries
    is_industry_admin BOOLEAN DEFAULT FALSE, -- Industry-specific admin
    active_industry_id UUID REFERENCES industries(id) ON DELETE SET NULL, -- Current active industry context
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Use Cases table - defines available use cases
CREATE TABLE IF NOT EXISTS use_cases (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE, -- e.g., 'outreach', 'pitch_presentation'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed use cases
INSERT INTO use_cases (code, name, description) VALUES
    ('outreach', 'Outreach', 'Send outreach messages via Email, WhatsApp, LinkedIn'),
    ('pitch_presentation', 'Pitch Presentation', 'Generate and send AI-powered pitch presentations'),
    ('analytics', 'Analytics', 'View dashboard analytics and engagement metrics'),
    ('target_management', 'Target Management', 'Add, edit, and manage target companies'),
    ('meetings', 'Meetings', 'Schedule and manage meetings via Cal.com'),
    ('sheets_import_export', 'Google Sheets Import/Export', 'Import and export data from Google Sheets'),
    ('ai_message_generation', 'AI Message Generation', 'Generate AI-powered outreach messages')
ON CONFLICT (code) DO NOTHING;

-- User Permissions table - many-to-many: users ↔ use_cases
CREATE TABLE IF NOT EXISTS user_permissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    use_case_id UUID NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
    industry_id UUID REFERENCES industries(id) ON DELETE CASCADE, -- NULL = all industries (super user only)
    granted_by UUID REFERENCES app_users(id) ON DELETE SET NULL, -- Who granted this permission
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, use_case_id, industry_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_app_users_supabase_id ON app_users(supabase_user_id);
CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email);
CREATE INDEX IF NOT EXISTS idx_app_users_industry ON app_users(industry_id);
CREATE INDEX IF NOT EXISTS idx_app_users_super_user ON app_users(is_super_user);
CREATE INDEX IF NOT EXISTS idx_use_cases_code ON use_cases(code);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_use_case ON user_permissions(use_case_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_industry ON user_permissions(industry_id);

-- Add updated_at trigger
CREATE TRIGGER update_app_users_updated_at BEFORE UPDATE ON app_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
