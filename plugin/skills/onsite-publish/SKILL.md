---
name: onsite-publish
description: Use to publish an APPROVED, drafted content item to WordPress - "publish the draft", /organic-os:publish. Refuses unapproved items.
---

# Publish content (gated)

1. Input: a brief item with status "drafted" whose draft file sits next to it
   (same folder, <brief-name>.draft.md produced by ce-produce).
2. Gate: the brief's status must be "drafted" (step 1 already checks) AND
   `core.contracts.require_approval_lineage(brief_path)` must pass; abort on
   ContractError. A rejected item must never reach `create_post`. The profile
   user must also confirm the final draft in-session or via channel.
3. Create the post via the CMS adapter (`onsite.cms.adapter_for`;
   WordPress today): `create_post` (status draft by default; status
   "publish" only when site-profile sets publishing: direct), then
   `update_seo_meta` with title/description/focus keyword from the draft's
   frontmatter, and schema if the draft includes it. (`update_rankmath`
   remains as the WordPress adapter's alias for `update_seo_meta`.)
4. Verify with `get_rendered_head`; on success `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib"
   python3 -m core status <brief-path> published --actor agent` and
   write the outcome record with measurement dates; on failure leave the post
   in draft and record the post id + failure reason in the outcome record.
   IndexNow: when site-profile.yaml has `indexnow: {enabled: true, key: ...}`
   (additive key) AND the post actually went live (status "publish" - a WP
   draft has no public URL to submit), call `hoo.indexnow.submit(host, key,
   [post_url])` after the successful verify and record the returned status
   in the outcome record; a non-200 is recorded, never retried in-run.
5. If a Canva image brief exists next to the draft (from ce-image), record its
   path in the outcome record for manual upload (media upload is not in v1).

Dry-run: with `onsite: {dry_run: true}` in site-profile.yaml, run the same
gated flow with the adapter constructed `dry_run=True` - nothing is
created, the brief stays `drafted`, and the outcome record is marked
dry-run listing every write from the adapter's `dry_run_log` (see
skills/onsite-apply).

Never edit brain frontmatter directly. The contract CLI is the only write
path for status and approvals.
