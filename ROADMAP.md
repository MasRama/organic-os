# Roadmap

Themes, not promises. Within each release, items are ordered by evidence of
user value, not by engineering convenience. The organizing insight behind
this order: commercial AI-visibility tools stop at monitoring and leave
execution on the user's desk
([source](https://discoveredlabs.com/blog/profound-vs-peec-vs-otterly-which-ai-visibility-platform-should-you-buy)).
organic-os is built as the inverse - a gated execution loop, not another
dashboard. All adapter work below is governed by ADR-0009
(`docs/adr/0009-capability-slots-not-tool-bindings.md`): every external
tool is a swappable adapter behind a named capability slot, never a
binding in contract logic. Issues and PRs against any item here are
welcome, including reprioritization - see `CONTRIBUTING.md`.

## v0.2 - First-week wins and loop hardening - COMPLETE

Closed by the v0.2.0 release (2026-07-19): the final item, approval
expiry, shipped there (ADR-0008) - approvals lapse after a per-site TTL,
default 30 days, and an expired item requires re-confirmation before the
next mutating stage runs. Everything else in this phase landed early
across v0.1.3 through v0.1.10, as itemized below.

**Landed early:** brain-repo schema versioning + migration entry point
shipped in v0.1.3 (`core.contracts.check_schema()`,
`schema_version: 1` in `site-profile.yaml`, the migration entry point in
`/organic-os:setup` update mode) rather than waiting for v0.2 - see
CHANGELOG.md. Also landed early in v0.1.4: the striking-distance detector
in the weekly routine (`hoo-weekly`), the Monday report (`hoo-monday-
report`), and the gate self-verification script (`scripts/verify-gates.sh`)
- see CHANGELOG.md. Also landed early in v0.1.5 (Wave A, from first-run
field testing): user docs shipping inside the plugin package, the runtime
wrapper plus launchd templates, and the rewritten local-runtime guide
(the `setup-token` requirement for headless auth, template-body invocation
instead of a slash string, model-404 recovery, and the TCC brain-path
guard now enforced in code, not just documented) - see CHANGELOG.md. Also
landed early in v0.1.6 (wave 1 of the block below, from the same first-run
field testing): the postflight scorecard (setup ends by testing what it
configured, not just writing config), runtime-location awareness (setup
distinguishes where it runs from where routines will run, and tags every
connector probe with the context it was tested in), the connector wizard
with live verification (GA4/GSC absence is a blocker to resolve with a
guided connect and a passed probe, not a status to record; `hoo-daily`
escalates a nudge after 3 consecutive no-data runs), and the
one-secret-at-a-time credentials flow - see CHANGELOG.md. Also landed
early in v0.1.7 (wave 2 of the block below): the three observe-side
detectors - the cannibalization detector and content decay detection in
the weekly routine, and the site drift watch riding the daily observe -
see CHANGELOG.md. Also landed early in v0.1.8 (wave 3): the audit-and-
propose interview and the AI-visibility baseline at setup - see
CHANGELOG.md. This finishes the "Setup verification and runtime
awareness" sub-block in full - every item first identified from
first-run field testing has now shipped ahead of the formal v0.2 release.
Also landed early in v0.1.9 (wave 4): cost transparency per routine run
(the monthly cost ledger written by the runtime wrapper, surfaced in the
Monday report), dry-run mode for `onsite-apply` (the full gated flow
against a client that records intended writes instead of performing
them, proven by verify-gates probe 7), and Bing Webmaster + IndexNow
submission (key generation, root-file verification, and per-ship URL
submission with the status recorded in the outcome) - see CHANGELOG.md.

## v0.3 - Execution breadth

**Landed early:** the CMS adapter contract, the structural priority for
this release, shipped in v0.3.0-alpha.1: `plugin/lib/onsite/cms.py`
defines `CmsAdapter` (the cms slot's documented interface) plus the
`adapter_for` factory reading the additive `cms: {type: wordpress}`
site-profile key, and `WPClient` is adapter one (`update_rankmath` stays
as its WordPress-specific alias for `update_seo_meta`). Adding a CMS is
now a new adapter file plus a profile entry, not a fork - see
CHANGELOG.md and CONTRIBUTING.md's "Contributing a CMS adapter" section.
The onsite skills were normalized to ADR-0009 slot language ("the CMS
adapter, WordPress today") in the same wave. Also landed early, in
v0.3.0-alpha.2: the git-based static-site adapter -
`onsite.gitstatic.GitStaticClient` targets Astro/Next/Hugo/Jekyll-class
sites, writes markdown/MDX frontmatter in a local clone of the site
repo, and delivers every approved change as a pull request, so the human
merge is the final act - the natural pair for the pr-merge approval
channel, serving the early-adopter persona directly. See CHANGELOG.md.
The Shopify adapter (deprioritized) remains open. Also landed early, in
v0.3.0-alpha.5: internal-link graph analysis (`onsite.linkgraph` - a
capped, sitemap-seeded, own-site-only crawl feeding onsite-audit's
link-health dimension: broken links, orphans, hubs, shallow
striking-distance pages, redirect chains) and the gated redirect and
404 fix workflow (the redirect action type in onsite-apply, decided by
the adapter's `capabilities()['redirects']` mode - wordpress
`needs-plugin`, git-static `config-file` via the additive
`cms.redirect_file` key - with anything beyond the declared mode ending
partially-applied and the human step named). See CHANGELOG.md. Also
landed early, in v0.3.0-alpha.6: the three observe-side items -
digital-PR mention signals (hoo-weekly samples where the brand and its
competitors are mentioned across public surfaces; competitor-only
surfaces become P3 signals, at most one gated outreach proposal per
run, and a human executes it - brand mentions correlate roughly 3x
more strongly with AI visibility than backlinks do, per Ahrefs'
75,000-brand study,
[source](https://ahrefs.com/blog/ai-brand-visibility-correlations/)),
the entity-consistency audit (hoo-monthly-audit compares core brand
facts across the site and the profile-listed properties in the
additive `brand.properties:` key; consistency across authoritative
sources drives inclusion in AI answers,
[source](https://www.useomnia.com/blog/how-to-improve-brand-visibility-chatgpt)),
and AI-referral traffic segmentation in the daily observe
([source](https://www.semrush.com/blog/the-operational-gap-ai-seo-study/)).
See CHANGELOG.md.

- **Analytics adapter slot.** GA4 is the first adapter; Microsoft Clarity
  and Matomo are welcome contributions.
- **Image-generation adapter slot.** Canva is the first adapter; Gemini
  and local generators fit the same slot.
- **Gated image and alt-text fix workflow.** The audit already finds the
  gaps; close the loop with proposals the apply path executes.
- **Comparison-content brief type in content-engine.** Listicles and
  X-vs-Y pages are the most-cited content shapes in AI search
  ([source](https://www.position.digital/blog/digital-pr-tactics/)).
- **Topic clustering for content architecture.** Hub-and-spoke clusters
  feeding brief generation. (Pattern credit:
  [claude-seo](https://github.com/AgriciDaniel/claude-seo)'s SERP
  clustering; ours consumes keyword-intel output.)
- **Editorial-oversight scoring before publish.** A human-review-required
  gate, scored per draft. Scaled, unedited AI content correlates with
  deindexation
  ([source](https://www.rankability.com/data/does-google-penalize-ai-content/)).
- **Editorial policy in the site profile.** An additive `editorial:`
  section turning an organization's written conventions (minimum internal
  links, external-link limits, image requirements, sourcing rules) into
  hard QA checks, the way the answer capsule and readability target are
  enforced today. Free-text rulebook prose keeps working; this makes it
  enforceable. Regulated-industry review stages (for example a compliance
  reviewer before publish) belong to v1.0's multi-approver work.
- **claude-seo audit import.** They audit, we operate: import a claude-seo
  report as a seed set of findings organic-os can turn into proposals,
  instead of re-deriving what a point-in-time audit already found.
- **Pipeline parallelism.** Per-page audit fan-out and research prefetch
  when sub-agent dispatch is reliable in headless runs (upstream
  dependency).

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
