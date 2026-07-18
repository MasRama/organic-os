# organic-os

An agentic organic-growth operating system for any website, built as a
single Claude plugin. The loop is the product: **observe -> decide ->
approve -> apply -> verify -> learn.** It watches a site's search and
AI-answer-engine performance, proposes work, waits for a human decision
through whichever channel you chose, applies approved changes to
WordPress, verifies the change actually took effect, measures the outcome,
and writes what it learned back into a per-site playbook that compounds
over time.

## Why another SEO thing

Point-in-time audit tools already exist and are good - [claude-seo](https://github.com/AgriciDaniel/claude-seo)
(11.6k+ stars) runs a thorough technical/content/schema/GEO audit against a
site in one pass, and organic-os's own onsite audit borrows from its
signal-quality bar directly (credited below). What none of the point-in-time
tools do is run every day and remember what happened last time. organic-os
is the layer underneath that: daily signals, gated execution on your own
WordPress site, outcome measurement against what you actually shipped, and
a skillbook your site earns entry by entry as changes get confirmed to work
or not.

## What you get

Three bounded modules, one install:

| Module | Does |
|---|---|
| **head-of-organic** | Observes (GA4, GSC, Google Ads keyword intel, AI-citation tracking, competitor content) and decides: emits signals and work items with falsifiable reasoning behind each one |
| **onsite-optimizer** | Audits any public page with no credentials; with a WordPress connection, applies approved on-page fixes and publishes approved drafts, always verified and rollback-capable |
| **content-engine** | Turns an approved brief into a publish-ready draft - research, brand-voice compliance, SEO/authority pass, editorial QA - with an optional featured-image step |

```
                       +-----------------------------+
                       |   site repo (the brain)      |
                       |  profile, signals, skillbook,|
                       |  briefs, approvals, ADRs     |
                       +------^----------+------------+
              reads/writes via lib/core contracts only
        +-----------------+--------------+------------------+
        |                 |              |                  |
  head-of-organic   onsite-optimizer   content-engine   routines (any runtime)
  observe + decide  audit + mutate WP  draft + assets   scheduled invocations
  (GA4, GSC, Ads,   (REST + app pwd,   (brief in,       of the same skills
  citations,        RankMath bridge,    draft + assets
  competitors)       verify, measure)   out)
```

Modules talk only through the site repo's file contracts, enforced by a
`lib/core` layer that owns every read and write - a change to one module
never breaks another, and each module is fully usable on its own:
head-of-organic without WordPress is still an analytics/strategy tool,
content-engine without head-of-organic accepts manually written briefs,
onsite-optimizer without the others is a standalone on-page audit/fix tool.

## Install

```
/plugin marketplace add shalintripathi/organic-os
/plugin install organic-os@organic-os
```

Works identically on Claude Code CLI and Claude Cowork - there is nothing
to host. The plugin is skills, agents, slash commands, and plain scripts
invoked over Bash; no server process, no stdio MCP server, no database.

## Quickstart in 10 minutes

Zero credentials required to see it work:

1. `/organic-os:setup` - run the interview in analysis mode (skip
   WordPress, skip Google Ads, leave connectors unconfigured).
2. `/organic-os:onsite-audit https://yoursite.com` - a read-only on-page
   audit against a live URL, no login needed.
3. Run a full orchestrator sweep and let it emit signals and candidate
   work items from whatever public data it can reach.
4. Open `approvals/queue.md` in the brain repo it scaffolded. That is your
   first queue of proposed work - briefs and fix proposals sitting in
   `status: proposed`, waiting on a human decision. Nothing has touched
   your site yet.

Full walkthrough: `docs/getting-started.md`.

## Credentials (all optional, all yours)

Every capability degrades gracefully when its credential is absent, and
nothing is required to start. The upgrade ladder, one rung at a time:

- Add GSC/GA4 -> real ranking and traffic signals instead of public-page
  guesses. `docs/credentials/gsc-ga4.md`
- Add WordPress -> gated writes and publishing. `docs/credentials/wordpress.md`
- Add Google Ads -> full keyword planner data at Basic tier, honest
  degraded modes below it. `docs/credentials/google-ads-token.md`
- Add a channel -> approvals that reach you outside a live session.
  `docs/approval-channels.md`
- Schedule routines -> move from manual to daily/weekly/monthly.
  `docs/routines.md`

The promise underneath all of it: no secrets in any repo (env files only,
chmod 600), no telemetry, no third-party call organic-os did not make
because you configured it to.

## Human gates

Analysis is free. Mutation - writing to WordPress, changing tracked-keyword
strategy, curating the skillbook - is gated, in code, not by convention:
the executor checks a proposal's recorded approval status before every
write and refuses anything that is not `approved`. You choose the approval
channel at setup; none is privileged over the others. Full protocol:
`docs/approval-channels.md`.

## Routines

Cadences (daily signal pull, weekly reflection, monthly deep audit) are
declared in the site profile; the runtime that executes them is a separate
choice. Four options: claude.ai scheduled tasks (zero setup, runs on your
subscription), a local OS schedule, GitHub Actions CI (an API key, billed
per token), or fully manual. Full comparison and setup steps for each:
`docs/routines.md`.

## Evidence honesty

Every AEO/GEO tactic organic-os recommends is labeled by how strong the
evidence behind it actually is, and it says so when a popular tactic is
weakly supported - schema markup shows no measured lift on AI citations in
controlled testing (still shipped, because it holds up independently for
Google rich results), and `llms.txt` sees close to zero AI-bot traffic in
the largest study run on it to date (shipped only as an optional, low-cost
hedge). Full ranked table with sources: `docs/evidence.md`.

## Credits and prior art

- [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) - the point-in-time SEO audit this project's signal-quality bar borrows from directly.
- [seranking/seo-skills](https://github.com/seranking/seo-skills) - Claude Agent Skills for the SE Ranking MCP server; a reference for how to shape SEO data into finished deliverables as skills.
- [WordPress/mcp-adapter](https://github.com/WordPress/mcp-adapter) - the official WordPress MCP bridge; not load-bearing in v1 (onsite-optimizer writes over plain REST) but tracked for its 1.0.
- [Automattic/mcp-wordpress-remote](https://github.com/Automattic/mcp-wordpress-remote) - a reference implementation for remote WordPress MCP auth flows.
- [Devora-AS/rank-math-api-manager](https://github.com/Devora-AS/rank-math-api-manager) - exposes RankMath's SEO meta fields over the WordPress REST API; the alternative to organic-os's own bundled bridge mu-plugin.
- [AminForou/mcp-gsc](https://github.com/AminForou/mcp-gsc) - a Search Console MCP server; one of the paths `docs/credentials/gsc-ga4.md` documents.
- [DataForSEO MCP server](https://github.com/dataforseo/mcp-server-typescript) - a documented BYO adapter for paid keyword/SERP data beyond Google Ads.
- [firecrawl/llmstxt-generator](https://github.com/firecrawl/llmstxt-generator) - a reference implementation for generating `llms.txt`, which organic-os ships as an optional hedge per `docs/evidence.md`.
- [oneglanse](https://github.com/aryamantodkar/oneglanse) - an open-source GEO/AI-visibility tracker; a reference for how `hoo-citation-tracker` measures share of voice across AI engines.
- [Aggarwal et al., "GEO: Generative Engine Optimization," KDD 2024](https://arxiv.org/abs/2311.09735) - the controlled-experiment basis for organic-os's strong-tier AEO/GEO tactics.
- [Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning," NeurIPS 2023](https://arxiv.org/abs/2303.11366) - the memory-via-reflection pattern behind the weekly reflector.
- [Wang et al., "Voyager: An Open-Ended Embodied Agent with Large Language Models," 2023](https://arxiv.org/abs/2305.16291) - the ever-growing skill-library pattern behind the skillbook.
- [Suzgun et al., "Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory," 2025](https://arxiv.org/abs/2504.07952) - the adaptive, curated-memory-at-inference-time pattern the skillbook follows.
- [Zhang et al., "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models," 2025](https://arxiv.org/abs/2510.04618) - the generator/reflector/curator division of labor and the brevity-bias/context-collapse failure modes the site-repo contract is built to avoid.
- [MADR - Markdown Architectural Decision Records](https://adr.github.io/madr/) - the ADR template format used throughout `docs/adr/` and every site repo's `decisions/`.

## License

MIT. See `LICENSE`.
