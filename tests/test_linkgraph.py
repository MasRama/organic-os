"""linkgraph tests: synthetic sites through a fake fetcher, no network.

The crawler only ever sees its own site (ADR-0006 bans third-party
scraping; your own property is yours to crawl): same-host BFS with a
page cap, injectable fetcher like wp.py's session pattern. analyze()
turns the graph into findings: broken links, orphans, hubs, shallow
pages, redirect chains.
"""
import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from onsite.linkgraph import analyze, crawl  # noqa: E402


BASE = "https://site.example"


def page(*links, title="Page"):
    anchors = "".join(f'<a href="{h}">x</a>' for h in links)
    return (200, "<html><head><title>" + title + "</title></head>"
                 "<body>" + anchors + "</body></html>")


def fetch_for(pages):
    """Fake fetcher: {url: (status, html)}; anything else is a 404."""
    def fetch(url):
        return pages.get(url, (404, ""))
    return fetch


def small_site():
    """home -> about, blog; about -> home; blog -> home, post-1;
    post-1 -> home. Plus an off-host link and a mailto on home."""
    return {
        f"{BASE}/": page(f"{BASE}/about", f"{BASE}/blog",
                         "https://elsewhere.example/out",
                         "mailto:me@site.example", title="Home"),
        f"{BASE}/about": page(f"{BASE}/", title="About"),
        f"{BASE}/blog": page(f"{BASE}/", f"{BASE}/post-1", title="Blog"),
        f"{BASE}/post-1": page(f"{BASE}/", title="Post 1"),
    }


# -- crawl ---------------------------------------------------------------------

def test_crawl_discovers_every_same_host_page():
    graph = crawl(f"{BASE}/", fetch_for(small_site()))
    assert set(graph) == {f"{BASE}/", f"{BASE}/about", f"{BASE}/blog",
                          f"{BASE}/post-1"}


def test_crawl_never_follows_off_host_links():
    graph = crawl(f"{BASE}/", fetch_for(small_site()))
    assert "https://elsewhere.example/out" not in graph
    assert "https://elsewhere.example/out" not in graph[f"{BASE}/"]["out"]


def test_crawl_skips_non_http_schemes():
    graph = crawl(f"{BASE}/", fetch_for(small_site()))
    assert not any(u.startswith("mailto:") for u in graph[f"{BASE}/"]["out"])


def test_crawl_honors_max_pages_cap():
    pages = {f"{BASE}/p{i}": page(f"{BASE}/p{i + 1}") for i in range(20)}
    graph = crawl(f"{BASE}/p0", fetch_for(pages), max_pages=5)
    assert len(graph) == 5
    assert f"{BASE}/p0" in graph


def test_crawl_records_status_and_title():
    graph = crawl(f"{BASE}/", fetch_for(small_site()))
    assert graph[f"{BASE}/"]["status"] == 200
    assert graph[f"{BASE}/"]["title"] == "Home"
    assert graph[f"{BASE}/about"]["title"] == "About"


def test_crawl_strips_fragments_and_query_for_graph_keys():
    pages = {
        f"{BASE}/": page(f"{BASE}/docs?tab=install#setup"),
        f"{BASE}/docs": page(title="Docs"),
    }
    graph = crawl(f"{BASE}/", fetch_for(pages))
    assert f"{BASE}/docs" in graph
    assert graph[f"{BASE}/"]["out"] == [f"{BASE}/docs"]
    # ...but the as-written resolved link survives for reporting.
    assert graph[f"{BASE}/"]["out_raw"] == [f"{BASE}/docs?tab=install#setup"]


def test_crawl_resolves_relative_hrefs():
    pages = {
        f"{BASE}/blog/": page("post-1", "/about"),
        f"{BASE}/blog/post-1": page(),
        f"{BASE}/about": page(),
    }
    graph = crawl(f"{BASE}/blog/", fetch_for(pages))
    assert graph[f"{BASE}/blog/"]["out"] == [f"{BASE}/blog/post-1",
                                             f"{BASE}/about"]


