-- Migration 017: Contact Processing Tracking
-- Tracks which contacts have been analyzed or converted to targets to prevent duplicate recommendations

-- Option 1: Add columns to contacts table (simpler, better performance)
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS is_target BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS last_analyzed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS analysis_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_target_created_at TIMESTAMPTZ;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_contacts_is_target ON contacts(is_target) WHERE is_target = true;
CREATE INDEX IF NOT EXISTS idx_contacts_last_analyzed_at ON contacts(last_analyzed_at) WHERE last_analyzed_at IS NOT NULL;

-- Backfill: Mark existing contacts that are already targets
UPDATE contacts c
SET is_target = true,
    last_target_created_at = COALESCE(
        (SELECT MIN(t.created_at) FROM targets t WHERE t.contact_id = c.id),
        now()
    )
WHERE EXISTS (
    SELECT 1 FROM targets t WHERE t.contact_id = c.id
);

-- Add comments for documentation
COMMENT ON COLUMN contacts.is_target IS 'True if this contact has been converted to a target';
COMMENT ON COLUMN contacts.last_analyzed_at IS 'Timestamp when contact was last analyzed by AI Target Finder';
COMMENT ON COLUMN contacts.analysis_count IS 'Number of times this contact has been analyzed';
COMMENT ON COLUMN contacts.last_target_created_at IS 'Timestamp when target was created from this contact';



