# organic-os - design spec

- **Date:** 2026-07-18
- **Status:** approved-pending-review (Shivaa to review this document)
- **Owner:** Shivaa Tripathi (shalintripathi)
- **Repo:** `shalintripathi/organic-os` (public at ship time)

## 1. What this is

organic-os is a single installable Claude plugin that gives any marketer an agentic organic-growth team: it watches a website's search and AI-answer-engine performance, learns day by day, proposes work (content briefs, on-page fixes, keyword plays), gets human approval through the channel the user chose, applies approved changes to WordPress, verifies them, and measures the outcome - feeding what it learned back into its own playbook.

Three principles carried through every section:

1. **One install, separate insides.** Users install one plugin. Internally, three modules (head-of-organic, onsite-optimizer, content-engine) are cleanly bounded and talk only through file contracts, so a change to one never breaks another.
2. **Bring your own everything.** Credentials, connectors, channels, and runtimes are chosen by the installer at setup. Nothing personal, employer-specific, or secret ships in the repo. Every capability degrades gracefully when its credential or connector is absent.
3. **Memory that compounds.** A per-site git repo is the brain: signals, a curated skillbook, ADRs, and approval history. This is the differentiator - existing SEO plugins audit a moment in time; organic-os runs a loop that learns.

### Non-goals (v1)

- No SERP/autocomplete scraping, ever (Google deployed SearchGuard and sued SerpApi in Dec 2025; we do not transfer that risk to users).
- No hosted SaaS, no telemetry, no accounts. The "cloud" is the user's own Claude subscription or API key.
- No support for CMSs other than WordPress in onsite-optimizer v1 (the audit half works on any site; the write half is WordPress-only).
- No bundled paid-API keys (DataForSEO, Keywords Everywhere are documented BYO adapters only).

## 2. Distribution and packaging

- The GitHub repo `shalintripathi/organic-os` uses the standard Claude plugin marketplace format with exactly one plugin listed. Install UX:
  ```
  /plugin marketplace add shalintripathi/organic-os
  /plugin install organic-os@organic-os
  ```
- `.claude-plugin/marketplace.json` at repo root lists `./plugin` as the single plugin source. `plugin/.claude-plugin/plugin.json` carries name, version (semver, starts 0.1.0), description.
- **Cross-platform rule:** everything must run on Claude Code CLI *and* Claude Cowork. Therefore: skills + agents + slash commands + plain scripts invoked via Bash only. **No stdio MCP servers** (CLI-only). External SaaS reached through the user's own connectors (GA4, GSC, Notion, Slack, Canva) which exist on both platforms. Hooks limited to SessionStart (degrade silently where unsupported).
- Repo layout:
  ```
  organic-os/
    .claude-plugin/marketplace.json
    plugin/
      .claude-plugin/plugin.json
      skills/          # flat dirs, names prefixed by module: hoo-*, onsite-*, ce-*, plus setup/
      agents/          # 8 head-of-organic specialists + onsite auditor + content pipeline agents
      commands/        # /organic-os:* slash commands
      lib/             # module-scoped scripts: lib/hoo/, lib/onsite/, lib/ce/, lib/core/
      hooks/           # SessionStart state dashboard (optional, degrades)
    docs/
      getting-started.md
      credentials/google-ads-token.md   # verified 10-step guide, 2026-current
      credentials/google-cloud-gsc-ga4.md
      credentials/wordpress.md          # app passwords, RankMath bridge, mu-plugin
      approval-channels.md
      routines.md                       # the three runtimes, costs, setup per runtime
      evidence.md                       # honest AEO/GEO evidence ranking
      site-repo-contract.md             # the file contracts (section 4)
    docs/adr/                           # ADRs for organic-os itself, MADR-lite
    docs/specs/                         # this file
    playground/                         # reference WordPress deployment (compose + Caddy + runbook)
    README.md, LICENSE (MIT), CHANGELOG.md
  ```
- Module boundary enforcement: a `lib/core/` contract layer owns all reads/writes of the site repo. Modules import core, never each other. CI check greps for cross-module imports.

## 3. Internal architecture

```
                       ┌─────────────────────────────┐
                       │   site repo (the brain)      │
                       │  profile, signals, skillbook,│
                       │  briefs, approvals, ADRs     │
                       └──────▲──────────┬────────────┘
              reads/writes via lib/core contracts only
        ┌─────────────────┼──────────────┼──────────────────┐
        │                 │              │                  │
  head-of-organic   onsite-optimizer   content-engine   routines (any runtime)
  observe + decide  audit + mutate WP  draft + assets   scheduled invocations
  (GA4, GSC, Ads,   (REST + app pwd,   (briefs in,      of the same skills
  citations,        RankMath bridge,   posts out,
  competitors)      verify, measure)   Canva step)
```

