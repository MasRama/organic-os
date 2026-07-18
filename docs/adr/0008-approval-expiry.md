# ADR-0008: Approval expiry

- Status: accepted
- Date: 2026-07-19
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
An approval, once recorded, never lapsed. An item sitting at `approved` or
`drafted` for weeks stayed actionable with no re-confirmation step: a
proposal approved in March could publish in September, executing a decision
whose context may no longer hold. The gates checked that an approval
existed, not that it was recent - staleness was invisible to the one place
built to catch exactly this kind of drift.

## Decision
Approvals expire after 30 days by default, configurable per site with the
additive `approvals: {ttl_days: n}` key in `site-profile.yaml`
(`schema_version` stays 1; a TTL below 1 refuses - to disable expiry, set a
large value deliberately). Both gates - `require_approved` and
`require_approval_lineage` - additionally verify that the latest approved
record is younger than the TTL, comparing UTC dates at gate time. Because
the check is timestamp-based and runs at the gate, it applies retroactively
to every existing record with no migration.

Expiry means re-confirm, never silent rejection. An expired item keeps its
status; the gate blocks with the exact re-confirm command. Running
`python3 -m core approve` on the item again appends a fresh approval entry
through `record_decision`, refreshing the clock - the same path a replayed
decision takes, except a replay within the TTL stays a silent no-op.

## Consequences
- The gate now answers two questions instead of one: was this approved,
  and is that approval still current. A scheduled routine that picks up an
  old item re-asks the human instead of acting on a stale yes.
- Re-confirmation is one command, and every channel gets it without new
  machinery: a Telegram reply of `approve` to the original proposal message
  re-confirms, because it lands in the same `record_decision` call.
- Cost: an operator who approves in bursts and applies slowly will see
  blocks on items they consider settled. The per-site TTL is the dial for
  that working style.
- The approvals list becomes a re-confirmation history: multiple approved
  entries on one item are now expected, not a fingerprint of an anomaly.

## Agent Context
Proposed from the roadmap's "honest gap" note; the owner ratified the TTL
semantics (30-day default, per-site key, retroactive timestamp check,
re-confirm over rejection) after field testing surfaced that approvals
never lapsed - a March approval could publish in September. Implemented in
the v0.2.0 release session (2026-07-19), proven by verify-gates probe 8.
