# Changelog

## [Unreleased]

## [0.3.0-alpha.2] - 2026-07-19

Adapter two: git-static. Proposals arrive as pull requests; merging is
approving.

- **feat(onsite): git-static adapter.** `plugin/lib/onsite/gitstatic.py`
  implements the CmsAdapter contract for static sites built from a git
  repo (Astro, Next, Hugo, Jekyll class): content is markdown/MDX files
  with YAML frontmatter, and the adapter reads and writes them in a
  LOCAL CLONE (`cms: {type: git-static, repo_root: ..., content_dir:
  ..., fields: {...}}`). It never shells out to git - the skill layer
  runs the git/gh commands, which keeps the adapter testable and honest.
  Frontmatter conventions, overridable per site via the `fields`
  mapping: title, description, canonical, the draft flag, slug, and
  `jsonld` for a raw JSON-LD string the site's layout must render.
  `capabilities()` declares the gaps instead of papering over them:
  `schema_injection: "frontmatter-field"`, `rendered_head_verify: False`
  (static sites verify post-deploy), `needs_human: ["merge-pr",
  "deploy"]`, and `get_rendered_head` raises naming the gap rather than
  faking a verify. Snapshot stores the file's full text; rollback
  restores it byte-identical. Dry-run mirrors WPClient: zero writes,
  every intent in `dry_run_log`. `adapter_for` builds it from the
  additive `cms:` profile key. 35 new tmp-dir tests (no real git, no
  transport) bring the suite to 180.
- **feat: git-static skill path + pr-merge flow.** onsite-apply and
  onsite-publish gain the git-static branch: the gate check runs
  unchanged BEFORE any write, changes land on a new
  `organic-os/<item-id>` branch, `gh pr create` carries the proposal
  text as the body, and the item sits `partially-applied` (apply) or
  stays `drafted` (publish) until merge detection (`gh pr view --json
  state`) moves it to applied/published - no publish without a human
  merge. For pr-merge-channel sites the brain-repo proposal PR's merge
  is recorded as the approval via the contract CLI when detected, so
  the same gesture governs both layers. Verification states the honest
  limit: no rendered head at apply time; a best-effort live fetch
  against `cms.deploy_url` after the merge, recorded as exactly that.
  Docs in the same wave: site-repo-contract documents the git-static
  profile keys, approval-channels' pr-merge section covers the
  two-layer flow, getting-started gains the one-line git-static
  variant, and the information map's adapter row names both supported
  types.
- **docs + release.** CONTRIBUTING cites GitStaticClient as the second
  reference implementation - the smallest honest adapter, no transport
  at all; ROADMAP moves the git-based static-site adapter to landed
  early (the Shopify adapter stays deprioritized, as documented).

## [0.3.0-alpha.1] - 2026-07-19

The v0.3 phase opens with its structural priority: the CMS adapter
contract. Alpha signals the phase is open, not finished.

