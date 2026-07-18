---
name: hoo-monthly-audit
description: Use for the monthly deep audit - "run the monthly audit", /organic-os:monthly-audit, or the scheduled monthly routine.
---

# Monthly deep audit

1. Full sweep via the orchestrator pattern: launch all eight specialists in
   parallel with the profile path.
2. Additionally: content freshness review (pages > 12 months stale that hold
   rankings - freshness is a strong-evidence AEO factor), schema validity,
   internal-link health, tracked-keyword trend over the month, outcomes review
   (which applied changes moved metrics; feed wins/losses to the reflector).
   Run the page-essentials dimension (skills/onsite-audit step 3: author
   entity, answer capsule, in-content images, social image shape,
   publisher schema shape, sitemap membership) site-wide across the
   audited page set, not only on newly flagged pages - the checklist is
   the product's eyes, and a check that does not run cannot fire.
3. Compare with last month's runs/ artifacts; the report leads with deltas.
4. File signals, briefs, and fixes through core contracts; rebuild queue;
   notify per approval channel. Only send items where `is_notified(item)` is
   false; call `mark_notified(path)` right after a successful send.
5. Output runs/YYYYMM-monthly/REPORT.md: executive summary in plain language,
   then per-specialist sections, then this month's queued work.

At each stage boundary, append a one-line progress marker with a UTC
timestamp to the run report file before starting the stage - headless runs
are watched by tailing that file, not a terminal.
