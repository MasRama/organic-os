#!/usr/bin/env bash
# organic-os gate red-team: prove the approval gates actually block what they
# claim to block, instead of trusting the docstrings.
#
# Builds a throwaway brain repo in a temp dir (cleaned on exit) and drives
# core.contracts against it directly - the same functions onsite-apply and
# onsite-publish call before every mutating write.
#
# Usage: ./scripts/verify-gates.sh
#   exit 0 = every probe behaved as designed
#   exit N = probe N did not behave as designed (see output above the summary)
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

BRAIN="$(mktemp -d)"
trap 'rm -rf "$BRAIN"' EXIT

PYTHONPATH="plugin/lib" python3 - "$BRAIN" <<'PYEOF'
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])

from core.init_site_repo import init_site_repo
from core import contracts as C

init_site_repo(root, site_url="https://verify-gates.invalid", site_name="Verify Gates")

fail_at = 0


def probe(n, desc, fn):
    global fail_at
    try:
        fn()
        print(f"PASS  probe {n}: {desc}")
    except AssertionError as e:
        print(f"FAIL  probe {n}: {desc}")
        print(f"      {e}")
        if not fail_at:
            fail_at = n


def item(slug, kind="onpage-fix"):
    return C.create_item(root, kind=kind, slug=slug, title="t", body="b",
                          target=f"https://verify-gates.invalid/{slug}",
                          source="verify-gates")


def p1():
    p = item("p1")
    try:
        C.require_approved(p)
    except C.ContractError:
        return
    raise AssertionError("require_approved did not raise on a fresh proposed item")


def p2():
    p = item("p2")
    try:
        C.set_status(p, "applied", actor="verify-gates")
    except C.ContractError:
        return
    raise AssertionError("set_status allowed proposed -> applied directly")


def p3():
    p = item("p3")
    C.set_status(p, "rejected", actor="verify-gates", channel="in-session")
    try:
        C.require_approval_lineage(p)
    except C.ContractError:
        return
    raise AssertionError("require_approval_lineage did not raise on a rejected item")


def p4():
    p = item("p4")
    raw = p.read_text()
    assert "status: proposed" in raw, "unexpected frontmatter shape, cannot hand-edit"
    p.write_text(raw.replace("status: proposed", "status: approved", 1))
    try:
        C.require_approval_lineage(p)
    except C.ContractError:
        return
    raise AssertionError(
        "require_approval_lineage passed a hand-edited status with no approvals record")


def p5():
    p = item("p5", kind="content-brief")
    C.set_status(p, "approved", actor="verify-gates", channel="in-session")
    C.set_status(p, "drafted", actor="verify-gates")
    C.require_approval_lineage(p)  # must not raise


def p6():
    prof = root / "site-profile.yaml"
    text = prof.read_text()
    text = re.sub(r"schema_version:\s*\d+", "schema_version: 99", text)
    prof.write_text(text)
    result = C.check_schema(root)
    assert result["compatible"] is False, f"expected incompatible, got {result}"
    assert "update the plugin" in result["action"], f"expected update-plugin action, got {result}"


def p7():
    from onsite.wp import WPClient

    class RecordingSession:
        def __init__(self):
            self.calls = []
        def request(self, method, url, **kw):
            self.calls.append((method, url))

    sess = RecordingSession()
    wp = WPClient("https://verify-gates.invalid/wp-json", "gate", "pw",
                  session=sess, dry_run=True)

    # Gate ordering holds in dry-run: a proposed item still refuses.
    p = item("p7")
    blocked = False
    try:
        C.require_approved(p)
    except C.ContractError:
        blocked = True
    assert blocked, "require_approved passed a proposed item under a dry-run client"

    # Once approved, a dry-run apply logs intent and makes zero session calls.
    C.set_status(p, "approved", actor="verify-gates", channel="in-session")
    C.require_approved(p)  # the gate opens on the real approval
    out = wp.update_rankmath(7, title="dry")
    wp.update_post(7, title="dry")
    wp.create_post(title="t", content="c", slug="p7-dry")
    assert out.get("dry_run") is True, f"dry-run response not marked: {out}"
    assert sess.calls == [], f"dry-run apply reached the session: {sess.calls}"
    assert len(wp.dry_run_log) == 3, \
        f"expected 3 logged write intents, got {wp.dry_run_log}"


def p8():
    p = item("p8")
    C.set_status(p, "approved", actor="verify-gates", channel="in-session")
    C.require_approved(p)  # a fresh approval passes

    # Rewrite the approval timestamp to 40 days ago - simulates aging, which
    # is why a direct file edit is fine inside this probe and nowhere else.
    doc = C.load_item(p)
    old = (datetime.datetime.now(datetime.timezone.utc)
           - datetime.timedelta(days=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc["meta"]["approvals"][-1]["at"] = old
    C._dump(p, doc["meta"], doc["body"])

    blocked = False
    try:
        C.require_approved(p)
    except C.ContractError as e:
        assert "expired" in str(e), f"block reason does not mention expiry: {e}"
        blocked = True
    assert blocked, "require_approved passed a 40-day-old approval"
    assert C.load_item(p)["meta"]["status"] == "approved", \
        "the gate changed the item's status on expiry (must stay re-confirmable)"

    # Re-confirm through the contract CLI - the exact command the block
    # message names - and the gate opens again on the fresh entry.
    env = dict(os.environ, PYTHONPATH="plugin/lib")
    r = subprocess.run([sys.executable, "-m", "core", "approve", str(p),
                        "--actor", "verify-gates", "--channel", "in-session"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, f"CLI re-confirm failed: {r.stderr}"
    assert len(C.load_item(p)["meta"]["approvals"]) == 2, \
        "re-confirm did not append a fresh approval entry"
    C.require_approved(p)  # must not raise


probe(1, "require_approved on a fresh proposed item raises (gate closed by default)", p1)
probe(2, "set_status proposed -> applied directly raises (no skipping the approval step)", p2)
probe(3, "require_approval_lineage on a rejected item raises", p3)
probe(4, "hand-edited status: approved with no approvals record still raises "
         "(lineage check defeats hand-editing)", p4)
probe(5, "a drafted item with a real approved lineage passes require_approval_lineage "
         "(the gate opens only the front door)", p5)
probe(6, "check_schema on a schema_version: 99 brain refuses with the update-plugin action", p6)
probe(7, "dry-run does not relax the gate: a proposed item still refuses, and an "
         "approved dry-run apply makes zero session calls", p7)
probe(8, "an approval aged past the TTL blocks with an expiry reason, keeps its "
         "status, and re-confirming via the CLI reopens the gate", p8)

sys.exit(fail_at)
PYEOF
status=$?

if [ "$status" -eq 0 ]; then
  printf '\nverify-gates: all 8 probes behaved as designed\n'
else
  printf '\nverify-gates: probe %d did not behave as designed\n' "$status"
fi
exit "$status"
