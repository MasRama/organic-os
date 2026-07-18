"""Git-static CMS adapter: content files in a local clone of a site repo.

Adapter two of the CmsAdapter contract (onsite/cms.py). Targets static
sites built from a git repo (Astro, Next, Hugo, Jekyll and similar) where
content is markdown/MDX files with YAML frontmatter.

The adapter operates on a LOCAL CLONE path. The runtime clones or pulls
the site repo; this class only reads and writes files under it and
returns structured results. It never shells out to git - branching,
committing, pushing, and PR creation belong to the skill layer
(onsite-apply / onsite-publish), which is also where the approval gates
(core.contracts.require_approved / require_approval_lineage) run BEFORE
any write lands here. Publishing is a human's merge plus the site's own
deploy: capabilities() declares needs_human: ["merge-pr", "deploy"], and
rendered_head_verify is False - a static site verifies post-deploy
against the live URL, never through this adapter.

Frontmatter conventions, overridable per site via the profile's
cms: {fields: {...}} mapping (generic key -> frontmatter key):

    title -> title            description -> description
    canonical -> canonical    schema_jsonld -> jsonld
    draft flag -> draft       slug override -> slug

`jsonld` holds a raw JSON-LD string. The adapter only manages the
frontmatter field; the site's layout must render it into the page head.
Status maps to the draft flag: status "draft" writes `draft: true`,
anything else writes `draft: false`. update_post never renames a file;
writing the slug field overrides the URL where the framework supports it.
"""
from __future__ import annotations
import re
from pathlib import Path

import yaml

from core.contracts import _atomic_write
from .cms import CmsAdapter

DEFAULT_FIELDS = {"title": "title", "description": "description",
                  "canonical": "canonical", "schema_jsonld": "jsonld",
                  "draft": "draft", "slug": "slug"}
# The generic SEO keys update_seo_meta maps; anything else is dropped,
# never an error (contract rule in onsite/cms.py).
SEO_KEYS = ("title", "description", "canonical", "schema_jsonld")
EXTENSIONS = (".md", ".mdx")
_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


