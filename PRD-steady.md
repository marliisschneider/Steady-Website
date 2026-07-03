# Product Brief — Steady Nutrition Coaching Website

## The Problem

Busy professionals know they should eat better, but every solution they've tried is built for people with unlimited time and willpower. Diet apps demand daily logging. Meal prep takes hours. Generic plans don't account for back-to-back travel, client dinners, or the fact that their fridge is empty by Wednesday. They keep starting over. The problem isn't discipline — it's that the tools assume a life they don't have.

Meanwhile, chronic low-grade inflammation, blood sugar crashes, and daily bloating are quietly draining their energy, focus, and mood — and most don't connect it to food. They think it's stress, age, or just how they feel. It's not.

## Who Has It

**Primary user: professionals in their 30s–50s who feel worse than they should.**

They're high-functioning at work. They work out occasionally. They're not eating fast food every day. But they're bloated by 3pm, crashing after lunch, can't sleep well, and feel inflamed and puffy most mornings. They've tried cutting carbs, doing cleanses, taking supplements — nothing sticks because nothing explained *why* their body is reacting this way.

They're not looking for a diet plan. They want to understand what's actually going on in their body and make changes they can keep. They trust credible, research-backed information and are willing to pay for expertise they believe in.

**Secondary user: high-performing professionals with a specific trigger** — a recent blood test, a doctor's warning, or a health scare that made food feel suddenly urgent.

## What Steady Does

Steady offers 1:1 nutrition coaching built around the three root causes most busy professionals never address: chronic inflammation, blood sugar dysregulation, and gut disruption. The coach diagnoses which patterns are driving the client's symptoms, then builds a practical protocol that fits their actual life.

Three engagement options:
- **1:1 Coaching** — 3-month program, biweekly video calls + async voice check-ins
- **Pantry Reset** — single 90-min session to rebuild what the client keeps at home
- **Corporate Wellness** — team programs for companies; scoped per engagement

The differentiator: no macros spreadsheets, no weekly weigh-ins, no shame. The goal is to make the client understand their body well enough that they don't need a coach forever.

## What the Website Needs to Do

Three things:
1. **Educate** — give visitors real, research-backed content that makes them understand their symptoms differently. This builds trust faster than any testimonial.
2. **Qualify** — the symptom quiz routes visitors to their root cause and warms them up before the CTA.
3. **Convert** — move educated, qualified visitors to book a free 20-min discovery call OR join the email list.

The content strategy: teach them something true that surprises them, and they'll want to know what else they've been missing.

## What I'm NOT Building

- ❌ Client portal or login
- ❌ Food tracking or logging tools
- ❌ E-commerce or payment flow (Stripe handled separately)
- ❌ Booking system (Calendly embed placeholder only)
- ❌ Full blog (the Learn pages ARE the content; no CMS needed for v1)

## Pages

---

### index.html — Home

Hero: clear value proposition ("Feel like yourself again — without overhauling your life") + single CTA ("Book a free 20-min call").

Below the fold:
- What Steady is and who it's for
- Three root causes teaser — inflammation / blood sugar / gut — with one-line hooks linking to the Learn pages
- Three service cards
- One testimonial placeholder
- Final CTA

---

### about.html — About

Coach background, philosophy, and credentials. Why 1:1 works when apps don't. Personal but professional — warm without being self-indulgent. Photo placeholder.

---

### contact.html — Contact

Simple form (name, email, message) + Calendly embed placeholder for discovery call. No friction.

---

### learn-bloodsugar.html — Blood Sugar: What's Actually Happening

**Goal:** Explain blood sugar dysregulation in plain language and give actionable fixes the reader can start today.

**Sections:**

**What blood sugar actually is**
Your cells run on glucose. When you eat, blood sugar rises — your pancreas releases insulin to move glucose into cells. The problem: most people eat in a way that causes sharp spikes followed by sharp crashes. That crash is the 3pm slump, the brain fog, the irritability, the craving for something sweet. It's not a willpower problem. It's a glucose problem.

**Why it matters beyond energy**
Chronic blood sugar spikes drive inflammation, accelerate aging (glycation damages collagen and arteries), disrupt sleep, and are a direct precursor to type 2 diabetes. Most people don't feel "diabetic" — they feel tired, foggy, and puffy.

**What causes spikes**
- Eating carbohydrates alone (especially processed: bread, pasta, rice, pastries, juice)
- Skipping meals then eating a large one
- Eating in the wrong order (carbs first, protein last)
- Sedentary periods after meals

**How to flatten the curve — practical fixes:**
- **Eat in order:** Start every meal with protein and fat, then fiber, then carbs. This dramatically slows glucose absorption. A salad before pasta, eggs before toast.
- **Move after eating:** A 10-minute walk or 20 squats after a meal blunts the glucose spike by up to 30% (research: Diabetes Care, 2022). You don't need a gym — you need to not sit down for 10 minutes.
- **Don't eat carbs naked:** Pair every carb with protein, fat, or fiber. Fruit with nut butter. Bread with eggs. Rice with meat and vegetables.
- **Vinegar before meals:** 1 tbsp apple cider vinegar in water before a carb-heavy meal slows gastric emptying and reduces the spike. Supported by multiple RCTs.
- **Prioritize sleep:** One night of poor sleep increases insulin resistance the next day. The effect is measurable and immediate.

