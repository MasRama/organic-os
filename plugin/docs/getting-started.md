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

**Prerequisite:** the plugin's Python scripts need PyYAML. Check with
`python3 -c "import yaml"`; if that fails, run
`python3 -m pip install --user pyyaml` before running setup.

Every organic-os command is namespaced by the plugin name -
`/organic-os:setup`, `/organic-os:daily`, and so on - so there is no
collision with another plugin's `/setup` or `/daily` command in the same
session.

## Run setup

Not sure where to start? `/organic-os:start` health-checks the environment
(Python, PyYAML, the registry) and routes you into quick-start or full
setup for a new site, or a compact status view for a returning one. Setup
itself, walked through below, is what it hands off to either way.

```
/organic-os:setup
```

URL first, questions second. Setup asks for the site URL, then audits the
site itself - fetches the homepage and sitemap, detects WordPress/Yoast/
RankMath, reads a handful of representative pages - and proposes a full
profile: brand voice descriptors grounded in the actual copy, audience
segments, 5-9 seed keywords, 3-5 content-SERP competitors (sites competing
for the same queries, not necessarily business rivals), and target geos.
That proposal is presented as a table: accept all, edit specific rows, or
answer manually instead if you'd rather skip the inference entirely.

Only what the audit genuinely cannot answer gets asked directly: operator
knowledge (what already works in this niche - the audit cannot read your
experience), which connectors are available (GA4, GSC, Notion, Slack,
Canva), Google Ads token status, an optional WordPress connection, which
approval channel to use, and which runtime should execute routines. Every
question has a sensible default and every answer is editable later by hand
in `site-profile.yaml`.

Setup never prompts you to authorize a connector - it probes what you have
already connected and tells you exactly how to connect anything missing.
See `plugin/docs/connectors.md` for the full model and a capability-by-capability
table.

Setup scaffolds a per-site "brain" repo (see `plugin/docs/site-repo-contract.md`)
and, if you choose a git brain, offers to create a private GitHub repo for
it. Nothing about your site or your answers is sent anywhere except into
that repo, which you own.

## The zero-credential quickstart

You can run organic-os against any public site with no credentials at all.
Analysis is always free; only mutation is gated (see
`plugin/docs/approval-channels.md`).

1. Run `/organic-os:setup` and answer the interview in analysis-only mode:
   skip WordPress, skip Google Ads, leave connectors unconfigured.
2. Run `/organic-os:onsite-audit https://yoursite.com`. This reads the live
   page, no login required, and reports on-page SEO findings.
3. Run `/organic-os:daily`. It logs signals every run and only creates
   briefs or proposals when a signal crosses a significant threshold (a
   money-page drop, a lost AI citation). With zero credentials configured
   there are no GSC/GA4 sources to pull from, so expect a signal like "no
   sources available" rather than a queued brief or fix. For proposals from
   day one with no credentials, ask for a full audit (the orchestrator fans
   out to all eight specialists on public data alone) or run
   `/organic-os:onsite-audit` and `/organic-os:propose` against its findings.
4. Open `approvals/queue.md` in the brain repo. Once step 3 (or a full audit)
   queues something, that file is your first queue of
   proposed work, sitting in `status: proposed`, waiting for a human
   decision. Nothing has touched your site yet.

## The upgrade ladder

Each rung below adds one credential or connector. None are required to get
value from the plugin; each one turns on a specific capability.

**Add GSC/GA4.** Authorize the Search Console and Analytics connectors (or
run any GSC/GA4 MCP server you already have in Claude Code) and organic-os
starts pulling real ranking and traffic signals instead of guessing from
public pages alone. See `plugin/docs/credentials/gsc-ga4.md`.

**Add WordPress.** Connect a dedicated Editor user with an Application
Password and organic-os can write approved on-page fixes and publish
approved drafts, always through the approval gate. See
`plugin/docs/credentials/wordpress.md`. Want to try the loop risk-free
first? Set `onsite: {dry_run: true}` in `site-profile.yaml` - apply and
publish run the whole gated flow, write nothing, and the outcome record
lists every write that would have happened. Static site built from a git
repo instead of WordPress? Set `cms: {type: git-static, repo_root: ...}`
and approved changes arrive as pull requests against the site repo -
merging is the human's final act (see `plugin/docs/site-repo-contract.md`).

**Add Google Ads.** A developer token, even at the lowest access tier,
opens up keyword research beyond what GSC alone can mine. See
`plugin/docs/credentials/google-ads-token.md` for the full setup and what each
access tier enables.

**Enable IndexNow.** No account needed: setup's connector wizard generates
a key, you place `<key>.txt` at the site root, and once the wizard
verifies it by fetch, every successfully applied or published change gets
its URL submitted to Bing, Yandex, and the other participating engines
the moment it ships. See `plugin/docs/connectors.md`.

**Add a channel.** In-session approval works from day one, but a channel
(Telegram, Slack, email, or a pr-merge workflow) lets proposals reach you
outside a live session, which matters once routines run on a schedule. See
`plugin/docs/approval-channels.md`.

**Schedule routines.** Once you are comfortable with what the plugin
proposes, move daily/weekly/monthly runs off manual and onto a schedule -
claude.ai scheduled tasks, a local cron job, or CI. The weekly run adds a
striking-distance detector on top of its analytics/SERP/AI-citation check
and reflection: pages at GSC positions 4-15 with above-median impressions
surface as gated proposals, no extra credential beyond GSC. See
`plugin/docs/routines.md` for the full comparison and setup steps for each
runtime.

## Updating

`/plugin update organic-os` only ever touches plugin code - your brain
repo(s), `~/.config/organic-os/`, and any connected site are untouched by
design, and a brain-layout change always ships with a migration path. See
`plugin/docs/updating.md` for the full compatibility policy.
