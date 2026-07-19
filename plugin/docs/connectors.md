# How connectors connect

## The honest model

organic-os bundles no MCP servers and cannot trigger an OAuth prompt
itself. It uses whatever you have already connected:

- **GA4, GSC, Notion, Slack, Canva** - connectors you authorize yourself,
  either from claude.ai's Settings -> Connectors, or via `claude mcp add`
  / `/mcp` in Claude Code.
- **Google Ads** - a developer token plus OAuth client credentials, stored
  as local env vars (see `plugin/docs/credentials/google-ads-token.md`).
- **WordPress** - an Application Password for a dedicated Editor user,
  stored in a local env file (see `plugin/docs/credentials/wordpress.md`).

organic-os is a plugin - skills, agents, and scripts - not a running
process, so it has no server-side identity to authenticate anything on its
own behalf. Every credential above is yours, connected by you, on your
terms.

Credentials entered at the plugin's enable-time install form (the
Telegram bot token, the WordPress Application Password) skip the
paste-into-terminal step: setup finds them keychain-backed as
`CLAUDE_PLUGIN_OPTION_*` env vars and verifies them by probe like any
other credential.

## What happens instead of a prompt

Nothing in organic-os pops an OAuth window. `/organic-os:start` and
`/organic-os:setup` **probe** what is reachable - they try listing GA4/GSC
tools, ask about Notion/Slack/Canva - and print a per-connector status with
the exact instructions for connecting on your surface:

- **claude.ai / Cowork:** Settings, then Connectors.
- **Claude Code:** `/mcp`, or `claude mcp add <server>` on the command
  line.

Every skill then degrades gracefully per what it finds, following the
credentials ladder in `plugin/docs/getting-started.md#the-upgrade-ladder`: no
credentials still gets you audits, briefs, and keyword work from public
data; each connector or credential you add turns on one more capability,
never blocks the ones you already have.

## Why no bundled servers

stdio MCP servers do not run on Cowork - there is no long-lived process to
host one. Bundling a GA4/GSC server with organic-os would work in Claude
Code but silently break on Cowork, which contradicts the plugin's actual
promise: the same skills, commands, and behavior on Claude Code CLI and
Claude Cowork (see `README.md`'s Install section - "no server process, no
stdio MCP server, no database"). Probing for connectors you already manage
is the only approach that works identically on both surfaces.

## Capability table

| Capability | Connector / credential | Where to connect | What works without it |
|---|---|---|---|
| Search ranking + impression signals | Google Search Console connector or MCP server | claude.ai Settings -> Connectors, or `/mcp` / `claude mcp add` in Claude Code | `hoo-daily` and the orchestrator skip the GSC pull and say so; on-page audits still run against any public URL |
| Traffic + AI-referral signals | Google Analytics 4 connector or MCP server | claude.ai Settings -> Connectors, or `/mcp` / `claude mcp add` in Claude Code | Same skip-and-state behavior as GSC; no traffic-trend signals until connected |
| Keyword planner data (volume, forecasts) | Google Ads developer token + OAuth client (env vars) | `plugin/docs/credentials/google-ads-token.md` | `hoo-keyword-intel` falls back to CSV import or public-data estimation |
| Task/brief hand-off | Notion connector | claude.ai Settings -> Connectors, or `/mcp` / `claude mcp add` in Claude Code | Briefs and proposals still write to the brain repo's `briefs/`/`proposals/`; nothing mirrors to Notion |
| Approval notifications outside a live session | Slack connector, or Telegram/email per `plugin/docs/approval-channels.md` | claude.ai Settings -> Connectors (Slack); channel-specific setup for Telegram/email | in-session approval works immediately with zero setup; you just have to be in the session when a proposal lands |
| Asset/creative generation | Canva connector | claude.ai Settings -> Connectors, or `/mcp` / `claude mcp add` in Claude Code | Content briefs and drafts still produce text; no generated creative assets |
| Publishing approved fixes/drafts to a live site | WordPress Application Password (env file) | `plugin/docs/credentials/wordpress.md` | Everything up to `approved` still works - proposals queue and get approved, they just are not applied until WordPress is connected |
| Instant URL submission on ship (Bing, Yandex, other IndexNow engines) | `indexnow: {enabled, key}` in site-profile.yaml + `<key>.txt` at the site root | `/organic-os:setup` connector wizard (generate key, place file, verify by fetch) | Apply and publish work unchanged; changed URLs just wait to be crawled naturally |

## IndexNow and Bing Webmaster

When `site-profile.yaml` has `indexnow: {enabled: true, key: ...}`,
`onsite-apply` and `onsite-publish` submit each successfully verified
changed URL via `hoo.indexnow.submit()` - one POST to
`api.indexnow.org/indexnow`, the single endpoint shared by Bing, Yandex,
and every other participating engine - and record the response status in
the outcome. Enablement runs through setup's connector wizard: generate a
32-char hex key, place `<key>.txt` (containing exactly the key) at the
site root, and the wizard verifies by fetching it before writing the
profile key. No account, no OAuth, no API key.

Bing Webmaster Tools itself is a different, honest story: site
verification there is a manual step in Bing's portal (bing.com/webmasters
- add the site, verify via DNS record, meta tag, or Bing's XML file, then
submit the sitemap once). organic-os claims no Bing Webmaster API
integration; IndexNow covers the submission path, and portal verification
stays a one-time manual task you do yourself.

Setup never stores a token, password, or credential in the brain repo or
this plugin's own files - only a record of what a probe found, and where
it ran. `/organic-os:setup`'s connector wizard writes each connector as
`{status, context, checked}` in `site-profile.yaml` via
`core.contracts.record_connector()` - `status` is `verified` (a live query
succeeded, not just tool presence), `unavailable`, or `declined`; `context`
is where the probe ran (`local-cli`, `cowork-cloud`, `ci`), since a
connector reachable from the setup session is not the same claim as one
reachable from wherever routines actually run. See `plugin/docs/
updating.md` for how this boundary holds across plugin updates.

## No-data escalation in the daily routine

`hoo-daily` needs GSC/GA4 to produce anything beyond "no sources
available." When neither connector is reachable for a given run, the
routine writes a specific `no-data:` signal line instead of the ordinary
"no notable movement" one, and counts how many days in a row that has
happened.

At three consecutive no-data days, `hoo-daily` sends one nudge through the
configured approval channel - a plain notification, not an approval item,
since there is no decision to approve, only a connector to fix: "3 daily
runs with no analytics data - GSC/GA4 are not reachable from this runtime.
Fix: <exact connect instruction>." The nudge is marked sent with a
`nudge-sent:` line inside that day's own signal file - no new state file -
and `hoo-daily` checks the last 7 days of signals for that marker before
sending again, so a persistently disconnected site gets nudged at most once
a week, not every single day.
