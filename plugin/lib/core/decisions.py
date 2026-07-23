"""Durable decision memory for the site brain.

A decision is a markdown file in `<root>/decisions/`: YAML frontmatter
(date, title, choice, actor, scope, and the item it came from) plus the
rationale as the body. Two calls, no index file, no dependency:

- `record` writes one, on rejection and on any other call a skill makes.
- `search` finds prior decisions whose title, scope, or rationale overlap
  the terms a skill is about to propose work against.

Why it exists: without it the loop re-proposes work a human already
rejected, because the item's own rejection note dies with the item. The
skills search here BEFORE calling `create_item`, so a re-proposal is
either skipped or carries the reason it is being raised again.

Same write discipline as every other brain file: atomic writes through
`core.contracts`, never a raw open() on a status-bearing file.
"""
from __future__ import annotations
import datetime as _dt
import re
from pathlib import Path

from . import contracts as C

_SLUG_OK = re.compile(r"[a-z0-9][a-z0-9-]*")
_TOKEN = re.compile(r"[a-z0-9]+")


def slugify(title: str) -> str:
    """Title -> the slug shape `create_item` enforces: lowercase letters,
    digits, hyphens. Refuses anything that cannot produce one rather than
    inventing a filename."""
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    if not _SLUG_OK.fullmatch(slug):
        raise C.ContractError(
            f"cannot derive a slug from title {title!r} - "
            "use lowercase letters, digits, hyphens")
    return slug


def record(root, title: str, choice: str, rationale: str, actor: str,
           scope: str, item=None) -> Path:
    """Writes `<root>/decisions/<UTCdate>-<slug>.md` and returns its path.

    A second decision with the same title on the same day gets a `-2`,
    `-3` suffix: memory is append-only, so a new record never overwrites
    an older one.
    """
    slug = slugify(title)
    date = _dt.datetime.now(_dt.timezone.utc).date()
    folder = Path(root) / "decisions"
    path = folder / f"{date.strftime('%Y%m%d')}-{slug}.md"
    n = 1
    while path.exists():
        n += 1
        path = folder / f"{date.strftime('%Y%m%d')}-{slug}-{n}.md"
    meta = {"date": date.isoformat(), "title": title, "choice": choice,
            "actor": actor, "scope": scope}
    if item is not None:
        meta["item"] = str(item)
    # _dump is the shared frontmatter writer and routes through
    # contracts._atomic_write, so a decision file parses with load_item.
    C._dump(path, meta, rationale)
    return path


def search(root, terms) -> list:
    """Prior decisions whose title, scope, or rationale share a token with
    `terms` (a string or an iterable of strings), newest first.

    Case-insensitive token overlap - deliberately loose, because the cost
    of one irrelevant hit a human skims is far lower than the cost of
    re-proposing rejected work. A brain with no `decisions/` directory
    returns [] rather than raising.
    """
    if isinstance(terms, str):
        terms = [terms]
    wanted = {t for term in terms or [] for t in _TOKEN.findall(str(term).lower())}
    folder = Path(root) / "decisions"
    if not wanted or not folder.is_dir():
        return []
    hits = []
    for f in sorted(folder.glob("*.md")):
        try:
            doc = C.load_item(f)
        except C.ContractError:
            continue  # not a decision record; leave it alone
        meta = doc["meta"] or {}
        body = doc["body"]
        haystack = " ".join(str(meta.get(k) or "")
                            for k in ("title", "scope")) + " " + body
        if not wanted & set(_TOKEN.findall(haystack.lower())):
            continue
        hits.append({"path": str(f), "date": str(meta.get("date") or ""),
                     "title": meta.get("title") or "", "choice": meta.get("choice") or "",
                     "scope": meta.get("scope") or "", "item": meta.get("item"),
                     "rationale": body.strip()})
    hits.sort(key=lambda h: (h["date"], h["path"]), reverse=True)
    return hits
