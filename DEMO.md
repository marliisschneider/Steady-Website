# Steady — End-to-End Demo Script

A single walkthrough that shows the whole system working: a stranger fills out a
form → it lands in the database → an AI agent researches them and writes a
personalized draft → you review it, move them through your pipeline, and the
draft is waiting in Gmail. It touches every layer, in order.

**The one-line point:** this is an AI *agent* wired into a *real* app — not a toy
demo. Form → database → agent (observe → think → act → check) → draft → human
review → pipeline → email.

---

## Before you start (2-minute setup)

You need three things open:

1. **The backend server**, running in a terminal you can show:
   ```
   cd ~/Desktop/steady-website/Steady-Website
   PORT=8001 PANEL_PAUSE_SECONDS=0 ./.venv/bin/python main.py
   ```
   Leave this window visible — the agent's reasoning prints here live.
   *(Once deployed to Render, the board points at the Render URL instead and you
   don't need this locally — but for a demo, running it locally lets the audience
   watch the agent think.)*

2. **The leads board** in a browser:
   - Live: `https://marliisschneider.github.io/Steady-Website/leads.html`
   - or local: run `python3 -m http.server 8934` in a second terminal, then open
     `http://localhost:8934/leads.html`

3. **Gmail** for `steadycoaching.co@gmail.com`, so you can show the draft it creates.

> **Tip:** if you're on Render's free tier, hit the server URL once a minute before
> you present — it spins down when idle and the first request after a nap is slow.

---

## The demo (the golden path)

### 1. Show the public site
Open the live site. *"This is the public nutrition-coaching site — static, always
up, no server. A busy professional lands here and fills out the contact form."*

### 2. Submit a lead — as a real visitor would
Go to **contact.html**. Fill it in with a believable message, e.g.:
- Name: `Alex Rivera`
- Email: `arivera@stripe.com`  *(a real company domain makes the research richer)*
- Message: *"I keep crashing at 3pm and I'm basically running on coffee until
  dinner. Not sure if it's what I'm eating or just work stress."*

Submit. Point out the **"You're in — check your inbox"** confirmation.
*"That just wrote a row into our Supabase database."*

### 3. Show it appear on the board
Open **leads.html**. The new lead is a card in the **New** column.
*"No server needed for this — the board reads straight from the database."*

### 4. Run the agent — and watch it think
Click the card → the modal opens. Click **Enrich**.

**Now switch to the terminal.** The agent's loop prints live:
`OBSERVE → ACT → CHECK`, twice at most. *"This is the agent deciding what to do:
it researches the lead, and if that's thin, does one targeted web search. It stops
as soon as it knows enough — a bounded loop, never runs forever."*

Back in the browser, the modal fills in: **industry, pain points, conversation
hook, and a drafted follow-up** — all referencing the message from step 2.

### 5. Review and edit the draft
Read the draft aloud — notice it quotes their actual words ("3pm crash",
"coffee"). *"The agent did the homework. But we always review before sending."*
Tweak a sentence, hit **Save draft**, then **Copy**.

### 6. Move them through the pipeline
Drag the card from **Drafted** → **Contacted** (or use the Status dropdown in the
modal). *"Once I've sent the follow-up, I move them along. Later: Booked, then
Client."* The move saves instantly.

### 7. Show the draft in Gmail
Switch to Gmail → **Drafts**. The follow-up the agent wrote is sitting there,
addressed to the lead, ready for you to review one more time and send.
*"Nothing gets sent automatically — a human always has the last look."*

---

## Grand finale (optional): batch mode

Back in the terminal, process every un-enriched lead at once:
```
./.venv/bin/python enrich_agent.py
```
It runs the same loop for each `new` lead, and at the end **emails you a digest**
listing anyone it couldn't draft for (so nothing falls through the cracks). Show
that digest email in Gmail. *"This is how you'd run a whole morning's leads in one
shot instead of clicking each one."*

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Enrich button spins forever / "Couldn't enrich" | The backend isn't running. Start it (setup step 1). |
| Draft/status won't save | Same — writes go through the server; reads don't. |
| First enrich takes ~45–60s | Render cold start. Hit the URL once to wake it, then demo. |
| A new lead doesn't appear on the board | Refresh the page (the board loads once on open). |
| Clicking a card does nothing | Hard-refresh (Cmd+Shift+R) — you may have a cached old page. |
| Placeholder emails (test.com, example.com) come back empty | Correct behavior — the agent refuses to invent facts for fake domains. |

---

## The teaching point

Every piece the cohort learns shows up here in one flow:
- **Lead capture** → a form writing to Supabase.
- **An agent** → the observe/think/act/check loop with a hard stop condition.
- **Tools** → web research, a database, email (Gmail via Composio).
- **Guardrails** → it won't fabricate; thin leads get flagged, not faked.
- **A real UI** → a pipeline board a non-technical person can actually use.
- **Human-in-the-loop** → drafts are reviewed, never auto-sent.

That's the "wire an agent into a real app" arc, start to finish.
