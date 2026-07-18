# ADR-0007: Partially-applied is a first-class state

- Status: accepted
- Date: 2026-07-19
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
The first full pipeline field run applied an approved proposal whose changes
did not all land: the connected WordPress user held the Editor role, and one
step needed a capability only an Administrator has. Part of the proposal was
live, part was not, and the lifecycle had no state that told the truth -
"applied" overclaims, "failed" discards real work, and leaving the item at
"approved" invites re-applying the half that already landed. Because the
honest state did not exist, the field workaround was a direct frontmatter
edit - exactly the write path the contracts exist to prevent.

## Decision
`partially-applied` joins the lifecycle as a first-class status. Exactly
three edges touch it: approved -> partially-applied when some changes in an
approved proposal landed and the rest hit a permission or capability wall;
partially-applied -> applied when a human finishes the pending steps; and
partially-applied -> failed when the partial work is rolled back instead.
Nothing else enters or leaves it. The state is set through the contract CLI
with a note naming exactly what a human must finish, and the outcome record
lists done versus pending steps. `require_approval_lineage` is unaffected:
a partially-applied item still carries its recorded approval.

## Consequences
- The queue shows partial work explicitly: `rebuild_queue` renders a PARTIAL
  row per partially-applied item with the human-follow-up note inline, so
  half-done work is never invisible.
- Cost: one more state to reason about - every consumer of the lifecycle
  (task board, measurement, reflector) has to decide what partially-applied
  means for it.
- The gate stays honest: when reality lands between applied and failed,
  there is a contract-checked path to say so, removing the pressure to
  hand-edit frontmatter.

## Agent Context
Proposed by the agent from field evidence; approved by the human in the
v0.1.10 fixes session (2026-07-19). Evidence: the first full pipeline field
run, where an editor-role capability wall left an approved proposal half
applied and the only available record of that reality was a direct
frontmatter edit.
