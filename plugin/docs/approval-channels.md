# Approval channels

## The protocol

Analysis is free; mutation is gated. Every proposed change - an on-page fix,
a content brief, a publish request, a keyword-strategy update - is a file in
the brain repo (`briefs/` or `proposals/`) with a `status` field in its
frontmatter. Nothing in organic-os writes to your site, or to the
skillbook, without a recorded approval attached to that file.

The status lifecycle:

```
proposed -> approved | rejected
approved -> applied | drafted | failed | partially-applied
partially-applied -> applied | failed
drafted  -> published
applied | published -> measured
```

`partially-applied` is the honest state for an approved proposal where some
changes landed and the rest hit a permission or capability wall; the queue
shows such items as PARTIAL rows with the human-follow-up note inline (see
docs/adr/0007 in the repo).

`approved` is the only status a mutating skill will act on, and the code
that enforces this (`core.contracts.require_approved`, and
`require_approval_lineage` for stages past the first mutation, such as
publishing a drafted brief) refuses anything else. This is enforced in the
executor, not by convention - a proposal file hand-edited to say `approved`
without an `approvals:` entry still fails, because the gate also checks
that a decision was actually recorded.

`approvals/queue.md` in the brain repo is the index: every item currently
sitting at `proposed` appears there, rebuilt on every change. That file is
the thing you actually look at. The rebuild also lints existing approval
records: an `approvals:` entry with no `decision` field (the fingerprint
of a hand-edit) is surfaced as a `MALFORMED-APPROVAL` row.

Never edit brain frontmatter directly. The contract CLI is the only write
path for status and approvals:

```
PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core approve <item-path> --actor NAME --channel CH [--note TEXT]
PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core reject  <item-path> --actor NAME --channel CH [--note TEXT]
PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core status  <item-path> <new-status> --actor NAME
PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core reset-to-proposed <item-path> --actor NAME [--note TEXT]
```

`reset-to-proposed` exists for exactly one case: an item file that entered
the brain with a non-proposed status and an empty approvals list - an
illegal birth state (items are born `proposed` via `create_item`). Such an
item can neither be approved nor pass a gate, so the queue flags it as an
`ILLEGAL-STATE` row naming this repair. The command refuses any item with
approval history; those reached their status legally and must move through
status transitions. The repair is recorded as a `status_note` on the item.

It prints the resulting status line, and refuses an illegal transition
with a nonzero exit and the reason on stderr - the same contract checks
every skill goes through.

**No channel is privileged.** You choose one at setup; every channel below
records the same thing (actor, decision, channel, timestamp) into the same
file. Switching channels later is a one-line edit to `site-profile.yaml`.

## What you will hear and when

Whatever channel you pick, the message taxonomy is the same, and it is
deliberately short. This table is the canonical definition (see
docs/INFORMATION-MAP.md in the repo):

| When | What arrives |
|---|---|
| A proposal needs you | The item (id, kind, title, target, body excerpt) plus how to approve or reject it |
| An apply or publish run finishes | ONE outcome summary for the run: applied-and-verified items, partially-applied items with the named human step, failed or rolled-back items with the reason, published posts with their URL |
| A daily run finds something actionable | ONE alert: P1 signals (drift, money-page drops) or the no-data nudge |
| Anything else | Nothing. Quiet days are silent - silence means no action needed, never that something was hidden |

The outcome summary exists because approval without feedback breaks the
loop: whoever said yes hears what happened, whether the change landed,
half-landed, or failed and was rolled back. Delivery is one message per
run, never one per item.

## Approval expiry

An approval is not forever, and expiry is a contract-layer fact: it is
enforced at the gate, not in any channel. No channel implements its own
clock and no channel can opt out - every channel's approvals age
identically, because both gates check the same recorded timestamp
regardless of where the decision came from. Concretely, the gates check
that the latest approved record is younger than the site's TTL - 30 days
by default, configurable per site in `site-profile.yaml`:

