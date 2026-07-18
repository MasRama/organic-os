"""WordPress REST client for on-page SEO. Application-password auth.
Session injected for tests; real use builds a stdlib session (no requests dep).

RankMath meta keys must be REST-registered on the site (the bundled
playground/wp-extras/organic-os-bridge.php mu-plugin, or Devora's
rank-math-api-manager). See docs/credentials/wordpress.md.
"""
from __future__ import annotations
import base64
import json
import urllib.request

RANKMATH_KEYS = {"title": "rank_math_title", "description": "rank_math_description",
                 "canonical": "rank_math_canonical_url",
                 "focus_keyword": "rank_math_focus_keyword",
                 "schema_jsonld": "agent_jsonld"}


class StdlibSession:
    def request(self, method, url, headers=None, json_body=None, **kw):
        data = json.dumps(json_body).encode() if json_body is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers=headers or {})
        if data:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode()
            class R:
                status_code = r.status
                text = body
                def json(self):
                    return json.loads(body)
            return R()


class WPClient:
    def __init__(self, endpoint: str, username: str, app_password: str, session=None):
        self.endpoint = endpoint.rstrip("/")
        self._auth = base64.b64encode(f"{username}:{app_password}".encode()).decode()
        self.session = session or StdlibSession()

    def auth_header(self) -> str:
        return f"Basic {self._auth}"

    def _call(self, method: str, path: str, payload=None):
        url = f"{self.endpoint}{path}"
        kw = {"headers": {"Authorization": self.auth_header()}}
        if payload is not None:
            kw["json"] = payload           # FakeSession reads kw['json']
            kw["json_body"] = payload      # StdlibSession reads kw['json_body']
        r = self.session.request(method, url, **kw)
        if getattr(r, "status_code", 200) >= 300:
            raise RuntimeError(f"WP {method} {path} -> {r.status_code}: {r.text[:200]}")
        return r.json()

    # -- reads --
    def get_post(self, post_id: int) -> dict:
        return self._call("GET", f"/wp/v2/posts/{post_id}?context=edit")

    def get_head(self, page_url: str) -> dict:
        """RankMath Headless getHead: the rendered head for verification."""
        return self._call("GET", f"/rankmath/v1/getHead?url={page_url}")

    # -- writes (callers MUST hold an approved item; enforced in skills) --
    def update_post(self, post_id: int, **fields) -> dict:
        return self._call("POST", f"/wp/v2/posts/{post_id}", fields)

    def update_rankmath(self, post_id: int, **seo) -> dict:
        meta = {RANKMATH_KEYS[k]: v for k, v in seo.items() if k in RANKMATH_KEYS}
        return self._call("POST", f"/wp/v2/posts/{post_id}", {"meta": meta})

    def create_post(self, title: str, content: str, slug: str,
                    status: str = "draft", excerpt: str = "") -> dict:
        return self._call("POST", "/wp/v2/posts",
                          {"title": title, "content": content, "slug": slug,
                           "status": status, "excerpt": excerpt})

    # -- rollback --
    def snapshot(self, post_id: int, fields) -> dict:
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
        return snap

    def rollback(self, snap: dict) -> dict:
        payload = {k: v for k, v in snap.items() if k != "post_id"}
        return self._call("POST", f"/wp/v2/posts/{snap['post_id']}", payload)
