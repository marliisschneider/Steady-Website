import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from steady_lead_researcher import LeadResearchError, research_lead

app = FastAPI()


class LeadInput(BaseModel):
    name: str
    email: str
    source: str | None = None
    message: str | None = None


@app.get("/")
def health():
    return {"status": "ok", "endpoint": "/research", "method": "POST"}


@app.post("/research")
def research(input: LeadInput):
    try:
        return research_lead(input.name, input.email, source=input.source, message=input.message)
    except LeadResearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
