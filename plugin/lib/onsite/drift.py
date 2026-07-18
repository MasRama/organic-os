"""Site drift watch: snapshot the on-page SEO fields organic-os cares about
and compare against a stored baseline to catch changes made outside the
loop - a theme update rewriting titles, a plugin dropping schema, a manual
edit nobody logged. Needs a connected CMS adapter (onsite/cms.py;
WordPress today): there is nothing to snapshot without one.

Uses only the adapter's get_post() - no new adapter surface needed. The
tracked field names are the WordPress adapter's today (rank_math_*,
agent_jsonld). The baseline lives at <root>/drift/baseline.json, written
through core.contracts' atomic-write helper (lib/onsite writes brain-repo
files only through core, per plugin/docs/site-repo-contract.md).
"""
from __future__ import annotations
import json
from pathlib import Path

from core.contracts import _atomic_write

FIELDS = ("title", "rank_math_title", "rank_math_description", "canonical",
          "slug", "status", "jsonld_present")


def snapshot_pages(wp, page_ids) -> dict:
    """{page_id: {title, rank_math_title, rank_math_description, canonical,
    slug, status, jsonld_present}} for each id in page_ids, via the
    adapter's get_post(). `wp` is any CmsAdapter (duck-typed: only
    get_post is used). Keys are stringified page ids (JSON round-trips
    object keys as strings, so snapshots and the loaded baseline compare
    on the same key type)."""
    snap = {}
    for page_id in page_ids:
        post = wp.get_post(page_id)
        meta = post.get("meta", {}) or {}
        snap[str(page_id)] = {
            "title": post.get("title", {}).get("raw", ""),
            "rank_math_title": meta.get("rank_math_title", ""),
            "rank_math_description": meta.get("rank_math_description", ""),
            "canonical": meta.get("rank_math_canonical_url", ""),
            "slug": post.get("slug", ""),
            "status": post.get("status", ""),
            "jsonld_present": bool(meta.get("agent_jsonld")),
        }
    return snap


def baseline_path(root) -> Path:
    return Path(root) / "drift" / "baseline.json"


def save_baseline(root, snap: dict) -> Path:
    path = baseline_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, json.dumps(snap, indent=2, sort_keys=True) + "\n")
    return path


def compare(root, snap: dict) -> list:
    """[{'page_id', 'field', 'was', 'now'}, ...] for every field that differs
    from the stored baseline. No baseline on disk yet (first run establishes
    one, nothing to compare against) -> [], never raises."""
    path = baseline_path(root)
    if not path.exists():
        return []
    baseline = json.loads(path.read_text())
    changes = []
    for page_id, fields in snap.items():
        old = baseline.get(page_id, {})
        for field, now in fields.items():
            was = old.get(field)
            if was != now:
                changes.append({"page_id": page_id, "field": field,
                                "was": was, "now": now})
    return changes
