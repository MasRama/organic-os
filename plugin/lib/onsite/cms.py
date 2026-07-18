"""CMS adapter contract: the cms capability slot behind every on-page write.

ADR-0009 (capability slots, not tool bindings): organic-os code and skills
talk to "the CMS adapter", never to a named tool. `CmsAdapter` documents
the slot's interface; `onsite.wp.WPClient` (WordPress) is adapter one,
`onsite.gitstatic.GitStaticClient` (git-static) is adapter two. Adding a
CMS is a new adapter file implementing this class plus a site-profile
`cms: {type: ...}` entry - never a rewrite of contract code, and never a
fork of a skill.

Contract rules, binding on every adapter:

- Error behavior: adapters surface backend errors as RuntimeError carrying
  the backend's status and message (see WPClient._call for the shape). No
  silent retries, no swallowed failed writes.
- Gates stay in core: approval checks (core.contracts.require_approved /
  require_approval_lineage) run in the skills BEFORE any mutating adapter
  call. An adapter never gates and never inspects item status.
- Honesty: capabilities() declares what the adapter cannot do. An action
  listed in needs_human ends the item partially-applied with a note naming
  what a human must finish (docs/adr/0007 in the repo); an adapter must
  never fake success for an action it cannot perform.
- Dry-run: adapters accept dry_run=True at construction. Mutating methods
  then record intent in the adapter's `dry_run_log` list instead of
  touching the backend; reads behave normally.
"""
from __future__ import annotations

SUPPORTED_CMS_TYPES = ("wordpress", "git-static")


class CmsAdapter:
    """The capability surface a CMS adapter implements.

    Plain base class, no abc dependency: every method raises
    NotImplementedError until an adapter overrides it. "post" is the
    slot-level word for the backend's content unit (a WordPress post, a
    static-site page). Ids and backend field names are adapter-defined,
    but must round-trip through snapshot()/rollback().
    """

    # -- reads --
    def get_post(self, post_id) -> dict:
        """The backend's full editable record for one content unit,
        including the SEO meta fields update_seo_meta() can write.
        Raises RuntimeError with the backend's message on any error."""
        raise NotImplementedError

    def get_rendered_head(self, page_url: str) -> dict:
        """The rendered document head for a live URL: the source of truth
        for verifying that a write took effect. Only meaningful when
        capabilities()['rendered_head_verify'] is True."""
        raise NotImplementedError

    # -- writes (callers MUST hold an approved item; gates stay in core) --
    def update_post(self, post_id, **fields) -> dict:
        """Update core content fields (title, content, slug, excerpt,
        status). Returns the backend's updated record; under dry_run, a
        realistic-shaped dict marked dry_run: True."""
        raise NotImplementedError

    def update_seo_meta(self, post_id, **seo) -> dict:
        """Update SEO meta fields: title, description, canonical,
        focus_keyword, schema_jsonld. Adapters map these generic keys to
        their backend's own field names; unknown keys are dropped, never
        an error."""
        raise NotImplementedError

    def create_post(self, title: str, content: str, slug: str,
                    status: str = "draft", excerpt: str = "") -> dict:
        """Create a content unit, defaulting to an unpublished draft."""
        raise NotImplementedError

    # -- rollback --
    def snapshot(self, post_id, fields) -> dict:
        """Capture everything update_post/update_seo_meta can change (pick
        via `fields`) so rollback() can undo it. Includes the post id."""
        raise NotImplementedError

    def rollback(self, snap: dict) -> dict:
        """Restore a snapshot() capture verbatim."""
        raise NotImplementedError

    # -- introspection --
    def capabilities(self) -> dict:
        """What this adapter can and cannot do:
        {'seo_meta_fields': bool, 'schema_injection': bool or a mode
         string (e.g. 'frontmatter-field'), 'rendered_head_verify': bool,
         'needs_human': [action types the adapter cannot perform]}. The
        honesty rule: declare the gaps; never fake success around them."""
        raise NotImplementedError

    def adapter_name(self) -> str:
        """Stable lowercase adapter id, matching the site-profile cms
        type (e.g. 'wordpress')."""
        raise NotImplementedError


def adapter_for(profile, secret: str = "", session=None,
                dry_run: bool = False) -> CmsAdapter:
    """Build the configured CMS adapter from a parsed site-profile dict.

    The `cms:` profile key is additive (schema_version stays 1):
    `cms: {type: wordpress}`. When the key is absent, the type defaults
    to wordpress if the profile has a wordpress endpoint configured.
    `secret` is the adapter's write credential, passed in from the site
    env file and never stored in the profile; for wordpress, the
    Application Password. The git-static adapter takes no secret and no
    session - it reads and writes files in a local clone
    (`cms: {type: git-static, repo_root: ..., content_dir: ...,
    fields: {...}}`); the skill layer runs the git/gh commands. An
    unknown or missing type raises ValueError naming the supported types.
    """
    profile = profile or {}
    cms_type = str((profile.get("cms") or {}).get("type") or "").strip()
    if not cms_type and (profile.get("wordpress") or {}).get("endpoint"):
        cms_type = "wordpress"
    if cms_type == "wordpress":
        from .wp import WPClient  # adapter import stays off the module load path
        wp = profile.get("wordpress") or {}
        return WPClient(wp.get("endpoint", ""), wp.get("username", ""),
                        secret, session=session, dry_run=dry_run)
    if cms_type == "git-static":
        from .gitstatic import GitStaticClient  # off the module load path too
        cms = profile.get("cms") or {}
        repo_root = str(cms.get("repo_root") or "").strip()
        if not repo_root:
            raise ValueError(
                "cms type git-static needs repo_root: the local clone of "
                "the site repo (cms: {type: git-static, repo_root: ...} "
                "in site-profile.yaml)")
        return GitStaticClient(repo_root,
                               content_dir=cms.get("content_dir",
                                                   "src/content"),
                               fields=cms.get("fields"), dry_run=dry_run)
    supported = ", ".join(SUPPORTED_CMS_TYPES)
    if not cms_type:
        raise ValueError(
            "no cms configured: set cms: {type: ...} or a wordpress "
            f"endpoint in site-profile.yaml; supported types: {supported}")
    raise ValueError(
        f"unsupported cms type {cms_type!r}; supported types: {supported}")
