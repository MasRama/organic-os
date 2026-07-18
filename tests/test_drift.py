import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from core.init_site_repo import init_site_repo  # noqa: E402
from onsite import drift  # noqa: E402


class FakeWP:
    """Minimal fake WP client: only get_post, matching WPClient's post shape
    (see tests/test_wp.py FakeSession's response body)."""
    def __init__(self, posts):
        self.posts = posts  # {page_id: post_dict}

    def get_post(self, post_id):
        return self.posts[post_id]


def _post(title, rank_math_title, rank_math_description="", canonical="",
          slug="page", status="publish", jsonld=None):
    meta = {"rank_math_title": rank_math_title,
            "rank_math_description": rank_math_description,
            "rank_math_canonical_url": canonical}
    if jsonld is not None:
        meta["agent_jsonld"] = jsonld
    return {"title": {"raw": title}, "slug": slug, "status": status, "meta": meta}


def test_snapshot_shape():
    wp = FakeWP({42: _post("Home", "Home | Example", jsonld="{}")})
    snap = drift.snapshot_pages(wp, [42])
    assert snap == {
        "42": {
            "title": "Home",
            "rank_math_title": "Home | Example",
            "rank_math_description": "",
            "canonical": "",
            "slug": "page",
            "status": "publish",
            "jsonld_present": True,
        }
    }


def test_snapshot_jsonld_absent_is_false():
    wp = FakeWP({42: _post("Home", "Home | Example")})
    snap = drift.snapshot_pages(wp, [42])
    assert snap["42"]["jsonld_present"] is False


def test_snapshot_multiple_pages():
    wp = FakeWP({1: _post("A", "A T"), 2: _post("B", "B T")})
    snap = drift.snapshot_pages(wp, [1, 2])
    assert set(snap) == {"1", "2"}
    assert snap["1"]["title"] == "A" and snap["2"]["title"] == "B"


def test_baseline_path(tmp_path):
    root = tmp_path / "brain"
    assert drift.baseline_path(root) == root / "drift" / "baseline.json"


def test_no_baseline_compare_returns_empty_and_does_not_crash(tmp_path):
    root = init_site_repo(tmp_path / "brain", "https://example.com", "Example")
    wp = FakeWP({42: _post("Home", "Home | Example")})
    snap = drift.snapshot_pages(wp, [42])
    assert drift.compare(root, snap) == []


def test_save_baseline_writes_atomically_and_creates_dir(tmp_path):
    root = init_site_repo(tmp_path / "brain", "https://example.com", "Example")
    wp = FakeWP({42: _post("Home", "Home | Example")})
    snap = drift.snapshot_pages(wp, [42])
    path = drift.save_baseline(root, snap)
    assert path == drift.baseline_path(root)
    assert path.exists()
    assert not path.with_suffix(path.suffix + ".tmp").exists()


def test_compare_detects_changed_title_and_appeared_disappeared_jsonld(tmp_path):
    root = init_site_repo(tmp_path / "brain", "https://example.com", "Example")

    wp_before = FakeWP({
        42: _post("Home", "Home | Example", jsonld="{}"),   # jsonld present
        43: _post("About", "About | Example"),               # jsonld absent
    })
    baseline_snap = drift.snapshot_pages(wp_before, [42, 43])
    drift.save_baseline(root, baseline_snap)

    wp_after = FakeWP({
        42: _post("Home", "Home | Example Rewritten"),       # title changed, jsonld gone
        43: _post("About", "About | Example", jsonld="{}"),  # jsonld appeared
    })
    new_snap = drift.snapshot_pages(wp_after, [42, 43])
    changes = drift.compare(root, new_snap)

    by_page_field = {(c["page_id"], c["field"]): c for c in changes}

    title_change = by_page_field[("42", "rank_math_title")]
    assert title_change["was"] == "Home | Example"
    assert title_change["now"] == "Home | Example Rewritten"

    disappeared = by_page_field[("42", "jsonld_present")]
    assert disappeared["was"] is True
    assert disappeared["now"] is False

    appeared = by_page_field[("43", "jsonld_present")]
    assert appeared["was"] is False
    assert appeared["now"] is True

    # unrelated fields on unchanged pages/values are not reported
    assert ("42", "slug") not in by_page_field


def test_compare_no_changes_returns_empty(tmp_path):
    root = init_site_repo(tmp_path / "brain", "https://example.com", "Example")
    wp = FakeWP({42: _post("Home", "Home | Example")})
    snap = drift.snapshot_pages(wp, [42])
    drift.save_baseline(root, snap)
    assert drift.compare(root, snap) == []
