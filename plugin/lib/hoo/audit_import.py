"""External-audit import: best-effort parsing of a markdown audit report or
action plan (claude-seo shape) into findings organic-os can turn into gated
proposals. "They audit, we operate": the report format belongs to the
external tool and may vary between versions, so parsing is defensive -
whatever cannot be recognized as a finding is preserved as a raw excerpt in
`unparsed`, never dropped, and the finding text itself is kept verbatim.
Stdlib only.

Pattern credit: claude-seo (https://github.com/AgriciDaniel/claude-seo).
"""
from __future__ import annotations
import re

SEVERITIES = ("critical", "high", "medium", "low")

# Keyword -> onsite-audit dimension (SKILL.md steps 3-4). Insertion order is
# match order; llms.txt goes first so its dedicated note always wins.
# "deliberate-skip" is not a dimension: it flags a finding organic-os
# deliberately declines to act on, with the evidence.md position quoted.
DIMENSION_HINTS = {
    "llms.txt": "deliberate-skip",
    "sitemap": "page-essentials/sitemap-membership",
    "author": "author-entity",
    "e-e-a-t": "author-entity",
    "capsule": "answer-capsule",
    "answer": "answer-capsule",
    "meta description": "meta-length",
    "image": "images",
    "schema": "publisher-schema",
    "publisher": "publisher-schema",
    "redirect": "link-health",
    "404": "link-health",
}

ATTRIBUTION = ("Imported from an external audit report - pattern credit: "
               "claude-seo (https://github.com/AgriciDaniel/claude-seo).")

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_BOLD_LEAD = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+\*\*(.+?)\*\*")
_NUMBERED = re.compile(r"^\s{0,3}\d+[.)]\s+(\S.*)$")
_BULLET = re.compile(r"^\s{0,3}[-*+]\s+(\S.*)$")
_EVIDENCE = re.compile(r"\[(Measured|Inference|Unverified)\]")
_EFFORT = re.compile(r"(?i)\beffort\b[*\s]*[:=][*\s]*([^\n)\]|,]+)")
_SEV_WORD = re.compile(r"(?i)\b(critical|high|medium|low)\b")
_DATE_LINE = re.compile(
    r"(?im)^\**\s*(?:audit\s+|report\s+)?date\**\s*[:=]\s*(.+?)\s*$")
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_URL_LINE = re.compile(
    r"(?im)^\**\s*(?:site|url|domain|page)\**\s*[:=]\s*<?(\S+?)>?\s*$")
_URL = re.compile(r"https?://[^\s)>\]]+")


def _tier_severity(stack) -> str | None:
    """Nearest severity word in the current heading path, deepest first."""
    for _, title in reversed(stack):
        m = _SEV_WORD.search(title)
        if m:
            return m.group(1).lower()
    return None


def _clean_title(t: str) -> str:
    t = _EVIDENCE.sub("", t)
    t = re.sub(r"\*\*|`", "", t)
    return re.sub(r"\s+", " ", t).strip().strip(":").rstrip(".").strip()


def parse_report(text) -> dict:
    """Best-effort extraction from a markdown audit or action plan.

    Returns {"items": [...], "unparsed": [...], "source_meta": {...}}. An
    item is recognized from a bold-lead bullet or numbered entry anywhere,
    or any plain bullet inside a severity-tier heading (Critical/High/
    Medium/Low, emoji or plain). Everything else lands in `unparsed` as raw
    excerpts.
    """
    lines = (text or "").replace("\r\n", "\n").split("\n")
    items: list = []
    unparsed: list = []
    headings: list = []
    stack: list = []          # (level, title) heading path
    cur_item: dict | None = None
    cur_block: list = []

    def close_item():
        nonlocal cur_item
        if cur_item is None:
            return
        block = "\n".join(cur_item.pop("_lines")).rstrip()
        cur_item["body"] = block
        ev = _EVIDENCE.search(block)
        cur_item["evidence_label"] = ev.group(1) if ev else None
        ef = _EFFORT.search(block)
        cur_item["effort"] = ef.group(1).strip(" *") if ef else None
        items.append(cur_item)
        cur_item = None

    def close_block():
        nonlocal cur_block
        blk = "\n".join(cur_block).strip()
        if blk and not re.fullmatch(r"[-*_=\s]+", blk):
            unparsed.append(blk)
        cur_block = []

    for raw in lines:
        h = _HEADING.match(raw)
        if h:
            close_item()
            close_block()
            level, title = len(h.group(1)), h.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            headings.append(title)
            continue

        title = None
        m = _BOLD_LEAD.match(raw)
        if m:
            title = m.group(1)
        else:
            n = _NUMBERED.match(raw)
            if n:
                title = n.group(1)
            elif _tier_severity(stack) is not None:
                b = _BULLET.match(raw)
                if b:
                    title = b.group(1)
        if title is not None:
            close_item()
            close_block()
            cur_item = {"title": _clean_title(title),
                        "severity": _tier_severity(stack),
                        "section": " > ".join(t for _, t in stack),
                        "_lines": [raw]}
            continue

        if cur_item is not None:
            if raw.strip() == "" or raw.startswith((" ", "\t")):
                cur_item["_lines"].append(raw)
            elif cur_item["_lines"][-1].strip() == "":
                # Blank line then a flush-left paragraph: the item is over.
                close_item()
                cur_block.append(raw)
            else:
                cur_item["_lines"].append(raw)   # lazy continuation
            continue

        if raw.strip() == "":
            close_block()
        else:
            cur_block.append(raw)

    close_item()
    close_block()
    return {"items": items, "unparsed": unparsed,
            "source_meta": _source_meta(text or "", headings)}


