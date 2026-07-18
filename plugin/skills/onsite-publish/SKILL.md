---
name: onsite-publish
description: Use to publish an APPROVED, drafted content item to WordPress - "publish the draft", /organic-os:publish. Refuses unapproved items.
---

# Publish content (gated)

1. Input: a brief item with status "drafted" whose draft file sits next to it
   (same folder, <brief-name>.draft.md produced by ce-produce).
2. Gate: call `core.contracts.require_approved(brief)` - the same gate
   onsite-apply uses - and abort on ContractError. A rejected item must never
   reach `create_post`. The profile user must also confirm the final draft
   in-session or via channel.
3. Create the post via wp.py `create_post` (status draft by default; status
   "publish" only when site-profile sets publishing: direct), then
   `update_rankmath` with title/description/focus keyword from the draft's
   frontmatter, and `agent_jsonld` if the draft includes schema.
4. Verify with `get_head`; on success `set_status(brief, "published")` and
   write the outcome record with measurement dates; on failure leave the post
   in draft and record the post id + failure reason in the outcome record.
5. If a Canva image brief exists next to the draft (from ce-image), record its
   path in the outcome record for manual upload (media upload is not in v1).
