import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import json  # noqa: E402
import pytest  # noqa: E402
from hoo.google_ads import tier, keyword_ideas, historical  # noqa: E402


class FakeIdeaService:
    def generate_keyword_ideas(self, request=None):
        class Idea:
            def __init__(self, text, vol, comp):
                self.text = text
                self.keyword_idea_metrics = type(
                    "M", (), {"avg_monthly_searches": vol, "competition": comp,
                              "competition_index": 55,
                              "low_top_of_page_bid_micros": 1_000_000,
                              "high_top_of_page_bid_micros": 5_000_000})()
        return [Idea("crm for smb", 1200, 3), Idea("smb crm pricing", 400, 2)]


class FakeClient:
    def __init__(self, planner_ok=True):
        self.planner_ok = planner_ok
    def get_service(self, name):
        if name == "KeywordPlanIdeaService":
            if not self.planner_ok:
                raise RuntimeError("PERMISSION_DENIED: planner blocked")
            return FakeIdeaService()
        raise AssertionError(name)
    def get_type(self, name):
        return type("T", (), {"__init__": lambda s: None})()


def test_detect_tier_basic():
    assert tier.detect(FakeClient(planner_ok=True), customer_id="1") == "basic"

def test_detect_tier_explorer():
    assert tier.detect(FakeClient(planner_ok=False), customer_id="1") == "explorer"


def test_keyword_ideas_normalizes(tmp_path):
    out = keyword_ideas.run(FakeClient(), customer_id="1",
                            seeds=["crm"], site_seed=None, geo="2356", lang="1000",
                            cache_dir=tmp_path)
    assert out[0] == {"keyword": "crm for smb", "avg_monthly_searches": 1200,
                      "competition": 3, "competition_index": 55,
                      "low_bid": 1.0, "high_bid": 5.0}


def test_keyword_ideas_cache_hit(tmp_path):
    a = keyword_ideas.run(FakeClient(), "1", ["crm"], None, "2356", "1000", tmp_path)
    class Exploding:
        def get_service(self, n): raise AssertionError("must use cache")
    b = keyword_ideas.run(Exploding(), "1", ["crm"], None, "2356", "1000", tmp_path)
    assert a == b


def test_historical_batches(monkeypatch):
    calls = []
    def fake_fetch(client, customer_id, batch, geo, lang):
        calls.append(list(batch)); return [{"keyword": k} for k in batch]
    monkeypatch.setattr(historical, "_fetch_batch", fake_fetch)
    monkeypatch.setattr(historical.time, "sleep", lambda s: None)
    out = historical.run(FakeClient(), "1", [f"k{i}" for i in range(450)],
                         geo="2356", lang="1000")
    assert len(calls) == 3 and len(out) == 450  # 200 + 200 + 50
