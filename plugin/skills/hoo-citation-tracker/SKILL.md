---
name: hoo-citation-tracker
description: Use to measure AI answer-engine visibility - "are we cited by ChatGPT/Perplexity", "AI share of voice", /organic-os:citations, or the weekly routine's citation step.
---

# AI citation tracking

1. Read profile: keywords.targets (the query set), competitors, site url.
2. For each query (cap 20 per run; rotate through the set across runs), ask the
   available engines. Sources in order of preference: an authorized AI-search
   connector or WebSearch with engine-targeted queries; plain WebSearch
   otherwise. Never scrape engines through automation that violates their ToS.
3. Record per query: engine | our domain mentioned? | cited (linked)? |
   competitors mentioned | answer summary (<=30 words).
4. Metrics: mention rate, citation rate, share of voice vs competitors
   (mentions of us / mentions of anyone tracked).
5. Persist to runs/YYYYMMDD-citations/ + append one signal line with the
   headline movement vs the previous run (diff the last runs/ folder).
6. New citation appearing or disappearing on a money query -> P1 signal.
