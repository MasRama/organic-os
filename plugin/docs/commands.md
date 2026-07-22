# Command reference

Every organic-os command is namespaced, so type it in full: the leading slash, then `organic-os:`, then the command name.

## Getting started

| Command | What it does | Skill invoked |
|---|---|---|
| `/organic-os:start` | The guided front door - run this first | `organic-os:start` |
| `/organic-os:setup` | Onboard a site into organic-os (interview + brain scaffold + routines) | `organic-os:setup` |
| `/organic-os:sites` | Manage organic-os sites - add another website, switch the active site, or show registry status | `organic-os:setup` |
| `/organic-os:status` | Show organic-os site status - pending approvals, recent signals, next routine | - |
| `/organic-os:reset` | Guided teardown of an organic-os site - what gets deregistered automatically, what you must delete or revoke yourself, and why | `organic-os:reset` |
| `/organic-os:diagnose` | Print a paste-ready diagnostic report - runtime, versions, connector status - that is never transmitted | `organic-os:diagnose` |

## Observe and report

| Command | What it does | Skill invoked |
|---|---|---|
| `/organic-os:daily` | Run the daily organic signal pull (append-only, never mutates) | `organic-os:hoo-daily` |
| `/organic-os:weekly` | Run the weekly organic health check + reflection | `organic-os:hoo-weekly` |
| `/organic-os:monthly-audit` | Run the monthly deep organic audit across all eight specialists | `organic-os:hoo-monthly-audit` |
| `/organic-os:monday-report` | Write a stakeholder-shareable weekly summary of what moved, shipped, and needs a decision | `organic-os:hoo-monday-report` |
| `/organic-os:task-board` | Show the organic-os work queue and mirror it to Notion when available | `organic-os:hoo-task-board` |
| `/organic-os:export` | Export the brain to CSV for Sheets, Looker Studio, or any BI tool | `organic-os:hoo-export` |
| `/organic-os:citations` | Track AI answer-engine citations and share of voice for the profile's query set | `organic-os:hoo-citation-tracker` |
| `/organic-os:competitors` | Run competitor content intelligence and surface gaps against the profile | `organic-os:hoo-competitor-intel` |
| `/organic-os:keywords` | Run tiered keyword intelligence - ideas, competitor gaps, or CSV import | `organic-os:hoo-keyword-intel` |

## Act on the site

| Command | What it does | Skill invoked |
|---|---|---|
| `/organic-os:onsite-audit` | Audit on-page SEO for a URL or a whole site section (read-only) | `organic-os:onsite-audit` |
| `/organic-os:propose` | Turn audit findings or signals into concrete gated on-page change proposals | `organic-os:onsite-propose` |
| `/organic-os:apply` | Execute approved on-page proposals against WordPress (refuses anything not approved) | `organic-os:onsite-apply` |
| `/organic-os:publish` | Publish an approved, drafted content item to WordPress (refuses unapproved items) | `organic-os:onsite-publish` |
| `/organic-os:measure` | Measure applied or published on-page changes at day 7 and day 28 | `organic-os:onsite-measure` |
| `/organic-os:verify-outcome` | Recompute a recorded outcome from raw data and compare it against what was claimed | `organic-os:hoo-verify-outcome` |
| `/organic-os:import-audit` | Import an external claude-seo audit report as gated proposals | `organic-os:hoo-import-audit` |

## Content

| Command | What it does | Skill invoked |
|---|---|---|
| `/organic-os:produce` | Draft a publish-ready post from an approved content brief (six-stage pipeline) | `organic-os:ce-produce` |
| `/organic-os:image` | Create the featured image / social card for a drafted post | `organic-os:ce-image` |
