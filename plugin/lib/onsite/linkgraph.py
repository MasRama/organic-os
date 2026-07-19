"""Internal-link graph: crawl your own site, map the links, find the gaps.

Observe-side only - nothing here mutates anything. The crawl targets the
profile's OWN site exclusively: ADR-0006's no-scraping decision bans
third-party scraping, and your own property is yours to crawl. crawl()
enforces that in code - it never follows a link off the host it started
on, and off-host seed URLs are dropped.

The fetcher is injectable, wp.py's session pattern: tests pass a fake
callable, real use passes stdlib_fetch (stdlib urllib, no requests dep).
The fetch contract is `fetch(url) -> (status, html_text)`, where a
network error is `(0, "")` and redirects are NEVER followed - a 3xx is
graph data, not a hop to take.

crawl() returns `{url: {"out": [...], "out_raw": [...], "status": int,
"title": str}}`. Graph keys and "out" entries have fragments and query
strings stripped so /docs?tab=a#b and /docs are one node; "out_raw"
keeps the as-written resolved links for reporting. analyze() reads only
that structure, so any graph source with the same shape works.
"""
from __future__ import annotations
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from html.parser import HTMLParser


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def stdlib_fetch(url: str, timeout: int = 30) -> tuple[int, str]:
    """Default fetcher: (status, body); (0, "") on a network error."""
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(url, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError):
        return 0, ""


class _LinkParser(HTMLParser):
    """href values from <a> tags plus the <title> text; html.parser is
    tolerant of broken markup, which real pages require."""

    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def _key(url: str) -> str:
    """Graph key: the URL with fragment and query stripped."""
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, parts.path, "", ""))


def crawl(base_url: str, fetch, max_pages: int = 100,
          seed_urls=None) -> dict:
    """BFS from base_url, same host only, at most max_pages fetches.

    seed_urls (optional, e.g. the profile's sitemap URLs) join the
    initial frontier so a page nothing links to still enters the graph -
    that is what makes orphan detection possible. Off-host seeds are
    dropped, same rule as discovered links.
    """
    host = urllib.parse.urlsplit(base_url).netloc.lower()
    graph: dict = {}
    queue: deque = deque()
    seen: set = set()
    for url in [base_url, *(seed_urls or [])]:
        key = _key(url)
        if urllib.parse.urlsplit(key).netloc.lower() != host:
            continue
        if key not in seen:
            seen.add(key)
            queue.append(key)
    while queue and len(graph) < max_pages:
        url = queue.popleft()
        status, body = fetch(url)
        parser = _LinkParser()
        parser.feed(body or "")
        out: list = []
        out_raw: list = []
        for href in parser.hrefs:
            absolute = urllib.parse.urljoin(url, href)
            parts = urllib.parse.urlsplit(absolute)
            if parts.scheme not in ("http", "https"):
                continue
            if parts.netloc.lower() != host:
                continue  # never followed, never listed: own site only
            key = _key(absolute)
            out_raw.append(absolute)
            if key != url and key not in out:
                out.append(key)
        graph[url] = {"out": out, "out_raw": out_raw, "status": status,
                      "title": parser.title.strip()}
        for key in out:
            if key not in seen:
                seen.add(key)
                queue.append(key)
    return graph


def analyze(graph: dict) -> dict:
    """Findings from a crawl() graph:

    - broken: [(from_url, to_url, status)] for linked targets answering
      4xx/5xx or unreachable (status 0)
    - orphans: crawled pages no other page links to, sorted
    - hubs: [(url, inbound_count)], top 10 by inbound
    - shallow: pages with fewer than 2 inbound links, sorted
    - redirect_chains: [(from_url, to_url, status)] for 3xx targets -
      each is a link resolving through a redirect hop

    A target the page cap left uncrawled has no status: it appears in no
    finding rather than being guessed at.
    """
    inbound = {url: 0 for url in graph}
    broken: list = []
    redirect_chains: list = []
    for src, page in graph.items():
        for target in page["out"]:
            if target in inbound:
                inbound[target] += 1
            entry = graph.get(target)
            if entry is None:
                continue
            status = entry["status"]
            if status >= 400 or status == 0:
                broken.append((src, target, status))
            elif 300 <= status < 400:
                redirect_chains.append((src, target, status))
    ranked = sorted(graph, key=lambda u: (-inbound[u], u))
    return {
        "broken": broken,
        "orphans": sorted(u for u, n in inbound.items() if n == 0),
        "hubs": [(u, inbound[u]) for u in ranked[:10]],
        "shallow": sorted(u for u, n in inbound.items() if n < 2),
        "redirect_chains": redirect_chains,
    }
