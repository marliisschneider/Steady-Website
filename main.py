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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,380;9..144,450;9..144,550;9..144,600&family=Inter:wght@400;500;600;650;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://marliisschneider.github.io/Steady-Website/steady2.css">
<style>
  /* Page-specific bits not covered by the site stylesheet (this page doesn't ship there) */
  .demo-badge {
    display: inline-block; font-family: var(--sans); font-size: 0.75rem; font-weight: 650;
    letter-spacing: 0.04em; text-transform: uppercase; color: var(--green-800);
    background: var(--green-100); padding: 4px 10px; border-radius: 999px; margin-bottom: 10px;
  }
  #error {
    display: none; margin-top: 16px; padding: 14px 16px; border-radius: 10px;
    background: #fbe4de; color: #8a3324; font-family: var(--sans); font-size: 0.92rem;
  }
  #result { display: none; margin-top: 28px; }
  #result h3 {
    font-family: var(--sans); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--green-600); margin: 20px 0 6px;
  }
  #result h3:first-child { margin-top: 0; }
  #result p, #result li { font-family: var(--sans); color: var(--ink); line-height: 1.5; }
  .muted { color: var(--muted); font-style: italic; }
  details { margin-top: 22px; font-family: var(--sans); font-size: 0.85rem; color: var(--muted); }
  pre {
    white-space: pre-wrap; background: var(--green-900); color: var(--cream);
    padding: 14px; border-radius: 10px; overflow-x: auto; margin-top: 8px;
  }
</style>
</head>
<body>

  <nav class="nav">
    <div class="nav-inner">
      <a href="https://marliisschneider.github.io/Steady-Website/index.html" class="brand"><span class="dot"></span>Steady</a>
    </div>
  </nav>

  <section class="article-hero">
    <div class="wrap narrow">
      <span class="demo-badge">Skill demo</span>
      <p class="eyebrow">SteadyLeadResearcher</p>
      <h1>Watch the lead-research Skill run, live.</h1>
      <p class="lede">Fill this in like a real Steady lead would on the contact page, and see exactly what the Skill sends back — no code, no terminal.</p>
    </div>
  </section>

  <section>
    <div class="wrap narrow">
      <div class="form-card">
        <form id="lead-form" class="lead-form">
          <div class="field">
            <label for="name">Name</label>
            <input id="name" required placeholder="Sarah Kim">
          </div>
          <div class="field">
            <label for="email">Email</label>
            <input id="email" type="email" required placeholder="sarah.kim88@gmail.com">
          </div>
          <div class="field">
            <label for="source">Source page</label>
            <select id="source">
              <option value="coaching">Coaching page</option>
              <option value="pantry-reset">Pantry Reset page</option>
              <option value="contact">Contact page</option>
              <option value="homepage">Homepage</option>
            </select>
          </div>
          <div class="field">
            <label for="message">What's going on? (optional — mimics the real contact form)</label>
            <textarea id="message" placeholder="I've tried keto and intermittent fasting but nothing sticks with my travel schedule..."></textarea>
          </div>
          <button type="submit" class="btn btn-primary" id="submit-btn">Research this lead →</button>
          <p class="form-msg" id="error" role="status" aria-live="polite"></p>
        </form>
      </div>

      <div id="result"></div>
    </div>
  </section>

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
