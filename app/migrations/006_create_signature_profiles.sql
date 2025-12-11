-- Migration: Create signature_profiles table
-- Description: Stores signature profiles for different channels (Email, WhatsApp, LinkedIn)
-- Date: 2025-12

-- Create signature_profiles table
CREATE TABLE IF NOT EXISTS signature_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    from_name VARCHAR(255) NOT NULL,
    from_email VARCHAR(255) NOT NULL,
    reply_to VARCHAR(255),
    signature_json JSONB DEFAULT '{}'::jsonb,
    calendar_link TEXT,
    cta_text VARCHAR(255),
    cta_button VARCHAR(255),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES app_users(id),
    
    -- Ensure unique email per profile
    CONSTRAINT unique_from_email UNIQUE (from_email)
);

-- Create index on from_email for quick lookups
CREATE INDEX IF NOT EXISTS idx_signature_profiles_from_email ON signature_profiles(from_email);

-- Create index on is_default for default signature lookup
CREATE INDEX IF NOT EXISTS idx_signature_profiles_is_default ON signature_profiles(is_default) WHERE is_default = TRUE;

-- Add comment
COMMENT ON TABLE signature_profiles IS 'Signature profiles for different communication channels';
COMMENT ON COLUMN signature_profiles.signature_json IS 'JSON containing title, company, phone, website, linkedin, address, etc.';
COMMENT ON COLUMN signature_profiles.is_default IS 'Whether this is the default signature to use when no specific signature is assigned';