def _source_meta(text: str, headings: list) -> dict:
    d = _DATE_LINE.search(text)
    date = d.group(1).strip() if d else None
    if date is None:
        iso = _ISO_DATE.search(text)
        date = iso.group(0) if iso else None
    url = None
    u = _URL_LINE.search(text)
    if u and u.group(1).lower().startswith(("http://", "https://")):
        url = u.group(1)
    if url is None:
        m = _URL.search(text)
        url = m.group(0) if m else None
    return {"headings": headings, "audit_date": date, "page_url": url}


def _slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return s[:60].rstrip("-")


def _mapping_note(item: dict) -> str:
    text = ((item.get("title") or "") + "\n" + (item.get("body") or "")).lower()
    for kw, dim in DIMENSION_HINTS.items():
        if kw in text:
            if dim == "deliberate-skip":
                return ("Dimension mapping: deliberate-skip. organic-os "
                        "treats llms.txt as an optional hedge, never a "
                        "visibility tactic: Ahrefs' 137K-site study found 97% "
                        "of llms.txt files never get read (see "
                        "plugin/docs/evidence.md). The finding is kept for "
                        "the human to weigh against that position, not "
                        "silently dropped.")
            return (f"Dimension mapping: overlaps our onsite-audit dimension "
                    f"`{dim}`. Our own audit covers this check; if the two "
                    "disagree, the disagreement is flagged for the human, "
                    "never silently rewritten.")
    return ("Dimension mapping: external-only. No overlapping organic-os "
            "audit dimension; imported as-is on the source audit's evidence.")


def _proposal_body(item: dict) -> str:
    label = item.get("evidence_label")
    ev_line = (f"Evidence label: [{label}] (preserved from the source audit)"
               if label else "Evidence label: none given by the source audit")
    quoted = "\n".join("> " + line if line else ">"
                       for line in (item.get("body") or "").split("\n"))
    lines = [
        f"Severity (source audit): {item.get('severity') or 'unspecified'} | "
        f"Effort (source audit): {item.get('effort') or 'unspecified'}",
        ev_line,
        f"Section in source report: {item.get('section') or '(top level)'}",
        "",
        "Original finding, verbatim:",
        "",
        quoted,
        "",
        _mapping_note(item),
        "",
        ATTRIBUTION,
    ]
    return "\n".join(lines) + "\n"


def to_proposals(parsed, max_items=5) -> list:
    """Ranks parsed items (critical > high > medium > low > unlabeled; ties
    keep document order) and returns at most `max_items` dicts shaped for
    core.contracts.create_item. `kind` is "onpage-fix" - the kind whose
    items land in proposals/ and are born `proposed`, so every import rides
    the normal approval gate."""
    rank = {s: i for i, s in enumerate(SEVERITIES)}
    ordered = sorted(parsed.get("items") or [],
                     key=lambda it: rank.get(it.get("severity"),
                                             len(SEVERITIES)))
    out, used = [], set()
    for item in ordered[:max_items]:
        base = _slugify(item.get("title") or "") or "imported-finding"
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        out.append({"kind": "onpage-fix", "slug": slug,
                    "title": item["title"], "body": _proposal_body(item)})
    return out
