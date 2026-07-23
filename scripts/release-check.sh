#!/usr/bin/env bash
# organic-os pre-release check: is there plugin code past the last tag that
# ships without a version bump? A tagged-but-unbumped commit is invisible to
# the plugin updater - it downloads the same version string and the running
# install never advances (see plugin/docs/updating.md). This is the exact gap
# that let a tested feature sit on main unreleased.
#
# MAINTAINER-run and advisory. It is NOT wired into the PR CI gate on purpose:
# a contributor's feature branch is expected to sit past the last tag without a
# bump, so gating PRs on this would fight normal contribution. Run it yourself
# before cutting a release. Assumes `git fetch --tags` has already run.
#
# Usage: ./scripts/release-check.sh   (exit 0 = OK, exit 1 = needs a bump)
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
say() { printf '%s\n' "$*"; }

# The most recent version tag reachable from HEAD.
tag=$(git describe --tags --abbrev=0 --match 'v[0-9]*' 2>/dev/null || true)
if [ -z "$tag" ]; then
  say "release-check: OK - no version tag found, nothing to compare against."
  exit 0
fi

# Commits after the tag? If HEAD is the tag itself, there is nothing to ship.
ahead=$(git rev-list "$tag"..HEAD --count 2>/dev/null || echo 0)
if [ "$ahead" -eq 0 ]; then
  say "release-check: OK - HEAD is at $tag, no commits past the last tag."
  exit 0
fi

# Did any plugin code change since the tag? Docs-only or scripts-only work past
# a tag does not need a plugin version bump to reach the updater.
plugin_changed=$(git diff --name-only "$tag"..HEAD -- plugin/ 2>/dev/null || true)
if [ -z "$plugin_changed" ]; then
  say "release-check: OK - $ahead commit(s) past $tag, but nothing under plugin/ changed."
  exit 0
fi

# The version the tag represents, and the version plugin.json declares now.
tag_version="${tag#v}"
version=$(python3 -c "import json;print(json.load(open('plugin/.claude-plugin/plugin.json'))['version'])" 2>/dev/null || true)
if [ -z "$version" ]; then
  say "FAIL: could not read version from plugin/.claude-plugin/plugin.json."
  exit 1
fi

if [ "$version" = "$tag_version" ]; then
  say "FAIL: plugin code changed since $tag but the version is still $version - bump before releasing so the updater can see it."
  say ""
  say "plugin/ files changed since $tag:"
  say "$plugin_changed" | sed 's/^/  /'
  say ""
  say "Fix: bump \"version\" in plugin/.claude-plugin/plugin.json and"
  say ".claude-plugin/marketplace.json, add a CHANGELOG entry, then tag."
  exit 1
fi

say "release-check: OK - plugin code changed since $tag and the version moved to $version."
exit 0
