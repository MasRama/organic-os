# ADR-0010: Audit-dimension responsibility map

- Status: accepted
- Date: 2026-07-19
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
Field testing on a live deployment surfaced a miss the loop itself never
caught: two full-loop audit runs passed over a thin author entity (an
AI-persona author with no bio, no sameAs links, no credentials, and no
human-reviewer note) because no E-E-A-T dimension existed in the audit
checklist. A third-party audit caught it instead. In the same period, a
published article shipped without the answer capsule the pipeline
mandates: the convention existed as prose, but no stage enforced it.
Both misses share a root cause - a rule or a check that lives nowhere
executable cannot fire - and both raised the same question: when a gap
is found, which part of the system owns detecting it, and which part
owns fixing it?

## Decision
Detection belongs to head-of-organic's audit dimensions. The checklist
IS the product's eyes: a check that does not exist cannot fire, so every
class of miss must exist as an explicit, numbered dimension in
`plugin/skills/onsite-audit/SKILL.md` (run site-wide by
`hoo-monthly-audit`). Audits do not rely on general judgment to notice
what the checklist forgot.

Remediation splits by artifact locality:

- **Site-level artifacts** (author bio, publisher schema, og:image
  assets, sitemap health) are the onsite lane's job: a finding becomes a
  gated proposal (`onsite-propose`), applied only after approval
  (`onsite-apply`), with steps beyond the adapter's `capabilities()`
  ending partially-applied per ADR-0007.
- **In-article conventions** (answer capsule, readability, outbound
  link judgment) are content-engine's job, enforced as hard checks at
  QA (`ce-qa`) so a non-conforming draft is returned to the writer, not
  published and later flagged.

The dimension list is a living contract: every externally-caught miss
becomes a dimension addition, and each addition is logged here, in this
ADR's Agent Context or a successor ADR, so the list's growth stays
traceable to the misses that forced it.

## Consequences
- Audits get longer: seven page-essentials checks per page, plus the
  site-wide sweeps, cost fetches and produce more findings per run.
- More proposals reach the approval queue, and the human reviews them;
  that is the accepted price of a checklist that covers what field
  testing proved it must.
- The v0.3 entity-consistency item (ROADMAP.md) is the deeper successor
  to the author-entity check: same brand facts verified across site,
  LinkedIn, GitHub, and directories, not only on-page.
- The v0.3 claude-seo audit import is the complement, not a substitute:
  importing an external report seeds findings beyond our dimensions'
  depth, while this ADR guarantees our own dimensions cover every class
  of miss already caught.
- A future externally-caught miss is now a process event with a defined
  response (add the dimension, log it), not an embarrassment to patch
  quietly.

## Agent Context
Proposed after third-party field-testing feedback on a live deployment
(2026-07-19): two full-loop runs never flagged a thin author entity
because the dimension did not exist, and a mandated answer capsule
shipped missing because no stage enforced it. Recorded in the
v0.3.0-alpha.4 session alongside the page-essentials dimension
(onsite-audit), the site-wide monthly reference (hoo-monthly-audit), and
the content-engine hard checks (ce-qa, ce-editor, ce-produce,
onsite-publish).
