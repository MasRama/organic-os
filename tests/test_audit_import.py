import re
import sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from hoo import audit_import  # noqa: E402

# Synthetic report shaped like an external audit/action plan. Written for
# the tests; no real audit text is copied here.
REPORT = """# Full Audit Report

Site: https://example.com
Date: 2026-07-01

Executive summary paragraph that matches no item pattern.

## 🔴 Critical

- **Missing meta description on /pricing** [Measured]
  The pricing page ships no meta description tag. (Effort: Low)
- **Broken redirect chain to /signup** [Inference]
  Three hops ending in a 404. Effort: Medium

## 🟡 Medium

1. **No answer capsule above the fold** [Unverified]
   First 200 words contain no standalone answer.
2. Add llms.txt at the site root
   AI crawlers may read it. Effort: Low

## Other observations

- **Thin author bio on blog posts**
  Author pages lack sameAs links.
- **Improve page load speed on mobile**
  LCP over 4 seconds on 4G.

## Notes

Some closing prose that is not a finding.
"""


def titles(parsed):
    return [i["title"] for i in parsed["items"]]


def by_title(parsed, title):
    return next(i for i in parsed["items"] if i["title"] == title)


def test_tiered_bold_items_parse_with_severity():
    parsed = audit_import.parse_report(REPORT)
    it = by_title(parsed, "Missing meta description on /pricing")
    assert it["severity"] == "critical"
    assert it["section"] == "Full Audit Report > 🔴 Critical"
    assert "no meta description tag" in it["body"]
    assert by_title(parsed, "Broken redirect chain to /signup")["severity"] == "critical"


def test_numbered_findings_parse():
    parsed = audit_import.parse_report(REPORT)
    assert by_title(parsed, "No answer capsule above the fold")["severity"] == "medium"
    it = by_title(parsed, "Add llms.txt at the site root")
    assert it["severity"] == "medium"
    assert "AI crawlers may read it" in it["body"]


def test_item_outside_tier_has_no_severity():
    parsed = audit_import.parse_report(REPORT)
    it = by_title(parsed, "Thin author bio on blog posts")
    assert it["severity"] is None
    assert it["section"] == "Full Audit Report > Other observations"


def test_evidence_labels_captured():
    parsed = audit_import.parse_report(REPORT)
    assert by_title(parsed, "Missing meta description on /pricing")["evidence_label"] == "Measured"
    assert by_title(parsed, "Broken redirect chain to /signup")["evidence_label"] == "Inference"
    assert by_title(parsed, "No answer capsule above the fold")["evidence_label"] == "Unverified"
    assert by_title(parsed, "Add llms.txt at the site root")["evidence_label"] is None


def test_effort_captured():
    parsed = audit_import.parse_report(REPORT)
    assert by_title(parsed, "Missing meta description on /pricing")["effort"] == "Low"
    assert by_title(parsed, "Broken redirect chain to /signup")["effort"] == "Medium"
    assert by_title(parsed, "Thin author bio on blog posts")["effort"] is None


def test_unparsed_preserved_not_dropped():
    parsed = audit_import.parse_report(REPORT)
    joined = "\n---\n".join(parsed["unparsed"])
    assert "Executive summary paragraph" in joined
    assert "Some closing prose that is not a finding." in joined


def test_source_meta():
    parsed = audit_import.parse_report(REPORT)
    meta = parsed["source_meta"]
    assert meta["page_url"] == "https://example.com"
    assert meta["audit_date"] == "2026-07-01"
    assert "Full Audit Report" in meta["headings"]
    assert "🔴 Critical" in meta["headings"]


def test_empty_input_is_safe():
    parsed = audit_import.parse_report("")
    assert parsed["items"] == []
    assert parsed["unparsed"] == []
    assert parsed["source_meta"]["audit_date"] is None
    assert parsed["source_meta"]["page_url"] is None


def test_ranking_and_max_items():
    parsed = audit_import.parse_report(REPORT)
    props = audit_import.to_proposals(parsed, max_items=2)
    assert len(props) == 2
    assert props[0]["title"] == "Missing meta description on /pricing"
    assert props[1]["title"] == "Broken redirect chain to /signup"


def test_severity_none_ranks_last():
    parsed = audit_import.parse_report(REPORT)
    props = audit_import.to_proposals(parsed, max_items=10)
    assert [p["title"] for p in props[-2:]] == [
        "Thin author bio on blog posts",
        "Improve page load speed on mobile",
    ]


def test_slugs_valid_and_unique():
    parsed = audit_import.parse_report(REPORT)
    props = audit_import.to_proposals(parsed, max_items=10)
    slugs = [p["slug"] for p in props]
    assert len(slugs) == len(set(slugs))
    for slug in slugs:
        assert re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug), slug


def test_proposals_feed_create_item(tmp_path):
    from core import contracts
    parsed = audit_import.parse_report(REPORT)
    p = audit_import.to_proposals(parsed)[0]
    path = contracts.create_item(
        tmp_path, kind=p["kind"], slug=p["slug"], title=p["title"],
        body=p["body"], target="https://example.com", source="import-audit")
    item = contracts.load_item(path)
    assert item["meta"]["status"] == "proposed"
    assert item["meta"]["approvals"] == []
    assert "claude-seo" in item["body"]


def test_body_quotes_original_and_attributes():
    parsed = audit_import.parse_report(REPORT)
    p = audit_import.to_proposals(parsed)[0]
    assert "> - **Missing meta description on /pricing** [Measured]" in p["body"]
    assert "Imported from an external audit report - pattern credit: claude-seo" in p["body"]
    assert "[Measured]" in p["body"]


def test_dimension_mapping_note():
    parsed = audit_import.parse_report(REPORT)
    props = audit_import.to_proposals(parsed, max_items=10)
    bodies = {p["title"]: p["body"] for p in props}
    assert "`meta-length`" in bodies["Missing meta description on /pricing"]
    assert "`link-health`" in bodies["Broken redirect chain to /signup"]
    assert "`answer-capsule`" in bodies["No answer capsule above the fold"]
    assert "`author-entity`" in bodies["Thin author bio on blog posts"]


def test_llms_txt_gets_deliberate_skip_note():
    parsed = audit_import.parse_report(REPORT)
    props = audit_import.to_proposals(parsed, max_items=10)
    body = next(p["body"] for p in props if "llms.txt" in p["title"])
    assert "deliberate-skip" in body
    assert "evidence.md" in body


def test_external_only_marking():
    parsed = audit_import.parse_report(REPORT)
    props = audit_import.to_proposals(parsed, max_items=10)
    body = next(p["body"] for p in props
                if p["title"] == "Improve page load speed on mobile")
    assert "external-only" in body
