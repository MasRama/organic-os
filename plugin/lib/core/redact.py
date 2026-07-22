"""Advisory redaction scan for outbound content. Stdlib only.

THIS IS ADVISORY. It reports; it does not block and it does not prevent a
leak. Nothing here removes a value, refuses a send, or raises at a caller.
Every sink that uses it sends anyway and simply shows the human what the
scan noticed.

Read a finding for what it is: a high-tier hit on outbound content means a
credential-shaped string has already left the brain, so the honest response
is to rotate that credential, not to assume the guard caught it in time.
Pattern matching also misses whatever it was not taught - an unusual key
format, a paraphrased secret, a value split across lines - so a clean scan
is the absence of a match, never a guarantee.

Excerpts are masked before they leave this module: at most the first 4 and
last 2 characters of a match survive, so a finding can be shown in a report
or a chat message without re-publishing the value it found.
"""
from __future__ import annotations

import re

# Highest concern first; summarize() reports in this order.
TIERS = ("high", "medium", "low")

_HEAD, _TAIL = 4, 2


def _mask(match: str) -> str:
    """A finding the human can act on without the raw value being shown."""
    if len(match) <= _HEAD + _TAIL:
        return "*" * len(match)
    middle = max(3, len(match) - _HEAD - _TAIL)
    return match[:_HEAD] + "*" * middle + match[-_TAIL:]


def _has_digit(match: str) -> bool:
    """Real WordPress application passwords mix letters and digits; six
    four-letter words in a row are prose, not a credential."""
    return any(c.isdigit() for c in match)


def _phone_like(match: str) -> bool:
    """A phone-shaped run, not any long stretch of numbers. 10-15 digits,
    and either bare or carrying phone punctuation - a table row of
    space-separated metrics is neither."""
    digits = sum(c.isdigit() for c in match)
    if not 10 <= digits <= 15:
        return False
    return (match.startswith("+") or any(c in "()-" for c in match)
            or digits == len(match))


# (tier, name, pattern, extra validator or None). Names are stable: skills
# and docs quote them.
_PATTERNS = (
    ("high", "telegram-bot-token",
     re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}"), None),
    ("high", "wordpress-app-password",
     re.compile(r"\b[A-Za-z0-9]{4}(?: [A-Za-z0-9]{4}){5}\b"), _has_digit),
    ("high", "authorization-bearer",
     re.compile(r"Authorization:\s*Bearer\s+\S+", re.I), None),
    ("high", "api-key-assignment",
     re.compile(r"\b(?:api[_-]?key|token|secret)\s*[=:]\s*\S{20,}", re.I), None),
    ("medium", "personal-email",
     re.compile(r"\b[A-Za-z0-9._%+-]+@(?:gmail|yahoo|hotmail|outlook|"
                r"proton(?:mail)?)\.[A-Za-z]{2,}\b", re.I), None),
    ("medium", "phone-number",
     # A single space is the only whitespace a phone number uses. \s here
     # would let a value on one line join the next line's digits.
     re.compile(r"(?<!\w)\+?\(?\d[\d ().-]{7,}\d(?!\w)"), _phone_like),
    ("low", "local-path",
     re.compile(r"(?:/Users/|/home/)[A-Za-z0-9._-]+(?:/[^\s\"'<>]*)?"
                r"|\b[A-Za-z]:\\\\?[A-Za-z0-9._-]+(?:\\[^\s\"'<>]*)?"), None),
)


def scan(text) -> list[dict]:
    """Findings in `text` as [{tier, pattern, excerpt}], highest tier first.

    `excerpt` is masked, never the raw match. Identical hits from the same
    pattern are reported once: a repeated value is one problem, not ten.
    """
    if not text:
        return []
    text = str(text)
    findings: list[dict] = []
    seen: set = set()
    for tier, name, pattern, valid in _PATTERNS:
        for m in pattern.finditer(text):
            raw = m.group(0)
            if valid is not None and not valid(raw):
                continue
            if (name, raw) in seen:
                continue
            seen.add((name, raw))
            findings.append({"tier": tier, "pattern": name,
                             "excerpt": _mask(raw)})
    return findings


def summarize(findings) -> str:
    """One line naming the counts per tier, or "" when there is nothing to
    say. Carries no excerpt: the counts travel, the values do not."""
    if not findings:
        return ""
    counts: dict = {}
    for f in findings:
        counts[f.get("tier")] = counts.get(f.get("tier"), 0) + 1
    parts = [f"{counts[t]} {t}" for t in TIERS if counts.get(t)]
    if not parts:
        return ""
    return "redaction: " + ", ".join(parts) + " finding(s) - see the run report"
