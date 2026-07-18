"""File contracts for the site brain. The ONLY code that reads/writes brain files.

Item = a brief or proposal: markdown file with YAML frontmatter.
Lifecycle: proposed -> approved|rejected; approved -> applied|drafted|failed;
drafted -> published; applied|published -> measured.
("failed" marks an approved item whose apply-verify failed and was rolled back;
it happens pre-applied, so applied -> failed is deliberately illegal.)
Skillbook: append-only entries with IDs; updates touch single entries only.
"""
from __future__ import annotations
import datetime as _dt
import os
import re
from pathlib import Path

import yaml

TRANSITIONS = {
    "proposed": {"approved", "rejected"},
    "approved": {"applied", "drafted", "failed"},
    "drafted": {"published"},
    "applied": {"measured"},
    "published": {"measured"},
}
KINDS = {"onpage-fix", "content-brief", "publish", "strategy"}

SCHEMA_VERSION = 1


class ContractError(Exception):
    pass


# -- schema versioning ---------------------------------------------------------

def check_schema(root) -> dict:
    """Returns {"version": int, "compatible": bool, "action": str}.

    Missing site-profile.yaml -> version 0, compatible False, action
    "run /organic-os:setup". Missing schema_version key (pre-v0.1.3 brain)
    -> version 1 assumed, compatible True, action "stamp" (layout is
    identical; setup update mode adds the key). version == SCHEMA_VERSION
    -> compatible True, action "none". version < SCHEMA_VERSION ->
    compatible False, action "run /organic-os:setup to migrate".
    version > SCHEMA_VERSION -> compatible False, action "update the
    plugin (/plugin update organic-os)".
    """
    path = Path(root) / "site-profile.yaml"
    if not path.exists():
        return {"version": 0, "compatible": False, "action": "run /organic-os:setup"}
    data = yaml.safe_load(path.read_text()) or {}
    if "schema_version" not in data:
        return {"version": 1, "compatible": True, "action": "stamp"}
    version = data["schema_version"]
    if version == SCHEMA_VERSION:
        return {"version": version, "compatible": True, "action": "none"}
    if version < SCHEMA_VERSION:
        return {"version": version, "compatible": False,
                "action": "run /organic-os:setup to migrate"}
    return {"version": version, "compatible": False,
            "action": "update the plugin (/plugin update organic-os)"}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -- signals ------------------------------------------------------------------

def append_signal(root, text: str, date: str | None = None) -> Path:
    root = Path(root)
    date = date or _dt.datetime.now(_dt.timezone.utc).date().isoformat()
    f = root / "signals" / f"{date}.md"
    stamp = _now()
    with f.open("a") as fh:
        fh.write(f"- [{stamp}] {text}\n")
    return f


# -- items (briefs + proposals) ----------------------------------------------

def _folder(root: Path, kind: str) -> Path:
    return root / ("briefs" if kind == "content-brief" else "proposals")