- **refactor(onsite): CmsAdapter contract; WordPress is adapter one.**
  `plugin/lib/onsite/cms.py` defines the cms capability slot's interface
  (ADR-0009): `CmsAdapter` with `get_post`, `update_post`, `create_post`,
  `update_seo_meta`, `get_rendered_head`, `snapshot`, `rollback`, plus
  the introspection pair `capabilities()` (what the adapter can do, and
  the `needs_human` actions it honestly cannot) and `adapter_name()`.
  The `adapter_for` factory builds the configured adapter from the
  additive `cms: {type: wordpress}` site-profile key, defaulting to
  wordpress when a wordpress endpoint exists and refusing unknown types
  by naming the supported list. `WPClient` implements the contract:
  `update_rankmath` and `get_head` stay as the WordPress-specific
  implementations, with the contract names delegating to them. The
  onsite skills now speak slot language ("the CMS adapter, WordPress
  today"), drift accepts any adapter, and 20 new contract tests bring
  the suite to 145.
- **docs: adapter contribution guide.** CONTRIBUTING's "Contributing a
  CMS adapter" section: implement `CmsAdapter`, the `capabilities()`
  honesty rule (`needs_human` steps end partially-applied, never faked
  success), the fake-transport test bar mirroring `tests/test_wp.py`,
  and gates stay in core (adapters never gate). The PR template gains
  the adapter checklist line; ROADMAP marks the contract landed early,
  with the git-static and Shopify adapters remaining open.
- Honesty note: this release is a pure refactor with zero behavior
  change, proven by the pre-existing test suite passing unmodified.

## [0.2.1] - 2026-07-19

Channel neutrality, made explicit and made checkable.

- **docs:** expiry re-confirmation is channel-neutral. The approval-expiry
  section now leads with the contract-layer fact - expiry is enforced at
  the gate, not in any channel, so every channel's approvals age
  identically - and documents the re-confirm path per channel: in-session
  re-ask, Telegram reply to the original message, slack/email reply where
  the adapter reads replies, pr-merge comment plus CLI re-approval
  (merging is a one-time event), and the universal `python3 -m core
  approve`. README's human-gates section states the rule in one line.
- **docs:** ADR-0009, capability slots over tool bindings. Every external
  dependency belongs to a named capability slot (analytics, search-data,
  image-generation, approval-channel, cms, indexing) with tools as
  swappable adapters behind it: contract and gate logic never references
  a specific tool, skills name the configured adapter from the site
  profile, and new tools (Microsoft Clarity for analytics, Gemini for
  image generation) are adapter additions, never rewrites. The roadmap
  names ADR-0009 as the governing principle for all adapter work and adds
  the analytics and image-generation slots to v0.3.
- **audit:** check 8, information integrity. `docs/INFORMATION-MAP.md`
  tables every load-bearing fact (plugin version, test and inventory
  counts, approval TTL, schema version, install commands, brain layout)
  with its canonical source, every quoting file, and who checks it; audit
  check 8 mechanically verifies that relative markdown links resolve,
  that the README version badge and marketplace.json match plugin.json,
  and that the README tests badge and inventory line match pytest and the
  filesystem. Its first run against the repo caught real drift: the
  README version badge still said 0.1.9 and both test-count quotes still
  said 90 (actual: 125) after two releases, the install SVG still showed
  v0.1.3 with 19 skills and 19 commands, and CONTRIBUTING still said 52
  tests. All fixed; CONTRIBUTING now states the expectation without a
  number, which removes that drift surface for good.

## [0.2.0] - 2026-07-19

Approval expiry - the last v0.2 item - and the release that closes the
v0.2 phase.

- **core:** approval expiry (ADR-0008). Approvals lapse after 30 days by
  default, configurable per site with the additive `approvals:
  {ttl_days: n}` key in `site-profile.yaml` (`schema_version` stays 1;
  below 1 refuses). Both gates - `require_approved` and
  `require_approval_lineage` - now verify the latest approved record is
  younger than the TTL, comparing UTC dates at gate time, so the check
  applies retroactively to existing records with no migration. Expiry
  means re-confirm, never silent rejection: the item keeps its status and
  the gate blocks with the exact `python3 -m core approve` command to
  run; that command (or a Telegram reply of `approve` to the original
  proposal message) appends a fresh approval entry through
  `record_decision`, refreshing the clock, while a replay within the TTL
  stays a silent no-op. Proven end to end by verify-gates probe 8
  (12 new tests).

**v0.2 in aggregate.** Most of the phase shipped ahead of this release in
v0.1.3 through v0.1.10; this entry closes it. The headline capabilities:
the setup verification block (postflight scorecard, runtime-location
awareness, connector wizard with live verification, one-secret-at-a-time
credentials), the observe-side detectors (striking-distance,
cannibalization, content decay, site drift watch), the audit-and-propose
interview with the AI-visibility baseline at setup, cost transparency plus
dry-run mode plus Bing/IndexNow submission, and the field-run hardening
wave (contracts CLI, reply-context Telegram approvals, the
partially-applied state, headless resilience) - now capped by approval
expiry, so a gate never acts on a stale yes.

## [0.1.10] - 2026-07-19

Approval UX and contract ergonomics - fixes from the first full pipeline
field run, which continues to set the priorities here.

- **core:** reply-context Telegram approvals. Replying to a proposal
  message with a bare decision word now works: approve/approved/yes/ok/
  thumbs-up approve, reject/rejected/no/thumbs-down reject, with the item
  id resolved from the replied-to text and any trailing words kept as the
  note. The strict `approve <item-id>` grammar is unchanged and takes
  precedence when both could apply; a bare word outside a reply, or a
  reply to a message without an item id, resolves nothing. Proposal
  messages state the reply format prominently (8 new tests).
- **core:** contracts CLI. `python3 -m core approve|reject|status
  <item-path>` is now the only supported write path for item status and
  approvals - it prints the resulting status line and refuses an illegal
  transition with a nonzero exit and the reason on stderr. Decisions
  accept `--note`; telegram reply reasons persist as notes too. Every
  skill that records decisions or status now invokes the CLI and carries
  the rule: never edit brain frontmatter directly (9 new tests).
- **core:** approval-record lint. `rebuild_queue` flags any approvals
  entry missing its `decision` field - the fingerprint of a hand-edit -
  as a `MALFORMED-APPROVAL` row in the queue.
- **core:** `partially-applied` is a first-class state (ADR-0007). When
  some changes in an approved proposal land and the rest hit a permission
  or capability wall, the honest state now exists: approved ->
  partially-applied (with a note naming exactly what a human must
  finish), then -> applied or -> failed, and nothing else touches it. The
  queue shows PARTIAL rows with the note inline; the outcome record lists
  done vs pending (6 new tests).
- **runtime:** headless resilience. `run-routine.sh` pins the model with
  `--model "${ANTHROPIC_MODEL:-sonnet}"` (the env override reaches
  sub-agents unreliably); `plugin/docs/routines.md` documents the known
  sub-agent dispatch limitation and its inline fallback, watching a live
  run by tailing the run report, `--output-format stream-json`, and
  recovering a skill from its on-disk body. The four long skills append a
  UTC-stamped progress marker to the run report at each stage boundary.
- **docs:** WordPress capability matrix. Action vs minimum role in
  `plugin/docs/credentials/wordpress.md`: public reads need no role,
  REST writes need Editor plus an Application Password, and
  Administrator-only steps (SEO-plugin cache purges, plugin settings) are
  never requested - they report pending-human and end the proposal
  partially-applied. The setup scorecard's WordPress row now names the
  detected role and what it cannot do.

## [0.1.9] - 2026-07-19

Cost, dry-run, and IndexNow (v0.2 wave 4) - see ROADMAP.md.

- **runtime:** cost transparency per routine run. `run-routine.sh` now
  runs `claude -p` with `--output-format json`, times the run, recovers
  the assistant text and any usage fields with python3 only (no jq), and
  appends one row per run - date, routine, duration seconds,
  tokens-or-unavailable - to a monthly ledger at
  `~/.config/organic-os/cost-ledger-YYYYMM.tsv`, plus a cost line in the
  routine log. Usage parsing is defensive across CLI versions and says
  "usage unavailable in this CLI version" rather than guessing. The
  Monday report closes its "What moved" section with a one-line cost
  summary when the ledger exists and never invents numbers when it does
  not; `plugin/docs/routines.md` documents what the ledger can and cannot
  capture per runtime (subscription runtimes: tokens counted, not billed
  per token; CI: tokens are money; runs that bypass the wrapper leave no
  row).
- **onsite:** dry-run mode for apply. `WPClient(dry_run=True)` records
  every mutating call (update_post, update_rankmath, create_post,
  rollback) in `dry_run_log` - method, post id, fields - and returns a
  realistic-shaped response marked `dry_run: True` without touching the
  session; reads behave normally (4 new tests). With
  `onsite: {dry_run: true}` in site-profile.yaml (additive, schema stays
  1), `onsite-apply` and `onsite-publish` run the full gated flow -
  `require_approved` still enforced before the dry-run write, so a dry
  run rehearses the real path - write nothing, leave the item's status
  untouched, and mark the outcome record dry-run with every write that
  would have happened. `scripts/verify-gates.sh` gains probe 7: dry-run
  does not relax the gate, and an approved dry-run apply makes zero
  session calls.
- **hoo:** IndexNow and Bing submission. `plugin/lib/hoo/indexnow.py`
  (5 new tests): `gen_key` (32-char hex), `key_file_content`, and
  `submit` - one stdlib POST to `api.indexnow.org` with
  `{host, key, keyLocation, urlList}` through an injectable transport,
  returning `{status, submitted}` and never raising on a non-200. With
  `indexnow: {enabled: true, key: ...}` in site-profile.yaml (additive),
  apply and publish submit each successfully verified changed URL and
  record the status in the outcome; publish only submits posts that
  actually went live. Setup's connector wizard offers enablement
  verify-not-record style: generate the key, place `<key>.txt` at the
  site root, verify by fetch, then enable. `plugin/docs/connectors.md`
  adds the capability row and an honest Bing Webmaster paragraph - portal
  verification is manual, IndexNow covers the submission path, no API
  integration claimed.

## [0.1.8] - 2026-07-19

Baseline and audit-first setup (v0.2 wave 3) - see ROADMAP.md.

- **setup:** AI-visibility baseline - a new optional step, offered in full
  setup after connectors/credentials and before the postflight scorecard
  (~5 minutes, always skippable). Samples up to 8 seed keywords and 2
  competitors against whatever AI answer surfaces this session can reach
  via WebSearch/WebFetch, records per query whether the brand and each
  competitor appear and who is actually cited, and writes
  `runs/<date>-ai-baseline/REPORT.md`: a per-query table plus three
  summary numbers (brand mention rate, competitor mention rate,
  share-of-voice ratio), each labeled with an explicit sampling caveat -
  this method samples reachable engines, it does not measure every engine.
  Appends one signal with the headline numbers and a 90-day falsifiability
  line (re-run monthly via `/organic-os:citations`; no movement in mention
  rate 90 days after shipped content work means the content strategy
  hypothesis is wrong, not the baseline). Degrades to "baseline deferred"
  with no web access rather than fabricating a report.
- **hoo-citation-tracker:** when a baseline report exists, later runs
  compare against it and report movement, not just this run's absolutes.
- **setup:** audit-and-propose is now the default first-run flow, for both
  quick-start and full setup. Setup asks for the site URL first, then
  audits before asking anything else - fetches the homepage and sitemap,
  detects WordPress/Yoast/RankMath from markup and sitemap shape, reads
  3-5 representative pages, and proposes brand voice descriptors, audience
  segments, 5-9 seed keywords, 3-5 content-SERP competitors (sites
  competing for the same queries, not necessarily business rivals - the
  proposal says so), and target geos, grounded in what was actually read.
  The proposal is presented as a table for approval: accept all, edit
  specific rows, or answer manually instead. Quick-start collapses to 3
  questions (URL, approval channel, confirm) and now seeds keywords,
  competitors, and voice from the audit instead of leaving them blank.
  Full setup keeps every question the audit genuinely cannot answer -
  operator knowledge, connectors, Google Ads, WordPress, approval channel,
  runtime, brain mode - unchanged downstream of the new proposal step.
  Degrades to the old blind-question defaults when the site cannot be
  fetched.
- **docs:** `plugin/docs/getting-started.md`'s setup walkthrough and
  README's zero-credential quickstart now describe the audit-first flow.

## [0.1.7] - 2026-07-19

Observe-side detectors (v0.2 wave 2) - see ROADMAP.md.

- **hoo:** cannibalization detector, added to `hoo-weekly` directly after
  the striking-distance section and fed by the same 28-day GSC query
  pull. Flags queries split across two or more landing pages with no
  stable majority (guideline: the second page carries 20% or more of the
  query's impressions), writes one P2 signal per case for the top 3 by
  total impressions - query, both pages, positions, impression split, and
  a falsifiability check - and calls out the linkage when a page also
  shows up in the striking-distance list, since cannibalization is often
  the actual blocker behind a stuck position. Opens at most one gated
  consolidation proposal per run (canonical, 301, or content merge),
  never applied automatically. Degrades to a one-line REPORT.md note when
  GSC is unreachable.
- **hoo:** content decay detection, also in `hoo-weekly`. Compares each
  page's last-28-days GSC clicks against the same page's 28-day window
  90 days back, flags a 30%+ decline above a 50-click noise floor on the
  older window, and writes P2 signals for the top 3 pages by absolute
  click loss with a likely-cause read on position-vs-CTR movement
  (position fell means a ranking problem; position held but CTR fell
  points at a SERP feature or title/meta staleness). At most one gated
  refresh brief per run, created as a `content-brief` item so it moves
  through the existing brief lifecycle into content-engine rather than
  being applied directly. Same GSC-unavailable degradation.
- **core + onsite:** site drift watch. `plugin/lib/onsite/drift.py`
  (`snapshot_pages`, `baseline_path`, `save_baseline`, `compare`, 8 new
  tests) snapshots title, RankMath title/description, canonical, slug,
  status, and JSON-LD presence per tracked page via the existing
  `wp.get_post()` getter, and diffs against a stored baseline at
  `drift/baseline.json` (atomic-written through
  `core.contracts._atomic_write`; additive, `schema_version` stays 1).
  `hoo-daily` gains a WP-only "Drift watch" section: establishes the
  baseline on first run against a capped tracked-page set (pages from
  `outcomes/`/`proposals/` plus the homepage), then on later runs writes
  one P1 signal per changed field before refreshing the baseline, so a
  given drift is reported exactly once. `onsite-apply`'s verify step
  refreshes the baseline for a page it just changed, so an approved
  change is never reported back as drift on the next daily run. Skips
  silently with no WordPress connector.

## [0.1.6] - 2026-07-19

Setup verification and runtime awareness (v0.2 wave 1, field-tested) -
see ROADMAP.md.

- **core:** `contracts.record_connector()` - the `connectors:` block in
  `site-profile.yaml` now stores `{status, context, checked}` per
  connector, never a bare string or boolean. `status` is `verified`
  (a live probe query succeeded, not just tool presence), `unavailable`,
  or `declined`; `context` records where the probe actually ran
  (`local-cli`, `cowork-cloud`, `ci`) so a connector reachable from the
  setup session is never recorded as available for a runtime that cannot
  reach it. Upgrades pre-wave-1 bare-string entries in place, one
  connector at a time, without touching siblings.
- **core:** `contracts.write_scorecard()` - writes a pass/degraded/fail
  table with the exact fix command per non-pass row to
  `runs/<date>-setup-scorecard/REPORT.md`.
- **setup:** rewritten as v3 - runtime-aware, verify-not-record. A new
  "where am I, where will routines run" step catches a setup/runtime
  environment mismatch (e.g. a cloud Cowork session onboarding a local
  runtime) before scaffolding anything, and bans running git through a
  device bridge. The old passive connector probe is replaced by a
  connector wizard: GA4/GSC (the heartbeat pair) then Notion/Slack/Canva,
  each probed and then live-verified (GSC list-sites, a GA4 7-day
  sessions pull, etc.) before ever recording `verified`, with a guided
  connect, a wait-and-reprobe option, or an honest `declined` on
  absence. Credentials move to a one-secret-at-a-time flow, precisely
  named and always offering a paste-into-terminal alternative. Setup now
  ends on a mandatory postflight scorecard - brain scaffold, git push,
  registry readability in runtime context, WordPress REST, approval-
  channel delivery, each connector's live result, headless auth + model
  resolution, and (local runtime) one real scheduled run proven by
  commit hash - and states "configured" and "verified working" as
  different claims.
- **start:** returning-user status now shows the latest postflight
  scorecard's summary line, read-only.
- **hoo:** `hoo-daily` escalates after 3 consecutive no-data days (GSC
  and GA4 both unreachable) with one send_item-style nudge through the
  configured approval channel, not an approval item - naming the exact
  connect fix. The nudge is marked inside that day's own signal file (no
  new state file) and is suppressed if one was already sent in the last
  7 days.
- **docs:** `plugin/docs/connectors.md` documents the new connector
  record shape and the no-data escalation behavior.

## [0.1.5] - 2026-07-19

- **onboarding:** user-facing docs now ship inside `plugin/docs/` so
  marketplace and synced installs (which contain only the plugin
  directory) actually have them - `$CLAUDE_PLUGIN_ROOT/../docs` never
  resolved for those installs.
- **runtime:** `plugin/runtime/` - a wrapper script (`run-routine.sh`)
  and three `launchd` plist templates (daily, weekly, monthly) for the
  local-schedule recipe.
- **docs:** `plugin/docs/routines.md` rewritten from a first real
  local-runtime install, covering five failure modes the original
  version did not warn about: the `claude setup-token` requirement for
  headless auth, passing a command's template body instead of a slash
  string (slash-command expansion is not reliable headless), model-404
  recovery when a CLI model alias resolves to a retired model, and what
  the `claude-scheduled` runtime cannot reach (personal GitHub auth,
  local env-file secrets, desktop-bridged connectors).
- **core:** `registry.path_warnings()` - the TCC brain-path guard is now
  enforced in code, not just documented: warns when a local runtime's
  brain path sits under a macOS TCC-protected folder (Documents, Desktop,
  Downloads) or inside a plugin-managed directory, and `/organic-os:setup`
  re-asks with a safe default when it fires.
- **refactor:** the bridge mu-plugin (`organic-os-bridge.php`) is a
  product asset, not demo infra - relocated to `plugin/wordpress/` so it
  ships with the plugin. The rest of `playground/` (compose file, Caddy
  snippet, php.ini tweak, deploy runbook) is demo-deployment infra, not a
  marketplace-user concern, and is removed from the package.
- **docs:** `plugin/docs/credentials/wordpress.md` gains the direct
  wp-admin URL for the Application Password screen, a one-line sandbox
  pointer (any local WordPress works), and an explicit Editor-not-
  Administrator note; `plugin/docs/approval-channels.md` explains why the
  first message to your Telegram bot has to happen before the first poll.
- **docs:** ROADMAP gains a new v0.2 sub-block, "Setup verification and
  runtime awareness," covering five gaps this wave's field testing
  surfaced (postflight scorecard, runtime-location awareness,
  audit-and-propose interview, connector wizard with live verification,
  one-secret-at-a-time credentials flow) - see ROADMAP.md.

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
