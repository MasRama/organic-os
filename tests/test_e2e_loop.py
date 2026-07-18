import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import pytest  # noqa: E402
from core.init_site_repo import init_site_repo  # noqa: E402
from core import contracts as C, approval as A  # noqa: E402
from onsite.wp import WPClient  # noqa: E402
from tests.test_wp import FakeSession  # noqa: E402


def test_signal_to_measured_outcome(tmp_path):
    root = init_site_repo(tmp_path / "brain", "https://play.example", "Play")
    # observe
    C.append_signal(root, "position 9 -> 14 on /pricing", date="2026-07-18")
    # decide
    p = C.create_item(root, "onpage-fix", "pricing-title", "Rewrite pricing title",
                      "before: X / after: Y", "https://play.example/pricing", "signal")
    C.rebuild_queue(root)
    assert "Rewrite pricing title" in (root / "approvals" / "queue.md").read_text()
    # gate blocks before approval
    with pytest.raises(C.ContractError):
        C.require_approved(p)
    # approve
    A.record_decision(root, C.load_item(p)["meta"]["id"], "approved", "human", "in-session")
    # apply (with snapshot) + verify happens in the skill; here: client-level
    wp = WPClient("https://play.example/wp-json", "agent", "pw", session=FakeSession())
    snap = wp.snapshot(42, ["title", "meta"])
    assert snap["post_id"] == 42
    wp.update_rankmath(42, title="Y")
    C.set_status(p, "applied", actor="agent")
    # measure
    C.set_status(p, "measured", actor="agent")
    assert C.load_item(p)["meta"]["status"] == "measured"
    # learn
    sid = C.skillbook_append(root, "Title rewrites recover striking-distance drops",
                             evidence="anecdotal", source=C.load_item(p)["meta"]["id"])
    C.skillbook_update(root, sid, helpful=1)
    assert "helpful: 1" in (root / "skillbook.md").read_text()
