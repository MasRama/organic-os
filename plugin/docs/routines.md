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
| claude.ai scheduled tasks (recommended default) | Anthropic-hosted scheduled agent clones the brain repo, runs the skill, pushes, notifies | Included in your Claude subscription usage; no API key, no infra to run | Marketers who want zero setup, and whose brain repo is public or otherwise reachable without personal GitHub auth (see the honesty box below) |
| Local schedule | Claude Code on your own machine, invoked by `launchd` (macOS) or a `systemd` timer / cron (Linux) | Subscription usage; your machine has to be on at the scheduled time | Privacy-first users, private brain repos, anyone who wants local MCP servers or SSH-based connectors in the run |
| CI (GitHub Actions) | A headless `claude -p` job on a cron schedule | An API key, billed per token - separate from your Claude subscription | Teams, fully cloud-native setups |
| Manual | You run `/organic-os:daily` etc. yourself | Subscription usage, whenever you run it | Trying the plugin out before committing to a schedule |

## The cost ledger

The wrapper (`plugin/runtime/run-routine.sh`) records what each run
actually cost: one row per run appended to
`~/.config/organic-os/cost-ledger-YYYYMM.tsv` (one file per month), with
four tab-separated columns - date, routine, duration in seconds, and the
run's token count when the CLI's JSON output reports one. When the CLI
version does not expose usage fields, the row says "usage unavailable in
this CLI version" instead of a guessed number.

Read the token column against the cost-model column above. On
subscription runtimes (claude.ai scheduled tasks, local, manual), tokens
are counted but not billed per token - the ledger shows how much of your
plan's usage a routine consumes, not a bill. On the CI runtime, tokens are
money: the same rows are per-run spend to reconcile against your API
invoice.

What the ledger cannot capture: runs that never pass through the wrapper.
claude.ai scheduled tasks execute in Anthropic's cloud without it, and the
sample CI workflow below calls `claude -p` directly - neither produces a
ledger row unless you route the run through the wrapper. The Monday report
(`hoo-monday-report`) reads the ledger when it exists and adds a one-line
cost summary to its "What moved" section; when the ledger is absent, the
report simply carries no cost line.

This page was rewritten after a first real local-runtime install surfaced
five failure modes that the original version did not warn about (headless
auth, model aliases, slash-command expansion, TCC file permissions, and the
wrong scheduler). Everything below reflects that field experience, not just
the design intent.

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
servers) - see the connector note in `plugin/docs/credentials/gsc-ga4.md`.

Honest cost: this runs on your existing Claude subscription's usage, the
same as any other scheduled agent task. There is no separate billing and no
infrastructure to maintain, but usage still counts against your plan the
same as an equivalent interactive session would.

**What a cloud scheduled session cannot do.** The `claude-scheduled` runtime
runs in Anthropic's cloud, not on your machine, so it does not have:

- **Your personal GitHub auth.** If the brain repo is private, the
  scheduled agent cannot clone or push to it unless you provision a
  credential it can use on its own - a deploy key or a machine-user token
  stored where the scheduled task can read it. There is no "borrow your
  logged-in session" option.
- **Your local env file secrets.** `~/.config/organic-os/<slug>.env` never
  leaves your machine. Google Ads tokens, the WordPress application
  password, Telegram bot tokens - none of it is visible to a cloud
  scheduled run unless you re-provision it as a secret the scheduled
  agent can reach.
- **Desktop-bridged connectors.** Any MCP server that runs through the
  Cowork device bridge or a local process is local by construction; a
  cloud session cannot reach it.

If you are not willing to provision a deploy key and cloud-side secret
storage for a private brain, pick **local** or **CI** instead - both run
somewhere that already has (or can be given) that access. Say this plainly
during setup rather than letting a scheduled task fail silently on its
first real run.

## Local schedule - macOS (primary recipe)

**Use `launchd`, not `cron`.** `cron` is not the right tool on a modern
Mac: the daemon is throttled and can be skipped under App Nap or low-power
states, and every `cron` job needs Full Disk Access granted to
`/usr/sbin/cron` itself, which almost nobody grants. `launchd` is the
OS-native scheduler with no such restriction. `plugin/runtime/` ships the
assets for this: a wrapper script and three plist templates.

