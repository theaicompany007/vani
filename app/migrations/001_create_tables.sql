-- VANI Outreach Command Center Database Schema
-- Run this in your Supabase SQL Editor

-- Targets table - FMCG companies and contacts
CREATE TABLE IF NOT EXISTS targets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    role VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    linkedin_url TEXT,
    pain_point TEXT,
    pitch_angle TEXT,
    script TEXT,
    status VARCHAR(50) DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'responded', 'meeting_scheduled', 'converted', 'not_interested')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Outreach sequences - Multi-step outreach templates
CREATE TABLE IF NOT EXISTS outreach_sequences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    channels TEXT[] DEFAULT ARRAY[]::TEXT[], -- ['email', 'whatsapp', 'linkedin']
    steps JSONB DEFAULT '[]'::JSONB, -- Array of step objects with delay, channel, template
    delay_between_steps INTEGER DEFAULT 24, -- hours
    total_duration INTEGER, -- total hours
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Outreach activities - Individual outreach actions
CREATE TABLE IF NOT EXISTS outreach_activities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    target_id UUID REFERENCES targets(id) ON DELETE CASCADE,
    sequence_id UUID REFERENCES outreach_sequences(id) ON DELETE SET NULL,
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('email', 'whatsapp', 'linkedin')),
    step_number INTEGER DEFAULT 1,
    message_content TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'failed')),
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,
    external_id VARCHAR(255), -- Resend email ID, Twilio message SID, etc.
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Meetings - Cal.com scheduled meetings
CREATE TABLE IF NOT EXISTS meetings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    target_id UUID REFERENCES targets(id) ON DELETE CASCADE,
    cal_event_id VARCHAR(255) UNIQUE,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    meeting_url TEXT,
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Webhook events - Track all webhook responses
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source VARCHAR(50) NOT NULL CHECK (source IN ('resend', 'twilio', 'cal_com')),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB DEFAULT '{}'::JSONB,
    activity_id UUID REFERENCES outreach_activities(id) ON DELETE SET NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_targets_status ON targets(status);
CREATE INDEX IF NOT EXISTS idx_targets_company ON targets(company_name);
CREATE INDEX IF NOT EXISTS idx_activities_target ON outreach_activities(target_id);
CREATE INDEX IF NOT EXISTS idx_activities_status ON outreach_activities(status);
CREATE INDEX IF NOT EXISTS idx_activities_sent_at ON outreach_activities(sent_at);
CREATE INDEX IF NOT EXISTS idx_meetings_target ON meetings(target_id);
CREATE INDEX IF NOT EXISTS idx_meetings_scheduled_at ON meetings(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_webhooks_source ON webhook_events(source);
CREATE INDEX IF NOT EXISTS idx_webhooks_activity ON webhook_events(activity_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for updated_at
CREATE TRIGGER update_targets_updated_at BEFORE UPDATE ON targets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sequences_updated_at BEFORE UPDATE ON outreach_sequences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_activities_updated_at BEFORE UPDATE ON outreach_activities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meetings_updated_at BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


