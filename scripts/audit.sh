#!/usr/bin/env bash
# organic-os repo audit: personal-data leakage, secrets, style, module boundaries.
# Usage: ./scripts/audit.sh   (exit 0 = clean, exit 1 = violations)
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
say() { printf '%s\n' "$*"; }

# 1. Personal/employer data must never appear (spec §15). Case-insensitive.
PERSONAL='exotel|ameyo|wsofi|78382|32X|29X MROI|4\.2M|5-FTE|MQL to SQL|CAC reduction'
hits=$(grep -rniE "$PERSONAL" --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=docs --exclude=audit.sh . || true)
[ -n "$hits" ] && { say "FAIL personal/employer data:"; say "$hits"; fail=1; }

# 2. Secrets patterns.
SECRETS='AKIA[0-9A-Z]{16}|-----BEGIN|ghp_[A-Za-z0-9]{20,}|xox[baprs]-|sk-ant-|AIza[0-9A-Za-z_-]{30,}'
hits=$(grep -rnE "$SECRETS" --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv --exclude=audit.sh . || true)
[ -n "$hits" ] && { say "FAIL secret-like string:"; say "$hits"; fail=1; }

# 3. Em-dash ban (all shipped text).
hits=$(grep -rn "$(printf '\xe2\x80\x94')" --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv --exclude=audit.sh . || true)
[ -n "$hits" ] && { say "FAIL em-dash found:"; say "$hits"; fail=1; }

# 4. Banned phrases in shipped copy (plugin/, docs/, README, playground).
BANNED='seamless|robustly?|delve|dive into|in today.s fast-paced|transformative|unlock|unleash|supercharge|game-chang|cutting-edge|world-class|best-in-class|synergy|holistic|revolutionary'
hits=$(grep -rniE "$BANNED" plugin docs README.md SECURITY.md playground 2>/dev/null | grep -v 'audit.sh' || true)
[ -n "$hits" ] && { say "FAIL banned phrase:"; say "$hits"; fail=1; }

# 5. Module boundary: no cross-module imports.
hits=$(grep -rnE 'from (lib\.)?(hoo|onsite)|import (lib\.)?(hoo|onsite)' plugin/lib/core 2>/dev/null || true)
[ -n "$hits" ] && { say "FAIL core imports a module:"; say "$hits"; fail=1; }
hits=$(grep -rnE 'from (lib\.)?onsite|import (lib\.)?onsite' plugin/lib/hoo 2>/dev/null || true)
[ -n "$hits" ] && { say "FAIL hoo imports onsite:"; say "$hits"; fail=1; }
hits=$(grep -rnE 'from (lib\.)?hoo|import (lib\.)?hoo' plugin/lib/onsite 2>/dev/null || true)
[ -n "$hits" ] && { say "FAIL onsite imports hoo:"; say "$hits"; fail=1; }

# 6. Manifests parse.
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null || { say "FAIL marketplace.json"; fail=1; }
python3 -m json.tool plugin/.claude-plugin/plugin.json >/dev/null || { say "FAIL plugin.json"; fail=1; }

[ "$fail" -eq 0 ] && say "audit: clean"
exit "$fail"
