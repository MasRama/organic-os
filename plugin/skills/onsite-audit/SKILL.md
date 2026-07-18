---
name: onsite-audit
description: Use to audit on-page SEO for a URL or a whole site section - "audit this page", "on-page check", /organic-os:onsite-audit. Read-only; needs no credentials for public checks.
---

# On-page audit (read-only)

1. Read profile if a brain repo exists (optional - this skill also works bare).
2. Public checks per URL (WebFetch): title (length, keyword presence),
   meta description, H1 count, heading structure, canonical, robots meta,
   image alts, internal links out, JSON-LD present/valid, answer-capsule
   presence in the first 200 words, server-rendered content check.
3. If WordPress credentials exist: pull the post via wp.py `get_post` +
   `get_head` for the rendered truth; list RankMath field values.
4. Launch technical-seo-auditor for site-level context when auditing > 3 URLs.
5. Output: per-URL scorecard table + prioritized issue list. File signals for
   P0/P1 issues if a brain repo exists. Propose nothing here; that is
   onsite-propose's job.
