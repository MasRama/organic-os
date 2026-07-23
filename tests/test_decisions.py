import datetime as dt
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import pytest  # noqa: E402
from core.init_site_repo import init_site_repo  # noqa: E402
from core import contracts as C  # noqa: E402
from core import decisions as D  # noqa: E402


@pytest.fixture
def root(tmp_path):
    return init_site_repo(tmp_path / "brain", "https://ex.com", "Ex")


def _backdate(path, date):
    """Simulates an older decision: rewrites the recorded date in place."""
    doc = C.load_item(path)
    doc["meta"]["date"] = date
    C._dump(Path(path), doc["meta"], doc["body"])


# -- record --------------------------------------------------------------------

def test_record_round_trips_frontmatter_and_rationale(root):
    p = D.record(root, title="Rewrite the /pricing title tag",
                 choice="rejected",
                 rationale="legal owns that page's wording this quarter",
                 actor="operator", scope="pricing page title",
                 item="proposals/20260723-pricing-title.md")
    assert p.parent == root / "decisions"
    today = dt.datetime.now(dt.timezone.utc).date()
    assert p.name == f"{today.strftime('%Y%m%d')}-rewrite-the-pricing-title-tag.md"
    doc = C.load_item(p)
    meta = doc["meta"]
    assert meta["date"] == today.isoformat()
    assert meta["title"] == "Rewrite the /pricing title tag"
    assert meta["choice"] == "rejected"
    assert meta["actor"] == "operator"
    assert meta["scope"] == "pricing page title"
    assert meta["item"] == "proposals/20260723-pricing-title.md"
    assert "legal owns that page" in doc["body"]


def test_record_without_an_item_omits_the_key(root):
    p = D.record(root, title="Stop chasing branded queries", choice="agreed",
                 rationale="brand terms already convert", actor="operator",
                 scope="keyword strategy")
    assert "item" not in C.load_item(p)["meta"]


def test_record_duplicate_title_same_day_does_not_overwrite(root):
    first = D.record(root, title="Same call twice", choice="rejected",
                     rationale="first reason", actor="a", scope="s")
    second = D.record(root, title="Same call twice", choice="rejected",
                      rationale="second reason", actor="a", scope="s")
    assert first != second
    assert "first reason" in first.read_text()
    assert "second reason" in second.read_text()
    assert len(list((root / "decisions").glob("*.md"))) == 2


def test_record_bad_slug_raises(root):
    with pytest.raises(C.ContractError):
        D.record(root, title="???", choice="rejected", rationale="r",
                 actor="a", scope="s")
    assert list((root / "decisions").glob("*.md")) == []


# -- search --------------------------------------------------------------------

def test_search_matches_on_overlapping_terms(root):
    D.record(root, title="Rewrite the pricing title", choice="rejected",
             rationale="legal owns that copy", actor="a", scope="pricing page")
    D.record(root, title="Build a careers hub", choice="approved",
             rationale="hiring push next quarter", actor="a", scope="careers section")
    hits = D.search(root, "pricing title")
    assert len(hits) == 1
    assert hits[0]["choice"] == "rejected"
    assert hits[0]["title"] == "Rewrite the pricing title"
    assert hits[0]["scope"] == "pricing page"
    assert "legal owns that copy" in hits[0]["rationale"]
    assert Path(hits[0]["path"]).exists()


def test_search_matches_scope_and_rationale_not_just_title(root):
    D.record(root, title="Leave it alone", choice="rejected",
             rationale="the integrations directory is thin on purpose",
             actor="a", scope="integrations hub")
    assert len(D.search(root, "integrations")) == 1
    assert len(D.search(root, "directory")) == 1


def test_search_accepts_a_list_of_terms(root):
    D.record(root, title="Skip the glossary", choice="rejected",
             rationale="no demand", actor="a", scope="glossary")
    assert len(D.search(root, ["glossary", "hub"])) == 1


def test_search_without_overlap_returns_empty(root):
    D.record(root, title="Skip the glossary", choice="rejected",
             rationale="no demand", actor="a", scope="glossary")
    assert D.search(root, "webinar landing page") == []


def test_search_orders_newest_first(root):
    old = D.record(root, title="Older call on the pricing page", choice="rejected",
                   rationale="too early", actor="a", scope="pricing")
    D.record(root, title="Newer call on the pricing page", choice="approved",
             rationale="now it is worth it", actor="a", scope="pricing")
    _backdate(old, "2026-01-05")
    hits = D.search(root, "pricing")
    assert [h["title"] for h in hits] == ["Newer call on the pricing page",
                                          "Older call on the pricing page"]
    assert hits[1]["date"] == "2026-01-05"


def test_search_is_case_insensitive(root):
    D.record(root, title="Drop the Pricing Comparison", choice="rejected",
             rationale="competitor data goes stale", actor="a", scope="Pricing")
    assert len(D.search(root, "PRICING")) == 1


def test_search_missing_decisions_dir_returns_empty(tmp_path):
    assert D.search(tmp_path / "no-brain-here", "anything") == []
