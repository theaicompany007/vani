-- Migration: Create import_jobs table for background contact imports
-- Supports large file imports with progress tracking

CREATE TABLE IF NOT EXISTS import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES app_users(id) ON DELETE SET NULL,  -- Nullable: can be NULL if app_user doesn't exist
    supabase_user_id UUID,  -- Store Supabase Auth user ID as fallback for lookup
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    imported_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    error_details JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    file_name VARCHAR(255),
    file_size BIGINT,
    options JSONB DEFAULT '{}'::jsonb,  -- Store import options (updateExisting, importOnlyNew, etc.)
    progress_message TEXT,
    industry_id UUID REFERENCES industries(id) ON DELETE SET NULL,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_import_jobs_user_id ON import_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_import_jobs_status ON import_jobs(status);
CREATE INDEX IF NOT EXISTS idx_import_jobs_created_at ON import_jobs(created_at DESC);

-- Add comment
COMMENT ON TABLE import_jobs IS 'Tracks background import jobs for large contact imports with progress tracking';

