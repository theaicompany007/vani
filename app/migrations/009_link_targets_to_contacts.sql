-- Link targets to contacts and companies
ALTER TABLE targets 
ADD COLUMN IF NOT EXISTS contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE SET NULL;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_targets_contact_id ON targets(contact_id);
CREATE INDEX IF NOT EXISTS idx_targets_company_id ON targets(company_id);

-- Optional: Try to link existing targets to contacts/companies by email/company_name match
-- This is a best-effort matching - may not match all targets
UPDATE targets t
SET contact_id = c.id
FROM contacts c
WHERE t.contact_id IS NULL 
  AND t.email IS NOT NULL 
  AND LOWER(t.email) = LOWER(c.email)
  AND c.id IS NOT NULL;

UPDATE targets t
SET company_id = c.id
FROM companies c
WHERE t.company_id IS NULL 
  AND t.company_name IS NOT NULL 
  AND LOWER(TRIM(t.company_name)) = LOWER(TRIM(c.name))
  AND c.id IS NOT NULL;




















