"""
leads_api.py — backend for the Steady leads pipeline board (leads.html).

Deployed as its own Render service, SEPARATE from main.py (the
SteadyLeadResearcher skill), so a change here can never break the skill.

Endpoints:
  POST /enrich/{lead_id}  — run the enrichment agent on one lead
  POST /lead/{lead_id}    — save a lead's draft and/or move its pipeline status

Both write through the service-role key (server-side only): the public site's
anon key intentionally can't UPDATE steady_leads.

Run locally:  PORT=8001 PANEL_PAUSE_SECONDS=0 ./.venv/bin/python leads_api.py
"""

import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from enrich_agent import EnrichmentError, enrich_lead, supabase_admin

# Pipeline stages a lead can move through. The agent sets 'drafted' /
# 'needs_manual_followup'; the rest are human sales-pipeline stages set from
# the leads board.
ALLOWED_STATUSES = {
    "new", "drafted", "needs_manual_followup", "contacted", "booked", "client",
}

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


@app.get("/")
def health():
    return {"status": "ok", "endpoints": ["/enrich/{lead_id}", "/lead/{lead_id}"]}


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
