import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import pytest  # noqa: E402
from core.init_site_repo import init_site_repo  # noqa: E402
from core import contracts as C  # noqa: E402


@pytest.fixture
def root(tmp_path):
    return init_site_repo(tmp_path / "brain", "https://ex.com", "Ex")


def test_append_signal_is_append_only(root):
    C.append_signal(root, "clicks dropped 12% on /pricing", date="2026-07-18")
    C.append_signal(root, "second observation", date="2026-07-18")
    text = (root / "signals" / "2026-07-18.md").read_text()
    assert text.index("clicks dropped") < text.index("second observation")


def test_create_and_load_proposal(root):
    p = C.create_item(root, kind="onpage-fix", slug="pricing-title",
                      title="Rewrite /pricing title tag",
                      body="Change title to 'Pricing - Ex'.",
                      target="https://ex.com/pricing", source="signal:2026-07-18")
    item = C.load_item(p)
    assert item["meta"]["status"] == "proposed"
    assert item["meta"]["kind"] == "onpage-fix"
    assert "Rewrite /pricing" in item["meta"]["title"]


def test_status_lifecycle_enforced(root):
    p = C.create_item(root, kind="onpage-fix", slug="x", title="t", body="b",
                      target="https://ex.com/x", source="s")
    with pytest.raises(C.ContractError):
        C.set_status(p, "applied", actor="agent")          # cannot skip approval
    C.set_status(p, "approved", actor="shivaa", channel="in-session")
    C.set_status(p, "applied", actor="agent")
    meta = C.load_item(p)["meta"]
    assert meta["status"] == "applied"
    assert meta["approvals"][0]["actor"] == "shivaa"


def test_require_approved_gate(root):
    p = C.create_item(root, kind="publish", slug="post-1", title="t", body="b",
                      target="", source="s")
    with pytest.raises(C.ContractError):
        C.require_approved(p)
    C.set_status(p, "approved", actor="shivaa", channel="pr-merge")
    C.require_approved(p)  # no raise


def test_skillbook_append_and_update(root):
    sid = C.skillbook_append(root, "Answer capsule under 60 words lifts snippet capture",
                             evidence="strong", source="princeton-geo")
    assert sid == "S-001"
    sid2 = C.skillbook_append(root, "Second lesson", evidence="anecdotal", source="operator")
    assert sid2 == "S-002"
    C.skillbook_update(root, "S-001", helpful=1)
    book = (root / "skillbook.md").read_text()
    assert "[helpful: 1, harmful: 0" in book.split("S-001")[1].split("\n")[0]


def test_skillbook_deprecate_not_delete(root):
    C.skillbook_append(root, "old idea", evidence="anecdotal", source="x")
    C.skillbook_update(root, "S-001", deprecate=True)
    line = [l for l in (root / "skillbook.md").read_text().splitlines() if "S-001" in l][0]
    assert line.startswith("~~") or "DEPRECATED" in line


def test_queue_index_lists_pending(root):
    C.create_item(root, kind="content-brief", slug="guide", title="A guide", body="b",
                  target="", source="s")
    C.rebuild_queue(root)
    q = (root / "approvals" / "queue.md").read_text()
    assert "A guide" in q and "content-brief" in q
