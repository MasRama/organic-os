---
name: onsite-propose
description: Use to turn audit findings or signals into concrete gated change proposals - "propose fixes for /pricing", /organic-os:propose.
---

# Propose on-page changes (creates gated items; applies nothing)

1. Input: audit findings, a signal reference, or a user request naming URLs.
2. For each change, draft the exact after-state: new title (<= 60 chars),
   new meta description (<= 155 chars), canonical, focus keyword, schema
   JSON-LD payload, or a content edit (quote the exact before/after text).
3. One proposal item per page: `create_item(kind="onpage-fix", target=<url>,
   body=<before/after table + rationale + expected effect + falsifiability>)`.
4. Rebuild queue. Notify per the profile approval channel. Only send items
   where `core.contracts.is_notified(item)` is false; call
   `core.contracts.mark_notified(path)` immediately after a successful send
   so re-runs never re-notify the same item:
   - in-session: present now with AskUserQuestion (approve/reject each)
   - telegram: send via core.telegram `send_item` (token from env file), then
     poll with `core.approval.process_telegram_decisions` on the next run to
     collect replies (offset persisted automatically)
   - pr-merge: commit the proposal file on a branch, open a PR (gh pr create)
   - slack/email: post/send a summary via the available connector; approval
     happens in-session or by channel reply read at the next run
5. Record any in-session decisions immediately via `record_decision`.
