# organic-os Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish the organic-os Claude plugin: one installable plugin with three bounded modules (head-of-organic, onsite-optimizer, content-engine) plus core file contracts, tiered Google Ads keyword intel, channel-agnostic approval gates, and full docs, per the approved spec at `docs/specs/2026-07-18-organic-os-design.md`.

**Architecture:** Skills + agents + plain Python/bash scripts (no stdio MCP servers, so everything runs on Claude Code CLI and Cowork). A `lib/core` contract layer owns all reads/writes of the per-site "brain" repo; modules import core, never each other. Mutations execute only through an approval gate enforced in code.

**Tech Stack:** Markdown skills/agents/commands per the Claude plugin format; Python 3.11+ (stdlib + pyyaml; google-ads and requests imported lazily and optional); bash; PHP (one mu-plugin file); pytest; GitHub Actions.

**Working directory for every task:** `/Users/shiva/Documents/Claude/Projects/organic-os` (git repo, branch `main`). Playground WordPress deployment is OUT OF SCOPE (parallel session builds it from spec §10; Task 19 only ships reference files).

**Global rules for every task (from spec + house style):**
- No em-dashes anywhere. Use ` - ` or commas.
- No banned phrases (seamless, robust, delve, transform, unlock, supercharge, game-changer, cutting-edge, world-class, best-in-class, synergy, holistic, revolutionary, leverage-as-verb).
- Zero personal/employer data: no Exotel, Ameyo, wsofi, phone numbers, employer metrics. `scripts/audit.sh` (Task 2) enforces this; run it before every commit.
- Zero secrets in the repo, ever. Credentials live in `~/.config/organic-os/` or env vars.
- Python: tests first (pytest), minimal implementation, run tests, commit. Test deps are mocked/injected; the google-ads and requests libraries must NOT be required to run the test suite.

---

## File structure (locked before tasks)

```
organic-os/
  .claude-plugin/marketplace.json          # marketplace with 1 plugin (Task 1)
  plugin/
    .claude-plugin/plugin.json             # name organic-os, v0.1.0 (Task 1)
    commands/                              # slash commands, thin: each invokes its skill (T7,9,11,12,15,16)
      setup.md  daily.md  weekly.md  monthly-audit.md  keywords.md  citations.md
      competitors.md  onsite-audit.md  propose.md  apply.md  publish.md  measure.md
      produce.md  image.md  task-board.md  status.md
    skills/
      setup/SKILL.md                       # onboarding interview (T7)
      hoo-orchestrator/SKILL.md            # (T9)
      hoo-daily/SKILL.md                   # (T9)
      hoo-weekly/SKILL.md                  # (T9)
      hoo-monthly-audit/SKILL.md           # (T12)
      hoo-keyword-intel/SKILL.md           # (T11)
      hoo-citation-tracker/SKILL.md        # (T12)
      hoo-competitor-intel/SKILL.md        # (T12)
      hoo-reflector/SKILL.md               # (T12)
      hoo-task-board/SKILL.md              # (T12)
      onsite-audit/SKILL.md                # (T15)
      onsite-propose/SKILL.md              # (T15)
      onsite-apply/SKILL.md                # (T15)
      onsite-publish/SKILL.md              # (T15)
      onsite-measure/SKILL.md              # (T15)
      ce-produce/SKILL.md                  # (T16)
      ce-image/SKILL.md                    # (T16)
    agents/
      technical-seo-auditor.md  content-strategy-architect.md  aeo-geo-optimizer.md
      entity-schema-engineer.md serp-ai-monitor.md  competitive-intel-analyst.md
      link-authority-strategist.md  analytics-reporting-chief.md            # (T8)
      ce-researcher.md  ce-writer.md  ce-brand-auditor.md  ce-seo-aeo.md
      ce-qa.md  ce-editor.md                                                # (T16)
    lib/
      core/__init__.py  core/contracts.py  core/approval.py  core/telegram.py
      core/init_site_repo.py  core/templates/site-profile.yaml             # (T4,5,6)
      hoo/google_ads/__init__.py  tier.py  keyword_ideas.py  historical.py
      hoo/google_ads/gaql.py  csv_import.py                                 # (T10,11)
      onsite/wp.py                                                          # (T13)
  playground/
    docker-compose.yml  uploads.ini  Caddyfile.snippet  wp-extras/organic-os-bridge.php
    RUNBOOK.md                                                              # (T14,19)
  scripts/audit.sh                                                          # (T2)
  tests/  (mirrors lib: test_contracts.py test_approval.py test_telegram.py
           test_init_site_repo.py test_google_ads.py test_csv_import.py test_wp.py)
  .github/workflows/ci.yml                                                  # (T2)
  docs/ adr/ specs/ plans/ credentials/ ...                                 # (T3,17)
  README.md SECURITY.md LICENSE CHANGELOG.md .gitignore                     # (T1,18)
```

Module boundary rule (enforced by audit): `lib/hoo/**` and `lib/onsite/**` may import `lib/core/**`; nothing under `lib/` may import across `hoo`/`onsite`; skills reference only their own module's lib scripts plus core.

---

# Phase 0 - Foundation

### Task 1: Repo skeleton and manifests

**Files:**
- Create: `.claude-plugin/marketplace.json`, `plugin/.claude-plugin/plugin.json`, `.gitignore`, `LICENSE`, `CHANGELOG.md`, `README.md` (stub, replaced in Task 18)

- [ ] **Step 1: Write `.claude-plugin/marketplace.json`**

```json
{
  "name": "organic-os",
  "owner": { "name": "Shivaa Tripathi", "url": "https://shivaatripathi.com" },
  "plugins": [
    {
      "name": "organic-os",
      "source": "./plugin",
      "description": "An agentic organic-growth operating system: observe, decide, approve, apply, verify, learn. SEO + AEO/GEO + content + on-page execution with a memory that compounds.",
      "version": "0.1.0"
    }
  ]
}
```

- [ ] **Step 2: Write `plugin/.claude-plugin/plugin.json`**

```json
{
  "name": "organic-os",
  "version": "0.1.0",
  "description": "Agentic organic growth for any website: analytics-driven signals, keyword intelligence, AI-citation tracking, gated on-page execution on WordPress, and a learning loop that compounds in a per-site git repo.",
  "author": { "name": "Shivaa Tripathi", "url": "https://shivaatripathi.com" },
  "homepage": "https://github.com/shalintripathi/organic-os",
  "license": "MIT"
}
```

- [ ] **Step 3: Write `.gitignore`**

```
__pycache__/
*.pyc
.venv/
.env
*.local.*
.DS_Store
node_modules/
```

- [ ] **Step 4: Write `LICENSE` (MIT, copyright 2026 Shivakant Tripathi), `CHANGELOG.md` (heading `# Changelog` + `## [Unreleased]`), and a 5-line `README.md` stub: project name, one-line description, "Under construction - see docs/specs/ for the design. Full README lands with v0.1.0."**

- [ ] **Step 5: Validate JSON and commit**

Run: `python3 -m json.tool .claude-plugin/marketplace.json && python3 -m json.tool plugin/.claude-plugin/plugin.json`
Expected: both print parsed JSON, exit 0.

```bash
git add -A && git commit -m "feat: repo skeleton, marketplace and plugin manifests"
```

### Task 2: audit.sh and CI gate

**Files:**
- Create: `scripts/audit.sh`, `.github/workflows/ci.yml`

- [ ] **Step 1: Write `scripts/audit.sh`**

```bash
#!/usr/bin/env bash
# organic-os repo audit: personal-data leakage, secrets, style, module boundaries.
# Usage: ./scripts/audit.sh   (exit 0 = clean, exit 1 = violations)
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
say() { printf '%s\n' "$*"; }

# 1. Personal/employer data must never appear (spec §15). Case-insensitive.
PERSONAL='exotel|ameyo|wsofi|78382|32X|29X MROI|4\.2M|5-FTE|MQL to SQL|CAC reduction'
hits=$(grep -rniE "$PERSONAL" --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv . || true)
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
```

- [ ] **Step 2: Make executable, run, expect clean**

Run: `chmod +x scripts/audit.sh && ./scripts/audit.sh`
Expected: `audit: clean`, exit 0.

- [ ] **Step 3: Write `.github/workflows/ci.yml`**

```yaml
name: ci
on: [push, pull_request]
jobs:
  audit-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pyyaml pytest
      - run: ./scripts/audit.sh
      - run: '[ -d tests ] && pytest -q || echo "no tests yet"'
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: audit script (personal data, secrets, style, boundaries) + CI"
```

### Task 3: ADRs 0001-0006

**Files:**
- Create: `docs/adr/0001-single-plugin-marketplace.md` through `docs/adr/0006-no-scraping.md`

- [ ] **Step 1: Write the six ADRs.** Each uses this exact MADR-lite template (fill the fields as given below):

```markdown
# ADR-NNNN: <title>

- Status: accepted
- Date: 2026-07-18
- Decision makers: Shivaa Tripathi (human), Claude (agent)

## Context
<2-4 sentences>

## Decision
<1-3 sentences>

## Consequences
<2-4 bullets, include at least one cost/risk>

## Agent Context
Proposed by the agent from research evidence; approved by the human in the
2026-07-18 design session. Evidence: <one line naming the source>.
```

The six, with their content in brief (write each out fully in the file):
1. **0001-single-plugin-marketplace**: one install for users, three bounded modules inside; marketplace format retained for distribution; cost: one version number for all modules.
2. **0002-git-repo-as-brain**: per-site git repo holds profile/signals/skillbook/ADRs/approvals; enables cloud routines and versioned memory; local-folder mode for users without GitHub; cost: git familiarity needed for full power.
3. **0003-rest-over-mcp-for-wordpress**: WP REST + Application Passwords + RankMath meta bridge; wordpress mcp-adapter is pre-1.0 with read-only core abilities; revisit at its 1.0. Evidence: WordPress/mcp-adapter status research 2026-07-18.
4. **0004-tiered-google-ads-access**: keyword-intel degrades Basic → Explorer → GSC → CSV because planner calls gate on Basic access and approvals are backlogged in 2026.
5. **0005-execution-agnostic-routines**: cadences declared in the site repo; runtimes = claude.ai schedule, local, CI, manual; chosen at setup; no hardcoded scheduler.
6. **0006-no-scraping**: no SERP/autocomplete scrapers shipped; Google SearchGuard + the SerpApi lawsuit (Dec 2025) make it a legal risk we refuse to transfer to users; BYO third-party APIs documented instead.

- [ ] **Step 2: Audit and commit**

Run: `./scripts/audit.sh` Expected: `audit: clean`

```bash
git add -A && git commit -m "docs: ADRs 0001-0006 (packaging, brain, WP path, Ads tiers, runtimes, no-scraping)"
```

# Phase 1 - Core contracts

### Task 4: Site-profile template and site-repo scaffolder

**Files:**
- Create: `plugin/lib/core/__init__.py` (empty), `plugin/lib/core/templates/site-profile.yaml`, `plugin/lib/core/init_site_repo.py`
- Test: `tests/test_init_site_repo.py`

- [ ] **Step 1: Write `plugin/lib/core/templates/site-profile.yaml`**

```yaml
# organic-os site profile. One file per site. Edit freely; setup fills it.
site:
  url: ""                # https://example.com
  name: ""               # brand name
  sitemap: ""            # https://example.com/sitemap.xml
brand:
  voice: []              # e.g. ["first person", "short sentences", "facts before adjectives"]
  banned_phrases: []     # phrases the drafts must never use
  rulebook: ""           # free text: brand and editorial rules
audience:
  segments: []           # ICP segments
  geos: []               # e.g. ["IN", "US"]
  languages: ["en"]
keywords:
  targets: []            # seed target keywords/topics
competitors: []          # domains
operator_notes: []       # "what already works in this niche" - seeded to skillbook at setup
connectors:              # detected at setup: available | absent | unknown
  ga4: unknown
  gsc: unknown
  notion: unknown
  slack: unknown
  canva: unknown
google_ads:
  status: none           # none | explorer | basic | standard
  login_customer_id: ""
wordpress:
  endpoint: ""           # https://site.example/wp-json (empty = not connected)
  username: ""           # app-password user; the password itself lives OUTSIDE this repo
approval:
  channel: in-session    # in-session | telegram | slack | email | pr-merge
  telegram_chat_id: ""
runtime:
  mode: manual           # claude-scheduled | local | ci | manual
routines:
  daily: true
  weekly: true
  monthly: true
brain:
  mode: local            # git | local
  repo: ""               # git remote when mode: git
```

