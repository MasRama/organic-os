# organic-os local runtime (macOS launchd)

Templates for running organic-os routines unattended on a Mac, driven by
`launchd` (not `cron` - see below). This is the recipe `plugin/docs/routines.md`
walks through in full; this file is the quick reference for the files
themselves.

Contents:

- `run-routine.sh` - the wrapper `launchd` calls. Sources your env file, cds
  into the brain repo, invokes the routine's skill headlessly via
  `claude -p`, then commits and pushes whatever changed.
- `launchd/com.organic-os.daily.plist` - daily at 08:00.
- `launchd/com.organic-os.weekly.plist` - Mondays at 08:30.
- `launchd/com.organic-os.monthly.plist` - the 1st of the month at 09:00.

## Why launchd, not cron

`cron` on modern macOS is not reliably scheduled (the daemon is throttled
and can be skipped entirely under App Nap / low-power states) and every
`cron` job needs Full Disk Access granted to `/usr/sbin/cron` itself, which
most users never grant. `launchd` is the OS-native scheduler, does not have
that restriction, and is what Apple actually runs its own periodic jobs
through. Use `launchd`.

## Setup

1. **Get a headless auth token.** Interactive `claude login` stores
   credentials in the macOS keychain, which a `launchd` job has no access to
   (headless shells fail with `Invalid API key - Please run /login`). Run:

   ```
   claude setup-token
   ```

   and add the resulting value to your site's env file as
   `CLAUDE_CODE_OAUTH_TOKEN=...`. Full detail, including the model-pinning
   step this often surfaces, in `plugin/docs/routines.md`.

2. **Copy the wrapper script** into place (do not symlink - `launchd`
   should not depend on this repo checkout still existing at the same
   path):

   ```
   mkdir -p ~/.config/organic-os
   cp plugin/runtime/run-routine.sh ~/.config/organic-os/run-routine.sh
   chmod +x ~/.config/organic-os/run-routine.sh
   ```

3. **Substitute the placeholders** in your copy of
   `~/.config/organic-os/run-routine.sh`:
   - `SITE_SLUG` -> your site's slug (matches the env file name already at
     `~/.config/organic-os/<slug>.env`).
   - `BRAIN_PATH` -> the absolute path to the brain repo, e.g.
     `$HOME/organic-hq/<slug>`.

   **TCC warning:** the brain path must NOT be under `~/Documents`,
   `~/Desktop`, or `~/Downloads`. macOS Transparency, Consent, and Control
   (TCC) silently blocks `launchd` (and `cron`) processes from writing
   inside those folders - `git commit` fails with `error: unable to create
   '.git/index.lock': Operation not permitted`, and nothing in the
   terminal warns you ahead of time because it only applies to
   non-interactive processes. The default `~/organic-hq/<slug>` is outside
   all three and is safe. `/organic-os:setup` checks this for you and
   warns before scaffolding a brain in a protected location.

4. **Substitute the placeholders** in each plist you plan to use (`Label`
   stays as-is; every `/Users/YOUR_USERNAME/...` path needs your real home
   directory - `launchd` plists cannot expand `$HOME` or any other shell
   variable):

   ```
   echo $HOME   # copy this value into each plist by hand
   ```

5. **Install and load** the plists you want:

   ```
   cp plugin/runtime/launchd/com.organic-os.daily.plist ~/Library/LaunchAgents/
   cp plugin/runtime/launchd/com.organic-os.weekly.plist ~/Library/LaunchAgents/
   cp plugin/runtime/launchd/com.organic-os.monthly.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.organic-os.daily.plist
   launchctl load ~/Library/LaunchAgents/com.organic-os.weekly.plist
   launchctl load ~/Library/LaunchAgents/com.organic-os.monthly.plist
   ```

6. **Test one run immediately** instead of waiting for the schedule:

   ```
   launchctl kickstart -k gui/$(id -u)/com.organic-os.daily
   ```

7. **Verify.** Tail the log and confirm a new commit landed in the brain
   repo:

   ```
   tail -f ~/.config/organic-os/routine-daily.log
   cd ~/organic-hq/<slug> && git log -1 --format='%h %s'
   ```

   A fresh `chore(routine): daily <date>` commit (or a commit the skill
   itself made) confirms the whole chain worked: token, env file, brain
   path, skill invocation, and push.

## Uninstall / pause

```
launchctl unload ~/Library/LaunchAgents/com.organic-os.daily.plist
rm ~/Library/LaunchAgents/com.organic-os.daily.plist
```

Repeat per routine. Unloading stops future runs; it does not touch the
brain repo or your env file.
