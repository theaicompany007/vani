-- Make company name optional (some contacts don't have company names)
-- We'll use domain as the primary identifier and enrich with AI when needed

ALTER TABLE companies ALTER COLUMN name DROP NOT NULL;

-- Add comment
COMMENT ON COLUMN companies.name IS 'Company name (optional, can be enriched from domain using AI)';
COMMENT ON COLUMN companies.domain IS 'Company domain (primary identifier for enrichment)';










