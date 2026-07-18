import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from core.init_site_repo import init_site_repo  # noqa: E402
from core import contracts as C  # noqa: E402
from core import approval as A  # noqa: E402


def test_pending_lists_and_approve_records(tmp_path):
    root = init_site_repo(tmp_path / "b", "https://e.com", "E")
    p = C.create_item(root, "onpage-fix", "fix1", "Fix one", "body", "https://e.com/1", "s")
    assert [i["meta"]["id"] for i in A.pending(root)] == ["p-" + p.name[:8] + "-fix1"]
    A.record_decision(root, item_id=A.pending(root)[0]["meta"]["id"],
                      decision="approved", actor="shivaa", channel="telegram")
    assert A.pending(root) == []
    assert C.load_item(p)["meta"]["status"] == "approved"
