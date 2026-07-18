import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import string  # noqa: E402

from hoo.indexnow import ENDPOINT, gen_key, key_file_content, submit  # noqa: E402


class FakeTransport:
    def __init__(self, status=200):
        self.status = status
        self.calls = []

    def __call__(self, url, payload):
        self.calls.append((url, payload))
        return self.status


def test_gen_key_is_32_char_hex():
    key = gen_key()
    assert len(key) == 32
    assert set(key) <= set(string.hexdigits.lower())
    assert gen_key() != key                     # keys are not constant


def test_key_file_content_is_the_key_itself():
    assert key_file_content("abc123") == "abc123"   # IndexNow spec: key only


def test_submit_payload_shape_and_key_location():
    t = FakeTransport()
    result = submit("play.example", "a" * 32,
                    ["https://play.example/p1", "https://play.example/p2"],
                    transport=t)
    url, payload = t.calls[-1]
    assert url == ENDPOINT == "https://api.indexnow.org/indexnow"
    assert payload["host"] == "play.example"
    assert payload["key"] == "a" * 32
    assert payload["keyLocation"] == f"https://play.example/{'a' * 32}.txt"
    assert payload["urlList"] == ["https://play.example/p1",
                                  "https://play.example/p2"]
    assert result == {"status": 200, "submitted": 2}


def test_submit_non_200_returns_status_without_raising():
    t = FakeTransport(status=429)
    result = submit("play.example", "b" * 32, ["https://play.example/p1"],
                    transport=t)
    assert result == {"status": 429, "submitted": 1}


def test_submit_accepts_any_iterable_of_urls():
    t = FakeTransport()
    result = submit("play.example", "c" * 32,
                    (u for u in ["https://play.example/only"]), transport=t)
    _, payload = t.calls[-1]
    assert payload["urlList"] == ["https://play.example/only"]
    assert result["submitted"] == 1
