---
name: hoo-competitor-intel
description: Use for competitor content analysis - "what are competitors publishing", "content gaps vs <domain>", /organic-os:competitors, or the biweekly routine.
---

# Competitor intelligence

1. Read profile competitors. For each: fetch sitemap or blog index; diff
   against the previous snapshot in runs/ (first run = baseline, say so).
2. Launch competitive-intel-analyst agent per competitor (parallel, cap 3 per
   run) with the profile path.
3. Synthesize: new pages, topics they cover that we lack (cross-reference our
   sitemap), their apparent keyword focus per new page.
4. Gaps that fit our profile keywords/segments -> create_item
   kind="content-brief" (proposed, gated as always).
5. Persist runs/YYYYMMDD-competitors/ + signals for notable moves.
