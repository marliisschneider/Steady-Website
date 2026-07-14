import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from steady_lead_researcher import LeadResearchError, research_lead

app = FastAPI()

# Wide open on purpose: this is a public demo skill with no sensitive data,
# meant to be called from any test page (including a plain local HTML file).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/demo", response_class=HTMLResponse)
def demo():
    return DEMO_HTML


DEMO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SteadyLeadResearcher — Live Demo</title>
<style>
  :root { color-scheme: light dark; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Inter", sans-serif;
    max-width: 640px; margin: 40px auto; padding: 0 20px;
    background: #F5F4F0; color: #181849;
  }
  h1 { font-size: 1.4rem; margin-bottom: 4px; }
  p.sub { color: #4a4a63; margin-top: 0; }
  form {
    background: white; border-radius: 12px; padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-top: 20px;
  }
  label { display: block; font-weight: 600; margin: 14px 0 4px; font-size: 0.9rem; }
  label:first-child { margin-top: 0; }
  input, select, textarea {
    width: 100%; padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px;
    font-size: 0.95rem; box-sizing: border-box; font-family: inherit;
  }
  textarea { min-height: 70px; resize: vertical; }
  button {
    margin-top: 18px; background: #403DD8; color: white; border: none;
    padding: 10px 18px; border-radius: 6px; font-size: 0.95rem; cursor: pointer;
  }
  button:disabled { opacity: 0.6; cursor: wait; }
  #error {
    display: none; margin-top: 16px; padding: 12px; border-radius: 8px;
    background: #fde8e8; color: #a12626; font-size: 0.9rem;
  }
  #result {
    display: none; margin-top: 20px; background: white; border-radius: 12px;
    padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  #result h3 { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em;
    color: #81AAFB; margin: 16px 0 4px; }
  #result h3:first-child { margin-top: 0; }
  .muted { color: #999; font-style: italic; }
  details { margin-top: 18px; font-size: 0.85rem; }
  pre { white-space: pre-wrap; background: #181849; color: #dfe3ff; padding: 12px;
    border-radius: 8px; overflow-x: auto; }
</style>
</head>
<body>
  <h1>SteadyLeadResearcher</h1>
  <p class="sub">Live demo — fill this in like a real lead would, and watch the skill run.</p>

  <form id="lead-form">
    <label for="name">Name</label>
    <input id="name" required placeholder="Sarah Kim">

    <label for="email">Email</label>
    <input id="email" type="email" required placeholder="sarah.kim88@gmail.com">

    <label for="source">Source page</label>
    <select id="source">
      <option value="coaching">Coaching page</option>
      <option value="pantry-reset">Pantry Reset page</option>
      <option value="contact">Contact page</option>
      <option value="homepage">Homepage</option>
    </select>

    <label for="message">What's going on? (optional — mimics the contact form)</label>
    <textarea id="message" placeholder="I've tried keto and intermittent fasting but nothing sticks with my travel schedule..."></textarea>

    <button type="submit" id="submit-btn">Research this lead →</button>
  </form>

  <div id="error"></div>

  <div id="result"></div>

  <script>
    function escapeHtml(str) {
      const div = document.createElement('div');
      div.textContent = str;
      return div.innerHTML;
    }

    function fmt(v) {
      if (v === null || v === undefined || v === '') {
        return '<span class="muted">— not enough evidence to say —</span>';
      }
      return escapeHtml(String(v));
    }

    function renderResult(data) {
      const el = document.getElementById('result');
      const pains = Array.isArray(data.potential_pain_points) && data.potential_pain_points.length
        ? '<ul>' + data.potential_pain_points.map(function (p) { return '<li>' + escapeHtml(p) + '</li>'; }).join('') + '</ul>'
        : fmt(data.potential_pain_points);

      el.innerHTML =
        '<h3>Likely Industry</h3><p>' + fmt(data.likely_industry) + '</p>' +
        '<h3>Potential Pain Points</h3>' + pains +
        '<h3>Conversation Hook</h3><p>' + fmt(data.one_conversation_hook) + '</p>' +
        '<details><summary>Raw JSON</summary><pre>' + escapeHtml(JSON.stringify(data, null, 2)) + '</pre></details>';
      el.style.display = 'block';
    }

    document.getElementById('lead-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = document.getElementById('submit-btn');
      var errorEl = document.getElementById('error');
      var resultEl = document.getElementById('result');
      errorEl.style.display = 'none';
      resultEl.style.display = 'none';
      btn.disabled = true;
      btn.textContent = 'Researching… (can take ~30s if the server was asleep)';

      var payload = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        source: document.getElementById('source').value || null,
        message: document.getElementById('message').value || null
      };

      fetch('/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(function (res) {
          return res.json().then(function (data) { return { ok: res.ok, data: data }; });
        })
        .then(function (r) {
          if (!r.ok) throw new Error(r.data.detail || 'Request failed');
          renderResult(r.data);
        })
        .catch(function (err) {
          errorEl.textContent = 'Error: ' + err.message;
          errorEl.style.display = 'block';
        })
        .finally(function () {
          btn.disabled = false;
          btn.textContent = 'Research this lead →';
        });
    });
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
