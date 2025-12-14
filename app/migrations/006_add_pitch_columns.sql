-- Add missing columns to generated_pitches table
-- Run this in Supabase SQL Editor

-- Add generated_content column (JSONB) to store full AI-generated content
ALTER TABLE generated_pitches 
ADD COLUMN IF NOT EXISTS generated_content JSONB;

-- Add sent_at and sent_channel columns if they don't exist
ALTER TABLE generated_pitches 
ADD COLUMN IF NOT EXISTS sent_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE generated_pitches 
ADD COLUMN IF NOT EXISTS sent_channel VARCHAR(50);

-- Add generated_at column (alias for created_at, but we'll use created_at in code)
-- Actually, let's just ensure created_at exists and use that
-- The code will be updated to use created_at instead of generated_at



















