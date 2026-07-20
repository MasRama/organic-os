# Threat model

organic-os edits live websites. That is the whole point, and it is also the
reason to be precise about what the plugin can touch, what the worst case
looks like, and what stops it. This document is the map. It complements
[SECURITY.md](SECURITY.md), which covers reporting and the env-file
convention.

## Permissions and scopes

Every capability below is off until you configure the credential behind it.
organic-os bundles no credentials, no MCP servers, and no scrapers, and it
states plainly which capabilities it found configured this session. No
credential value ever lives in this repo or in a site's brain repo: the brain
stores only a reference that a credential exists.

| Capability | What it accesses | Credential or connector | Where the credential lives |
|---|---|---|---|
| Read analytics | GA4 sessions, referral segmentation, per-page metrics (read-only) | GA4 through your own connector or MCP server | claude.ai connector store or your MCP config, never a repo |
| Read search data | GSC queries, positions, impressions, clicks (read-only) | GSC through your own connector or MCP server | claude.ai connector store or your MCP config, never a repo |
| Read and write WordPress | Posts, SEO meta, media alt text, the author profile description | WordPress REST API as a dedicated Editor-role user with an Application Password | `~/.config/organic-os/<site>.env` (chmod 600), or the OS keychain via the plugin's sensitive `userConfig` fields |
| Write git branches | Content files in a local clone, on an `organic-os/<item-id>` branch, opened as a PR | the git and gh auth you already hold; the git-static adapter never shells out, the skill layer runs git/gh | your machine's own git/gh credential store, never a repo |
| Send to approval channel | Proposal notifications, outcome summaries, the Monday report document | Telegram bot token, or Slack, email, or pr-merge through your connector | keychain (sensitive `userConfig`) or the site env file, never a repo |
| Run routines | Invokes the skills above on the cadence declared in the site profile | the runtime you chose: claude.ai scheduled tasks, a local OS schedule, or CI | that runtime's own auth (`claude setup-token`, a CI secret), never a repo |

Optional add-ons follow the same rule: Google Ads (a developer token plus
OAuth you generate), IndexNow (a key file you place at the site root), and
any BYO SERP or backlink adapter each read from your own env file or
connector, and each is absent until you set it up.

## Blast radius

The realistic worst case is a mis-approval: a human approves a proposal that
should not have shipped. What that can and cannot do:

- **On WordPress**, the write is scoped to the Editor role. It can change post
  content, SEO meta, media alt text, and the author description on the
  configured site. It cannot install plugins, change site settings, touch
  other users, or reach Administrator surfaces: those are declared
  `needs_human` and the item ends `partially-applied` with the exact manual
  step named, never faked as done.
- **On a git-static site**, the change lands on a branch as a PR. Nothing goes
  live until a human merges and the site redeploys, so a mis-approval is a PR
  to close, not a live edit.

The mitigations, layered:

- **The contract gate.** Every mutating call runs behind
  `core.contracts.require_approved` or `require_approval_lineage`, checked in
  code before the write, not by convention. A hand-edited `status: approved`
  with no matching `approvals:` entry still fails. Verify it yourself with
  `./scripts/verify-gates.sh`.
- **Dry-run.** `onsite: {dry_run: true}` runs the full gated flow, approval
  check included, and writes nothing, recording every change it would have
  made. You can rehearse the real path on your real site with zero writes.
- **Snapshot and rollback.** Each mutating adapter snapshots the prior state
  before it writes, and rollback restores it byte-identical. A verify step
  reads the change back from the live page after it lands.
- **Partially-applied honesty.** When part of an approved proposal cannot be
  performed, the item ends `partially-applied` naming exactly what a human
  must finish. An adapter never claims success for an action it cannot do.
- **Approval expiry.** Approvals lapse after a per-site TTL (default 30 days).
  Once expired, both gates block until you re-confirm, so a stale yes never
  ships months later.

## What it never does

- **No SERP or autocomplete scraping**, ever, by design
  ([ADR-0006](docs/adr/0006-no-scraping.md)). Ranking and citation data come
  only from APIs and connectors you authorized.
- **No telemetry, no phone-home.** Nothing about your site, your usage, or
  your credentials leaves your machine except to the APIs you configured.
- **No outbound calls** other than to those user-configured APIs. There is no
  server process and no background network activity.
- **No business data in this repo.** A site's profile, keywords, skillbook,
  and signals live in your own private brain repo. CI check 7 in
  `scripts/audit.sh` fails the build if brain-shaped content ever lands here.

## Release integrity

- A release is tagged only from a commit on `main` that passed CI green
  (pytest, `scripts/audit.sh`, and `scripts/verify-gates.sh`). The tag is the
  integrity anchor: what you install is the tagged, tested tree.
- **Build-provenance attestation (Sigstore / SLSA) is not yet implemented.**
  It is a roadmap item, stated here honestly rather than implied. Until it
  ships, the tag on a CI-green commit is the guarantee on offer, and nothing
  claims a cryptographic build attestation that does not exist. See
  [ROADMAP.md](ROADMAP.md).
