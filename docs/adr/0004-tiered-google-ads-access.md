# ADR-0004: Tiered Google Ads access for keyword intelligence

- Status: accepted
- Date: 2026-07-18
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
hoo-keyword-intel wants Google Ads Keyword Planner data (search volume,
competition, forecasts), but planner calls require Basic or Standard API
access, and Google's Basic-access approval queue is backlogged through 2026.
Many installers, including Shivaa's own token, will sit at Explorer or
no-token for weeks.

## Decision
hoo-keyword-intel degrades through four tiers detected at runtime:
Basic/Standard (full planner via `GenerateKeywordIdeas` and
`GenerateKeywordHistoricalMetrics`), Explorer/pending (own-account GAQL
search-term mining plus an honest "apply for Basic" message, with planner
calls blocked), no token (Google Search Console query mining, 16 months of
history), and manual (CSV import of Keyword Planner UI exports and Auction
Insights exports).

## Consequences
- The skill never blocks or errors when a user lacks Basic access; it
  returns the best available data for that tier and states which tier it
  used.
- Demo and early-adopter usage is not gated on Google's approval backlog.
- Cost: output shape and confidence differ by tier, so downstream skills
  (briefs, competitor gap analysis) must handle four data qualities instead
  of one.
- The CSV tier requires a manual export step from the user, so it cannot run
  unattended inside a scheduled routine.

## Agent Context
Proposed by the agent from research evidence; approved by the human in the
2026-07-18 design session, from its hoo-keyword-intel tiering analysis and the
2026 Google Ads API Basic-access approval backlog.