- **head-of-organic** observes (analytics, rankings, AI citations, competitors, keywords), decides (signals with falsifiable reasoning), and emits work items (briefs, fix proposals) into the site repo.
- **onsite-optimizer** consumes approved fix proposals and publish requests, mutates WordPress, verifies the rendered result, and writes outcome records.
- **content-engine** consumes approved content briefs, produces publish-ready drafts (with an optional Canva image step), and hands them to onsite-optimizer for publishing.
- Each module is fully usable standalone: head-of-organic without a WordPress site is an analytics/strategy tool; content-engine without head-of-organic accepts manual briefs; onsite-optimizer without the others is an on-page audit/fix tool.

## 4. The site repo (the brain)

One repo (or plain folder, see setup modes) per site. Default name `organic-hq-<domain-slug>`, private.

```
organic-hq-<site>/
  site-profile.yaml        # identity: url, sitemap, brand voice rules, competitors, geos,
                           # connectors available, approval channel, runtime mode, WP endpoint
  skillbook.md             # curated playbook. Entries: S-014 [evidence: strong|moderate|anecdotal]
                           # [helpful: n, harmful: n, last-confirmed: date] one-line lesson + source
  signals/YYYY-MM-DD.md    # daily raw observations, append-only, never edited
  reflections/YYYY-Www.md  # weekly reflector output: proposed skillbook deltas by entry ID
  decisions/NNNN-*.md      # ADRs, MADR-lite + Agent Context section (who decided: agent|human,
                           # on what evidence). Never edited, only superseded.
  briefs/                  # content briefs emitted by head-of-organic, one file each, with
                           # status frontmatter: proposed → approved → drafted → published → measured
  proposals/               # on-page fix proposals (same status lifecycle)
  approvals/queue.md       # pending approvals index; approval recorded by channel reply or PR merge
  runs/YYYYMMDD-<skill>/   # timestamped run outputs: numbered raw files + REPORT.md
  keywords/tracking.yaml   # tracked keyword set + per-keyword history
  outcomes/                # post-change measurements (GSC deltas at day 7/28) linked to proposals
```

Memory discipline (from ACE / Reflexion / Voyager research):

- **Generator** (daily routines) appends signals; never touches skillbook.
- **Reflector** (weekly routine) reads the week's signals + outcomes, proposes itemized deltas referencing skillbook entry IDs.
- **Curator** applies deltas as append/edit/deprecate operations on specific entries. Full-file rewrites are forbidden (context collapse); summarizing to shorten is forbidden (brevity bias). Curator merge is human-gated by default; the user can promote it to autonomous after trust builds.
- Every skillbook entry carries an evidence tag and source. ADRs record strategy-level decisions; the skillbook records tactical lessons.

## 5. Approval protocol

- **Rule: analysis is free; mutation is gated.** Mutations = publishing/editing WordPress content or meta, changing tracked-keyword strategy budgets, writing the skillbook (curator), creating Notion/task-board entries marked as commitments.
- Proposals are files in the site repo with status frontmatter. `approvals/queue.md` indexes everything pending.
- **Channel adapters** (chosen at setup, no privileged default; in-session used when nothing is configured):
  - *in-session*: AskUserQuestion right now.
  - *telegram*: BYO bot token; adapter posts the proposal summary; a later run polls `getUpdates` for reply/reaction before applying. Works from every runtime via plain HTTPS.
  - *slack* / *email (Gmail)*: post/notify via the user's connector; approval read back at next run or given in-session.
  - *pr-merge* (git-native): proposal arrives as a PR against the site repo; merging is approving. Best audit trail; pairs naturally with the CI runtime.
- A mutation executes only when its proposal file shows `status: approved` with an approval record (who, when, channel). Scheduled runs never block waiting; they queue, notify, exit.

## 6. Routines and runtimes (execution-agnostic)

Cadence definitions live in the site repo (`site-profile.yaml routines:` block): daily signal pull, weekly reflection + keyword refresh, monthly deep audit, per-publish measurement at day 7/28. The *definitions* are declarative; the *runtime* is the installer's choice at setup:

