"""Semantic-version comparison for the diagnose update-currency check.

Stdlib only, and no I/O of any kind. The diagnose skill reads the running
version from the plugin manifest and fetches the latest published tag from
GitHub's public releases endpoint, then calls currency() to decide, with no
guesswork, whether the running install is behind. Keeping the comparison
here - rather than asking a model to eyeball two version strings - is what
makes 0.5.10 correctly newer than 0.5.9, and keeps a leading "v" or a
pre-release suffix from derailing the ordering.

No network read lives in this module by design. The outbound fetch stays in
the skill, where it is visible and where its honesty framing (a read of a
public number, never telemetry) belongs. This module only compares strings.
"""
from __future__ import annotations

import re

_LEADING_NUM = re.compile(r"^\d+")


def _parse(v):
    """(release_tuple, prerelease_or_None), or None when unparseable.

    Tolerates a leading 'v'/'V' and surrounding space. The release tuple is
    the dotted integer run at the front; anything after the first '-' is the
    pre-release string. A component with no leading digit (garbage) makes the
    whole value unparseable, reported as None rather than guessed.
    """
    if v is None:
        return None
    s = str(v).strip()
    if s[:1] in ("v", "V"):
        s = s[1:]
    if not s:
        return None
    core, _, pre = s.partition("-")
    nums = []
    for part in core.split("."):
        m = _LEADING_NUM.match(part.strip())
        if m is None:
            return None
        nums.append(int(m.group()))
    if not nums:
        return None
    return (tuple(nums), pre or None)


def compare(a, b):
    """-1 if a < b, 0 if equal, 1 if a > b; None if either is unparseable.

    Release numbers compare as integer tuples, the shorter zero-padded so
    0.5 and 0.5.0 are equal. At equal release numbers a pre-release sorts
    BELOW its release (0.5.1-rc.1 < 0.5.1), per semver; two pre-releases fall
    back to a plain string compare, a best-effort tiebreak rather than full
    identifier precedence, which the update check does not need.
    """
    pa, pb = _parse(a), _parse(b)
    if pa is None or pb is None:
        return None
    (na, prea), (nb, preb) = pa, pb
    width = max(len(na), len(nb))
    na = na + (0,) * (width - len(na))
    nb = nb + (0,) * (width - len(nb))
    if na != nb:
        return -1 if na < nb else 1
    if prea == preb:
        return 0
    if prea is None:
        return 1
    if preb is None:
        return -1
    return -1 if prea < preb else 1


def currency(running, latest):
    """Where `running` stands against `latest`, as one stable word.

    'current' (same), 'behind' (running older, an update is available),
    'ahead' (running newer than the latest published release, normal on a
    development checkout), or 'unknown' when either value is missing or
    unparseable. The skill maps 'unknown' to "could not check latest" - it
    never reads as up to date.
    """
    c = compare(running, latest)
    if c is None:
        return "unknown"
    return {-1: "behind", 0: "current", 1: "ahead"}[c]
