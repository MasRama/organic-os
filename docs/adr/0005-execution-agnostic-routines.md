# ADR-0005: Execution-agnostic routines

- Status: accepted
- Date: 2026-07-18
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
organic-os routines (daily signal pull, weekly reflection, monthly audit,
per-publish measurement) need to run on a schedule, but installers differ
widely: some want zero infrastructure, some run Claude Code locally, some
already operate CI, and some just want to trigger a run by hand.

## Decision
Cadences are declared once in the site repo (`site-profile.yaml routines:`
block) as data, not as code tied to a scheduler. The runtime that executes
them is chosen by the installer at setup from four options: claude.ai
scheduled tasks (default), a local OS schedule via Claude Code, CI (GitHub
Actions), or manual invocation. The setup skill emits the exact configuration
for whichever runtime is chosen; no scheduler is hardcoded into the skills
themselves.

## Consequences
- Skills work identically regardless of what triggers them, since they read
  the same declarative cadence and detect what is reachable (connectors,
  SSH, local repo versus clone) at run time.
- Zero-infrastructure installers get a working default (claude.ai scheduled
  tasks) with no API key and no server to maintain.
- Cost: four runtimes mean four sets of setup instructions and four
  degradation paths to test and keep working as the plugin evolves.
- Runtime choice is a setup-time decision recorded in `site-profile.yaml`;
  changing runtimes later means re-running part of setup, not just editing a
  cron line.

## Agent Context
Proposed by the agent from research evidence; approved by the human in the
2026-07-18 design session, from its "Routines and runtimes
(execution-agnostic)" analysis.
