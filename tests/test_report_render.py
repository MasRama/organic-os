import os
import stat
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from core import report_render as R  # noqa: E402


SAMPLE = """# Monday report

## What moved

- **Clicks** rose from 120 to 150 ([signal](../signals/2026-07-13.md))
- AI referrals: 12 this week, up from 9

## What shipped

| Item | Status |
|---|---|
| p-20260713-title | applied |
| b-20260710-guide | published |

## What needs you

Nothing is waiting on a decision this week.
"""


def test_render_html_covers_the_report_subset():
    out = R.render_html(SAMPLE, title="Monday report", site_name="Example Site")
    assert "<h1>Monday report</h1>" in out
    assert "<h2>What moved</h2>" in out
    assert "<strong>Clicks</strong>" in out
    assert '<a href="../signals/2026-07-13.md">signal</a>' in out
    assert "<li>" in out
    assert "<table>" in out and "<th>Item</th>" in out
    assert "<td>applied</td>" in out
    assert "<p>Nothing is waiting on a decision this week.</p>" in out
    assert "Example Site" in out
    assert "<title>Monday report</title>" in out


def test_render_html_is_self_contained():
    # The page chrome references nothing external: content with no URLs
    # must render to HTML with no URLs at all - no CDN CSS, fonts, or
    # scripts smuggled in by the template.
    out = R.render_html("# T\n\nA plain paragraph.", title="T", site_name="S")
    assert "http" not in out
    assert "<script" not in out.lower()
    assert "<style>" in out  # inline CSS only


def test_render_html_escapes_raw_html():
    out = R.render_html("A <script>alert(1)</script> tag.",
                        title="T", site_name="S")
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out


def _fake_bin(dirpath, name, body="#!/bin/sh\nexit 0\n"):
    p = dirpath / name
    p.write_text(body)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def test_find_pdf_converter_probes_path_in_order(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    monkeypatch.setenv("PATH", str(bindir))
    assert R.find_pdf_converter() is None
    _fake_bin(bindir, "weasyprint")
    assert R.find_pdf_converter() == "weasyprint"
    # pandoc outranks weasyprint in the declared order
    _fake_bin(bindir, "pandoc")
    assert R.find_pdf_converter() == "pandoc"


def test_to_pdf_returns_path_when_converter_succeeds(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    # A fake wkhtmltopdf that writes its second argument.
    _fake_bin(bindir, "wkhtmltopdf",
              "#!/bin/sh\nprintf 'pdf' > \"$2\"\nexit 0\n")
    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ["PATH"])
    html = tmp_path / "r.html"
    html.write_text("<p>hi</p>")
    out = R.to_pdf(html, "wkhtmltopdf")
    assert out == html.with_suffix(".pdf")
    assert out.read_bytes() == b"pdf"


def test_to_pdf_returns_none_when_converter_fails(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _fake_bin(bindir, "wkhtmltopdf", "#!/bin/sh\nexit 1\n")
    monkeypatch.setenv("PATH", str(bindir))
    html = tmp_path / "r.html"
    html.write_text("<p>hi</p>")
    assert R.to_pdf(html, "wkhtmltopdf") is None


def test_to_pdf_never_raises_on_a_missing_converter(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))  # empty PATH dir
    html = tmp_path / "r.html"
    html.write_text("<p>hi</p>")
    assert R.to_pdf(html, "wkhtmltopdf") is None


def test_render_html_renders_deeper_heading_levels():
    out = R.render_html("### Detail\n\ntext", title="T", site_name="S")
    assert "<h3>Detail</h3>" in out


def test_render_html_joins_wrapped_paragraph_lines():
    out = R.render_html("One line\nwrapped onto two.", title="T", site_name="S")
    assert "<p>One line wrapped onto two.</p>" in out


def test_render_html_table_cells_carry_inline_markup():
    md = "| Item |\n|---|\n| **bold** [x](y.md) |"
    out = R.render_html(md, title="T", site_name="S")
    assert "<td><strong>bold</strong> <a href=\"y.md\">x</a></td>" in out


def test_to_pdf_unknown_converter_returns_none(tmp_path):
    html = tmp_path / "r.html"
    html.write_text("<p>hi</p>")
    assert R.to_pdf(html, "not-a-converter") is None
