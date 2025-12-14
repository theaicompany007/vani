-- Industry Persona Mappings Table
-- Stores customizable persona mappings for industries
-- Allows admins to edit pain points, use cases, and value propositions

CREATE TABLE IF NOT EXISTS industry_persona_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_name TEXT NOT NULL UNIQUE,
    vani_persona TEXT NOT NULL,
    persona_description TEXT,
    pain_points JSONB DEFAULT '[]'::jsonb, -- Array of strings
    use_case_examples JSONB DEFAULT '[]'::jsonb, -- Array of strings
    value_proposition_template TEXT,
    common_use_cases JSONB DEFAULT '[]'::jsonb, -- Array of strings
    is_custom BOOLEAN DEFAULT false, -- true if user-edited, false if from default mapping
    created_by UUID REFERENCES app_users(id),
    updated_by UUID REFERENCES app_users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Index for fast lookups by industry name
CREATE INDEX IF NOT EXISTS idx_industry_persona_mappings_industry_name ON industry_persona_mappings(industry_name);

-- Index for persona lookups
CREATE INDEX IF NOT EXISTS idx_industry_persona_mappings_persona ON industry_persona_mappings(vani_persona);

-- Index for custom mappings
CREATE INDEX IF NOT EXISTS idx_industry_persona_mappings_custom ON industry_persona_mappings(is_custom);

COMMENT ON TABLE industry_persona_mappings IS 'Stores customizable persona mappings for industries. Allows admins to edit pain points, use cases, and value propositions per industry.';
COMMENT ON COLUMN industry_persona_mappings.industry_name IS 'Name of the industry (must match industries.name)';
COMMENT ON COLUMN industry_persona_mappings.vani_persona IS 'VANI Persona assigned to this industry';
COMMENT ON COLUMN industry_persona_mappings.pain_points IS 'JSON array of pain points for this industry';
COMMENT ON COLUMN industry_persona_mappings.use_case_examples IS 'JSON array of use case examples';
COMMENT ON COLUMN industry_persona_mappings.value_proposition_template IS 'Value proposition template text';
COMMENT ON COLUMN industry_persona_mappings.is_custom IS 'True if this mapping was edited by a user, false if from default mapping';



