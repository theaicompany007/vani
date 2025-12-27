-- Add industry-specific metrics to industry_persona_mappings table
-- These metrics enable personalization of Situation Room, Arbitrage, and Revenue Simulator tabs

ALTER TABLE industry_persona_mappings
ADD COLUMN IF NOT EXISTS cost_per_visit DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS default_aov DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS store_count_min INTEGER,
ADD COLUMN IF NOT EXISTS store_count_max INTEGER,
ADD COLUMN IF NOT EXISTS coverage_gap_percentage INTEGER;

-- Add comments
COMMENT ON COLUMN industry_persona_mappings.cost_per_visit IS 'Industry-specific cost per human visit (e.g., ₹300 for FMCG)';
COMMENT ON COLUMN industry_persona_mappings.default_aov IS 'Default Average Order Value for revenue simulator';
COMMENT ON COLUMN industry_persona_mappings.store_count_min IS 'Minimum store count for revenue simulator (e.g., 1000 for pilot)';
COMMENT ON COLUMN industry_persona_mappings.store_count_max IS 'Maximum store count for revenue simulator (e.g., 100000 for enterprise)';
COMMENT ON COLUMN industry_persona_mappings.coverage_gap_percentage IS 'Coverage gap percentage (e.g., 80 for FMCG)';

-- Set default values for existing FMCG mapping (if exists)
UPDATE industry_persona_mappings
SET 
    cost_per_visit = 300.00,
    default_aov = 2000.00,
    store_count_min = 1000,
    store_count_max = 100000,
    coverage_gap_percentage = 80
WHERE industry_name = 'FMCG' AND cost_per_visit IS NULL;

-- Set default values for Financial Services
UPDATE industry_persona_mappings
SET 
    cost_per_visit = 500.00,
    default_aov = 5000.00,
    store_count_min = 10000,
    store_count_max = 1000000,
    coverage_gap_percentage = 60
WHERE industry_name IN ('Financial Services', 'Banking', 'FinTech') AND cost_per_visit IS NULL;

-- Set default values for Manufacturing/B2B
UPDATE industry_persona_mappings
SET 
    cost_per_visit = 1000.00,
    default_aov = 10000.00,
    store_count_min = 500,
    store_count_max = 50000,
    coverage_gap_percentage = 70
WHERE industry_name IN ('Manufacturing', 'B2B', 'Exports') AND cost_per_visit IS NULL;




