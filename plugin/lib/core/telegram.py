"""Telegram adapter. Transport is injected so tests never touch the network.

Real transport (used by skills):
    from core.telegram import UrllibHTTP
    http = UrllibHTTP()
Approval grammar in chat: 'approve <item-id>' or 'reject <item-id> [reason]'.
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"
_DECISION = re.compile(r"^(approve|reject)\s+([bp]-[\w-]+)\s*(.*)$", re.I)


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
            f"Reply: approve {m['id']}  |  reject {m['id']} <reason>")
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
        if m:
            verb, item_id, reason = m.groups()
            decisions.append((item_id,
                              "approved" if verb.lower() == "approve" else "rejected",
                              reason.strip()))
    return decisions, last
