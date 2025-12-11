-- Add Industry Support to Existing Tables
-- Run this in your Supabase SQL Editor

-- Add industry_id to targets table
ALTER TABLE targets 
ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id) ON DELETE SET NULL;

-- Add industry_id to outreach_activities table
ALTER TABLE outreach_activities 
ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id) ON DELETE SET NULL;

-- Add industry_id to meetings table
ALTER TABLE meetings 
ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id) ON DELETE SET NULL;

-- Add industry_id to outreach_sequences table
ALTER TABLE outreach_sequences 
ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id) ON DELETE SET NULL;

-- Create indexes for industry filtering
CREATE INDEX IF NOT EXISTS idx_targets_industry ON targets(industry_id);
CREATE INDEX IF NOT EXISTS idx_activities_industry ON outreach_activities(industry_id);
CREATE INDEX IF NOT EXISTS idx_meetings_industry ON meetings(industry_id);
CREATE INDEX IF NOT EXISTS idx_sequences_industry ON outreach_sequences(industry_id);

-- Set default industry for existing records (optional - you may want to manually assign)
-- UPDATE targets SET industry_id = (SELECT id FROM industries WHERE code = 'FMCG' LIMIT 1) WHERE industry_id IS NULL;
-- UPDATE outreach_activities SET industry_id = (SELECT id FROM industries WHERE code = 'FMCG' LIMIT 1) WHERE industry_id IS NULL;
