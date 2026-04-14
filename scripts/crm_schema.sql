-- Rank4AI CRM Schema
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/tsscscjcxbzhicuuhter/sql

DROP TABLE IF EXISTS activity_log CASCADE;
DROP TABLE IF EXISTS crm_tasks CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;

CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name TEXT,
  contact_name TEXT,
  website_url TEXT,
  email TEXT,
  phone TEXT,
  company_size TEXT,
  current_stage TEXT DEFAULT 'new',
  source TEXT DEFAULT 'website',
  assigned_to TEXT DEFAULT 'Jimmy',
  goals TEXT,
  marketing_type TEXT,
  agency_experience TEXT,
  message TEXT,
  consent BOOLEAN DEFAULT false,
  audit_status TEXT DEFAULT 'pending',
  audit_score INTEGER,
  lost_reason TEXT,
  lost_notes TEXT,
  won_value TEXT,
  won_notes TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_activity_at TIMESTAMPTZ DEFAULT NOW(),
  closed_at TIMESTAMPTZ
);

CREATE TABLE activity_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  details TEXT,
  from_stage TEXT,
  to_stage TEXT,
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE crm_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending',
  due_date TIMESTAMPTZ,
  assigned_to TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Triggers
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); NEW.last_activity_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversations_timestamp BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_tasks_timestamp BEFORE UPDATE ON crm_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE FUNCTION log_stage_change() RETURNS TRIGGER AS $$
BEGIN
  IF OLD.current_stage IS DISTINCT FROM NEW.current_stage THEN
    INSERT INTO activity_log (conversation_id, action, from_stage, to_stage, details)
    VALUES (NEW.id, 'stage_change', OLD.current_stage, NEW.current_stage,
      CASE WHEN NEW.current_stage = 'lost' THEN NEW.lost_reason
           WHEN NEW.current_stage = 'won' THEN NEW.won_value ELSE NULL END);
    NEW.last_activity_at = NOW();
    IF NEW.current_stage IN ('won', 'lost') THEN NEW.closed_at = NOW(); END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_stage_change BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION log_stage_change();

-- Indexes
CREATE INDEX idx_conversations_stage ON conversations(current_stage);
CREATE INDEX idx_conversations_email ON conversations(email);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
CREATE INDEX idx_activity_conversation ON activity_log(conversation_id);
CREATE INDEX idx_tasks_conversation ON crm_tasks(conversation_id);
CREATE INDEX idx_tasks_due ON crm_tasks(due_date);

-- RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public insert" ON conversations FOR INSERT WITH CHECK (true);
CREATE POLICY "Full access" ON conversations FOR ALL USING (true);
CREATE POLICY "Full access activity" ON activity_log FOR ALL USING (true);
CREATE POLICY "Full access tasks" ON crm_tasks FOR ALL USING (true);
