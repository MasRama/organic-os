---
name: hoo-weekly
description: Use for the weekly health check + reflection - "run the weekly", scheduled weekly routine. Runs analytics-reporting-chief and serp-ai-monitor, then hands the week to the reflector.
---

# Weekly check

1. Read profile. Launch analytics-reporting-chief and serp-ai-monitor agents
   (parallel) with the profile path.
2. Save their reports under runs/YYYYMMDD-weekly/ (01-analytics.md,
   02-serp-ai.md, REPORT.md synthesis).
3. Append the week's headline observations as signals.
4. Invoke the organic-os:hoo-reflector skill to propose skillbook deltas from
   this week's signals + outcomes.
5. Queue any proposed work items; rebuild queue; notify per approval channel;
   commit + push if git.