- [ ] **Step 2: Write the failing test `tests/test_init_site_repo.py`**

```python
import subprocess, sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from core.init_site_repo import init_site_repo  # noqa: E402


def test_scaffold_creates_brain_layout(tmp_path):
    root = tmp_path / "organic-hq-example"
    init_site_repo(root, site_url="https://example.com", site_name="Example Co")
    for p in ["site-profile.yaml", "skillbook.md", "approvals/queue.md",
              "signals/.gitkeep", "reflections/.gitkeep", "decisions/.gitkeep",
              "briefs/.gitkeep", "proposals/.gitkeep", "runs/.gitkeep",
              "keywords/tracking.yaml", "outcomes/.gitkeep", ".gitignore"]:
        assert (root / p).exists(), p
    prof = (root / "site-profile.yaml").read_text()
    assert "https://example.com" in prof and "Example Co" in prof
    assert "# Skillbook" in (root / "skillbook.md").read_text()


def test_scaffold_is_idempotent(tmp_path):
    root = tmp_path / "s"
    init_site_repo(root, site_url="https://a.com", site_name="A")
    (root / "skillbook.md").write_text("# Skillbook\n\nS-001 [evidence: anecdotal] keep me\n")
    init_site_repo(root, site_url="https://a.com", site_name="A")
    assert "keep me" in (root / "skillbook.md").read_text()  # never overwrites existing
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest tests/test_init_site_repo.py -q`
Expected: FAIL (ModuleNotFoundError: core.init_site_repo)

- [ ] **Step 4: Write `plugin/lib/core/init_site_repo.py`**

```python
"""Scaffold a site 'brain' repo. Idempotent: never overwrites existing files."""
from pathlib import Path

DIRS = ["signals", "reflections", "decisions", "briefs", "proposals", "runs", "outcomes",
        "approvals", "keywords"]

SKILLBOOK_HEADER = (
    "# Skillbook\n\n"
    "Curated lessons. One entry per line, appended by the curator only.\n"
    "Format: S-NNN [evidence: strong|moderate|anecdotal] "
    "[helpful: n, harmful: n, last-confirmed: YYYY-MM-DD] lesson text (source)\n\n"
)


def init_site_repo(root, site_url: str = "", site_name: str = "") -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for d in DIRS:
        (root / d).mkdir(exist_ok=True)
        keep = root / d / ".gitkeep"
        if not any((root / d).iterdir()):
            keep.touch()
    template = Path(__file__).parent / "templates" / "site-profile.yaml"
    _write_once(root / "site-profile.yaml",
                template.read_text().replace('url: ""', f'url: "{site_url}"', 1)
                                     .replace('name: ""', f'name: "{site_name}"', 1))
    _write_once(root / "skillbook.md", SKILLBOOK_HEADER)
    _write_once(root / "approvals" / "queue.md", "# Pending approvals\n\n(none)\n")
    _write_once(root / "keywords" / "tracking.yaml", "keywords: []\n")
    _write_once(root / ".gitignore", "*.secret\n.env\n")
    return root


def _write_once(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("--url", default=""); ap.add_argument("--name", default="")
    a = ap.parse_args()
    print(init_site_repo(a.root, a.url, a.name))
```

- [ ] **Step 5: Run tests to verify pass, then audit + commit**

Run: `python3 -m pytest tests/test_init_site_repo.py -q` Expected: 2 passed
Run: `./scripts/audit.sh` Expected: `audit: clean`

```bash
git add -A && git commit -m "feat(core): site-profile template + idempotent site-repo scaffolder"
```

### Task 5: contracts.py - statuses, signals, briefs/proposals, skillbook

**Files:**
- Create: `plugin/lib/core/contracts.py`
- Test: `tests/test_contracts.py`

- [ ] **Step 1: Write the failing tests `tests/test_contracts.py`**

```python
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import pytest  # noqa: E402
from core.init_site_repo import init_site_repo  # noqa: E402
from core import contracts as C  # noqa: E402


@pytest.fixture
def root(tmp_path):
    return init_site_repo(tmp_path / "brain", "https://ex.com", "Ex")


def test_append_signal_is_append_only(root):
    C.append_signal(root, "clicks dropped 12% on /pricing", date="2026-07-18")
    C.append_signal(root, "second observation", date="2026-07-18")
    text = (root / "signals" / "2026-07-18.md").read_text()
    assert text.index("clicks dropped") < text.index("second observation")


def test_create_and_load_proposal(root):
    p = C.create_item(root, kind="onpage-fix", slug="pricing-title",
                      title="Rewrite /pricing title tag",
                      body="Change title to 'Pricing - Ex'.",
                      target="https://ex.com/pricing", source="signal:2026-07-18")
    item = C.load_item(p)
    assert item["meta"]["status"] == "proposed"
    assert item["meta"]["kind"] == "onpage-fix"
    assert "Rewrite /pricing" in item["meta"]["title"]


def test_status_lifecycle_enforced(root):
    p = C.create_item(root, kind="onpage-fix", slug="x", title="t", body="b",
                      target="https://ex.com/x", source="s")
    with pytest.raises(C.ContractError):
        C.set_status(p, "applied", actor="agent")          # cannot skip approval
    C.set_status(p, "approved", actor="shivaa", channel="in-session")
    C.set_status(p, "applied", actor="agent")
    meta = C.load_item(p)["meta"]
    assert meta["status"] == "applied"
    assert meta["approvals"][0]["actor"] == "shivaa"


def test_require_approved_gate(root):
    p = C.create_item(root, kind="publish", slug="post-1", title="t", body="b",
                      target="", source="s")
    with pytest.raises(C.ContractError):
        C.require_approved(p)
    C.set_status(p, "approved", actor="shivaa", channel="pr-merge")
    C.require_approved(p)  # no raise


def test_skillbook_append_and_update(root):
    sid = C.skillbook_append(root, "Answer capsule under 60 words lifts snippet capture",
                             evidence="strong", source="princeton-geo")
    assert sid == "S-001"
    sid2 = C.skillbook_append(root, "Second lesson", evidence="anecdotal", source="operator")
    assert sid2 == "S-002"
    C.skillbook_update(root, "S-001", helpful=1)
    book = (root / "skillbook.md").read_text()
    assert "[helpful: 1, harmful: 0" in book.split("S-001")[1].split("\n")[0]


def test_skillbook_deprecate_not_delete(root):
    C.skillbook_append(root, "old idea", evidence="anecdotal", source="x")
    C.skillbook_update(root, "S-001", deprecate=True)
    line = [l for l in (root / "skillbook.md").read_text().splitlines() if "S-001" in l][0]
    assert line.startswith("~~") or "DEPRECATED" in line


def test_queue_index_lists_pending(root):
    C.create_item(root, kind="content-brief", slug="guide", title="A guide", body="b",
                  target="", source="s")
    C.rebuild_queue(root)
    q = (root / "approvals" / "queue.md").read_text()
    assert "A guide" in q and "content-brief" in q
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_contracts.py -q`
Expected: FAIL (No module named 'core.contracts')

- [ ] **Step 3: Write `plugin/lib/core/contracts.py`**

```python
"""File contracts for the site brain. The ONLY code that reads/writes brain files.

Item = a brief or proposal: markdown file with YAML frontmatter.
Lifecycle: proposed -> approved|rejected; approved -> applied|drafted;
drafted -> published; applied|published -> measured.
Skillbook: append-only entries with IDs; updates touch single entries only.
"""
from __future__ import annotations
import datetime as _dt
import re
from pathlib import Path

import yaml

TRANSITIONS = {
    "proposed": {"approved", "rejected"},
    "approved": {"applied", "drafted"},
    "drafted": {"published"},
    "applied": {"measured"},
    "published": {"measured"},
}
KINDS = {"onpage-fix", "content-brief", "publish", "strategy"}


class ContractError(Exception):
    pass


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -- signals ------------------------------------------------------------------

def append_signal(root, text: str, date: str | None = None) -> Path:
    root = Path(root)
    date = date or _dt.date.today().isoformat()
    f = root / "signals" / f"{date}.md"
    stamp = _now()
    with f.open("a") as fh:
        fh.write(f"- [{stamp}] {text}\n")
    return f


# -- items (briefs + proposals) ----------------------------------------------

def _folder(root: Path, kind: str) -> Path:
    return root / ("briefs" if kind == "content-brief" else "proposals")


def create_item(root, kind: str, slug: str, title: str, body: str,
                target: str, source: str) -> Path:
    if kind not in KINDS:
        raise ContractError(f"unknown kind {kind!r}")
    root = Path(root)
    date = _dt.date.today().strftime("%Y%m%d")
    path = _folder(root, kind) / f"{date}-{slug}.md"
    if path.exists():
        raise ContractError(f"item exists: {path}")
    meta = {"id": f"{'b' if kind == 'content-brief' else 'p'}-{date}-{slug}",
            "kind": kind, "status": "proposed", "created": _now(),
            "title": title, "target": target, "source": source, "approvals": []}
    _dump(path, meta, body)
    return path


def load_item(path) -> dict:
    raw = Path(path).read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise ContractError(f"no frontmatter: {path}")
    return {"meta": yaml.safe_load(m.group(1)), "body": m.group(2)}


def set_status(path, status: str, actor: str, channel: str | None = None) -> None:
    item = load_item(path)
    cur = item["meta"]["status"]
    if status not in TRANSITIONS.get(cur, set()):
        raise ContractError(f"illegal transition {cur} -> {status}")
    item["meta"]["status"] = status
    if status in {"approved", "rejected"}:
        item["meta"]["approvals"].append(
            {"actor": actor, "channel": channel or "unknown",
             "decision": status, "at": _now()})
    _dump(Path(path), item["meta"], item["body"])


def require_approved(path) -> dict:
    item = load_item(path)
    if item["meta"]["status"] != "approved":
        raise ContractError(
            f"MUTATION BLOCKED: {Path(path).name} is '{item['meta']['status']}', "
            "needs 'approved' with a recorded approval")
    return item


def _dump(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False).strip()
                    + "\n---\n" + body.lstrip("\n"))


# -- skillbook ----------------------------------------------------------------

_ENTRY = re.compile(r"^(~~)?(S-\d{3}) \[evidence: (\w+)\] "
                    r"\[helpful: (\d+), harmful: (\d+), last-confirmed: ([0-9-]+)\] (.*)$")


def skillbook_append(root, text: str, evidence: str, source: str) -> str:
    if evidence not in {"strong", "moderate", "anecdotal"}:
        raise ContractError("evidence must be strong|moderate|anecdotal")
    book = Path(root) / "skillbook.md"
    ids = [int(m.group(2)[2:]) for line in book.read_text().splitlines()
           if (m := _ENTRY.match(line))]
    sid = f"S-{(max(ids) + 1 if ids else 1):03d}"
    today = _dt.date.today().isoformat()
    with book.open("a") as fh:
        fh.write(f"{sid} [evidence: {evidence}] [helpful: 0, harmful: 0, "
                 f"last-confirmed: {today}] {text} ({source})\n")
    return sid


def skillbook_update(root, sid: str, helpful: int = 0, harmful: int = 0,
                     deprecate: bool = False, edit: str | None = None) -> None:
    book = Path(root) / "skillbook.md"
    out, found = [], False
    for line in book.read_text().splitlines():
        m = _ENTRY.match(line)
        if m and m.group(2) == sid:
            found = True
            h, x = int(m.group(4)) + helpful, int(m.group(5)) + harmful
            text = edit if edit is not None else m.group(7)
            today = _dt.date.today().isoformat()
            new = (f"{sid} [evidence: {m.group(3)}] [helpful: {h}, harmful: {x}, "
                   f"last-confirmed: {today}] {text}")
            out.append(f"~~{new}~~ DEPRECATED" if deprecate else new)
        else:
            out.append(line)
    if not found:
        raise ContractError(f"no skillbook entry {sid}")
    book.write_text("\n".join(out) + "\n")


# -- approvals queue ----------------------------------------------------------

def rebuild_queue(root) -> Path:
    root = Path(root)
    rows = []
    for folder in ("briefs", "proposals"):
        for f in sorted((root / folder).glob("*.md")):
            meta = load_item(f)["meta"]
            if meta["status"] == "proposed":
                rows.append(f"- `{meta['id']}` [{meta['kind']}] {meta['title']} "
                            f"(created {meta['created']}) -> {folder}/{f.name}")
    q = root / "approvals" / "queue.md"
    q.write_text("# Pending approvals\n\n" + ("\n".join(rows) + "\n" if rows else "(none)\n"))
    return q
```

