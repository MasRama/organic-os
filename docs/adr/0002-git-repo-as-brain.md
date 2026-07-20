# ADR-0002: Git repo as the per-site brain

- Status: accepted
- Date: 2026-07-18
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
organic-os needs persistent memory per site: signals, a curated skillbook,
decisions, and approval history, so the loop compounds across daily, weekly,
and monthly routine runs instead of resetting each session. Not every
installer has a GitHub account or wants cloud-hosted routines.

## Decision
The per-site memory lives in a git repo (the "brain"): `site-profile.yaml`,
`signals/`, `skillbook.md`, `decisions/` (ADRs), `approvals/`, `briefs/`, and
`outcomes/`. A local-folder mode with the same file layout but no git remote
is supported for users who decline GitHub, with routines then limited to the
local-schedule runtime.

## Consequences
- Cloud runtimes (claude.ai scheduled tasks, CI) work because the brain is a
  clone-able, push-able repo; the loop's state travels with the repo, not
  with a chat session.
- Every decision and skillbook change is versioned and diffable, so a bad
  automated edit is a revert, not data loss.
- Cost: full power, meaning cloud scheduling, PR-merge approvals, and
  multi-machine access, needs git and, in most setups, a GitHub account;
  local-folder mode is a deliberate downgrade, not a substitute.
- The repo must never hold secrets; credentials stay in platform-native
  storage and the repo stores only references to which credentials exist.

## Agent Context
Proposed by the agent from research evidence; approved by the human in the
2026-07-18 design session, from its "The site repo (the brain)" analysis and
its execution-agnostic routines-and-runtimes design.
