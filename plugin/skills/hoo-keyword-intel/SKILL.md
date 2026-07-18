---
name: hoo-keyword-intel
description: Use for keyword research, competitor keyword gaps, "what should we rank for", "keyword ideas for X", or the /organic-os:keywords command. Detects the user's Google Ads access tier and degrades honestly.
---

# Keyword intelligence (tiered)

0. Read site-profile.yaml (google_ads.status, keywords.targets, competitors,
   geos, languages). Source env from `~/.config/organic-os/<site-slug>.env`
   if present.

## Tier detection (once per session)
Run: `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -c "..."` snippet importing
`hoo.google_ads.tier`: if env vars missing -> tier "none". Else build
real_client() and `tier.detect()` -> basic|explorer. Tell the user which tier
is active and what that enables.

## basic (or standard)
1. Ideas: `keyword_ideas.run` with profile target keywords as seeds AND, per
   competitor, `site_seed=<competitor domain>`. Cache dir: `<brain>/keywords/cache/`.
2. Gap: ideas(own site_seed) vs ideas(competitor site_seed) - keywords in
   their set, absent from ours, volume >= 100. Rank by volume x profile fit.
3. Metrics for the shortlist: `historical.run` (batches of 200 handled inside).
4. Write `runs/YYYYMMDD-keywords/` (01-ideas.json, 02-gaps.json, REPORT.md)
   and update `keywords/tracking.yaml` targets the user confirms (additions
   are a strategy mutation -> create_item kind="strategy" + approval gate).

## explorer
Own-account GAQL only: search_term_view mining (queries with impressions and
no matching target), keyword_view quality scores. State plainly: "Planner
blocked at Explorer tier - apply for Basic (https://github.com/shalintripathi/organic-os/blob/main/plugin/docs/credentials/google-ads-token.md, also at $CLAUDE_PLUGIN_ROOT/docs/credentials/google-ads-token.md in a local checkout)".

## none (no token)
GSC query mining via the user's GSC connector: 16 months, queries with
impressions > 100 and position 8-30 = the opportunity set. If no GSC either:
offer CSV import.

## csv (always available)
Accept a Keyword Planner UI export: `csv_import.load_planner_csv(path)`.
Auction Insights CSVs: summarize overlap/position trends per competitor.

Output in every tier: REPORT.md with the top 20 opportunities, each carrying
volume (or proxy), difficulty proxy, intent guess, recommended action
(new page | optimize existing | ignore), and the evidence line.
