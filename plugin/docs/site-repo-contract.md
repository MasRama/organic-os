# The site repo contract

Every site organic-os manages has its own "brain": a git repo (or plain
folder, in local brain mode) holding everything the plugin knows about that
site. This page documents its layout, the item schema, the skillbook line
format, and the write discipline that keeps memory useful instead of
becoming an unreadable pile.

**The rule that matters most: any tool may READ these files; only
`lib/core` WRITES them.** Skills in `lib/hoo`, `lib/onsite`, and the
content-engine agents call into `core.contracts` and `core.approval` for
every mutation. None of them touch a brain-repo file with a raw `open()` or
a raw commit for anything status-bearing. This is what makes the approval
gate enforceable in code rather than by convention - there is exactly one
choke point where a write can happen, and that choke point checks status.

## Layout

```
organic-hq-<site>/
  site-profile.yaml        identity: url, sitemap, brand voice rules, competitors,
                            geos, connectors, approval channel, runtime mode, WP endpoint
  skillbook.md              curated playbook, one entry per line (see below)
  signals/YYYY-MM-DD.md     daily raw observations, append-only, never edited
  reflections/YYYY-Www.md   weekly reflector output: proposed skillbook deltas by entry ID
  decisions/NNNN-*.md       ADRs for this site, MADR-lite + Agent Context section
  briefs/                   content briefs, one file each, status frontmatter
  proposals/                on-page fix proposals, same status lifecycle as briefs
  approvals/queue.md        pending-approval index, rebuilt on every status change
  runs/YYYYMMDD-<skill>/    timestamped run outputs: numbered raw files + REPORT.md
  keywords/tracking.yaml    tracked keyword set + per-keyword history
  outcomes/                 post-change measurements linked back to the item that caused them
  drift/baseline.json       on-page snapshot for drift detection, WP-only, lazy (see below)
```

`init_site_repo` (run by `/organic-os:setup`) creates every directory above,
a starter `site-profile.yaml` with the site's URL and name filled in, an
empty `skillbook.md` with its header, an empty `approvals/queue.md`, and an
empty `keywords/tracking.yaml`. It never overwrites a file that already
exists, so re-running setup on an existing brain repo is safe.

`drift/` is additive and does not appear in that scaffold: `schema_version`
stays `1`, and the directory only comes into existence the first time
`hoo-daily`'s drift-watch section runs with a verified WordPress
connector (`onsite.drift.save_baseline` creates it on demand). A brain
repo with no WordPress connection never gets a `drift/` directory at all.

The optional `site-profile.yaml` key `onsite: {dry_run: true}` is
additive the same way (`schema_version` stays `1`; absence means off):
when present, `onsite-apply` and `onsite-publish` run their full gated
flow against a dry-run client that records every intended write instead
of performing it - the outcome record is marked dry-run and lists them.

## Items: briefs and proposals

An item is a markdown file with YAML frontmatter, living in `briefs/`
(content briefs, `kind: content-brief`) or `proposals/` (everything else:
`onpage-fix`, `publish`, `strategy`). The filename is
`<created-date>-<slug>.md`; the frontmatter `id` is `b-<date>-<slug>` for
briefs and `p-<date>-<slug>` for proposals.

Frontmatter fields: `id`, `kind`, `status`, `created` (UTC timestamp),
`title`, `target` (the URL or entity the item is about), `source` (what
produced it - a signal, an audit finding, an operator note), and
`approvals` (a list that starts empty and gets an entry appended every time
`set_status` records an `approved` or `rejected` decision: `actor`,
`channel`, `decision`, `at`).

### Status lifecycle

```
proposed -> approved | rejected
approved -> applied | drafted | failed
drafted  -> published
applied | published -> measured
```

`failed` exists for the case where an approved on-page fix was applied,
failed its post-write verification, and was rolled back - it sits between
`approved` and everything downstream, and `applied -> failed` is
deliberately not a legal transition, because a failure is only possible
before the write is confirmed to have stuck.

Illegal transitions raise `ContractError` rather than silently no-op. There
is no path back from `approved` to `proposed`, and no path at all out of
`rejected` - a rejected item is done; a new item gets created if the work
still needs doing.

### The approval gate in code

Two functions gate mutation, used at different points in an item's life:

- **`require_approved(path)`** - the item's *current* status must be
  `approved`. This is the gate `onsite-apply` uses before it writes
  anything to WordPress: an on-page fix has exactly one mutating step, so
  its status is still `approved` at the moment of the write.
