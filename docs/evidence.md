# Evidence

organic-os labels every AEO/GEO tactic it recommends by how strong the
evidence behind it actually is, and says so out loud when a popular tactic
is weakly supported. This page is that ranking, kept current as new studies
land. `ce-seo-aeo` (the content-engine SEO/authority stage) reads this
table before recommending anything.

## Strong

| Claim | Evidence | Source | What organic-os does |
|---|---|---|---|
| Server-rendered HTML is required for AI crawlers to see your content | Vercel and MERJ analyzed a billion-plus AI crawler requests and found none of the major AI crawlers (GPTBot, ClaudeBot, PerplexityBot) execute JavaScript; only Google's Gemini (via Googlebot's infrastructure) and AppleBot render JS | [Vercel: The rise of the AI crawler](https://vercel.com/blog/the-rise-of-the-ai-crawler) | `onsite-audit` flags client-side-only rendering as a blocking issue, not a suggestion |
| Named statistics, quotes, and cited sources measurably increase AI citation | A controlled experiment across 10,000 queries and 9 datasets found named expert quotes with credentials lifted citation probability 40.9%, statistics paired with named sources 30.6%, inline citations to authoritative references 27.5% | [Aggarwal et al., "GEO: Generative Engine Optimization," KDD 2024](https://dl.acm.org/doi/10.1145/3637528.3671900) ([arXiv preprint](https://arxiv.org/abs/2311.09735)) | content-engine's brief stage requires a named statistic or quote with a real source before a draft passes QA |
| Bing indexing determines most ChatGPT search citations | An analysis of SearchGPT citations found 87% matched Bing's top organic results | [Seer Interactive: 87% of SearchGPT citations match Bing's top results](https://www.seerinteractive.com/insights/87-percent-of-searchgpt-citations-match-bings-top-results) | `onsite-audit` checks Bing indexation status, not only Google's, and flags pages missing from Bing |
| Fresh content is cited disproportionately across AI engines | A longitudinal citation study found AI-cited content averaged 25.7% fresher than traditionally ranked content, and 76.4% of ChatGPT's top-cited pages had been updated within the prior 30 days | [Semrush: How fast do AI search platforms cite new content](https://www.semrush.com/blog/how-fast-do-ai-search-platforms-cite-new-content/) | `hoo-monthly-audit` flags content older than 12 months without an update as a freshness gap; `onsite-propose` can open a refresh proposal |
| Extractable structure (clear headings, direct answers, scannable lists) helps passages get lifted into AI answers | Consistent finding across the GEO paper's ablations and industry crawler studies: content structured for direct extraction outperforms equivalent prose-only content | [GEO: Generative Engine Optimization](https://arxiv.org/abs/2311.09735) | content-engine's TL;DR-capsule-first structure and answer-first paragraphing are the default draft shape |

## Moderate

| Claim | Evidence | Source | What organic-os does |
|---|---|---|---|
| Community discussion (Reddit and similar) contributes to AI answer sourcing | Widely observed in AI answer citation mixes and industry commentary, but with less controlled measurement than the strong-tier items above | Directional industry consensus; no single controlled study cited here | `hoo-citation-tracker` records when a competitor or the site itself is cited via a forum/community result, but organic-os does not recommend seeding community posts as a strategy |
| Covering the fan-out of related sub-queries an AI engine generates around a topic improves overall visibility | Consistent with how retrieval-augmented answer engines assemble context from multiple queries per user question, reported across several vendor studies | Directional industry consensus | `hoo-keyword-intel`'s gap analysis includes adjacent/related queries alongside the primary seed, not only exact-match targets |
| Third-party listings and directories help entity-level (brand, product) queries get answered correctly | Observed in entity-query citation mixes; plausible given how AI engines resolve entities, not rigorously isolated as a causal factor | Directional industry consensus | `entity-schema-engineer` notes missing third-party listings as a finding, not a mandated fix |

## Weak or contradicted

| Claim | Evidence | Source | What organic-os does |
|---|---|---|---|
| Adding schema markup increases AI citations | Ahrefs tracked 1,885 pages that added JSON-LD against 4,000 matched controls: no platform (Google AI Overviews, Google AI Mode, ChatGPT) showed a meaningful citation increase after schema was added. Pages with schema are cited more often on average, but that correlation tracks overall site quality, not schema itself | [Ahrefs: We tracked 1,885 pages adding schema. AI citations didn't move](https://ahrefs.com/blog/schema-ai-citations/) | organic-os still ships schema markup by default (`agent_jsonld` bridge, `entity-schema-engineer`) because it is well-established for Google rich results independent of AI citation effects; the docs are explicit that the AI-citation case for it is unproven |
| Publishing an `llms.txt` file improves AI visibility | Ahrefs analyzed 137,000 sites with an `llms.txt` file: 97% received zero bot requests to that file in the study period, and among the requests that did land, only about 1% came from AI retrieval bots (most were SEO tools and unrelated crawlers). No AI provider has committed to parsing it | [Ahrefs: We analyzed 137K sites - 97% of llms.txt files never get read](https://ahrefs.com/blog/llmstxt-study/) | organic-os can generate `llms.txt` as an optional, low-cost hedge if the installer wants it, but it is never presented as a visibility tactic and setup does not recommend it by default |

## How this page gets used

- `ce-seo-aeo` cites this table's strong-tier tactics as the basis for its
  recommendations and explicitly declines to recommend weak/contradicted
  tactics as if they were load-bearing.
- `hoo-monthly-audit` and `onsite-audit` reference the strong-tier checks
  (server-rendering, Bing indexation, freshness, extractable structure) as
  audit criteria.
- This table is reviewed, not fixed: when a cited study is superseded or a
  new controlled study changes a tactic's tier, update the row and the tier
  it lives in rather than adding a second contradicting row.
