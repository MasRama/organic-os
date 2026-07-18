# Roadmap

Themes, not promises. Within each release, items are ordered by evidence of
user value, not by engineering convenience. The organizing insight behind
this order: commercial AI-visibility tools stop at monitoring and leave
execution on the user's desk
([source](https://discoveredlabs.com/blog/profound-vs-peec-vs-otterly-which-ai-visibility-platform-should-you-buy)).
organic-os is built as the inverse - a gated execution loop, not another
dashboard. Issues and PRs against any item here are welcome, including
reprioritization - see `CONTRIBUTING.md`.

## v0.2 - First-week wins and loop hardening

**Landed early:** brain-repo schema versioning + migration entry point
shipped in v0.1.3 (`core.contracts.check_schema()`,
`schema_version: 1` in `site-profile.yaml`, the migration entry point in
`/organic-os:setup` update mode) rather than waiting for v0.2 - see
CHANGELOG.md.

- **Striking-distance detector in the weekly routine.** Pages sitting at
  positions 4-15 in GSC surfaced as gated proposals - pure GSC math, no new
  credentials to configure
  ([source](https://llmfy.ai/blog/striking-distance-keywords)).
- **Cannibalization detector.** Two URLs splitting one query is often the
  real blocker behind a page stuck at positions 4-15, not a content or
  authority gap
  ([source](https://www.averi.ai/how-to/striking-distance-keywords-the-ai-era-playbook-for-positions-4-15)).
- **The Monday report.** A stakeholder-shareable weekly summary in
  markdown. Reporting is the documented top time sink for solo operators -
  25 to 35 hours a week spent across reporting, rank checks, and audits
  ([source](https://seojuice.com/blog/automating-repetitive-seo-tasks-for-freelancers/)).
- **AI-visibility baseline at setup.** Where you appear in AI answers today
  versus two competitors, captured once during onboarding. 45 percent of
  marketing leaders say they cannot measure this today, and commercial
  tools price the capability at 99 to 499 dollars a month
  ([source](https://www.semrush.com/news/463141-semrush-releases-expanded-2026-ai-visibility-index-analyzing-126-million-ai-search-prompts/),
  [source](https://www.surmado.com/blog/best-ai-visibility-tools-2026)).
- **Content decay detection in the weekly routine.** Carried over from the
  v1 roadmap. Refresh loops are the most-loved feature of commercial
  content tools
  ([source](https://diyai.io/ai-tools/seo/clearscope-vs-surfer-seo/)).
- **Gate self-verification script** (`scripts/verify-gates.sh`) plus a
  dry-run mode for `onsite-apply`. Confirms `require_approved` /
  `require_approval_lineage` actually block an unapproved write, without
  touching a real WordPress site.
- **Approval expiry.** Honest gap today: an item sitting at `approved` or
  `drafted` for weeks is still actionable with no re-confirmation step. A
  staleness window means a stale item requires re-confirmation before the
  next mutating stage runs.
- **Cost transparency per routine run.** Each daily/weekly/monthly run
  reports the token cost of the run it just completed, not just the
  runtime-level cost model in `docs/routines.md`.
- **Bing Webmaster + IndexNow submission.** Useful, but not a week-one win
  - demoted to last in this release. Bing indexation already matters to
  `onsite-audit` findings (strong-evidence tier, `docs/evidence.md`); this
  adds the submission side, not just the audit side.

## v0.3 - Execution breadth

- **CMS adapter contract extracted from `wp.py`.** The structural
  priority for this release: turns the current WordPress-specific write
  path in `plugin/lib/onsite/wp.py` into a documented interface any
  adapter can implement, so adding a CMS is a new file, not a fork.
- **Git-based static-site adapter.** Proposals arrive as pull requests
  against a static-site repo (Astro, Hugo, Jekyll, and similar) instead of
  a REST write - the approve gate becomes "merge the PR," matching the
  pr-merge approval channel that already exists. Serves the early-adopter
  persona directly.
- **Gated redirect and 404 fix workflow.** `onsite-audit` already finds
  broken links and missing redirects; this closes the loop with an apply
  path instead of leaving the finding as a report line.
- **Internal-link graph analysis.** A site-wide crawl that maps internal
  links and flags orphaned or under-linked money pages, feeding
  `link-authority-strategist`. The most-cited gap in commercial content
  tools
  ([source](https://slatehq.com/blog/clearscope-vs-marketmuse)).
- **Digital-PR mention signals.** Proposes outreach targets; a human
  executes. Brand mentions correlate roughly 3x more strongly with AI
  visibility than backlinks do, per Ahrefs' 75,000-brand study
  ([source](https://ahrefs.com/blog/ai-brand-visibility-correlations/)).
- **Entity-consistency audit.** Checks the same brand facts across site,
  LinkedIn, GitHub, and directories. Consistency across authoritative
  sources drives inclusion in AI answers
  ([source](https://www.useomnia.com/blog/how-to-improve-brand-visibility-chatgpt)).
- **Comparison-content brief type in content-engine.** Listicles and
  X-vs-Y pages are the most-cited content shapes in AI search
  ([source](https://www.position.digital/blog/digital-pr-tactics/)).
- **AI-referral traffic segmentation in the daily observe.**
  ([source](https://www.semrush.com/blog/the-operational-gap-ai-seo-study/)).
- **Editorial-oversight scoring before publish.** A human-review-required
  gate, scored per draft. Scaled, unedited AI content correlates with
  deindexation
  ([source](https://www.rankability.com/data/does-google-penalize-ai-content/)).
- **claude-seo audit import.** They audit, we operate: import a claude-seo
  report as a seed set of findings organic-os can turn into proposals,
  instead of re-deriving what a point-in-time audit already found.

## v1.0 - Many sites, many hands

- **Multi-site orchestration across brain repos.** The sites registry
  (`~/.config/organic-os/sites.yaml`) already tracks multiple sites; v1.0
  adds running routines across all of them in one pass, not one at a time.
- **Agency mode.** Named approvers per site, approval TTL, white-label
  Monday report. Reporting is the retention feature for the agency
  persona, same evidence as the Monday report above
  ([source](https://seojuice.com/blog/automating-repetitive-seo-tasks-for-freelancers/)).
- **Content inventory and portfolio view over the brain repo.** Inventory
  analysis is the retention hook of MarketMuse-class tools
  ([source](https://checkthat.ai/brands/marketmuse/reviews)).
- **Reddit and community observe, read-only.** Subreddit mentions as
  signals, never posting. Reddit accounts for roughly a quarter of
  Perplexity citations
  ([source](https://www.cmswire.com/digital-marketing/reddits-rise-in-ai-citations-what-marketers-must-know-about-aeo-strategy/)).
- **AI-crawler analytics from server logs.** GPTBot, ClaudeBot,
  PerplexityBot crawl behavior over time - an open-source gap today
  ([source](https://www.surmado.com/blog/best-ai-visibility-tools-2026)).
- **Adapter contribution guide.** A how-to for the CMS/channel adapter
  pattern established in v0.3, once there are enough real adapters to
  generalize from.

## Deprioritized, with reasons

Not dropped - reordered below the items above, on purpose, with the reason
made explicit instead of left implicit.

- **Shopify adapter.** Waits for the first external request. The
  git-static adapter above serves the actual early adopters seen so far.
- **CrUX Core Web Vitals monitoring.** Table stakes elsewhere. Off-site
  authority is roughly 3x more influential than on-site technical factors
  for AI visibility, the same study cited for digital-PR mention signals
  above
  ([source](https://ahrefs.com/blog/ai-brand-visibility-correlations/)).
- **Anonymized lessons library.** A community feature that waits for a
  community. Tactic and evidence tier only, opt-in, no URLs, keywords, or
  brand names - the structured version of the "share a learning without
  data" path `CONTRIBUTING.md` describes today as an issue.

## Out of scope, deliberately

Each of these is a different surface with its own tooling category.
organic-os stays the search-and-AI-answers engine; it does not grow into a
general marketing suite.

- **Local SEO and Google Business Profile.** A different ranking system
  (map pack, not organic/AI answers) with its own signal set.
- **Review management.** A reputation-management surface, not a
  search-visibility one.
- **Email and newsletters.** A distribution channel organic-os's output
  can feed, not a channel it should operate.
- **Social repurposing.** Same reasoning as email - downstream of what
  this project produces, not a function it should absorb.
- **Conversion optimization beyond reporting.** On-site conversion work is
  a different discipline (CRO) from earning and keeping organic and AI
  visibility.

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
