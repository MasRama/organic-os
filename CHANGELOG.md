# Changelog

## [Unreleased]

## [0.1.4] - 2026-07-19

- **fix(ci):** all five CI runs since the 0.1.3 publish failed at
  collection, not on test results. Bare `pytest` on the runner lacks the
  repo root on `sys.path`, so the e2e test's `from tests.test_wp import
  FakeSession` import only ever resolved locally under `python -m
  pytest`. Fix: added `tests/__init__.py` and switched the CI step to
  `python -m pytest -q`.
- **hoo:** striking-distance detector in the weekly routine. `hoo-weekly`
  pulls 28 days of GSC queries, filters to positions 4.0-15.0 with
  impressions above the site's median, groups by page, and writes P2
  signals for the top 5 opportunities; a page with 2+ striking queries
  gets a gated `onpage-fix` proposal. Degrades to a one-line REPORT.md
  note with no GSC connector.
- **hoo:** the Monday report - a new `hoo-monday-report` skill and
  `/organic-os:monday-report` command that reads the brain's last 7 days
  and writes a five-section, under-400-word stakeholder summary (what
  moved, what shipped, what needs you, what we learned, next week). Every
  number traces to a brain file; a sparse week produces a shorter honest
  report, never a padded one.
- **security:** `scripts/verify-gates.sh` red-teams the approval gates
  against a throwaway brain repo - `require_approved`, `set_status`,
  `require_approval_lineage`, and `check_schema`, six probes, PASS/FAIL
  per probe. Referenced from `SECURITY.md` and README's Human gates
  section, and now runs in CI right after pytest.
- **docs:** ROADMAP gained three new items (site drift watch, gated
  image/alt-text fix workflow, topic clustering for content
  architecture) and moved the striking-distance detector, the Monday
  report, and the gate self-verification script into v0.2's "Landed
  early" note now that all three shipped here; the dry-run mode for
  `onsite-apply` that used to share a bullet with the self-verification
  script is now its own open item.

## [0.1.3] - 2026-07-18

- **core:** brain schema versioning - every scaffolded `site-profile.yaml`
  now carries `schema_version: 1`, and `core.contracts.check_schema()`
  classifies any brain repo as missing, pre-versioning (stamp needed),
  current, stale (migrate), or newer-than-plugin (update needed).
  `/organic-os:start`, `/organic-os:setup` update mode, and the three
  routine skills (`hoo-daily`, `hoo-weekly`, `hoo-orchestrator`) call it
  before doing any work and stop with the exact next action on an
  incompatible brain instead of guessing.
- **docs:** `docs/updating.md` - what `/plugin update organic-os` can and
  cannot touch (plugin code only; brain repos, `~/.config/organic-os/`,
  and WordPress are outside its reach by design), the semver compatibility
  policy, and the downgrade note.
- **docs:** `docs/connectors.md` - the probe-and-guide connector model
  (organic-os bundles no MCP servers and cannot trigger OAuth), why
  (stdio MCP does not run on Cowork), and a capability-to-connector table.
- **docs:** README FAQ gained two entries ("What happens when I update"
  and "Why does nothing prompt me to connect Google Analytics") linking
  the two new docs; version badge and verified inventory bumped to 0.1.3
  and 57 passing tests.

## [0.1.2] - 2026-07-18

- **onboarding:** `/organic-os:start` - the branded front door. Health-checks
  python3/PyYAML/the registry, then routes a new user into quick-start or
  full setup and a returning user into a compact status view (active site,
  pending approvals, last signal date) plus a menu; always closes by naming
  the three commands used most (daily, onsite-audit, weekly).
- **onboarding:** quick-start setup path - 3 questions (site URL, brand name
  + voice note, approval channel), everything else defaulted and stated in a
  closing summary table; a one-question-at-a-time interview style (default
  with every question, progress indicator, closing summary) now applies
  explicitly to every setup mode.
- **docs:** visual install walkthrough - three SVG terminal frames in
  `docs/images/` for marketplace add, plugin install, and the first
  `/organic-os:start` run, embedded in a new README "Install, step by step"
  section.
- **docs:** fully-namespaced command references confirmed across README and
  `docs/getting-started.md`, plus an explanatory line on why namespacing
  prevents collisions with other plugins' commands.

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
