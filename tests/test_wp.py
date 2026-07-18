import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import json  # noqa: E402
import pytest  # noqa: E402
from onsite.wp import WPClient  # noqa: E402


class FakeSession:
    def __init__(self):
        self.calls = []
        self.responses = {}
    def request(self, method, url, **kw):
        self.calls.append((method, url, kw.get("json")))
        body = self.responses.get((method, url), {"id": 42, "title": {"raw": "Old"},
                                                  "meta": {"rank_math_title": "Old T"}})
        class R:
            status_code = 200
            text = json.dumps(body)
            def json(self):
                return body
        return R()


def make_client(sess):
    return WPClient("https://play.example/wp-json", "organic-agent", "secret", session=sess)


def test_auth_header_is_basic():
    c = make_client(FakeSession())
    assert c.auth_header().startswith("Basic ")


def test_update_rankmath_posts_meta():
    s = FakeSession(); c = make_client(s)
    c.update_rankmath(42, title="New T", description="New D")
    method, url, payload = s.calls[-1]
    assert method == "POST" and url.endswith("/wp/v2/posts/42")
    assert payload["meta"]["rank_math_title"] == "New T"
    assert payload["meta"]["rank_math_description"] == "New D"


def test_snapshot_then_rollback_restores(tmp_path):
    s = FakeSession(); c = make_client(s)
    snap = c.snapshot(42, fields=["title", "meta"])
    rec = tmp_path / "rollback.json"; rec.write_text(json.dumps(snap))
    c.rollback(json.loads(rec.read_text()))
    method, url, payload = s.calls[-1]
    assert method == "POST" and url.endswith("/wp/v2/posts/42")
    assert payload["title"] == "Old"          # restored raw title
    assert payload["meta"]["rank_math_title"] == "Old T"


def test_create_post_draft_by_default():
    s = FakeSession(); c = make_client(s)
    c.create_post(title="T", content="C", slug="t")
    method, url, payload = s.calls[-1]
    assert payload["status"] == "draft"
