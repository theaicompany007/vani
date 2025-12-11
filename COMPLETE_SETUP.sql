-- ============================================================
-- PROJECT VANI - COMPLETE DATABASE SETUP
-- Run this ENTIRE file in Supabase SQL Editor
-- ============================================================

-- ============================================================
-- STEP 1: Industries & Multi-Tenant Support
-- ============================================================
CREATE TABLE IF NOT EXISTS industries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO industries (name, code, description) VALUES
    ('FMCG', 'FMCG', 'Fast Moving Consumer Goods - HUL, Britannia, Asian Paints, etc.'),
    ('Food & Beverages', 'FOOD_BEVERAGES', 'Food & Beverages - Domino''s, Pizza Hut, Starbucks, etc.')
ON CONFLICT (code) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_industries_code ON industries(code);

CREATE TRIGGER update_industries_updated_at BEFORE UPDATE ON industries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- STEP 2: Authentication & Permissions System
-- ============================================================
CREATE TABLE IF NOT EXISTS app_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    supabase_user_id UUID UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    industry_id UUID REFERENCES industries(id) ON DELETE SET NULL,
    is_super_user BOOLEAN DEFAULT FALSE,
    is_industry_admin BOOLEAN DEFAULT FALSE,
    active_industry_id UUID REFERENCES industries(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS use_cases (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO use_cases (code, name, description) VALUES
    ('outreach', 'Outreach', 'Send outreach messages via Email, WhatsApp, LinkedIn'),
    ('pitch_presentation', 'Pitch Presentation', 'Generate and send AI-powered pitch presentations'),
    ('analytics', 'Analytics', 'View dashboard analytics and engagement metrics'),
    ('target_management', 'Target Management', 'Add, edit, and manage target companies'),
    ('meetings', 'Meetings', 'Schedule and manage meetings via Cal.com'),
    ('sheets_import_export', 'Google Sheets Import/Export', 'Import and export data from Google Sheets'),
    ('ai_message_generation', 'AI Message Generation', 'Generate AI-powered outreach messages')
ON CONFLICT (code) DO NOTHING;

CREATE TABLE IF NOT EXISTS user_permissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    use_case_id UUID NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
    industry_id UUID REFERENCES industries(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES app_users(id) ON DELETE SET NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, use_case_id, industry_id)
);

CREATE INDEX IF NOT EXISTS idx_app_users_supabase_id ON app_users(supabase_user_id);
CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email);
CREATE INDEX IF NOT EXISTS idx_app_users_industry ON app_users(industry_id);
CREATE INDEX IF NOT EXISTS idx_app_users_super_user ON app_users(is_super_user);
CREATE INDEX IF NOT EXISTS idx_use_cases_code ON use_cases(code);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_use_case ON user_permissions(use_case_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_industry ON user_permissions(industry_id);

CREATE TRIGGER update_app_users_updated_at BEFORE UPDATE ON app_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- STEP 3: Pitch Content Storage
-- ============================================================
CREATE TABLE IF NOT EXISTS generated_pitches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    target_id UUID NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    industry_id UUID REFERENCES industries(id) ON DELETE SET NULL,
    html_content TEXT NOT NULL,
    title TEXT,
    problem_statement TEXT,
    solution_description TEXT,
    hit_list_content TEXT,
    trojan_horse_strategy TEXT,
    ai_model VARCHAR(100),
    ai_tokens_used INTEGER,
    generation_metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE outreach_activities 
ADD COLUMN IF NOT EXISTS pitch_id UUID REFERENCES generated_pitches(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_generated_pitches_target ON generated_pitches(target_id);
CREATE INDEX IF NOT EXISTS idx_generated_pitches_industry ON generated_pitches(industry_id);
CREATE INDEX IF NOT EXISTS idx_activities_pitch ON outreach_activities(pitch_id);

CREATE TRIGGER update_generated_pitches_updated_at BEFORE UPDATE ON generated_pitches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- STEP 4: Add Industry Support to Existing Tables
-- ============================================================
ALTER TABLE targets 
ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id) ON DELETE SET NULL;

ALTER TABLE outreach_activities 
ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id) ON DELETE SET NULL;

ALTER TABLE meetings 
ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id) ON DELETE SET NULL;

ALTER TABLE outreach_sequences 
ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_targets_industry ON targets(industry_id);
CREATE INDEX IF NOT EXISTS idx_activities_industry ON outreach_activities(industry_id);
CREATE INDEX IF NOT EXISTS idx_meetings_industry ON meetings(industry_id);
CREATE INDEX IF NOT EXISTS idx_sequences_industry ON outreach_sequences(industry_id);

-- ============================================================
-- STEP 5: Create Super User
-- ============================================================
INSERT INTO app_users (supabase_user_id, email, name, is_super_user, is_industry_admin)
VALUES (
    'eb98e4aa-96cc-48d1-ba60-96cc541c4fdf',
    'rajvins@theaicompany.co',
    'Super Admin',
    true,
    true
)
ON CONFLICT (supabase_user_id) 
DO UPDATE SET 
    is_super_user = true,
    is_industry_admin = true,
    email = 'rajvins@theaicompany.co';

-- ============================================================
-- STEP 6: Grant All Permissions to Super User
-- ============================================================
INSERT INTO user_permissions (user_id, use_case_id, industry_id, granted_by)
SELECT 
    (SELECT id FROM app_users WHERE supabase_user_id = 'eb98e4aa-96cc-48d1-ba60-96cc541c4fdf'),
    uc.id,
    NULL,  -- NULL = all industries (super user)
    (SELECT id FROM app_users WHERE supabase_user_id = 'eb98e4aa-96cc-48d1-ba60-96cc541c4fdf')
FROM use_cases uc
ON CONFLICT (user_id, use_case_id, industry_id) DO NOTHING;

-- ============================================================
-- VERIFY SETUP
-- ============================================================
SELECT 
    'Setup Complete!' as status,
    (SELECT COUNT(*) FROM industries) as industries_count,
    (SELECT COUNT(*) FROM use_cases) as use_cases_count,
    (SELECT COUNT(*) FROM app_users WHERE is_super_user = true) as super_users_count,
    (SELECT COUNT(*) FROM user_permissions WHERE user_id = (SELECT id FROM app_users WHERE email = 'rajvins@theaicompany.co')) as permissions_count;