Walkthrough (full detail and troubleshooting in
`plugin/runtime/README.md`):

1. **Get a headless auth token.**

   ```
   claude setup-token
   ```

   Interactive `claude login` stores credentials in the macOS keychain,
   which a non-interactive shell cannot reach - a `launchd`-invoked
   `claude -p` fails with `Invalid API key - Please run /login` without
   this step. Add the resulting value to your site's env file:

   ```
   CLAUDE_CODE_OAUTH_TOKEN=<token from claude setup-token>
   ```

2. **Copy and configure the wrapper.**

   ```
   mkdir -p ~/.config/organic-os
   cp plugin/runtime/run-routine.sh ~/.config/organic-os/run-routine.sh
   chmod +x ~/.config/organic-os/run-routine.sh
   ```

   Edit the copy and substitute its `SITE_SLUG` and `BRAIN_PATH`
   placeholders.

3. **Substitute the plist placeholders.** `launchd` plists cannot expand
   `$HOME` or any shell variable, so every `/Users/YOUR_USERNAME/...` path
   in `plugin/runtime/launchd/*.plist` has to become your real home
   directory (`echo $HOME`) before use.

4. **Load it.**

   ```
   cp plugin/runtime/launchd/com.organic-os.daily.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.organic-os.daily.plist
   ```

   Repeat for `weekly` and `monthly` if you want them scheduled too.

5. **Kick off a test run immediately** rather than waiting for the
   schedule:

   ```
   launchctl kickstart -k gui/$(id -u)/com.organic-os.daily
   ```

6. **Verify by commit hash**, not just "the log looks fine":

   ```
   tail -f ~/.config/organic-os/routine-daily.log
   cd ~/organic-hq/<slug> && git log -1 --format='%h %s'
   ```

   A fresh commit with today's date confirms the entire chain worked -
   token, env file, brain path, skill invocation, and push - not just that
   `claude -p` exited zero.

### Hard requirement: `claude setup-token`

Any non-interactive runtime - `launchd`, `systemd`, cron, CI - needs this.
Keychain-based OAuth from `claude login` only works in an interactive
shell with access to the logged-in user's keychain; a headless process
does not have that access and `claude -p` fails immediately with
`Invalid API key - Please run /login`. Run `claude setup-token` once,
store the resulting value in the site env file as
`CLAUDE_CODE_OAUTH_TOKEN`, and every runtime that sources that env file
picks it up automatically.

### Invocation rule: pass the command body, not a slash string

`claude -p "/organic-os:daily"` does not reliably expand plugin slash
commands in a headless run - the plugin may not be resolved the same way
it is in an interactive session, and the call can silently no-op or error.
Pass the command's underlying instruction text instead:

```
claude -p "Invoke the organic-os:hoo-daily skill and follow it end to end. When finished, stage, commit, and push all changes to git." --permission-mode bypassPermissions
```

This is exactly what `plugin/runtime/run-routine.sh` does - the wrapper is
the reference implementation of this rule, not just an example of it.

### Model-404 recovery

**Symptom:** `claude -p` fails with a 404 on the model, even though the
same alias works fine interactively.

**Cause:** CLI model aliases (`sonnet`, `opus`, etc.) can resolve to a
model that has since been retired. Interactive sessions sometimes redirect
around this more gracefully than a headless `-p` call does.

**Fix:** list the models available to your token and pin the current one
explicitly, rather than relying on an alias:

```
curl https://api.anthropic.com/v1/models -H "x-api-key: $CLAUDE_CODE_OAUTH_TOKEN" -H "anthropic-version: 2023-06-01"
```

List models with your token and pin the newest one by adding both of the
following to the site env file:

```
ANTHROPIC_MODEL=<newest model id from the list above>
ANTHROPIC_SMALL_FAST_MODEL=<newest fast/small model id from the list above>
```

Re-run the routine after adding these. This turns a silent alias-drift
failure into an explicit, version-pinned config you control.