**Visual:** Glucose curve diagram — spiky eating pattern vs. steady curve with same foods eaten in order.

---

### learn-inflammation.html — Inflammation: The Fire You Can't See

**Goal:** Make inflammation tangible and show exactly which foods drive it vs. fight it.

**Sections:**

**What inflammation actually is**
Acute inflammation is good — it's how your body heals a cut or fights an infection. Chronic low-grade inflammation is different. It's your immune system stuck in "on" mode, quietly damaging tissue, disrupting hormones, and draining energy. You can't see it, but you feel it: joint stiffness in the morning, skin issues, brain fog, slow recovery, feeling generally "off."

**What drives chronic inflammation**
- **Seed oils (linoleic acid overload):** Canola, soybean, sunflower, vegetable, corn, and safflower oil are extremely high in omega-6 polyunsaturated fatty acids. When heated, they oxidize and produce toxic aldehydes (4-HNE, MDA) that trigger inflammatory cascades. These oils are in almost every restaurant dish, packaged food, and fast food item. The average American gets 80%+ of their fat from these oils — our great-grandparents got almost none.
- **Ultra-processed food:** Anything with more than 5 ingredients you can't picture in their natural state. Emulsifiers, artificial dyes, and preservatives disrupt the gut lining and trigger an immune response.
- **Sugar and refined carbs:** Fructose in excess (especially from liquid sources like juice and soda) is processed in the liver and generates inflammatory byproducts. High-fructose corn syrup is particularly problematic.
- **Fast food:** A McDonald's meal has been shown in studies to trigger an immune response within 4 hours measurably similar to a bacterial infection. Researchers at University of Bonn (2018) found fast food caused the innate immune system to become more aggressive — and that response persisted for weeks after.

**What seed oils are doing in your body**
When omega-6 fats dominate your cell membranes (as they do when you eat a modern diet), your body produces more pro-inflammatory prostaglandins. The ideal omega-6:omega-3 ratio is roughly 4:1. The modern American diet is 20:1. This imbalance is directly associated with cardiovascular disease, depression, autoimmune conditions, and accelerated aging.

**What to replace seed oils with:**
| Swap this | For this | Why |
|---|---|---|
| Canola / vegetable oil | Extra virgin olive oil | High in oleic acid (anti-inflammatory), stable at medium heat |
| Soybean / corn oil | Butter or ghee | Saturated fat is stable; no oxidation |
| Sunflower oil | Coconut oil | Saturated, heat-stable, neutral flavor |
| Restaurant cooking | Home cooking | You control the oil |

**What to look for in the store:**
Check the ingredients of every packaged food. If it lists: canola oil, soybean oil, vegetable oil, sunflower oil, safflower oil, corn oil — put it back. This includes: chips, crackers, salad dressings, mayo, granola bars, bread, plant-based meat, most "healthy" packaged snacks. Cook with olive oil, butter, ghee, avocado oil, or coconut oil.

**Foods that actively reduce inflammation:**
- **Fatty fish** (salmon, sardines, mackerel): High in EPA and DHA omega-3s, which directly counteract inflammatory pathways
- **Extra virgin olive oil:** Contains oleocanthal, which inhibits COX enzymes the same way ibuprofen does
- **Blueberries:** Anthocyanins reduce NF-κB (a master inflammatory switch)
- **Turmeric + black pepper:** Curcumin suppresses multiple inflammatory markers; black pepper increases absorption by 2000%
- **Leafy greens** (spinach, kale, arugula): Magnesium deficiency is strongly linked to inflammation; greens are the best source
- **Walnuts:** Best plant source of ALA omega-3; also reduce CRP levels
- **Green tea:** EGCG is one of the most studied anti-inflammatory compounds

---

### learn-bloating.html — Bloating: Why You Feel Like That at 3pm

**Goal:** Explain the real causes of bloating and give practical, immediate fixes.

**Sections:**

**What bloating actually is**
Bloating is gas and fluid trapped in your digestive tract — usually because something disrupted how your gut is processing food. It's not just uncomfortable. Chronic bloating is your gut sending a signal that something in your inputs is causing a problem.

**The most common causes:**

