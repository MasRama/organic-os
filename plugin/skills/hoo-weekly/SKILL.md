---
name: hoo-weekly
description: Use for the weekly health check + reflection - "run the weekly", scheduled weekly routine. Runs analytics-reporting-chief and serp-ai-monitor, then hands the week to the reflector.
---

# Weekly check

Resolve the brain: use registry.get_active() when running interactively;
scheduled runs receive the brain path from the routine configuration.

0. Run `core.contracts.check_schema(brain_path)` first. If not compatible,
   relay the action string and stop before any of the steps below.

1. Read profile. Launch analytics-reporting-chief and serp-ai-monitor agents
   (parallel) with the profile path.
2. Save their reports under runs/YYYYMMDD-weekly/ (01-analytics.md,
   02-serp-ai.md, REPORT.md synthesis).
3. Append the week's headline observations as signals. Include the
   week-over-week `ai_referrals` trend read from the week's daily signal
   lines (the AI-surface list is maintained in hoo-daily's SKILL.md -
   quote it, never extend it here); days without an `ai_referrals` line
   are stated as gaps, never interpolated. A sustained rise on a single
   landing page (3 or more of the week's daily lines) feeds the citation
   tracker: name the page in REPORT.md so the next citation run checks
   whether a new AI citation explains the traffic.
4. Invoke the organic-os:hoo-reflector skill to propose skillbook deltas from
   this week's signals + outcomes.
5. Queue any proposed work items; rebuild queue; notify per approval channel.
   Only send items where `is_notified(item)` is false; call `mark_notified(path)`
   right after a successful send. Commit + push if git.

Any content brief this run emits for comparison-intent queries (vs,
alternative, best X for) sets `brief_type="comparison"` on `create_item`;
absence means explainer (see docs/site-repo-contract.md).

Run cost: wrapper-invoked runs land one row in
`~/.config/organic-os/cost-ledger-YYYYMM.tsv` (written by the runtime
wrapper, never by this skill); the Monday report is what surfaces it.

## Striking distance

1. Pull GSC queries for the last 28 days for the profile's site.
2. Filter to positions 4.0-15.0 with impressions above the site's median
   impressions for the period.
3. Group the filtered queries by landing page.
4. For the top 5 opportunities, write one P2 signal per opportunity in
   falsifiable form: query | page | position | impressions | leading
   indicator to watch.
5. Where a single page carries 2+ striking-distance queries, `create_item(
   kind="onpage-fix", ...)` naming the specific on-page focus (the queries
   it should consolidate around) - gated through the approval queue like
   every other proposal, never applied directly.

No GSC connector: skip this section and note it as one line in REPORT.md
("striking distance: skipped, no GSC connector") instead of guessing.

## Cannibalization

1. From the same 28-day GSC query pull, find queries where two or more
   pages each earned impressions and neither holds a stable majority
   (guideline: the second page carries 20% or more of the query's
   impressions).
2. For the top 3 offending queries by total impressions, write one P2
   signal each: the query, both pages with their positions, the
   impression split between them, and the falsifiability check - "if
   consolidating did not lift the primary page's position within 28 days,
   the diagnosis was wrong."
3. Where a page on this list also appears in the striking-distance list
   above, note the linkage in the signal: cannibalization is often the
   blocker behind a stuck striking-distance position, not a content or
   authority gap.
4. For the single clearest case (largest impression split, most obvious
   primary-page pick), `create_item(kind="onpage-fix", ...)` naming the
   recommended consolidation direction - canonical tag, 301 redirect, or
   content merge - as a proposal item, gated through the approval queue
   like every other proposal, never applied directly. At most 1 gated
   proposal from this section per run.

No GSC connector: skip this section and note it as one line in REPORT.md
("cannibalization: skipped, no GSC connector") instead of guessing.

## Content decay

1. Pull each page's GSC clicks for the last 28 days and for the same
   page's 28-day window starting 90 days prior - two date-windowed pulls,
   not a single trend line.
2. Flag pages with a 30% or greater click decline between the two windows
   AND at least 50 clicks in the older window (noise floor - a 5-click
   page swinging 30% is not a signal).
3. For the top 3 flagged pages by absolute click loss, write one P2
   signal each: the page, both window values, the decline percent, and a
   likely-cause hypothesis read off position-vs-CTR movement across the
   same two windows - position fell = ranking problem; position held but
   CTR fell = SERP feature intrusion or title/meta staleness. Name which
   one the data points to.
4. For the single clearest case, `create_item(kind="content-brief", ...)`
   as a refresh brief - target the decayed page, cite the decline and the
   likely-cause hypothesis, and let it move through the normal brief
   lifecycle (approve -> skills/ce-produce -> skills/onsite-publish). At
   most 1 gated proposal from this section per run; never drafted or
   applied directly.

No GSC connector: skip this section and note it as one line in REPORT.md
("content decay: skipped, no GSC connector") instead of guessing.

## Mention opportunities

Runs after the detectors above, capped at roughly 10 minutes of work per
run - this is a sample, not a census.

1. From the profile take the top 3 topics (keywords.targets, file order)
   and the top 2 competitors (competitors, file order).
2. Via WebSearch, sample where the brand and those competitors are
   mentioned across public surfaces for those topics - industry
   roundups, comparison posts, community threads. Record per surface:
   URL, does the brand appear, does each competitor appear.
   WebSearch/WebFetch of public pages within the session is the
   sanctioned mechanism (docs/adr/0006 in the repo, same as the
   citation tracker); never scrape engines or third-party tools.
3. For each surface where a competitor appears and the brand does not,
   write one P3 signal in falsifiable form: the surface | why it
   matters (one line: what the surface answers and for whom) | the
   falsifiability check - "if a mention landed here does not show up in
   AI answers or referral traffic within 90 days, this surface mattered
   less than it looked."
4. At most ONE outreach proposal per run: for the single best-fit gap,
   `create_item(kind="strategy", ...)` naming the target surface, the
   angle (why that editor or thread would plausibly include the brand),
   and the existing asset to reference (a page, a tool, a data point
   already published - never one to be invented). Gated through the
   approval queue like every other proposal; a human executes the
   outreach. This skill NEVER contacts anyone - no emails, no form
   fills, no posts, no DMs.
5. Rationale line, carried next to this section's output in REPORT.md:
   brand mentions correlate roughly 3x more strongly with AI visibility
   than backlinks do, per Ahrefs' 75,000-brand study
   (https://ahrefs.com/blog/ai-brand-visibility-correlations/).
6. Sampling caveat, same discipline as the AI-visibility baseline:
   state which surfaces this session actually reached, and never let
   the report imply broader coverage than that.

No web access this session: skip this section and note it as one line
in REPORT.md ("mention opportunities: skipped, no web access") instead
of guessing.
