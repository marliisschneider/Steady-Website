-- Run in Supabase SQL editor before using enrich_agent.py
alter table steady_leads
  add column if not exists industry text,
  add column if not exists pain_points text[],
  add column if not exists hook text,
  add column if not exists draft_message text;

-- status already exists as free-text ('new', 'contacted', ...);
-- enrich_agent.py additionally writes 'drafted' and 'needs_manual_followup'.