def create_item(root, kind: str, slug: str, title: str, body: str,
                target: str, source: str) -> Path:
    if kind not in KINDS:
        raise ContractError(f"unknown kind {kind!r}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise ContractError(f"bad slug {slug!r} - use lowercase letters, digits, hyphens")
    root = Path(root)
    date = _dt.datetime.now(_dt.timezone.utc).date().strftime("%Y%m%d")
    path = _folder(root, kind) / f"{date}-{slug}.md"
    if path.exists():
        raise ContractError(f"item exists: {path}")
    meta = {"id": f"{'b' if kind == 'content-brief' else 'p'}-{date}-{slug}",
            "kind": kind, "status": "proposed", "created": _now(),
            "title": title, "target": target, "source": source, "approvals": []}
    _dump(path, meta, body)
    return path


def load_item(path) -> dict:
    try:
        raw = Path(path).read_text()
    except FileNotFoundError:
        raise ContractError(f"no such item: {path}") from None
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise ContractError(f"no frontmatter: {path}")
    try:
        meta = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        raise ContractError(f"bad frontmatter yaml: {path}") from None
    return {"meta": meta, "body": m.group(2)}


def set_status(path, status: str, actor: str, channel: str | None = None,
               note: str | None = None) -> None:
    item = load_item(path)
    cur = item["meta"]["status"]
    if status not in TRANSITIONS.get(cur, set()):
        raise ContractError(f"illegal transition {cur} -> {status}")
    item["meta"]["status"] = status
    if status in {"approved", "rejected"}:
        entry = {"actor": actor, "channel": channel or "unknown",
                 "decision": status, "at": _now()}
        if note:
            entry["note"] = note
        item["meta"]["approvals"].append(entry)
    _dump(Path(path), item["meta"], item["body"])


def require_approved(path) -> dict:
    item = load_item(path)
    if item["meta"]["status"] != "approved":
        raise ContractError(
            f"MUTATION BLOCKED: {Path(path).name} is '{item['meta']['status']}', "
            "needs 'approved' with a recorded approval")
    return item


def mark_notified(path) -> None:
    item = load_item(path)
    item["meta"]["notified_at"] = _now()
    _dump(Path(path), item["meta"], item["body"])


def is_notified(item) -> bool:
    return bool(item["meta"].get("notified_at"))


# -- connectors -----------------------------------------------------------

CONNECTOR_STATUSES = {"verified", "unavailable", "declined"}


def record_connector(profile_path, name: str, status: str, context: str) -> None:
    """Updates the connectors: block in site-profile.yaml. status:
    'verified'|'unavailable'|'declined'. context: where the probe ran, e.g.
    'local-cli', 'cowork-cloud', 'ci'. Stored as 'name: {status: ...,
    context: ..., checked: <UTC date>}'. Never stores bare booleans.

    Only the named connector entry is touched - every other key in the
    connectors: block and the rest of the profile is left exactly as read,
    including pre-wave-1 profiles where sibling connectors are still bare
    strings ('available'/'absent'/'unknown').
    """
    if status not in CONNECTOR_STATUSES:
        raise ContractError(
            f"connector status must be one of {sorted(CONNECTOR_STATUSES)}, got {status!r}")
    path = Path(profile_path)
    data = yaml.safe_load(path.read_text()) or {}
    connectors = data.setdefault("connectors", {})
    connectors[name] = {
        "status": status,
        "context": context,
        "checked": _dt.datetime.now(_dt.timezone.utc).date().isoformat(),
    }
    _atomic_write(path, yaml.safe_dump(data, sort_keys=False))


# -- postflight scorecard ---------------------------------------------------

SCORECARD_STATUSES = {"pass", "degraded", "fail"}


def write_scorecard(root, checks: list) -> Path:
    """checks: list of {'name','status'('pass'|'degraded'|'fail'),'detail','fix'}.
    Writes <root>/runs/<UTCdate>-setup-scorecard/REPORT.md with a pass/degraded/
    fail table and the exact fix command per non-pass row. Returns the path.
    """
    today = _dt.datetime.now(_dt.timezone.utc).date().strftime("%Y%m%d")
    folder = Path(root) / "runs" / f"{today}-setup-scorecard"
    folder.mkdir(parents=True, exist_ok=True)

    lines = [f"# Setup scorecard - {today}", "",
             "| Check | Status | Detail |", "|---|---|---|"]
    fixes = []
    for c in checks:
        status = c["status"]
        if status not in SCORECARD_STATUSES:
            raise ContractError(
                f"scorecard status must be one of {sorted(SCORECARD_STATUSES)}, got {status!r}")
        lines.append(f"| {c['name']} | {status} | {c.get('detail', '')} |")
        if status != "pass":
            fix = c.get("fix", "")
            if fix:
                fixes.append(f"- **{c['name']}**: `{fix}`")

    if fixes:
        lines += ["", "## Fixes", ""] + fixes

    path = folder / "REPORT.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def require_approval_lineage(path) -> dict:
    """For post-approval lifecycle stages (e.g. drafted) where require_approved's status check no longer applies; safe because approved -> rejected is an illegal transition, so an approved lineage cannot be revoked."""
    item = load_item(path)
    approvals = item["meta"].get("approvals") or []
    if not any(a.get("decision") == "approved" for a in approvals):
        raise ContractError(
            f"MUTATION BLOCKED: {Path(path).name} has no approved decision in its lineage")
    return item


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def _dump(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, "---\n" + yaml.safe_dump(meta, sort_keys=False).strip()
                  + "\n---\n" + body.lstrip("\n"))


# -- skillbook ----------------------------------------------------------------

_ENTRY = re.compile(r"^(~~)?(S-\d{3,}) \[evidence: (\w+)\] "
                    r"\[helpful: (\d+), harmful: (\d+), last-confirmed: ([0-9-]+)\] (.*)$")


def skillbook_append(root, text: str, evidence: str, source: str) -> str:
    if evidence not in {"strong", "moderate", "anecdotal"}:
        raise ContractError("evidence must be strong|moderate|anecdotal")
    book = Path(root) / "skillbook.md"
    ids = [int(m.group(2)[2:]) for line in book.read_text().splitlines()
           if (m := _ENTRY.match(line))]
    sid = f"S-{(max(ids) + 1 if ids else 1):03d}"
    today = _dt.datetime.now(_dt.timezone.utc).date().isoformat()
    with book.open("a") as fh:
        fh.write(f"{sid} [evidence: {evidence}] [helpful: 0, harmful: 0, "
                 f"last-confirmed: {today}] {text} ({source})\n")
    return sid


def skillbook_update(root, sid: str, helpful: int = 0, harmful: int = 0,
                     deprecate: bool = False, edit: str | None = None) -> None:
    book = Path(root) / "skillbook.md"
    out, found = [], False
    for line in book.read_text().splitlines():
        m = _ENTRY.match(line)
        if m and m.group(2) == sid:
            if m.group(1):
                raise ContractError(f"{sid} is deprecated")
            found = True
            h, x = int(m.group(4)) + helpful, int(m.group(5)) + harmful
            text = edit if edit is not None else m.group(7)
            today = _dt.datetime.now(_dt.timezone.utc).date().isoformat()
            new = (f"{sid} [evidence: {m.group(3)}] [helpful: {h}, harmful: {x}, "
                   f"last-confirmed: {today}] {text}")
            out.append(f"~~{new}~~ DEPRECATED" if deprecate else new)
        else:
            out.append(line)
    if not found:
        raise ContractError(f"no skillbook entry {sid}")
    _atomic_write(book, "\n".join(out) + "\n")


# -- approvals queue ----------------------------------------------------------

def rebuild_queue(root) -> Path:
    root = Path(root)
    rows = []
    for folder in ("briefs", "proposals"):
        for f in sorted((root / folder).glob("*.md")):
            try:
                meta = load_item(f)["meta"]
            except ContractError:
                rows.append(f"- MALFORMED: {folder}/{f.name}")
                continue
            # Lint: every approvals entry must carry a decision field. An
            # entry without one is the fingerprint of a hand-edit that
            # bypassed set_status - surface it, never silently accept it.
            for entry in meta.get("approvals") or []:
                if not isinstance(entry, dict) or "decision" not in entry:
                    rows.append(f"- MALFORMED-APPROVAL: {folder}/{f.name} "
                                "(entry missing decision field)")
                    break
            if meta["status"] == "proposed":
                rows.append(f"- `{meta['id']}` [{meta['kind']}] {meta['title']} "
                            f"(created {meta['created']}) -> {folder}/{f.name}")
    q = root / "approvals" / "queue.md"
    q.write_text("# Pending approvals\n\n" + ("\n".join(rows) + "\n" if rows else "(none)\n"))
    return q
