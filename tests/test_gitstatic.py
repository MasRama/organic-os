"""GitStaticClient tests: tmp-dir repos, no real git, no transport.

The git-static adapter operates on a local clone path: it reads and writes
content files and returns structured results. The skill layer runs the
git/gh commands; nothing in the adapter (or these tests) shells out.
"""
import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import json  # noqa: E402
import pytest  # noqa: E402
import yaml  # noqa: E402
from onsite.cms import CmsAdapter, SUPPORTED_CMS_TYPES, adapter_for  # noqa: E402
from onsite.gitstatic import GitStaticClient  # noqa: E402


POST = (
    "---\n"
    "title: Old Title\n"
    "description: Old description\n"
    "canonical: https://site.example/old-post\n"
    "draft: false\n"
    "tags:\n"
    "  - keep\n"
    "---\n"
    "\n"
    "# Old Title\n"
    "\n"
    "Body paragraph one.\n"
    "\n"
    "---\n"
    "\n"
    "A thematic break above must survive every rewrite.\n"
)
POST_BODY = POST.split("\n---\n", 1)[1]


@pytest.fixture
def repo(tmp_path):
    content = tmp_path / "src" / "content"
    content.mkdir(parents=True)
    (content / "old-post.md").write_text(POST)
    return tmp_path


def make_client(repo, **kw):
    return GitStaticClient(repo, **kw)


def read_parts(path):
    """Parse a written file back into (frontmatter dict, exact body text)."""
    raw = path.read_text()
    assert raw.startswith("---\n")
    head, body = raw[4:].split("\n---\n", 1)
    return yaml.safe_load(head), body


# -- contract conformance ------------------------------------------------------

CONTRACT_SURFACE = ["get_post", "get_rendered_head", "get_media",
                    "update_post", "update_seo_meta", "update_media_alt",
                    "create_post", "snapshot", "rollback",
                    "capabilities", "adapter_name"]


def test_gitstatic_is_a_cms_adapter(repo):
    assert isinstance(make_client(repo), CmsAdapter)


@pytest.mark.parametrize("method", CONTRACT_SURFACE)
def test_gitstatic_overrides_the_full_contract_surface(method):
    # Mirror of test_cms.py's parametrized surface check: every contract
    # method must be this adapter's own, never the base's NotImplementedError.
    assert getattr(GitStaticClient, method) is not getattr(CmsAdapter, method)


def test_git_static_is_a_supported_cms_type():
    assert "git-static" in SUPPORTED_CMS_TYPES


def test_adapter_name_is_git_static(repo):
    assert make_client(repo).adapter_name() == "git-static"


def test_capabilities_declare_the_honest_gaps(repo):
    caps = make_client(repo).capabilities()
    assert caps["seo_meta_fields"] is True
    assert caps["schema_injection"] == "frontmatter-field"
    assert caps["rendered_head_verify"] is False
    assert caps["author_profile_fields"] is False
    # Redirects land in the platform's config file (_redirects,
    # netlify.toml, vercel.json - the profile's cms.redirect_file key).
    assert caps["redirects"] == "config-file"
    # Alt text lives in the content file itself (markdown image syntax or
    # frontmatter), not a media database - the mode string says so.
    assert caps["media_alt"] == "in-content"
    assert caps["needs_human"] == ["merge-pr", "deploy"]


# -- reads ---------------------------------------------------------------------

def test_get_post_parses_frontmatter_and_body(repo):
    post = make_client(repo).get_post("old-post")
    assert post["frontmatter"]["title"] == "Old Title"
    assert post["frontmatter"]["draft"] is False
    assert post["frontmatter"]["tags"] == ["keep"]
    assert post["body"] == POST_BODY
    assert post["path"] == "src/content/old-post.md"


def test_get_post_resolves_nested_mdx_by_slug(repo):
    nested = repo / "src" / "content" / "blog" / "nested.mdx"
    nested.parent.mkdir()
    nested.write_text("---\ntitle: Nested\n---\nBody.\n")
    post = make_client(repo).get_post("nested")
    assert post["frontmatter"]["title"] == "Nested"
    assert post["path"] == "src/content/blog/nested.mdx"


def test_get_post_accepts_a_relative_path(repo):
    post = make_client(repo).get_post("src/content/old-post.md")
    assert post["frontmatter"]["title"] == "Old Title"


def test_get_post_missing_slug_raises_naming_it(repo):
    with pytest.raises(RuntimeError) as exc:
        make_client(repo).get_post("nope")
    assert "nope" in str(exc.value)


def test_get_post_ambiguous_slug_raises_listing_matches(repo):
    for sub in ("a", "b"):
        d = repo / "src" / "content" / sub
        d.mkdir()
        (d / "dup.md").write_text("---\ntitle: Dup\n---\nBody.\n")
    with pytest.raises(RuntimeError) as exc:
        make_client(repo).get_post("dup")
    assert "src/content/a/dup.md" in str(exc.value)
    assert "src/content/b/dup.md" in str(exc.value)


