"""WordPress REST client for on-page SEO. Application-password auth.
Session injected for tests; real use builds a stdlib session (no requests dep).
The session contract is requests-compatible: request(method, url, headers=...,
json=..., timeout=...).

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

RANKMATH_KEYS = {"title": "rank_math_title", "description": "rank_math_description",
                 "canonical": "rank_math_canonical_url",
                 "focus_keyword": "rank_math_focus_keyword",
                 "schema_jsonld": "agent_jsonld"}


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


class WPClient:
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
