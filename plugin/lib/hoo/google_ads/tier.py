"""Detect the effective Google Ads access tier by probing, not guessing."""


def detect(client, customer_id: str) -> str:
    """Returns 'basic' (planner works), 'explorer' (auth ok, planner blocked),
    or raises whatever auth error the client throws (caller reports 'none')."""
    try:
        svc = client.get_service("KeywordPlanIdeaService")
        # A zero-seed dry probe is not supported; probe with one throwaway seed.
        probe = getattr(svc, "generate_keyword_ideas", None)
        if probe is None:
            return "explorer"
        svc.generate_keyword_ideas(request=None)
        return "basic"
    except Exception as e:  # PERMISSION_DENIED / DEVELOPER_TOKEN_NOT_APPROVED
        if "PERMISSION" in str(e).upper() or "TOKEN" in str(e).upper():
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