def test_get_post_bad_frontmatter_yaml_raises(repo):
    bad = repo / "src" / "content" / "bad.md"
    bad.write_text("---\ntitle: [unclosed\n---\nBody.\n")
    with pytest.raises(RuntimeError) as exc:
        make_client(repo).get_post("bad")
    assert "bad.md" in str(exc.value)


def test_get_rendered_head_raises_naming_the_capability_gap(repo):
    with pytest.raises(RuntimeError) as exc:
        make_client(repo).get_rendered_head("https://site.example/old-post")
    assert "rendered_head_verify" in str(exc.value)
    assert "post-deploy" in str(exc.value)


# -- writes --------------------------------------------------------------------

def test_update_post_rewrites_frontmatter_preserves_body_bytes(repo):
    make_client(repo).update_post("old-post", title="New Title")
    fm, body = read_parts(repo / "src" / "content" / "old-post.md")
    assert fm["title"] == "New Title"
    assert fm["tags"] == ["keep"]          # untouched keys survive
    assert body == POST_BODY               # body byte-identical


def test_update_post_content_replaces_body_keeps_frontmatter(repo):
    make_client(repo).update_post("old-post", content="\nNew body.\n")
    fm, body = read_parts(repo / "src" / "content" / "old-post.md")
    assert body == "\nNew body.\n"
    assert fm["title"] == "Old Title"


def test_update_post_status_maps_to_the_draft_flag(repo):
    c = make_client(repo)
    c.update_post("old-post", status="draft")
    fm, _ = read_parts(repo / "src" / "content" / "old-post.md")
    assert fm["draft"] is True
    c.update_post("old-post", status="publish")
    fm, _ = read_parts(repo / "src" / "content" / "old-post.md")
    assert fm["draft"] is False


def test_update_seo_meta_touches_only_mapped_fields(repo):
    make_client(repo).update_seo_meta(
        "old-post", title="SEO T", description="SEO D",
        canonical="https://site.example/new", focus_keyword="dropped")
    fm, body = read_parts(repo / "src" / "content" / "old-post.md")
    assert fm["title"] == "SEO T"
    assert fm["description"] == "SEO D"
    assert fm["canonical"] == "https://site.example/new"
    assert "focus_keyword" not in fm       # unmapped keys dropped, not written
    assert fm["draft"] is False            # unrelated keys untouched
    assert fm["tags"] == ["keep"]
    assert body == POST_BODY


def test_update_seo_meta_schema_jsonld_lands_in_the_jsonld_field(repo):
    raw = '{"@type": "Article"}'
    make_client(repo).update_seo_meta("old-post", schema_jsonld=raw)
    fm, _ = read_parts(repo / "src" / "content" / "old-post.md")
    assert fm["jsonld"] == raw
    assert "schema_jsonld" not in fm


def test_fields_override_remaps_frontmatter_keys(repo):
    c = make_client(repo, fields={"description": "excerpt"})
    c.update_seo_meta("old-post", description="Remapped")
    fm, _ = read_parts(repo / "src" / "content" / "old-post.md")
    assert fm["excerpt"] == "Remapped"
    assert fm["description"] == "Old description"   # original key untouched
    assert c.fields["title"] == "title"             # defaults kept for the rest


def test_create_post_draft_by_default(repo):
    make_client(repo).create_post("fresh", "Fresh Title", "Fresh body.\n")
    path = repo / "src" / "content" / "fresh.md"
    fm, body = read_parts(path)
    assert fm["title"] == "Fresh Title"
    assert fm["draft"] is True
    assert body == "Fresh body.\n"


def test_create_post_publish_sets_draft_false(repo):
    make_client(repo).create_post("live", "Live", "B", status="publish")
    fm, _ = read_parts(repo / "src" / "content" / "live.md")
    assert fm["draft"] is False


def test_create_post_existing_file_raises(repo):
    with pytest.raises(RuntimeError) as exc:
        make_client(repo).create_post("old-post", "Clash", "B")
    assert "old-post" in str(exc.value)


# -- media: get_media / update_media_alt ---------------------------------------

IMAGE_POST = (
    "---\n"
    "title: With Images\n"
    "alt: Featured card alt\n"
    "draft: false\n"
    "---\n"
    "\n"
    "Intro paragraph.\n"
    "\n"
    "![Old chart alt](/images/chart.png)\n"
    "\n"
    '<img src="/images/photo.jpg" alt="Photo alt">\n'
    "\n"
    "![](/images/no-alt.png)\n"
)


@pytest.fixture
def image_repo(repo):
    (repo / "src" / "content" / "with-images.md").write_text(IMAGE_POST)
    return repo


def test_get_media_lists_markdown_and_html_images(image_repo):
    media = make_client(image_repo).get_media("with-images")
    assert [(m["src"], m["alt"]) for m in media] == [
        ("/images/chart.png", "Old chart alt"),
        ("/images/photo.jpg", "Photo alt"),
        ("/images/no-alt.png", "")]
    # media_id is post-ref-scoped so update_media_alt can act on it alone.
    assert media[0]["media_id"] == "with-images::/images/chart.png"


