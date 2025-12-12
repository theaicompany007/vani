-- Multiple Industry Assignment & Default Industry
-- Allows users to be assigned to multiple industries with a default selection

-- Create user_industries junction table for many-to-many relationship
CREATE TABLE IF NOT EXISTS user_industries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    industry_id UUID NOT NULL REFERENCES industries(id) ON DELETE CASCADE,
    is_default BOOLEAN DEFAULT FALSE, -- One default per user
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES app_users(id) ON DELETE SET NULL,
    UNIQUE(user_id, industry_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_industries_user_id ON user_industries(user_id);
CREATE INDEX IF NOT EXISTS idx_user_industries_industry_id ON user_industries(industry_id);
CREATE INDEX IF NOT EXISTS idx_user_industries_default ON user_industries(user_id, is_default) WHERE is_default = TRUE;

-- Add default_industry_id to app_users (for quick access)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS default_industry_id UUID REFERENCES industries(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_app_users_default_industry ON app_users(default_industry_id);

-- Migrate existing data: If user has industry_id, create entry in user_industries
INSERT INTO user_industries (user_id, industry_id, is_default)
SELECT id, industry_id, TRUE
FROM app_users
WHERE industry_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM user_industries 
    WHERE user_id = app_users.id AND industry_id = app_users.industry_id
);

-- Also migrate active_industry_id if different
INSERT INTO user_industries (user_id, industry_id, is_default)
SELECT id, active_industry_id, FALSE
FROM app_users
WHERE active_industry_id IS NOT NULL
AND active_industry_id != industry_id
AND NOT EXISTS (
    SELECT 1 FROM user_industries 
    WHERE user_id = app_users.id AND industry_id = app_users.active_industry_id
);

-- Set default_industry_id from existing active_industry_id or industry_id
UPDATE app_users
SET default_industry_id = COALESCE(active_industry_id, industry_id)
WHERE default_industry_id IS NULL
AND (active_industry_id IS NOT NULL OR industry_id IS NOT NULL);

-- Ensure only one default per user
CREATE OR REPLACE FUNCTION ensure_single_default_industry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        -- Remove default flag from other industries for this user
        UPDATE user_industries
        SET is_default = FALSE
        WHERE user_id = NEW.user_id
        AND id != NEW.id
        AND is_default = TRUE;
        
        -- Update app_users.default_industry_id
        UPDATE app_users
        SET default_industry_id = NEW.industry_id
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ensure_single_default_industry
AFTER INSERT OR UPDATE ON user_industries
FOR EACH ROW
WHEN (NEW.is_default = TRUE)
EXECUTE FUNCTION ensure_single_default_industry();







