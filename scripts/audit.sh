#!/usr/bin/env bash
# organic-os repo audit: personal-data leakage, secrets, style, module boundaries.
# Usage: ./scripts/audit.sh   (exit 0 = clean, exit 1 = violations)
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
fail=0
say() { printf '%s\n' "$*"; }
EXCLUDES='--exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv'

# 1. Personal/employer data must never appear (spec §15). Case-insensitive.
# docs/specs quotes the blocklist verbatim; audit.sh defines it.
PERSONAL='exotel|ameyo|wsofi|78382|32X|29X MROI|4\.2M|5-FTE|MQL to SQL|CAC reduction'
hits=$(grep -rniE "$PERSONAL" $EXCLUDES --exclude-dir=specs --exclude-dir=plans --exclude=audit.sh . || true)
[ -n "$hits" ] && { say "FAIL personal/employer data:"; say "$hits"; fail=1; }

# 2. Secrets patterns.
SECRETS='AKIA[0-9A-Z]{16}|-----BEGIN|ghp_[A-Za-z0-9]{20,}|xox[baprs]-|sk-ant-|AIza[0-9A-Za-z_-]{30,}'
hits=$(grep -rnE "$SECRETS" $EXCLUDES --exclude=audit.sh . || true)
[ -n "$hits" ] && { say "FAIL secret-like string:"; say "$hits"; fail=1; }

# 3. Em-dash ban (all shipped text).
hits=$(grep -rn "$(printf '\xe2\x80\x94')" $EXCLUDES --exclude=audit.sh . || true)
[ -n "$hits" ] && { say "FAIL em-dash found:"; say "$hits"; fail=1; }

# 4. Banned phrases in shipped copy (plugin/, docs/, README).
BANNED='seamless|robust(ly)?|delve|dive into|in today.s fast-paced|transform(ative|ing)?|unlock|unleash|supercharge|game-chang|cutting-edge|world-class|best-in-class|synergy|holistic|revolutionary'
hits=$(grep -rniE "$BANNED" $EXCLUDES --exclude=audit.sh plugin docs README.md SECURITY.md CONTRIBUTING.md ROADMAP.md CHANGELOG.md 2>/dev/null || true)
[ -n "$hits" ] && { say "FAIL banned phrase:"; say "$hits"; fail=1; }

# 5. Module boundary: no cross-module imports (absolute, package, or relative).
IMPORT_PRE='(^|[^.a-zA-Z_])(from|import)[[:space:]]+(\.+)?((plugin\.)?lib\.)?'
IMPORT_POST='(\.|[[:space:]]|$)'
hits=$(grep -rnE "${IMPORT_PRE}(hoo|onsite)${IMPORT_POST}" $EXCLUDES plugin/lib/core 2>/dev/null || true)
[ -n "$hits" ] && { say "FAIL core imports a module:"; say "$hits"; fail=1; }
hits=$(grep -rnE "${IMPORT_PRE}onsite${IMPORT_POST}" $EXCLUDES plugin/lib/hoo 2>/dev/null || true)
[ -n "$hits" ] && { say "FAIL hoo imports onsite:"; say "$hits"; fail=1; }
hits=$(grep -rnE "${IMPORT_PRE}hoo${IMPORT_POST}" $EXCLUDES plugin/lib/onsite 2>/dev/null || true)
[ -n "$hits" ] && { say "FAIL onsite imports hoo:"; say "$hits"; fail=1; }

# 6. Manifests parse.
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null || { say "FAIL marketplace.json"; fail=1; }
python3 -m json.tool plugin/.claude-plugin/plugin.json >/dev/null || { say "FAIL plugin.json"; fail=1; }

# 7. Brain-data boundary: business data belongs in a site's own brain repo,
# never in this one (see CONTRIBUTING.md). Flags actual files/directories
# only - prose mentions in docs are fine.
BRAIN_FILES='site-profile.yaml skillbook.md tracking.yaml telegram-offset.json'
for f in $BRAIN_FILES; do
  hits=$(find . -not -path '*/.git/*' -not -path './plugin/lib/core/templates/*' -type f -name "$f")
  [ -n "$hits" ] && { say "FAIL brain-data file found outside plugin/lib/core/templates/: $f"; say "$hits"; fail=1; }
