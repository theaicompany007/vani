-- Industries & Multi-Tenant Support
-- Run this in your Supabase SQL Editor

-- Industries table - supports multi-industry tenant model
CREATE TABLE IF NOT EXISTS industries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'FMCG', 'FOOD_BEVERAGES'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed initial industries
INSERT INTO industries (name, code, description) VALUES
    ('FMCG', 'FMCG', 'Fast Moving Consumer Goods - HUL, Britannia, Asian Paints, etc.'),
    ('Food & Beverages', 'FOOD_BEVERAGES', 'Food & Beverages - Domino''s, Pizza Hut, Starbucks, etc.')
ON CONFLICT (code) DO NOTHING;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_industries_code ON industries(code);

-- Add updated_at trigger
CREATE TRIGGER update_industries_updated_at BEFORE UPDATE ON industries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
