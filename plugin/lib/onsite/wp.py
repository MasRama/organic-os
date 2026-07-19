"""WordPress REST client for on-page SEO. Application-password auth.
Session injected for tests; real use builds a stdlib session (no requests dep).
The session contract is requests-compatible: request(method, url, headers=...,
json=..., timeout=...).

Implements the CmsAdapter contract (onsite/cms.py); WordPress is adapter
one. The WordPress-specific names (update_rankmath, get_head) stay as the
implementations, with the contract names (update_seo_meta,
get_rendered_head) delegating to them.

RankMath meta keys must be REST-registered on the site (the bundled
plugin/wordpress/organic-os-bridge.php mu-plugin, or Devora's
rank-math-api-manager). See plugin/docs/credentials/wordpress.md.
"""
from __future__ import annotations
import base64
import json as _json
import urllib.error
import urllib.parse
import urllib.request

import re

from .cms import CmsAdapter

RANKMATH_KEYS = {"title": "rank_math_title", "description": "rank_math_description",
                 "canonical": "rank_math_canonical_url",
                 "focus_keyword": "rank_math_focus_keyword",
                 "schema_jsonld": "agent_jsonld"}
_IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
_ATTR = {name: re.compile(rf'{name}\s*=\s*["\']([^"\']*)["\']', re.I)
         for name in ("src", "alt", "class")}
_WP_IMAGE_CLASS = re.compile(r"\bwp-image-(\d+)\b")


class StdlibSession:
    def request(self, method, url, headers=None, json=None, timeout=60, **kw):
        data = _json.dumps(json).encode() if json is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers=headers or {})
        if data:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                status, body = r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            # Surface the WordPress error body (rest_forbidden etc.) so the
            # caller's status check can report it instead of a bare exception.
            status, body = e.code, e.read().decode("utf-8", "replace")

        class R:
            status_code = status
            text = body
            def json(self):
                return _json.loads(body)
        return R()


