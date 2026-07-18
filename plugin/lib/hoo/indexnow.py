"""IndexNow submission: key generation, key-file content, and the POST to
api.indexnow.org (Bing, Yandex, and every other IndexNow-participating
engine share the one endpoint). Stdlib only; the transport is injectable
for tests. submit() never raises on a non-200 - the caller records the
returned status in the outcome instead. Spec: https://www.indexnow.org/
"""
from __future__ import annotations
import json as _json
import secrets
import urllib.error
import urllib.request

ENDPOINT = "https://api.indexnow.org/indexnow"


def gen_key() -> str:
    """A 32-char lowercase hex key (IndexNow allows 8-128 hex chars)."""
    return secrets.token_hex(16)


def key_file_content(key: str) -> str:
    """The file served at https://<host>/<key>.txt is the key and nothing
    else - that is the whole IndexNow ownership proof."""
    return key


def _stdlib_transport(url: str, payload: dict) -> int:
    data = _json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def submit(host: str, key: str, urls, transport=None) -> dict:
    """POST the changed URLs for one host. Returns
    {"status": <HTTP status>, "submitted": <url count>} - a non-200 comes
    back as the status, never as an exception, so an unattended routine can
    record the result and move on."""
    url_list = list(urls)
    payload = {"host": host, "key": key,
               "keyLocation": f"https://{host}/{key}.txt",
               "urlList": url_list}
    send = transport or _stdlib_transport
    status = send(ENDPOINT, payload)
    return {"status": int(status), "submitted": len(url_list)}
