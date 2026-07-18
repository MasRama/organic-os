"""Normalize Keyword Planner UI exports (and Auction Insights CSVs) so users
without API access still get keyword data in."""
import csv
import re
from pathlib import Path

_SUFFIX = {"K": 1_000, "M": 1_000_000}
_RANGE_SPLIT = re.compile(r"\s*[-–]\s*")  # hyphen or en-dash


def load_planner_csv(path) -> list[dict]:
    path = Path(path)
    encoding, delimiter = "utf-8-sig", ","
    with path.open("rb") as fh:
        bom = fh.read(2)
    if bom in (b"\xff\xfe", b"\xfe\xff"):
        # Real Keyword Planner downloads are UTF-16 tab-separated.
        encoding, delimiter = "utf-16", "\t"
    rows = []
    with path.open(newline="", encoding=encoding) as fh:
        for r in csv.DictReader(fh, delimiter=delimiter):
            k = (r.get("Keyword") or "").strip()
            if not k:
                continue
            row = {"keyword": k,
                   "avg_monthly_searches": _num(r.get("Avg. monthly searches", "0")),
                   "competition": (r.get("Competition") or "").strip()}
            for col, field in (("Top of page bid (low range)", "low_bid"),
                               ("Top of page bid (high range)", "high_bid")):
                money = _money(r.get(col))
                if money is not None:
                    row[field] = money
            rows.append(row)
    return rows


def _num(v: str) -> int:
    v = (v or "").replace(",", "").replace('"', "").strip()
    parts = _RANGE_SPLIT.split(v)
    if len(parts) == 2 and parts[0]:  # "10-100" or "1K - 10K" -> midpoint
        return (_scalar(parts[0]) + _scalar(parts[1])) // 2
    return _scalar(v)


def _scalar(v: str) -> int:
    v = v.strip().upper()
    mult = 1
    if v[-1:] in _SUFFIX:
        mult = _SUFFIX[v[-1]]
        v = v[:-1]
    try:
        return int(float(v) * mult)
    except ValueError:
        return 0


def _money(v):
    """Bid cell -> float. Strips currency symbols, commas, spaces; returns
    None (skip the field, never raise) on empty or garbage input."""
    if not v:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(v))
    try:
        return float(cleaned)
    except ValueError:
        return None