- [ ] **Step 4: Run tests, expect pass; audit; commit**

Run: `python3 -m pytest tests/test_contracts.py tests/test_init_site_repo.py -q` Expected: all pass
Run: `./scripts/audit.sh` Expected: `audit: clean`

```bash
git add -A && git commit -m "feat(core): contracts - signals, item lifecycle with approval gate, skillbook ops, queue"
```

### Task 6: Approval adapters (queue + Telegram)

**Files:**
- Create: `plugin/lib/core/approval.py`, `plugin/lib/core/telegram.py`
- Test: `tests/test_approval.py`, `tests/test_telegram.py`

- [ ] **Step 1: Write failing tests `tests/test_approval.py`**

```python
import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from core.init_site_repo import init_site_repo  # noqa: E402
from core import contracts as C  # noqa: E402
from core import approval as A  # noqa: E402


def test_pending_lists_and_approve_records(tmp_path):
    root = init_site_repo(tmp_path / "b", "https://e.com", "E")
    p = C.create_item(root, "onpage-fix", "fix1", "Fix one", "body", "https://e.com/1", "s")
    assert [i["meta"]["id"] for i in A.pending(root)] == ["p-" + p.name[:8] + "-fix1"]
    A.record_decision(root, item_id=A.pending(root)[0]["meta"]["id"],
                      decision="approved", actor="shivaa", channel="telegram")
    assert A.pending(root) == []
    assert C.load_item(p)["meta"]["status"] == "approved"
```

- [ ] **Step 2: Write failing tests `tests/test_telegram.py`** (transport injected, no network)

```python
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
```

- [ ] **Step 3: Run both, expect ModuleNotFoundError.**

- [ ] **Step 4: Write `plugin/lib/core/approval.py`**

```python
"""Channel-neutral approval operations over the brain repo."""
from pathlib import Path
from . import contracts as C


def pending(root):
    items = []
    for folder in ("briefs", "proposals"):
        for f in sorted((Path(root) / folder).glob("*.md")):
            item = C.load_item(f)
            if item["meta"]["status"] == "proposed":
                item["path"] = f
                items.append(item)
    return items


def find(root, item_id: str):
    for folder in ("briefs", "proposals"):
        for f in (Path(root) / folder).glob("*.md"):
            if C.load_item(f)["meta"]["id"] == item_id:
                return f
    raise C.ContractError(f"no item {item_id}")


def record_decision(root, item_id: str, decision: str, actor: str, channel: str) -> None:
    C.set_status(find(root, item_id), decision, actor=actor, channel=channel)
    C.rebuild_queue(root)
```

- [ ] **Step 5: Write `plugin/lib/core/telegram.py`**

```python
"""Telegram adapter. Transport is injected so tests never touch the network.

Real transport (used by skills):
    from core.telegram import UrllibHTTP
    http = UrllibHTTP()
Approval grammar in chat: 'approve <item-id>' or 'reject <item-id> [reason]'.
"""
import json
import re
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"
_DECISION = re.compile(r"^(approve|reject)\s+([bp]-[\w-]+)\s*(.*)$", re.I)


class UrllibHTTP:
    def post(self, url, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    def get(self, url, params):
        with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params),
                                    timeout=30) as r:
            return json.load(r)


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
        if msg.get("chat", {}).get("id") != chat_id:
            continue
        m = _DECISION.match(msg.get("text", "").strip())
        if m:
            verb, item_id, reason = m.groups()
            decisions.append((item_id,
                              "approved" if verb.lower() == "approve" else "rejected",
                              reason.strip()))
    return decisions, last
```

- [ ] **Step 6: Run all tests, audit, commit**

Run: `python3 -m pytest tests -q` Expected: all pass
Run: `./scripts/audit.sh` Expected: `audit: clean`

```bash
git add -A && git commit -m "feat(core): approval ops + injectable Telegram adapter"
```

### Task 7: Setup skill and command

**Files:**
- Create: `plugin/skills/setup/SKILL.md`, `plugin/commands/setup.md`, `plugin/commands/status.md`

- [ ] **Step 1: Write `plugin/skills/setup/SKILL.md`** (complete content):

```markdown
---
name: setup
description: Use when the user installs organic-os, says "set up organic-os", "onboard my site", "connect my website", or runs /organic-os:setup. Interviews the user, scaffolds the per-site brain repo, records connectors and credentials references, seeds the skillbook with operator knowledge, and registers routines for the chosen runtime.
---

# organic-os setup

You are onboarding a site into organic-os. Everything site-specific comes from
this interview. Never assume; ask. One question at a time, AskUserQuestion
with options where possible.

## Interview order

1. Site: URL, brand name, sitemap URL (offer to guess `<url>/sitemap.xml` and verify with a fetch).
2. Brand rulebook: voice rules, banned phrases (offer sensible defaults: first person, short sentences, facts before adjectives, no exclamation marks; user edits).
3. Audience: segments/ICP, geographies, languages.
4. Keywords: target keywords/topics (free list; can be empty - keyword-intel will propose).
5. Competitors: domains (up to 5 to start).
6. Operator knowledge: "What do you already know works in this niche - tips, channels, formats?" Each answer becomes a skillbook entry tagged `evidence: anecdotal`.
7. Connectors: probe availability (try listing GA4/GSC tools; ask about Notion, Slack, Canva). Record available/absent in site-profile - never store tokens.
8. Google Ads: ask whether they have a developer token and which access level. Point to docs/credentials/google-ads-token.md. Record status only.
9. WordPress: connected site? If yes: endpoint URL + username; instruct the user to create an Application Password (Users -> Profile) and store it via:
   `mkdir -p ~/.config/organic-os && read -s -p "App password: " P && printf 'WP_APP_PASSWORD=%s\n' "$P" > ~/.config/organic-os/<site-slug>.env && chmod 600 ~/.config/organic-os/<site-slug>.env`
   Never echo the password into the transcript.
10. Approval channel: in-session | telegram | slack | email | pr-merge. For telegram: bot token (stored in the same env file as TELEGRAM_BOT_TOKEN) + chat id. No channel is privileged; default in-session.
11. Runtime for routines: claude-scheduled | local | ci | manual. Explain costs honestly: claude-scheduled and local run on the user's Claude subscription; ci uses an API key billed per token.
12. Brain mode: git repo (recommended; needed for claude-scheduled and ci runtimes and for versioned memory) or local folder.

## Actions after the interview

1. Run: `python3 "$CLAUDE_PLUGIN_ROOT/lib/core/init_site_repo.py" <brain-path> --url <url> --name <name>`
2. Fill `site-profile.yaml` with every answer (edit the file directly).
3. Seed skillbook: for each operator note, run a small Python snippet calling `core.contracts.skillbook_append(root, note, evidence="anecdotal", source="operator")`.
4. If brain mode git: `git init`, first commit, offer `gh repo create <name> --private`.
5. Register routines per the chosen runtime by following docs/routines.md for that runtime, and write the chosen cadence into site-profile `routines:`.
6. Print a summary: what is configured, what is degraded (missing connectors/credentials) and the exact doc to fix each gap.

## Rules

- Analysis-only mode is a valid outcome: a user with zero credentials still gets
  audits, briefs, and keyword work from public data.
- Never write a secret into the brain repo or the transcript. Env files only.
- Re-running setup is safe: the scaffolder never overwrites; the interview
  offers current values as defaults.
```

- [ ] **Step 2: Write `plugin/commands/setup.md`**

```markdown
---
description: Onboard a site into organic-os (interview + brain scaffold + routines)
---
Invoke the organic-os:setup skill and follow it end to end.
```

- [ ] **Step 3: Write `plugin/commands/status.md`**

```markdown
---
description: Show organic-os site status - pending approvals, recent signals, next routine
---
Locate the brain repo (site-profile.yaml). Print: site url; approval channel and
runtime; count + list of pending items from approvals/queue.md; last 5 signal
lines; skillbook entry count; date of last reflection. If anything is missing,
say which setup step fixes it. Read-only: change nothing.
```

- [ ] **Step 4: Audit + commit**

Run: `./scripts/audit.sh` Expected: `audit: clean`

```bash
git add -A && git commit -m "feat: setup skill + /organic-os:setup and :status commands"
```

# Phase 2 - head-of-organic module

### Task 8: The eight specialist agents

**Files:**
- Create: `plugin/agents/technical-seo-auditor.md`, `content-strategy-architect.md`, `aeo-geo-optimizer.md`, `entity-schema-engineer.md`, `serp-ai-monitor.md`, `competitive-intel-analyst.md`, `link-authority-strategist.md`, `analytics-reporting-chief.md`

- [ ] **Step 1: Write all eight agent files.** Every file follows this exact template (shown filled for the first agent; write the other seven with the per-agent content from the table in Step 2):

```markdown
---
name: technical-seo-auditor
description: Use to audit any site's technical SEO - crawlability, indexability, Core Web Vitals, on-page elements, AI-crawler readiness. Reads the organic-os site profile for context. Example - user says "check site health for example.com" -> run this agent with the profile path and site URL.
tools: Read, WebFetch, WebSearch, Bash
---

You are the technical SEO specialist on an organic-growth team.

Input contract: the prompt gives you (1) the path to site-profile.yaml, (2) the
target URL(s). Read the profile first; respect its geos/languages.

Method:
1. Fetch robots.txt, sitemap, homepage, and 3-5 key templates. Note status
   codes, canonicals, meta robots, title/description/H1 per page.
2. Check AI-crawler access: is content server-rendered (fetch raw HTML and
   verify the main copy is present without JS)? Are GPTBot/ClaudeBot/
   PerplexityBot allowed in robots.txt?
3. Check Core Web Vitals via PageSpeed Insights API if a key is configured,
   else note "lab check skipped - no PSI key".
4. Flag broken internals, redirect chains, duplicate titles, missing alts on
   content images.

Output contract (return exactly this shape):
## Findings
- one bullet per finding: [severity P0-P3] observation - evidence URL/line
## Signals
- one line per signal worth tracking, each with: observation | why it matters |
  falsifiability ("we are wrong if...") | leading indicator to watch
## Proposed fixes
- one bullet per fix: target URL | change | expected effect | effort S/M/L

Never invent metrics. If a check needs a credential the environment lacks,
say "skipped: <check> (needs <credential>)" instead of guessing.
```

- [ ] **Step 2: Per-agent content table.** Keep the same frontmatter shape (name, one-sentence "Use to..." description with a trigger example, tools) and the same three-part output contract (Findings / Signals / Proposed fixes - for the reporting chief: Findings / Signals / Narrative). Method sections per agent:

