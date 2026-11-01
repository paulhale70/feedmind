"""Regression tests for: RSS 1.0 parsing, Atom link choice, podcast page links,
readable list dates, throttled download progress, and local-network feeds."""
import io
import ipaddress
import types
from datetime import datetime, timezone

import pytest

import rss_core
import rss_podcast_downloader
from rss_core import RSSFetcher, UnsafeURLError, article_page_link
from rss_dates import format_display_date

FEED = "https://example.com/feed"


# --- RSS 1.0 (RDF) -----------------------------------------------------------

RDF_FEED = b"""<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns="http://purl.org/rss/1.0/"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel rdf:about="https://example.com/">
    <title>RDF Example</title>
    <link>https://example.com/</link>
  </channel>
  <item rdf:about="https://example.com/a">
    <title>First</title>
    <link>https://example.com/a</link>
    <description>&lt;p&gt;Hello&lt;/p&gt;</description>
    <dc:date>2026-10-27T10:30:00Z</dc:date>
  </item>
  <item rdf:about="https://example.com/b">
    <title>Second</title>
    <link>
      https://example.com/b
    </link>
  </item>
</rdf:RDF>"""


def test_rss1_rdf_feed_parses():
    articles = RSSFetcher()._parse_rss(RDF_FEED, FEED)
    assert [a.title for a in articles] == ["First", "Second"]
    assert [a.link for a in articles] == ["https://example.com/a", "https://example.com/b"]
    assert articles[0].feed_title == "RDF Example"
    assert articles[0].description == "Hello"
    assert articles[0].published == "2026-10-27T10:30:00Z"


def test_rss2_uses_dc_date_when_pubdate_missing():
    xml = b"""<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>
      <title>T</title>
      <item><title>X</title><link>https://example.com/x</link>
        <dc:date>2026-10-27</dc:date></item>
    </channel></rss>"""
    (article,) = RSSFetcher()._parse_rss(xml, FEED)
    assert article.published == "2026-10-27"
    assert article.feed_title == "T"


# --- Atom link selection ------------------------------------------------------

def _atom(entry_links):
    return (b'<feed xmlns="http://www.w3.org/2005/Atom"><title>A</title><entry>'
            b'<title>E</title>' + entry_links + b'</entry></feed>')


@pytest.mark.parametrize("links, expected", [
    # self/enclosure listed before the article page
    (b'<link rel="self" href="https://example.com/feed/e"/>'
     b'<link rel="enclosure" type="audio/mpeg" href="https://example.com/e.mp3"/>'
     b'<link rel="alternate" type="text/html" href="https://example.com/e"/>',
     "https://example.com/e"),
    # rel omitted means alternate
    (b'<link rel="replies" href="https://example.com/e#comments"/>'
     b'<link href="https://example.com/e"/>',
     "https://example.com/e"),
    # HTML alternate preferred over another alternate type
    (b'<link rel="alternate" type="application/pdf" href="https://example.com/e.pdf"/>'
     b'<link rel="alternate" type="text/html" href="https://example.com/e"/>',
     "https://example.com/e"),
    # only a non-HTML alternate
    (b'<link rel="alternate" type="application/pdf" href="https://example.com/e.pdf"/>',
     "https://example.com/e.pdf"),
    # no alternate: use a link that isn't self/enclosure/...
    (b'<link rel="self" href="https://example.com/feed/e"/>'
     b'<link rel="related" href="https://example.com/related"/>',
     "https://example.com/related"),
    # nothing usable
    (b'<link rel="self" href="https://example.com/feed/e"/>', ""),
])
def test_atom_picks_article_page_link(links, expected):
    (article,) = RSSFetcher()._parse_atom(_atom(links), FEED)
    assert article.link == expected


def test_atom_enclosure_still_detected():
    links = (b'<link rel="alternate" href="https://example.com/e"/>'
             b'<link rel="enclosure" type="audio/mpeg" length="5" href="https://example.com/e.mp3"/>')
    (article,) = RSSFetcher()._parse_atom(_atom(links), FEED)
    assert (article.link, article.audio_url) == ("https://example.com/e", "https://example.com/e.mp3")


# --- Podcast episode page links ----------------------------------------------

def _episode(n, page="https://example.com/show"):
    return types.SimpleNamespace(
        title=f"Ep {n}", link=page, description="d", published="2026-10-27",
        audio_url=f"https://cdn.example.com/ep{n}.mp3", audio_type="audio/mpeg",
        audio_length=1, duration_seconds=60)


