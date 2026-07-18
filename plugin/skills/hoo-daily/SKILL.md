---
name: hoo-daily
description: Use for the daily signal pull - "run the daily", scheduled daily routine, or "pull today's numbers". Appends observations to the brain repo signals; never mutates the site or the skillbook.
---

# Daily signal pull (Generator role - append only)

Resolve the brain: use registry.get_active() when running interactively;
scheduled runs receive the brain path from the routine configuration.

1. Read site-profile.yaml. Determine available sources: GSC connector, GA4
   connector, tracked keywords in keywords/tracking.yaml, WordPress endpoint.
2. Pull, for yesterday (or since the last signal date - read the latest file in
   signals/): GSC clicks/impressions/CTR/position for top and tracked queries;
   GA4 sessions + AI-referral sessions (source contains chatgpt/perplexity/
   gemini/copilot); spot-check 3 tracked keywords in one AI engine, rotating.
3. Write one `append_signal` line per notable observation (threshold: any WoW
   move > 10% or position change > 2 or a new AI citation appearing/vanishing).
   Quiet days produce one line: "no notable movement (checked: <sources>)".
4. If an observation crosses P1 (drop > 30% on a money page), also
   `create_item(kind="onpage-fix"...)` or `kind="strategy"` and notify per the
   approval channel. Only send items where `is_notified(item)` is false; call
   `mark_notified(path)` right after a successful send.
5. Outcome follow-ups: for items in `outcomes/` with a due measurement date of
   today, run the measurement per skills/onsite-measure and record.
6. If brain mode is git: commit and push with message "signals: YYYY-MM-DD".

Missing sources are stated, never guessed. This skill NEVER writes skillbook.md.
