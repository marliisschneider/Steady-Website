"""
Vercel Python + FastAPI test for the AccountResearcher Skill pattern.

This deploys as a serverless function at /api/researcher on Vercel.
It calls Claude Sonnet with web_search (max 2 uses) — same shape as
what Cameron and Ted will build for their real Skills Tuesday.

Endpoint: POST /api/researcher
Body: {"account_name": "Airbnb"}
Response: {"account_name": ..., "result": ..., "elapsed_seconds": ...}
"""
from fastapi import FastAPI
from pydantic import BaseModel
import os
import time
from anthropic import Anthropic

app = FastAPI()


class ResearchInput(BaseModel):
    account_name: str


@app.get("/api/researcher")
def health():
    """Health check — GET to verify the endpoint is alive."""
    return {"status": "ok", "endpoint": "/api/researcher", "method": "POST"}


@app.post("/api/researcher")
def researcher(input: ResearchInput):
    start = time.time()

    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    msg = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=(
            "You are a SaaS researcher. Use web_search to find 2-3 recent "
            "signals about the account (funding, hiring, product launches). "
            "Return a short summary with source URLs cited inline."
        ),
        tools=[
            {"type": "web_search_20250305", "name": "web_search", "max_uses": 2}
        ],
        messages=[
            {
                "role": "user",
                "content": f"Research {input.account_name}. Return findings + sources.",
            }
        ],
    )

    elapsed = time.time() - start

    # Pull the final text block from the response
    text = ""
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            text = block.text

    return {
        "account_name": input.account_name,
        "result": text,
        "elapsed_seconds": round(elapsed, 2),
    }