def test_episode_keeps_page_link(db):
    db.cache_articles([_episode(1, "https://example.com/ep1"), _episode(2)], FEED)
    rows = {a["title"]: a for a in db.get_cached_articles()}
    # link stays the audio URL (unique per episode); page_link is the web page
    assert rows["Ep 1"]["link"] == "https://cdn.example.com/ep1.mp3"
    assert article_page_link(rows["Ep 1"]) == "https://example.com/ep1"
    assert article_page_link(rows["Ep 2"]) == "https://example.com/show"


def test_old_episode_gets_page_link_on_refresh(db):
    db.cache_articles([_episode(1, "https://example.com/ep1")], FEED)
    db.conn.execute("UPDATE articles SET page_link = NULL")  # as cached by an older version
    db.conn.commit()
    (row,) = db.get_cached_articles()
    assert article_page_link(row) == "https://cdn.example.com/ep1.mp3"  # fallback

    assert db.cache_articles([_episode(1, "https://example.com/ep1")], FEED) == 0
    (row,) = db.get_cached_articles()
    assert article_page_link(row) == "https://example.com/ep1"


def test_regular_article_page_link(db):
    db.cache_articles([types.SimpleNamespace(title="A", link="https://example.com/a",
                                             description="", published="")], FEED)
    (row,) = db.get_cached_articles()
    assert article_page_link(row) == "https://example.com/a"


# --- List date display -------------------------------------------------------

def test_display_date_rfc822_converted_to_local():
    expected = (datetime(2026, 10, 27, 3, 30, tzinfo=timezone.utc)
                .astimezone().strftime("%Y-%m-%d"))
    assert format_display_date("Tue, 27 Oct 2026 03:30:00 GMT") == expected


def test_display_date_bare_date_unchanged():
    assert format_display_date("2026-10-27") == "2026-10-27"


@pytest.mark.parametrize("text, expected", [
    ("", ""), (None, ""), ("sometime last week, probably", "sometime last we")])
def test_display_date_unparseable(text, expected):
    assert format_display_date(text) == expected


# --- Download progress throttling -------------------------------------------

class _FakeResponse(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}


def test_download_progress_is_throttled(tmp_path, monkeypatch):
    size = 8192 * 2000  # 2000 chunks
    monkeypatch.setattr(rss_podcast_downloader, "safe_urlopen",
                        lambda req, timeout: _FakeResponse(b"x" * size))
    calls, done = [], []
    dl = rss_podcast_downloader.PodcastDownloader(download_dir=str(tmp_path))
    dl._download_worker("https://example.com/ep.mp3", tmp_path / "ep.mp3",
                        lambda d, t: calls.append((d, t)),
                        lambda ok, path, err: done.append((ok, err)))
    assert done == [(True, None)]
    assert 1 <= len(calls) < 50          # was 2000 (one per chunk)
    assert calls[-1] == (size, size)     # final total always reported


# --- Local-network feeds -----------------------------------------------------

@pytest.fixture
def local_feeds():
    """Yield the setter; always restore the default (blocked) afterwards."""
    yield rss_core.set_allow_private_addresses
    rss_core.set_allow_private_addresses(False)


@pytest.mark.parametrize("addr, blocked_by_default, allowed_when_enabled", [
    ("8.8.8.8", False, True),
    ("127.0.0.1", True, True),
    ("192.168.1.10", True, True),
    ("10.0.0.5", True, True),
    ("172.16.0.1", True, True),
    ("::1", True, True),
    ("169.254.169.254", True, False),   # cloud metadata: always blocked
    ("fe80::1", True, False),           # link-local
    ("0.0.0.0", True, False),
    ("224.0.0.1", True, False),         # multicast
])
def test_local_network_setting(local_feeds, addr, blocked_by_default, allowed_when_enabled):
    ip = ipaddress.ip_address(addr)
    assert rss_core._is_allowed_ip(ip) is (not blocked_by_default)
    local_feeds(True)
    assert rss_core._is_allowed_ip(ip) is allowed_when_enabled


def test_localhost_url_needs_opt_in(local_feeds):
    with pytest.raises(UnsafeURLError, match="Preferences"):
        rss_core._validate_url("http://localhost:8080/feed")
    local_feeds(True)
    rss_core._validate_url("http://localhost:8080/feed")  # no error
    with pytest.raises(UnsafeURLError):
        rss_core._validate_url("file:///C:/Windows/win.ini")  # scheme check unaffected
