"""GenerateKeywordHistoricalMetrics in batches of 200 with 1.1s spacing
(planning services are limited to 1 QPS per customer id)."""
import time

BATCH = 200
SPACING_S = 1.1


def run(client, customer_id: str, keywords, geo: str, lang: str) -> list[dict]:
    out = []
    for i in range(0, len(keywords), BATCH):
        if i:
            time.sleep(SPACING_S)
        out.extend(_fetch_batch(client, customer_id, keywords[i:i + BATCH], geo, lang))
    return out


def _fetch_batch(client, customer_id, batch, geo, lang) -> list[dict]:
    svc = client.get_service("KeywordPlanIdeaService")
    req = client.get_type("GenerateKeywordHistoricalMetricsRequest")
    req.customer_id = customer_id
    req.keywords.extend(batch)
    req.language = f"languageConstants/{lang}"
    req.geo_target_constants.append(f"geoTargetConstants/{geo}")
    req.historical_metrics_options.include_average_cpc = True
    rows = []
    for r in svc.generate_keyword_historical_metrics(request=req).results:
        m = r.keyword_metrics
        rows.append({"keyword": r.text,
                     "avg_monthly_searches": int(m.avg_monthly_searches or 0),
                     "competition": int(m.competition or 0),
                     "avg_cpc": (getattr(m, "average_cpc_micros", 0) or 0) / 1_000_000})
    return rows
