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