class WPClient(CmsAdapter):
    def __init__(self, endpoint: str, username: str, app_password: str, session=None,
                 dry_run: bool = False):
        self.endpoint = endpoint.rstrip("/")
        self._auth = base64.b64encode(f"{username}:{app_password}".encode()).decode()
        self.session = session or StdlibSession()
        # dry_run=True: reads behave normally; every mutating method records
        # its intent in dry_run_log instead of calling the session.
        self.dry_run = dry_run
        self.dry_run_log: list[dict] = []

    def auth_header(self) -> str:
        return f"Basic {self._auth}"

    def _dry(self, method: str, fields: dict, post_id: int | None = None) -> dict:
        """Log the write that would have happened and return a realistic-shaped
        response marked dry_run: True, so callers can carry on without any
        session call being made."""
        entry = {"method": method, "fields": fields}
        if post_id is not None:
            entry["post_id"] = post_id
        self.dry_run_log.append(entry)
        return {"dry_run": True, "id": post_id, **fields}

    def _call(self, method: str, path: str, payload=None):
        url = f"{self.endpoint}{path}"
        kw = {"headers": {"Authorization": self.auth_header()}, "timeout": 60}
        if payload is not None:
            kw["json"] = payload
        r = self.session.request(method, url, **kw)
        if getattr(r, "status_code", 200) >= 300:
            raise RuntimeError(f"WP {method} {path} -> {r.status_code}: {r.text[:200]}")
        return r.json()

    # -- reads --
    def get_post(self, post_id: int) -> dict:
        return self._call("GET", f"/wp/v2/posts/{post_id}?context=edit")

    def get_head(self, page_url: str) -> dict:
        """RankMath Headless getHead: the rendered head for verification."""
        quoted = urllib.parse.quote(page_url, safe="")
        return self._call("GET", f"/rankmath/v1/getHead?url={quoted}")

    def get_media(self, post_id: int) -> list:
        """Images referenced in the post's content, with their alt text.

        What is reliably readable, and what this returns per image:
        - `src` and `alt`: parsed from the post's RENDERED content <img>
          tags - the alt attribute the visitor's browser actually gets.
          A missing alt attribute reads as "" (that is the finding).
        - `media_id` + `library_alt`: WordPress stamps inserted
          attachments with a `wp-image-<id>` class; for those, the media
          endpoint's `alt_text` field (what WP re-inserts at insertion
          time) is fetched from /wp/v2/media/<id>. An image without the
          class stamp (hot-linked, theme-built, page-builder markup) has
          media_id None and library_alt None - the attachment is never
          guessed at, and only update_post can fix its in-content alt.
        """
        post = self.get_post(post_id)
        content = (post.get("content") or {})
        html = content.get("rendered") or content.get("raw") or ""
        media = []
        for tag in _IMG_TAG.findall(html):
            attrs = {name: (m.group(1) if (m := rx.search(tag)) else None)
                     for name, rx in _ATTR.items()}
            stamp = _WP_IMAGE_CLASS.search(attrs.get("class") or "")
            media_id = int(stamp.group(1)) if stamp else None
            library_alt = None
            if media_id is not None:
                record = self._call("GET", f"/wp/v2/media/{media_id}")
                library_alt = record.get("alt_text", "")
            media.append({"media_id": media_id,
                          "src": attrs.get("src") or "",
                          "alt": attrs.get("alt") if attrs.get("alt")
                          is not None else "",
                          "library_alt": library_alt})
        return media

    # -- writes (callers MUST hold an approved item; enforced in skills) --
    def update_post(self, post_id: int, **fields) -> dict:
        if self.dry_run:
            return self._dry("update_post", fields, post_id)
        return self._call("POST", f"/wp/v2/posts/{post_id}", fields)

    def update_rankmath(self, post_id: int, **seo) -> dict:
        meta = {RANKMATH_KEYS[k]: v for k, v in seo.items() if k in RANKMATH_KEYS}
        if self.dry_run:
            return self._dry("update_rankmath", {"meta": meta}, post_id)
        return self._call("POST", f"/wp/v2/posts/{post_id}", {"meta": meta})

    def update_user(self, user_id: int, **fields) -> dict:
        """Site-level author-entity write (WordPress-specific, like
        update_rankmath): profile fields via /wp/v2/users/<id> -
        `description` (the visible bio) and `url`. The connected user can
        always edit their own profile; editing another user's needs an
        admin role, and that wall ends the item partially-applied per
        skills/onsite-apply, never faked as done."""
        if self.dry_run:
            self.dry_run_log.append({"method": "update_user",
                                     "fields": fields, "user_id": user_id})
            return {"dry_run": True, "id": user_id, **fields}
        return self._call("POST", f"/wp/v2/users/{user_id}", fields)

    def update_media_alt(self, media_id: int, alt_text: str) -> dict:
        """Set an attachment's library alt text via /wp/v2/media/<id>.
        Fixes the alt WP inserts going forward AND the rendered alt for
        images whose markup echoes the attachment field; a hard-coded
        in-content alt (media_id None in get_media) needs update_post."""
        if self.dry_run:
            self.dry_run_log.append({"method": "update_media_alt",
                                     "fields": {"alt_text": alt_text},
                                     "media_id": media_id})
            return {"dry_run": True, "id": media_id, "alt_text": alt_text}
        return self._call("POST", f"/wp/v2/media/{media_id}",
                          {"alt_text": alt_text})

    def create_post(self, title: str, content: str, slug: str,
                    status: str = "draft", excerpt: str = "") -> dict:
        payload = {"title": title, "content": content, "slug": slug,
                   "status": status, "excerpt": excerpt}
        if self.dry_run:
            return self._dry("create_post", payload)
        return self._call("POST", "/wp/v2/posts", payload)

    # -- rollback --
    def snapshot(self, post_id: int, fields) -> dict:
        """Capture everything update_post can change so rollback() can undo it:
        title, meta, content, slug, excerpt, status (pick via fields)."""
        post = self.get_post(post_id)
        snap = {"post_id": post_id}
        for f in fields:
            if f == "title":
                snap["title"] = post.get("title", {}).get("raw", "")
            elif f == "meta":
                snap["meta"] = {k: post.get("meta", {}).get(k, "")
                                for k in RANKMATH_KEYS.values()}
            elif f == "content":
                snap["content"] = post.get("content", {}).get("raw", "")
            elif f == "excerpt":
                snap["excerpt"] = post.get("excerpt", {}).get("raw", "")
            elif f in ("slug", "status"):
                snap[f] = post.get(f, "")
        return snap

    def rollback(self, snap: dict) -> dict:
        payload = {k: v for k, v in snap.items() if k != "post_id"}
        if self.dry_run:
            return self._dry("rollback", payload, snap["post_id"])
        return self._call("POST", f"/wp/v2/posts/{snap['post_id']}", payload)

    # -- CmsAdapter contract surface (see onsite/cms.py) --
    def update_seo_meta(self, post_id: int, **seo) -> dict:
        """Contract name. update_rankmath stays the implementation (and the
        dry_run_log method name) as this adapter's WordPress-specific
        alias; both write the same RankMath meta."""
        return self.update_rankmath(post_id, **seo)

    def get_rendered_head(self, page_url: str) -> dict:
        """Contract name for get_head."""
        return self.get_head(page_url)

    def capabilities(self) -> dict:
        return {
            "seo_meta_fields": True,        # RankMath keys via the bridge
            "schema_injection": True,       # agent_jsonld via the bridge
            "rendered_head_verify": True,   # RankMath Headless getHead
            "author_profile_fields": True,  # update_user via /wp/v2/users
            "media_alt": True,              # update_media_alt via /wp/v2/media
            # Core WordPress exposes no redirect REST surface; redirects
            # need an SEO plugin's module (Rank Math redirections, the
            # Redirection plugin). The apply skill probes those surfaces
            # at run time; absent or role-blocked, the item ends
            # partially-applied naming the manual step.
            "redirects": "needs-plugin",
            # The Editor role cannot do these (see the capability matrix in
            # plugin/docs/credentials/wordpress.md); such steps end the item
            # partially-applied with a note, never faked as done.
            "needs_human": ["seo-plugin-cache-purge", "plugin-settings"],
        }

    def adapter_name(self) -> str:
        return "wordpress"