- **Eating too fast:** You swallow air with your food. Slow down, chew more.
- **FODMAP overload:** Fermentable carbohydrates (onions, garlic, beans, apples, wheat) feed gut bacteria rapidly, producing gas. High-FODMAPs aren't bad for everyone — but if you're sensitive, these are the culprits.
- **Eating large volumes of raw fiber on a disrupted gut:** Salads and raw vegetables are healthy, but a huge raw salad when your gut is already inflamed will make bloating worse, not better.
- **Carbonated drinks:** Even sparkling water adds gas to an already sensitive system.
- **Seed oils and emulsifiers in processed food:** These damage the gut lining (tight junctions), allowing partially digested food particles into the bloodstream — triggering immune responses and bloating.
- **Stress:** The gut has more neurons than your spinal cord. Cortisol directly slows digestion and disrupts gut motility. Eating at your desk under deadline pressure will bloat you regardless of what you eat.
- **Dysbiosis:** An imbalanced gut microbiome (too many gas-producing bacteria, not enough beneficial ones) causes chronic bloating that doesn't resolve with any single food fix. This requires rebuilding over weeks.

**Immediate fixes:**
- Ginger tea or ginger before meals (stimulates gastric motility)
- Peppermint oil capsules (enteric-coated): reduces IBS-related bloating significantly in clinical trials
- Digestive enzymes with meals if you're eating high-fiber foods
- Walk after eating
- Don't eat within 2 hours of sleep — your gut needs to rest too

**Longer-term fixes:**
- Eliminate seed oils and processed food for 2 weeks and observe
- Try a low-FODMAP elimination for 3 weeks, then reintroduce systematically
- Add fermented foods: kefir, kimchi, sauerkraut, plain yogurt — these feed beneficial bacteria
- Address stress as a first-class input, not an afterthought

---

---

### quiz.html — "What's Your Root Cause?" Symptom Quiz

**Goal:** 3-question interactive quiz in vanilla JS. No backend, no API. Runs entirely in the browser.

**How it works:**

User sees one question at a time. Each question has 3–4 symptom options they can multi-select. At the end, JS tallies which category (blood sugar / inflammation / gut) scored highest and shows a personalized result with a link to the matching Learn page + CTA to book a call.

**Questions:**

Q1: "When do you feel worst?" 
- After lunch (blood sugar)
- When I wake up — stiff or puffy (inflammation)
- After meals — bloated or gassy (gut)
- Pretty much all the time (all three)

Q2: "Which of these sounds most like you?"
- I crash at 3pm and crave something sweet (blood sugar)
- My joints ache, my skin flares, I feel foggy (inflammation)
- I'm bloated by midday even when I eat "healthy" (gut)
- I have low energy no matter how much I sleep (blood sugar + inflammation)

Q3: "What does your typical lunch look like?"
- Sandwich, wrap, or pasta (blood sugar)
- Fast food or restaurant meals most days (inflammation)
- Big salad or lots of raw vegetables (gut)
- I skip lunch or eat at my desk (blood sugar)

**Result screen:**
- Headline: "Your likely root cause: [Blood Sugar / Inflammation / Gut Disruption]"
- 2-sentence plain-language explanation of what that means for them
- Button: "Read the full guide →" (links to matching Learn page)
- Secondary CTA: "Book a free call to talk through your results →"

**Implementation:** Pure vanilla JS object that maps answer combinations to outcomes. ~60 lines of JS, no libraries.

---

### Email Capture → Supabase (homepage + Learn pages)

**Goal:** Collect leads from organic content readers. Store emails in Supabase `steady_leads` table. Real data, real database — this is Marliis's live Supabase instance.

**Where it appears:**
- Homepage: after the three root causes teaser section — "Get the free inflammation guide" inline form
- Bottom of each Learn page: "Want the full protocol for this?" form with name + email

**Form fields:** Name, Email, optional "Which topic brought you here?" dropdown (blood sugar / inflammation / bloating / quiz result)

**Supabase table: `steady_leads`**
```sql
create table steady_leads (
  id uuid default gen_random_uuid() primary key,
  name text,
  email text not null,
  source text,  -- 'homepage', 'bloodsugar', 'inflammation', 'bloating', 'quiz'
  created_at timestamp default now()
);
```

**Implementation:** Supabase JS client (CDN import, no npm). On form submit: insert row → show "You're in — check your inbox" confirmation. No page reload.

**Supabase credentials:** Use Marliis's live project URL + anon key in a `config.js` file (not hardcoded in HTML).

---

## Design Direction

Clean and minimal. Deep forest green with cream and off-white. Lots of white space. Strong, confident typography. Data visualizations where possible (glucose curves, oil comparison charts). No diet culture imagery — no salads, no scales, no before/after. Feels like a premium health service written by someone who actually knows the science.

The Learn pages should feel like the best health article you've ever read: well-sourced, plainly written, immediately actionable.

## Tech Stack

Plain HTML, CSS, vanilla JS. One stylesheet (style.css). Mobile-responsive. Deploys to Vercel via GitHub push.

## File Structure

```
index.html
about.html
contact.html
quiz.html
learn-bloodsugar.html
learn-inflammation.html
learn-bloating.html
style.css
config.js          ← Supabase project URL + anon key
```

## Success Metric

A visitor reads one Learn page and thinks "I've never had anyone explain this to me this clearly" — then books a discovery call because they want to know what else they've been missing.
