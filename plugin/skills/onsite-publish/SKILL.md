---
name: onsite-publish
description: Use to publish an APPROVED, drafted content item to WordPress - "publish the draft", /organic-os:publish. Refuses unapproved items.
---

# Publish content (gated)

1. Input: a brief item with status "drafted" whose draft file sits next to it
   (same folder, <brief-name>.draft.md produced by ce-produce).
2. The brief must carry an approval (check meta.approvals non-empty) AND the
   profile user must confirm the final draft in-session or via channel.
3. Create the post via wp.py `create_post` (status draft by default; status
   "publish" only when site-profile sets publishing: direct), then
   `update_rankmath` with title/description/focus keyword from the draft's
   frontmatter, and `agent_jsonld` if the draft includes schema.
4. Verify with `get_head`; on success `set_status(brief, "published")` and
   write the outcome record with measurement dates; on failure delete the
   draft post and report.
5. If a Canva image brief exists next to the draft (from ce-image) and the
   connector is available, upload the exported image as featured media first.