class GitStaticClient(CmsAdapter):
    def __init__(self, repo_root, content_dir: str = "src/content",
                 fields: dict | None = None, dry_run: bool = False):
        self.repo_root = Path(repo_root)
        self.content_dir = content_dir
        self.fields = {**DEFAULT_FIELDS, **(fields or {})}
        # dry_run=True: reads behave normally; every mutating method records
        # its intent in dry_run_log instead of touching a file.
        self.dry_run = dry_run
        self.dry_run_log: list[dict] = []

    # -- plumbing --------------------------------------------------------------

    def _dry(self, method: str, fields: dict, post_id=None) -> dict:
        """Log the write that would have happened and return a realistic-shaped
        response marked dry_run: True (mirrors WPClient's pattern)."""
        entry = {"method": method, "fields": fields}
        if post_id is not None:
            entry["post_id"] = post_id
        self.dry_run_log.append(entry)
        return {"dry_run": True, "id": post_id, **fields}

    def _rel(self, path: Path) -> str:
        return str(path.relative_to(self.repo_root))

    def _resolve(self, ref) -> Path:
        """A content file from a slug or a relative path. A bare slug is
        searched under content_dir (nested dirs included, .md and .mdx,
        plus <slug>/index.*); zero matches or more than one is an error."""
        ref = str(ref).strip().lstrip("/")
        base = self.repo_root / self.content_dir
        if "/" in ref or ref.endswith(EXTENSIONS):
            for parent in (base, self.repo_root):
                for candidate in [parent / ref] + [parent / (ref + ext)
                                                   for ext in EXTENSIONS]:
                    if candidate.is_file():
                        return candidate
            raise RuntimeError(f"git-static: no content file at {ref!r} "
                               f"under {base}")
        matches: set = set()
        for ext in EXTENSIONS:
            matches |= set(base.rglob(f"{ref}{ext}"))
            matches |= set(base.rglob(f"{ref}/index{ext}"))
        matches = sorted(matches)
        if not matches:
            raise RuntimeError(f"git-static: no content file for {ref!r} "
                               f"under {base}")
        if len(matches) > 1:
            listing = ", ".join(self._rel(m) for m in matches)
            raise RuntimeError(f"git-static: ambiguous slug {ref!r}: {listing} "
                               "- pass the relative path instead")
        return matches[0]

    def _parse(self, path: Path) -> tuple[dict, str]:
        raw = path.read_text()
        m = _FRONTMATTER.match(raw)
        if not m:
            return {}, raw
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError as e:
            raise RuntimeError("git-static: bad frontmatter yaml in "
                               f"{self._rel(path)}: {e}") from None
        if fm is None:
            fm = {}
        if not isinstance(fm, dict):
            raise RuntimeError("git-static: frontmatter in "
                               f"{self._rel(path)} is not a mapping")
        return fm, m.group(2)

    def _write(self, path: Path, fm: dict, body: str) -> None:
        text = ("---\n"
                + yaml.safe_dump(fm, sort_keys=False,
                                 allow_unicode=True).strip("\n")
                + "\n---\n" + body)
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(path, text)

    def _record(self, path: Path, ref, fm: dict, body: str) -> dict:
        return {"id": str(ref), "slug": str(ref), "path": self._rel(path),
                "frontmatter": fm, "body": body}

    # -- reads -----------------------------------------------------------------

    def get_post(self, post_id) -> dict:
        path = self._resolve(post_id)
        fm, body = self._parse(path)
        return self._record(path, post_id, fm, body)

    def get_rendered_head(self, page_url: str) -> dict:
        raise RuntimeError(
            "git-static cannot fetch a rendered head: the site builds and "
            "deploys only after a human merges the PR "
            "(capabilities()['rendered_head_verify'] is False). Verify "
            f"post-deploy against the live URL instead: {page_url}")

    # -- writes (callers MUST hold an approved item; enforced in skills) -------

    def update_post(self, post_id, **fields) -> dict:
        path = self._resolve(post_id)
        fm, body = self._parse(path)
        for key, value in fields.items():
            if key == "content":
                body = value
            elif key == "status":
                fm[self.fields["draft"]] = (value == "draft")
            elif key == "excerpt":
                fm[self.fields["description"]] = value
            else:
                fm[self.fields.get(key, key)] = value
        if self.dry_run:
            return self._dry("update_post", fields, post_id)
        self._write(path, fm, body)
        return self._record(path, post_id, fm, body)

    def update_seo_meta(self, post_id, **seo) -> dict:
        mapped = {self.fields[k]: v for k, v in seo.items()
                  if k in SEO_KEYS and v is not None}
        path = self._resolve(post_id)
        fm, body = self._parse(path)
        fm.update(mapped)
        if self.dry_run:
            return self._dry("update_seo_meta", {"frontmatter": mapped},
                             post_id)
        self._write(path, fm, body)
        return self._record(path, post_id, fm, body)

    def create_post(self, slug: str, title: str, content: str,
                    status: str = "draft", excerpt: str = "",
                    **frontmatter) -> dict:
        """New file at content_dir/<slug>.md; draft means draft: true.

        Contract note: the CmsAdapter base orders (title, content, slug);
        this adapter leads with slug because the slug IS the filename.
        Call create_post with keyword arguments in any code that swaps
        adapters. Extra keyword arguments land as frontmatter fields,
        remapped through the fields mapping where a key matches."""
        path = self.repo_root / self.content_dir / f"{slug}.md"
        if path.exists():
            raise RuntimeError(f"git-static: {self._rel(path)} already "
                               "exists; update_post changes an existing file")
        fm = {self.fields["title"]: title}
        if excerpt:
            fm[self.fields["description"]] = excerpt
        fm[self.fields["draft"]] = (status == "draft")
        for k, v in frontmatter.items():
            fm[self.fields.get(k, k)] = v
        if self.dry_run:
            return self._dry("create_post", {"slug": slug, "title": title,
                                             "status": status,
                                             "frontmatter": fm,
                                             "content": content})
        self._write(path, fm, content)
        return self._record(path, slug, fm, content)

    # -- rollback --------------------------------------------------------------

    def snapshot(self, post_id, fields) -> dict:
        """The file IS the record: whichever `fields` the caller picks, the
        snapshot stores the file's complete text and rollback() rewrites it
        verbatim - a byte-identical restore, no field-level merging."""
        path = self._resolve(post_id)
        return {"post_id": str(post_id), "path": self._rel(path),
                "fields": list(fields), "text": path.read_text()}

    def rollback(self, snap: dict) -> dict:
        if self.dry_run:
            return self._dry("rollback", {"path": snap["path"]},
                             snap["post_id"])
        path = self.repo_root / snap["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(path, snap["text"])
        return {"id": snap["post_id"], "path": snap["path"], "restored": True}

    # -- introspection ---------------------------------------------------------

    def capabilities(self) -> dict:
        return {
            "seo_meta_fields": True,        # frontmatter keys per the mapping
            # jsonld is a frontmatter field the site's layout must render:
            "schema_injection": "frontmatter-field",
            "rendered_head_verify": False,  # static sites verify post-deploy
            # Publishing is a human's merge, then the site's own deploy;
            # such steps end the item partially-applied with a note, never
            # faked as done.
            "needs_human": ["merge-pr", "deploy"],
        }

    def adapter_name(self) -> str:
        return "git-static"
