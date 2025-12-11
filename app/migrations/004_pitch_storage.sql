-- Pitch Content Storage
-- Run this in your Supabase SQL Editor

-- Generated Pitches table - stores AI-generated pitch presentations
CREATE TABLE IF NOT EXISTS generated_pitches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    target_id UUID NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    industry_id UUID REFERENCES industries(id) ON DELETE SET NULL,
    html_content TEXT NOT NULL, -- Full HTML pitch presentation
    title TEXT,
    problem_statement TEXT,
    solution_description TEXT,
    hit_list_content TEXT, -- Company-specific hit list card
    trojan_horse_strategy TEXT,
    ai_model VARCHAR(100), -- e.g., 'gpt-4', 'gpt-3.5-turbo'
    ai_tokens_used INTEGER,
    generation_metadata JSONB DEFAULT '{}'::JSONB, -- Store prompt, temperature, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Link pitches to outreach activities
ALTER TABLE outreach_activities 
ADD COLUMN IF NOT EXISTS pitch_id UUID REFERENCES generated_pitches(id) ON DELETE SET NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_generated_pitches_target ON generated_pitches(target_id);
CREATE INDEX IF NOT EXISTS idx_generated_pitches_industry ON generated_pitches(industry_id);
CREATE INDEX IF NOT EXISTS idx_activities_pitch ON outreach_activities(pitch_id);

-- Add updated_at trigger
CREATE TRIGGER update_generated_pitches_updated_at BEFORE UPDATE ON generated_pitches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
