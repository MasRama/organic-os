---
name: onsite-audit
description: Use to audit on-page SEO for a URL or a whole site section - "audit this page", "on-page check", /organic-os:onsite-audit. Read-only; needs no credentials for public checks.
---

# On-page audit (read-only)

1. Read profile if a brain repo exists (optional - this skill also works bare).
2. Public checks per URL (WebFetch): title (length, keyword presence),
   meta description (present, and flagged when over ~155 chars - Google
   truncates around there), H1 count, heading structure, canonical,
   robots meta, image alts, internal links out, JSON-LD present/valid,
   answer-capsule presence in the first 200 words, server-rendered
   content check.
3. Page essentials dimension - runs for each audited page, and site-wide
   where a check says so. Every check emits the standard falsifiable
   signal line (observation | why it matters | "we are wrong if..." |
   leading indicator) and, where a fix is actionable, feeds
   onsite-propose. Evidence discipline throughout (see
   plugin/docs/evidence.md): state what was measured versus what was
   inferred, and never promise a third-party outcome (rankings,
   citations) as the result of a fix.
   1. Author entity (E-E-A-T): the author has a visible on-page bio,
      sameAs links, and - for AI-attributed content - a named human
      reviewer note on the page; the author schema node carries
      `description` + `sameAs`. A thin entity -> P2 signal + a gated
      proposal. The remediation is site-level: the CMS adapter can write
      the author profile description where
      `capabilities()['author_profile_fields']` is true (the WordPress
      adapter's `update_user` writes it over REST), plus the schema
      settings; any step beyond the adapter's `capabilities()` ends
      partially-applied per skills/onsite-apply, with the human step
      named.
   2. Answer capsule: a 40-60 word standalone answer sits above the
      first H2. Missing -> P2 signal + a content-refresh proposal.
   3. In-content images: zero images in a 500+ word explainer -> P3
      signal referencing the image-brief path (skills/ce-image writes
      `<slug>-image-brief.md`). The audit only surfaces the gap
      honestly; the full in-content image workflow remains roadmapped.
   4. Meta description length: lives in step 2's meta checks (extended
      there with the ~155-char flag) - listed here for completeness,
      never duplicated as a second check.
   5. Social image shape: og:image is square while twitter:card is
      summary_large_image -> P3 signal + proposal (site-level asset);
      if no landscape asset exists, route via the image-brief fallback
      above.
   6. Publisher schema shape: the publisher node missing `logo`/`url`,
      or mixing Person and Organization types -> P3 signal for the
      entity-schema lane (entity-schema-engineer).
   7. Sitemap membership (site-wide): any published post older than 1
      hour absent from the sitemap -> P2 signal ("likely regeneration
      lag or cache; if the SEO plugin's cache purge needs admin, this
      ends partially-applied").
4. If CMS credentials exist: pull the post via the CMS adapter (WordPress
   today) with `get_post` + `get_rendered_head` for the rendered truth;
   list the SEO meta field values (RankMath fields on WordPress).
5. Launch technical-seo-auditor for site-level context when auditing > 3 URLs.
6. Output: per-URL scorecard table + prioritized issue list. File signals for
   P0/P1 issues, plus the page-essentials signals from step 3, if a brain
   repo exists. Propose nothing here; that is onsite-propose's job.

At each stage boundary, append a one-line progress marker with a UTC
timestamp to the run report file before starting the stage - headless runs
are watched by tailing that file, not a terminal.
