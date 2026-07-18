import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from core import telegram as T  # noqa: E402


class FakeHTTP:
    def __init__(self):
        self.sent = []
        self.updates = {"result": [
            {"update_id": 7, "message": {"chat": {"id": 42},
                                          "text": "approve p-20260718-fix1"}},
            {"update_id": 8, "message": {"chat": {"id": 42},
                                          "text": "reject b-20260718-guide too thin"}},
        ]}
    def post(self, url, payload):
        self.sent.append((url, payload))
        return {"ok": True, "result": {"message_id": 1}}
    def get(self, url, params):
        return self.updates


def test_send_proposal_formats_message():
    http = FakeHTTP()
    T.send_item(http, token="t", chat_id=42,
                item={"meta": {"id": "p-1", "kind": "onpage-fix", "title": "Fix titles",
                                "target": "https://e.com/x"}, "body": "details"})
    url, payload = http.sent[0]
    assert "sendMessage" in url and "Fix titles" in payload["text"]
    assert "approve p-1" in payload["text"]  # instructions included


def test_poll_decisions_parses_both():
    http = FakeHTTP()
    decisions, last = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-fix1", "approved", ""),
                        ("b-20260718-guide", "rejected", "too thin")]
    assert last == 8


def test_poll_decisions_chat_id_type_insensitive():
    # API sends int chat ids; site-profile.yaml stores strings. Both must match.
    http = FakeHTTP()
    decisions, last = T.poll_decisions(http, token="t", chat_id="42", offset=0)
    assert decisions == [("p-20260718-fix1", "approved", ""),
                        ("b-20260718-guide", "rejected", "too thin")]
    assert last == 8
