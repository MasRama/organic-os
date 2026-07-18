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


# -- reply-context decisions --------------------------------------------------

PROPOSAL_TEXT = ("organic-os proposal p-20260718-fix1\n"
                 "[onpage-fix] Fix titles\ntarget: https://example.com/x")


class ReplyHTTP:
    """FakeHTTP variant with caller-supplied updates."""
    def __init__(self, updates):
        self.updates = {"result": updates}

    def get(self, url, params):
        return self.updates


def _upd(uid, text, reply_to_text=None):
    msg = {"chat": {"id": 42}, "text": text}
    if reply_to_text is not None:
        msg["reply_to_message"] = {"text": reply_to_text}
    return {"update_id": uid, "message": msg}


def test_reply_approved_resolves_id_from_replied_to_text():
    http = ReplyHTTP([_upd(9, "Approved", reply_to_text=PROPOSAL_TEXT)])
    decisions, last = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-fix1", "approved", "")]
    assert last == 9


def test_reply_thumbs_up_with_note_approves_and_keeps_note():
    http = ReplyHTTP([_upd(10, "\U0001F44D looks good", reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-fix1", "approved", "looks good")]


def test_reply_reject_word_with_note():
    http = ReplyHTTP([_upd(11, "no too thin", reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-fix1", "rejected", "too thin")]


def test_non_reply_bare_approved_resolves_nothing():
    # No reply context means no item id to resolve against.
    http = ReplyHTTP([_upd(12, "Approved")])
    decisions, last = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == []
    assert last == 12  # still acknowledged, never re-polled


def test_strict_form_in_reply_still_works_and_takes_precedence():
    # The typed id wins over the replied-to message's id.
    http = ReplyHTTP([_upd(13, "approve p-20260718-other",
                           reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-other", "approved", "")]


def test_reply_to_message_without_item_id_resolves_nothing():
    http = ReplyHTTP([_upd(14, "Approved", reply_to_text="hello there")])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == []


def test_reply_with_non_decision_text_resolves_nothing():
    http = ReplyHTTP([_upd(15, "interesting, let me think",
                           reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == []


def test_reply_go_ahead_approves():
    http = ReplyHTTP([_upd(16, "Go ahead", reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-fix1", "approved", "")]


def test_reply_go_ahead_with_trailing_text_approves_with_note():
    http = ReplyHTTP([_upd(17, "go ahead and fix the title too",
                           reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-fix1", "approved", "and fix the title too")]


def test_reply_ship_it_approves():
    http = ReplyHTTP([_upd(18, "ship it", reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-fix1", "approved", "")]


def test_reply_lgtm_approves():
    http = ReplyHTTP([_upd(19, "LGTM", reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-fix1", "approved", "")]


def test_reply_wait_for_now_resolves_nothing():
    # Deferring is not rejecting: "wait" must stay a non-decision so the
    # item stays pending for a real answer later.
    http = ReplyHTTP([_upd(20, "Wait for now", reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == []


def test_reply_hold_resolves_nothing():
    http = ReplyHTTP([_upd(21, "hold", reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == []


def test_reply_bare_no_rejects():
    http = ReplyHTTP([_upd(22, "no", reply_to_text=PROPOSAL_TEXT)])
    decisions, _ = T.poll_decisions(http, token="t", chat_id=42, offset=0)
    assert decisions == [("p-20260718-fix1", "rejected", "")]


def test_send_item_states_reply_format():
    http = FakeHTTP()
    T.send_item(http, token="t", chat_id=42,
                item={"meta": {"id": "p-2", "kind": "onpage-fix", "title": "T",
                                "target": ""}, "body": "b"})
    _, payload = http.sent[0]
    assert "Reply to this message" in payload["text"]
    assert "approve p-2" in payload["text"]  # strict form still shown
