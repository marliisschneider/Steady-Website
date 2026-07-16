# Steady — Nutrition Coaching Website

A marketing website for **Steady**, a 1:1 nutrition coaching service for busy professionals in their 30s–50s.

## What Steady is

Steady offers 1:1 nutrition coaching focused on the **three root causes** most people never address: chronic inflammation, blood sugar dysregulation, and gut disruption. No macros spreadsheets, no weekly weigh-ins, no shame — just habits that survive real-world chaos.

## Who it's for

Professionals who feel worse than they should — bloated by 3pm, crashing after lunch, foggy — and who've tried apps + generic meal plans that don't fit their travel/work schedule.

## Services

- **1:1 Coaching** — 3-month program, biweekly video + async voice
- **Pantry Reset** — single 90-min session to overhaul the kitchen
- **Corporate Wellness** — team programs

## Pages

- `index.html` — Home (value prop + book call CTA)
- `about.html` — Coach story + philosophy
- `contact.html` — Booking form + Calendly embed
- `quiz.html` — Symptom quiz routing to relevant Learn page
- `learn-*.html` — Deep-dive educational pages on blood sugar, inflammation, gut health, etc.
- `leads.html` — Internal leads pipeline board (private): drag leads through stages, click a card to see the agent's enrichment + editable draft
- `board.html` — Internal tasks kanban (private)

## Tech stack

- HTML / CSS / vanilla JavaScript
- Supabase (leads capture, symptom quiz responses)
- Vercel (hosting + auto-deploy from GitHub pushes)
- GitHub (version control)

## How to run locally

Just open `index.html` in a browser. No build step, no dependencies.

For the Supabase-backed features (leads board, quiz submission), the Supabase URL + anon key live in `config.js`. The leads board's write actions (drag-to-move, draft edits, enrich) go through the FastAPI server in `main.py`, which holds the service-role key.

## Built as part of MakerSquare Cohort 1

This site started as a Day 3 build during MakerSquare's 2-week AI builder program. It's been iterated since as a real, working project.
