"""Normalize Keyword Planner UI exports (and Auction Insights CSVs) so users
without API access still get keyword data in."""
import csv
from pathlib import Path


def load_planner_csv(path) -> list[dict]:
    rows = []
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            k = (r.get("Keyword") or "").strip()
            if not k:
                continue
            row = {"keyword": k,
                   "avg_monthly_searches": _num(r.get("Avg. monthly searches", "0")),
                   "competition": (r.get("Competition") or "").strip()}
            if r.get("Top of page bid (low range)"):
                row["low_bid"] = float(r["Top of page bid (low range)"])
            if r.get("Top of page bid (high range)"):
                row["high_bid"] = float(r["Top of page bid (high range)"])
            rows.append(row)
    return rows


def _num(v: str) -> int:
    v = (v or "").replace(",", "").replace('"', "").strip()
    if "-" in v:  # "10-100" range -> midpoint
        lo, hi = v.split("-", 1)
        try:
            return (int(lo) + int(hi)) // 2
        except ValueError:
            return 0
    try:
        return int(float(v))
    except ValueError:
        return 0