| Runtime | How it runs | Cost model | Best for |
|---|---|---|---|
| claude.ai scheduled tasks (recommended default) | Anthropic-hosted scheduled agent clones the site repo, runs the skill, pushes, notifies | Included in the user's Claude subscription usage; no API key, no infra | Marketers; zero setup |
| Local schedule | Claude Code on the user's machine via OS scheduler / `/loop` | Subscription usage; machine must be on | Privacy-first users, no-GitHub mode |
| CI (GitHub Actions) | Headless `claude -p` / Agent SDK job on a schedule | API key, pay per token | Teams, full cloud-native |
| Manual | User runs `/organic-os:daily` etc. | Subscription | Trying it out |

The setup skill asks "where should routines run?" and emits the exact configuration for the chosen runtime (schedule instructions, crontab lines, or a ready workflow YAML). Skills are runtime-agnostic; they detect what is reachable (connectors, SSH, local repo vs clone) and degrade per the capability matrix in `docs/routines.md`.

## 7. Module: head-of-organic

- **`/organic-os:setup`** (shared onboarding, owned by core, populates all modules): interviews the user - site URL, sitemap, brand name + voice rulebook (defaults offered, all editable), competitors, target geos/languages, **target keywords/segments/ICP**, **operator knowledge** ("what do you already know works in your niche" - seeded into the skillbook as `evidence: anecdotal` entries so the loop starts warm), which connectors exist (probes GA4/GSC/Notion/Slack/Canva), Google Ads credential status, WordPress endpoint + app password (optional, connect-time only), approval channel, runtime, brain mode (git repo vs local folder). Writes `site-profile.yaml`, scaffolds the site repo, registers routines. The plugin has no WordPress dependency until the user connects one.
- **Skills:** `hoo-orchestrator` (fan-out to specialists, synthesize, emit signals/briefs), `hoo-daily` (signal pull: GSC + GA4 + tracked keywords + citation spot-checks), `hoo-weekly` (health check + reflector), `hoo-monthly-audit` (deep technical + content + authority audit), `hoo-citation-tracker` (AI answer-engine visibility: mention rate, share of voice vs competitors, citation rate - query set from site-profile), `hoo-competitor-intel` (content gaps, new pages, keyword overlap), `hoo-keyword-intel` (below), `hoo-reflector` (weekly deltas), plus `hoo-task-board` (Notion mirror when connector present, local markdown otherwise).
- **Agents (8, generalized):** technical-seo-auditor, content-strategy-architect, aeo-geo-optimizer, entity-schema-engineer, serp-ai-monitor, competitive-intel-analyst, link-authority-strategist, analytics-reporting-chief. All read site-profile; none contain a brand name.
- **Signal quality bar** (borrowed from claude-seo, credited): every signal carries observation, dependencies, a falsifiability check ("how would we know this was wrong"), and a leading indicator.

### hoo-keyword-intel (Google Ads)

Tiered by the user's access level, detected at runtime:

1. **Basic/Standard token:** full planner via `GenerateKeywordIdeas` (keyword/url/site seeds) and `GenerateKeywordHistoricalMetrics` (batches of 200-500, 1.1 s spacing for the 1 QPS planning limit, 30-day cache because Google refreshes monthly). Competitor gap = own domain vs competitor domain as `site_seed`, diff the sets, attach metrics. Forecasts via `GenerateKeywordForecastMetrics` for shortlists.
2. **Explorer/pending:** own-account GAQL (search-term mining, quality score, coverage) + "apply for Basic" guidance. Planner calls are blocked at this tier and the skill says so honestly.
3. **No token:** GSC query mining (16 months, 25k rows/request).
4. **Manual:** CSV import for Keyword Planner UI exports and Auction Insights CSVs (the API allowlist for auction insights is closed; the UI export is the legitimate path).

Implementation: `lib/hoo/google_ads/*.py` using google-ads-python, config via env vars (`GOOGLE_ADS_DEVELOPER_TOKEN` etc.) or `~/.config/organic-os/google-ads.yaml`, prompted at setup, never committed. `docs/credentials/google-ads-token.md` ships the verified 2026 guide (manager account → API Center token → Cloud project → OAuth desktop client → loopback-flow refresh token → apply for Basic; notes the current review backlog and Explorer limitations).

## 8. Module: onsite-optimizer

