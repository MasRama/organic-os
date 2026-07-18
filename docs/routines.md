# Routines and runtimes

A routine (daily signal pull, weekly reflection, monthly deep audit,
per-publish measurement at day 7/28) is a declarative cadence recorded in
`site-profile.yaml routines:`. The *runtime* - what actually invokes the
skill on that cadence - is a separate, installer-chosen decision. Skills are
runtime-agnostic: they detect what is reachable (connectors, SSH, a local
repo vs. a freshly cloned one) and degrade per the capability notes below,
regardless of which runtime called them.

| Runtime | How it runs | Cost model | Best for |
|---|---|---|---|
| claude.ai scheduled tasks (recommended default) | Anthropic-hosted scheduled agent clones the brain repo, runs the skill, pushes, notifies | Included in your Claude subscription usage; no API key, no infra to run | Marketers who want zero setup |
| Local schedule | Claude Code on your own machine, invoked by the OS scheduler or `/loop` | Subscription usage; your machine has to be on at the scheduled time | Privacy-first users, or anyone who does not want a brain repo on GitHub |
| CI (GitHub Actions) | A headless `claude -p` (or the Agent SDK) job on a cron schedule | An API key, billed per token - separate from your Claude subscription | Teams, fully cloud-native setups |
| Manual | You run `/organic-os:daily` etc. yourself | Subscription usage, whenever you run it | Trying the plugin out before committing to a schedule |

## claude.ai scheduled tasks

Setup: create a scheduled task with the exact prompt the routine needs, one
task per cadence. For example:

```
Open <brain repo>. Run /organic-os:daily. Commit and push. Notify per the profile channel.
```

Repeat for `/organic-os:weekly` (weekly cadence) and
`/organic-os:monthly-audit` (monthly cadence). The scheduled agent clones
(or re-opens) the brain repo fresh each run, so it only sees connectors
authorized at the account level (claude.ai connectors, not local MCP
servers) - see the connector note in `docs/credentials/gsc-ga4.md`.

Honest cost: this runs on your existing Claude subscription's usage, the
same as any other scheduled agent task. There is no separate billing and no
infrastructure to maintain, but usage still counts against your plan the
same as an equivalent interactive session would.

## Local schedule

Setup: add a crontab line that invokes Claude Code non-interactively against
the brain repo, for example:

```
0 7 * * * cd ~/organic-hq-yoursite && claude -p "Run /organic-os:daily. Commit and push." >> ~/organic-os-daily.log 2>&1
```

Adjust the schedule per routine (daily/weekly/monthly cadence, per your
`site-profile.yaml`). This runtime sees everything the local machine sees -
local MCP servers, SSH access for WP-CLI, anything installed on that box -
which is the local runtime's main advantage over claude-scheduled.

Honest cost: subscription usage only, same as running the command
yourself, but the routine only fires if the machine is on, awake, and not
asleep/suspended at the scheduled minute. There is no server-side retry if
it is not.

## CI (GitHub Actions)

Setup: add a workflow to the brain repo (not to organic-os itself) that
checks it out, runs the skill headlessly, and pushes any changes back. A
complete starting workflow:

```yaml
name: organic-os-daily
on:
  schedule:
    - cron: "0 1 * * *"   # 07:00 IST
  workflow_dispatch: {}
jobs:
  daily:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code
      - name: Run the daily routine
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: claude -p "Run /organic-os:daily. Notify per the profile channel." --output-format text
      - name: Commit and push
        run: |
          git config user.name "organic-os-bot"
          git config user.email "actions@users.noreply.github.com"
          git add -A
          git diff --cached --quiet || git commit -m "chore(organic-os): daily routine $(date -u +%F)"
          git push
```

Duplicate the job per cadence (weekly, monthly) with the matching cron
expression and skill invocation, or use `anthropics/claude-code-action` in
place of the manual `npm install` + `claude -p` steps if you prefer a
maintained action wrapper. `ANTHROPIC_API_KEY` is a repo or org secret,
never committed.

Honest cost: this is the only runtime billed outside your Claude
subscription - an API key billed per token, separate from subscription
usage. For a single site running daily/weekly/monthly routines this is
typically a small, predictable spend, but it is real spend, unlike the
other three runtimes.

## Manual

Setup: none. Run `/organic-os:daily`, `/organic-os:weekly`, or
`/organic-os:monthly-audit` yourself, whenever you want. This is what setup
defaults to if you skip the runtime question, and it is a fine permanent
choice if you would rather stay hands-on than schedule anything.

Honest cost: subscription usage, only when you actually run something.

## Choosing

`/organic-os:setup` asks "where should routines run?" and, based on the
answer, either registers the claude.ai scheduled tasks for you, prints the
crontab lines to add locally, writes the GitHub Actions workflow into the
brain repo, or leaves routines manual. You can change runtimes later by
re-running setup or editing `site-profile.yaml runtime: mode` directly.
