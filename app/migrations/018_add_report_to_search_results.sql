-- Migration 018: Add report storage to AI Target Search Results
-- Stores generated reports so they can be recalled without regenerating

ALTER TABLE ai_target_search_results 
ADD COLUMN IF NOT EXISTS report TEXT,
ADD COLUMN IF NOT EXISTS report_generated_at TIMESTAMP WITH TIME ZONE;

-- Add index for faster report lookups
CREATE INDEX IF NOT EXISTS idx_ai_search_results_report ON ai_target_search_results(report_generated_at DESC) 
WHERE report IS NOT NULL;

-- Add comment
COMMENT ON COLUMN ai_target_search_results.report IS 'Stores the generated markdown report for this search';
COMMENT ON COLUMN ai_target_search_results.report_generated_at IS 'Timestamp when the report was generated';






