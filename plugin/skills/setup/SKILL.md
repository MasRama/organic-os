---
name: setup
description: Use when the user installs organic-os, says "set up organic-os", "onboard my site", "connect my website", "add another website", "switch site", "organic-os status", or runs /organic-os:setup or /organic-os:sites. Interviews the user, scaffolds the per-site brain repo, runs the connector wizard with live verification, records credentials one at a time, registers routines for the chosen runtime, ends with a tested postflight scorecard, and manages the multi-site registry (add / update / switch / status).
---

# organic-os setup

You are onboarding or managing sites in organic-os. Everything site-specific
comes from this interview. Never assume; ask. One question at a time,
AskUserQuestion with options where possible.

Two claims matter and they are not the same: "configured" (an answer was
recorded) and "verified working" (a live probe proved it). Setup collects
both, but only ends on the second - see Postflight scorecard.

## Interview style (every mode, every question)

- **One question at a time.** Never present a wall of questions. Ask, wait
  for the answer, then ask the next one.
- **Offer a default with every question.** State it plainly ("default: none
  - press enter to skip") so the user can move fast when they do not care.
- **Show progress.** Prefix each question with where the user is - "question
  4 of 12" for the full first-run interview, "question 2 of 3" for
  quick-start, "question 1 of 2" for a targeted update-mode re-ask.
- **End with a summary table.** After the last question and the scaffold/
  write actions, print a table of what was written and where (file path,
  field, value) so the user can see the whole result of the interview in one
  place before they move on. The postflight scorecard (below) comes after
  this table, not instead of it.

## Step 0: environment checks

- Confirm `python3` is on PATH.
- Confirm PyYAML is importable: `python3 -c "import yaml"`. If this fails,
  tell the user to run `python3 -m pip install --user pyyaml` before
  continuing - both `core.contracts` and `core.registry` require it.

## Step 0.5: where am I, where will routines run

Setup may be running in a different environment than the one routines will
execute in - most commonly a cloud Cowork session setting up a `local`
runtime that lives on the user's Mac. Work this out before touching any
file, because it changes where almost everything below gets written.

1. **Determine the setup environment.** No single signal is proof by
   itself; weigh them together, and ask if still unsure:
   - `ls ~/.config/organic-os 2>/dev/null` and `test -f ~/.claude.json` -
     a fresh cloud sandbox rarely carries config from a prior local run.
   - `gh auth status 2>&1` - a cloud sandbox is almost always
     unauthenticated; a local CLI session the user has used before usually
     is not.
   - macOS Keychain probe (local-only signal): `security find-generic-
     password -s "Claude Code-credentials" 2>&1` - a cloud sandbox has no
     keychain, so this errors immediately or the command is unavailable.
   - If the signals disagree or nothing is conclusive: ask plainly, "Are
     you running this in a local terminal on your own machine, or a
     cloud / Cowork session?"
2. **Ask which runtime will execute routines** (unless the caller already
   established this): claude-scheduled | local | ci | manual - same
   options as interview question 11 below. If answered here, do not
   re-ask it later; carry it forward.
3. **If setup environment and runtime location match** (e.g. a local CLI
   session setting up a local runtime), continue normally - every step
   below writes directly where it says it does.
4. **If they differ**, say so out loud to the user before continuing, then
   hold to these three rules for the rest of the session:
   - **Registry and brain scaffold target the runtime location, not the
     setup session.** If setup has no way to write files on the runtime
     machine directly (no bridge shell reaching it), do not fake success.
     Emit a ready-to-run snippet - one bash block covering
     `init_site_repo.py`, `core.registry.register(...)`, and `git init` -
     for the user to paste into a terminal on the runtime machine. Record
     this row in the summary table as "handed off, not yet confirmed" and
     let the postflight scorecard be the thing that actually confirms it
     landed.
   - **Connector probes are labeled with the context that actually ran
     them.** Every `core.contracts.record_connector(...)` call passes the
     real context - `cowork-cloud` for a probe this session ran itself,
     `local-cli` for one the user ran locally and reported back, `ci` for
     a CI runner. A connector reachable from the setup session is not
     "available" for a runtime that cannot reach it - never blur the two.
     Say plainly that the runtime-side probe (which the postflight
     scorecard runs, or asks the user to run and report) is the one that
     actually matters for routines.
   - **Never run git through a device bridge.** If setup is bridging
     commands into the user's local machine, use the bridge only to
     scaffold files. `git init`, the first commit, and `gh repo create`
     happen natively - hand the user the exact commands and let them run
     in their own terminal. A bridge-proxied git init tends to write with
     the wrong identity or permissions, and it proves nothing about
     whether the runtime machine can push on its own.

## Step 1: read the registry, pick a mode

Read `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -c "..."` calling
`core.registry.load()` (default path `~/.config/organic-os/sites.yaml`,
resolved at the runtime location per Step 0.5 when it differs from the
setup session).

- **Registry empty** (no sites): if the caller (e.g. `start`) already
  established which mode the user picked, go straight to that mode below.
  Otherwise ask first, AskUserQuestion with options:
  - `Quick start (3 questions, sensible defaults, ~2 minutes)` - go to the
    quick-start interview below.
  - `Full setup (the complete interview)` - go to the first-run interview
    below.
- **Sites exist**: ask the user what they want, AskUserQuestion with options:
  - `update <active site name>` - refresh the currently active site's profile
  - `add another website` - onboard a new site (full interview, own brain path)
  - `switch active site` - change which site routines/commands act on
  - `show status` - print the registry (all sites, which is active) plus the
    active site's site-profile.yaml summary, and the latest postflight
    scorecard summary line if one exists (see Postflight scorecard); no
    writes

### Update mode

1. READ the existing `site-profile.yaml` for the active site first. Present
   the current values back to the user.
2. Schema check: run `core.contracts.check_schema(brain_path)`. If
   `action: "stamp"`, the profile predates versioning - add
   `schema_version: 1` at the top of the file, unchanged otherwise, before
   doing anything else, and tell the user this is the migration entry
   point (this is where a future major version's migration steps would run
   too). If `compatible: false` for any other reason, relay the action
   string and stop before re-asking anything.
3. Re-ask **only** the sections the user picks (site, brand, audience,
   keywords, competitors, connectors, Google Ads, WordPress, approval
   channel, runtime). Do not re-run the full interview. If the user picks
   "connectors," run the Connector wizard below rather than a plain
   available/absent question. If the user picks "WordPress" or "approval
   channel" and it needs a new secret, run it through Credentials below.
4. Rewrite `site-profile.yaml` with just those changes.
5. Skillbook: NEVER re-append an operator note unless its text is new - read
   `skillbook.md` first, skip anything that already matches an existing
   entry's text.
6. NEVER touch `signals/`, `decisions/`, `reflections/`, or existing
   skillbook entries beyond the dedup check above - those are memory, not
   config, and setup does not rewrite memory.
7. Do not re-register routines unless the user explicitly asks to change
   cadence or runtime.
8. If any of connectors, WordPress, approval channel, or runtime changed,
   re-run just those rows of the Postflight scorecard (below) and show the
   updated table - do not force a full scorecard re-run for an update that
   only touched brand voice or keywords.
9. **Rule of thumb to state to the user: config is editable, memory is not.**
   `site-profile.yaml` and the registry are safe to change anytime; anything
   already written under signals/decisions/reflections/outcomes/skillbook
   stays as a historical record.

### Add mode

Run the full interview below with a fresh brain path (never reuse another
site's brain). After scaffolding, call `core.registry.register(url, name,
brain_path)` - this both records the site and makes it the active one.

### Switch mode

Ask which registered site (list slugs + names + urls from the registry), then
`core.registry.set_active(slug)`. No file other than the registry changes.

### Show status

Print, without writing anything: every registered site (slug, name, url,
brain path), which one is active, and - for the active site - whether its
site-profile.yaml, skillbook.md, and approvals/queue.md exist, a one-line
summary of each, and the latest postflight scorecard summary line (see
Postflight scorecard) if a `runs/*-setup-scorecard/REPORT.md` exists.

## Quick-start interview (3 questions, ~2 minutes)

Everything not asked here gets a stated default, not a silent one - tell the
user what was defaulted in the closing summary table so nothing is a
surprise later.

1. Site URL. (No default - this is the one thing quick-start cannot guess.)
2. Brand name + a one-line voice note ("how should this sound - direct,
   playful, formal?"). Default: brand name guessed from the URL's domain
   label, voice note left blank.
3. Approval channel: in-session | telegram | slack | email | pr-merge.
   Default: in-session - no setup required, works immediately.

Defaulted silently (state each one in the summary table, do not ask):

- **Geos**: inferred from the URL's TLD (`.in` -> `IN`, `.co.uk` -> `GB`,
  a generic `.com`/`.io`/etc. -> left empty). Never asked in quick-start.
- **Keywords, competitors, operator notes**: left empty. Note in the summary
  that they can be filled in later via `/organic-os:setup` update mode.
- **Connectors, Google Ads, WordPress**: left `unknown`/`none`/unconnected.
  Quick-start never runs the Connector wizard and never probes connectors -
  analysis-only is the correct default outcome for a 2-minute setup.
- **Runtime**: `manual`. The user runs commands themselves until they choose
  to schedule routines (`$CLAUDE_PLUGIN_ROOT/docs/routines.md`).
- **Brain path**: `~/organic-hq/<slug>`, same derivation as full setup.
- **Brain mode**: `local` (no git init, no GitHub repo offer). Quick-start
  optimizes for "see something work in two minutes," not for versioned
  memory from the first run - the user can move to a git brain later via
  update mode if they want it.

### Actions after the quick-start interview

1. Run: `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 "$CLAUDE_PLUGIN_ROOT/lib/core/init_site_repo.py" <brain-path> --url <url> --name <name>`
2. Fill `site-profile.yaml`: the three answered fields, plus every defaulted
   field from the list above (geos, approval channel, runtime: manual, brain
   mode: local, brain repo path).
3. Call `core.registry.register(<url>, <name>, <brain-path>)`.
4. Print the summary table (interview style, above): what was asked and
   answered, what was defaulted, and where each value landed in
   `site-profile.yaml`. Point at `/organic-os:setup` update mode for filling
   in keywords, competitors, connectors, or WordPress later, and at
   `/organic-os:onsite-audit` as the first thing to try right now.
5. Run a lightweight postflight scorecard: just "brain scaffold" (the four
   files from step 1 exist) and "registry readable" (`core.registry.
   get_active()` returns this site). Every connector/WordPress/approval/
   runtime row is skipped, not shown as failing, because quick-start never
   configured them - the scorecard only tests what was actually attempted.

## First-run interview (also used for "add another website")

1. Site: URL, brand name, sitemap URL (offer to guess `<url>/sitemap.xml` and verify with a fetch).
2. Brand rulebook: voice rules, banned phrases (offer sensible defaults: first person, short sentences, facts before adjectives, no exclamation marks; user edits).
3. Audience: segments/ICP, geographies, languages.
4. Keywords: target keywords/topics (free list; can be empty - keyword-intel will propose).
5. Competitors: domains (up to 5 to start).
6. Operator knowledge: "What do you already know works in this niche - tips, channels, formats?" Each answer becomes a skillbook entry tagged `evidence: anecdotal`.
7. Connectors: run the **Connector wizard** below for GA4 and GSC (the
   heartbeat pair) first, then Notion, Slack, Canva as optional extras.
   This replaces a plain available/absent question - every connector this
   interview records has been probed, and every `verified` status has
   passed one live query, not just "the tool appeared to be there."
8. Google Ads: ask whether they have a developer token and which access
   level. Point to https://github.com/shalintripathi/organic-os/blob/main/plugin/docs/credentials/google-ads-token.md
   (also at $CLAUDE_PLUGIN_ROOT/docs/credentials/google-ads-token.md in a
   local checkout). If they have a developer token or client secret to
   hand, route it through **Credentials** below. Record status only.
9. WordPress: connected site? If yes: endpoint URL + username; the
   Application Password itself goes through **Credentials** below - it
   mirrors the exact wording of `plugin/docs/credentials/wordpress.md`
   step 2.
10. Approval channel: in-session | telegram | slack | email | pr-merge. For
    telegram: chat id here, bot token through **Credentials** below (same
    env file, key `TELEGRAM_BOT_TOKEN`). No channel is privileged; default
    in-session.
11. Runtime for routines: claude-scheduled | local | ci | manual - skip
    this question if Step 0.5 already answered it; otherwise ask now and
    carry the answer into Step 0.5's rules for the rest of setup. Explain
    costs honestly: claude-scheduled and local run on the user's Claude
    subscription; ci uses an API key billed per token.
12. Where should the brain live? Default `~/organic-hq/<slug>` **on the
    runtime machine** (per Step 0.5 - if setup and runtime differ, this
    path is not on the machine setup is currently running in), where
    `<slug>` is derived the same way the registry derives it (host minus
    `www.`, dots to hyphens - e.g. `example.com` -> `example-com`). Offer
    to change the path. After the answer, run `PYTHONPATH="$CLAUDE_PLUGIN_
    ROOT/lib" python3 -c "..."` calling `core.registry.path_warnings(<brain-
    path>, <runtime from question 11>)` - on the runtime machine if setup
    can reach it directly, or as a line inside the ready-to-run snippet
    (Step 0.5) with instructions to run it before scaffolding if setup
    cannot. If it returns any warnings, show them to the user verbatim and
    re-ask the question, with the default now switched to
    `~/organic-hq/<slug>`. Do not scaffold anything at a path that still has
    open warnings without the user explicitly confirming they want to
    proceed anyway.
13. Brain mode: git repo (recommended; needed for claude-scheduled and ci
    runtimes and for versioned memory) or local folder. If git and Step 0.5
    flagged a setup/runtime mismatch, `git init` and the first commit
    happen natively on the runtime machine (see Step 0.5's git rule) - do
    not run them through a bridge.

## Connector wizard (GA4, GSC, then Notion/Slack/Canva)

Replaces a passive "is this available" question with a probe-then-verify
flow. Run this for GA4 and GSC first - call them the heartbeat pair,
because they are the primary data source the rest of the plugin depends on
- then, only if the user wants to continue, for Notion, Slack, and Canva.

For each connector, in this order:

1. **Probe** reachability in the current context: try listing the
   connector's tools (GA4/GSC/Notion/Slack/Canva - whatever surface this
   session actually exposes). Note which context this probe ran in
   (`local-cli`, `cowork-cloud`, `ci`) - it is passed to `record_connector`
   either way.
2. **If reachable, run exactly one live verification query before
   recording anything as verified:**
   - GSC: list sites.
   - GA4: pull a 7-day sessions count.
   - Notion: search or list one workspace/database.
   - Slack: list channels.
   - Canva: list designs or brand kits.
   A live call, not just tool presence, is what earns `verified` - a
   connector can appear installed but be unauthorized or pointed at the
   wrong property, and only a real call catches that. Only after the live
   call succeeds: `core.contracts.record_connector(profile_path, name,
   "verified", context)`. If the live call fails even though the
   connector looked reachable, treat it as absent and continue to step 3 -
   never record `verified` on a failed live call.
3. **If absent (or the live call failed):** present the guided connect for
   the user's actual surface:
   - claude.ai / Cowork: Settings, then Connectors.
   - Claude Code: `/mcp`, or `claude mcp add <server>` on the command line.
   Then offer, AskUserQuestion:
   - **Wait, connect it now** - pause, let the user connect, then re-probe
     from step 1 once they confirm.
   - **Skip for now** - `core.contracts.record_connector(profile_path,
     name, "declined", context)`, plus one honest line about what
     degrades, pulled from the matching row of `plugin/docs/
     connectors.md`'s capability table.

**GSC/GA4 get a stronger framing than the optional three.** Before offering
to skip either one, say plainly: "organic-os without GSC/GA4 still runs,
but `hoo-daily` will log no-data signals with nothing to act on until one
of these connects. Of everything in this interview, this is the single
connector most worth stopping to fix now." Still respect a "skip for now"
answer if that is what the user wants - never force a connection, just
make the tradeoff explicit before they choose.

## Credentials: one secret at a time

Applies to every secret this interview or an update touches - the
WordPress Application Password, the Telegram bot token, the Google Ads
OAuth client secret.

- **One secret per question.** Never present a wall of env-file fields at
  once.
- **Name it precisely** - the exact field the user is looking at in the
  exact UI, so they never go hunting. Mirror the wording already proven in
  `plugin/docs/credentials/wordpress.md`: "In wp-admin, go to Users ->
  Profile ... -> Application Passwords, name the new password ..., click
  Add New Application Password. WordPress shows the password once; copy it
  immediately." Do the equivalent lookup before asking for any other
  secret - BotFather's one-time token print for Telegram, the developer
  token in the Google Ads API Center - rather than sending the user off to
  find the field themselves.
- **Always offer the paste-into-terminal alternative**, even when setup
  could technically run the write itself: give the exact command sequence
  and let the user run it in their own terminal.
  ```
  mkdir -p ~/.config/organic-os && read -s -p "App password: " P && printf 'WP_APP_PASSWORD=%s\n' "$P" > ~/.config/organic-os/<site-slug>.env && chmod 600 ~/.config/organic-os/<site-slug>.env
  ```
  Same pattern for `TELEGRAM_BOT_TOKEN` or any Google Ads secret - one
  `read -s` / `printf` / `chmod 600` line, one key.
- **Setup never needs to see the raw value.** It verifies the credential
  worked by probing - the Connector wizard's live check for connectors, a
  WordPress REST call (`wp-json/wp/v2/users/me`) for WordPress, a Telegram
  `getMe` call for the bot token - inside the Postflight scorecard, not by
  asking the user to paste the secret into the transcript.
- **Never echo a secret into the transcript**, regardless of which path
  the user picks.

## Postflight scorecard (mandatory final step)

Setup does not claim success on its own - the scorecard does. Run every
check below that applies to what this session actually configured (skip
rows that are structurally not applicable, e.g. no WordPress row when
there is no WordPress connection at all), build a `checks` list of
`{"name", "status": "pass"|"degraded"|"fail", "detail", "fix"}`, call
`core.contracts.write_scorecard(brain_path, checks)`, and print the
resulting table to the user with any Fixes section intact.

Checks, in order:

1. **Brain scaffold** - pass if `site-profile.yaml`, `skillbook.md`, and
   `approvals/queue.md` exist at the brain path. Fix on fail: re-run
   `init_site_repo.py`.
2. **Git push** (brain mode: git only) - pass if `git log -1` in the brain
   path shows a commit, and, when a remote is configured, the push
   reached it. Detail: commit hash + branch. Fix: the exact `git remote
   add` / `git push -u origin main` command, or `gh repo create <name>
   --private --source=. --push` run from inside the brain path.
3. **Registry readable in runtime context** - pass if `core.registry.
   get_active()`, run from the runtime location, returns this site as
   active. If Step 0.5 flagged a setup/runtime mismatch and setup handed
   off a snippet instead of writing directly, this row is `degraded` with
   detail "handed off via snippet, not yet independently confirmed" and
   fix "run the Step 0.5 snippet, then `PYTHONPATH=... python3 -c
   \"from core import registry; print(registry.get_active())\"` on the
   runtime machine."
4. **WordPress REST** (only if WordPress connected) - pass if `curl -u
   '<user>:<app-password>' '<endpoint>/wp/v2/users/me'` returns 200 JSON
   for the configured user. Fix on fail: recheck `plugin/docs/credentials/
   wordpress.md` step 2 (recreate the Application Password) or step 4
   (bridge plugin not active).
5. **Approval channel test delivery** - for telegram: send a real test
   message ("organic-os setup test - reply not required") to the
   configured chat id and confirm the API call returned ok. State the
   prerequisite explicitly in the detail column either way: the first
   message to the bot has to come from the user first (open a chat, send
   anything) before `sendMessage` can deliver - Telegram rejects a
   bot-initiated first contact. Fix on fail: exactly that line. For
   in-session or pr-merge: pass automatically, detail "nothing to test -
   works by definition" / "confirmed on the first PR." For slack/email:
   the lightest live equivalent available in this session, same pass/fail
   logic as telegram.
6. **Each connector's live probe result** - one row per connector touched
   in the Connector wizard, carrying forward its recorded status
   (verified -> pass, declined -> degraded, unavailable -> fail) and
   context. Degraded/fail rows repeat the guided-connect instructions as
   the fix.
7. **Headless auth + model resolution** (runtime local or ci only; skip
   with detail "not applicable - runtime is manual/claude-scheduled"
   otherwise). For local runtime: have the user run `claude -p "ping"`
   through the wrapper (or a one-off `claude -p "ping" --permission-mode
   bypassPermissions`) and report the result.
   - Success: pass.
   - `Invalid API key - Please run /login`: fail, fix "run `claude
     setup-token`, add the result to the site env file as
     `CLAUDE_CODE_OAUTH_TOKEN`" (per `plugin/docs/routines.md`'s "Hard
     requirement: claude setup-token").
   - A 404 on the model: fail, fix "see the Model-404 recovery box in
     `plugin/docs/routines.md` - list models via curl, pin
     `ANTHROPIC_MODEL`/`ANTHROPIC_SMALL_FAST_MODEL`."
8. **One real scheduled run** (local runtime only) - kick the actual
   scheduler (`launchctl kickstart -k gui/$(id -u)/com.organic-os.daily`,
   or the systemd/cron equivalent already registered) and confirm via
   `git log -1 --format='%h %s'` in the brain repo that a fresh commit
   landed with today's date. Detail: the commit hash - this is the same
   proof `plugin/docs/routines.md`'s "Verify by commit hash" step already
   prescribes; pull that hash into the scorecard rather than re-describing
   it. Fix on fail: check `~/.config/organic-os/routine-daily.log` and
   `plugin/runtime/README.md`.

Close with one line: "<n> of <total> checks passed; <m> degraded, with the
fix for each above." Never say "setup complete" or "you're all set" unless
every non-skipped row is `pass` - a degraded or failed row is a next step
to hand to the user, not a caveat to bury.

## Rules

- Analysis-only mode is a valid outcome: a user with zero credentials still gets
  audits, briefs, and keyword work from public data.
- Never write a secret into the brain repo, the registry, or the transcript. Env files only.
- Re-running setup is safe: the scaffolder never overwrites; the interview
  offers current values as defaults; update mode never touches memory.
- The registry (`~/.config/organic-os/sites.yaml`) is local operator state,
  not part of any brain repo - it is never committed to a site's git history.
- "Configured" and "verified working" are different claims. A connector is
  `verified` only after a live probe in the Connector wizard; a runtime is
  proven only after the postflight scorecard's headless-auth and (for
  local) scheduled-run checks pass. Never state either claim without the
  check behind it.
- Never run git through a device bridge (Step 0.5) - scaffold through the
  bridge, then let the user run git natively in the runtime environment.
