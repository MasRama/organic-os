import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import json  # noqa: E402
import json as _json  # noqa: E402  (alias: 'json' is shadowed inside request())
import pytest  # noqa: E402
from onsite.wp import WPClient  # noqa: E402


class FakeSession:
    def __init__(self):
        self.calls = []
        self.responses = {}
        self.force_error = None          # (status_code, body_text)
    def request(self, method, url, auth=None, json=None, timeout=60, **kw):
        self.calls.append((method, url, json))
        if self.force_error:
            status, text_body = self.force_error
        else:
            body = self.responses.get((method, url),
                                      {"id": 42, "title": {"raw": "Old"},
                                       "slug": "old-slug",
                                       "meta": {"rank_math_title": "Old T"}})
            status, text_body = 200, _json.dumps(body)
        class R:
            status_code = status
            text = text_body
            def json(self):
                return _json.loads(text_body)
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
    snap = c.snapshot(42, fields=["title", "meta", "slug"])
    rec = tmp_path / "rollback.json"; rec.write_text(json.dumps(snap))
    c.rollback(json.loads(rec.read_text()))
    method, url, payload = s.calls[-1]
    assert method == "POST" and url.endswith("/wp/v2/posts/42")
    assert payload["title"] == "Old"          # restored raw title
    assert payload["meta"]["rank_math_title"] == "Old T"
    assert payload["slug"] == "old-slug"      # slug round-trips too


def test_create_post_draft_by_default():
    s = FakeSession(); c = make_client(s)
    c.create_post(title="T", content="C", slug="t")
    method, url, payload = s.calls[-1]
    assert payload["status"] == "draft"


def test_call_raises_with_error_body():
    s = FakeSession(); c = make_client(s)
    s.force_error = (401, '{"code":"rest_forbidden","message":"Sorry"}')
    with pytest.raises(RuntimeError) as exc:
        c.get_post(42)
    assert "401" in str(exc.value)
    assert "rest_forbidden" in str(exc.value)


def test_get_head_percent_encodes_url():
    s = FakeSession(); c = make_client(s)
    c.get_head("https://play.example/page?variant=b&utm=x")
    method, url, payload = s.calls[-1]
    assert "url=" in url
    assert "&" not in url.split("url=", 1)[1]   # the page URL is fully encoded


# -- dry-run mode -------------------------------------------------------------

def test_update_user_writes_profile_fields():
    # Site-level author-entity fix: the onsite-audit page-essentials
    # dimension proposes a user profile description; this is the write.
    s = FakeSession(); c = make_client(s)
    c.update_user(7, description="Bio text", url="https://play.example/about")
    method, url, payload = s.calls[-1]
    assert method == "POST" and url.endswith("/wp/v2/users/7")
    assert payload == {"description": "Bio text",
                       "url": "https://play.example/about"}


def make_dry_client(sess):
    return WPClient("https://play.example/wp-json", "organic-agent", "secret",
                    session=sess, dry_run=True)


def test_dry_run_update_user_zero_session_calls_logs_intent():
    s = FakeSession(); c = make_dry_client(s)
    out = c.update_user(7, description="Bio text")
    assert s.calls == []                        # the session was never touched
    assert out["dry_run"] is True
    entry = c.dry_run_log[-1]
    assert entry["method"] == "update_user"
    assert entry["user_id"] == 7
    assert entry["fields"]["description"] == "Bio text"


def test_dry_run_update_rankmath_zero_session_calls_logs_intent():
    s = FakeSession(); c = make_dry_client(s)
    out = c.update_rankmath(42, title="New T", description="New D")
    assert s.calls == []                        # the session was never touched
    assert out["dry_run"] is True
    entry = c.dry_run_log[-1]
    assert entry["method"] == "update_rankmath"
    assert entry["post_id"] == 42
    assert entry["fields"]["meta"]["rank_math_title"] == "New T"
    assert entry["fields"]["meta"]["rank_math_description"] == "New D"


def test_dry_run_create_post_zero_session_calls_logs_intent():
    s = FakeSession(); c = make_dry_client(s)
    out = c.create_post(title="T", content="C", slug="t")
    assert s.calls == []
    assert out["dry_run"] is True
    assert out["status"] == "draft"             # realistic shape, draft default
    entry = c.dry_run_log[-1]
    assert entry["method"] == "create_post"
    assert entry["fields"]["slug"] == "t"


def test_dry_run_update_post_and_rollback_log_never_write():
    s = FakeSession(); c = make_dry_client(s)
    c.update_post(42, title="New")
    c.rollback({"post_id": 42, "title": "Old", "slug": "old-slug"})
    assert s.calls == []
    assert [e["method"] for e in c.dry_run_log] == ["update_post", "rollback"]
    assert all(e["post_id"] == 42 for e in c.dry_run_log)


def test_dry_run_snapshot_still_calls_session():
    s = FakeSession(); c = make_dry_client(s)
    snap = c.snapshot(42, fields=["title", "slug"])
    assert len(s.calls) == 1                    # reads behave normally
    assert snap["title"] == "Old"
    assert snap["slug"] == "old-slug"
    assert c.dry_run_log == []                  # a read is not a logged intent
