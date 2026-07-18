---
name: onsite-apply
description: Use to execute APPROVED on-page proposals - "apply the approved fixes", /organic-os:apply, or a routine's apply step. Refuses anything not approved.
---

# Apply approved changes (the gate lives here)

1. Read profile + env file. Poll the channel first if telegram, via
   `core.approval.process_telegram_decisions(root, token, chat_id)` - it
   persists the poll offset and tolerates unknown/stale ids without raising.
2. List approved onpage-fix items. For each:
   a. `require_approved(path)` - this raises on anything not approved. Never
      catch that error to proceed; report it and skip.
   b. `snapshot()` the post (title + meta + content if the proposal touches it)
      -> save to `outcomes/<item-id>-rollback.json` in the brain repo.
   c. Apply via wp.py: `update_rankmath` / `update_post` per the proposal body.
   d. Verify: `get_head(target_url)` - assert the new title/description appear
      in the rendered head. On mismatch: `rollback()` immediately, then
      `set_status(path, "failed", actor="agent")`, append a signal
      "apply-verify failed", and alert. Never leave the item approved.
   e. `set_status(path, "applied", actor="agent")`; write an outcome record
      `outcomes/<item-id>.md`: what changed, when, rollback file, measurement
      due dates (+7d, +28d).
   f. On a successful verify, refresh the drift baseline for this page
      (`onsite.drift.snapshot_pages` on this post id, merged into the
      stored `onsite.drift.baseline_path` entry, then `save_baseline`) so
      the change we just made intentionally is never flagged as drift by
      the next `hoo-daily` run.
3. Commit + push the brain repo if git. Summarize: applied / skipped / failed.

HARD RULES: no snapshot -> no write. Verify after every write. A failed verify
means rollback, never retry-and-hope.
