# ADR-0006: No SERP or autocomplete scraping

- Status: accepted
- Date: 2026-07-18
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
SERP position tracking and autocomplete or suggestion scraping are common in
SEO tooling, but Google has hardened against them with SearchGuard and
pursued legal action against a scraping vendor, suing SerpApi in December
2025. Shipping a scraper inside a public plugin would pass that legal
exposure on to every installer who runs it.

## Decision
organic-os ships no SERP or autocomplete scraper of any kind. Rank tracking,
SERP features, and keyword-suggestion data come only from official or
licensed sources the user brings: Google Search Console, the Google Ads API,
and documented third-party APIs (DataForSEO and similar) that the user
connects with their own credentials.

## Consequences
- No installer inherits scraping-related legal risk from running organic-os;
  SECURITY.md states this as an explicit guarantee.
- Some SERP-feature and rank-tracking data that scrapers can see stays
  unavailable unless the user brings a licensed API.
- Cost: keyword and rank-tracking coverage is gated by which paid APIs, if
  any, a user connects, so the free-tier experience is narrower than tools
  that scrape.
- If Google or a comparable provider ships an official rank-tracking API in
  the future, that becomes the path to add the missing coverage, not
  scraping.

## Agent Context
Proposed by the agent from research evidence; approved by the human in the
2026-07-18 design session, from its "No SERP/autocomplete scraping, ever"
analysis, citing Google SearchGuard and the SerpApi lawsuit, December 2025.
