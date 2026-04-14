import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://tsscscjcxbzhicuuhter.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzc2NzY2pjeGJ6aGljdXVodGVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzU1NDEsImV4cCI6MjA5MTYxMTU0MX0.Q4z8-zHq0RAjZ1Vnv339JwAY36aq5TvnDBwE7OvUNOM';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export const STAGES = [
  { id: 'partial', label: 'Partial', color: 'gray' },
  { id: 'new', label: 'New', color: 'blue' },
  { id: 'contacted', label: 'Contacted', color: 'cyan' },
  { id: 'qualified', label: 'Qualified', color: 'yellow' },
  { id: 'proposal', label: 'Proposal', color: 'orange' },
  { id: 'negotiation', label: 'Negotiation', color: 'purple' },
  { id: 'won', label: 'Won', color: 'green' },
  { id: 'lost', label: 'Lost', color: 'red' },
] as const;

export type Conversation = {
  id: string;
  company_name: string | null;
  contact_name: string | null;
  website_url: string | null;
  email: string | null;
  phone: string | null;
  company_size: string | null;
  current_stage: string;
  source: string | null;
  assigned_to: string | null;
  goals: string | null;
  marketing_type: string | null;
  agency_experience: string | null;
  message: string | null;
  consent: boolean;
  audit_status: string | null;
  audit_score: number | null;
  lost_reason: string | null;
  lost_notes: string | null;
  won_value: string | null;
  won_notes: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
  closed_at: string | null;
};

export type Activity = {
  id: string;
  conversation_id: string;
  action: string;
  details: string | null;
  from_stage: string | null;
  to_stage: string | null;
  created_by: string | null;
  created_at: string;
};

export type CrmTask = {
  id: string;
  conversation_id: string;
  title: string;
  description: string | null;
  status: string;
  due_date: string | null;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
};
