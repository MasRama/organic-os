# Search Console and Analytics setup

organic-os never talks to Google Search Console or Google Analytics
directly. It calls whatever GSC/GA4 tools are already available in your
Claude environment and states plainly which ones it found. There are two
supported paths; use either one, or both.

## Path A: claude.ai connectors

Authorize the Search Console and Analytics connectors from your claude.ai
connector settings. This is the path with the widest reach: connectors
authorized this way are available in Claude Code, in Claude Cowork, and in
scheduled cloud runs (claude.ai scheduled tasks), because the authorization
lives on your account rather than on a single machine.

This is the recommended path if you plan to run routines on the
claude-scheduled runtime (see `docs/routines.md`) - a scheduled agent has no
access to anything running only on your laptop, so a local-only setup would
silently lose GSC/GA4 data on every scheduled run.

## Path B: a GSC/GA4 MCP server in Claude Code

If you already run a GSC or GA4 MCP server in your Claude Code setup (for
example an MCP server wired to a service account), organic-os calls it the
same way it would call a connector. This path works well for the local and
CI runtimes, where the MCP server runs alongside the CLI session. It is not
visible to claude.ai scheduled tasks, since those run in a hosted
environment separate from your machine.

## What organic-os does when neither is present

Nothing breaks. `hoo-daily` and the orchestrator skip the GSC/GA4 pull and
say so in the run's REPORT.md, and `hoo-keyword-intel` falls further down
its tier ladder (see `docs/credentials/google-ads-token.md`) to CSV import.
Setup asks about connectors once and records `available | absent | unknown`
in `site-profile.yaml` under `connectors:` - it never stores a token or
credential for either service, only the fact that a connector exists.

## Verifying which path is active

Ask the orchestrator or `hoo-daily` to run once in-session. The run's
REPORT.md states, per data source, whether it found a live GSC/GA4 tool and
which path it used. If both a connector and an MCP server are present,
organic-os uses whichever responds; there is no configured preference
between them.