done
BRAIN_DIRS='organic-hq* signals reflections'
for d in $BRAIN_DIRS; do
  hits=$(find . -not -path '*/.git/*' -not -path './plugin/lib/core/templates/*' -type d -name "$d")
  [ -n "$hits" ] && { say "FAIL brain-data directory found outside plugin/lib/core/templates/: $d"; say "$hits"; fail=1; }
done

# 8. Information integrity: relative markdown links resolve, and the facts
# quoted across files match their canonical sources (docs/INFORMATION-MAP.md).
hits=$(python3 - <<'PYEOF'
import json
import re
import subprocess
import sys
from pathlib import Path

problems = []

# (a) Every relative link in every tracked .md file resolves.
md_files = subprocess.run(["git", "ls-files", "*.md"], capture_output=True,
                          text=True).stdout.split()
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
for name in md_files:
    path = Path(name)
    for target in LINK.findall(path.read_text(encoding="utf-8")):
        if "://" in target or target.startswith(("mailto:", "#")):
            continue
        rel = target.split("#", 1)[0]
        if rel and not (path.parent / rel).exists():
            problems.append(f"broken relative link in {name}: {target}")

# (b) Version sync: plugin.json is canonical.
version = json.load(open("plugin/.claude-plugin/plugin.json"))["version"]
readme = Path("README.md").read_text(encoding="utf-8")
badge = next((l for l in readme.splitlines()
              if "img.shields.io/badge/version-" in l), "")
if f"version-{version}-" not in badge:
    problems.append(f"README version badge out of sync with plugin.json "
                    f"{version}: {badge.strip() or '(badge line missing)'}")
marketplace = json.load(open(".claude-plugin/marketplace.json"))
mp_version = next(p["version"] for p in marketplace["plugins"]
                  if p["name"] == "organic-os")
if mp_version != version:
    problems.append(f"marketplace.json version {mp_version} != "
                    f"plugin.json version {version}")

# (c) Count sync: filesystem and pytest are canonical; the README tests
# badge and inventory line quote them.
skills = len(list(Path("plugin/skills").rglob("SKILL.md")))
commands = len(list(Path("plugin/commands").glob("*.md")))
agents = len(list(Path("plugin/agents").glob("*.md")))
collect = subprocess.run(
    [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
    capture_output=True, text=True)
m = re.search(r"(\d+) tests? collected", collect.stdout)
if m is None:
    problems.append("could not count tests: pytest --collect-only gave no "
                    "'N tests collected' line")
    tests = None
else:
    tests = int(m.group(1))
inv = re.search(r"(\d+)\s+skills,\s+(\d+)\s+slash\s+commands,\s+"
                r"(\d+)\s+specialist\s+agents,\s+(\d+)\s+passing\s+tests",
                readme)
if inv is None:
    problems.append("README inventory line not found "
                    "(N skills, N slash commands, N specialist agents, "
                    "N passing tests)")
else:
    for label, actual, quoted in (("skills", skills, inv.group(1)),
                                  ("slash commands", commands, inv.group(2)),
                                  ("specialist agents", agents, inv.group(3)),
                                  ("passing tests", tests, inv.group(4))):
        if actual is not None and actual != int(quoted):
            problems.append(f"README inventory says {quoted} {label}, "
                            f"canonical source says {actual}")
if tests is not None and f"tests-{tests}%20passing" not in readme:
    problems.append(f"README tests badge out of sync: canonical count "
                    f"is {tests}")

print("\n".join(problems))
PYEOF
)
[ -n "$hits" ] && { say "FAIL information integrity:"; say "$hits"; fail=1; }

[ "$fail" -eq 0 ] && say "audit: clean"
exit "$fail"
