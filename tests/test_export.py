import csv
import datetime
import shutil
import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from core.init_site_repo import init_site_repo  # noqa: E402
from core import export  # noqa: E402


def _brain(tmp_path):
    return init_site_repo(tmp_path / "brain", "https://example.com", "Example")


def _read_csv(path):
    with open(path, newline="") as fh:
        return list(csv.reader(fh))


# -- signals -------------------------------------------------------------------

def test_export_signals_parses_metric_lines(tmp_path):
    root = _brain(tmp_path)
    (root / "signals" / "2026-07-17.md").write_text(
        "- [2026-07-17T06:00:00Z] clicks: 41, impressions: 1200, sessions: 33\n"
        "- [2026-07-17T06:00:01Z] ai_referrals: 3 (top: /post-a 2, /post-b 1)\n"
        "- [2026-07-17T06:00:02Z] no notable movement (checked: gsc, ga4)\n")
    out = export.export_signals(root, tmp_path / "out")
    rows = _read_csv(out)
    assert rows[0] == ["date", "metric", "value"]
    assert ["2026-07-17", "clicks", "41"] in rows
    assert ["2026-07-17", "impressions", "1200"] in rows
    assert ["2026-07-17", "sessions", "33"] in rows
    assert ["2026-07-17", "ai_referrals", "3"] in rows
    # the narrative line contributes no rows
    assert len(rows) == 5


def test_export_signals_skips_malformed_line_and_counts_it(tmp_path):
    root = _brain(tmp_path)
    (root / "signals" / "2026-07-17.md").write_text(
        "- [2026-07-17T06:00:00Z] clicks: 41\n"
        "- [2026-07-17T06:00:01Z] clicks: many, impressions: 1200\n")
    out_dir = tmp_path / "out"
    out = export.export_signals(root, out_dir)
    rows = _read_csv(out)
    # the malformed line is skipped whole - no partial rows from it
    assert rows == [["date", "metric", "value"],
                    ["2026-07-17", "clicks", "41"]]
    summary = export.export_all(root)
    assert summary["skipped_lines"] == 1


def test_export_signals_multiple_days_dated_from_filename(tmp_path):
    root = _brain(tmp_path)
    (root / "signals" / "2026-07-16.md").write_text(
        "- [2026-07-16T06:00:00Z] ai_referrals: 0\n")
    (root / "signals" / "2026-07-17.md").write_text(
        "- [2026-07-17T06:00:00Z] sessions: 20\n")
    rows = _read_csv(export.export_signals(root, tmp_path / "out"))
    assert ["2026-07-16", "ai_referrals", "0"] in rows
    assert ["2026-07-17", "sessions", "20"] in rows


def test_export_signals_empty_brain_writes_header_only(tmp_path):
    root = _brain(tmp_path)
    rows = _read_csv(export.export_signals(root, tmp_path / "out"))
    assert rows == [["date", "metric", "value"]]


# -- keywords ------------------------------------------------------------------

def test_export_keywords_passthrough(tmp_path):
    root = _brain(tmp_path)
    (root / "keywords" / "history.tsv").write_text(
        "date\tkeyword\tposition\tclicks\timpressions\n"
        "2026-07-14\tcloud calling\t7.2\t12\t840\n"
        "2026-07-14\tzero keyword\t\t0\t0\n")
    out = export.export_keywords(root, tmp_path / "out")
    rows = _read_csv(out)
    assert rows == [
        ["date", "keyword", "position", "clicks", "impressions"],
        ["2026-07-14", "cloud calling", "7.2", "12", "840"],
        ["2026-07-14", "zero keyword", "", "0", "0"],
    ]


def test_export_keywords_missing_returns_none(tmp_path):
    root = _brain(tmp_path)
    assert export.export_keywords(root, tmp_path / "out") is None


# -- outcomes ------------------------------------------------------------------

def test_export_outcomes_best_effort_parse(tmp_path):
    root = _brain(tmp_path)
    (root / "outcomes").mkdir(exist_ok=True)
    (root / "outcomes" / "p-20260701-title-fix.md").write_text(
        "---\n"
        "item: p-20260701-title-fix\n"
        "date: 2026-07-01\n"
        "action: rewrote title + meta description\n"
        "status: applied\n"
        "verified: true\n"
        "---\n"
        "Rollback: p-20260701-title-fix-rollback.json\n")
    out = export.export_outcomes(root, tmp_path / "out")
    rows = _read_csv(out)
    assert rows[0] == ["date", "item", "action", "status", "verified"]
    assert rows[1] == ["2026-07-01", "p-20260701-title-fix",
                       "rewrote title + meta description", "applied", "true"]


