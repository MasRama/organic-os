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

def test_planner_csv_handles_suffixed_volumes(tmp_path):
    f = tmp_path / "kp.csv"
    f.write_text('Keyword,Avg. monthly searches,Competition\n'
                 'a,"1K - 10K",Low\nb,10K,Low\nc,1M,Low\n'
                 'd,"1K – 10K",Low\n')  # en-dash range
    rows = csv_import.load_planner_csv(f)
    assert rows[0]["avg_monthly_searches"] == 5500
    assert rows[1]["avg_monthly_searches"] == 10000
    assert rows[2]["avg_monthly_searches"] == 1000000
    assert rows[3]["avg_monthly_searches"] == 5500

def test_planner_csv_currency_bids(tmp_path):
    f = tmp_path / "kp.csv"
    f.write_text('Keyword,Avg. monthly searches,Competition,'
                 'Top of page bid (low range),Top of page bid (high range)\n'
                 'x,100,Low,"₹1,234.56",not-a-number\n')
    rows = csv_import.load_planner_csv(f)
    assert rows[0]["low_bid"] == 1234.56
    assert "high_bid" not in rows[0]  # garbage skipped, never raises

def test_planner_utf16_tsv(tmp_path):
    f = tmp_path / "kp.csv"
    content = ("Keyword\tAvg. monthly searches\tCompetition\n"
               "crm for smb\t1K - 10K\tHigh\n")
    f.write_bytes(content.encode("utf-16"))  # BOM + tab-separated, real download shape
    rows = csv_import.load_planner_csv(f)
    assert rows[0] == {"keyword": "crm for smb", "avg_monthly_searches": 5500,
                       "competition": "High"}
