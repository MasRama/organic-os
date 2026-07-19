# Information map

Load-bearing facts that appear in more than one file drift unless something
guards them. This map names each fact, the single place it is canonical,
every file that quotes it, and what checks the quote: `audit-8` means
`scripts/audit.sh` check 8 verifies it mechanically on every run; `manual`
means a human consults this map when the canonical source changes.

| Fact | Canonical source | Quoted in | Checked by |
|---|---|---|---|
| Plugin version | `version` in `plugin/.claude-plugin/plugin.json` | `README.md` version badge; `.claude-plugin/marketplace.json` plugin entry; `CHANGELOG.md` release heading; `docs/images/install-2-install.svg` | audit-8 (badge, marketplace); manual (CHANGELOG, SVG) |
| Test count | `python3 -m pytest --collect-only -q tests` | `README.md` tests badge; `README.md` inventory line | audit-8 |
| Skill / command / agent counts | Filesystem: dirs holding a `SKILL.md` under `plugin/skills/`; `plugin/commands/*.md`; `plugin/agents/*.md` | `README.md` inventory line; `docs/images/install-2-install.svg` | audit-8 (README); manual (SVG) |
| Approval TTL default (30 days) | `approval_ttl_days` in `plugin/lib/core/contracts.py` | `plugin/docs/approval-channels.md`; `README.md` human-gates paragraph; `docs/adr/0008-approval-expiry.md`; `plugin/docs/site-repo-contract.md` | manual |
| Schema version | `SCHEMA_VERSION` in `plugin/lib/core/contracts.py` | `plugin/docs/updating.md`; `plugin/docs/site-repo-contract.md` | manual |
| Install commands | Marketplace and plugin name in `.claude-plugin/marketplace.json` | `README.md`; `plugin/docs/getting-started.md`; `docs/images/install-1-marketplace.svg`; `docs/images/install-2-install.svg` | manual |
| Brain layout dirs | `DIRS` in `plugin/lib/core/init_site_repo.py` | `plugin/docs/site-repo-contract.md` layout block | manual |
| CMS adapter contract (`CmsAdapter` surface, `adapter_for`, supported types `wordpress` + `git-static`, `cms:` profile key, redirect modes in `capabilities()['redirects']`) | `plugin/lib/onsite/cms.py` | `plugin/docs/site-repo-contract.md` cms key bullet; `plugin/docs/approval-channels.md` pr-merge section; `plugin/docs/getting-started.md` upgrade ladder; `plugin/skills/onsite-apply/SKILL.md` redirect-fixes section; `CONTRIBUTING.md` adapter section; `ROADMAP.md` v0.3 | manual |
| Notification taxonomy (what the operator hears and when) | "What you will hear and when" table in `plugin/docs/approval-channels.md` | `plugin/skills/onsite-apply/SKILL.md` outcome-summary step; `plugin/skills/onsite-publish/SKILL.md` outcome-summary step; `plugin/skills/hoo-daily/SKILL.md` daily-alert section. README FAQ checked 2026-07-19: it does not mention notifications, nothing to sync there | manual |
| Audit-dimension list (page essentials: the seven checks, step 3; link health: the crawl-driven checks, step 4; signal severities for both) | numbered dimensions in `plugin/skills/onsite-audit/SKILL.md` (steps 3-4) | `plugin/skills/hoo-monthly-audit/SKILL.md` site-wide step; `docs/adr/0010-audit-dimension-responsibility.md` | manual |
| AI-surface referral list (chatgpt.com, perplexity.ai, gemini.google.com, copilot.microsoft.com, claude.ai; reviewed quarterly) | `ai_referrals` step (2.5) in `plugin/skills/hoo-daily/SKILL.md` | `plugin/skills/hoo-weekly/SKILL.md` week-over-week trend step; `plugin/skills/hoo-monday-report/SKILL.md` What-moved section | manual |
| Brief types (`explainer` via field absence, `comparison`) | `BRIEF_TYPES` in `plugin/lib/core/contracts.py` | `plugin/docs/site-repo-contract.md` items section; `plugin/skills/ce-produce/SKILL.md` comparison section; `plugin/skills/hoo-weekly/SKILL.md`; `plugin/skills/hoo-orchestrator/SKILL.md` step 4; `plugin/skills/hoo-keyword-intel/SKILL.md` cluster section | manual |

Check 8 also verifies that every relative markdown link in the repo
resolves to an existing file, so cross-references never silently rot when
a file moves.

**The dev-cycle rule.** Any wave that touches a canonical source consults
this map before committing and updates every quoting file in the same
commit - a version bump, a test added, a renamed doc, a new skill all
land together with their quotes. When a change introduces a new
load-bearing fact (anything about to be quoted in a second file), add its
row here in that same commit, and prefer wiring it into audit check 8
over leaving it `manual`.
