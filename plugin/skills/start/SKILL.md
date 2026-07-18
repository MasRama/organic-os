---
name: start
description: Use when the user first opens organic-os, says "get started", "start organic-os", "what do I do first", "guide me through this", or runs /organic-os:start. The branded front door - health-checks the environment, then routes to first-run quick setup or, for a returning user, a compact status view and menu. Always ends by naming the three commands used most.
---

# organic-os start (guided front door)

This is the first thing a new or returning user should run. It never writes
anything itself - it health-checks, then hands off to `setup` or to whatever
the user picks from the menu.

## Step 1: greet

One sentence, no hype: organic-os observes a site's search and AI-answer-
engine performance, proposes changes, and only ships them once a human
approves - the loop is the product.

## Step 2: health check

Run each check in order and report plainly what passed and what did not.
Do not stop at the first failure - collect all three results, then act.

1. `python3` on PATH: `python3 --version`. If missing, tell the user
   organic-os needs Python 3.9+ and stop here - nothing else in this skill
   works without it.
2. PyYAML importable: `python3 -c "import yaml"`. If this fails, show the
   fix and stop: `python3 -m pip install --user pyyaml`. Offer to run it for
   them.
3. Registry readable:
   `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -c "from core import registry; print(registry.load())"`.
   A clean `{'active': None, 'sites': {}}` or a populated registry both count
   as a pass - this check is about `core.registry` importing and running,
   not about whether any site exists yet.

If all three pass, say so in one line and move to Step 3.

## Step 3: route

Use the Step 2 registry read to decide which branch applies.

### Registry empty (no sites)

Offer two paths, AskUserQuestion with options:

- **Quick start** - 3 questions, sensible defaults, about 2 minutes.
- **Full setup** - the complete interview (site, brand, audience, keywords,
  competitors, operator knowledge, connectors, Google Ads, WordPress,
  approval channel, runtime, brain location and mode).

Then invoke the `setup` skill in the chosen mode - quick-start mode or the
full first-run interview - and let it run to completion (scaffold, register,
summary). Do not duplicate its questions here.

### Registry has sites

Resolve the active site's brain path, then run
`core.contracts.check_schema(brain_path)` before anything else in this
branch:

- `action: "stamp"` - tell the user this brain predates schema versioning
  and that running `/organic-os:setup` in update mode will stamp
  `schema_version: 1` into it; continue to the status view below (stamping
  is informational, not blocking).
- `action` anything else with `compatible: false` - relay the action string
  verbatim and stop. Do not show status or the menu, and do not route into
  a routine, until the user has resolved it.
- `compatible: true` with `action: "none"` - continue silently.

Show a compact status, read-only, no writes:

1. Active site: name + url (`core.registry.get_active()`).
2. Pending approvals: count lines under a `status: proposed` (or similar
   pending) heading in `<brain>/approvals/queue.md`.
3. Last signal date: the filename (or latest entry date) of the most recent
   file in `<brain>/signals/`. If the directory is empty, say "no signals
   yet".

Then offer a menu, AskUserQuestion with options:

- **Run daily** - invoke `hoo-daily` (the daily signal pull).
- **Review approvals** - open `<brain>/approvals/queue.md` and walk the user
  through pending items.
- **Update settings** - invoke `setup` in update mode.
- **Add a site** - invoke `setup` in add mode.
- **Docs** - point at `$CLAUDE_PLUGIN_ROOT/docs/getting-started.md` and `README.md`'s
  Quickstart-by-persona section.

## Step 4: always close with the three commands

Regardless of which branch ran, end every `/organic-os:start` session by
naming the three commands a user reaches for most:

- `/organic-os:daily` - the daily signal pull.
- `/organic-os:onsite-audit` - a credential-free on-page audit of any URL.
- `/organic-os:weekly` - the weekly reflection pass.

## Rules

- This skill never writes to the registry, a brain repo, or any config file
  itself - every write happens inside `setup`, `hoo-daily`, or whichever
  skill the menu hands off to.
- Never skip the health check, even for a returning user with sites already
  registered - a broken PyYAML install fails silently deep inside `setup` or
  a routine otherwise.
- If the registry read in Step 2 fails for a reason other than "no sites yet"
  (a corrupt YAML file, a permissions error), show the raw error and stop -
  do not guess a fix.
