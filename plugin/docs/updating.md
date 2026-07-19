# How updates work

## How updates arrive

`/plugin update organic-os` (or a marketplace refresh, if your Claude
surface pulls updates that way) replaces **plugin code only** - the skills,
agents, commands, and `lib/` scripts under the plugin's own install
directory. Nothing else on your machine or in your accounts changes as a
side effect of an update.

## What an update can never touch, by design

- **Your brain repo(s)** - `~/organic-hq/<slug>` by default, or wherever you
  pointed a site's `brain:` path, whether it is a git repo or a local
  folder. Everything that makes organic-os *yours* lives here: signals,
  the skillbook, decisions, briefs, proposals, outcomes, approvals. An
  update is a plugin-directory operation; it has no path into a brain repo
  that lives outside that directory.
- **`~/.config/organic-os/`** - the sites registry (`sites.yaml`),
  credentials-adjacent env files (WordPress application passwords, a
  Telegram bot token), and anything else scoped to your local operator
  state.
- **Your WordPress site.** organic-os only writes to WordPress through the
  gated apply/publish steps behind an approval (see
  `plugin/docs/approval-channels.md`); an update to the plugin does not run those
  steps and cannot reach a live site on its own.

The plugin directory contains no user data - `scripts/audit.sh` check 7
(the "brain-data boundary" check) enforces this on every CI run by failing
the build if a brain-shaped file or directory (`site-profile.yaml`,
`skillbook.md`, `signals/`, `organic-hq*`, and so on) ever appears anywhere
outside `plugin/lib/core/templates/`. If the repo you are updating from
passes that check, as every released version does, there is nothing brain-
shaped in it to overwrite yours with.

## Compatibility policy

organic-os follows semver, stated here as commitments rather than
aspirations:

- **Patch and minor releases are additive to the brain layout, never
  breaking.** A patch or minor version never removes a field, renames a
  file, or changes what an existing file means. Verifiable directly: `git
  diff v0.1.0..v0.1.2 -- plugin/lib/core/templates` is empty - zero brain-
  format bytes changed across two minor releases.
- **A major release that changes the layout ships a migration.** The
  migration step lives in `/organic-os:setup`'s update mode (see
  `plugin/docs/getting-started.md`), and `core.contracts.check_schema()` blocks
  every routine (`hoo-daily`, `hoo-weekly`, the orchestrator) from running
  against an incompatible brain until you run it. You get a clear message
  naming the exact command to run, never silent corruption or a routine
  quietly operating on data it does not understand.

## Context loss: none possible from an update

All memory lives in your brain repo, which every skill and routine reads
fresh on each run. A plugin update changes the code that reads the brain,
not the brain itself, so there is no session state, cache, or embedded
history inside the plugin that an update could drop.

## Your organization's definitions survive every update

Everything that makes your deployment yours lives in YOUR brain, not in
the plugin: brand voice and tonality rules, banned phrases, the
readability target, editorial conventions written into your brand
rulebook, keywords, competitors, operator knowledge, and every lesson the
skillbook has learned. Two different organizations running the same
plugin version produce different content because their brains differ -
that is the design, not an accident.

Practical consequences:

- Updating the plugin never re-asks your setup questions and never resets
  a definition. If a release changes what the profile can express, the
  new keys are additive and optional; your existing profile keeps working.
- Free-text editorial rules in your brand rulebook (for example "add at
  least three internal links per post" or "every claim needs a named
  source") are read and honored by the content pipeline today. Structured
  enforcement of such rules now exists as the additive `editorial:`
  profile section: link minimums, external-link caps, image
  requirements, sourcing mode, and a required reviewer note are
  enforced as hard QA checks, the way the answer capsule and
  readability target already are (see the editorial section in
  `site-repo-contract.md`). The prose rulebook still applies on top -
  the policy keys are the enforceable floor, the prose is the voice.
- If your organization needs review stages beyond the standard approval
  gate (for example a compliance review before publish), that belongs to
  the multi-approver work on the roadmap. Until then, the approval
  channel plus the pending queue is the single human gate.

## Downgrading

Reinstall an older tag through the marketplace (`/plugin marketplace add
shalintripathi/organic-os` picks up whatever ref you point it at). One
one-way constraint: a brain stamped with a newer `schema_version` will
refuse to operate under an older plugin, the same `check_schema()` gate
described above, just triggered from the other direction. That refusal is
the safe outcome - an older plugin silently misreading a newer brain layout
would be worse than a blocked routine with a clear message.