- **Write path (decided):** WordPress REST API + Application Passwords over HTTPS. SEO meta via RankMath keys (`rank_math_title`, `rank_math_description`, `rank_math_canonical_url`, `rank_math_focus_keyword`) registered for REST by the Devora rank-math-api-manager plugin or our bundled 10-line mu-plugin (both shipped in `playground/wp-extras/`). Schema via a dedicated `agent_jsonld` meta field rendered into `wp_head` by the same mu-plugin. **Verification:** after every apply, read back RankMath `getHead` (or the live page) and confirm the rendered head matches the proposal; write the diff to the outcome record.
- Yoast sites: read-only audit supported (`yoast_head_json`); writes require RankMath (documented; the setup skill detects which SEO plugin is installed).
- **WP-CLI over SSH** is the optional admin path (bulk ops, plugin/option management, cache/cron) when the user's environment has SSH; skills detect availability.
- **WordPress mcp-adapter:** installed on the playground as an experiment, explicitly not load-bearing (core ships read-only abilities today). Revisit at its 1.0.
- **Skills:** `onsite-audit` (page + site-level on-page audit, any URL, no credentials needed), `onsite-propose` (turn signals/audit findings into proposal files), `onsite-apply` (gated executor with verify + rollback: previous values stored in the outcome record for one-command revert), `onsite-publish` (gated publisher for content-engine drafts: create post, set RankMath fields, schema, featured image), `onsite-measure` (day-7/28 GSC pulls per change, writes outcomes/).

## 9. Module: content-engine (generalized v3)

- The 8-stage pipeline (research → draft → brand compliance → SEO/authority → editorial QA → compliance check → production → editor-in-chief) rebuilt brand-agnostic: voice rules, banned phrases, TL;DR capsule style, citation requirements all come from `site-profile.yaml` (shipped defaults follow the evidence: answer capsule up front, statistics + quotable lines + cited sources, extractable structure).
- Input: an approved brief from `briefs/`; output: a publish-ready draft (markdown + meta + schema suggestion) written back to the brief's folder, then handed to `onsite-publish` (gated).
- **`ce-image` skill:** featured image / social card via the user's Canva connector when authorized; degrades to writing an image brief file (prompt + dimensions + alt text) the user can execute anywhere.

## 10. Playground (the living demo) - built in a parallel session

The playground exists only to demonstrate the plugin on a real WordPress site. It is built by a **separate WordPress session** working from this section; the organic-os build does not block on it and only needs its endpoint + application password at demo time (step 8 of §14). Reference copies of the compose file, mu-plugin, and runbook land in `playground/` in this repo; the live deployment and its infra commits belong to the hq repo per personal-infra conventions.

