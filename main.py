import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from steady_lead_researcher import LeadResearchError, research_lead

# NOTE: the leads-board backend (/enrich, /lead) lives in a SEPARATE app,
# leads_api.py, deployed as its own Render service. This file stays lean —
# just the SteadyLeadResearcher skill — so a leads-code change can't break it.

app = FastAPI()

# Wide open on purpose: this is a public demo skill with no sensitive data,
# meant to be called from any test page (including a plain local HTML file).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Ask Steady: a grounded Q&A assistant over the Learn library ----------
# Reads the site's own guides at startup and answers questions using ONLY that
# content, in Steady's voice, with health guardrails. Lean by design — needs
# only the Anthropic key (already set for this service).
ASK_MODEL = "claude-sonnet-4-5-20250929"

anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _strip_html(html: str) -> str:
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    m = re.search(r"<article.*?>(.*?)</article>", html, flags=re.S | re.I)
    body = m.group(1) if m else html
    text = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", text).strip()


def _load_library() -> str:
    base = Path(__file__).resolve().parent
    parts = []
    for f in sorted(base.glob("learn-*.html")):
        html = f.read_text(encoding="utf-8", errors="ignore")
        tm = re.search(r"<title>(.*?)</title>", html, flags=re.S | re.I)
        title = (tm.group(1).strip() if tm else f.stem).replace(" — Steady", "")
        text = _strip_html(html)
        if text:
            parts.append(f"### {title}\n{text}")
    return "\n\n".join(parts)


LIBRARY = _load_library()

ASK_SYSTEM_PROMPT = (
    "You are Steady — a warm, honest nutrition educator. Answer the reader's "
    "question using ONLY the Steady library below plus well-established, "
    "non-controversial nutrition basics. Steady's voice is calm, direct, and "
    "plain: no hype, no fear-mongering, no fad diets.\n\n"
    "Rules:\n"
    "- Keep it SHORT and conversational: about 2 to 4 sentences, plain text, like a "
    "knowledgeable friend texting back. NO markdown, NO headings, NO bullet lists, NO "
    "bold — just plain sentences.\n"
    "- Lead with the direct answer, then a sentence of why or how.\n"
    "- Ground every answer in the library. When a specific guide is relevant, name it "
    "in plain words (e.g., \"the Protein guide covers this\") so they know where to read "
    "more. NEVER write a URL or link — you do not know the site's web addresses, so do "
    "not invent one.\n"
    "- You are NOT a doctor. Never diagnose, never give medical advice, never name "
    "medications or doses. For anything severe, persistent, or a red-flag symptom, tell "
    "them to see a doctor.\n"
    "- If a question is outside nutrition, or the library doesn't cover it, say so "
    "honestly and suggest the symptom quiz or booking a free call — don't invent an answer.\n"
    "- Never invent studies, numbers, or statistics.\n\n"
    "=== STEADY LIBRARY ===\n" + LIBRARY
)


class LeadInput(BaseModel):
    name: str
    email: str
    source: str | None = None
    message: str | None = None


class AskInput(BaseModel):
    question: str


def _sanitize_answer(text: str) -> str:
    """Belt-and-suspenders: the model sometimes invents URLs and over-formats
    despite the prompt. Strip any links/URLs (it doesn't know real ones) and
    flatten markdown so the chat widget gets clean plain text."""
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)      # [label](url) -> label
    text = re.sub(r"https?://\S+", "", text)                  # bare URLs
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)        # markdown headers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)            # bold
    text = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)", r"\1", text)  # italics
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.M)       # bullet markers
    text = re.sub(r"[ \t]*📖[^\n]*", "", text)                # stray CTA emoji lines
    text = re.sub(r"[ \t]{2,}", " ", text)                    # collapse double spaces
    text = re.sub(r"\n{3,}", "\n\n", text)                    # collapse blank runs
    return text.strip()


@app.get("/")
def health():
    return {"status": "ok", "endpoints": ["/research", "/ask", "/demo"]}


@app.post("/ask")
def ask(input: AskInput):
    question = (input.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please ask a question.")
    question = question[:500]
    message = anthropic_client.messages.create(
        model=ASK_MODEL,
        max_tokens=500,
        # Cache the big library prefix so repeat questions are ~cheap.
        system=[{"type": "text", "text": ASK_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": question}],
    )
    answer = "".join(b.text for b in message.content if b.type == "text").strip()
    return {"answer": _sanitize_answer(answer)}


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
