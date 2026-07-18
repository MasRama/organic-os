"""Telegram adapter. Transport is injected so tests never touch the network.

Real transport (used by skills):
    from core.telegram import UrllibHTTP
    http = UrllibHTTP()
Approval grammar in chat: 'approve <item-id>' or 'reject <item-id> [reason]'.
Reply-context grammar: replying to a message that contains an item id, a bare
decision word resolves against that id - approve/approved/yes/ok/thumbs-up
approve it, reject/rejected/no/thumbs-down reject it; trailing text after the
word is kept as the note. The strict grammar takes precedence when both could
apply.
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"
_DECISION = re.compile(r"^(approve|reject)\s+([bp]-[\w-]+)\s*(.*)$", re.I)
# Item ids as create_item mints them: [bp]-YYYYMMDD-slug (lowercase slug).
_ITEM_ID = re.compile(r"\b[bp]-\d{8}-[a-z0-9][a-z0-9-]*")
_REPLY_VERBS = {"approved": "approved", "approve": "approved", "yes": "approved",
                "ok": "approved", "\U0001F44D": "approved",
                "rejected": "rejected", "reject": "rejected", "no": "rejected",
                "\U0001F44E": "rejected"}
# Longest alternatives first so 'approved' is not split as 'approve' + 'd'.
_REPLY_DECISION = re.compile(
    "^(" + "|".join(sorted(_REPLY_VERBS, key=len, reverse=True))
    + r")(?:[\s,.:;-]+(.*))?$", re.I | re.S)


def _reply_decision(msg: dict):
    """Resolve a reply-context decision: (item_id, decision, note) or None.

    Only fires when the update is a reply, the replied-to text carries an
    item id, and the reply's own text is (or starts with) a decision word.
    """
    reply = msg.get("reply_to_message") or {}
    ids = _ITEM_ID.findall(reply.get("text") or "")
    if not ids:
        return None
    m = _REPLY_DECISION.match(msg.get("text", "").strip())
    if not m:
        return None
    verb, note = m.group(1).lower(), (m.group(2) or "").strip()
    return ids[0], _REPLY_VERBS[verb], note


class UrllibHTTP:
    # Errors are re-raised with status/reason only: the URL embeds the bot
    # token and must never surface in a printed exception.
    def post(self, url, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"telegram api error: HTTP {e.code} {e.reason}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"telegram api error: {e.reason}") from None

    def get(self, url, params):
        try:
            with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params),
                                        timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"telegram api error: HTTP {e.code} {e.reason}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"telegram api error: {e.reason}") from None


def send_item(http, token: str, chat_id, item: dict) -> None:
    m = item["meta"]
    text = (f"organic-os proposal {m['id']}\n"
            f"[{m['kind']}] {m['title']}\n"
            f"target: {m.get('target') or '-'}\n\n"
            f"{item['body'][:800]}\n\n"
            f"Reply to this message with approve or reject "
            f"(a bare 'approved' works as a reply).\n"
            f"Or send: approve {m['id']}  |  reject {m['id']} <reason>")
    http.post(API.format(token=token, method="sendMessage"),
              {"chat_id": chat_id, "text": text})


def poll_decisions(http, token: str, chat_id, offset: int = 0):
    data = http.get(API.format(token=token, method="getUpdates"),
                    {"offset": offset + 1, "timeout": 0})
    decisions, last = [], offset
    for u in data.get("result", []):
        last = max(last, u["update_id"])
        msg = u.get("message") or {}
        if str(msg.get("chat", {}).get("id")) != str(chat_id):
            continue
        m = _DECISION.match(msg.get("text", "").strip())
        if m:  # strict grammar wins whenever it matches, reply or not
            verb, item_id, reason = m.groups()
            decisions.append((item_id,
                              "approved" if verb.lower() == "approve" else "rejected",
                              reason.strip()))
            continue
        resolved = _reply_decision(msg)
        if resolved:
            decisions.append(resolved)
    return decisions, last
