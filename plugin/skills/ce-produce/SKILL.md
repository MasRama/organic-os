---
name: ce-produce
description: Use to produce a publish-ready draft from an approved content brief - "draft the approved brief", "write this post", /organic-os:produce. Runs the six-stage pipeline.
---

# Content pipeline

1. Input: an APPROVED brief item (require_approved - drafting counts as work
   the user pays attention for, so briefs are gated before drafting).
   A user may also hand a manual brief; then confirm scope in-session first.
2. Stages, sequential agents (each receives profile path + prior artifacts):
   ce-researcher -> ce-writer -> ce-brand-auditor -> ce-seo-aeo -> ce-qa ->
   ce-editor.
3. Save the final draft as <brief-file>.draft.md next to the brief (frontmatter:
   title, slug, meta_description, focus_keyword, schema block). Save the
   research pack + QA log under runs/YYYYMMDD-produce-<slug>/.
4. `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m core status
   <brief-path> drafted --actor agent`. Then invoke ce-image for the
   featured-image step. Publishing is onsite-publish's job (separately gated).
5. Rules from the profile override everything: voice, banned phrases, rulebook.
   House defaults if profile is silent: answer capsule up top, no em-dashes,
   active voice, statistics cited inline with live links.
6. Never edit brain frontmatter directly. The contract CLI is the only write
   path for status and approvals.
7. At each stage boundary, append a one-line progress marker with a UTC
   timestamp to the run report file before starting the stage - headless
   runs are watched by tailing that file, not a terminal.
