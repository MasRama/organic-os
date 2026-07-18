# Roadmap

Themes, not promises. Ordered by user value within each release, not by
engineering convenience. Issues and PRs against any item here are welcome -
see `CONTRIBUTING.md`.

## v0.2 - Hardening the loop

- **Brain-repo schema versioning + migration entry point.** Every brain
  repo scaffolded so far assumes the current `site-profile.yaml` /
  `skillbook.md` / item-frontmatter shape. v0.2 adds a version marker and a
  migration path so a schema change does not silently break an existing
  installer's brain repo.
- **Gate self-verification script** (`scripts/verify-gates.sh`) plus a
  dry-run mode for `onsite-apply`. Confirms `require_approved` /
  `require_approval_lineage` actually block an unapproved write, without
  touching a real WordPress site.
- **Approval expiry.** Honest gap today: an item sitting at `approved` or
  `drafted` for weeks is still actionable with no re-confirmation step.
  v0.2 adds a staleness window after which a stale `approved`/`drafted`
  item requires re-confirmation before the next mutating stage runs.
- **Cost transparency per routine run.** Each daily/weekly/monthly run
  reports the token cost of the run it just completed, not just the
  runtime-level cost model in `docs/routines.md`.
- **Content decay detection in the weekly routine.** Extends the freshness
  check `hoo-monthly-audit` already does into the weekly cadence, so a
  decaying page surfaces sooner than once a month.
- **Bing Webmaster + IndexNow submission.** Bing indexation already matters
  to `onsite-audit` findings (strong-evidence tier, `docs/evidence.md`);
  v0.2 adds the submission side, not just the audit side.

## v0.3 - Beyond one CMS

- **CMS adapter contract extracted from `wp.py`.** Turns the current
  WordPress-specific write path in `plugin/lib/onsite/wp.py` into a
  documented interface any adapter can implement, so adding a CMS is a new
  file, not a fork.
- **Git-based static-site adapter.** Proposals arrive as pull requests
  against a static-site repo (Astro, Hugo, Jekyll, and similar) instead of
  a REST write - the approve gate becomes "merge the PR," matching the
  pr-merge approval channel that already exists.
- **Shopify adapter.** The second CMS-adapter implementation once the
  contract from the item above exists.
- **Internal-link graph analysis.** A site-wide crawl that maps internal
  links and flags orphaned or under-linked money pages, feeding
  `link-authority-strategist`.
- **Weekly stakeholder report** (markdown/PDF). A distillation of the
  week's signals, proposals, and outcomes meant to be shared outside the
  brain repo, for anyone who does not want to read `runs/` directly.
- **claude-seo audit import.** They audit, we operate: import a claude-seo
  report as a seed set of findings organic-os can turn into proposals,
  instead of re-deriving what a point-in-time audit already found.

## v1.0 - Many sites, many hands

- **Multi-site orchestration across brain repos.** The sites registry
  (`~/.config/organic-os/sites.yaml`) already tracks multiple sites; v1.0
  adds running routines across all of them in one pass, not one at a time.
- **Agency mode.** Named approvers per site, approval TTL - for an operator
  managing organic growth across client sites rather than one of their own.
- **CrUX Core Web Vitals monitoring.** Field data (not just the lab data
  `onsite-audit` can gather today) tracked over time per site.
- **Anonymized lessons library.** Tactic and evidence tier only, opt-in, no
  URLs, keywords, or brand names - the structured version of the "share a
  learning without data" path `CONTRIBUTING.md` describes today as an
  issue.
- **Adapter contribution guide.** A how-to for the CMS/channel adapter
  pattern established in v0.3, once there are enough real adapters to
  generalize from.

## Revisit triggers (not versioned)

Some items are blocked on something outside this project, not on
engineering time. They get picked up when the trigger fires, regardless of
which version is current:

- **WordPress `mcp-adapter` reaching 1.0** (see ADR-0003,
  `docs/adr/0003-rest-over-mcp-for-wordpress.md`) - the write path may move
  off plain REST once the official MCP bridge is no longer pre-1.0 and
  covers write operations, not just reads.
- **An official rank-tracking API** from Google or a comparable provider
  (see ADR-0006, `docs/adr/0006-no-scraping.md`) - organic-os ships no
  scraper by design; a licensed, official API is the only path to closing
  the rank-tracking coverage gap that decision leaves open.
