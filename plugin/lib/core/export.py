"""CSV export from the brain for BI tools. Stdlib only.

Flattens the brain's plain files - signals/, keywords/history.tsv,
outcomes/ - into CSV a spreadsheet or BI tool imports directly. Read-only
over the brain: the only writes are the CSV files themselves, under a
dated runs/ folder. The data is the user's own files, so export is a
right, not an upsell (ROADMAP, v0.4).

The export file set (signals.csv, keywords.csv, outcomes.csv, in
runs/<UTCdate>-export/) is canonical here; docs/INFORMATION-MAP.md in the
repo tracks who quotes it.
"""
from __future__ import annotations
import csv
import datetime as _dt
import re
from pathlib import Path

# The daily's structured metric forms (hoo-daily steps 2.5-2.6).
METRICS = ("clicks", "impressions", "sessions", "ai_referrals")
_METRIC = re.compile(r"\b(clicks|impressions|sessions|ai_referrals):\s*(\S+)")
_SIGNAL_FILE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")

# Outcome records are best-effort: skills write them as prose plus keys.
_OUTCOME_KEYS = {"date": ("date", "applied", "when"),
                 "action": ("action", "changed", "change"),
                 "status": ("status",),
                 "verified": ("verified",)}
_KEYLINE = re.compile(r"^\s*([A-Za-z_-]+)\s*:\s*(.+?)\s*$")


def _write_csv(path: Path, header: list, rows: list) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def _signal_rows(root) -> tuple[list, int]:
    """(rows, skipped) from signals/*.md metric lines. A line carrying at
    least one metric token whose value does not parse as an integer is
    skipped whole and counted - partial rows from a garbled line would be
    worse than none. Lines with no metric token are narrative, not skipped."""
    rows, skipped = [], 0
    signals = Path(root) / "signals"
    for f in sorted(signals.glob("*.md")) if signals.is_dir() else []:
        if not _SIGNAL_FILE.match(f.name):
            continue
        date = f.stem
        for line in f.read_text().splitlines():
            matches = _METRIC.findall(line)
            if not matches:
                continue
            parsed = []
            for metric, raw in matches:
                try:
                    parsed.append((metric, int(raw.rstrip(",.;:)"))))
                except ValueError:
                    parsed = None
                    break
            if parsed is None:
                skipped += 1
                continue
            rows.extend([date, m, str(v)] for m, v in parsed)
    return rows, skipped


def export_signals(root, out_dir) -> Path:
    """signals/*.md metric lines -> signals.csv (date, metric, value)."""
    rows, _ = _signal_rows(root)
    return _write_csv(Path(out_dir) / "signals.csv",
                      ["date", "metric", "value"], rows)


def export_keywords(root, out_dir) -> Path | None:
    """keywords/history.tsv -> keywords.csv, columns verbatim. None when
    the history file does not exist yet."""
    src = Path(root) / "keywords" / "history.tsv"
    if not src.exists():
        return None
    rows = [line.split("\t") for line in src.read_text().splitlines()]
    header = rows[0] if rows else []
    return _write_csv(Path(out_dir) / "keywords.csv", header, rows[1:])


def export_outcomes(root, out_dir) -> Path | None:
    """outcomes/*.md records -> outcomes.csv (date, item, action, status,
    verified), best-effort key parse. The item is the filename stem; a key
    the record never states stays empty - absent is recorded as absent,
    never guessed. Rollback .json files are not records. None when there
    are no records."""
    outcomes = Path(root) / "outcomes"
    records = sorted(outcomes.glob("*.md")) if outcomes.is_dir() else []
    if not records:
        return None
    rows = []
    for f in records:
        found = {}
        for line in f.read_text().splitlines():
            m = _KEYLINE.match(line)
            if not m:
                continue
            key = m.group(1).lower()
            for col, aliases in _OUTCOME_KEYS.items():
                if key in aliases and col not in found:
                    found[col] = m.group(2)
        rows.append([found.get("date", ""), f.stem, found.get("action", ""),
                     found.get("status", ""), found.get("verified", "")])
    return _write_csv(Path(out_dir) / "outcomes.csv",
                      ["date", "item", "action", "status", "verified"], rows)


def export_all(root) -> dict:
    """Run all three exports into <root>/runs/<UTCdate>-export/. Returns
    {"dir": Path, "files": [Path, ...], "skipped_lines": int} - absent
    sources are simply not in the file list, never an error."""
    root = Path(root)
    today = _dt.datetime.now(_dt.timezone.utc).date().strftime("%Y%m%d")
    out_dir = root / "runs" / f"{today}-export"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, skipped = _signal_rows(root)
    files = [_write_csv(out_dir / "signals.csv",
                        ["date", "metric", "value"], rows)]
    for fn in (export_keywords, export_outcomes):
        path = fn(root, out_dir)
        if path is not None:
            files.append(path)
    return {"dir": out_dir, "files": files, "skipped_lines": skipped}
