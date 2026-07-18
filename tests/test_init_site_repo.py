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
