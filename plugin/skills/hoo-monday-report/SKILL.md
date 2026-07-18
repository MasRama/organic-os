---
name: hoo-monday-report
description: Use for a stakeholder-shareable weekly summary - "Monday report", "what happened this week", /organic-os:monday-report. Reads the brain only, invents no numbers, degrades to a shorter honest report on a sparse brain.
---

# Monday report

Resolve the brain: use registry.get_active() when running interactively;
scheduled runs receive the brain path from the routine configuration.

0. Run `core.contracts.check_schema(brain_path)` first. If not compatible,
   relay the action string and stop before any of the steps below.

1. Read the last 7 days only: `signals/YYYY-MM-DD.md` files in the window,
   `outcomes/` records touched in the window, `approvals/queue.md` as it
   stands today, `runs/` report folders created in the window, and any
   `skillbook.md` entries whose `last-confirmed` date falls in the window
   (cross-reference `reflections/` for the week to see which entries were
   added vs. just touched).
2. Write `runs/YYYYMMDD-monday-report/REPORT.md` with exactly these five
   sections, in this order, and no others:
   - **What moved** - the top 3 metric changes this week. Each line names
     the number and the file it came from (a signal line or an outcome
     record).
   - **What shipped** - proposals that reached `applied` and briefs that
     reached `published` this week, each with the item id and a link to
     its file in the brain.
   - **What needs you** - every item currently `proposed` in
     `approvals/queue.md`, one line each: what it is and what deciding it
     takes (a yes/no, not "please review").
   - **What we learned** - skillbook entries appended or edited this week,
     restated in plain language, no evidence-tier jargon, each with its
     source item.
   - **Next week** - the 2-3 highest-leverage `proposed` or `approved`
     items still queued, ranked by the expected impact stated in their own
     source signal or finding.
3. Every number and claim must trace to one specific file in the brain.
   Never invent a metric, a trend, or a "likely cause" the brain does not
   already state. If a section has nothing to report, say so in one line
   instead of omitting the section or padding it.
4. Write for a reader with no SEO background: plain nouns and verbs, no
   unexplained acronyms, no jargon. Keep the whole report under 400 words.
5. Sparse week (few or no signals, outcomes, or shipped items): the report
   gets shorter, not padded - state plainly what did not happen ("no
   proposals shipped this week; two are still waiting on your review").
6. Commit "monday-report: YYYY-MM-DD" if git.
