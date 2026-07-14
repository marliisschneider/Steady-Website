# Loops — plain-English explainer for teaching Monday

## What a loop IS (in code, not in agent-speak)

A loop is a piece of code that says: do something over and over until some condition is met. Nothing more.

Real-world analogy — making coffee: "is coffee ready? no → wait 30 sec → check again. yes → stop." That's a loop. Observe → check condition → wait or exit. Without the "coffee is ready" check, you'd wait forever.

In programming this is written as `while (not done) { do stuff }`. It runs the body repeatedly. Each pass through is called an iteration. It stops when the condition flips to true.

## Why AI agents need loops specifically

Most computer programs don't need loops in this sense — they have fixed steps. A pipeline is a fixed program: step 1, step 2, step 3, done.

But some problems are open-ended. The number of steps depends on what you find as you go. That's where loops come in.

Cameron's problem: "get 6 facts about an account." Sometimes one search returns all 6, sometimes he needs 3 searches, sometimes 4. A pipeline can't handle variable steps. A loop can, because it keeps checking "do I have all 6 yet?" after each search.

The AI part just means Claude is the thing DECIDING inside the loop what to do next (which tool to call, what to search for). Without an AI, the loop needs hard-coded rules. With an AI, the AI reads the current state and picks the next action.

## The 4-stage cycle explained

Every AI agent loop has 4 stages that repeat:

- **OBSERVE** — read what you know so far. "I have industry and size. I don't have growth signals or hiring status yet."
- **THINK** — decide what to do next. "The most useful next search would be 'Acme hiring 2026' — that'll get me both hiring status AND recent growth signals in one shot."
- **ACT** — call ONE tool. "Call Exa with query 'Acme hiring 2026'."
- **CHECK** — did that get me closer? Am I done? "Great, I got hiring status but growth signals are still empty. Not done. Loop back to Observe."

Then Observe again. And so on. Until you're done.

## The exit condition — this is 90% of the design

Every loop MUST have an exit condition. Two kinds, and you need both:

1. **Goal met** (the happy path) — "I have all 6 fields. Done." This is the natural stop.
2. **Max tool calls** (the safety net) — "I've called tools 4 times, that's enough, stop even if I'm not done." This is the circuit breaker.

Without a max tool calls cap, agents run forever if the goal is unreachable. They burn API money or spin infinitely.

**The mantra: goal met OR max tool calls. Never trust an unbounded loop.**

## Cameron's real loop for Wednesday

**Goal** = enrich this account until you have 6 fields (industry, size, growth signals, hiring status, tech stack, recent news) AND 2 buying triggers.
**Tools** = his AccountResearcher Skill, Exa, Supabase read.
**Exit** = goal met (all 6 fields + 2 triggers) OR 4 tool calls made.

Plays out something like:

- Observe: I have zero fields
- Think: call my Skill first, it returns structured output
- Act: call AccountResearcher(account_name)
- Check: got 4 fields back but missing 2. Not done, loop
- Observe: still missing tech_stack, hiring
- Think: Exa search "Acme tech stack 2026"
- Act: call Exa
- Check: got tech_stack. Still missing hiring. Loop
- Observe: still missing hiring
- Think: Exa search "Acme hiring engineers 2026"
- Act: call Exa
- Check: got hiring. All 6 fields present. Now need 2 buying triggers...
- (continues until goal met or 4 tool calls hit)

## Ted's real loop for Wednesday

**Goal** = 30 unique companies with hiring signals.
**Tools** = his CompanyMatcher Skill, Exa.
**Exit** = 30 candidates OR 20 tool calls.

His agent loops the Skill 6 different ways ("Austin startups Series A hiring", then "remote SaaS hiring", then "healthtech mid-size hiring", etc.) each with a different angle. After each call it checks: how many unique candidates do I have so far? Keep going until 30.

## Video recommendations

The canonical text explainer is Anthropic's own **anthropic.com/engineering/building-effective-agents** — 15-min read, uses the exact vocabulary you'll teach. Better than most videos.

If you want video specifically, ask Claude in a new chat with web search: "find me the best 5-10 min YouTube video that explains agent loops for beginners." Channels that cover this well: IndyDevDan, AI Jason, Harrison Chase / LangChain.

## Whiteboard practice — 15 min tonight

Draw this 3 times on paper until you can do it without thinking:

```
    OBSERVE → THINK → ACT → CHECK
       ↑                        ↓
       └─── loop back if ───────┘
            not done
                          ↓
                        EXIT
                (goal met OR max tool calls)
```

Then out loud, without notes, walk through Cameron's loop. Then Ted's. If you can do both in under 90 seconds each, you own it.

## Two questions students will ask (from Instructor Runbook Confusions section)

**"My pipeline uses Claude — isn't that already an agent?"**
No. Claude does the thinking INSIDE step 3 of your pipeline, but the pipeline itself has fixed steps YOU wrote. In an agent, Claude decides WHICH step comes next. Same LLM inside, different control flow around it.

**"If pipelines work, why do we need agents?"**
Because some jobs can't be broken into fixed steps. Cameron's real job — "get enough information to write a compelling personalized email" — doesn't have a fixed sequence. Sometimes one search is enough, sometimes he needs four, sometimes different research angles depending on what he finds first. A pipeline can't handle that. An agent can.
