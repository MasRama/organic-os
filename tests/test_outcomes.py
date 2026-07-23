import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import pytest  # noqa: E402
from core import contracts as C  # noqa: E402
from core import outcomes as O  # noqa: E402

FULL_RECORD = """---
item: p-20260601-pricing-title
url: https://example.invalid/pricing
applied_at: 2026-06-01T09:00:00Z
---
# Outcome: rewrite the /pricing title tag

Applied the approved title rewrite. Rendered head verified at apply time.

windows:
  before:
    start: 2026-05-04
    end: 2026-05-31
  after:
    start: 2026-06-02
    end: 2026-06-29
before:
  clicks: 120
  impressions: 3000
  position: 8.2
after:
  clicks: 180
  impressions: 3300
  position: 5.9
delta:
  clicks: 60
  impressions: 300
  position: -2.3

cause: unknown (before/after window not compared)
"""


def _write(tmp_path, text, name="p-20260601-pricing-title.md"):
    root = tmp_path / "outcomes"
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_text(text)
    return path


# -- parse_outcome -------------------------------------------------------------

def test_parse_outcome_round_trips_a_full_record(tmp_path):
    rec = O.parse_outcome(_write(tmp_path, FULL_RECORD))
    assert rec["item"] == "p-20260601-pricing-title"
    assert rec["url"] == "https://example.invalid/pricing"
    assert rec["applied_at"] == "2026-06-01T09:00:00Z"
    assert rec["claimed_before"] == {"clicks": 120, "impressions": 3000,
                                     "position": 8.2}
    assert rec["claimed_after"] == {"clicks": 180, "impressions": 3300,
                                    "position": 5.9}
    assert rec["claimed_delta"] == {"clicks": 60, "impressions": 300,
                                    "position": -2.3}
    assert rec["windows"] == {"before": {"start": "2026-05-04",
                                         "end": "2026-05-31"},
                              "after": {"start": "2026-06-02",
                                        "end": "2026-06-29"}}


def test_parse_outcome_keeps_prose_out_of_the_numbers(tmp_path):
    rec = O.parse_outcome(_write(tmp_path, FULL_RECORD))
    assert "Applied" not in rec["claimed_delta"]
    assert set(rec["claimed_delta"]) == {"clicks", "impressions", "position"}


def test_parse_outcome_tolerates_a_record_missing_optional_keys(tmp_path):
    path = _write(tmp_path, "Applied the fix. Nothing measured yet.\n",
                  name="p-20260701-thin.md")
    rec = O.parse_outcome(path)
    for key in ("url", "applied_at", "claimed_before", "claimed_after",
                "claimed_delta", "windows"):
        assert rec[key] is None, f"{key} should be None when the record omits it"


def test_parse_outcome_falls_back_to_the_filename_for_the_item(tmp_path):
    path = _write(tmp_path, "no keys here\n", name="p-20260701-thin.md")
    assert O.parse_outcome(path)["item"] == "p-20260701-thin"


def test_parse_outcome_reads_a_record_with_no_frontmatter(tmp_path):
    text = ("url: https://example.invalid/guide\n"
            "applied: 2026-06-10\n"
            "delta:\n  clicks: 40\n")
    rec = O.parse_outcome(_write(tmp_path, text, name="p-20260610-guide.md"))
    assert rec["url"] == "https://example.invalid/guide"
    assert rec["applied_at"] == "2026-06-10"
    assert rec["claimed_delta"] == {"clicks": 40}


def test_parse_outcome_accepts_alias_key_names(tmp_path):
    text = ("target: https://example.invalid/x\n"
            "claimed_before:\n  clicks: 10\n"
            "claimed_after:\n  clicks: 12\n")
    rec = O.parse_outcome(_write(tmp_path, text, name="p-1.md"))
    assert rec["url"] == "https://example.invalid/x"
    assert rec["claimed_before"] == {"clicks": 10}
    assert rec["claimed_after"] == {"clicks": 12}


def test_parse_outcome_takes_the_last_statement_of_a_repeated_key(tmp_path):
    text = "delta:\n  clicks: 10\ndelta:\n  clicks: 25\n"
    rec = O.parse_outcome(_write(tmp_path, text, name="p-2.md"))
    assert rec["claimed_delta"] == {"clicks": 25}


def test_parse_outcome_does_not_raise_on_broken_frontmatter(tmp_path):
    text = "---\nitem: [unclosed\n---\ndelta:\n  clicks: 5\n"
    rec = O.parse_outcome(_write(tmp_path, text, name="p-3.md"))
    assert rec["claimed_delta"] == {"clicks": 5}
    assert rec["item"] == "p-3"


