import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import pytest  # noqa: E402
from onsite.cms import CmsAdapter, SUPPORTED_CMS_TYPES, adapter_for  # noqa: E402
from onsite.wp import WPClient  # noqa: E402
from tests.test_wp import FakeSession  # noqa: E402


# -- the contract surface -----------------------------------------------------

CONTRACT_CALLS = [
    ("get_post", (42,), {}),
    ("get_rendered_head", ("https://play.example/page",), {}),
    ("update_post", (42,), {"title": "T"}),
    ("update_seo_meta", (42,), {"title": "T"}),
    ("create_post", ("T", "C", "t"), {}),
    ("snapshot", (42, ["title"]), {}),
    ("rollback", ({"post_id": 42},), {}),
    ("capabilities", (), {}),
    ("adapter_name", (), {}),
]


@pytest.mark.parametrize("method,args,kwargs",
                         CONTRACT_CALLS, ids=[c[0] for c in CONTRACT_CALLS])
def test_base_contract_method_raises_not_implemented(method, args, kwargs):
    with pytest.raises(NotImplementedError):
        getattr(CmsAdapter(), method)(*args, **kwargs)


# -- WPClient satisfies the contract ------------------------------------------

def make_client(sess=None, **kw):
    return WPClient("https://play.example/wp-json", "organic-agent", "secret",
                    session=sess or FakeSession(), **kw)


def test_wpclient_is_a_cms_adapter():
    assert isinstance(make_client(), CmsAdapter)


def test_wpclient_capabilities_shape():
    caps = make_client().capabilities()
    assert caps["seo_meta_fields"] is True
    assert caps["schema_injection"] is True
    assert caps["rendered_head_verify"] is True
    assert caps["author_profile_fields"] is True
    # Honest: core WP has no redirect REST surface; the apply skill
    # probes known plugin surfaces at run time.
    assert caps["redirects"] == "needs-plugin"
    assert caps["needs_human"] == ["seo-plugin-cache-purge", "plugin-settings"]


def test_wpclient_adapter_name():
    assert make_client().adapter_name() == "wordpress"


def test_update_seo_meta_writes_rankmath_meta():
    s = FakeSession(); c = make_client(s)
    c.update_seo_meta(42, title="New T", description="New D")
    method, url, payload = s.calls[-1]
    assert method == "POST" and url.endswith("/wp/v2/posts/42")
    assert payload["meta"]["rank_math_title"] == "New T"
    assert payload["meta"]["rank_math_description"] == "New D"


def test_get_rendered_head_hits_gethead_route():
    s = FakeSession(); c = make_client(s)
    c.get_rendered_head("https://play.example/page?variant=b")
    method, url, payload = s.calls[-1]
    assert method == "GET" and "/rankmath/v1/getHead?url=" in url


def test_dry_run_update_seo_meta_logs_under_the_wordpress_alias():
    # update_rankmath stays the implementation; the contract name delegates
    # to it, so a dry-run intent is logged under the adapter's own name.
    s = FakeSession(); c = make_client(s, dry_run=True)
    out = c.update_seo_meta(42, title="New T")
    assert s.calls == []
    assert out["dry_run"] is True
    assert c.dry_run_log[-1]["method"] == "update_rankmath"


# -- adapter_for factory ------------------------------------------------------

def _profile(**over):
    p = {"wordpress": {"endpoint": "https://play.example/wp-json",
                       "username": "organic-agent"}}
    p.update(over)
    return p


def test_adapter_for_explicit_wordpress_type():
    a = adapter_for(_profile(cms={"type": "wordpress"}), secret="pw")
    assert isinstance(a, WPClient)
    assert a.endpoint == "https://play.example/wp-json"
    assert a.adapter_name() == "wordpress"


def test_adapter_for_defaults_to_wordpress_when_endpoint_exists():
    a = adapter_for(_profile(), secret="pw")
    assert isinstance(a, WPClient)


def test_adapter_for_passes_session_and_dry_run_through():
    s = FakeSession()
    a = adapter_for(_profile(), secret="pw", session=s, dry_run=True)
    assert a.session is s
    assert a.dry_run is True


def test_adapter_for_unknown_type_raises_naming_supported():
    with pytest.raises(ValueError) as exc:
        adapter_for(_profile(cms={"type": "shopify"}))
    assert "shopify" in str(exc.value)
    for supported in SUPPORTED_CMS_TYPES:
        assert supported in str(exc.value)


def test_adapter_for_nothing_configured_raises_naming_supported():
    with pytest.raises(ValueError) as exc:
        adapter_for({})
    for supported in SUPPORTED_CMS_TYPES:
        assert supported in str(exc.value)