- On `hq-fsn1-01` per the locked personal-infra stack; first Docker workload on the box.
- `docker-compose.yml` (in `playground/`): `mariadb:11.4` (innodb_buffer_pool 256M, performance_schema off, mem_limit 512m) + `wordpress:php8.3-apache` (mem_limit 768m, loopback port 8081, `WP_HOME`/`WP_SITEURL` pinned to `https://playground.shivaatripathi.com`, `DISABLE_WP_CRON`), `wp-cli` service under `profiles: [cli]`, uploads.ini 64M. Host crontab runs `wp cron event run --due-now` every 15 min. Total budget ~1.2 GB, leaving 2.5 GB+ headroom.
- Caddy vhost `playground.shivaatripathi.com → 127.0.0.1:8081` (Caddy sets X-Forwarded-Proto; the official image consumes it - no redirect loops behind Cloudflare Full). Cloudflare A record, proxied.
- WordPress setup: default theme (Twenty Twenty-Five), RankMath free, the REST bridge + `agent_jsonld` mu-plugin, dedicated `organic-agent` Editor user with an Application Password (stored in `~/.config/organic-os/`, never in git), 4-6 seeded posts so agents have material, GSC verification + sitemap submit, GA4 property, mcp-adapter installed as the experiment.
- The playground is where onsite-optimizer runs with gates set to Telegram + PR-merge (Shivaa's own channel choice) - the public showcase of the full loop.

## 11. Notion dashboard (optional mirror)

- `hoo-task-board` mirrors the site repo's queue/briefs/outcomes into a Notion workspace: Task Board, Content Calendar, Keyword Tracker, Decision Log databases. One-way mirror v1 (repo → Notion); approvals stay in the approval protocol.
- Shivaa's instance is created today via the Notion connector. Public users get it if their Notion connector is authorized; otherwise the local markdown board is the dashboard.

## 12. Credentials and security

- Zero secrets in the repo; `.gitignore` and a CI secret-scan gate enforce it.
- Prompted at setup, stored per platform convention: plugin userConfig sensitive fields (keychain-backed) where supported, else `~/.config/organic-os/` files chmod 600, else env vars. Site repo stores only *references* (which credentials exist), never values.
- The published repo carries a SECURITY.md: what the plugin touches, what it never does (no scraping, no telemetry, no outbound calls except user-configured APIs), and the mutation-gate guarantee.
- Site repos may contain business-sensitive strategy; default-private is documented loudly.

## 13. Publishing plan

- MIT license. README leads with the loop (observe → decide → approve → apply → verify → learn), an honest "what this is not" (not another point-in-time auditor), install for both Claude Code and Cowork, a 10-minute quickstart against any site (audit-only needs zero credentials).
- **Credits section (prominent):** AgriciDaniel/claude-seo, seranking/seo-skills, WordPress/mcp-adapter + Automattic remote proxy, Devora rank-math-api-manager, ACE paper, Reflexion, Voyager, Dynamic Cheatsheet, MADR, mcp-gsc, DataForSEO MCP, firecrawl llmstxt-generator, oneglanse.
- **`docs/evidence.md`:** the ranked evidence table (server-rendering, statistics/quotes/citations, Bing indexing, freshness, extractable structure = strong; Reddit presence, query fan-out, listings = moderate; llms.txt and schema-for-AI-citations = weak/contradicted, shipped as options with honest labels). This honesty is a stated feature.
- Launch assets (post-ship, not gating): LinkedIn essay + shivaatripathi.com essay via the existing content pipeline.

## 14. Build order (today)

1. Scaffold repo + marketplace/plugin manifests + core contracts (`lib/core`, site-repo scaffolder) + ADRs 0001-0006.
2. *(parallel WordPress session, not this build)* Playground live per §10: DNS + compose on hq + Caddy + WordPress + RankMath + bridge/mu-plugin + agent user + seed posts; GSC + GA4 wired. This build consumes only the resulting endpoint + credentials.
3. head-of-organic module: setup interview, orchestrator, daily/weekly skills, keyword-intel (all tiers incl. Google Ads scripts), citation tracker, reflector; 8 agents.
4. onsite-optimizer module: audit, propose, apply (with verify + rollback), publish, measure; approval adapters (in-session, telegram, pr-merge; slack/email as thin adapters).
5. content-engine module: generalized pipeline + ce-image.
6. Shivaa's instance: site repo `organic-hq-playground` created, profile filled, Telegram bot + PR gates, routines registered on claude.ai schedule; Notion dashboard created and mirrored.
7. Docs (getting-started, credentials guides, routines, evidence, site-repo contract), README, SECURITY, LICENSE; secret-scan + audit script.
8. End-to-end demo run: signal → brief → approval (Telegram) → draft → publish (gated) → verify → measure scheduled; screenshots/records into README.
9. Publish: repo public, install tested from a clean environment (`/plugin marketplace add`), tag v0.1.0.

## 15. Acceptance criteria

- [ ] `/plugin marketplace add shalintripathi/organic-os` + install works from a clean Claude Code; skills load on Cowork.
- [ ] Zero personal/employer data in the repo (audited: no Exotel, no client names, no credentials, no phone).
- [ ] Setup completes against a fresh site with *no* credentials (audit-only mode) and with full credentials.
- [ ] Mutation without an approval record is impossible by construction (executor checks status, refuses otherwise).
- [ ] keyword-intel returns useful output at every tier (Basic, Explorer, GSC-only, CSV).
- [ ] Playground: full loop demonstrated once end-to-end with real approval via Telegram.
- [ ] Every skillbook write goes through the curator; signals are append-only.
- [ ] README credits + evidence.md ship; no unverifiable ranking claims anywhere.
- [ ] No em-dashes in any shipped copy; voice rules per site-profile defaults.

## 16. Risks and open items

- **Google Ads Basic approval is backlogged (2026)** - Shivaa's own token may stay at Explorer for weeks; demo uses GSC tier + test seeds until approved. Documented in the guide.
- **Connector availability in scheduled cloud runs** varies (OAuth-based connectors generally present; verify GA4/GSC in a real scheduled run early).
- **RankMath bridge dependency:** Devora plugin is maintained but third-party; our bundled mu-plugin is the fallback we control.
- **Cowork parity:** hooks and some UX degrade on Cowork; acceptance test covers skill-level parity only.
- **Scope risk for one day:** modules 3-5 are large. Mitigation: the file contracts are frozen first (step 1), so modules can be built by parallel agents and land independently; anything unfinished ships as a follow-up release without breaking installs.