### TCC warning: brain path

**Symptom:** `launchd` (or cron) logs show `error: unable to create
'.git/index.lock': Operation not permitted` even though the same `git`
commands work fine when you run them yourself in Terminal.

**Cause:** macOS Transparency, Consent, and Control (TCC) silently blocks
non-interactive processes - `launchd` jobs and cron jobs specifically -
from writing inside `~/Documents`, `~/Desktop`, and `~/Downloads`, even
when the interactive Terminal app has full access to those same folders.
There is no prompt and no log line explaining this; the write just fails.

**Fix:** never place a brain repo inside `~/Documents`, `~/Desktop`, or
`~/Downloads` if it will run under a local runtime. The default
`~/organic-hq/<slug>` is outside all three and is safe.
`/organic-os:setup` runs an automated check on the brain path you choose
and warns (defaulting the suggestion to `~/organic-hq/<slug>`) before it
scaffolds anything there.

## Local schedule - Linux

The same wrapper pattern applies; swap the scheduler. A `systemd` user
timer is the closest Linux equivalent of the macOS `launchd` recipe above
(no TCC-equivalent restriction to work around):

```ini
# ~/.config/systemd/user/organic-os-daily.service
[Service]
Type=oneshot
ExecStart=/bin/bash %h/.config/organic-os/run-routine.sh daily
```

```ini
# ~/.config/systemd/user/organic-os-daily.timer
[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```
systemctl --user enable --now organic-os-daily.timer
```

Or, if you would rather keep it simple, a `cron` line calling the same
wrapper works fine on Linux (unlike macOS, there is no TCC restriction
blocking it):

```
0 8 * * * /bin/bash $HOME/.config/organic-os/run-routine.sh daily
```

Both still need `claude setup-token` and the same `CLAUDE_CODE_OAUTH_TOKEN`
/ `ANTHROPIC_MODEL` env vars described above - the auth and model-pinning
requirements are not macOS-specific.

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
          CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
        run: claude -p "Invoke the organic-os:hoo-daily skill and follow it end to end. Notify per the profile channel." --output-format text --permission-mode bypassPermissions
      - name: Commit and push
        run: |
          git config user.name "organic-os-bot"
          git config user.email "actions@users.noreply.github.com"
          git add -A
          git diff --cached --quiet || git commit -m "chore(organic-os): daily routine $(date -u +%F)"
          git push
```

Duplicate the job per cadence (weekly, monthly) with the matching cron
expression and skill name (`hoo-weekly`, `hoo-monthly-audit`), or use
`anthropics/claude-code-action` in place of the manual `npm install` +
`claude -p` steps if you prefer a maintained action wrapper.
`CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`, same as the local
runtime) is a repo or org secret, never committed. The slash-command
caveat above applies here too - the workflow passes the skill instruction
directly rather than `/organic-os:daily`.

Honest cost: this is the only runtime billed outside your Claude
subscription - an API key billed per token, separate from subscription
usage. For a single site running daily/weekly/monthly routines this is
typically a small, predictable spend, but it is real spend, unlike the
other three runtimes.

## Manual

Setup: none. Run `/organic-os:daily`, `/organic-os:weekly`, or
`/organic-os:monthly-audit` yourself, whenever you want, in an interactive
Claude Code session. This is what setup defaults to if you skip the
runtime question, and it is a fine permanent choice if you would rather
stay hands-on than schedule anything. The slash-command caveat above is
specific to headless `claude -p` calls; typed slash commands in an
interactive session expand normally.

Honest cost: subscription usage, only when you actually run something.

## Choosing

`/organic-os:setup` asks "where should routines run?" and, based on the
answer, either registers the claude.ai scheduled tasks for you (after
stating the honesty box above if the brain repo is private), points you at
`plugin/runtime/` for macOS `launchd`, prints the `systemd`/cron
equivalent for Linux, writes the GitHub Actions workflow into the brain
repo, or leaves routines manual. You can change runtimes later by
re-running setup or editing `site-profile.yaml runtime: mode` directly.
