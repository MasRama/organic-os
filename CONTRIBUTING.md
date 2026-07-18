# Contributing to organic-os

Thanks for looking at this. organic-os is an engine, not a dataset - the
guidance below exists to keep it that way.

## What we welcome

- **Bug reports** with a repro: what you ran, what you expected, what
  happened. Include `python3 --version` and whether `python3 -c "import
  yaml"` succeeds.
- **Code fixes with tests.** `plugin/lib/core`, `plugin/lib/hoo`, and
  `plugin/lib/onsite` are plain Python covered by `tests/`. A fix without a
  regression test that would have caught it is a partial fix.
- **New skills or agents that read the site profile.** Anything under
  `plugin/skills/` or `plugin/agents/` that takes `site-profile.yaml` (or an
  equivalent generic input) and works for any site, not one business.
- **CMS or channel adapters.** A new CMS backend implements the
  `CmsAdapter` contract in `plugin/lib/onsite/cms.py` (see "Contributing
  a CMS adapter" below); a new approval channel lands alongside
  telegram/pr-merge/slack/email in `lib/core/approval.py`.
- **Docs.** Fixes, clarifications, missing setup steps.
- **Evidence updates, with primary sources.** A change to `plugin/docs/evidence.md`
  needs a real citation (a study, a vendor analysis with methodology, a
  controlled experiment) - not "I heard AI cites X more now."

## The data boundary (hard rule)

organic-os is an engine. Your business data - the contents of
`site-profile.yaml`, keyword lists, brand rulebooks, competitor lists,
skillbook entries, signals, screenshots with real data - lives in **your own
private brain repo**, never in this one.

Any PR to this repo that contains brain-shaped content is auto-rejected.
Concretely, CI runs `scripts/audit.sh`, whose check 7 fails the build if the
diff introduces:

- a file named `site-profile.yaml`, `skillbook.md`, `tracking.yaml`, or
  `telegram-offset.json` anywhere outside `plugin/lib/core/templates/`
- a directory named `organic-hq*`, `signals/`, or `reflections/` anywhere
  outside `.git`

Why this is a hard rule and not a style preference: every business's site
profile, keywords, and skillbook are different, and the engine has to stay
generic enough to serve all of them - the moment one contributor's real
brand rulebook or keyword list lands in this repo, the codebase starts
silently coupling to one business's specifics. It is also a privacy
guarantee: nobody's competitor list, traffic numbers, or approval history
should ever be one accidental `git add .` away from a public PR.

If your PR trips this check because you were testing against a real brain
repo locally, move the brain repo outside the organic-os checkout (the
default `organic-hq-<site>/` scaffolding already does this) and re-push.

## How to share learnings without data

Found a tactic that works? Open an issue describing the tactic, its
evidence tier (`strong` / `moderate` / `anecdotal`, matching
`plugin/docs/evidence.md`), and where the evidence comes from - no URLs, no
keywords, no brand names, no screenshots of a real site. The roadmap's
anonymized lessons library (see `ROADMAP.md`, v1.0) will formalize this into
something structured; until then, an issue is the right venue.

## Dev setup

```
git clone https://github.com/shalintripathi/organic-os.git
cd organic-os
python3 -m pip install --user pyyaml pytest
python3 -m pytest tests/ -q
./scripts/audit.sh
```

Both commands should be clean before you start (every test passing,
`audit: clean`) and clean again before you open a PR.

## Contributing a CMS adapter

The cms capability slot (ADR-0009,
`docs/adr/0009-capability-slots-not-tool-bindings.md`) takes new backends
as adapters. WordPress (`plugin/lib/onsite/wp.py`) is adapter one and the
reference for a REST backend. Git-static
(`plugin/lib/onsite/gitstatic.py`) is adapter two and the smallest honest
adapter - a local-clone file writer with no transport at all and every
gap declared (`rendered_head_verify: False`, `needs_human: ["merge-pr",
"deploy"]`, `get_rendered_head` raises naming the gap). Start from
whichever shape your backend matches.

- **Implement `CmsAdapter`** (`plugin/lib/onsite/cms.py`): one class per
  backend covering the full surface - `get_post`, `update_post`,
  `create_post`, `update_seo_meta`, `get_rendered_head`, `snapshot`,
  `rollback`, `capabilities`, `adapter_name`. Register the type in
  `adapter_for` and `SUPPORTED_CMS_TYPES`, and document any
  backend-specific site-profile keys the adapter reads.
- **The capabilities() honesty rule.** Declare what your adapter cannot
  do: `needs_human` lists the action types it cannot perform. When an
  approved proposal includes such a step, the item ends
  `partially-applied` with a note naming exactly what a human must finish
  (`docs/adr/0007-partially-applied-state.md`) - an adapter never fakes
  success for an action it cannot perform.
- **The test bar.** A fake-transport test file mirroring
  `tests/test_wp.py`'s pattern (an injected fake session, no network) -
  or, for a file-based backend, `tests/test_gitstatic.py`'s tmp-dir
  pattern (no real git, no transport) - proving the contract end to end:
  reads, writes, the snapshot/rollback round-trip, dry-run logging with
  zero transport calls, and backend errors surfacing as `RuntimeError`
  carrying the backend's message.
- **Gates stay in core.** Adapters never gate: `require_approved` /
  `require_approval_lineage` run in the skills through `core.contracts`
  before any mutating adapter call. An adapter performs the write it is
  asked to perform, nothing more, and never inspects item status.
- **PR checklist.** Tick the adapter line in the PR template: state which
  `capabilities()` flags are true and why, backed by the backend's docs,
  and point at the fake-transport test file.

## Standards

- **TDD for `lib/core`, `lib/hoo`, `lib/onsite` code.** Write the failing
  test first. See `tests/` for the existing pattern per module.
- **No em-dashes.** Use a hyphen with spaces (` - `), a comma, or split the
  sentence.
- **No hype words.** `scripts/audit.sh` (check 4, the `BANNED` pattern)
  blocks a list of marketing cliches across `plugin/`, `docs/`, and the
  root-level docs. Open the script to see the exact pattern. If the audit
  flags a word, rephrase rather than add it to an exclude list.
- **Every claim sourced.** Numbers, study results, and comparisons need a
  link to where they came from, the same standard `plugin/docs/evidence.md` holds
  itself to.
- **Cross-file consistency.** `docs/INFORMATION-MAP.md` plus audit check 8
  guard the facts quoted in more than one file (version, counts, TTLs,
  layout); when you add a load-bearing fact, add its row to the map in the
  same commit.

## PR checklist

Mirrors `.github/PULL_REQUEST_TEMPLATE.md` - see that file for the exact
checkboxes a PR should carry.

## Code of conduct

Be professional. Disagree about code, not people. Assume good faith on a
first pass, and say so plainly if a PR does not fit organic-os's scope
rather than letting it sit. Maintainer discretion applies to anything not
covered explicitly above.
