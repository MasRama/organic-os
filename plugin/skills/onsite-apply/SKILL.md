---
name: onsite-apply
description: Use to execute APPROVED on-page proposals - "apply the approved fixes", /organic-os:apply, or a routine's apply step. Refuses anything not approved.
---

# Apply approved changes (the gate lives here)

1. Read profile + env file. Poll the channel first if telegram
   (`poll_decisions` -> `record_decision` for each).
2. List approved onpage-fix items. For each:
   a. `require_approved(path)` - this raises on anything not approved. Never
      catch that error to proceed; report it and skip.
   b. `snapshot()` the post (title + meta + content if the proposal touches it)
      -> save to `outcomes/<item-id>-rollback.json` in the brain repo.
   c. Apply via wp.py: `update_rankmath` / `update_post` per the proposal body.
   d. Verify: `get_head(target_url)` - assert the new title/description appear
      in the rendered head. On mismatch: `rollback()` immediately, set item
      back by filing a new signal "apply-verify failed", and alert.
   e. `set_status(path, "applied", actor="agent")`; write an outcome record
      `outcomes/<item-id>.md`: what changed, when, rollback file, measurement
      due dates (+7d, +28d).
3. Commit + push the brain repo if git. Summarize: applied / skipped / failed.

HARD RULES: no snapshot -> no write. Verify after every write. A failed verify
means rollback, never retry-and-hope.