def test_export_outcomes_missing_keys_stay_empty_and_item_falls_back_to_filename(tmp_path):
    root = _brain(tmp_path)
    (root / "outcomes").mkdir(exist_ok=True)
    (root / "outcomes" / "p-20260702-freeform.md").write_text(
        "What changed: something, recorded loosely.\n")
    rows = _read_csv(export.export_outcomes(root, tmp_path / "out"))
    assert rows[1] == ["", "p-20260702-freeform", "", "", ""]


def test_export_outcomes_skips_rollback_json_and_none_when_no_records(tmp_path):
    root = _brain(tmp_path)
    (root / "outcomes").mkdir(exist_ok=True)
    (root / "outcomes" / "p-20260701-x-rollback.json").write_text("{}")
    assert export.export_outcomes(root, tmp_path / "out") is None


def test_export_outcomes_none_when_dir_absent(tmp_path):
    root = _brain(tmp_path)
    shutil.rmtree(root / "outcomes")
    assert export.export_outcomes(root, tmp_path / "out") is None


# -- export_all ----------------------------------------------------------------

def test_export_all_creates_dated_dir_and_reports(tmp_path):
    root = _brain(tmp_path)
    (root / "signals" / "2026-07-17.md").write_text(
        "- [2026-07-17T06:00:00Z] clicks: 41\n")
    (root / "keywords" / "history.tsv").write_text(
        "date\tkeyword\tposition\tclicks\timpressions\n")
    summary = export.export_all(root)
    today = datetime.datetime.now(datetime.timezone.utc).date().strftime("%Y%m%d")
    assert summary["dir"] == root / "runs" / f"{today}-export"
    assert summary["dir"].is_dir()
    names = sorted(p.name for p in summary["files"])
    # outcomes absent -> not in the file list, and nothing crashed
    assert names == ["keywords.csv", "signals.csv"]
    assert summary["skipped_lines"] == 0
    for p in summary["files"]:
        assert p.exists()


def test_export_all_missing_sources_do_not_crash(tmp_path):
    root = _brain(tmp_path)
    summary = export.export_all(root)
    assert [p.name for p in summary["files"]] == ["signals.csv"]
    assert summary["skipped_lines"] == 0


# -- advisory redaction over the produced CSVs ---------------------------------
#
# export reports what its own output carries. It never edits a CSV: the files
# are the user's data, and a guard that quietly rewrites them would be worse
# than the finding it reported.

from core import redact  # noqa: E402

PLANTED_KEY = "api_key=FAKE-API-KEY-VALUE-abcdefghij"


def test_export_all_reports_a_finding_in_the_produced_csv(tmp_path):
    root = _brain(tmp_path)
    (root / "outcomes").mkdir(exist_ok=True)
    (root / "outcomes" / "p-20260720-title.md").write_text(
        "date: 2026-07-20\n"
        f"action: rotated the key, {PLANTED_KEY}, then re-applied the title\n"
        "status: applied\n")
    out = export.export_all(root)
    assert "redaction" in out
    assert "1 high" in out["redaction"]["summary"]
    assert out["redaction"]["findings"][0]["tier"] == "high"
    # Masked in the report, untouched in the file.
    assert PLANTED_KEY not in out["redaction"]["findings"][0]["excerpt"]
    written = (out["dir"] / "outcomes.csv").read_text()
    assert PLANTED_KEY in written, "export edited the CSV instead of reporting"


def test_export_all_reports_nothing_for_a_clean_brain(tmp_path):
    root = _brain(tmp_path)
    (root / "signals" / "2026-07-17.md").write_text(
        "- [2026-07-17T06:00:00Z] clicks: 41, impressions: 1200\n")
    out = export.export_all(root)
    assert out["redaction"] == {"summary": "", "findings": []}


def test_export_all_still_exports_when_the_scan_raises(tmp_path, monkeypatch):
    def boom(_text):
        raise RuntimeError("scanner exploded")

    monkeypatch.setattr(redact, "scan", boom)
    root = _brain(tmp_path)
    (root / "signals" / "2026-07-17.md").write_text(
        "- [2026-07-17T06:00:00Z] clicks: 41\n")
    out = export.export_all(root)
    assert out["files"], "the guard cost us the export"
    assert out["redaction"] == {"summary": "", "findings": []}
