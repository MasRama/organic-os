---
name: setup
description: Use when the user installs organic-os, says "set up organic-os", "onboard my site", "connect my website", or runs /organic-os:setup. Interviews the user, scaffolds the per-site brain repo, records connectors and credentials references, seeds the skillbook with operator knowledge, and registers routines for the chosen runtime.
---

# organic-os setup

You are onboarding a site into organic-os. Everything site-specific comes from
this interview. Never assume; ask. One question at a time, AskUserQuestion
with options where possible.

## Interview order

1. Site: URL, brand name, sitemap URL (offer to guess `<url>/sitemap.xml` and verify with a fetch).
2. Brand rulebook: voice rules, banned phrases (offer sensible defaults: first person, short sentences, facts before adjectives, no exclamation marks; user edits).
3. Audience: segments/ICP, geographies, languages.
4. Keywords: target keywords/topics (free list; can be empty - keyword-intel will propose).
5. Competitors: domains (up to 5 to start).
6. Operator knowledge: "What do you already know works in this niche - tips, channels, formats?" Each answer becomes a skillbook entry tagged `evidence: anecdotal`.
7. Connectors: probe availability (try listing GA4/GSC tools; ask about Notion, Slack, Canva). Record available/absent in site-profile - never store tokens.
8. Google Ads: ask whether they have a developer token and which access level. Point to docs/credentials/google-ads-token.md. Record status only.
9. WordPress: connected site? If yes: endpoint URL + username; instruct the user to create an Application Password (Users -> Profile) and store it via:
   `mkdir -p ~/.config/organic-os && read -s -p "App password: " P && printf 'WP_APP_PASSWORD=%s\n' "$P" > ~/.config/organic-os/<site-slug>.env && chmod 600 ~/.config/organic-os/<site-slug>.env`
   Never echo the password into the transcript.
10. Approval channel: in-session | telegram | slack | email | pr-merge. For telegram: bot token (stored in the same env file as TELEGRAM_BOT_TOKEN) + chat id. No channel is privileged; default in-session.
11. Runtime for routines: claude-scheduled | local | ci | manual. Explain costs honestly: claude-scheduled and local run on the user's Claude subscription; ci uses an API key billed per token.
12. Brain mode: git repo (recommended; needed for claude-scheduled and ci runtimes and for versioned memory) or local folder.

## Actions after the interview

1. Run: `python3 "$CLAUDE_PLUGIN_ROOT/lib/core/init_site_repo.py" <brain-path> --url <url> --name <name>`
2. Fill `site-profile.yaml` with every answer (edit the file directly).
3. Seed skillbook: for each operator note, run a small Python snippet calling `core.contracts.skillbook_append(root, note, evidence="anecdotal", source="operator")`.
4. If brain mode git: `git init`, first commit, offer `gh repo create <name> --private`.
5. Register routines per the chosen runtime by following docs/routines.md for that runtime, and write the chosen cadence into site-profile `routines:`.
6. Print a summary: what is configured, what is degraded (missing connectors/credentials) and the exact doc to fix each gap.

## Rules

- Analysis-only mode is a valid outcome: a user with zero credentials still gets
  audits, briefs, and keyword work from public data.
- Never write a secret into the brain repo or the transcript. Env files only.
- Re-running setup is safe: the scaffolder never overwrites; the interview
  offers current values as defaults.
