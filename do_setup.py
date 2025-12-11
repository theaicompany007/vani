import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env')
load_dotenv('.env.local', override=True)

conn = psycopg2.connect(os.getenv('SUPABASE_CONNECTION'))
cur = conn.cursor()

print("=" * 60)
print("SETTING UP DATABASE AND SUPER USER")
print("=" * 60)

# 1. Industries
print("\n1. Creating industries table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS industries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
""")
conn.commit()
cur.execute("""
INSERT INTO industries (name, code, description) VALUES
    ('FMCG', 'FMCG', 'Fast Moving Consumer Goods - HUL, Britannia, Asian Paints, etc.'),
    ('Food & Beverages', 'FOOD_BEVERAGES', 'Food & Beverages - Domino''s, Pizza Hut, Starbucks, etc.')
ON CONFLICT (code) DO NOTHING
""")
conn.commit()
print("✅ Industries table created")

# 2. App Users
print("\n2. Creating app_users table...")
cur.execute("""
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
)
""")
conn.commit()
print("✅ app_users table created")

# 3. Use Cases
print("\n3. Creating use_cases table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS use_cases (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
""")
conn.commit()
cur.execute("""
INSERT INTO use_cases (code, name, description) VALUES
    ('outreach', 'Outreach', 'Send outreach messages via Email, WhatsApp, LinkedIn'),
    ('pitch_presentation', 'Pitch Presentation', 'Generate and send AI-powered pitch presentations'),
    ('analytics', 'Analytics', 'View dashboard analytics and engagement metrics'),
    ('target_management', 'Target Management', 'Add, edit, and manage target companies'),
    ('meetings', 'Meetings', 'Schedule and manage meetings via Cal.com'),
    ('sheets_import_export', 'Google Sheets Import/Export', 'Import and export data from Google Sheets'),
    ('ai_message_generation', 'AI Message Generation', 'Generate AI-powered outreach messages')
ON CONFLICT (code) DO NOTHING
""")
conn.commit()
print("✅ use_cases table created")

# 4. User Permissions
print("\n4. Creating user_permissions table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS user_permissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    use_case_id UUID NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
    industry_id UUID REFERENCES industries(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES app_users(id) ON DELETE SET NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, use_case_id, industry_id)
)
""")
conn.commit()
print("✅ user_permissions table created")

# 5. Generated Pitches
print("\n5. Creating generated_pitches table...")
cur.execute("""
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
)
""")
conn.commit()
print("✅ generated_pitches table created")

# 6. Add industry_id to existing tables
print("\n6. Adding industry_id to existing tables...")
for table in ['targets', 'outreach_activities', 'meetings', 'outreach_sequences']:
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id) ON DELETE SET NULL")
        conn.commit()
        print(f"  ✅ {table}")
    except Exception as e:
        print(f"  ⚠️  {table}: {str(e)[:50]}")

# 7. Create Super User
print("\n7. Creating super user...")
cur.execute("""
INSERT INTO app_users (supabase_user_id, email, name, is_super_user, is_industry_admin)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (supabase_user_id) DO UPDATE SET
    is_super_user = EXCLUDED.is_super_user,
    is_industry_admin = EXCLUDED.is_industry_admin,
    email = EXCLUDED.email
""", ('eb98e4aa-96cc-48d1-ba60-96cc541c4fdf', 'rajvins@theaicompany.co', 'Super Admin', True, True))
conn.commit()

cur.execute("SELECT id FROM app_users WHERE supabase_user_id = %s", ('eb98e4aa-96cc-48d1-ba60-96cc541c4fdf',))
app_user_id = cur.fetchone()[0]
print(f"✅ Super user created: {app_user_id}")

# 8. Grant permissions
print("\n8. Granting all permissions...")
cur.execute("""
INSERT INTO user_permissions (user_id, use_case_id, industry_id, granted_by)
SELECT %s, uc.id, NULL, %s
FROM use_cases uc
ON CONFLICT (user_id, use_case_id, industry_id) DO NOTHING
""", (app_user_id, app_user_id))
conn.commit()

cur.execute("SELECT COUNT(*) FROM user_permissions WHERE user_id = %s", (app_user_id,))
count = cur.fetchone()[0]
print(f"✅ Granted {count} permissions")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ SETUP COMPLETE!")
print("=" * 60)
print("Email: rajvins@theaicompany.co")
print(f"User ID: {app_user_id}")
print(f"Permissions: {count} use cases")
print("\n💡 Start app: python run.py")
print("💡 Login: http://localhost:5000/login")
print("=" * 60)

