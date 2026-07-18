#!/bin/zsh
# organic-os local-runtime wrapper: runs one routine headlessly (launchd, or
# by hand) and commits+pushes whatever the routine changed in the brain repo.
#
# PLACEHOLDER - this file is a template, not runnable as-is. Before use,
# substitute both of the following (search for "PLACEHOLDER" below):
#   SITE_SLUG   -> the site slug from `site-profile.yaml` / `organic-os sites`
#                  (e.g. "example-com"). Selects the env file this script
#                  sources for credentials and the OAuth token.
#   BRAIN_PATH  -> the absolute path to this site's brain repo, e.g.
#                  "$HOME/organic-hq/example-com". Must NOT live under
#                  ~/Documents, ~/Desktop, or ~/Downloads - macOS TCC blocks
#                  launchd/cron from writing git's lock files there and the
#                  failure is silent except for "Operation not permitted" in
#                  this script's log.
#
# Requires: `claude setup-token` has been run once, and the resulting
# CLAUDE_CODE_OAUTH_TOKEN is set in the env file this script sources.
# Keychain-based `claude login` auth does not work in a headless shell -
# `claude -p` fails with "Invalid API key - Please run /login" without it.
#
# Usage: run-routine.sh <daily|weekly|monthly>
# Invoked by launchd (see plugin/runtime/launchd/*.plist) or run manually
# for a one-off test: zsh run-routine.sh daily

set -uo pipefail

ROUTINE="${1:-}"

# Routine name -> skill name. daily and weekly share their routine's name;
# monthly's skill is hoo-monthly-audit, not hoo-monthly.
typeset -A SKILL_FOR_ROUTINE=(
  daily   hoo-daily
  weekly  hoo-weekly
  monthly hoo-monthly-audit
)

if [[ -z "${SKILL_FOR_ROUTINE[$ROUTINE]:-}" ]]; then
  echo "usage: run-routine.sh <daily|weekly|monthly>" >&2
  exit 1
fi
SKILL="${SKILL_FOR_ROUTINE[$ROUTINE]}"

# PLACEHOLDER - substitute SITE_SLUG before use.
source "$HOME/.config/organic-os/SITE_SLUG.env"

# PLACEHOLDER - substitute BRAIN_PATH before use.
cd "BRAIN_PATH" || exit 1

LOG_FILE="$HOME/.config/organic-os/routine-$ROUTINE.log"
LEDGER_FILE="$HOME/.config/organic-os/cost-ledger-$(date +%Y%m).tsv"

{
  echo "=== $(date '+%F %T') starting $ROUTINE ($SKILL) ==="

  START_EPOCH=$(date +%s)
  CLAUDE_JSON="$(mktemp)"

  # Pass the command's template body directly - `claude -p
  # "/organic-os:$ROUTINE"` does not reliably expand plugin slash commands
  # in a headless run, so invoke the skill by name instead. JSON output
  # keeps the run's usage fields next to the assistant text; both are
  # recovered below with python3 only - no jq dependency.
  claude -p "Invoke the organic-os:$SKILL skill and follow it end to end. When finished, stage, commit, and push all changes to git." --permission-mode bypassPermissions --output-format json > "$CLAUDE_JSON" 2>&1

  END_EPOCH=$(date +%s)
  DURATION=$(( END_EPOCH - START_EPOCH ))

  # Emit the assistant text into this log. The output shape varies by CLI
  # version, so fall back to the raw output when it is not the expected JSON.
  python3 - "$CLAUDE_JSON" <<'PYEOF'
import json, sys
raw = open(sys.argv[1]).read()
try:
    data = json.loads(raw)
except ValueError:
    data = None
text = data.get("result") if isinstance(data, dict) else None
print(text if isinstance(text, str) and text.strip() else raw)
PYEOF

  # Usage extraction is defensive: field names differ across CLI versions,
  # so sum every *_tokens / *Tokens integer found (top level, or nested one
  # level for per-model breakdowns) and fall back to an honest
  # "unavailable" line rather than guessing.
  USAGE=$(python3 - "$CLAUDE_JSON" <<'PYEOF'
import json, sys
FALLBACK = "usage unavailable in this CLI version"

def tokens(d):
    total, found = 0, False
    for k, v in d.items():
        if isinstance(v, int) and (k.endswith("_tokens") or k.endswith("Tokens")):
            total, found = total + v, True
    return total, found

try:
    data = json.loads(open(sys.argv[1]).read())
except Exception:
    data = None
if not isinstance(data, dict):
    print(FALLBACK)
    raise SystemExit
total, found = 0, False
for candidate in (data.get("usage"), data.get("modelUsage")):
    if not isinstance(candidate, dict):
        continue
    t, f = tokens(candidate)
    total, found = total + t, found or f
    for v in candidate.values():  # per-model breakdowns nest one level down
        if isinstance(v, dict):
            t, f = tokens(v)
            total, found = total + t, found or f
parts = [f"tokens={total}"] if found else []
cost = data.get("total_cost_usd")
if isinstance(cost, (int, float)):
    parts.append(f"cost_usd={cost:.4f}")
print(" ".join(parts) if parts else FALLBACK)
PYEOF
)
  rm -f "$CLAUDE_JSON"

  # One cost line in this log, and one row in the monthly ledger.
  # Ledger columns: date, routine, duration seconds, tokens-or-unavailable.
  echo "cost: $ROUTINE ${DURATION}s $USAGE"
  printf '%s\t%s\t%s\t%s\n' "$(date +%F)" "$ROUTINE" "$DURATION" "$USAGE" >> "$LEDGER_FILE"

  # Belt-and-braces: the skill is asked to commit and push itself, but this
  # runs unattended, so make it non-optional here too. Nothing-to-commit or
  # an unreachable remote must not fail the run.
  git add -A
  git commit -m "chore(routine): $ROUTINE $(date +%F)" || true
  git push || true

  echo "=== $(date '+%F %T') finished $ROUTINE ==="
} >> "$LOG_FILE" 2>&1
