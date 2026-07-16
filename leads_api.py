"""
leads_api.py — backend for the Steady leads pipeline board (leads.html) and
the new-lead automation.

Deployed as its own Render service, SEPARATE from main.py (the
SteadyLeadResearcher skill), so a change here can never break the skill.

Endpoints:
  POST /enrich/{lead_id}  — run the enrichment agent on one lead
  POST /lead/{lead_id}    — save a lead's draft and/or move its pipeline status
  POST /lead-created      — Supabase webhook target: on every new lead, send an
                            instant confirmation email AND auto-enrich (both in
                            the background so the webhook returns immediately)

All writes go through the service-role key (server-side only): the public
site's anon key intentionally can't UPDATE steady_leads.

Run locally:  PORT=8001 PANEL_PAUSE_SECONDS=0 ./.venv/bin/python leads_api.py
"""

import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from enrich_agent import (
    COMPOSIO_USER_ID,
    GMAIL_SEND_SLUG,
    EnrichmentError,
    composio,
    enrich_lead,
    supabase_admin,
)

# Pipeline stages a lead can move through. The agent sets 'drafted' /
# 'needs_manual_followup'; the rest are human sales-pipeline stages set from
# the leads board.
ALLOWED_STATUSES = {
    "new", "drafted", "needs_manual_followup", "contacted", "booked", "client",
}

# Optional shared secret. If set (here AND as a header on the Supabase webhook),
# /lead-created rejects calls without the matching x-webhook-secret header —
# stops randoms from triggering enrichments (which cost API money).
WEBHOOK_SECRET = os.environ.get("STEADY_WEBHOOK_SECRET")

CONFIRMATION_SUBJECT = "Thanks for reaching out to Steady"

app = FastAPI()

# Open CORS: the board is served from GitHub Pages (and localhost in dev), so
# it calls this API cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LeadUpdate(BaseModel):
    status: str | None = None
    draft_message: str | None = None


class WebhookPayload(BaseModel):
    # Supabase database webhooks POST {type, table, schema, record, old_record}
    type: str | None = None
    table: str | None = None
    record: dict | None = None


@app.get("/")
def health():
    return {"status": "ok", "endpoints": ["/enrich/{lead_id}", "/lead/{lead_id}", "/lead-created"]}


@app.post("/enrich/{lead_id}")
def enrich(lead_id: str):
    try:
        return enrich_lead(lead_id)
    except EnrichmentError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/lead/{lead_id}")
def update_lead(lead_id: str, update: LeadUpdate):
    patch = {}
    if update.status is not None:
        if update.status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail=f"Unknown status: {update.status!r}")
        patch["status"] = update.status
    if update.draft_message is not None:
        patch["draft_message"] = update.draft_message
    if not patch:
        raise HTTPException(status_code=400, detail="Nothing to update")

    resp = supabase_admin.table("steady_leads").update(patch).eq("id", lead_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail=f"No lead found with id={lead_id!r}")
    return resp.data[0]


def send_confirmation_email(name, email):
    """Warm, immediate autoresponder so the lead's inbox actually has something."""
    first = name.split()[0] if name else None
    greeting = f"Hi {first}," if first else "Hi there,"
    body = (
        f"{greeting}\n\n"
        "Thanks for reaching out to Steady — I got your note, and I'll be in touch "
        "personally within a day.\n\n"
        "In the meantime, if anything else comes to mind about how you've been "
        "feeling or what you've already tried, just reply to this email — it helps "
        "me come to our conversation already understanding you.\n\n"
        "Talk soon,\n"
        "Steady"
    )
    composio.tools.execute(
        GMAIL_SEND_SLUG,
        {"recipient_email": email, "subject": CONFIRMATION_SUBJECT, "body": body},
        user_id=COMPOSIO_USER_ID,
        dangerously_skip_version_check=True,
    )


def process_new_lead(lead_id):
    """Runs in the background after /lead-created returns. Idempotent: re-fetches
    the lead and only acts while it's still 'new', so a webhook retry (which
    fires after enrichment has already moved the status) is a no-op."""
    rows = supabase_admin.table("steady_leads").select("*").eq("id", lead_id).execute().data
    if not rows:
        return
    lead = rows[0]
    if (lead.get("status") or "new") != "new":
        return  # already handled

    if lead.get("email"):
        try:
            send_confirmation_email(lead.get("name"), lead["email"])
        except Exception as exc:  # never let a mail hiccup block enrichment
            print(f"[lead-created] confirmation email failed for {lead_id}: {exc}")

    try:
        enrich_lead(lead_id)
    except Exception as exc:
        print(f"[lead-created] auto-enrich failed for {lead_id}: {exc}")


@app.post("/lead-created")
def lead_created(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str | None = Header(default=None),
):
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    record = payload.record or {}
    lead_id = record.get("id")
    if not lead_id:
        raise HTTPException(status_code=400, detail="No record.id in webhook payload")

    # Return immediately; the slow work (email + ~15s enrich) runs after the
    # response so the Supabase webhook doesn't time out and retry.
    background_tasks.add_task(process_new_lead, lead_id)
    return {"status": "accepted", "lead_id": lead_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
