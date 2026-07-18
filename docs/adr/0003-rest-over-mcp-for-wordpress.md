# ADR-0003: WordPress REST API over MCP for the write path

- Status: accepted
- Date: 2026-07-18
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
onsite-optimizer needs a write path into WordPress for SEO meta, schema, and
publishing. Two candidate paths exist: the WordPress REST API with
Application Passwords, or the community WordPress/mcp-adapter project exposed
as an MCP server. RankMath, the target SEO plugin, does not register its meta
fields for REST by default.

## Decision
Use the WordPress REST API with Application Passwords over HTTPS as the write
path, paired with a bundled mu-plugin (or the Devora rank-math-api-manager
plugin) that registers the RankMath meta keys and a custom `agent_jsonld`
field for schema. WordPress mcp-adapter is installed on the playground as an
experiment only and is not load-bearing: it ships read-only core abilities as
of 2026-07-18 and is pre-1.0. Revisit MCP as the primary path once
mcp-adapter reaches 1.0.

## Consequences
- REST plus Application Passwords works on any WordPress install today, with
  no dependency on a pre-1.0 project's roadmap.
- The RankMath meta bridge is a small, auditable surface (one mu-plugin or
  one small third-party plugin) rather than a full MCP server footprint.
- Cost: read-back verification is required after every apply, since REST
  writes can bypass plugin-side validation that an MCP tool call might
  otherwise route through.
- Switching to mcp-adapter later means re-plumbing the write path inside
  onsite-apply and onsite-publish; the REST contract is kept swappable
  behind `lib/onsite`.

## Agent Context
Proposed by the agent from research evidence; approved by the human in the
2026-07-18 design session. Evidence: WordPress/mcp-adapter status research
2026-07-18.
