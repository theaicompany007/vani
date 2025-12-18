-- Contacts table for Contact & Company Management
CREATE TABLE IF NOT EXISTS contacts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    role TEXT,
    email TEXT,
    linkedin TEXT,
    phone TEXT,
    lead_source TEXT,
    company TEXT, -- Keep company name as text for backward compatibility
    city TEXT,
    industry TEXT,
    sheet TEXT, -- Excel sheet name
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Case-insensitive unique index on email to support upsert by email
CREATE UNIQUE INDEX IF NOT EXISTS contacts_email_lower_idx ON contacts (lower(email)) WHERE email IS NOT NULL;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_contacts_industry ON contacts(industry);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);

-- Add updated_at trigger
CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();




















