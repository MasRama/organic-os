---
name: onsite-measure
description: Use to measure applied/published changes at day 7 and day 28 - "measure outcomes", /organic-os:measure, or the daily routine's follow-up step.
---

# Measure outcomes (closing the loop)

1. Scan outcomes/ for records with a due measurement date <= today that lack
   that measurement.
2. Per record: pull GSC for the target URL - clicks/impressions/CTR/position
   for the 7 (or 28) days after the change vs the same window before.
   GSC data lags 2-3 days: fetch the day-7 window no earlier than day 10,
   and the day-28 window no earlier than day 31.
   No GSC connector: record "unmeasured (no GSC)" honestly.
3. Append the delta to the outcome record + one signal line
   ("outcome <item-id>: position 8.2 -> 5.9 after title rewrite").
4. Wins and losses BOTH matter: the reflector reads outcomes to score
   skillbook entries helpful/harmful. Set status "measured" at day-28.