| Agent | tools | Method focus (write 4-6 numbered steps from this) |
|---|---|---|
| content-strategy-architect | Read, WebFetch, WebSearch | Map existing content vs profile keywords/segments; hub-and-spoke gaps; propose briefs (title, angle, capsule, target query set, internal links); every brief cites the signal or keyword data that justifies it |
| aeo-geo-optimizer | Read, WebFetch, WebSearch | Evidence-ranked AEO: answer capsules present? statistics/quotes/citations in content? extractable structure (lists, tables)? freshness dates? server-rendered? Bing indexed? Flag weak-evidence tactics (llms.txt, schema-for-citations) as optional with honest labels |
| entity-schema-engineer | Read, WebFetch, Bash | Detect existing JSON-LD; validate shape; propose Organization/Article/FAQ schema as JSON-LD blocks; output ready-to-apply `agent_jsonld` payloads per URL; never claim schema drives AI citations (evidence: weak) |
| serp-ai-monitor | Read, WebFetch, WebSearch | For profile target keywords: check current SERP presence and AI-answer presence (run the profile's query set through available engines); record mention/citation per query; diff vs last run in runs/; emit drop/gain signals |
| competitive-intel-analyst | Read, WebFetch, WebSearch | For each profile competitor: new/changed pages (sitemap or blog index diff vs last run), topics covered we lack, their AI-citation presence on our query set; output gap list ranked by profile fit |
| link-authority-strategist | Read, WebFetch, WebSearch | Internal link graph of key pages (crawl depth 2); orphan pages; anchor quality; external authority ideas strictly white-hat (resource pages, digital PR angles from the profile's operator notes); no link buying |
| analytics-reporting-chief | Read, Bash, WebFetch | Pull GA4/GSC via available connector tools (skip gracefully if absent); WoW/MoM deltas on clicks, impressions, CTR, position, AI referrals; anomalies to signals; write the weekly narrative in plain language |

- [ ] **Step 3: Audit + commit**

Run: `./scripts/audit.sh` Expected: `audit: clean`

```bash
git add -A && git commit -m "feat(hoo): eight generalized specialist agents"
```

### Task 9: Orchestrator, daily, weekly skills

**Files:**
- Create: `plugin/skills/hoo-orchestrator/SKILL.md`, `plugin/skills/hoo-daily/SKILL.md`, `plugin/skills/hoo-weekly/SKILL.md`
- Create: `plugin/commands/daily.md`, `plugin/commands/weekly.md` (same thin shape as `setup.md`: one description line + "Invoke the organic-os:<skill> skill.")

- [ ] **Step 1: Write `plugin/skills/hoo-orchestrator/SKILL.md`**

```markdown
---
name: hoo-orchestrator
description: Use for any broad organic-growth request - "audit my organic presence", "what should we do this month", "full SEO/AEO review". Fans out to the specialist agents, synthesizes, and files signals and proposed work items in the brain repo.
---

# Head of Organic - orchestrator

1. Locate the brain repo (ask if unknown; a repo has site-profile.yaml at root).
   Read site-profile.yaml fully.
2. Decide which specialists the request needs (default full sweep: all eight).
   Launch them as parallel agents, each given the profile path + target URLs.
3. Synthesize results. Deduplicate findings. Rank by impact x confidence.
4. File outputs through lib/core ONLY:
   - observations -> `append_signal` (one call per signal line)
   - content ideas -> `create_item(kind="content-brief", ...)`
   - on-page fixes -> `create_item(kind="onpage-fix", ...)`
   - run artifacts -> `runs/YYYYMMDD-orchestrator/` (numbered raw files + REPORT.md)
5. Rebuild the queue (`rebuild_queue`) and notify per the profile's approval
   channel (see skills/onsite-apply for the adapter pattern). Do NOT apply
   anything: creating items is free, mutating the site is gated elsewhere.
6. Tell the user: top 5 actions, what is queued for approval, what was skipped
   for missing credentials.

Every signal line must be falsifiable: observation + "we are wrong if" + a
leading indicator. Reject vague signals.
```

- [ ] **Step 2: Write `plugin/skills/hoo-daily/SKILL.md`**

```markdown
---
name: hoo-daily
description: Use for the daily signal pull - "run the daily", scheduled daily routine, or "pull today's numbers". Appends observations to the brain repo signals; never mutates the site or the skillbook.
---

# Daily signal pull (Generator role - append only)

1. Read site-profile.yaml. Determine available sources: GSC connector, GA4
   connector, tracked keywords in keywords/tracking.yaml, WordPress endpoint.
2. Pull, for yesterday (or since the last signal date - read the latest file in
   signals/): GSC clicks/impressions/CTR/position for top and tracked queries;
   GA4 sessions + AI-referral sessions (source contains chatgpt/perplexity/
   gemini/copilot); spot-check 3 tracked keywords in one AI engine, rotating.
3. Write one `append_signal` line per notable observation (threshold: any WoW
   move > 10% or position change > 2 or a new AI citation appearing/vanishing).
   Quiet days produce one line: "no notable movement (checked: <sources>)".
4. If an observation crosses P1 (drop > 30% on a money page), also
   `create_item(kind="onpage-fix"...)` or `kind="strategy"` and notify per the
   approval channel.
5. Outcome follow-ups: for items in `outcomes/` with a due measurement date of
   today, run the measurement per skills/onsite-measure and record.
6. If brain mode is git: commit and push with message "signals: YYYY-MM-DD".

Missing sources are stated, never guessed. This skill NEVER writes skillbook.md.
```

- [ ] **Step 3: Write `plugin/skills/hoo-weekly/SKILL.md`**

```markdown
---
name: hoo-weekly
description: Use for the weekly health check + reflection - "run the weekly", scheduled weekly routine. Runs analytics-reporting-chief and serp-ai-monitor, then hands the week to the reflector.
---

# Weekly check

1. Read profile. Launch analytics-reporting-chief and serp-ai-monitor agents
   (parallel) with the profile path.
2. Save their reports under runs/YYYYMMDD-weekly/ (01-analytics.md,
   02-serp-ai.md, REPORT.md synthesis).
3. Append the week's headline observations as signals.
4. Invoke the organic-os:hoo-reflector skill to propose skillbook deltas from
   this week's signals + outcomes.
5. Queue any proposed work items; rebuild queue; notify per approval channel;
   commit + push if git.
```

- [ ] **Step 4: Write the two thin commands, audit, commit**

```bash
git add -A && git commit -m "feat(hoo): orchestrator, daily, weekly skills + commands"
```

### Task 10: Google Ads library (tiers, ideas, historical, GAQL)

**Files:**
- Create: `plugin/lib/hoo/__init__.py`, `plugin/lib/hoo/google_ads/__init__.py`, `tier.py`, `keyword_ideas.py`, `historical.py`, `gaql.py`
- Test: `tests/test_google_ads.py`

Design rule: every function takes an injected `client` (the GoogleAdsClient or a fake); building the real client happens only in `_real_client()` guarded by lazy import, so tests and credential-less machines never import the google-ads package.

- [ ] **Step 1: Write failing tests `tests/test_google_ads.py`**

```python
import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import json  # noqa: E402
import pytest  # noqa: E402
from hoo.google_ads import tier, keyword_ideas, historical  # noqa: E402


class FakeIdeaService:
    def generate_keyword_ideas(self, request=None):
        class Idea:
            def __init__(self, text, vol, comp):
                self.text = text
                self.keyword_idea_metrics = type(
                    "M", (), {"avg_monthly_searches": vol, "competition": comp,
                              "competition_index": 55,
                              "low_top_of_page_bid_micros": 1_000_000,
                              "high_top_of_page_bid_micros": 5_000_000})()
        return [Idea("crm for smb", 1200, 3), Idea("smb crm pricing", 400, 2)]


class FakeClient:
    def __init__(self, planner_ok=True):
        self.planner_ok = planner_ok
    def get_service(self, name):
        if name == "KeywordPlanIdeaService":
            if not self.planner_ok:
                raise RuntimeError("PERMISSION_DENIED: planner blocked")
            return FakeIdeaService()
        raise AssertionError(name)
    def get_type(self, name):
        return type("T", (), {"__init__": lambda s: None})()


def test_detect_tier_basic():
    assert tier.detect(FakeClient(planner_ok=True), customer_id="1") == "basic"

def test_detect_tier_explorer():
    assert tier.detect(FakeClient(planner_ok=False), customer_id="1") == "explorer"


def test_keyword_ideas_normalizes(tmp_path):
    out = keyword_ideas.run(FakeClient(), customer_id="1",
                            seeds=["crm"], site_seed=None, geo="2356", lang="1000",
                            cache_dir=tmp_path)
    assert out[0] == {"keyword": "crm for smb", "avg_monthly_searches": 1200,
                      "competition": 3, "competition_index": 55,
                      "low_bid": 1.0, "high_bid": 5.0}


def test_keyword_ideas_cache_hit(tmp_path):
    a = keyword_ideas.run(FakeClient(), "1", ["crm"], None, "2356", "1000", tmp_path)
    class Exploding:
        def get_service(self, n): raise AssertionError("must use cache")
    b = keyword_ideas.run(Exploding(), "1", ["crm"], None, "2356", "1000", tmp_path)
    assert a == b


def test_historical_batches(monkeypatch):
    calls = []
    def fake_fetch(client, customer_id, batch, geo, lang):
        calls.append(list(batch)); return [{"keyword": k} for k in batch]
    monkeypatch.setattr(historical, "_fetch_batch", fake_fetch)
    monkeypatch.setattr(historical.time, "sleep", lambda s: None)
    out = historical.run(FakeClient(), "1", [f"k{i}" for i in range(450)],
                         geo="2356", lang="1000")
    assert len(calls) == 3 and len(out) == 450  # 200 + 200 + 50
```

- [ ] **Step 2: Run, expect ModuleNotFoundError.**

- [ ] **Step 3: Write `plugin/lib/hoo/google_ads/tier.py`**

```python
"""Detect the effective Google Ads access tier by probing, not guessing."""


def detect(client, customer_id: str) -> str:
    """Returns 'basic' (planner works), 'explorer' (auth ok, planner blocked),
    or raises whatever auth error the client throws (caller reports 'none')."""
    try:
        svc = client.get_service("KeywordPlanIdeaService")
        # A zero-seed dry probe is not supported; probe with one throwaway seed.
        probe = getattr(svc, "generate_keyword_ideas", None)
        if probe is None:
            return "explorer"
        svc.generate_keyword_ideas(request=None)
        return "basic"
    except Exception as e:  # PERMISSION_DENIED / DEVELOPER_TOKEN_NOT_APPROVED
        if "PERMISSION" in str(e).upper() or "TOKEN" in str(e).upper():
            return "explorer"
        raise


def real_client():
    """Build the real GoogleAdsClient from env vars. Lazy import by design."""
    import os
    from google.ads.googleads.client import GoogleAdsClient  # noqa: WPS433
    cfg = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    if os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID"):
        cfg["login_customer_id"] = os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]
    return GoogleAdsClient.load_from_dict(cfg)
```

- [ ] **Step 4: Write `plugin/lib/hoo/google_ads/keyword_ideas.py`**

```python
"""GenerateKeywordIdeas with a 30-day JSON cache (Google refreshes monthly)."""
import hashlib
import json
import time
from pathlib import Path

CACHE_DAYS = 30
_MICROS = 1_000_000


def run(client, customer_id: str, seeds, site_seed, geo: str, lang: str,
        cache_dir) -> list[dict]:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(json.dumps([sorted(seeds or []), site_seed, geo, lang])
                         .encode()).hexdigest()[:16]
    cached = cache_dir / f"ideas-{key}.json"
    if cached.exists() and (time.time() - cached.stat().st_mtime) < CACHE_DAYS * 86400:
        return json.loads(cached.read_text())

    svc = client.get_service("KeywordPlanIdeaService")
    request = _build_request(client, customer_id, seeds, site_seed, geo, lang)
    rows = []
    for idea in svc.generate_keyword_ideas(request=request):
        m = idea.keyword_idea_metrics
        rows.append({"keyword": idea.text,
                     "avg_monthly_searches": int(m.avg_monthly_searches or 0),
                     "competition": int(m.competition or 0),
                     "competition_index": int(m.competition_index or 0),
                     "low_bid": (m.low_top_of_page_bid_micros or 0) / _MICROS,
                     "high_bid": (m.high_top_of_page_bid_micros or 0) / _MICROS})
    cached.write_text(json.dumps(rows, indent=1))
    return rows


def _build_request(client, customer_id, seeds, site_seed, geo, lang):
    try:
        req = client.get_type("GenerateKeywordIdeasRequest")
        req.customer_id = customer_id
        req.language = f"languageConstants/{lang}"
        req.geo_target_constants.append(f"geoTargetConstants/{geo}")
        if site_seed:
            req.site_seed.site = site_seed
        elif seeds:
            req.keyword_seed.keywords.extend(seeds)
        return req
    except Exception:
        return None  # fakes in tests accept request=None
```

- [ ] **Step 5: Write `plugin/lib/hoo/google_ads/historical.py`**

```python
"""GenerateKeywordHistoricalMetrics in batches of 200 with 1.1s spacing
(planning services are limited to 1 QPS per customer id)."""
import time

BATCH = 200
SPACING_S = 1.1


def run(client, customer_id: str, keywords, geo: str, lang: str) -> list[dict]:
    out = []
    for i in range(0, len(keywords), BATCH):
        if i:
            time.sleep(SPACING_S)
        out.extend(_fetch_batch(client, customer_id, keywords[i:i + BATCH], geo, lang))
    return out


def _fetch_batch(client, customer_id, batch, geo, lang) -> list[dict]:
    svc = client.get_service("KeywordPlanIdeaService")
    req = client.get_type("GenerateKeywordHistoricalMetricsRequest")
    req.customer_id = customer_id
    req.keywords.extend(batch)
    req.language = f"languageConstants/{lang}"
    req.geo_target_constants.append(f"geoTargetConstants/{geo}")
    req.historical_metrics_options.include_average_cpc = True
    rows = []
    for r in svc.generate_keyword_historical_metrics(request=req).results:
        m = r.keyword_metrics
        rows.append({"keyword": r.text,
                     "avg_monthly_searches": int(m.avg_monthly_searches or 0),
                     "competition": int(m.competition or 0),
                     "avg_cpc": (getattr(m, "average_cpc_micros", 0) or 0) / 1_000_000})
    return rows
```

- [ ] **Step 6: Write `plugin/lib/hoo/google_ads/gaql.py`**

```python
"""Run an arbitrary GAQL query and emit JSON rows (own-account reporting;
works at Explorer tier). Used by the keyword-intel skill for search-term
mining and keyword coverage."""
import json
import sys


def run(client, customer_id: str, query: str) -> list[dict]:
    svc = client.get_service("GoogleAdsService")
    rows = []
    for row in svc.search(customer_id=customer_id, query=query):
        rows.append(_flatten(row))
    return rows


def _flatten(row) -> dict:
    # google-ads rows are proto-plus; str() round-trip keeps this dependency-free
    try:
        from google.protobuf.json_format import MessageToDict
        return MessageToDict(row._pb, preserving_proto_field_name=True)
    except Exception:
        return {"raw": str(row)}


if __name__ == "__main__":
    from .tier import real_client
    client = real_client()
    print(json.dumps(run(client, sys.argv[1], sys.argv[2]), indent=1))
```

- [ ] **Step 7: Create `plugin/lib/hoo/__init__.py` and `plugin/lib/hoo/google_ads/__init__.py` (both empty). Run tests, audit, commit**

Run: `python3 -m pytest tests/test_google_ads.py -q` Expected: 5 passed
Run: `./scripts/audit.sh` Expected: `audit: clean`

```bash
git add -A && git commit -m "feat(hoo): google-ads lib - tier probe, cached ideas, batched historical, gaql"
```

### Task 11: CSV import + keyword-intel skill

**Files:**
- Create: `plugin/lib/hoo/google_ads/csv_import.py`, `plugin/skills/hoo-keyword-intel/SKILL.md`, `plugin/commands/keywords.md`
- Test: `tests/test_csv_import.py`

- [ ] **Step 1: Write failing test `tests/test_csv_import.py`**

```python
import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from hoo.google_ads import csv_import  # noqa: E402

PLANNER_CSV = """Keyword,Avg. monthly searches,Competition,Top of page bid (low range),Top of page bid (high range)
crm for smb,1300,High,12.5,48.2
smb crm pricing,390,Medium,8.1,30.0
"""

def test_planner_csv_normalizes(tmp_path):
    f = tmp_path / "kp.csv"; f.write_text(PLANNER_CSV)
    rows = csv_import.load_planner_csv(f)
    assert rows[0] == {"keyword": "crm for smb", "avg_monthly_searches": 1300,
                      "competition": "High", "low_bid": 12.5, "high_bid": 48.2}

def test_planner_csv_handles_dash_volumes(tmp_path):
    f = tmp_path / "kp.csv"
    f.write_text('Keyword,Avg. monthly searches,Competition\nx,"10-100",Low\n')
    rows = csv_import.load_planner_csv(f)
    assert rows[0]["avg_monthly_searches"] == 55  # midpoint of a "10-100" range
```

- [ ] **Step 2: Run, expect failure. Then write `plugin/lib/hoo/google_ads/csv_import.py`**

```python
"""Normalize Keyword Planner UI exports (and Auction Insights CSVs) so users
without API access still get keyword data in."""
import csv
from pathlib import Path


def load_planner_csv(path) -> list[dict]:
    rows = []
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            k = (r.get("Keyword") or "").strip()
            if not k:
                continue
            row = {"keyword": k,
                   "avg_monthly_searches": _num(r.get("Avg. monthly searches", "0")),
                   "competition": (r.get("Competition") or "").strip()}
            if r.get("Top of page bid (low range)"):
                row["low_bid"] = float(r["Top of page bid (low range)"])
            if r.get("Top of page bid (high range)"):
                row["high_bid"] = float(r["Top of page bid (high range)"])
            rows.append(row)
    return rows


def _num(v: str) -> int:
    v = (v or "").replace(",", "").replace('"', "").strip()
    if "-" in v:  # "10-100" range -> midpoint
        lo, hi = v.split("-", 1)
        try:
            return (int(lo) + int(hi)) // 2
        except ValueError:
            return 0
    try:
        return int(float(v))
    except ValueError:
        return 0
```

- [ ] **Step 3: Write `plugin/skills/hoo-keyword-intel/SKILL.md`**

```markdown
---
name: hoo-keyword-intel
description: Use for keyword research, competitor keyword gaps, "what should we rank for", "keyword ideas for X", or the /organic-os:keywords command. Detects the user's Google Ads access tier and degrades honestly.
---

# Keyword intelligence (tiered)

0. Read site-profile.yaml (google_ads.status, keywords.targets, competitors,
   geos, languages). Source env from `~/.config/organic-os/<site-slug>.env`
   if present.

## Tier detection (once per session)
Run: `python3 -c` snippet importing `hoo.google_ads.tier`: if env vars missing
-> tier "none". Else build real_client() and `tier.detect()` -> basic|explorer.
Tell the user which tier is active and what that unlocks.

## basic (or standard)
1. Ideas: `keyword_ideas.run` with profile target keywords as seeds AND, per
   competitor, `site_seed=<competitor domain>`. Cache dir: `<brain>/keywords/cache/`.
2. Gap: ideas(own site_seed) vs ideas(competitor site_seed) - keywords in
   their set, absent from ours, volume >= 100. Rank by volume x profile fit.
3. Metrics for the shortlist: `historical.run` (batches of 200 handled inside).
4. Write `runs/YYYYMMDD-keywords/` (01-ideas.json, 02-gaps.json, REPORT.md)
   and update `keywords/tracking.yaml` targets the user confirms (additions
   are a strategy mutation -> create_item kind="strategy" + approval gate).

## explorer
Own-account GAQL only: search_term_view mining (queries with impressions and
no matching target), keyword_view quality scores. State plainly: "Planner
blocked at Explorer tier - apply for Basic (docs/credentials/google-ads-token.md)".

## none (no token)
GSC query mining via the user's GSC connector: 16 months, queries with
impressions > 100 and position 8-30 = the opportunity set. If no GSC either:
offer CSV import.

## csv (always available)
Accept a Keyword Planner UI export: `csv_import.load_planner_csv(path)`.
Auction Insights CSVs: summarize overlap/position trends per competitor.

Output in every tier: REPORT.md with the top 20 opportunities, each carrying
volume (or proxy), difficulty proxy, intent guess, recommended action
(new page | optimize existing | ignore), and the evidence line.
```

- [ ] **Step 4: Write thin `plugin/commands/keywords.md`, run tests, audit, commit**

Run: `python3 -m pytest tests -q` Expected: all pass

```bash
git add -A && git commit -m "feat(hoo): keyword-intel skill with four access tiers + CSV import"
```

### Task 12: Citation tracker, competitor intel, monthly audit, reflector, task board

**Files:**
- Create: `plugin/skills/hoo-citation-tracker/SKILL.md`, `hoo-competitor-intel/SKILL.md`, `hoo-monthly-audit/SKILL.md`, `hoo-reflector/SKILL.md`, `hoo-task-board/SKILL.md`
- Create: thin commands `citations.md`, `competitors.md`, `monthly-audit.md`, `task-board.md`

- [ ] **Step 1: Write `hoo-citation-tracker/SKILL.md`**

```markdown
---
name: hoo-citation-tracker
description: Use to measure AI answer-engine visibility - "are we cited by ChatGPT/Perplexity", "AI share of voice", /organic-os:citations, or the weekly routine's citation step.
---

# AI citation tracking

1. Read profile: keywords.targets (the query set), competitors, site url.
2. For each query (cap 20 per run; rotate through the set across runs), ask the
   available engines. Sources in order of preference: an authorized AI-search
   connector or WebSearch with engine-targeted queries; plain WebSearch
   otherwise. Never scrape engines through automation that violates their ToS.
3. Record per query: engine | our domain mentioned? | cited (linked)? |
   competitors mentioned | answer summary (<=30 words).
4. Metrics: mention rate, citation rate, share of voice vs competitors
   (mentions of us / mentions of anyone tracked).
5. Persist to runs/YYYYMMDD-citations/ + append one signal line with the
   headline movement vs the previous run (diff the last runs/ folder).
6. New citation appearing or disappearing on a money query -> P1 signal.
```

- [ ] **Step 2: Write `hoo-competitor-intel/SKILL.md`**

```markdown
---
name: hoo-competitor-intel
description: Use for competitor content analysis - "what are competitors publishing", "content gaps vs <domain>", /organic-os:competitors, or the biweekly routine.
---

# Competitor intelligence

1. Read profile competitors. For each: fetch sitemap or blog index; diff
   against the previous snapshot in runs/ (first run = baseline, say so).
2. Launch competitive-intel-analyst agent per competitor (parallel, cap 3 per
   run) with the profile path.
3. Synthesize: new pages, topics they cover that we lack (cross-reference our
   sitemap), their apparent keyword focus per new page.
4. Gaps that fit our profile keywords/segments -> create_item
   kind="content-brief" (proposed, gated as always).
5. Persist runs/YYYYMMDD-competitors/ + signals for notable moves.
```

- [ ] **Step 3: Write `hoo-monthly-audit/SKILL.md`**

```markdown
---
name: hoo-monthly-audit
description: Use for the monthly deep audit - "run the monthly audit", /organic-os:monthly-audit, or the scheduled monthly routine.
---

# Monthly deep audit

1. Full sweep via the orchestrator pattern: launch all eight specialists in
   parallel with the profile path.
2. Additionally: content freshness review (pages > 12 months stale that hold
   rankings - freshness is a strong-evidence AEO factor), schema validity,
   internal-link health, tracked-keyword trend over the month, outcomes review
   (which applied changes moved metrics; feed wins/losses to the reflector).
3. Compare with last month's runs/ artifacts; the report leads with deltas.
4. File signals, briefs, and fixes through core contracts; rebuild queue;
   notify per approval channel.
5. Output runs/YYYYMM-monthly/REPORT.md: executive summary in plain language,
   then per-specialist sections, then this month's queued work.
```

- [ ] **Step 4: Write `hoo-reflector/SKILL.md`**

```markdown
---
name: hoo-reflector
description: Use to distill lessons from recent signals and outcomes - "run the reflector", weekly routine step 4, or "what did we learn". Proposes skillbook deltas; the curator merge is gated.
---

# Reflector (weekly) - propose deltas, never write directly

1. Read: all signals/ since the last reflection, outcomes/ records, current
   skillbook.md, the last reflections/ file.
2. Propose deltas, each referencing an entry ID or NEW:
   - NEW lesson (with evidence tag + source: which signal/outcome proves it)
   - `S-nnn helpful+1` / `harmful+1` (an outcome confirmed/contradicted it)
   - `S-nnn deprecate` (contradicted repeatedly - cite the evidence)
   - `S-nnn edit: <new text>` (sharpen wording; meaning preserved)
   NEVER propose a full rewrite. NEVER propose deleting lines.
3. Write reflections/YYYY-Www.md listing every delta + evidence.
4. Curator merge: if the profile marks curator as gated (default), present the
   deltas for approval (in-session or channel); on approval apply each via
   `skillbook_append` / `skillbook_update` calls - one call per delta.
5. Commit "reflection: YYYY-Www" if git.
```

- [ ] **Step 5: Write `hoo-task-board/SKILL.md`**

```markdown
---
name: hoo-task-board
description: Use to view or mirror the work queue - "task board", "show the queue", /organic-os:task-board. Mirrors to Notion when that connector exists; local queue.md is the source of truth.
---

# Task board

1. Rebuild queue (`core.contracts.rebuild_queue`) and show pending items,
   in-flight items (approved/drafted), and recently completed (published/
   measured, last 14 days).
2. If the Notion connector is available and site-profile connectors.notion is
   "available": upsert a page per item into the "organic-os board" database
   (create it on first run: properties Status, Kind, Target, Created, ItemId).
   One-way mirror: repo -> Notion. Approvals never flow back through Notion.
3. Without Notion: print the board and stop. No degradation warnings needed;
   the local board IS the product.
```

- [ ] **Step 6: Write the four thin commands, audit, commit**

```bash
git add -A && git commit -m "feat(hoo): citation tracker, competitor intel, monthly audit, reflector, task board"
```

# Phase 3 - onsite-optimizer module

### Task 13: WordPress client (wp.py)

**Files:**
- Create: `plugin/lib/onsite/__init__.py` (empty), `plugin/lib/onsite/wp.py`
- Test: `tests/test_wp.py`

- [ ] **Step 1: Write failing tests `tests/test_wp.py`** (session injected; no network)

```python
import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import json  # noqa: E402
import pytest  # noqa: E402
from onsite.wp import WPClient  # noqa: E402


class FakeSession:
    def __init__(self):
        self.calls = []
        self.responses = {}
    def request(self, method, url, **kw):
        self.calls.append((method, url, kw.get("json")))
        body = self.responses.get((method, url), {"id": 42, "title": {"raw": "Old"},
                                                  "meta": {"rank_math_title": "Old T"}})
        class R:
            status_code = 200
            def json(self):
                return body
            text = json.dumps(body)
        return R()


def make_client(sess):
    return WPClient("https://play.example/wp-json", "organic-agent", "secret", session=sess)


def test_auth_header_is_basic():
    c = make_client(FakeSession())
    assert c.auth_header().startswith("Basic ")


def test_update_rankmath_posts_meta():
    s = FakeSession(); c = make_client(s)
    c.update_rankmath(42, title="New T", description="New D")
    method, url, payload = s.calls[-1]
    assert method == "POST" and url.endswith("/wp/v2/posts/42")
    assert payload["meta"]["rank_math_title"] == "New T"
    assert payload["meta"]["rank_math_description"] == "New D"


def test_snapshot_then_rollback_restores(tmp_path):
    s = FakeSession(); c = make_client(s)
    snap = c.snapshot(42, fields=["title", "meta"])
    rec = tmp_path / "rollback.json"; rec.write_text(json.dumps(snap))
    c.rollback(json.loads(rec.read_text()))
    method, url, payload = s.calls[-1]
    assert method == "POST" and url.endswith("/wp/v2/posts/42")
    assert payload["title"] == "Old"          # restored raw title
    assert payload["meta"]["rank_math_title"] == "Old T"


def test_create_post_draft_by_default():
    s = FakeSession(); c = make_client(s)
    c.create_post(title="T", content="C", slug="t")
    method, url, payload = s.calls[-1]
    assert payload["status"] == "draft"
```

- [ ] **Step 2: Run, expect failure. Then write `plugin/lib/onsite/wp.py`**

```python
"""WordPress REST client for on-page SEO. Application-password auth.
Session injected for tests; real use builds a stdlib session (no requests dep).

RankMath meta keys must be REST-registered on the site (the bundled
playground/wp-extras/organic-os-bridge.php mu-plugin, or Devora's
rank-math-api-manager). See docs/credentials/wordpress.md.
"""
from __future__ import annotations
import base64
import json
import urllib.request

RANKMATH_KEYS = {"title": "rank_math_title", "description": "rank_math_description",
                 "canonical": "rank_math_canonical_url",
                 "focus_keyword": "rank_math_focus_keyword",
                 "schema_jsonld": "agent_jsonld"}


class StdlibSession:
    def request(self, method, url, headers=None, json_body=None, **kw):
        data = json.dumps(json_body).encode() if json_body is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers=headers or {})
        if data:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode()
            class R:
                status_code = r.status
                text = body
                def json(self):
                    return json.loads(body)
            return R()


class WPClient:
    def __init__(self, endpoint: str, username: str, app_password: str, session=None):
        self.endpoint = endpoint.rstrip("/")
        self._auth = base64.b64encode(f"{username}:{app_password}".encode()).decode()
        self.session = session or StdlibSession()

    def auth_header(self) -> str:
        return f"Basic {self._auth}"

    def _call(self, method: str, path: str, payload=None):
        url = f"{self.endpoint}{path}"
        kw = {"headers": {"Authorization": self.auth_header()}}
        if payload is not None:
            kw["json"] = payload           # FakeSession reads kw['json']
            kw["json_body"] = payload      # StdlibSession reads kw['json_body']
        r = self.session.request(method, url, **kw)
        if getattr(r, "status_code", 200) >= 300:
            raise RuntimeError(f"WP {method} {path} -> {r.status_code}: {r.text[:200]}")
        return r.json()

    # -- reads --
    def get_post(self, post_id: int) -> dict:
        return self._call("GET", f"/wp/v2/posts/{post_id}?context=edit")

    def get_head(self, page_url: str) -> dict:
        """RankMath Headless getHead: the rendered head for verification."""
        return self._call("GET", f"/rankmath/v1/getHead?url={page_url}")

    # -- writes (callers MUST hold an approved item; enforced in skills) --
    def update_post(self, post_id: int, **fields) -> dict:
        return self._call("POST", f"/wp/v2/posts/{post_id}", fields)

    def update_rankmath(self, post_id: int, **seo) -> dict:
        meta = {RANKMATH_KEYS[k]: v for k, v in seo.items() if k in RANKMATH_KEYS}
        return self._call("POST", f"/wp/v2/posts/{post_id}", {"meta": meta})

    def create_post(self, title: str, content: str, slug: str,
                    status: str = "draft", excerpt: str = "") -> dict:
        return self._call("POST", "/wp/v2/posts",
                          {"title": title, "content": content, "slug": slug,
                           "status": status, "excerpt": excerpt})

    # -- rollback --
    def snapshot(self, post_id: int, fields) -> dict:
        post = self.get_post(post_id)
        snap = {"post_id": post_id}
        for f in fields:
            if f == "title":
                snap["title"] = post.get("title", {}).get("raw", "")
            elif f == "meta":
                snap["meta"] = {k: post.get("meta", {}).get(k, "")
                                for k in RANKMATH_KEYS.values()}
            elif f == "content":
                snap["content"] = post.get("content", {}).get("raw", "")
        return snap

    def rollback(self, snap: dict) -> dict:
        payload = {k: v for k, v in snap.items() if k != "post_id"}
        return self._call("POST", f"/wp/v2/posts/{snap['post_id']}", payload)
```

- [ ] **Step 3: Run tests, audit, commit**

Run: `python3 -m pytest tests/test_wp.py -q` Expected: 4 passed

```bash
git add -A && git commit -m "feat(onsite): WP REST client - rankmath meta, snapshots, rollback, getHead verify"
```

### Task 14: The bridge mu-plugin + WordPress credential doc

**Files:**
- Create: `playground/wp-extras/organic-os-bridge.php`, `docs/credentials/wordpress.md`

- [ ] **Step 1: Write `playground/wp-extras/organic-os-bridge.php`**

```php
<?php
/**
 * Plugin Name: organic-os bridge
 * Description: Registers RankMath SEO meta + agent_jsonld for the REST API so
 * organic-os can read/write them with an Application Password, and renders
 * agent_jsonld into wp_head. Install as an mu-plugin (wp-content/mu-plugins/).
 * Version: 0.1.0
 * License: MIT
 */

add_action('init', function () {
    $keys = ['rank_math_title', 'rank_math_description',
             'rank_math_canonical_url', 'rank_math_focus_keyword', 'agent_jsonld'];
    foreach ($keys as $key) {
        register_post_meta('', $key, [
            'show_in_rest'  => true,
            'single'        => true,
            'type'          => 'string',
            'auth_callback' => function ($allowed, $meta_key, $post_id) {
                return current_user_can('edit_post', $post_id);
            },
        ]);
    }
});

add_action('wp_head', function () {
    if (!is_singular()) return;
    $jsonld = get_post_meta(get_the_ID(), 'agent_jsonld', true);
    if (!$jsonld) return;
    json_decode($jsonld);
    if (json_last_error() !== JSON_ERROR_NONE) return; // never render invalid JSON
    echo '<script type="application/ld+json">' . $jsonld . '</script>' . "\n";
});
```

- [ ] **Step 2: Write `docs/credentials/wordpress.md`** covering, in order: (1) create a dedicated Editor user (`organic-agent`), never an Administrator; (2) Users -> Profile -> Application Passwords -> new password, store via the `~/.config/organic-os/<site>.env` pattern (`WP_APP_PASSWORD=...`, chmod 600); (3) install RankMath free; (4) install the bridge - either copy `playground/wp-extras/organic-os-bridge.php` to `wp-content/mu-plugins/` (`wp eval` one-liner or SFTP) or install Devora's rank-math-api-manager plugin; (5) enable RankMath Headless CMS Support for `getHead`; (6) verify with the exact curl:
`curl -u 'organic-agent:APP_PASSWORD' https://SITE/wp-json/wp/v2/posts?per_page=1&context=edit` (expect JSON including a `meta` object with `rank_math_title`).

- [ ] **Step 3: Audit + commit**

```bash
git add -A && git commit -m "feat(onsite): bridge mu-plugin + WordPress credential guide"
```

### Task 15: Onsite skills (audit, propose, apply, publish, measure)

**Files:**
- Create: `plugin/skills/onsite-audit/SKILL.md`, `onsite-propose/SKILL.md`, `onsite-apply/SKILL.md`, `onsite-publish/SKILL.md`, `onsite-measure/SKILL.md`
- Create: thin commands `onsite-audit.md`, `propose.md`, `apply.md`, `publish.md`, `measure.md`

- [ ] **Step 1: Write `onsite-audit/SKILL.md`**

```markdown
---
name: onsite-audit
description: Use to audit on-page SEO for a URL or a whole site section - "audit this page", "on-page check", /organic-os:onsite-audit. Read-only; needs no credentials for public checks.
---

# On-page audit (read-only)

1. Read profile if a brain repo exists (optional - this skill also works bare).
2. Public checks per URL (WebFetch): title (length, keyword presence),
   meta description, H1 count, heading structure, canonical, robots meta,
   image alts, internal links out, JSON-LD present/valid, answer-capsule
   presence in the first 200 words, server-rendered content check.
3. If WordPress credentials exist: pull the post via wp.py `get_post` +
   `get_head` for the rendered truth; list RankMath field values.
4. Launch technical-seo-auditor for site-level context when auditing > 3 URLs.
5. Output: per-URL scorecard table + prioritized issue list. File signals for
   P0/P1 issues if a brain repo exists. Propose nothing here; that is
   onsite-propose's job.
```

- [ ] **Step 2: Write `onsite-propose/SKILL.md`**

```markdown
---
name: onsite-propose
description: Use to turn audit findings or signals into concrete gated change proposals - "propose fixes for /pricing", /organic-os:propose.
---

# Propose on-page changes (creates gated items; applies nothing)

1. Input: audit findings, a signal reference, or a user request naming URLs.
2. For each change, draft the exact after-state: new title (<= 60 chars),
   new meta description (<= 155 chars), canonical, focus keyword, schema
   JSON-LD payload, or a content edit (quote the exact before/after text).
3. One proposal item per page: `create_item(kind="onpage-fix", target=<url>,
   body=<before/after table + rationale + expected effect + falsifiability>)`.
4. Rebuild queue. Notify per the profile approval channel:
   - in-session: present now with AskUserQuestion (approve/reject each)
   - telegram: send via core.telegram `send_item` (token from env file)
   - pr-merge: commit the proposal file on a branch, open a PR (gh pr create)
   - slack/email: post/send a summary via the available connector; approval
     happens in-session or by channel reply read at the next run
5. Record any in-session decisions immediately via `record_decision`.
```

- [ ] **Step 3: Write `onsite-apply/SKILL.md`**

```markdown
---
name: onsite-apply
description: Use to execute APPROVED on-page proposals - "apply the approved fixes", /organic-os:apply, or a routine's apply step. Refuses anything not approved.
---

# Apply approved changes (the gate lives here)

1. Read profile + env file. Poll the channel first if telegram
   (`poll_decisions` -> `record_decision` for each).
2. List approved onpage-fix items. For each:
   a. `require_approved(path)` - this raises on anything not approved. Never
      catch that error to proceed; report it and skip.
   b. `snapshot()` the post (title + meta + content if the proposal touches it)
      -> save to `outcomes/<item-id>-rollback.json` in the brain repo.
   c. Apply via wp.py: `update_rankmath` / `update_post` per the proposal body.
   d. Verify: `get_head(target_url)` - assert the new title/description appear
      in the rendered head. On mismatch: `rollback()` immediately, set item
      back by filing a new signal "apply-verify failed", and alert.
   e. `set_status(path, "applied", actor="agent")`; write an outcome record
      `outcomes/<item-id>.md`: what changed, when, rollback file, measurement
      due dates (+7d, +28d).
3. Commit + push the brain repo if git. Summarize: applied / skipped / failed.

HARD RULES: no snapshot -> no write. Verify after every write. A failed verify
means rollback, never retry-and-hope.
```

- [ ] **Step 4: Write `onsite-publish/SKILL.md`**

```markdown
---
name: onsite-publish
description: Use to publish an APPROVED, drafted content item to WordPress - "publish the draft", /organic-os:publish. Refuses unapproved items.
---

# Publish content (gated)

1. Input: a brief item with status "drafted" whose draft file sits next to it
   (same folder, <brief-name>.draft.md produced by ce-produce).
2. The brief must carry an approval (check meta.approvals non-empty) AND the
   profile user must confirm the final draft in-session or via channel.
3. Create the post via wp.py `create_post` (status draft by default; status
   "publish" only when site-profile sets publishing: direct), then
   `update_rankmath` with title/description/focus keyword from the draft's
   frontmatter, and `agent_jsonld` if the draft includes schema.
4. Verify with `get_head`; on success `set_status(brief, "published")` and
   write the outcome record with measurement dates; on failure delete the
   draft post and report.
5. If a Canva image brief exists next to the draft (from ce-image) and the
   connector is available, upload the exported image as featured media first.
```

- [ ] **Step 5: Write `onsite-measure/SKILL.md`**

```markdown
---
name: onsite-measure
description: Use to measure applied/published changes at day 7 and day 28 - "measure outcomes", /organic-os:measure, or the daily routine's follow-up step.
---

# Measure outcomes (closing the loop)

1. Scan outcomes/ for records with a due measurement date <= today that lack
   that measurement.
2. Per record: pull GSC for the target URL - clicks/impressions/CTR/position
   for the 7 (or 28) days after the change vs the same window before.
   No GSC connector: record "unmeasured (no GSC)" honestly.
3. Append the delta to the outcome record + one signal line
   ("outcome <item-id>: position 8.2 -> 5.9 after title rewrite").
4. Wins and losses BOTH matter: the reflector reads outcomes to score
   skillbook entries helpful/harmful. Set status "measured" at day-28.
```

- [ ] **Step 6: Write the five thin commands, audit, commit**

```bash
git add -A && git commit -m "feat(onsite): audit/propose/apply/publish/measure skills - gate enforced in apply path"
```

# Phase 4 - content-engine module

### Task 16: Content pipeline agents + produce/image skills

**Files:**
- Create: `plugin/agents/ce-researcher.md`, `ce-writer.md`, `ce-brand-auditor.md`, `ce-seo-aeo.md`, `ce-qa.md`, `ce-editor.md`
- Create: `plugin/skills/ce-produce/SKILL.md`, `plugin/skills/ce-image/SKILL.md`
- Create: thin commands `produce.md`, `image.md`

- [ ] **Step 1: Write the six pipeline agents.** Same template as Task 8 (frontmatter name/description/tools + Method + Output contract). Content per agent:

| Agent | tools | Role (write 4-6 method steps + output contract from this) |
|---|---|---|
| ce-researcher | WebSearch, WebFetch, Read | From a brief: gather 5-8 authoritative live sources (fetch each, verify it loads and says what is claimed), extract statistics with exact citations, map the query fan-out (subquestions an AI engine would ask). Output: research pack with quotes + URLs + a claims-you-may-make list. Never fabricate a statistic or URL |
| ce-writer | Read | From brief + research pack + site-profile brand rules: draft with answer capsule (40-60 words) up top, statistics and quotable lines woven in, extractable structure (H2 question headings, lists, one comparison table where natural), first person if the profile voice says so. Output: complete draft in markdown with frontmatter (title, slug, meta description, focus keyword) |
| ce-brand-auditor | Read | Check draft against site-profile brand: voice rules, banned phrases, rulebook, no em-dashes, no exclamation marks, no self-labels. Output: pass/fail + line-referenced fixes (apply them directly, list what changed) |
| ce-seo-aeo | Read, WebFetch | Title <= 60 chars with keyword, meta <= 155, capsule present, heading hierarchy, internal link suggestions from the site's sitemap, schema JSON-LD suggestion (Article + FAQ only if real questions exist). Evidence-honest: no keyword stuffing (does nothing per the GEO paper). Output: optimized draft + agent_jsonld payload |
| ce-qa | Read, WebFetch | Verify every claim against the research pack; re-fetch 2 random cited URLs to confirm live + accurate; check statistics match sources exactly; flag anything unverifiable for removal. Output: verified draft + QA log |
| ce-editor | Read | Final read as editor-in-chief: cut 10% (flab), verify capsule answers the target query, headline options (3), publish-readiness verdict. Output: final draft + verdict + what changed |

- [ ] **Step 2: Write `plugin/skills/ce-produce/SKILL.md`**

```markdown
---
name: ce-produce
description: Use to produce a publish-ready draft from an approved content brief - "draft the approved brief", "write this post", /organic-os:produce. Runs the six-stage pipeline.
---

# Content pipeline

1. Input: an APPROVED brief item (require_approved - drafting counts as work
   the user pays attention for, so briefs are gated before drafting).
   A user may also hand a manual brief; then confirm scope in-session first.
2. Stages, sequential agents (each receives profile path + prior artifacts):
   ce-researcher -> ce-writer -> ce-brand-auditor -> ce-seo-aeo -> ce-qa ->
   ce-editor.
3. Save the final draft as <brief-file>.draft.md next to the brief (frontmatter:
   title, slug, meta_description, focus_keyword, schema block). Save the
   research pack + QA log under runs/YYYYMMDD-produce-<slug>/.
4. `set_status(brief, "drafted", actor="agent")`. Then invoke ce-image for the
   featured-image step. Publishing is onsite-publish's job (separately gated).
5. Rules from the profile override everything: voice, banned phrases, rulebook.
   House defaults if profile is silent: answer capsule up top, no em-dashes,
   active voice, statistics cited inline with live links.
```

- [ ] **Step 3: Write `plugin/skills/ce-image/SKILL.md`**

```markdown
---
name: ce-image
description: Use to create the featured image / social card for a drafted post - "make the featured image", /organic-os:image, or ce-produce step 4.
---

# Featured image

1. Input: a draft file. Derive: post title, one visual concept (no text-heavy
   design; title as overlay text max 8 words), site brand colors if the
   profile records them.
2. If the Canva connector is available: generate a 1200x630 design with the
   title text + brand colors, export as PNG, save next to the draft as
   <slug>-featured.png. Present it; regenerate on request (max 3 rounds).
3. Without Canva: write <slug>-image-brief.md next to the draft - dimensions
   1200x630, concept description, exact overlay text, alt text - so the user
   can produce it in any tool. State plainly that no image was generated.
4. Always write the alt text into the draft frontmatter (alt: ...).
```

- [ ] **Step 4: Write the two thin commands, audit, commit**

```bash
git add -A && git commit -m "feat(ce): six-stage content pipeline agents + produce/image skills"
```

# Phase 5 - docs, playground reference, publish

### Task 17: Documentation set

**Files:**
- Create: `docs/getting-started.md`, `docs/credentials/google-ads-token.md`, `docs/credentials/gsc-ga4.md`, `docs/approval-channels.md`, `docs/routines.md`, `docs/evidence.md`, `docs/site-repo-contract.md`

- [ ] **Step 1: Write `docs/getting-started.md`**: install (the two `/plugin` commands), run `/organic-os:setup`, the zero-credential quickstart (onsite-audit on any public URL + orchestrator in analysis-only mode), then the upgrade ladder (add GSC/GA4 -> add WordPress -> add Google Ads -> add a channel -> schedule routines), each rung one paragraph linking its doc.

- [ ] **Step 2: Write `docs/credentials/google-ads-token.md`** - the verified 2026 guide, exactly this outline with each step expanded to 2-5 sentences:
1. Create/have a Google Ads Manager account (the token lives there; free, no ads needed)
2. Admin > API Center > accept ToS > token issued at Test Account access (Google may auto-upgrade to Explorer)
3. Create a Google Cloud project; enable "Google Ads API"
4. OAuth consent screen: External, yourself as test user, scope `.../auth/adwords`; publish the app so refresh tokens do not expire every 7 days
5. Credentials > OAuth client ID > Desktop app (loopback flow; OOB is dead)
6. Generate the refresh token with google-ads-python's `generate_user_credentials.py`
7. Store credentials: `~/.config/organic-os/<site>.env` with the five `GOOGLE_ADS_*` vars, chmod 600
8. Verify at any tier: ListAccessibleCustomers + one GAQL query
9. Apply for Basic access (required for keyword planning; Explorer blocks planner services). Nominal ~5 business days; 2026 backlog acknowledged by Google, expect longer. Strengthen the application: advertiser verification, specific use-case text ("keyword research and reporting for my own accounts")
10. What each tier unlocks (table: Test/Explorer/Basic/Standard vs planner, reporting, quotas)
Close with the fallback note: no token still gets GSC mining + CSV import.

- [ ] **Step 3: Write `docs/credentials/gsc-ga4.md`**: the two supported paths - (a) claude.ai connectors for Search Console and Analytics (authorize in connector settings; available in Cowork, claude.ai, and scheduled runs), (b) any GSC/GA4 MCP server the user already runs in Claude Code. organic-os calls whichever tools exist and states which it found.

- [ ] **Step 4: Write `docs/approval-channels.md`**: the protocol (proposals are files; status lifecycle; nothing mutates without an approval record), then per-channel setup: in-session (nothing to set up), telegram (BotFather token 2-minute walkthrough, chat id via getUpdates, env vars, the approve/reject grammar), pr-merge (brain repo on GitHub; merging the proposal PR approves it), slack/email (notify-only via connectors; approval happens in-session or next-run reply). State explicitly: no channel is privileged; the installer chooses.

- [ ] **Step 5: Write `docs/routines.md`**: the four runtimes table from the spec (§6) with setup instructions each: claude-scheduled (create a scheduled task per cadence with the exact prompt "Open <brain repo>. Run /organic-os:daily" etc.), local (crontab lines calling `claude -p`), ci (a complete GitHub Actions workflow YAML with `anthropics/claude-code-action` or `claude -p` + `ANTHROPIC_API_KEY` secret, checkout of the brain repo, commit+push step), manual. Include the honest cost paragraph per runtime.

- [ ] **Step 6: Write `docs/evidence.md`** - the ranked evidence table: STRONG: server-rendering (Vercel/MERJ crawler study), statistics/quotes/cited sources (Princeton GEO, KDD 2024), Bing indexing for ChatGPT, freshness (< 12 months, ~3x Perplexity citations), extractable structure. MODERATE: community/Reddit presence, query fan-out coverage, third-party listings for entity queries. WEAK/CONTRADICTED: schema markup for AI citations (Ahrefs 1,885-page causal test: no uplift; still worth shipping for Google rich results), llms.txt (Google: not used; Ahrefs 137k-site study: 97% zero bot hits; shipped as optional hedge only). Each row: claim, evidence, source link, what organic-os does about it.

- [ ] **Step 7: Write `docs/site-repo-contract.md`**: the brain layout tree (spec §4), the item frontmatter schema and lifecycle diagram, skillbook line format, the append-only + curator rules, and "any tool may READ these files; only lib/core WRITES them".

- [ ] **Step 8: Audit + commit**

```bash
git add -A && git commit -m "docs: getting started, credentials, channels, routines, evidence, contract"
```

### Task 18: README, SECURITY, CHANGELOG

**Files:**
- Modify: `README.md` (replace stub), `CHANGELOG.md`
- Create: `SECURITY.md`

- [ ] **Step 1: Write the full `README.md`** with exactly these sections:
1. **organic-os** - one-paragraph pitch: an agentic organic-growth operating system for Claude; the loop is the product: observe -> decide -> approve -> apply -> verify -> learn.
2. **Why another SEO thing** - point-in-time audit tools exist and are good (credit claude-seo by name with link, 11.7k stars). organic-os is the layer that runs every day and compounds: signals, gated execution on your WordPress site, outcome measurement, and a skillbook your site earns over time.
3. **What you get** - the three modules table + the loop diagram (ASCII, from spec §3).
4. **Install** - the two commands; works on Claude Code CLI and Cowork; nothing to host.
5. **Quickstart in 10 minutes** - zero-credential path: setup interview (analysis mode) -> `/organic-os:onsite-audit https://yoursite.com` -> orchestrator sweep -> see your first briefs in the queue.
6. **Credentials (all optional, all yours)** - the upgrade ladder linking each docs/credentials page; the promise: no secrets in any repo, no telemetry, no third-party calls you did not configure.
7. **Human gates** - analysis is free, mutation is gated, channel is your choice; link docs/approval-channels.md.
8. **Routines** - the four runtimes in three sentences; link docs/routines.md.
9. **Evidence honesty** - two sentences + link docs/evidence.md: we label every tactic by evidence strength and we tell you when a popular tactic (llms.txt, schema-for-AI-citations) is weakly supported.
10. **Credits and prior art** - AgriciDaniel/claude-seo, seranking/seo-skills, WordPress/mcp-adapter, Automattic mcp-wordpress-remote, Devora rank-math-api-manager, mcp-gsc, DataForSEO MCP, ACE paper, Reflexion, Voyager, Dynamic Cheatsheet, MADR - one line + link each.
11. **License** - MIT.

- [ ] **Step 2: Write `SECURITY.md`**: what the plugin touches (your brain repo, your WordPress via your app password, APIs you configured), what it never does (scrape engines, phone home, store secrets in repos, mutate without an approval record), the env-file convention, how to report an issue (GitHub issues).

- [ ] **Step 3: Update `CHANGELOG.md`**: `## [0.1.0] - 2026-07-18` with a bullet per module.

- [ ] **Step 4: Audit + commit**

```bash
git add -A && git commit -m "docs: README, SECURITY, changelog for v0.1.0"
```

### Task 19: Playground reference files

**Files:**
- Create: `playground/docker-compose.yml`, `playground/uploads.ini`, `playground/Caddyfile.snippet`, `playground/RUNBOOK.md`

- [ ] **Step 1: Write `playground/docker-compose.yml`** (the parallel WordPress session deploys this; keep in sync with spec §10):

```yaml
services:
  db:
    image: mariadb:11.4
    restart: unless-stopped
    environment:
      MARIADB_DATABASE: wordpress
      MARIADB_USER: wordpress
      MARIADB_PASSWORD: ${DB_PASSWORD}
      MARIADB_RANDOM_ROOT_PASSWORD: "1"
    command: >
      --innodb-buffer-pool-size=256M
      --performance-schema=OFF
      --max-connections=30
    volumes: [db_data:/var/lib/mysql]
    mem_limit: 512m

  wordpress:
    image: wordpress:php8.3-apache
    restart: unless-stopped
    depends_on: [db]
    ports:
      - "127.0.0.1:8081:80"
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: ${DB_PASSWORD}
      WORDPRESS_CONFIG_EXTRA: |
        define('WP_HOME', 'https://playground.shivaatripathi.com');
        define('WP_SITEURL', 'https://playground.shivaatripathi.com');
        define('DISABLE_WP_CRON', true);
        define('WP_MEMORY_LIMIT', '256M');
    volumes:
      - wp_data:/var/www/html
      - ./uploads.ini:/usr/local/etc/php/conf.d/uploads.ini:ro
      - ./wp-extras:/var/www/html/wp-content/mu-plugins:ro
    mem_limit: 768m

  wp-cli:
    image: wordpress:cli-php8.3
    user: "33:33"
    depends_on: [wordpress, db]
    volumes: [wp_data:/var/www/html]
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: ${DB_PASSWORD}
    entrypoint: ["wp"]
    profiles: ["cli"]

volumes:
  db_data:
  wp_data:
```

- [ ] **Step 2: Write `playground/uploads.ini`**

```ini
upload_max_filesize = 64M
post_max_size = 64M
memory_limit = 256M
```

- [ ] **Step 3: Write `playground/Caddyfile.snippet`**

```
playground.shivaatripathi.com {
    reverse_proxy 127.0.0.1:8081
}
```

- [ ] **Step 4: Write `playground/RUNBOOK.md`**: deploy steps for the parallel session (DNS A record proxied -> copy playground/ to /opt/playground on the host -> `DB_PASSWORD=<generated> docker compose up -d` -> add Caddy block + reload -> `docker compose run --rm wp-cli core install ...` -> install RankMath + enable Headless support -> create organic-agent Editor + app password -> seed 4-6 posts -> host crontab `*/15 * * * * cd /opt/playground && docker compose run --rm wp-cli cron event run --due-now` -> GSC verify + sitemap submit + GA4 property), and the verification checklist (https loads, REST auth works with the curl from docs/credentials/wordpress.md, getHead returns, Site Health loopback note).

- [ ] **Step 5: Audit + commit**

```bash
git add -A && git commit -m "feat: playground reference deployment (compose, caddy, runbook)"
```

### Task 20: End-to-end dry run

**Files:**
- Create: `tests/test_e2e_loop.py`

- [ ] **Step 1: Write `tests/test_e2e_loop.py`** - the whole loop against a temp brain and a fake WP session, no network:

```python
import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import pytest  # noqa: E402
from core.init_site_repo import init_site_repo  # noqa: E402
from core import contracts as C, approval as A  # noqa: E402
from onsite.wp import WPClient  # noqa: E402
from tests.test_wp import FakeSession  # noqa: E402


def test_signal_to_measured_outcome(tmp_path):
    root = init_site_repo(tmp_path / "brain", "https://play.example", "Play")
    # observe
    C.append_signal(root, "position 9 -> 14 on /pricing", date="2026-07-18")
    # decide
    p = C.create_item(root, "onpage-fix", "pricing-title", "Rewrite pricing title",
                      "before: X / after: Y", "https://play.example/pricing", "signal")
    C.rebuild_queue(root)
    assert "Rewrite pricing title" in (root / "approvals" / "queue.md").read_text()
    # gate blocks before approval
    with pytest.raises(C.ContractError):
        C.require_approved(p)
    # approve
    A.record_decision(root, C.load_item(p)["meta"]["id"], "approved", "human", "in-session")
    # apply (with snapshot) + verify happens in the skill; here: client-level
    wp = WPClient("https://play.example/wp-json", "agent", "pw", session=FakeSession())
    snap = wp.snapshot(42, ["title", "meta"])
    assert snap["post_id"] == 42
    wp.update_rankmath(42, title="Y")
    C.set_status(p, "applied", actor="agent")
    # measure
    C.set_status(p, "measured", actor="agent")
    assert C.load_item(p)["meta"]["status"] == "measured"
    # learn
    sid = C.skillbook_append(root, "Title rewrites recover striking-distance drops",
                             evidence="anecdotal", source=C.load_item(p)["meta"]["id"])
    C.skillbook_update(root, sid, helpful=1)
    assert "helpful: 1" in (root / "skillbook.md").read_text()
```

- [ ] **Step 2: Run the whole suite + audit**

Run: `python3 -m pytest tests -q` Expected: all pass (13+ tests)
Run: `./scripts/audit.sh` Expected: `audit: clean`

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "test: end-to-end loop - signal to measured outcome to skillbook"
```

### Task 21: Publish to GitHub

- [ ] **Step 1: Final review pass**: `git log --oneline` sanity; `./scripts/audit.sh`; read README top to bottom once for tone (no banned phrases, no em-dashes, credits present).

- [ ] **Step 2: Create the repo and push** (public - confirm with Shivaa in-session immediately before this step):

Run: `gh repo create shalintripathi/organic-os --public --source . --push`
Expected: repo URL printed.

- [ ] **Step 3: Tag**

```bash
git tag v0.1.0 && git push --tags
```

- [ ] **Step 4: Install test from a clean environment**: in a fresh Claude Code session (or after `/plugin marketplace remove organic-os` locally): `/plugin marketplace add shalintripathi/organic-os` then `/plugin install organic-os@organic-os`; verify `/organic-os:setup` and `/organic-os:onsite-audit` appear and the setup skill loads. Record the result in CHANGELOG under 0.1.0.

# Phase 6 - Shivaa's instance (after publish; WordPress connection when the parallel session delivers)

### Task 22: Brain repo for the playground site

- [ ] Run `/organic-os:setup` for real: brain repo `organic-hq-playground` (private GitHub repo), profile filled (site url https://playground.shivaatripathi.com, brand "organic-os playground", competitors: 2-3 marketing-blog domains as demo, target keywords: 5-10 B2B SaaS marketing queries, operator notes from Shivaa), approval channel telegram + pr-merge, runtime claude-scheduled, brain mode git.
- [ ] Telegram: create the bot with BotFather, store token + chat id per docs/approval-channels.md, send a test proposal end to end.
- [ ] When the parallel session delivers WordPress credentials: add endpoint + username to the profile, store the app password env file, run the curl verification from docs/credentials/wordpress.md.

### Task 23: Notion dashboard

- [ ] With the Notion connector authorized: run `/organic-os:task-board` against the brain repo; let it create the "organic-os board" database; verify items mirror. Add a "Head of Organic HQ" page with links to the brain repo, the playground, and the board.

### Task 24: Register routines

- [ ] Create claude.ai scheduled tasks per docs/routines.md: daily (signal pull) 07:00 IST, weekly (check + reflect) Monday 08:00 IST, monthly audit 1st 09:00 IST. Each task prompt: "Clone/open <brain repo>. Run /organic-os:<skill>. Commit and push. Notify per the profile channel."
- [ ] Watch the first daily run; fix whatever breaks; record lessons as ADR-0007 if architectural.

---

## Plan self-review (done at write time)

- **Spec coverage:** §2 packaging -> T1; §2 boundaries -> T2 audit + lib/core rule; §4 brain -> T4/T5; §5 gates -> T5 require_approved + T6 adapters + T15 apply; §6 runtimes -> T17 routines doc + T24; §7 module -> T7-T12; §8 -> T13-T15; §9 -> T16; §10 -> T19 (reference only, parallel session deploys); §11 -> T12 task-board + T23; §12 -> audit.sh, env-file convention, SECURITY.md; §13 -> T18/T21; §15 acceptance -> T20/T21 + gates throughout. Playground deployment itself: deliberately out of scope (parallel session).
- **Placeholder scan:** clean; agent/doc tables give complete per-file content requirements with the template fully worked once.
- **Type consistency:** contracts API (`create_item`, `load_item`, `set_status`, `require_approved`, `skillbook_append`, `skillbook_update`, `rebuild_queue`, `append_signal`) used identically in T5, T6, T9, T11, T12, T15, T16, T20. WPClient methods (`update_rankmath`, `snapshot`, `rollback`, `get_head`, `create_post`) consistent across T13, T15, T20. FakeSession reused via import in T20.




