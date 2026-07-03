# SEO — what's done and what's left

## Done (live now, no domain required)
- **Titles & meta descriptions** — unique, keyword-aware, on every page.
- **Open Graph + Twitter cards** — every page previews correctly when shared (LinkedIn, iMessage, Slack, X).
- **Branded share image** — `og-image.png` / `og-image.jpg` (1200×630).
- **Favicons & PWA** — `favicon.svg`, `favicon.ico`, `apple-touch-icon.png`, `icon-192/512.png`, `site.webmanifest`, `theme-color`.
- **Structured data (JSON-LD)** — this is what Google, ChatGPT, Perplexity, etc. read to understand the site:
  - Home: `Organization` / `ProfessionalService` + `WebSite`
  - About: `Person` (Marliis Schneider — jobTitle, alumniOf USC, knowsAbout) + `AboutPage`
  - Each guide: `BlogPosting` (author, publisher, dates)
  - Contact / Quiz / Learn: `ContactPage` / `WebPage` / `CollectionPage`
- **`robots.txt`** — allows all crawlers, explicitly welcomes AI answer-engine bots (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, etc.).
- **`llms.txt`** — plain-language site map for AI assistants.

## To finish once the domain is live (~10 min)
Everything below just needs the real URL, e.g. `https://steadynutrition.com`:

1. **Canonical tags** — add `<link rel="canonical" href="https://DOMAIN/PAGE.html">` to each page's `<head>` (I removed the empty placeholders).
2. **Absolute URLs for share/structured data** — change `og:image`, `twitter:image`, and the JSON-LD `image`/`logo` values from `og-image.jpg` to the full `https://DOMAIN/og-image.jpg`. Social scrapers and Google prefer absolute URLs.
3. **`sitemap.xml`** — generate with absolute URLs for all 10 pages. (Tell me the domain and I'll create it in one step.)
4. **`robots.txt`** — uncomment and set the `Sitemap:` line at the bottom.
5. **Register** the domain with Google Search Console + Bing Webmaster Tools and submit the sitemap.

## Notes
- No testimonials are used anywhere — add them (with a `Review`/`AggregateRating` JSON-LD block) once you have real client quotes.
- Contact page: drop your Calendly inline embed inside `#calendly-embed` when ready (there's an HTML comment marking the spot).
- `datePublished` on the guides is set to 2026-07-03 — update if you want the real publish dates.
