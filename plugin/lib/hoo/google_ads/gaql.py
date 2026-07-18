"""Run an arbitrary GAQL query and emit JSON rows (own-account reporting;
works at Explorer tier). Used by the keyword-intel skill for search-term
mining and keyword coverage."""
import json
import sys


def run(client, customer_id: str, query: str) -> list[dict]:
    svc = client.get_service("GoogleAdsService")
    rows = []
    for row in svc.search(customer_id=customer_id, query=query):
        rows.append(_flatten(row))
    return rows


def _flatten(row) -> dict:
    # google-ads rows are proto-plus; str() round-trip keeps this dependency-free
    try:
        from google.protobuf.json_format import MessageToDict
        return MessageToDict(row._pb, preserving_proto_field_name=True)
    except Exception:
        return {"raw": str(row)}


# Usage: PYTHONPATH="$CLAUDE_PLUGIN_ROOT/lib" python3 -m hoo.google_ads.gaql <customer_id> "<query>"
# (the relative import below requires module execution, not direct file execution)
if __name__ == "__main__":
    from .tier import real_client
    client = real_client()
    print(json.dumps(run(client, sys.argv[1], sys.argv[2]), indent=1))
