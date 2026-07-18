import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import json  # noqa: E402
from types import SimpleNamespace  # noqa: E402
import pytest  # noqa: E402
from hoo.google_ads import tier, keyword_ideas, historical  # noqa: E402


class FakeIdeaService:
    def __init__(self, error=None):
        self.error = error

    def generate_keyword_ideas(self, request=None):
        if self.error:
            raise RuntimeError(self.error)
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
    def __init__(self, planner_ok=True, error="PERMISSION_DENIED: planner blocked"):
        self.planner_ok = planner_ok
        self.error = error
    def get_service(self, name):
        if name == "KeywordPlanIdeaService":
            return FakeIdeaService(None if self.planner_ok else self.error)
        raise AssertionError(name)
    def get_type(self, name):
        return SimpleNamespace(customer_id="", language="",
                               geo_target_constants=[],
                               keyword_seed=SimpleNamespace(keywords=[]),
                               site_seed=SimpleNamespace(site=""))


def test_detect_tier_basic():
    assert tier.detect(FakeClient(planner_ok=True), customer_id="1") == "basic"

def test_detect_tier_explorer():
    assert tier.detect(FakeClient(planner_ok=False), customer_id="1") == "explorer"

def test_detect_tier_dead_auth_reraises():
    dead = FakeClient(planner_ok=False, error="invalid_grant: token expired")
    with pytest.raises(RuntimeError):
        tier.detect(dead, customer_id="1")


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


def test_keyword_ideas_corrupt_cache_is_miss(tmp_path):
    keyword_ideas.run(FakeClient(), "1", ["crm"], None, "2356", "1000", tmp_path)
    cache_file = next(tmp_path.glob("ideas-*.json"))
    cache_file.write_text("{not json")
    out = keyword_ideas.run(FakeClient(), "1", ["crm"], None, "2356", "1000", tmp_path)
    assert out[0]["keyword"] == "crm for smb"
    assert json.loads(cache_file.read_text())  # cache rewritten clean


def test_historical_batches(monkeypatch):
    calls = []
    def fake_fetch(client, customer_id, batch, geo, lang):
        calls.append(list(batch)); return [{"keyword": k} for k in batch]
    monkeypatch.setattr(historical, "_fetch_batch", fake_fetch)
    monkeypatch.setattr(historical.time, "sleep", lambda s: None)
    out = historical.run(FakeClient(), "1", [f"k{i}" for i in range(450)],
                         geo="2356", lang="1000")
    assert len(calls) == 3 and len(out) == 450  # 200 + 200 + 50


def test_historical_retries_failed_batch_once(monkeypatch):
    calls = {"n": 0}
    def flaky(client, customer_id, batch, geo, lang):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient 503")
        return [{"keyword": k} for k in batch]
    monkeypatch.setattr(historical, "_fetch_batch", flaky)
    monkeypatch.setattr(historical.time, "sleep", lambda s: None)
    out = historical.run(FakeClient(), "1", [f"k{i}" for i in range(250)],
                         geo="2356", lang="1000")
    assert len(out) == 250 and calls["n"] == 3  # batch 1 retried, batch 2 clean


def test_historical_raises_with_partial_after_two_failures(monkeypatch):
    def fetch(client, customer_id, batch, geo, lang):
        if batch[0] == "k200":
            raise RuntimeError("hard failure")
        return [{"keyword": k} for k in batch]
    monkeypatch.setattr(historical, "_fetch_batch", fetch)
    monkeypatch.setattr(historical.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError) as ei:
        historical.run(FakeClient(), "1", [f"k{i}" for i in range(250)],
                       geo="2356", lang="1000")
    assert "batch 200" in str(ei.value)
    assert len(ei.value.partial) == 200  # batch 1's rows survive
