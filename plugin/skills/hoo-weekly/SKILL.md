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
3. Append the week's headline observations as signals.
4. Invoke the organic-os:hoo-reflector skill to propose skillbook deltas from
   this week's signals + outcomes.
5. Queue any proposed work items; rebuild queue; notify per approval channel.
   Only send items where `is_notified(item)` is false; call `mark_notified(path)`
   right after a successful send. Commit + push if git.

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
