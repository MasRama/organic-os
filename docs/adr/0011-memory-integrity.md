# ADR-0011: Memory integrity and honest boundaries

- Status: accepted
- Date: 2026-07-23
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
organic-os keeps memory across runs: signals, a skillbook, outcome
records, and a queue of gated work. Three failure modes in that memory
had no answer in the codebase, and a fourth question sat underneath all
of them.

A rejection died with the item that carried it. A human refused a
proposal, the note went into that item's frontmatter, and the next run
proposed the same work again, because nothing outside the item read the
refusal. Memory that only accumulates and never gets consulted is not
memory.

A skillbook entry, once written, was trusted forever. A lesson earned
from one anecdote in March still read as current in July, next to a
lesson backed by a controlled study, with nothing distinguishing them but
a tier tag nobody acted on. Search behaviour moves; a memory that never
expires eventually teaches the loop something that stopped being true.

Content left the brain through several sinks (an approval channel, a
Notion mirror, a report, a CSV export) with no scan on the way out. A
token pasted into a proposal body would ride along.

And the fourth: the project publishes numbers about the sites it works
on. Nothing let a reader recompute one. A claim that only its author can
check is a claim on the same footing as marketing.

## Decision
Four rules, one theme: memory has to be consultable, expirable,
boundaried, and checkable.

1. **Durable decisions are consulted before re-deciding.** Every
   rejection writes a decision record to `decisions/` (`core.decisions`,
   written by `set_status` so no skill has to remember), and the skills
   that create work search those records before calling `create_item`. A
   matching rejection means the work is skipped and named in the run
   report, or re-proposed carrying when it was refused, why, and what
   changed since. Never silently raised again.
2. **Lessons expire by evidence tier.** A skillbook entry carries
   `last-confirmed`, and goes stale past a per-tier threshold
   (`STALE_DEFAULTS`: anecdotal 90 days, moderate 180, strong 365,
   overridable per tier in the site profile). Weak evidence goes stale
   fast, strong evidence keeps for a year. Staleness is surfaced in the
   weekly reflection for a human to re-confirm or retire, never enforced:
   nothing deletes a lesson on a timer.
3. **The outbound boundary is advisory.** `core.redact` scans content
   at every sink before it leaves and reports what it found, masked. It
   does not block, does not rewrite, and does not raise. This is a
   deliberate limit, stated in the module and in the docs: a high-tier
   finding on outbound content means a credential-shaped string already
   left, so the honest response is to rotate that credential, not to
   assume a guard held. Pattern matching also misses what it was not
   taught, so a clean scan is the absence of a match and never a
   guarantee. A guard that quietly rewrote a user's own export would be a
   worse surprise than the finding it suppressed.
4. **Claims are independently reproducible.** Every outcome record names
   the URL and the measurement windows, and
   `/organic-os:verify-outcome` recomputes the delta from raw connector
   data BEFORE reading what was claimed, then compares
   (`core.outcomes.compare`). A divergence is recorded as a signal, not
   suppressed. Unreachable connectors mean unverified, never assumed
   correct. `plugin/docs/reproducing-results.md` documents the same check
   by hand in Search Console, so the claim survives without the tool.
   Reproduction proves consistency between a claim and the data, and
   nothing more: attribution to a single change stays unprovable, and
   the records say so.

## Not adopted
Each of these was considered in the same pass and refused, with the
reason recorded so the refusal survives being raised again.

- **Telemetry, including opt-in.** Two data flows get conflated under one
  word, so separate them: brain data flowing IN (a site's own analytics,
  into the user's own repo) is the product; usage data flowing OUT to a
  maintainer's server is a different thing entirely, and it is the second
  one refused here. Even opt-in, it costs a server, a database, and an
  account, which are the three things the README says organic-os does not
  have. The gain would be knowing how installs fail without asking.
  `/organic-os:diagnose` covers that instead: it collects the same
  install-shaped facts, prints them locally, redacts before printing, and
  never transmits. The operator decides what to paste. Revisit trigger:
  meaningful install volume combined with repeated guessing about failure
  modes that a printed report is demonstrably not answering. Not before
  both.
- **A browser sidebar with an ML classifier stack.** Driving a browser is
  not a core function of this project. organic-os reads licensed APIs and
  writes through a CMS adapter; a sidebar would add a runtime surface, a
  model to maintain, and a scraping-adjacent capability that ADR-0006
  rules out. Sites that need page-level inspection already have the
  read-only audit path, which needs no credentials.
- **A bundled cross-model reviewer.** Sending drafts to a second model
  for review is useful, and users who want it can wire their own: BYO
  stays the rule. Bundling one means picking a provider, carrying its
  key handling, and taking on its pricing changes for every installer,
  including the ones who would never use it.
- **LOC-style productivity claims.** Lines of code, items shipped per
  week, hours saved: vanity metrics that measure activity, not
  visibility. This project already refuses opaque 0-100 content scores
  and visibility indexes with no published methodology (ROADMAP, "What
  we will not build") for the same reason, and would be inconsistent to
  publish its own.

## Consequences
- Proposing work now costs a decision search first, and re-proposals
  carry an explanation. Slightly more work per item, and the loop stops
  re-litigating settled calls.
- The weekly reflection grows a stale-review section, so a human is asked
  periodically about lessons nobody has confirmed lately. A brain that is
  never reviewed accumulates stale entries and now says so out loud.
- The redaction scan runs on every outbound path and can report a finding
  the user then has to act on. It will also miss things. Both facts are
  documented at the sink, and neither is presented as protection.
- Published outcomes are now falsifiable by anyone with the site's Search
  Console. Some of them will fail to reproduce, and those findings land
  in the brain as signals rather than being quietly dropped.
- Every new sink inherits an obligation: scan before sending. Every new
  claim inherits one too: name the window it was measured over.

## Agent Context
Prompted by studying [gstack](https://github.com/garrytan/gstack)
(2026-07-23) and asking which of its patterns this project was missing.
Four carried over: durable decisions consulted before re-deciding,
learned knowledge that expires, a redaction boundary before external
sinks, and the reproduction-script posture applied to our own claims. The
not-adopted list is the rest of that study, refused on this project's
terms rather than left unexamined. Recorded in the v0.5.0 session
alongside `core.decisions`, `core.redact`, `core.outcomes`, the skillbook
staleness thresholds, `/organic-os:diagnose`, and
`/organic-os:verify-outcome`.
