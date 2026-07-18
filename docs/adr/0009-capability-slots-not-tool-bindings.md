# ADR-0009: Capability slots, not tool bindings

- Status: accepted
- Date: 2026-07-19
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
organic-os depends on external tools at several points: GA4 for analytics,
Google Ads and GSC for search data, Canva for featured images, Telegram
for approvals, WordPress for writes, IndexNow for indexing pings. During
the v0.2.0 review the owner flagged a risk in how those dependencies were
accumulating: fixes and features were being framed per tool ("the Telegram
expiry path", "the Canva step") rather than per capability, which is the
first step toward contract logic that knows tool names and adapters that
cannot be swapped without touching the gate. The expiry work made the
right call by accident of design (the TTL lives in the contract, so every
channel got it for free); this ADR makes that shape the rule.

## Decision
Every external dependency belongs to a named capability slot, with tools
as swappable adapters behind it. The slots: **analytics**, **search-data**,
**image-generation**, **approval-channel**, **cms**, and **indexing**.
Three rules follow:

1. Contract and gate logic must never reference a specific tool. The gate
   knows "an approval was recorded through the configured
   approval-channel"; it never knows "Telegram".
2. Skills reference the slot and name the configured adapter from the
   site profile at runtime, not in their fixed text. "Pull sessions from
   the analytics adapter (GA4 for this site)", not "pull sessions from
   GA4".
3. A new tool is an adapter addition, never a rewrite. Microsoft Clarity
   joins as a second analytics adapter; Gemini joins as a second
   image-generation adapter. Neither touches contract code, and neither
   forks a skill.

## Consequences
- Adding a CMS, an analytics source, or an approval channel is a new
  adapter file plus a site-profile entry - the v0.3 adapter items all
  inherit this shape instead of each inventing its own.
- Cost: adapter indirection adds a naming layer. Every slot needs a name,
  a documented interface, and a site-profile key, which is more ceremony
  than calling a tool directly.
- Cost: some current skill text names tools directly ("GA4", "Canva",
  "Telegram") where the slot name should appear. Those files will be
  normalized as they are next touched - a deliberate incremental
  migration, not a big-bang rewrite, because the text is descriptive
  today and none of it sits in contract or gate logic.
- Reviews get a new question to ask of any change: does this bind a
  capability to a tool, or an adapter to a slot? Only the second is
  accepted.

## Agent Context
Proposed after the owner flagged the risk of channel-specific and
tool-specific fixes during the v0.2.0 review: approval expiry had shipped
correctly channel-neutral, but only because the TTL happened to live in
the contract layer, and nothing yet stated that this is the required
shape for every external dependency. Recorded in the v0.2.1 session
(2026-07-19) alongside the channel-neutral expiry documentation.
