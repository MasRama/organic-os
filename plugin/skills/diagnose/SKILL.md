---
name: diagnose
description: Use to collect a bug-report diagnostic - "diagnose", "collect debug info", /organic-os:diagnose. Prints a report the user can paste into an issue; never transmits it anywhere.
---

# Diagnose (printed, never transmitted)

A support report the operator can read before anyone else does. This skill
PRINTS. It never sends, uploads, posts, mails, or opens an issue, and it has
no channel of its own. The operator decides whether any of it is pasted
anywhere.

Read-only over everything: no brain file is written, no profile is edited,
no connector is re-probed for the sake of this report.

Print this line first, before any collected value:

> Nothing below has been transmitted. organic-os collected it locally and
> printed it here. Read it, remove anything you would rather not share, then
> decide whether to paste it into an issue.

## What to collect

Resolve the brain: `registry.get_active()` when running interactively; a
scheduled run receives the brain path from the routine configuration. Every
item below is best-effort - a section that cannot be read prints
`unknown (<one-line reason>)` and the report continues. Missing information
is stated, never guessed.

1. **Runtime** - `platform.platform()` and `platform.python_version()`, plus
   which surface this is (Claude Code CLI or Cowork).
2. **PyYAML** - present or absent. Try the import; report the outcome, not a
   path or a version guess.
3. **Plugin version** - the `version` field in
   `plugin/.claude-plugin/plugin.json`.
4. **Brain schema** - `core.contracts.check_schema(brain_path)`: the version,
   whether it is compatible, and the action string it returns.
5. **Registry** - `core.registry.load()`: how many sites are registered and
   which slug is active. The active site's URL is fine to print; the other
   sites' URLs are not. Print the count, not the list.
6. **Connectors** - the profile's `connectors:` block, one line each: the
   name, the status (`verified` / `unavailable` / `declined`), the context
   the probe ran in (`local-cli`, `cowork-cloud`, `ci`), and the date it was
   checked. The context is the load-bearing part - a connector verified from
   an interactive session is not a claim about the runtime that runs the
   routines.
7. **Setup scorecard** - the newest `runs/*-setup-scorecard/REPORT.md` in the
   brain, if one exists: its date and the per-check status column. Say "no
   scorecard recorded" when there is none.
8. **Last routine outcome** - the newest `runs/<date>-*/REPORT.md` and its
   date, plus the tail of the runtime log if one exists
   (`~/.config/organic-os/routine-<name>.log`): whether the last run
   finished, and when.
9. **Recent error** - the most recent error line from that log or from the
   last run report, if any. One line, quoted as found.

## What never goes in

- **No credential values, ever.** A credential is reported as `present` or
  `absent` and nothing else. Do not read a token, a password, an env var
  value, or a keychain entry to confirm it - the existence of the file or
  the variable is the whole answer.
- **No full filesystem paths.** Relativise: print `~/organic-hq/<slug>` and
  `~/.config/organic-os/<file>`, never a real home directory. A path outside
  those shapes prints as `<custom path>` plus whether it exists.
- **No other site's URL** from the registry, and no per-site business data:
  no keywords, no signals, no item bodies. This is a report about the
  install, not about the site.

## Scan before printing

Assemble the whole report as text first. Then run
`core.redact.scan(report_text)`. If it returns findings, print
`core.redact.summarize(findings)` directly under the header, replace each
flagged span in the report with its masked excerpt, and name which section
carried it.

State the limit in the same breath: the scan is ADVISORY. It reports; it
does not block and it does not prevent a leak. A high-tier finding means
something credential-shaped reached the assembled report, which is a reason
to rotate that credential and to check what put it there, not a sign the
guard held. If the scan itself fails, print the report anyway with one line
saying the scan did not run - the operator reading their own output is the
control that matters.

## Then stop

Print the report and end. Do not offer to file it, do not send it through
the approval channel, and do not write it into the brain. If the operator
wants it in an issue, they paste it themselves - see
[SUPPORT.md](../../../SUPPORT.md).