- **`require_approval_lineage(path)`** - the item's history must contain at
  least one `approved` decision, regardless of current status. This is the
  gate `onsite-publish` uses: a content brief moves `approved -> drafted`
  (content-engine writing the draft is not itself the mutation that
  matters), and only then does publishing become the actual WordPress
  write. By the time publishing happens the item's current status is
  `drafted`, not `approved`, so `require_approved` would wrongly block it.
  `require_approval_lineage` is safe here specifically because
  `approved -> rejected` is not a legal transition: once an item has an
  `approved` decision in its history, nothing can revoke it later, so a
  lineage check can never be tricked into approving something that was
  actually rejected afterward.

## approvals/queue.md

Rebuilt by `rebuild_queue` on every status change: one line per item
currently sitting at `proposed`, across both `briefs/` and `proposals/`,
sorted by filename. A malformed item (bad frontmatter, missing fields)
appears as a `MALFORMED` row instead of being silently dropped, so a broken
file surfaces instead of disappearing from view.

## drift/baseline.json

The stored snapshot the daily drift watch (`hoo-daily`, `onsite.drift`)
compares against: `{page_id: {title, rank_math_title,
rank_math_description, canonical, slug, status, jsonld_present}}` for the
tracked-page set (pages from `outcomes/*-rollback.json` plus the homepage,
capped at 20). Written only through `onsite.drift.save_baseline`, which
atomic-writes via `core.contracts._atomic_write` - the same
read-through-core / write-through-core discipline as every other file in
this repo, just routed through `lib/onsite` instead of `lib/core` directly
since drift is an on-page (onsite) concern, not a mutation-gate concern.
No baseline on disk means `onsite.drift.compare` returns `[]` rather than
raising - a fresh brain or a brain that has never had a verified WordPress
connector simply has nothing to compare against yet. `onsite-apply`
refreshes the entry for a page it just changed as part of its own verify
step, so an intentional, approved change is never reported back as drift.

## Skillbook

`skillbook.md` is the curated, compounding memory: tactical lessons the
site has actually earned, not raw observations. One entry per line:

```
S-014 [evidence: strong] [helpful: 3, harmful: 0, last-confirmed: 2026-07-18] Title rewrites recover striking-distance drops (p-20260710-pricing-title)
```

- **ID** (`S-NNN`) is assigned sequentially by `skillbook_append` and never
  reused.
- **evidence** is one of `strong`, `moderate`, or `anecdotal` - the same
  three-tier vocabulary `plugin/docs/evidence.md` uses, so a skillbook entry's
  confidence is comparable across the whole plugin.
- **helpful / harmful** counters increment via `skillbook_update` whenever
  an outcome confirms or contradicts the lesson; they never reset.
- **last-confirmed** updates to today every time the entry is touched.
- The trailing `(source)` is the item id or the origin the lesson came
  from, so every lesson traces back to the evidence that produced it.

A deprecated entry is wrapped in `~~strikethrough~~` and suffixed
`DEPRECATED`; it stays in the file (memory is append-only-at-the-line-level,
not delete-capable) but is skipped by anything that reads active entries,
and any further update to it raises `ContractError`.

## The append-only + curator discipline

Borrowed from the ACE / Reflexion / Voyager line of agent-memory research,
carried through the whole brain repo, not just the skillbook:

- **Generator** (daily routines) appends signals via `append_signal`. It
  never touches the skillbook. `signals/YYYY-MM-DD.md` is a flat,
  timestamped, append-only log - lines are never edited or removed.
- **Reflector** (the weekly routine) reads the week's signals and outcomes
  and writes a `reflections/YYYY-Www.md` file proposing itemized deltas,
  each one referencing a specific skillbook entry ID (or proposing a new
  one). The reflector never writes `skillbook.md` directly.
- **Curator** applies those deltas as `skillbook_append` /
  `skillbook_update` calls - append, edit-in-place, or deprecate, on
  specific entries. Two things are forbidden by design: rewriting the whole
  file (it collapses the context each entry carries and makes the history
  useless for tracing why a lesson exists), and summarizing entries down to
  save space (it introduces brevity bias - a compressed lesson quietly
  drops the qualifier that made it correct). Curator merges are
  human-gated by default; a user can promote the curator to autonomous
  merging once they trust it, the same way any other mutation's gate can be
  adjusted.
- Every skillbook entry carries an evidence tag and a source, every ADR
  records the strategy-level decision it captures with an Agent Context
  section (who decided, on what evidence) - the skillbook is where
  tactical, repeatable lessons live; ADRs are where one-off strategic calls
  live. Neither substitutes for the other.
