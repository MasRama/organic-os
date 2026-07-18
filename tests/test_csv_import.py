import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from hoo.google_ads import csv_import  # noqa: E402

PLANNER_CSV = """Keyword,Avg. monthly searches,Competition,Top of page bid (low range),Top of page bid (high range)
crm for smb,1300,High,12.5,48.2
smb crm pricing,390,Medium,8.1,30.0
"""

def test_planner_csv_normalizes(tmp_path):
    f = tmp_path / "kp.csv"; f.write_text(PLANNER_CSV)
    rows = csv_import.load_planner_csv(f)
    assert rows[0] == {"keyword": "crm for smb", "avg_monthly_searches": 1300,
                      "competition": "High", "low_bid": 12.5, "high_bid": 48.2}

def test_planner_csv_handles_dash_volumes(tmp_path):
    f = tmp_path / "kp.csv"
    f.write_text('Keyword,Avg. monthly searches,Competition\nx,"10-100",Low\n')
    rows = csv_import.load_planner_csv(f)
    assert rows[0]["avg_monthly_searches"] == 55  # midpoint of a "10-100" range