def test_crawl_dedupes_out_and_drops_self_links():
    pages = {
        f"{BASE}/": page(f"{BASE}/a", f"{BASE}/a", f"{BASE}/#top"),
        f"{BASE}/a": page(),
    }
    graph = crawl(f"{BASE}/", fetch_for(pages))
    assert graph[f"{BASE}/"]["out"] == [f"{BASE}/a"]


def test_crawl_seed_urls_join_the_frontier():
    # /lonely is in the sitemap but nothing links to it: only the seed
    # list gets it crawled at all.
    pages = {**small_site(), f"{BASE}/lonely": page(title="Lonely")}
    graph = crawl(f"{BASE}/", fetch_for(pages),
                  seed_urls=[f"{BASE}/lonely"])
    assert f"{BASE}/lonely" in graph


def test_crawl_ignores_off_host_seed_urls():
    graph = crawl(f"{BASE}/", fetch_for(small_site()),
                  seed_urls=["https://elsewhere.example/paste"])
    assert "https://elsewhere.example/paste" not in graph


# -- analyze -------------------------------------------------------------------

def test_analyze_broken_link_named_with_its_source_page():
    pages = {
        f"{BASE}/": page(f"{BASE}/gone"),
        f"{BASE}/gone": (404, ""),
    }
    graph = crawl(f"{BASE}/", fetch_for(pages))
    out = analyze(graph)
    assert out["broken"] == [(f"{BASE}/", f"{BASE}/gone", 404)]


def test_analyze_unreachable_target_is_broken_too():
    pages = {
        f"{BASE}/": page(f"{BASE}/dead"),
        f"{BASE}/dead": (0, ""),  # fetcher convention for a network error
    }
    graph = crawl(f"{BASE}/", fetch_for(pages))
    assert analyze(graph)["broken"] == [(f"{BASE}/", f"{BASE}/dead", 0)]


def test_analyze_orphan_detection_from_the_seed_list():
    pages = {**small_site(), f"{BASE}/lonely": page(title="Lonely")}
    graph = crawl(f"{BASE}/", fetch_for(pages),
                  seed_urls=[f"{BASE}/lonely"])
    assert analyze(graph)["orphans"] == [f"{BASE}/lonely"]


def test_analyze_hub_ranking_by_inbound_count():
    graph = crawl(f"{BASE}/", fetch_for(small_site()))
    hubs = analyze(graph)["hubs"]
    # Home holds 3 inbound links; every other page holds at most 1.
    assert hubs[0] == (f"{BASE}/", 3)
    assert all(count <= 1 for _, count in hubs[1:])


def test_analyze_hubs_cap_at_ten():
    hub = page(*[f"{BASE}/p{i}" for i in range(14)], title="Hub")
    pages = {f"{BASE}/": hub}
    pages.update({f"{BASE}/p{i}": page(f"{BASE}/") for i in range(14)})
    hubs = analyze(crawl(f"{BASE}/", fetch_for(pages)))["hubs"]
    assert len(hubs) == 10


def test_analyze_shallow_pages_have_fewer_than_two_inbound():
    graph = crawl(f"{BASE}/", fetch_for(small_site()))
    shallow = analyze(graph)["shallow"]
    assert f"{BASE}/" not in shallow            # 3 inbound
    assert f"{BASE}/post-1" in shallow          # 1 inbound
    assert f"{BASE}/about" in shallow           # 1 inbound


def test_analyze_redirect_chain_records_the_301_target_with_source():
    pages = {
        f"{BASE}/": page(f"{BASE}/old"),
        f"{BASE}/old": (301, ""),
    }
    graph = crawl(f"{BASE}/", fetch_for(pages))
    out = analyze(graph)
    assert out["redirect_chains"] == [(f"{BASE}/", f"{BASE}/old", 301)]
    assert out["broken"] == []


def test_analyze_skips_targets_the_cap_left_uncrawled():
    pages = {f"{BASE}/p{i}": page(f"{BASE}/p{i + 1}") for i in range(6)}
    graph = crawl(f"{BASE}/p0", fetch_for(pages), max_pages=3)
    out = analyze(graph)
    # /p3 was linked but never fetched: unknown, so neither broken nor a
    # redirect entry - never guessed at.
    assert out["broken"] == []
    assert out["redirect_chains"] == []
