# Getting started

organic-os is a single Claude plugin. This page covers install, the
zero-credential quickstart, and the upgrade ladder for adding credentials one
at a time as you get comfortable with what the plugin does.

## Install

```
/plugin marketplace add shalintripathi/organic-os
/plugin install organic-os@organic-os
```

Both commands work the same way on Claude Code CLI and on Claude Cowork.
There is nothing to host: the plugin is skills, agents, slash commands, and
plain scripts invoked over Bash. No server, no database, no stdio MCP
process.

## Run setup

```
/organic-os:setup
```

This is an interview, not a form. It asks for the site URL, brand voice
rules, audience segments, target keywords, competitors, what connectors are
available (GA4, GSC, Notion, Slack, Canva), Google Ads token status, an
optional WordPress connection, which approval channel to use, and which
runtime should execute routines. Every question has a sensible default and
every answer is editable later by hand in `site-profile.yaml`.

Setup scaffolds a per-site "brain" repo (see `docs/site-repo-contract.md`)
and, if you choose a git brain, offers to create a private GitHub repo for
it. Nothing about your site or your answers is sent anywhere except into
that repo, which you own.

## The zero-credential quickstart

You can run organic-os against any public site with no credentials at all.
Analysis is always free; only mutation is gated (see
`docs/approval-channels.md`).

1. Run `/organic-os:setup` and answer the interview in analysis-only mode:
   skip WordPress, skip Google Ads, leave connectors unconfigured.
2. Run `/organic-os:onsite-audit https://yoursite.com`. This reads the live
   page, no login required, and reports on-page SEO findings.
3. Run the orchestrator (`/organic-os:daily` or ask for a full sweep). With
   no connectors it still produces signals from whatever public data it can
   reach and writes candidate briefs into the brain repo's `briefs/` and
   `proposals/` folders.
4. Open `approvals/queue.md` in the brain repo. That is your first queue of
   proposed work, sitting in `status: proposed`, waiting for a human
   decision. Nothing has touched your site yet.

## The upgrade ladder

Each rung below adds one credential or connector. None are required to get
value from the plugin; each one turns on a specific capability.

**Add GSC/GA4.** Authorize the Search Console and Analytics connectors (or
run any GSC/GA4 MCP server you already have in Claude Code) and organic-os
starts pulling real ranking and traffic signals instead of guessing from
public pages alone. See `docs/credentials/gsc-ga4.md`.

**Add WordPress.** Connect a dedicated Editor user with an Application
Password and organic-os can write approved on-page fixes and publish
approved drafts, always through the approval gate. See
`docs/credentials/wordpress.md`.

**Add Google Ads.** A developer token, even at the lowest access tier,
opens up keyword research beyond what GSC alone can mine. See
`docs/credentials/google-ads-token.md` for the full setup and what each
access tier enables.

**Add a channel.** In-session approval works from day one, but a channel
(Telegram, Slack, email, or a pr-merge workflow) lets proposals reach you
outside a live session, which matters once routines run on a schedule. See
`docs/approval-channels.md`.

**Schedule routines.** Once you are comfortable with what the plugin
proposes, move daily/weekly/monthly runs off manual and onto a schedule -
claude.ai scheduled tasks, a local cron job, or CI. See `docs/routines.md`
for the full comparison and setup steps for each runtime.