def test_update_media_alt_rewrites_markdown_alt_round_trip(image_repo):
    c = make_client(image_repo)
    c.update_media_alt("with-images::/images/chart.png", "New chart alt")
    media = c.get_media("with-images")
    assert media[0]["alt"] == "New chart alt"
    fm, body = read_parts(image_repo / "src" / "content" / "with-images.md")
    assert "![New chart alt](/images/chart.png)" in body
    assert "Old chart alt" not in body
    assert '<img src="/images/photo.jpg" alt="Photo alt">' in body  # untouched
    assert fm["title"] == "With Images"


def test_update_media_alt_rewrites_html_and_empty_alts(image_repo):
    c = make_client(image_repo)
    c.update_media_alt("with-images::/images/photo.jpg", "A better photo alt")
    c.update_media_alt("with-images::/images/no-alt.png", "Filled alt")
    _, body = read_parts(image_repo / "src" / "content" / "with-images.md")
    assert 'alt="A better photo alt"' in body
    assert "![Filled alt](/images/no-alt.png)" in body


def test_update_media_alt_frontmatter_target_writes_alt_field(image_repo):
    # ce-image's convention: the featured image's alt lives in frontmatter.
    c = make_client(image_repo)
    c.update_media_alt("with-images::frontmatter", "New featured alt")
    fm, body = read_parts(image_repo / "src" / "content" / "with-images.md")
    assert fm["alt"] == "New featured alt"
    assert "Old chart alt" in body              # body untouched


def test_update_media_alt_unknown_src_raises_naming_it(image_repo):
    with pytest.raises(RuntimeError) as exc:
        make_client(image_repo).update_media_alt(
            "with-images::/images/nope.png", "x")
    assert "/images/nope.png" in str(exc.value)


def test_dry_run_update_media_alt_zero_writes_logs_intent(image_repo):
    c = make_client(image_repo, dry_run=True)
    out = c.update_media_alt("with-images::/images/chart.png", "Dry alt")
    assert (image_repo / "src" / "content" / "with-images.md"
            ).read_text() == IMAGE_POST
    assert out["dry_run"] is True
    entry = c.dry_run_log[-1]
    assert entry["method"] == "update_media_alt"
    assert entry["fields"]["alt_text"] == "Dry alt"


# -- snapshot / rollback -------------------------------------------------------

def test_snapshot_then_rollback_restores_byte_identical(repo, tmp_path):
    c = make_client(repo)
    snap = c.snapshot("old-post", fields=["title", "meta", "content"])
    rec = tmp_path / "rollback.json"
    rec.write_text(json.dumps(snap))            # snapshots survive a JSON trip
    c.update_post("old-post", title="Wrecked", content="Wrecked body.\n")
    c.update_seo_meta("old-post", description="Wrecked too")
    c.rollback(json.loads(rec.read_text()))
    assert (repo / "src" / "content" / "old-post.md").read_text() == POST


# -- dry-run mode --------------------------------------------------------------

def test_dry_run_mutations_zero_writes_log_intent(repo):
    c = make_client(repo, dry_run=True)
    out = c.update_post("old-post", title="Dry")
    c.update_seo_meta("old-post", description="Dry D")
    c.create_post("dry-new", "Dry New", "B")
    c.rollback({"post_id": "old-post", "path": "src/content/old-post.md",
                "text": "replaced"})
    assert (repo / "src" / "content" / "old-post.md").read_text() == POST
    assert not (repo / "src" / "content" / "dry-new.md").exists()
    assert out["dry_run"] is True
    assert [e["method"] for e in c.dry_run_log] == [
        "update_post", "update_seo_meta", "create_post", "rollback"]
    assert c.dry_run_log[0]["post_id"] == "old-post"
    assert c.dry_run_log[0]["fields"] == {"title": "Dry"}
    assert c.dry_run_log[2]["fields"]["slug"] == "dry-new"


def test_dry_run_reads_behave_normally(repo):
    c = make_client(repo, dry_run=True)
    assert c.get_post("old-post")["frontmatter"]["title"] == "Old Title"
    snap = c.snapshot("old-post", fields=["title"])
    assert snap["text"] == POST
    assert c.dry_run_log == []                  # a read is not a logged intent


# -- adapter_for factory -------------------------------------------------------

def _gs_profile(repo, **cms_over):
    cms = {"type": "git-static", "repo_root": str(repo),
           "content_dir": "src/content"}
    cms.update(cms_over)
    return {"cms": cms}


def test_adapter_for_git_static_builds_client(repo):
    a = adapter_for(_gs_profile(repo, fields={"description": "excerpt"}))
    assert isinstance(a, GitStaticClient)
    assert a.repo_root == Path(str(repo))
    assert a.content_dir == "src/content"
    assert a.fields["description"] == "excerpt"
    assert a.adapter_name() == "git-static"


def test_adapter_for_git_static_passes_dry_run_through(repo):
    a = adapter_for(_gs_profile(repo), dry_run=True)
    assert a.dry_run is True


def test_adapter_for_git_static_without_repo_root_raises(repo):
    with pytest.raises(ValueError) as exc:
        adapter_for({"cms": {"type": "git-static"}})
    assert "repo_root" in str(exc.value)
