"""OPML import/export: round-trip and recursion-depth guard."""
from rss_opml import OPMLHandler


def test_roundtrip(tmp_path):
    feeds = [
        {"url": "https://a.com/feed", "title": "A Feed", "category_id": 1},
        {"url": "https://b.com/feed", "title": "B Feed", "category_id": None},
    ]
    categories = [{"id": 1, "name": "News"}]
    path = str(tmp_path / "out.opml")

    assert OPMLHandler.export_to_opml(feeds, categories, path) is True

    result = OPMLHandler.import_from_opml(path)
    urls = {f["url"] for f in result["feeds"]}
    assert "https://a.com/feed" in urls
    assert "https://b.com/feed" in urls


def test_deeply_nested_opml_does_not_recurse_forever(tmp_path):
    depth = 200  # well past the MAX_OPML_DEPTH guard
    leaf = '<outline text="leaf" xmlUrl="https://example.com/f.xml"/>'
    body = "<outline text='c'>" * depth + leaf + "</outline>" * depth
    opml = ('<?xml version="1.0"?><opml version="2.0"><head><title>t</title>'
            f'</head><body>{body}</body></opml>')
    path = tmp_path / "deep.opml"
    path.write_text(opml, encoding="utf-8")

    # Must not raise RecursionError; returns a normal result dict.
    result = OPMLHandler.import_from_opml(str(path))
    assert "feeds" in result and "categories" in result
