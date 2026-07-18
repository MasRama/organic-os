# ADR-0001: Single-plugin marketplace packaging

- Status: accepted
- Date: 2026-07-18
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
organic-os packages three functional modules (head-of-organic, onsite-optimizer,
content-engine) plus a shared core contract layer. Users need one install path.
The Claude plugin marketplace format supports multiple plugins per marketplace
repo, so the modules could instead ship as three separate plugins with three
separate installs and three version numbers.

## Decision
Ship one marketplace (`organic-os`) with one plugin (`organic-os`) that bundles
all three modules internally, bounded by directory (`plugin/lib/hoo`,
`plugin/lib/onsite`, `plugin/lib/ce`, `plugin/lib/core`) and import rules
enforced in CI, rather than three separate plugins.

## Consequences
- One `claude plugin install organic-os` gives a user the full team, with no
  manual assembly of three separate plugins.
- The marketplace format is retained, so distribution and update mechanics
  match every other Claude plugin.
- Cost: all three modules share one version number and one CHANGELOG; a change
  to content-engine alone still bumps the version users see for head-of-organic
  and onsite-optimizer.
- A future split into separate plugins would require a breaking change to the
  marketplace manifest and a user re-install.

## Agent Context
Proposed by the agent from research evidence; approved by the human in the
2026-07-18 design session. Evidence: docs/specs/2026-07-18-organic-os-design.md
section 1 ("One install, separate insides") and the module-boundary design in
section 3.
