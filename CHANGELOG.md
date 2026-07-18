# Changelog

## [Unreleased]

## [0.1.1] - 2026-07-18

- **core:** telegram offset persistence (`approvals/telegram-offset.json`)
  and tolerant decision processing, so replayed `getUpdates` replies apply
  once and a bad reply never blocks the rest of a batch; a `notified` flag
  on items so a routine never re-sends an approval notification it already
  sent.
- **core:** canonical plugin-root invocations across every skill - fixed
  `PYTHONPATH` and docs-link references so `lib/core` resolves the same way
  regardless of which skill or command triggers it.
- **core:** sites registry (`~/.config/organic-os/sites.yaml`), mode-aware
  `/organic-os:setup` (update / add / switch / status), and guided
  `/organic-os:reset` teardown that never deletes a brain repo or revokes a
  credential on the user's behalf.
- **docs:** README v2 - mermaid loop and architecture diagrams, a verified
  inventory line, three persona-based quickstarts, a respectful comparison
  table, and a 6-item FAQ.
- **docs:** CONTRIBUTING.md with an enforced data boundary (audit check 7)
  and a matching `.github/PULL_REQUEST_TEMPLATE.md`.
- **docs:** ROADMAP.md - v0.2 hardening, v0.3 CMS/channel adapters, v1.0
  multi-site and agency mode, plus two revisit triggers tracked separately.

## [0.1.0] - 2026-07-18

- **core:** file-contract layer for the per-site brain repo - items
  (briefs/proposals) with a status lifecycle, an in-code approval gate
  (`require_approved`, `require_approval_lineage`), an append-only
  skillbook with evidence tags, channel-neutral approval adapters
  (in-session, telegram, slack/email, pr-merge), and the site-repo
  scaffolder.
- **head-of-organic:** setup interview, orchestrator, daily/weekly/monthly
  routines, 8 specialist agents, tiered Google Ads keyword intelligence
  (Basic/Standard planner, Explorer GAQL, GSC mining, CSV import), AI
  citation tracking, competitor intelligence, the weekly reflector, and a
  Notion/local task board.
- **onsite-optimizer:** WordPress REST client over Application Passwords,
  a bundled RankMath REST bridge mu-plugin, on-page audit (credential-free),
  gated apply with snapshot/verify/rollback, gated publish for
  content-engine drafts, and day-7/28 outcome measurement.
- **content-engine:** the six-stage content pipeline (research, draft, brand
  compliance, SEO/authority, editorial QA, edit) with an optional image step,
  generalized to run off any site's `site-profile.yaml`, plus a featured-
  image skill with a Canva step that degrades to an image brief.
- **docs:** getting-started, credential guides (Google Ads, GSC/GA4,
  WordPress), approval channels, routines and runtimes, an honest AEO/GEO
  evidence ranking, and the full site-repo contract.
- **playground:** reference WordPress deployment (compose file, Caddy
  snippet, bridge mu-plugin, runbook) for the parallel session that stands
  up the live demo site.
