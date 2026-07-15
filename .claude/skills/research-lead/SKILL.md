---
name: research-lead
description: Research a Steady lead (name + email, optionally source + their intake message) using the SteadyLeadResearcher skill, and present the profile in plain language. Use when the user asks to research a lead, test the lead researcher, or wants a quick profile without opening the deployed /demo page or writing curl commands.
---

Run the SteadyLeadResearcher skill locally — this calls the exact same `research_lead()` function as the deployed Render service (same guardrails, same behavior), just triggered by typing here instead of an HTTP request.

## What to do

1. Get the lead's `name` and `email` from the user (both required — ask if either is missing).
2. Optionally get `source` (which page they came from, e.g. "coaching", "pantry-reset", "contact", "homepage") and `message` (what they wrote in the contact form) if the user gives them, or if they're deliberately testing a specific scenario (e.g. "test a personal-email lead with no message").
3. From `~/Desktop/steady-website/Steady-Website/`, run:
   ```
   ./.venv/bin/python research_lead_cli.py --name "<name>" --email "<email>"
   ```
   adding `--source "<source>"` and `--message "<message>"` if provided. This can take up to ~20-30 seconds since it's doing real web searches — that's expected, not a hang.
4. Parse the JSON result and present it in plain language, not a raw JSON dump:
   - **Likely industry:** value, or "not enough evidence to say" if `null`
   - **Potential pain points:** a short bulleted list, or "not enough evidence to say" if `null`
   - **Conversation hook:** the value, or "not enough evidence to say" if `null`
5. If the command exits non-zero, read the `error_type` from stderr and explain it plainly rather than dumping a traceback:
   - `InvalidLeadInputError` → the name or email was malformed
   - `LeadResearchAPIError` → the Anthropic API failed (transient or bad key)
   - `LeadResearchParseError` → the model never returned a usable answer after the forced retry

## Why this exists alongside the Render deployment

This only works when someone is actively in a Claude Code session typing a request — it can't be triggered by an automated loop or another program the way the deployed `/research` endpoint on Render can. Use this for quick interactive checks or demos; use the Render deployment for anything that needs to run without a human present.
