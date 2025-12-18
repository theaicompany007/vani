-- Migration 016: Create AI Target Search Results table
-- Stores search history and results for AI Target Finder

CREATE TABLE IF NOT EXISTS ai_target_search_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    industry_id UUID REFERENCES industries(id) ON DELETE SET NULL,
    search_config JSONB NOT NULL, -- {industries: [], min_seniority: 0.7, limit: 10, preset: "high_priority"}
    results JSONB NOT NULL, -- Array of recommendations
    result_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) DEFAULT 'completed', -- completed, failed, partial
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_search_results_user ON ai_target_search_results(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_search_results_created ON ai_target_search_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_search_results_status ON ai_target_search_results(status);

-- Add updated_at trigger
CREATE TRIGGER update_ai_search_results_updated_at 
    BEFORE UPDATE ON ai_target_search_results
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment
COMMENT ON TABLE ai_target_search_results IS 'Stores AI Target Finder search history and results for each user';
COMMENT ON COLUMN ai_target_search_results.search_config IS 'JSON object containing search parameters: industries array, min_seniority, limit, preset name';
COMMENT ON COLUMN ai_target_search_results.results IS 'JSON array of TargetRecommendation objects from the search';













