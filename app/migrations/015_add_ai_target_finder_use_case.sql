-- Migration 015: Add AI Target Finder Use Case
-- Description: Adds the ai_target_finder use case for AI-powered target identification
-- Date: 2025-12-11

-- Insert the ai_target_finder use case
INSERT INTO use_cases (code, name, description, is_active)
VALUES (
    'ai_target_finder',
    'AI Target Finder',
    'Access to AI-powered target identification and recommendation engine',
    true
)
ON CONFLICT (code) DO UPDATE
SET 
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Grant ai_target_finder to all existing super users
INSERT INTO user_permissions (user_id, use_case_id)
SELECT 
    au.id,
    uc.id
FROM app_users au
CROSS JOIN use_cases uc
WHERE au.is_super_user = true
  AND uc.code = 'ai_target_finder'
  AND NOT EXISTS (
    SELECT 1 FROM user_permissions up
    WHERE up.user_id = au.id AND up.use_case_id = uc.id
  );

-- Grant ai_target_finder to all existing industry admins
INSERT INTO user_permissions (user_id, use_case_id)
SELECT 
    au.id,
    uc.id
FROM app_users au
CROSS JOIN use_cases uc
WHERE au.is_industry_admin = true
  AND uc.code = 'ai_target_finder'
  AND NOT EXISTS (
    SELECT 1 FROM user_permissions up
    WHERE up.user_id = au.id AND up.use_case_id = uc.id
  );

-- Log the migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 015 completed: AI Target Finder use case added';
END $$;