# -- compare -------------------------------------------------------------------

def test_compare_agrees_within_tolerance():
    out = O.compare({"clicks": 100, "position": 5.0},
                    {"clicks": 103, "position": 5.1})
    assert out["agrees"] is True
    assert out["divergences"] == []
    assert sorted(out["compared"]) == ["clicks", "position"]


def test_compare_agrees_on_an_exact_match():
    out = O.compare({"clicks": 60}, {"clicks": 60})
    assert out["agrees"] is True
    assert out["divergences"] == []


def test_compare_flags_a_divergence_beyond_tolerance():
    out = O.compare({"clicks": 100}, {"clicks": 60})
    assert out["agrees"] is False
    assert len(out["divergences"]) == 1
    d = out["divergences"][0]
    assert d["metric"] == "clicks"
    assert d["claimed"] == 100
    assert d["recomputed"] == 60
    assert d["pct_diff"] == pytest.approx(0.4)


def test_compare_pct_diff_is_a_fraction_on_the_tolerance_scale():
    out = O.compare({"clicks": 110}, {"clicks": 100}, tolerance=0.05)
    assert out["divergences"][0]["pct_diff"] == pytest.approx(0.0909, abs=1e-4)
    assert O.compare({"clicks": 110}, {"clicks": 100},
                     tolerance=0.10)["agrees"] is True


def test_compare_detects_a_doctored_claim():
    """The point of the exercise: a record claiming a win the raw data does
    not show is caught, and the divergence names both numbers."""
    honest = {"clicks": 180, "impressions": 3300, "position": 5.9}
    doctored = {"clicks": 400, "impressions": 3300, "position": 1.2}
    out = O.compare(doctored, honest)
    assert out["agrees"] is False
    assert {d["metric"] for d in out["divergences"]} == {"clicks", "position"}
    clicks = next(d for d in out["divergences"] if d["metric"] == "clicks")
    assert clicks["claimed"] == 400 and clicks["recomputed"] == 180


def test_compare_marks_one_sided_metrics_unverifiable_not_divergent():
    out = O.compare({"clicks": 100, "ai_referrals": 12},
                    {"clicks": 100, "sessions": 40})
    assert out["agrees"] is True
    assert out["divergences"] == []
    reasons = {u["metric"]: u["reason"] for u in out["unverifiable"]}
    assert reasons == {"ai_referrals": "claimed only",
                       "sessions": "recomputed only"}
    one_sided = next(u for u in out["unverifiable"]
                     if u["metric"] == "ai_referrals")
    assert one_sided["claimed"] == 12 and one_sided["recomputed"] is None


def test_compare_marks_non_numeric_values_unverifiable():
    out = O.compare({"clicks": "unknown"}, {"clicks": 100})
    assert out["divergences"] == []
    assert out["unverifiable"][0]["metric"] == "clicks"
    assert out["unverifiable"][0]["reason"] == "not numeric"
    assert out["agrees"] is False, "nothing was compared, so nothing agreed"


def test_compare_with_no_shared_metric_does_not_claim_agreement():
    out = O.compare({"clicks": 10}, {"sessions": 10})
    assert out["agrees"] is False
    assert out["compared"] == []
    assert out["divergences"] == []
    assert len(out["unverifiable"]) == 2


def test_compare_on_two_empty_sides_agrees_with_nothing():
    out = O.compare({}, {})
    assert out["agrees"] is False
    assert out["compared"] == [] and out["unverifiable"] == []


def test_compare_handles_a_zero_on_either_side():
    assert O.compare({"clicks": 0}, {"clicks": 0})["agrees"] is True
    out = O.compare({"clicks": 10}, {"clicks": 0})
    assert out["agrees"] is False
    assert out["divergences"][0]["pct_diff"] == pytest.approx(1.0)


def test_compare_ignores_booleans_as_numbers():
    out = O.compare({"verified": True}, {"verified": True})
    assert out["compared"] == []
    assert out["unverifiable"][0]["reason"] == "not numeric"


def test_compare_reads_a_parsed_record_directly(tmp_path):
    rec = O.parse_outcome(_write(tmp_path, FULL_RECORD))
    out = O.compare(rec["claimed_delta"],
                    {"clicks": 61, "impressions": 295, "position": -2.25})
    assert out["agrees"] is True


def test_compare_refuses_a_negative_tolerance():
    with pytest.raises(C.ContractError):
        O.compare({"clicks": 1}, {"clicks": 1}, tolerance=-0.1)
