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


def test_skillbook_update_deprecated_entry_raises(root):
    C.skillbook_append(root, "old idea", evidence="anecdotal", source="x")
    C.skillbook_update(root, "S-001", deprecate=True)
    before = (root / "skillbook.md").read_text()
    with pytest.raises(C.ContractError):
        C.skillbook_update(root, "S-001", helpful=1)
    assert (root / "skillbook.md").read_text() == before  # line unchanged


def test_create_item_rejects_path_escape_slug(root):
    with pytest.raises(C.ContractError):
        C.create_item(root, kind="onpage-fix", slug="../../escape", title="t", body="b",
                      target="", source="s")
    assert list((root / "proposals").glob("*.md")) == []
    assert list(root.rglob("escape.md")) == []


def test_queue_index_lists_pending(root):
    C.create_item(root, kind="content-brief", slug="guide", title="A guide", body="b",
                  target="", source="s")
    C.rebuild_queue(root)
    q = (root / "approvals" / "queue.md").read_text()
    assert "A guide" in q and "content-brief" in q


def test_failed_status_only_from_approved(root):
    p = C.create_item(root, kind="onpage-fix", slug="verify-fail", title="t", body="b",
                      target="https://ex.com/v", source="s")
    with pytest.raises(C.ContractError):
        C.set_status(p, "failed", actor="agent")           # proposed -> failed illegal
    C.set_status(p, "approved", actor="shivaa", channel="in-session")
    C.set_status(p, "failed", actor="agent")               # approved -> failed legal
    assert C.load_item(p)["meta"]["status"] == "failed"

    q = C.create_item(root, kind="onpage-fix", slug="already-applied", title="t", body="b",
                      target="https://ex.com/a", source="s")
    C.set_status(q, "approved", actor="shivaa", channel="in-session")
    C.set_status(q, "applied", actor="agent")
    with pytest.raises(C.ContractError):
        C.set_status(q, "failed", actor="agent")           # applied -> failed illegal


def test_approval_lineage_passes_for_drafted_after_approval(root):
    p = C.create_item(root, kind="content-brief", slug="lineage-ok", title="t", body="b",
                      target="", source="s")
    C.set_status(p, "approved", actor="shivaa", channel="in-session")
    C.set_status(p, "drafted", actor="agent")
    C.require_approval_lineage(p)  # no raise: approved decision is in the lineage


def test_approval_lineage_rejected_item_raises(root):
    p = C.create_item(root, kind="content-brief", slug="lineage-rejected", title="t", body="b",
                      target="", source="s")
    C.set_status(p, "rejected", actor="shivaa", channel="in-session")
    with pytest.raises(C.ContractError):
        C.require_approval_lineage(p)


def test_approval_lineage_fresh_proposed_raises(root):
    p = C.create_item(root, kind="content-brief", slug="lineage-fresh", title="t", body="b",
                      target="", source="s")
    with pytest.raises(C.ContractError):
        C.require_approval_lineage(p)


# -- schema versioning ---------------------------------------------------------

def test_check_schema_missing_profile(tmp_path):
    empty = tmp_path / "no-brain-here"
    empty.mkdir()
    result = C.check_schema(empty)
    assert result == {"version": 0, "compatible": False, "action": "run /organic-os:setup"}


def test_check_schema_missing_key_assumes_v1_and_stamps(root):
    # root's site-profile.yaml was scaffolded with schema_version: 1 already;
    # simulate a pre-v0.1.3 brain by stripping the key out.
    profile = root / "site-profile.yaml"
    lines = [l for l in profile.read_text().splitlines() if "schema_version" not in l]
    profile.write_text("\n".join(lines) + "\n")
    result = C.check_schema(root)
    assert result == {"version": 1, "compatible": True, "action": "stamp"}


def test_check_schema_current_version(root):
    result = C.check_schema(root)
    assert result == {"version": 1, "compatible": True, "action": "none"}


def test_check_schema_older_version_needs_migration(root):
    profile = root / "site-profile.yaml"
    text = profile.read_text().replace("schema_version: 1", "schema_version: 0")
    profile.write_text(text)
    result = C.check_schema(root)
    assert result == {"version": 0, "compatible": False,
                       "action": "run /organic-os:setup to migrate"}


def test_check_schema_newer_version_needs_plugin_update(root):
    profile = root / "site-profile.yaml"
    text = profile.read_text().replace("schema_version: 1", "schema_version: 2")
    profile.write_text(text)
    result = C.check_schema(root)
    assert result == {"version": 2, "compatible": False,
                       "action": "update the plugin (/plugin update organic-os)"}


def test_mark_notified_and_is_notified(root):
    p = C.create_item(root, kind="onpage-fix", slug="notify-me", title="t", body="b",
                      target="https://ex.com/n", source="s")
    assert C.is_notified(C.load_item(p)) is False
    C.mark_notified(p)
    assert C.is_notified(C.load_item(p)) is True
