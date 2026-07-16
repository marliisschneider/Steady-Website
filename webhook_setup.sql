-- webhook_setup.sql
-- Run once in the Supabase SQL editor. Creates a database trigger that POSTs
-- every new steady_leads row to the leads backend (leads_api.py, /lead-created),
-- which sends the lead an instant confirmation email and auto-enriches them.
--
-- This is the "auto-confirm + auto-enrich every new lead" automation. Kept in
-- the repo so the trigger is reproducible (it otherwise lives only in Supabase).

-- 1. Enable the HTTP extension (no-op if already on)
create extension if not exists pg_net;

-- 2. Function that POSTs each new lead to the backend
create or replace function steady_notify_new_lead()
returns trigger
language plpgsql
security definer
as $$
begin
  perform net.http_post(
    url     := 'https://steady-leads-api.onrender.com/lead-created',
    headers := '{"Content-Type": "application/json"}'::jsonb,
    -- If you set STEADY_WEBHOOK_SECRET on the Render service, add it here:
    -- headers := '{"Content-Type": "application/json", "x-webhook-secret": "YOUR_SECRET"}'::jsonb,
    body    := jsonb_build_object(
                 'type',   'INSERT',
                 'table',  'steady_leads',
                 'record', to_jsonb(new)
               )
  );
  return new;
end;
$$;

-- 3. Fire it after every new lead
drop trigger if exists steady_new_lead_webhook on steady_leads;
create trigger steady_new_lead_webhook
after insert on steady_leads
for each row execute function steady_notify_new_lead();