```yaml
approvals:
  ttl_days: 30
```

The key is additive (absence means the default; `schema_version` stays 1),
and the check is timestamp-based at gate time, so it applies to existing
approval records too. A TTL below 1 refuses; to disable expiry, set a
large value deliberately.

Expiry means re-confirm, never silent rejection. The expired item keeps
its status - `approved` stays `approved`, `drafted` stays `drafted` - and
the gate blocks with the exact command to run:

```
MUTATION BLOCKED: approval for 20260315-pricing-title.md expired
(approved 2026-03-15, ttl 30 days) - re-confirm with:
python3 -m core approve proposals/20260315-pricing-title.md --actor <you> --channel <channel>
```

Re-confirming appends a fresh approval entry through the same
`record_decision` path a first confirmation takes, refreshing the clock;
the item's history keeps every confirmation, and a replay within the TTL
is still a silent no-op, so duplicate deliveries never pad the record.
How you re-confirm depends only on where you are, not on any
channel-specific expiry machinery:

- **in-session:** the skill that hits the block re-asks you directly and
  records the fresh decision - the same AskUserQuestion flow as a first
  approval.
- **telegram:** the same gesture as confirming. Reply `approve` to the
  original proposal message again; because the decision lands in the
  same `record_decision` path, the expired approval is refreshed rather
  than no-opped.
- **slack / email:** the same reply semantics wherever the adapter reads
  replies at the next run. Today's adapters are notify-only, so
  re-confirm in-session or with the CLI below.
- **pr-merge:** merging is a one-time event, so a merged PR cannot be
  re-merged to refresh the clock. Leave a fresh approving comment on the
  PR to document the intent, and record the re-approval via the CLI
  below - the merge commit stays the original approval record, and the
  new entry sits alongside it in the item's history.
- **universal:** `python3 -m core approve <item-path> --actor NAME
  --channel CH` works from anywhere, whatever channel recorded the
  original approval.

See docs/adr/0008 in the repo.

## in-session

Nothing to set up. When you are in a live session and a skill has proposed
work, it asks you directly with AskUserQuestion. This is the default when
no channel is configured, and it is always available regardless of which
channel you pick for scheduled runs - a scheduled run that queues something
can always be approved the next time you are in-session.

## telegram

A two-minute walkthrough:

1. Message @BotFather on Telegram, send `/newbot`, follow the prompts, and
   copy the bot token it gives you.
2. Send any message to your new bot from the Telegram account you want to
   approve from.
3. Fetch your chat id: `curl "https://api.telegram.org/bot<TOKEN>/getUpdates"`
   and read `message.chat.id` from the response.
4. Store both values in the site's env file:
   ```
   TELEGRAM_BOT_TOKEN=xxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TELEGRAM_CHAT_ID=123456789
   ```
   and put `telegram_chat_id` (the same chat id) into `site-profile.yaml`
   under `approval:`.

Before the first poll can find your chat, send your bot any message once -
a bot cannot see a chat it has never been messaged in. Setup verifies by
sending a confirmation message back.

When a routine has something to approve, it posts the proposal id, kind,
title, target, and a body excerpt, then exits without blocking - scheduled
runs never sit and wait. The next run polls `getUpdates` for a reply
matching the approve/reject grammar:

```
approve p-20260718-pricing-title
reject  p-20260718-pricing-title not now, revisit after the redesign
```

The strict form starts with `approve` or `reject`, followed by the item id
exactly as posted; anything after that on a `reject` line is stored as the
reason. Polling is replay-tolerant - the same reply delivered twice (a
common effect of `getUpdates` retried across runs) is applied once.

**Reply-context decisions.** Typing an item id on a phone is friction, so
there is a second path: use Telegram's reply feature on the proposal
message itself, and a bare decision word is enough - the item id is read
from the message you replied to. The grammar, case-insensitive; the
phrase must START the reply:

