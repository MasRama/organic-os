"""Cross-site registry: which sites has this operator onboarded, which is active.

Lives outside any brain repo at ~/.config/organic-os/sites.yaml (never committed,
never part of a site's git history). Config is editable here; a site's memory
(signals/decisions/reflections/skillbook inside its brain repo) is not touched
by this module.
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

DEFAULT = Path.home() / ".config" / "organic-os" / "sites.yaml"


def _slugify(url: str) -> str:
    host = urlparse(url if "://" in url else f"//{url}").hostname or url
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    slug = re.sub(r"[^a-z0-9]+", "-", host).strip("-")
    return slug


def load(path=DEFAULT) -> dict:
    path = Path(path)
    if not path.exists():
        return {"active": None, "sites": {}}
    data = yaml.safe_load(path.read_text()) or {}
    return {"active": data.get("active"), "sites": data.get("sites") or {}}


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False))
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def register(url: str, name: str, brain, path=DEFAULT) -> str:
    path = Path(path)
    data = load(path)
    slug = _slugify(url)
    data["sites"][slug] = {"url": url, "name": name, "brain": str(brain)}
    data["active"] = slug
    _atomic_write(path, data)
    return slug


def set_active(slug: str, path=DEFAULT) -> None:
    path = Path(path)
    data = load(path)
    if slug not in data["sites"]:
        known = sorted(data["sites"]) or ["(none registered)"]
        raise ValueError(f"unknown site {slug!r}; known sites: {', '.join(known)}")
    data["active"] = slug
    _atomic_write(path, data)


def get_active(path=DEFAULT) -> dict | None:
    data = load(path)
    slug = data.get("active")
    if not slug or slug not in data["sites"]:
        return None
    return {"slug": slug, **data["sites"][slug]}
