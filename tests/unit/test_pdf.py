"""PDF text cleaner: HTML stripping, entity-safe escaping for reportlab."""
from rss_pdf_exporter import PDFExporter


def test_clean_html_strips_tags_and_escapes():
    out = PDFExporter._clean_html("AT&T <b>bold</b> 1 < 2 & done")
    assert "<b>" not in out          # tags removed
    assert "&amp;" in out            # & escaped for reportlab markup
    assert "&lt;" in out             # < escaped
    assert "bold" in out             # inner text preserved


def test_clean_html_drops_script():
    out = PDFExporter._clean_html("safe<script>alert(1)</script>text")
    assert "alert" not in out
    assert "script" not in out.lower()


def test_clean_html_truncation_is_entity_safe():
    # Each '&' becomes '&amp;'; truncation must happen on plain text, never
    # splitting an entity, and end with the ellipsis marker.
    out = PDFExporter._clean_html("&" * 50, max_length=10)
    assert out.endswith("...")
    assert "&amp" in out
    # No dangling partial entity like '&am' at the very end (before the dots).
    assert not out.replace("...", "").endswith("&am")


def test_clean_html_empty():
    assert PDFExporter._clean_html("") == ""
    assert PDFExporter._clean_html(None) == ""