| Decision | Accepted replies |
|---|---|
| approve | `approve`, `approved`, `yes`, `ok`, `go ahead`, `ship it`, `lgtm`, a thumbs-up emoji |
| reject | `reject`, `rejected`, `no`, a thumbs-down emoji |
| none (stays pending) | anything else - including `wait`, `hold`, `later` |

The negative set is deliberately narrow by design: deferrals like "wait
for now", "hold", or "later" are NOT decisions, because deferring is not
rejecting. Such a reply resolves nothing and the item stays pending for a
real answer - a "wait" that quietly rejected would destroy trust in the
channel.

Any text after the phrase becomes the note (so a reply of `go ahead and
fix the title too` approves with note "and fix the title too"). The rules
around it:

- The strict `approve <item-id>` grammar still works everywhere and takes
  precedence when both could apply - a typed id always wins over the
  replied-to message's id.
- A bare `approved` sent as a normal message (not a reply) resolves
  nothing: without a reply there is no item id to resolve against.
- A reply to a message that contains no item id resolves nothing.

Both paths land in the same approvals record and the same replay-tolerant
outcomes below.

Polling goes through `core.approval.process_telegram_decisions`, which
persists the last acknowledged Telegram update id at
`approvals/telegram-offset.json` in the brain repo. Every run reads that
file, polls `getUpdates` from just past it, and writes the new value back
atomically - so replies stay acknowledged across runs and are never
reprocessed (Telegram itself drops unacked updates after roughly 24h, which
is why acking promptly matters).

Each decision it processes gets one of three outcomes, and one bad reply
never blocks the rest of the batch:

- `recorded` - the decision applied (or already matched the item's current
  status - replays are a no-op, not an error).
- `stale` - the item has already moved past `proposed` (someone else
  approved it, or it was already applied); the reply is skipped, nothing
  raises.
- `unknown` - the item id in the reply does not exist in this brain repo;
  skipped, nothing raises. This is what makes **one Telegram bot shared
  across multiple sites** safe: each site's routine polls with its own
  offset and brain repo, and replies meant for a different site's items
  simply come back `unknown` and are ignored cleanly.

## pr-merge

The most auditable channel, and the natural pair for the CI runtime. The
proposal arrives as a pull request against the brain repo; merging the PR
is the approval, and the PR's merge commit is the approval record. Rejecting
is closing the PR without merging. Because GitHub's own history captures
who merged and when, this channel needs no separate polling step - the next
run simply checks whether the PR merged (`gh pr view <n> --json
state,mergedBy`) and records the decision that merge represents through
the contract CLI (`python3 -m core approve <item-path> --actor <merger>
--channel pr-merge`), the same entry every other channel writes. The
gates check the recorded entry; GitHub keeps the durable history.

This channel pairs naturally with the git-static CMS adapter
(`cms: {type: git-static}`, see `site-repo-contract.md`): there, approved
changes are themselves delivered as a pull request against the SITE repo,
so the same gesture governs both layers - merging the brain-repo proposal
PR approves the item, and merging the site-repo change PR is the human's
final act that publishes it. Two-layer honesty: no file is written to any
branch without an approved item, and nothing reaches the live site
without a human merging. The flow lives in skills/onsite-apply and
skills/onsite-publish.

## slack / email

Both are notify-only via your existing connector: a routine posts the
proposal to a Slack channel or sends an email summarizing it, but the
actual decision is still recorded either in-session or by replying at the
next run, the same as the in-session flow. These are thinner adapters than
telegram or pr-merge - useful for visibility, not required for the approval
record itself.

## Choosing one

Pick in-session if you mostly run organic-os interactively and do not mind
approving as you go. Pick telegram if you want a lightweight mobile
approval loop for scheduled routines. Pick pr-merge if the brain repo
already lives on GitHub and you want every mutation to leave a normal PR
history. slack/email are for teams who want visibility somewhere shared
without changing where decisions actually get made.
