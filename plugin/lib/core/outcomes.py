"""Reading an outcome claim, and checking it against recomputed data.

An outcome record in `outcomes/` says what changed and what moved. This
module does two small things with that record:

- `parse_outcome` reads one, tolerantly. Records are written by skills as
  prose plus keys (the same view `core.export` takes), so anything that is
  not a key line is skipped rather than treated as an error, and a key the
  record never states comes back as None. Absent is recorded as absent,
  never guessed.
- `compare` puts a claim next to numbers recomputed from raw connector
  data and reports where the two disagree.

Why it exists: a claim nobody can recheck is a story. The verify-outcome
skill (`plugin/skills/hoo-verify-outcome`) pulls the raw windows and
recomputes the delta BEFORE it reads the claimed numbers, then calls
`compare`. Reading the claim first is what makes the recomputation worth
nothing, so the ordering is the point, not a detail.

`compare` has no opinion about what a divergence means. It reports one; the
skill records it as a signal. Nothing here suppresses, rounds toward, or
explains away a difference.

Read-only: this module never writes a brain file.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

import yaml

from . import contracts as C

# What a caller gets back from parse_outcome, always all seven keys.
FIELDS = ("item", "url", "applied_at", "claimed_before", "claimed_after",
          "claimed_delta", "windows")

# Field -> the key names records actually use for it. Skills write these
# records by hand, so the spellings vary; the field names above do not.
ALIASES = {
    "item": ("item", "item_id", "id", "slug"),
    "url": ("url", "target", "target_url", "page", "permalink"),
    "applied_at": ("applied_at", "applied", "date", "when", "published_at"),
    "claimed_before": ("claimed_before", "before", "baseline"),
    "claimed_after": ("claimed_after", "after"),
    "claimed_delta": ("claimed_delta", "delta", "change"),
    "windows": ("windows", "window", "measurement_windows"),
}

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
# An optional list dash, a key, a colon, and whatever follows. A prose line
# carrying a colon can match; that is fine, because only the keys named in
# ALIASES are ever read back out.
_KEYLINE = re.compile(r"^(\s*)(?:-\s+)?([A-Za-z][A-Za-z0-9 _-]*?)\s*:\s*(.*?)\s*$")
_NUM = re.compile(r"\A[+-]?\d+(?:\.\d+)?\Z")


def _plain(value):
    """YAML types the record never meant to carry, flattened back: a date or
    timestamp becomes the string it was written as, so a value parsed from
    frontmatter and the same value read from the body compare equal."""
    if isinstance(value, _dt.datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, _dt.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def _scalar(raw: str):
    """A key line's value: a number when it reads as one, otherwise the text
    as written. Quotes and a trailing comma are stripped; nothing else is
    interpreted."""
    text = raw.strip().rstrip(",").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if _NUM.match(text):
        return float(text) if "." in text else int(text)
    return text


def _normalise(key: str) -> str:
    return key.strip().lower().replace(" ", "_").replace("-", "_")


def _collect(text: str) -> dict:
    """A tolerant key map over a record: YAML frontmatter when it parses,
    then an indentation-aware scan of the body.

    A key stated twice takes its last value - outcome records are appended
    to (the apply writes one, the measurement adds to it), so the newest
    statement is the current one. Frontmatter that does not parse is
    skipped, not raised on: the body still has numbers worth reading.
    """
    data: dict = {}
    body = text
    m = _FRONTMATTER.match(text)
    if m:
        try:
            front = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            front = None
        if isinstance(front, dict):
            data.update({_normalise(str(k)): _plain(v)
                         for k, v in front.items()})
        body = text[m.end():]

    stack: list = [(-1, data)]
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        hit = _KEYLINE.match(line)
        if hit is None:
            continue  # prose, and prose is most of a record
        indent = len(hit.group(1).expandtabs(2))
        key = _normalise(hit.group(2))
        raw = hit.group(3)
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if raw in ("", "|", ">"):
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            parent[key] = _scalar(raw)
    return data


def _pick(data: dict, names):
    for name in names:
        if name in data and data[name] not in ("", None):
            return data[name]
    return None


def parse_outcome(path) -> dict:
    """One record from `outcomes/` as a dict carrying every key in FIELDS.

    A key the record does not state comes back None - the caller sees an
    absence, not a guess. `item` falls back to the filename stem, because
    the contract names these files `outcomes/<item-id>.md`, so the filename
    IS the item identity even when the body never repeats it. `path` rides
    along for the run report.
    """
    path = Path(path)
    data = _collect(path.read_text())
    record = {"path": str(path)}
    for field in FIELDS:
        record[field] = _pick(data, ALIASES[field])
    if record["item"] is None:
        record["item"] = path.stem
    return record


def _numeric(value):
    """The value as a float, or None when it is not a number. A bool is not
    a number here: True would otherwise compare as 1 and read as agreement."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and _NUM.match(value.strip()):
        return float(value.strip())
    return None


def compare(claimed: dict, recomputed: dict, tolerance: float = 0.05) -> dict:
    """A claimed set of metrics against an independently recomputed set.

    Returns `{agrees, divergences, unverifiable, compared, tolerance}`:

    - `divergences` is `[{metric, claimed, recomputed, pct_diff}]` for every
      shared numeric metric further apart than `tolerance`.
    - `pct_diff` is a fraction on the same scale as `tolerance` (0.05 is
      five percent), relative to the larger of the two values - so a zero on
      one side cannot divide by zero, and a claimed 10 against a recomputed
      0 reads as 1.0, fully off.
    - `unverifiable` is `[{metric, claimed, recomputed, reason}]` for a
      metric only one side has (`claimed only` / `recomputed only`) or a
      value that is not a number (`not numeric`). Neither is a divergence:
      one side missing means the check could not run, not that the claim
      was wrong.
    - `agrees` is True only when at least one metric was actually compared
      and every compared metric held. Nothing compared means nothing was
      verified, so `agrees` is False with an empty `compared` - read that as
      unverified, never as disagreement.

    A negative tolerance refuses rather than quietly failing every metric.
    """
    if tolerance is None or tolerance < 0:
        raise C.ContractError(
            f"tolerance must be zero or a positive fraction, got {tolerance!r} "
            "(0.05 is five percent)")
    claimed = claimed or {}
    recomputed = recomputed or {}

    divergences: list = []
    unverifiable: list = []
    compared: list = []

    for metric in sorted(set(claimed) | set(recomputed)):
        in_claim, in_recomputed = metric in claimed, metric in recomputed
        left = claimed.get(metric)
        right = recomputed.get(metric)
        if not in_recomputed:
            unverifiable.append({"metric": metric, "claimed": left,
                                 "recomputed": None, "reason": "claimed only"})
            continue
        if not in_claim:
            unverifiable.append({"metric": metric, "claimed": None,
                                 "recomputed": right,
                                 "reason": "recomputed only"})
            continue
        a, b = _numeric(left), _numeric(right)
        if a is None or b is None:
            unverifiable.append({"metric": metric, "claimed": left,
                                 "recomputed": right, "reason": "not numeric"})
            continue
        compared.append(metric)
        base = max(abs(a), abs(b))
        pct = 0.0 if base == 0 else abs(a - b) / base
        if pct > tolerance:
            divergences.append({"metric": metric, "claimed": left,
                                "recomputed": right, "pct_diff": round(pct, 6)})

    return {"agrees": bool(compared) and not divergences,
            "divergences": divergences, "unverifiable": unverifiable,
            "compared": compared, "tolerance": tolerance}
