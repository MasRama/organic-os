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
   c. Apply via the CMS adapter (`onsite.cms.adapter_for`; wordpress or
      git-static per `cms.type` - the git-static branch below replaces
      steps b-g):
      `update_seo_meta` / `update_post` per the proposal body.
      (`update_rankmath` remains as the WordPress adapter's alias for
      `update_seo_meta`.)
   d. Verify: `get_rendered_head(target_url)` - assert the new
      title/description appear in the rendered head. On mismatch:
      `rollback()` immediately, then
      `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core status
      <item-path> failed --actor agent`, append a signal
      "apply-verify failed", and alert. Never leave the item approved.
   e. `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core status
      <item-path> applied --actor agent`; write an outcome record
      `outcomes/<item-id>.md`: what changed, when, rollback file, measurement
      due dates (+7d, +28d).
   f. On a successful verify, refresh the drift baseline for this page
      (`onsite.drift.snapshot_pages` on this post id, merged into the
      stored `onsite.drift.baseline_path` entry, then `save_baseline`) so
      the change we just made intentionally is never flagged as drift by
      the next `hoo-daily` run.
   g. IndexNow: when site-profile.yaml has `indexnow: {enabled: true,
      key: ...}` (additive key), call `hoo.indexnow.submit(host, key,
      [target_url])` after the successful verify and record the returned
      status in the outcome record (`indexnow: {status: N, submitted: 1}`).
      A non-200 is recorded, never retried in-run, and never fails the
      apply. Skipped in dry-run - nothing changed, nothing to submit.
3. Commit + push the brain repo if git. Summarize: applied / skipped / failed.
4. Outcome summary - the approver always hears what happened. Compose ONE
   message for the whole run and deliver it through the configured
   approval channel (telegram: one `sendMessage` over the same transport
   `send_item` uses; slack/email: one post/send; in-session: print the
   summary; pr-merge: no live channel mid-cycle - append the summary to
   the run report and outcome records instead). Never send per-item
   messages. Content, one line per item:
   - applied and verified: item id + what changed
   - partially-applied: item id + the exact human step from the status
     note - the approver must know what is waiting on them
   - failed / rolled back: item id + the reason
   Silent success is a bug: whoever said yes hears the result, whether it
   landed, half-landed, or failed. A run that touched nothing sends
   nothing.

## Git-static sites (cms.type git-static)

The adapter is chosen by `cms.type` (`onsite.cms.adapter_for`). When it is
git-static, the write target is a local clone of the site repo
(`cms.repo_root`) and the pull request is the delivery mechanism. The gate
does not move: step 2a's `require_approved` runs unchanged, BEFORE any
file is written to any branch. The adapter never runs git; this skill runs
every git/gh command below.

0. pr-merge channel only, before the gate: proposals on such sites arrive
   as PRs against the brain repo, and the human merge IS the approval.
   Detect newly merged proposal PRs (`gh pr view <n> --json
   state,mergedBy`) and record each decision the merge represents:
   `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core approve
   <item-path> --actor <merger> --channel pr-merge`. The merge commit is
   GitHub's durable record; the CLI entry is the one the gates check. A
   closed-unmerged proposal PR is a rejection - record it with `core
   reject` the same way. (This mirrors step 1's telegram poll.)
   On every other channel the item was approved before this skill ran,
   and the site PR below is created only AFTER that approval.
1. Gate: `require_approved(path)` - unchanged, never caught to proceed.
2. Freshen the clone (`git pull` on the default branch in `cms.repo_root`).
3. `snapshot()` each target file (the snapshot stores the file's full
   text) -> `outcomes/<item-id>-rollback.json` in the brain repo.
4. Apply via the adapter: `update_seo_meta` / `update_post` per the
   proposal body - frontmatter and body edits in the working tree only.
5. Deliver as a PR - run:
   `git checkout -b organic-os/<item-id>`, `git add` the changed files,
   `git commit`, `git push -u origin organic-os/<item-id>`, then
   `gh pr create --title "<item title>" --body "<the proposal text>"`.
6. Honest status: the adapter's `capabilities()` declares `needs_human:
   ["merge-pr", "deploy"]`, so the item does NOT become applied here. Set
   `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core status
   <item-path> partially-applied --actor agent --note "PR <url> open - a
   human must merge; the site then deploys itself"`. The queue shows it
   as a PARTIAL row until the merge. No publish happens without a human.
7. Merge detection, next run: `gh pr view <n> --json state,mergedBy`.
   Merged -> `core status <item-path> applied --actor <merger>`; write
   the outcome record (what changed, PR url, who merged and when,
   measurement due dates +7d, +28d). On a pr-merge-channel site this
   merge doubles as the human sign-off; the merge commit and the outcome
   record carry it. Closed unmerged -> a human said no: `core status
   <item-path> failed --actor agent --note "PR closed unmerged"` and
   delete the branch; nothing reached the default branch, so the
   rollback file needs no replay.
8. Verify, honestly: `rendered_head_verify` is False for this adapter -
   there is no rendered head to assert at apply time, and step 2d's
   verify does not run. If the profile has `cms.deploy_url`, fetch the
   live page after merge detection and record the result in the outcome
   as a best-effort post-deploy check, labeled exactly that - it never
   counts as the WordPress-grade verify. IndexNow (step 2g) also moves
   to after merge detection: only a merged and deployed change has a
   live URL to submit. Skip the drift-baseline refresh (step 2f); the
   drift watch is WordPress-only.

Dry-run with git-static: the same rules as below - the gate still runs
first, the adapter logs every intended write in `dry_run_log`, and with
nothing written to the clone there is nothing to commit: no branch, no
PR. The outcome record, marked dry-run, lists the log.

## Dry-run mode

When site-profile.yaml has `onsite: {dry_run: true}` (additive key, schema
stays 1), construct the CMS adapter with `dry_run=True`
(`adapter_for(profile, ..., dry_run=True)`) and run
the full flow above unchanged - `require_approved` is still enforced
BEFORE the dry-run write, so a dry run rehearses the real path, gate
included, not a shortcut around it. Nothing reaches the site: every
mutating call lands in the adapter's `dry_run_log` instead of the session,
and reads (snapshot, get_rendered_head) behave normally. Skip step 2d's
verify assertion (a
write that never happened cannot appear in the rendered head) and do NOT
set the item to `applied` - it stays `approved` so a real apply can follow.
Write the outcome record marked `dry-run: true`, listing every entry from
the adapter's `dry_run_log` - each write that would have happened, with method,
post id, and fields. Skip the drift-baseline refresh (2f); the page did
not change.

## Partial application

When some changes in a proposal succeed and others hit a permission or
capability wall (a step needs a WordPress role the connected user does not
have), do NOT pick between "applied" and "failed" - both would lie. Set the
honest state via the contract CLI, with a note naming exactly what a human
must finish:

```
PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core status <item-path> \
  partially-applied --actor agent --note "<exactly what a human must finish>"
```

The outcome record lists done vs pending: every change that landed (with
its verify result) and every step still waiting on a human, each named
precisely. Once the human finishes the pending steps, the item moves
partially-applied -> applied via the CLI; if the partial work is rolled
back instead, partially-applied -> failed.

HARD RULES: no snapshot -> no write. Verify after every write. A failed verify
means rollback, never retry-and-hope. Never edit brain frontmatter directly.
The contract CLI is the only write path for status and approvals.
