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
approved -> applied | drafted | failed
drafted  -> published
applied | published -> measured
```

`approved` is the only status a mutating skill will act on, and the code
that enforces this (`core.contracts.require_approved`, and
`require_approval_lineage` for stages past the first mutation, such as
publishing a drafted brief) refuses anything else. This is enforced in the
executor, not by convention - a proposal file hand-edited to say `approved`
without an `approvals:` entry still fails, because the gate also checks
that a decision was actually recorded.

`approvals/queue.md` in the brain repo is the index: every item currently
sitting at `proposed` appears there, rebuilt on every change. That file is
the thing you actually look at.

**No channel is privileged.** You choose one at setup; every channel below
records the same thing (actor, decision, channel, timestamp) into the same
file. Switching channels later is a one-line edit to `site-profile.yaml`.

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

When a routine has something to approve, it posts the proposal id, kind,
title, target, and a body excerpt, then exits without blocking - scheduled
runs never sit and wait. The next run polls `getUpdates` for a reply
matching the approve/reject grammar:

```
approve p-20260718-pricing-title
reject  p-20260718-pricing-title not now, revisit after the redesign
```

The reply must start with `approve` or `reject`, followed by the item id
exactly as posted; anything after that on a `reject` line is stored as the
reason. Polling is replay-tolerant - the same reply delivered twice (a
common effect of `getUpdates` retried across runs) is applied once.

## pr-merge

The most auditable channel, and the natural pair for the CI runtime. The
proposal arrives as a pull request against the brain repo; merging the PR
is the approval, and the PR's merge commit is the approval record. Rejecting
is closing the PR without merging. Because GitHub's own history captures
who merged and when, this channel needs no separate polling step - the next
run simply checks whether the PR merged.

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
