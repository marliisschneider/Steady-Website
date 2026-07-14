# Pipeline Build Prompt — paste this into a fresh Claude Code chat

Open Claude Code from `~/Desktop/steady-website/Steady-Website/` and paste everything below the line.

---

I'm in the Steady project. I want to build a working pipeline that reads leads from Supabase, researches each company with Exa, drafts a personalized follow-up with Claude, and saves it as a Gmail draft via Composio. All credentials are in .env: SUPABASE_URL, SUPABASE_ANON_KEY, ANTHROPIC_API_KEY, EXA_API_KEY, COMPOSIO_API_KEY. Python 3.12 virtualenv already exists at ./.venv/.

Build a file called enrich_leads.py that runs this 4-step pipeline for each lead:

STEP 1 — Supabase read: fetch all rows from the steady_leads table where status = 'new'.

STEP 2 — Exa search: for each lead, extract the email domain and run exa.search(f"{email_domain} recent news 2026", num_results=3). Print the top result title so I can see it worked.

STEP 3 — Claude draft: send lead info (name, email, source) plus the Exa results to Claude Sonnet with this system prompt: "You are a nutrition coach following up with a warm lead. Given the lead info and what you found searching about their company, write a personalized 2-sentence follow-up that MUST reference something specific from the search results. Offer a free 20-minute discovery call. Just body text, no greeting, no signature." Use model claude-sonnet-4-5-20250929.

STEP 4 — Composio Gmail draft (NOT send): use slug GMAIL_CREATE_EMAIL_DRAFT with user_id "pg-test-d0673ae0-6485-4aaa-9241-4cedfadfb7f1", recipient_email = the lead's email, subject "Following up — quick nutrition Q", body = the drafted email from step 3.

Rules:
- Load .env with python-dotenv at the top
- Log each step for each lead: ✓ read / ✓ searched / ✓ drafted / ✓ Gmail draft saved
- On any error, print the full traceback and skip to the next lead — don't crash the whole run
- If GMAIL_CREATE_EMAIL_DRAFT slug isn't found, list gmail slugs with composio.tools.list(toolkit="gmail") to find the current name

Install anything missing with ./.venv/bin/pip install (composio, exa-py, anthropic, supabase, python-dotenv). Then run it with ./.venv/bin/python enrich_leads.py and report back exactly what you see — successes AND errors.

---

## For Monday students

Students paste the same prompt but swap the `user_id "pg-test-d0673ae0..."` with their own Composio connection's user_id (visible in their Composio dashboard).
