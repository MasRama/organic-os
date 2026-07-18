"""File contracts for the site brain. The ONLY code that reads/writes brain files.

Item = a brief or proposal: markdown file with YAML frontmatter.
Lifecycle: proposed -> approved|rejected; approved -> applied|drafted;
drafted -> published; applied|published -> measured.
Skillbook: append-only entries with IDs; updates touch single entries only.
"""
from __future__ import annotations
import datetime as _dt
import re
from pathlib import Path

import yaml

TRANSITIONS = {
    "proposed": {"approved", "rejected"},
    "approved": {"applied", "drafted"},
    "drafted": {"published"},
    "applied": {"measured"},
    "published": {"measured"},
}
KINDS = {"onpage-fix", "content-brief", "publish", "strategy"}


class ContractError(Exception):
    pass


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -- signals ------------------------------------------------------------------

def append_signal(root, text: str, date: str | None = None) -> Path:
    root = Path(root)
    date = date or _dt.date.today().isoformat()
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
    root = Path(root)
    date = _dt.date.today().strftime("%Y%m%d")
    path = _folder(root, kind) / f"{date}-{slug}.md"
    if path.exists():
        raise ContractError(f"item exists: {path}")
    meta = {"id": f"{'b' if kind == 'content-brief' else 'p'}-{date}-{slug}",
            "kind": kind, "status": "proposed", "created": _now(),
            "title": title, "target": target, "source": source, "approvals": []}
    _dump(path, meta, body)
    return path


def load_item(path) -> dict:
    raw = Path(path).read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise ContractError(f"no frontmatter: {path}")
    return {"meta": yaml.safe_load(m.group(1)), "body": m.group(2)}


def set_status(path, status: str, actor: str, channel: str | None = None) -> None:
    item = load_item(path)
    cur = item["meta"]["status"]
    if status not in TRANSITIONS.get(cur, set()):
        raise ContractError(f"illegal transition {cur} -> {status}")
    item["meta"]["status"] = status
    if status in {"approved", "rejected"}:
        item["meta"]["approvals"].append(
            {"actor": actor, "channel": channel or "unknown",
             "decision": status, "at": _now()})
    _dump(Path(path), item["meta"], item["body"])


def require_approved(path) -> dict:
    item = load_item(path)
    if item["meta"]["status"] != "approved":
        raise ContractError(
            f"MUTATION BLOCKED: {Path(path).name} is '{item['meta']['status']}', "
            "needs 'approved' with a recorded approval")
    return item


def _dump(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False).strip()
                    + "\n---\n" + body.lstrip("\n"))


# -- skillbook ----------------------------------------------------------------

_ENTRY = re.compile(r"^(~~)?(S-\d{3}) \[evidence: (\w+)\] "
                    r"\[helpful: (\d+), harmful: (\d+), last-confirmed: ([0-9-]+)\] (.*)$")


def skillbook_append(root, text: str, evidence: str, source: str) -> str:
    if evidence not in {"strong", "moderate", "anecdotal"}:
        raise ContractError("evidence must be strong|moderate|anecdotal")
    book = Path(root) / "skillbook.md"
    ids = [int(m.group(2)[2:]) for line in book.read_text().splitlines()
           if (m := _ENTRY.match(line))]
    sid = f"S-{(max(ids) + 1 if ids else 1):03d}"
    today = _dt.date.today().isoformat()
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
            found = True
            h, x = int(m.group(4)) + helpful, int(m.group(5)) + harmful
            text = edit if edit is not None else m.group(7)
            today = _dt.date.today().isoformat()
            new = (f"{sid} [evidence: {m.group(3)}] [helpful: {h}, harmful: {x}, "
                   f"last-confirmed: {today}] {text}")
            out.append(f"~~{new}~~ DEPRECATED" if deprecate else new)
        else:
            out.append(line)
    if not found:
        raise ContractError(f"no skillbook entry {sid}")
    book.write_text("\n".join(out) + "\n")


# -- approvals queue ----------------------------------------------------------

def rebuild_queue(root) -> Path:
    root = Path(root)
    rows = []
    for folder in ("briefs", "proposals"):
        for f in sorted((root / folder).glob("*.md")):
            meta = load_item(f)["meta"]
            if meta["status"] == "proposed":
                rows.append(f"- `{meta['id']}` [{meta['kind']}] {meta['title']} "
                            f"(created {meta['created']}) -> {folder}/{f.name}")
    q = root / "approvals" / "queue.md"
    q.write_text("# Pending approvals\n\n" + ("\n".join(rows) + "\n" if rows else "(none)\n"))
    return q
