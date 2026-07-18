---
name: hoo-daily
description: Use for the daily signal pull - "run the daily", scheduled daily routine, or "pull today's numbers". Appends observations to the brain repo signals; never mutates the site or the skillbook.
---

# Daily signal pull (Generator role - append only)

Resolve the brain: use registry.get_active() when running interactively;
scheduled runs receive the brain path from the routine configuration.

0. Run `core.contracts.check_schema(brain_path)` first. If not compatible,
   relay the action string and stop before any of the steps below.

1. Read site-profile.yaml. Determine available sources: GSC connector, GA4
   connector, tracked keywords in keywords/tracking.yaml, WordPress endpoint.
2. Pull, for yesterday (or since the last signal date - read the latest file in
   signals/): GSC clicks/impressions/CTR/position for top and tracked queries;
   GA4 sessions + AI-referral sessions (source contains chatgpt/perplexity/
   gemini/copilot); spot-check 3 tracked keywords in one AI engine, rotating.
3. Write one `append_signal` line per notable observation (threshold: any WoW
   move > 10% or position change > 2 or a new AI citation appearing/vanishing).
   Quiet days produce one line: "no notable movement (checked: <sources>)".
   If neither GSC nor GA4 was reachable this run (both connectors read
   anything other than `verified` in `connectors:`), write the literal line
   `no-data: GSC/GA4 not reachable from this runtime (checked: none)` instead
   - this exact string is what step 3.5 below counts and greps for, so do
   not paraphrase it.
3.5. **No-data escalation.** After writing today's signal, count consecutive
   daily signal files - today's plus however many immediately prior days'
   files also contain a `no-data:` line, walking backward by filename date
   and stopping at the first file that does not (a day with real data, or a
   missing file, breaks the streak). If that count reaches 3:
   - Check the last 7 days of signal files for a `nudge-sent:` line. If one
     is already there, skip sending - do not repeat the nudge more than once
     per 7 days.
   - Otherwise send one nudge through the configured approval channel. This
     is a plain notification, not an approval item - send_item-style text
     delivered directly over the channel (telegram: one `sendMessage`; slack:
     one post; email: one send; in-session: print it; pr-merge: no live
     channel mid-cycle, so just log it to the signal and skip delivery), not
     a `create_item`/approve-reject proposal:
     "3 daily runs with no analytics data - GSC/GA4 are not reachable from
     this runtime. Fix: run /organic-os:setup and use the connector wizard
     for GSC/GA4, or connect directly - claude.ai Settings -> Connectors, or
     /mcp / claude mcp add <server> in Claude Code."
   - Mark the nudge sent by appending `nudge-sent: no-data escalation
     (GSC/GA4)` to today's signal file via `append_signal` - this is the
     state marker; do not create a new state file for it.
4. If an observation crosses P1 (drop > 30% on a money page), also
   `create_item(kind="onpage-fix"...)` or `kind="strategy"` and notify per the
   approval channel. Only send items where `is_notified(item)` is false; call
   `mark_notified(path)` right after a successful send.
5. Outcome follow-ups: for items in `outcomes/` with a due measurement date of
   today, run the measurement per skills/onsite-measure and record.
6. If brain mode is git: commit and push with message "signals: YYYY-MM-DD".

Missing sources are stated, never guessed. This skill NEVER writes
skillbook.md. The no-data nudge in step 3.5 is a notification, never an
approval item - it needs no decision, just a fix.

## Drift watch

Runs only when the profile's WordPress connector is verified - drift is
WP-only, there is no page inventory to snapshot without it.

1. Build the tracked-page set: the WordPress post id recorded in every
   `outcomes/*-rollback.json` snapshot (already captured by onsite-apply's
   verify step), any `proposals/` item's target page still in play, plus
   the homepage - deduped, capped at 20.
2. First run for this brain (`onsite.drift.baseline_path(root)` does not
   exist yet): `onsite.drift.snapshot_pages(wp, page_ids)`, then
   `save_baseline`. Append one signal noting the baseline was established
   and how many pages it covers.
3. Every later run: snapshot the same tracked-page set again and
   `onsite.drift.compare(root, snap)`. Empty list: one quiet signal line,
   nothing else to do. Any diff: one P1 signal per changed page, naming
   the field, the old value, and the new value - "changed outside the
   loop: field, was, now - if this change was yours, refresh the
   baseline; if not, investigate theme or plugin updates."
4. Refresh the baseline (`save_baseline`) only AFTER the signal for that
   run's diff has been written, so a given drift is reported exactly once
   and never silently re-baselined out from under a pending
   investigation.

No WordPress connection: skip silently, no note needed - unlike the GSC
sections in the weekly routine, there is no page inventory to have
skipped pulling.
