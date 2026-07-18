"""Detect the effective Google Ads access tier by probing, not guessing."""
from . import keyword_ideas

_EXPLORER_MARKERS = ("PERMISSION_DENIED", "DEVELOPER_TOKEN_NOT_APPROVED",
                     "DEVELOPER_TOKEN_PROHIBITED")
_DEAD_AUTH_MARKERS = ("UNAUTHENTICATED", "INVALID_GRANT")


def detect(client, customer_id: str) -> str:
    """Probe the planner with a real one-seed ideas request.

    Returns 'basic' when the planner responds. Returns 'explorer' only when
    auth works but the planner is blocked (PERMISSION_DENIED, or a developer
    token that is not approved / prohibited). Dead auth (UNAUTHENTICATED,
    invalid_grant) and any other error re-raise; the caller reports 'none'."""
    try:
        svc = client.get_service("KeywordPlanIdeaService")
        req = keyword_ideas._build_request(
            client, customer_id, ["marketing"], None, "2840", "1000")
        svc.generate_keyword_ideas(request=req)
        return "basic"
    except Exception as e:
        msg = str(e).upper()
        if any(m in msg for m in _DEAD_AUTH_MARKERS):
            raise
        if any(m in msg for m in _EXPLORER_MARKERS):
            return "explorer"
        raise


def real_client():
    """Build the real GoogleAdsClient from env vars. Lazy import by design."""
    import os
    from google.ads.googleads.client import GoogleAdsClient  # noqa: WPS433
    cfg = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    if os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID"):
        cfg["login_customer_id"] = os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]
    return GoogleAdsClient.load_from_dict(cfg)
