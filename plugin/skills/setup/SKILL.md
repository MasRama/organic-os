---
name: setup
description: Use when the user installs organic-os, says "set up organic-os", "onboard my site", "connect my website", "add another website", "switch site", "organic-os status", or runs /organic-os:setup or /organic-os:sites. Interviews the user, scaffolds the per-site brain repo, records connectors and credentials references, seeds the skillbook with operator knowledge, registers routines for the chosen runtime, and manages the multi-site registry (add / update / switch / status).
---

# organic-os setup

You are onboarding or managing sites in organic-os. Everything site-specific
comes from this interview. Never assume; ask. One question at a time,
AskUserQuestion with options where possible.

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
  place before they move on.

## Step 0: environment checks

- Confirm `python3` is on PATH.
- Confirm PyYAML is importable: `python3 -c "import yaml"`. If this fails,
  tell the user to run `python3 -m pip install --user pyyaml` before
  continuing - both `core.contracts` and `core.registry` require it.

## Step 1: read the registry, pick a mode

Read `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -c "..."` calling
`core.registry.load()` (default path `~/.config/organic-os/sites.yaml`).

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
    active site's site-profile.yaml summary; no writes

### Update mode

1. READ the existing `site-profile.yaml` for the active site first. Present
   the current values back to the user.
2. Re-ask **only** the sections the user picks (site, brand, audience,
   keywords, competitors, connectors, Google Ads, WordPress, approval
   channel, runtime). Do not re-run the full interview.
3. Rewrite `site-profile.yaml` with just those changes.
4. Skillbook: NEVER re-append an operator note unless its text is new - read
   `skillbook.md` first, skip anything that already matches an existing
   entry's text.
5. NEVER touch `signals/`, `decisions/`, `reflections/`, or existing
   skillbook entries beyond the dedup check above - those are memory, not
   config, and setup does not rewrite memory.
6. Do not re-register routines unless the user explicitly asks to change
   cadence or runtime.
7. **Rule of thumb to state to the user: config is editable, memory is not.**
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
site-profile.yaml, skillbook.md, and approvals/queue.md exist and a one-line
summary of each.

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
  Quick-start never probes connectors or asks for credentials - analysis-only
  is the correct default outcome for a 2-minute setup.
- **Runtime**: `manual`. The user runs commands themselves until they choose
  to schedule routines (`docs/routines.md`).
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

## First-run interview (also used for "add another website")

1. Site: URL, brand name, sitemap URL (offer to guess `<url>/sitemap.xml` and verify with a fetch).
2. Brand rulebook: voice rules, banned phrases (offer sensible defaults: first person, short sentences, facts before adjectives, no exclamation marks; user edits).
3. Audience: segments/ICP, geographies, languages.
4. Keywords: target keywords/topics (free list; can be empty - keyword-intel will propose).
5. Competitors: domains (up to 5 to start).
6. Operator knowledge: "What do you already know works in this niche - tips, channels, formats?" Each answer becomes a skillbook entry tagged `evidence: anecdotal`.
7. Connectors: probe availability (try listing GA4/GSC tools; ask about Notion, Slack, Canva). Record available/absent in site-profile - never store tokens.
8. Google Ads: ask whether they have a developer token and which access level. Point to https://github.com/shalintripathi/organic-os/blob/main/docs/credentials/google-ads-token.md (also at $CLAUDE_PLUGIN_ROOT/../docs/credentials/google-ads-token.md in a local checkout). Record status only.
9. WordPress: connected site? If yes: endpoint URL + username; instruct the user to create an Application Password (Users -> Profile) and store it via:
   `mkdir -p ~/.config/organic-os && read -s -p "App password: " P && printf 'WP_APP_PASSWORD=%s\n' "$P" > ~/.config/organic-os/<site-slug>.env && chmod 600 ~/.config/organic-os/<site-slug>.env`
   Never echo the password into the transcript.
10. Approval channel: in-session | telegram | slack | email | pr-merge. For telegram: bot token (stored in the same env file as TELEGRAM_BOT_TOKEN) + chat id. No channel is privileged; default in-session.
11. Runtime for routines: claude-scheduled | local | ci | manual. Explain costs honestly: claude-scheduled and local run on the user's Claude subscription; ci uses an API key billed per token.
12. Where should the brain live? Default `~/organic-hq/<slug>`, where `<slug>`
    is derived the same way the registry derives it (host minus `www.`, dots
    to hyphens - e.g. `example.com` -> `example-com`). Offer to change the path.
13. Brain mode: git repo (recommended; needed for claude-scheduled and ci runtimes and for versioned memory) or local folder.

## Actions after the interview (full setup - first-run / add mode)

1. Run: `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 "$CLAUDE_PLUGIN_ROOT/lib/core/init_site_repo.py" <brain-path> --url <url> --name <name>`
2. Fill `site-profile.yaml` with every answer (edit the file directly).
3. Seed skillbook: for each operator note, run a small Python snippet calling `core.contracts.skillbook_append(root, note, evidence="anecdotal", source="operator")`.
4. If brain mode git: `git init`, first commit, offer `gh repo create <name> --private`.
5. Register routines per the chosen runtime by following https://github.com/shalintripathi/organic-os/blob/main/docs/routines.md (also at $CLAUDE_PLUGIN_ROOT/../docs/routines.md in a local checkout) for that runtime, and write the chosen cadence into site-profile `routines:`.
6. Call `core.registry.register(<url>, <name>, <brain-path>)` to add this site to `~/.config/organic-os/sites.yaml` and make it the active site.
7. Print a summary: what is configured, what is degraded (missing connectors/credentials) and the exact doc to fix each gap.

## Rules

- Analysis-only mode is a valid outcome: a user with zero credentials still gets
  audits, briefs, and keyword work from public data.
- Never write a secret into the brain repo, the registry, or the transcript. Env files only.
- Re-running setup is safe: the scaffolder never overwrites; the interview
  offers current values as defaults; update mode never touches memory.
- The registry (`~/.config/organic-os/sites.yaml`) is local operator state,
  not part of any brain repo - it is never committed to a site's git history.
