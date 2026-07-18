import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import pytest  # noqa: E402
from core import registry as R  # noqa: E402


def test_load_missing_file_returns_empty_structure(tmp_path):
    assert R.load(tmp_path / "sites.yaml") == {"active": None, "sites": {}}


def test_register_two_sites_switches_active_to_latest(tmp_path):
    path = tmp_path / "sites.yaml"
    slug1 = R.register("https://one.com", "One", "/brains/one", path=path)
    slug2 = R.register("https://two.com", "Two", "/brains/two", path=path)
    data = R.load(path)
    assert data["active"] == slug2
    assert set(data["sites"]) == {slug1, slug2}
    assert data["sites"][slug1]["brain"] == "/brains/one"
    assert data["sites"][slug1]["url"] == "https://one.com"
    assert data["sites"][slug1]["name"] == "One"


def test_set_active_switches_back(tmp_path):
    path = tmp_path / "sites.yaml"
    slug1 = R.register("https://one.com", "One", "/brains/one", path=path)
    R.register("https://two.com", "Two", "/brains/two", path=path)
    R.set_active(slug1, path=path)
    assert R.load(path)["active"] == slug1
    assert R.get_active(path=path)["slug"] == slug1
    assert R.get_active(path=path)["brain"] == "/brains/one"


def test_set_active_unknown_slug_raises_with_known_slugs_listed(tmp_path):
    path = tmp_path / "sites.yaml"
    R.register("https://one.com", "One", "/brains/one", path=path)
    with pytest.raises(ValueError, match="one-com"):
        R.set_active("ghost-site", path=path)


def test_slug_derivation_strips_www_and_hyphenates_dots(tmp_path):
    path = tmp_path / "sites.yaml"
    slug = R.register("https://www.my-site.co.uk/x", "My Site", "/brains/x", path=path)
    assert slug == "my-site-co-uk"


def test_register_upserts_existing_slug_instead_of_duplicating(tmp_path):
    path = tmp_path / "sites.yaml"
    slug1 = R.register("https://one.com", "One", "/brains/one", path=path)
    slug2 = R.register("https://one.com", "One Renamed", "/brains/one", path=path)
    assert slug1 == slug2
    data = R.load(path)
    assert len(data["sites"]) == 1
    assert data["sites"][slug1]["name"] == "One Renamed"


def test_register_locks_down_file_permissions(tmp_path):
    path = tmp_path / "sites.yaml"
    R.register("https://one.com", "One", "/brains/one", path=path)
    mode = path.stat().st_mode & 0o777
    assert mode == 0o600


def test_get_active_none_when_no_registry(tmp_path):
    assert R.get_active(tmp_path / "sites.yaml") is None
