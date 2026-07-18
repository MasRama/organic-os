"""The contract CLI: python3 -m core approve|reject|status <item-path> ..."""
import os
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from core.init_site_repo import init_site_repo  # noqa: E402
from core import contracts as C  # noqa: E402


def run_cli(*args):
    env = dict(os.environ, PYTHONPATH=str(LIB))
    return subprocess.run([sys.executable, "-m", "core", *args],
                          capture_output=True, text=True, env=env)


def _brain(tmp_path):
    return init_site_repo(tmp_path / "b", "https://example.com", "Ex")


def test_approve_proposed_item_succeeds_and_rebuilds_queue(tmp_path):
    root = _brain(tmp_path)
    p = C.create_item(root, "onpage-fix", "fix1", "t", "b",
                      "https://example.com/1", "s")
    C.rebuild_queue(root)
    r = run_cli("approve", str(p), "--actor", "operator",
                "--channel", "in-session", "--note", "ship it")
    assert r.returncode == 0, r.stderr
    assert "approved" in r.stdout
    meta = C.load_item(p)["meta"]
    assert meta["status"] == "approved"
    assert meta["approvals"][0]["note"] == "ship it"
    assert "(none)" in (root / "approvals" / "queue.md").read_text()


def test_reject_records_decision(tmp_path):
    root = _brain(tmp_path)
    p = C.create_item(root, "onpage-fix", "fix2", "t", "b",
                      "https://example.com/2", "s")
    r = run_cli("reject", str(p), "--actor", "operator", "--channel", "telegram")
    assert r.returncode == 0, r.stderr
    assert C.load_item(p)["meta"]["status"] == "rejected"


def test_status_moves_approved_to_applied(tmp_path):
    root = _brain(tmp_path)
    p = C.create_item(root, "onpage-fix", "fix3", "t", "b",
                      "https://example.com/3", "s")
    C.set_status(p, "approved", actor="operator", channel="in-session")
    r = run_cli("status", str(p), "applied", "--actor", "agent")
    assert r.returncode == 0, r.stderr
    assert "applied" in r.stdout
    assert C.load_item(p)["meta"]["status"] == "applied"


def test_approve_applied_item_exits_nonzero_with_message(tmp_path):
    root = _brain(tmp_path)
    p = C.create_item(root, "onpage-fix", "fix4", "t", "b",
                      "https://example.com/4", "s")
    C.set_status(p, "approved", actor="operator", channel="in-session")
    C.set_status(p, "applied", actor="agent")
    r = run_cli("approve", str(p), "--actor", "operator", "--channel", "cli")
    assert r.returncode != 0
    assert "illegal transition" in r.stderr


def test_missing_args_exit_nonzero(tmp_path):
    assert run_cli("approve").returncode != 0            # no item path
    root = _brain(tmp_path)
    p = C.create_item(root, "onpage-fix", "fix5", "t", "b",
                      "https://example.com/5", "s")
    assert run_cli("approve", str(p)).returncode != 0    # no --actor/--channel
    assert run_cli("status", str(p), "--actor", "a").returncode != 0  # no status


def test_reset_to_proposed_cli_repairs_and_rebuilds_queue(tmp_path):
    root = _brain(tmp_path)
    p = C.create_item(root, "content-brief", "born-wrong", "t", "b", "", "s")
    raw = p.read_text()
    assert "status: proposed" in raw
    p.write_text(raw.replace("status: proposed", "status: drafted", 1))
    C.rebuild_queue(root)
    assert "ILLEGAL-STATE" in (root / "approvals" / "queue.md").read_text()
    r = run_cli("reset-to-proposed", str(p), "--actor", "operator")
    assert r.returncode == 0, r.stderr
    assert "proposed" in r.stdout
    assert C.load_item(p)["meta"]["status"] == "proposed"
    q = (root / "approvals" / "queue.md").read_text()
    assert "ILLEGAL-STATE" not in q   # repaired item rejoins the normal queue
    assert "born-wrong" in q          # as an ordinary pending row


def test_reset_to_proposed_cli_refuses_item_with_history(tmp_path):
    root = _brain(tmp_path)
    p = C.create_item(root, "onpage-fix", "fix-hist", "t", "b",
                      "https://example.com/h", "s")
    C.set_status(p, "approved", actor="operator", channel="in-session")
    r = run_cli("reset-to-proposed", str(p), "--actor", "operator")
    assert r.returncode != 0
    assert "approval history" in r.stderr
    assert C.load_item(p)["meta"]["status"] == "approved"


def test_nonexistent_item_exits_nonzero(tmp_path):
    _brain(tmp_path)
    r = run_cli("approve", str(tmp_path / "b" / "proposals" / "ghost.md"),
                "--actor", "x", "--channel", "cli")
    assert r.returncode != 0
    assert r.stderr.strip()
