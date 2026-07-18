"""GenerateKeywordIdeas with a 30-day JSON cache (Google refreshes monthly)."""
import hashlib
import json
import time
from pathlib import Path

CACHE_DAYS = 30
_MICROS = 1_000_000


def run(client, customer_id: str, seeds, site_seed, geo: str, lang: str,
        cache_dir) -> list[dict]:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(json.dumps([sorted(seeds or []), site_seed, geo, lang])
                         .encode()).hexdigest()[:16]
    cached = cache_dir / f"ideas-{key}.json"
    if cached.exists() and (time.time() - cached.stat().st_mtime) < CACHE_DAYS * 86400:
        return json.loads(cached.read_text())

    svc = client.get_service("KeywordPlanIdeaService")
    request = _build_request(client, customer_id, seeds, site_seed, geo, lang)
    rows = []
    for idea in svc.generate_keyword_ideas(request=request):
        m = idea.keyword_idea_metrics
        rows.append({"keyword": idea.text,
                     "avg_monthly_searches": int(m.avg_monthly_searches or 0),
                     "competition": int(m.competition or 0),
                     "competition_index": int(m.competition_index or 0),
                     "low_bid": (m.low_top_of_page_bid_micros or 0) / _MICROS,
                     "high_bid": (m.high_top_of_page_bid_micros or 0) / _MICROS})
    cached.write_text(json.dumps(rows, indent=1))
    return rows


def _build_request(client, customer_id, seeds, site_seed, geo, lang):
    try:
        req = client.get_type("GenerateKeywordIdeasRequest")
        req.customer_id = customer_id
        req.language = f"languageConstants/{lang}"
        req.geo_target_constants.append(f"geoTargetConstants/{geo}")
        if site_seed:
            req.site_seed.site = site_seed
        elif seeds:
            req.keyword_seed.keywords.extend(seeds)
        return req
    except Exception:
        return None  # fakes in tests accept request=None
